from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Create async engine with connection pooling and performance optimizations
engine = create_async_engine(
    settings.DATABASE_URL,
    # Connection pool settings
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    # Echo SQL in development for debugging
    echo=settings.ENVIRONMENT == "development",
)

session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()