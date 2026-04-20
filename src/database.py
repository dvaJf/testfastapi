from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.config import settings

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.DATABASE_URL)
session_maker = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
    async with session_maker() as session:
        yield session