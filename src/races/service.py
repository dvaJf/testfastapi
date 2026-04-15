from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, case 
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from src.races.models import Race, RaceResult, OrganizerReview
from src.auth.models import User
from typing import Optional
from src.exceptions import *

pos = {1: 30, 2: 25, 3: 20, 4: 17, 5: 16, 6: 15, 7: 14, 8: 13, 9: 12, 10: 11, 11: 10, 12: 9, 13: 8, 14: 7, 15: 6, 16: 5, 17: 4, 18: 3, 19: 2, 20: 1}
def points_for_position(position: int) -> int:
    return pos.get(position, 0)

async def get_all_races_with_creator(session: AsyncSession):
    result = await session.execute(
        select(Race).options(selectinload(Race.creator))
    )
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

async def create_race(name: str, race: str, about: Optional[str], time: datetime, maxuser: int, status: str, created_by: int, session: AsyncSession):
    new_race = Race(
        name=name,
        race=race,
        about=about,
        time=time.replace(tzinfo=None),
        maxuser=maxuser,
        status=status,
        created_by=created_by,
        scores_awarded=False
    )
    session.add(new_race)
    await session.commit()
    await session.refresh(new_race)
    return new_race

async def get_all_users(id: int, session: AsyncSession):
    result = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .options(selectinload(RaceResult.user))
    )
    return result.scalars().all()

async def get_results(id: int, session: AsyncSession):
    result = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.position.isnot(None))
        .options(selectinload(RaceResult.user))
        .order_by(RaceResult.position)
    )
    return result.scalars().all()

async def register_user(id: int, user_id: int, session: AsyncSession):
    race = await get_race(id, session)

    if race.status != "Регистрация":
        raise BadRequestException()

    if race.users >= race.maxuser:
        raise BadRequestException()

    existing = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise BadRequestException()

    race_result = RaceResult(race_id=id, user_id=user_id)
    session.add(race_result)
    await session.execute(
        update(Race).where(Race.id == id).values(users=Race.users + 1)
    )
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
    await session.execute(
        update(Race).where(Race.id == id).values(users=Race.users - 1)
    )
    await session.delete(race_result)
    await session.commit()

async def set_results(race_id: int, results: list, session: AsyncSession):
    race = await get_race(race_id, session)
    if race.status != "Завершена":
        raise BadRequestException()

    positions = [r.position for r in results]
    if len(positions) != len(set(positions)):
        raise BadRequestException(detail="Позиции участников должны быть уникальными")


    existing_q = await session.execute(
        select(RaceResult).where(RaceResult.race_id == race_id)
    )
    existing_map: dict[int, RaceResult] = {
        rr.user_id: rr for rr in existing_q.scalars().all()
    }

    if race.scores_awarded:
        for user_id, rr in existing_map.items():
            if rr.position is not None:
                old_pts = points_for_position(rr.position)
                if old_pts > 0:
                    await session.execute(
                        update(User)
                        .where(User.id == user_id)
                        .values(score=User.score - old_pts)
                    )

    # Обновляем позиции
    for item in results:
        race_result = existing_map.get(item.user_id)
        if race_result is None:
            raise BadRequestException(detail=f"Пользователь {item.user_id} не зарегистрирован в этой гонке")
        race_result.position = item.position

    # Начисляем новые очки всем участникам
    for item in results:
        pts = points_for_position(item.position)
        if pts > 0:
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

async def get_organizer_rating(
    organizer_id: int,
    session: AsyncSession
) -> dict[str, int]:
    stmt = (
        select(
            func.sum(case((OrganizerReview.vote == 1, 1), else_=0)).label("likes"),
            func.sum(case((OrganizerReview.vote == -1, 1), else_=0)).label("dislikes"),
        )
        .where(OrganizerReview.organizer_id == organizer_id)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if row:
        return {"likes": row.likes or 0, "dislikes": row.dislikes or 0}
    return {"likes": 0, "dislikes": 0}


async def get_organizer_ratings_bulk(
    organizer_ids: list[int],
    session: AsyncSession
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
        ratings[row.organizer_id] = {
            "likes": row.likes or 0,
            "dislikes": row.dislikes or 0
        }
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
            race_id=race_id,
            voter_id=voter_id,
            organizer_id=race.created_by,
            vote=vote,
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