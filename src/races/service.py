from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from src.races.models import Race, RaceResult
from src.races.exceptions import (
    RaceNotFoundException,
    AlreadyRegisteredException,
    NotRegisteredException,
    RaceFullException,
    RegistrationClosedException,
)

async def get_all_races(session: AsyncSession):
    query = select(Race)
    result = await session.execute(query)
    return result.scalars().all()

async def get_race(id: int, session: AsyncSession):
    result = await session.execute(select(Race).where(Race.id == id))
    race = result.scalar_one_or_none()
    if race is None:
        raise RaceNotFoundException
    return race

async def get_count_users(id: int, session: AsyncSession):
    result = await session.execute(
        select(func.count())
        .where(RaceResult.race_id == id)
    )
    return result.scalar()

async def create_race(name: str, race: str, about: Optional[str], time: datetime, maxuser: int, status: str, created_by: str, session: AsyncSession):
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

async def register_user(id: int, user_id: str, session: AsyncSession):
    race = await get_race(id, session)

    if race.status != "Регистрация":
        raise RegistrationClosedException
    
    current = await get_count_users(id, session)
    if current >= race.maxuser:
        raise RaceFullException

    existing = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise AlreadyRegisteredException

    race_result = RaceResult(race_id=id, user_id=user_id)
    session.add(race_result)
    await session.commit()
    return race_result


async def unregister_user(id: int, user_id: str, session: AsyncSession):
    race = await get_race(id, session)
    
    if race.status != "Регистрация":
        raise RegistrationClosedException

    result = await session.execute(
        select(RaceResult)
        .where(RaceResult.race_id == id)
        .where(RaceResult.user_id == user_id)
    )
    race_result = result.scalar_one_or_none()
    if race_result is None:
        raise NotRegisteredException

    await session.delete(race_result)
    await session.commit()