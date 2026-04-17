from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List
from src.news.models import News
from src.exceptions import NotFoundException
from datetime import datetime, timedelta

async def get_all_news(session: AsyncSession) -> List[News]:
    query = select(News).order_by(desc(News.created_at))
    result = await session.execute(query)
    return result.scalars().all()


async def get_news_by_id(news_id: int, session: AsyncSession) -> News:
    result = await session.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if news is None:
        raise NotFoundException("Новость не найдена")
    return news


async def create_news(
    title: str,
    content: str,
    summary: Optional[str],
    image_url: Optional[str],
    created_by: int,
    session: AsyncSession
) -> News:
    news = News(
        title=title,
        content=content,
        summary=summary,
        image_url=image_url,
        created_by=created_by,
        created_at=datetime.utcnow()+timedelta(hours=3)
    )
    session.add(news)
    await session.commit()
    await session.refresh(news)
    return news


async def update_news(
    news_id: int,
    data: dict,
    session: AsyncSession
) -> News:
    news = await get_news_by_id(news_id, session)
    
    for field, value in data.items():
        if value is not None:
            setattr(news, field, value)
    
    await session.commit()
    await session.refresh(news)
    return news


async def delete_news(news_id: int, session: AsyncSession) -> None:
    news = await get_news_by_id(news_id, session)
    await session.delete(news)
    await session.commit()