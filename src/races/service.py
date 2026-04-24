from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, case
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from src.races.models import Race, RaceResult, OrganizerReview
from src.auth.models import User
from typing import Optional
from src.exceptions import *

# Позиции: положительные = очки за финиш, отрицательные = DNS/DSQ
pos = {
    1: 60, 2: 55, 3: 50, 4: 47, 5: 44, 6: 42, 7: 40, 8: 38, 9: 35, 10: 32,
    11: 28, 12: 25, 13: 22, 14: 20, 15: 18, 16: 16, 17: 13, 18: 10, 19: 5, 20: 0,
    -1: -30,  # DNS
    -2: -15,  # DSQ
}

def points_for_position(position: int) -> int:
    return pos.get(position, 0)

def is_special_position(position: int) -> bool:
    """DNS (-1) и DSQ (-2) — специальные позиции, не финиш."""
    return position < 0


async def get_all_races_with_creator(session: AsyncSession):
    result = await session.execute(select(Race).options(selectinload(Race.creator)))
    return result.scalars().all()


async def get_race(id: int, session: AsyncSession):
    result = await session.execute(select(Race).where(Race.id == id))
    race = result.scalar_one_or_none()
    if race is None:
        raise NotFoundException()
    return race


async def get_race_with_creator(id: int, session: AsyncSession):
    result = await session.execute(
        select(Race).where(Race.id == id).options(selectinload(Race.creator))
    )
    race = result.scalar_one_or_none()
    if race is None:
        raise NotFoundException()
    return race


async def create_race(
    name: str, race: str, about: Optional[str], time: datetime,
    maxuser: int, status: str, created_by: int, session: AsyncSession
):
    new_race = Race(
        name=name, race=race, about=about,
        time=time.replace(tzinfo=None) + timedelta(hours=3),
        maxuser=maxuser, status=status, created_by=created_by, scores_awarded=False,
    )
    session.add(new_race)
    await session.commit()
    await session.refresh(new_race)
    return new_race


async def get_all_users(id: int, session: AsyncSession):
    result = await session.execute(
        select(RaceResult).where(RaceResult.race_id == id).options(selectinload(RaceResult.user))
    )
    return result.scalars().all()


async def get_results(id: int, session: AsyncSession):
    """
    Возвращает результаты гонки:
    - сначала финишировавшие (position > 0), отсортированные по позиции по возрастанию
    - затем DNS/DSQ (position < 0) в конце списка
    """
    result = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.position.isnot(None))
        .options(selectinload(RaceResult.user))
        .order_by(
            # 0 = финишировавшие (вперёд), 1 = DNS/DSQ (в конец)
            case((RaceResult.position > 0, 0), else_=1),
            RaceResult.position,
        )
    )
    return result.scalars().all()


async def register_user(id: int, user_id: int, session: AsyncSession):
    race = await get_race(id, session)

    if race.status != "Регистрация":
        raise BadRequestException()

    if race.users >= race.maxuser:
        raise BadRequestException()

    existing = await session.execute(
        select(RaceResult).where(RaceResult.race_id == id).where(RaceResult.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise BadRequestException()

    race_result = RaceResult(race_id=id, user_id=user_id)
    session.add(race_result)
    await session.execute(update(Race).where(Race.id == id).values(users=Race.users + 1))
    await session.commit()
    return race_result


async def unregister_user(id: int, user_id: int, session: AsyncSession):
    race = await get_race(id, session)
    if race.status != "Регистрация":
        raise BadRequestException()

    result = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.user_id == user_id)
    )
    race_result = result.scalar_one_or_none()
    if race_result is None:
        raise BadRequestException()
    await session.execute(update(Race).where(Race.id == id).values(users=Race.users - 1))
    await session.delete(race_result)
    await session.commit()


