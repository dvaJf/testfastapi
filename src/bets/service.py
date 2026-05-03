from sqlalchemy import select, update, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, UTC
from typing import Optional

from src.bets.models import Bet, BetOption, UserBet
from src.auth.models import User
from src.database import AsyncSession
from src.exceptions import NotFoundException, BadRequestException


async def get_all_bets(session: AsyncSession) -> list[Bet]:
    result = await session.execute(
        select(Bet)
        .options(selectinload(Bet.creator), selectinload(Bet.options))
        .order_by(Bet.closes_at.desc())
    )
    return list(result.scalars().all())


async def get_bet(bet_id: int, session: AsyncSession) -> Bet:
    result = await session.execute(
        select(Bet).where(Bet.id == bet_id).options(selectinload(Bet.creator))
    )
    bet = result.scalar_one_or_none()
    if bet is None:
        raise NotFoundException(detail="Ставка не найдена")
    return bet


async def get_bet_with_options(bet_id: int, session: AsyncSession) -> Bet:
    result = await session.execute(
        select(Bet)
        .where(Bet.id == bet_id)
        .options(selectinload(Bet.creator), selectinload(Bet.options))
    )
    bet = result.scalar_one_or_none()
    if bet is None:
        raise NotFoundException(detail="Ставка не найдена")
    return bet


async def create_bet(
    title: str,
    description: Optional[str],
    closes_at: datetime,
    options: list[dict],
    created_by: int,
    session: AsyncSession,
) -> Bet:
    if closes_at <= datetime.now(UTC):
        raise BadRequestException(detail="Время закрытия должно быть в будущем")

    if len(options) < 2:
        raise BadRequestException(detail="Нужно минимум 2 варианта ставки")

    bet = Bet(
        title=title,
        description=description,
        closes_at=closes_at,
        created_by=created_by,
        status="открыта",
    )
    session.add(bet)
    await session.flush()

    for opt in options:
        option = BetOption(
            bet_id=bet.id,
            label=opt["label"],
            description=opt.get("description"),
        )
        session.add(option)

    await session.commit()
    await session.refresh(bet)
    return bet


async def update_bet(bet_id: int, data: dict, session: AsyncSession) -> Bet:
    bet = await get_bet_with_options(bet_id, session)

    if bet.status != "открыта":
        raise BadRequestException(detail="Можно редактировать только открытые ставки")

    # Update simple fields
    simple_fields = ["title", "description", "closes_at", "status"]
    for field in simple_fields:
        if field in data and data[field] is not None:
            if field == "closes_at" and data[field] <= datetime.now(UTC):
                raise BadRequestException(detail="Время закрытия должно быть в будущем")
            setattr(bet, field, data[field])

    # Update options if provided
    if "options" in data and data["options"] is not None:
        from src.bets.models import BetOption

        options_data = data["options"]
        existing_options = {opt.id: opt for opt in bet.options}
        updated_option_ids = set()

        for opt_dict in options_data:
            # opt_dict is a dict with keys: id (optional), label, description
            if opt_dict.get("id") and int(opt_dict["id"]) in existing_options:
                # Update existing option
                opt_id = int(opt_dict["id"])
                option = existing_options[opt_id]
                option.label = opt_dict["label"]
                option.description = opt_dict.get("description")
                updated_option_ids.add(opt_id)
            else:
                # Create new option
                new_opt = BetOption(
                    bet_id=bet.id,
                    label=opt_dict["label"],
                    description=opt_dict.get("description"),
                )
                session.add(new_opt)

        # Delete options not in updated list (only if no stakes)
        for opt_id, option in existing_options.items():
            if opt_id not in updated_option_ids:
                # Check if any user bets on this option
                result = await session.execute(
                    select(UserBet).where(UserBet.option_id == opt_id).limit(1)
                )
                if result.scalar_one_or_none():
                    raise BadRequestException(
                        detail=f"Нельзя удалить вариант '{option.label}', на него уже поставили очки"
                    )
                await session.delete(option)

        # Ensure at least 2 options remain
        remaining_options = await session.execute(
            select(BetOption).where(BetOption.bet_id == bet.id)
        )
        if len(list(remaining_options.scalars().all())) < 2:
            raise BadRequestException(detail="Должно остаться минимум 2 варианта")

    await session.commit()
    await session.refresh(bet)
    return bet


