from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.database import get_session
from src.auth.service import fastapi_users
from src.auth.models import User
from src.bets import service
from src.bets.schemas import *
from src.exceptions import ForbiddenException
from src.bets.models import Bet, BetOption, UserBet

current_user = fastapi_users.current_user()
router = APIRouter()


@router.get("/", response_model=list[BetShort])
async def list_bets(session: AsyncSession = Depends(get_session)):
    bets = await service.get_all_bets(session)
    result = []
    for bet in bets:
        participants = await service.get_bet_participants(bet.id, session)
        total_pool = sum(p.stake for p in participants)
        result.append(BetShort.model_validate({
            **bet.__dict__,
            "creator_email": bet.creator.email if bet.creator else None,
            "total_pool": total_pool,
            "options_count": len(bet.options),
        }))
    return result


@router.get("/{bet_id}", response_model=BetOut)
async def get_bet(
    bet_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    bet = await service.get_bet_with_options(bet_id, session)

    participants = await service.get_bet_participants(bet_id, session)
    total_pool = sum(p.stake for p in participants)

    user_bet_result = await session.execute(
        select(UserBet).where(and_(UserBet.bet_id == bet_id, UserBet.user_id == user.id))
    )
    user_bet = user_bet_result.scalar_one_or_none()

    options_out = []
    for opt in bet.options:
        option_stakes = sum(p.stake for p in participants if p.option_id == opt.id)
        options_out.append(BetOptionOut.model_validate({
            **opt.__dict__,
            "total_stakes": option_stakes,
        }))

    return BetOut.model_validate({
        **bet.__dict__,
        "total_pool": total_pool,
        "options": options_out,
        "user_has_bet": user_bet is not None,
        "user_bet": user_bet,
    })


@router.post("/", response_model=BetOut, status_code=status.HTTP_201_CREATED)
async def create_bet(
    data: BetCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException()

    bet = await service.create_bet(
        title=data.title,
        description=data.description,
        closes_at=data.closes_at,
        options=[opt.model_dump() for opt in data.options],
        created_by=user.id,
        session=session,
    )
    return await service.get_bet_with_options(bet.id, session)


@router.patch("/{bet_id}", response_model=BetOut)
async def update_bet(
    bet_id: int,
    data: BetUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException()

    bet = await service.update_bet(bet_id, data.model_dump(exclude_none=True), session)
    return await service.get_bet_with_options(bet.id, session)


@router.delete("/{bet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bet(
    bet_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException()

    await service.delete_bet(bet_id, session)


@router.post("/{bet_id}/bet", status_code=status.HTTP_201_CREATED)
async def place_bet(
    bet_id: int,
    data: UserBetCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    await service.place_bet(bet_id, user.id, data.option_id, data.stake, session)
    return {"message": "Ставка принята"}


@router.get("/user/my-bets", response_model=list[UserBetOut])
async def my_bets(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    bets = await service.get_user_bets(user.id, session)
    return [
        UserBetOut.model_validate({
            **b.__dict__,
            "option_label": b.option.label,
            "username": b.user.email,
        })
        for b in bets
    ]


@router.post("/{bet_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_bet(
    bet_id: int,
    data: BetResolve,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException()

    await service.resolve_bet(bet_id, data.winning_option_id, session)
    return {"message": "Ставка завершена, очки распределены"}