async def set_results(race_id: int, results: list, session: AsyncSession):
    race = await get_race(race_id, session)
    if race.status != "Завершена":
        raise BadRequestException()

    # Проверяем уникальность позиций ТОЛЬКО среди финишировавших (position > 0).
    # DNS (-1) и DSQ (-2) могут повторяться у нескольких пилотов.
    finish_positions = [r.position for r in results if r.position > 0]
    if len(finish_positions) != len(set(finish_positions)):
        raise BadRequestException(detail="Позиции финишировавших участников должны быть уникальными")

    # Загружаем всех зарегистрированных участников
    existing_q = await session.execute(
        select(RaceResult).where(RaceResult.race_id == race_id)
    )
    existing_map: dict[int, RaceResult] = {
        rr.user_id: rr for rr in existing_q.scalars().all()
    }

    # Валидируем: все пользователи в results должны быть зарегистрированы
    for item in results:
        if item.user_id not in existing_map:
            raise BadRequestException(
                detail=f"Пользователь {item.user_id} не зарегистрирован в этой гонке"
            )

    # Откатываем старые очки ТОЛЬКО для пользователей из нового списка результатов.
    # Это не затрагивает пользователей, которых нет в текущей отправке.
    if race.scores_awarded:
        for item in results:
            rr = existing_map.get(item.user_id)
            if rr and rr.position is not None:
                old_pts = points_for_position(rr.position)
                if old_pts != 0:
                    await session.execute(
                        update(User)
                        .where(User.id == item.user_id)
                        .values(score=User.score - old_pts)
                    )

    # Обновляем позиции
    for item in results:
        existing_map[item.user_id].position = item.position

    # Начисляем новые очки (включая отрицательные за DNS/DSQ)
    for item in results:
        pts = points_for_position(item.position)
        if pts != 0:
            await session.execute(
                update(User)
                .where(User.id == item.user_id)
                .values(score=User.score + pts)
            )

    race.scores_awarded = True
    await session.commit()


async def update_race(race_id: int, data: dict, session: AsyncSession):
    race = await get_race(race_id, session)

    for field, value in data.items():
        if value is not None:
            if isinstance(value, datetime):
                value = value.replace(tzinfo=None) + timedelta(hours=3)
            setattr(race, field, value)

    await session.commit()
    await session.refresh(race)
    return race


async def get_organizer_rating(organizer_id: int, session: AsyncSession) -> dict[str, int]:
    stmt = (
        select(
            func.sum(case((OrganizerReview.vote == 1, 1), else_=0)).label("likes"),
            func.sum(case((OrganizerReview.vote == -1, 1), else_=0)).label("dislikes"),
        ).where(OrganizerReview.organizer_id == organizer_id)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row:
        return {"likes": row.likes or 0, "dislikes": row.dislikes or 0}
    return {"likes": 0, "dislikes": 0}


async def get_organizer_ratings_bulk(
    organizer_ids: list[int], session: AsyncSession
) -> dict[int, dict[str, int]]:
    if not organizer_ids:
        return {}
    stmt = (
        select(
            OrganizerReview.organizer_id,
            func.sum(case((OrganizerReview.vote == 1, 1), else_=0)).label("likes"),
            func.sum(case((OrganizerReview.vote == -1, 1), else_=0)).label("dislikes"),
        )
        .where(OrganizerReview.organizer_id.in_(organizer_ids))
        .group_by(OrganizerReview.organizer_id)
    )
    result = await session.execute(stmt)
    ratings = {}
    for row in result:
        ratings[row.organizer_id] = {"likes": row.likes or 0, "dislikes": row.dislikes or 0}
    for oid in organizer_ids:
        if oid not in ratings:
            ratings[oid] = {"likes": 0, "dislikes": 0}
    return ratings


async def submit_review(race_id: int, voter_id: int, vote: int, session: AsyncSession):
    race = await get_race(race_id, session)

    if race.status != "Завершена":
        raise BadRequestException()

    if race.created_by == voter_id:
        raise BadRequestException()

    participant = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == race_id)
        .where(RaceResult.user_id == voter_id)
    )
    if participant.scalar_one_or_none() is None:
        raise ForbiddenException()

    existing = await session.execute(
        select(OrganizerReview)
        .where(OrganizerReview.race_id == race_id)
        .where(OrganizerReview.voter_id == voter_id)
    )
    review = existing.scalar_one_or_none()

    if review:
        review.vote = vote
    else:
        review = OrganizerReview(
            race_id=race_id, voter_id=voter_id,
            organizer_id=race.created_by, vote=vote,
        )
        session.add(review)

    await session.commit()
    await session.refresh(review)
    return review


async def delete_review(race_id: int, voter_id: int, session: AsyncSession):
    existing = await session.execute(
        select(OrganizerReview)
        .where(OrganizerReview.race_id == race_id)
        .where(OrganizerReview.voter_id == voter_id)
    )
    review = existing.scalar_one_or_none()
    if review is None:
        raise NotFoundException()
    await session.delete(review)
    await session.commit()