async def delete_bet(bet_id: int, session: AsyncSession) -> None:
    bet = await get_bet_with_options(bet_id, session)
    await refund_all_bets(bet_id, session)
    await session.delete(bet)
    await session.commit()


async def place_bet(
    bet_id: int, user_id: int, option_id: int, stake: int, session: AsyncSession
) -> UserBet:
    bet = await get_bet_with_options(bet_id, session)

    if bet.status != "открыта":
        raise BadRequestException(detail="Ставка закрыта для голосования")

    # Ensure both datetimes are offset-aware
    now = datetime.now(UTC)
    closes_at = bet.closes_at
    if closes_at.tzinfo is None:
        closes_at = closes_at.replace(tzinfo=UTC)
    if now >= closes_at:
        bet.status = "закрыта"
        await session.commit()
        raise BadRequestException(detail="Время приёма ставок истекло")

    valid_option_ids = {opt.id for opt in bet.options}
    if option_id not in valid_option_ids:
        raise BadRequestException(detail="Неверный вариант ставки")

    existing = await session.execute(
        select(UserBet).where(UserBet.bet_id == bet_id, UserBet.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise BadRequestException(detail="Вы уже сделали ставку на это событие")

    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or user.score < stake:
        raise BadRequestException(detail="Недостаточно очков для ставки")

    await session.execute(
        update(User).where(User.id == user_id).values(score=User.score - stake)
    )

    user_bet = UserBet(
        bet_id=bet_id,
        user_id=user_id,
        option_id=option_id,
        stake=stake,
    )
    session.add(user_bet)
    await session.commit()
    await session.refresh(user_bet)
    return user_bet


async def get_user_bets(user_id: int, session: AsyncSession) -> list[UserBet]:
    result = await session.execute(
        select(UserBet)
        .where(UserBet.user_id == user_id)
        .options(selectinload(UserBet.bet), selectinload(UserBet.option))
        .order_by(UserBet.placed_at.desc())
    )
    return list(result.scalars().all())


async def get_bet_participants(bet_id: int, session: AsyncSession) -> list[UserBet]:
    result = await session.execute(
        select(UserBet)
        .where(UserBet.bet_id == bet_id)
        .options(selectinload(UserBet.user), selectinload(UserBet.option))
    )
    return list(result.scalars().all())


async def resolve_bet(bet_id: int, winning_option_id: int, session: AsyncSession) -> None:
    bet = await get_bet_with_options(bet_id, session)

    if bet.status == "завершена":
        raise BadRequestException(detail="Ставка уже завершена")

    valid_option_ids = {opt.id for opt in bet.options}
    if winning_option_id not in valid_option_ids:
        raise BadRequestException(detail="Неверный вариант победителя")

    participants = await get_bet_participants(bet_id, session)

    if participants:
        total_pool = sum(p.stake for p in participants)
        winning_bets = [p for p in participants if p.option_id == winning_option_id]

        if winning_bets:
            winning_pool = sum(p.stake for p in winning_bets)
            for bet_item in winning_bets:
                share = int((bet_item.stake / winning_pool) * total_pool)
                await session.execute(
                    update(User).where(User.id == bet_item.user_id).values(score=User.score + share)
                )

    bet.status = "завершена"
    bet.winning_option_id = winning_option_id
    await session.commit()


async def refund_all_bets(bet_id: int, session: AsyncSession) -> None:
    participants = await get_bet_participants(bet_id, session)
    for bet_item in participants:
        await session.execute(
            update(User).where(User.id == bet_item.user_id).values(score=User.score + bet_item.stake)
        )
    await session.execute(delete(UserBet).where(UserBet.bet_id == bet_id))
