from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from datetime import datetime
from src.races.models import Race, RaceResult
from typing import Optional
from src.exceptions import *

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
        time=time,
        maxuser=maxuser,
        status=status,
        created_by=created_by
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
        raise BadRequestException()

    for item in results:
        result = await session.execute(
            select(RaceResult)
            .where(RaceResult.race_id == race_id)
            .where(RaceResult.user_id == item.user_id)
        )
        race_result = result.scalar_one_or_none()

        if race_result is None:
            raise BadRequestException()

        race_result.position = item.position

    await session.commit()

async def update_race(race_id: int, data: dict, session: AsyncSession):
    race = await get_race(race_id, session)

    for field, value in data.items():
        if value is not None:
            setattr(race, field, value)

    await session.commit()
    await session.refresh(race)
    return race