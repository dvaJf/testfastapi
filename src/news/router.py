from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_session
from src.auth.service import fastapi_users
from src.auth.models import User
from src.news import service
from src.news.schemas import NewsCreate, NewsUpdate, NewsOut, NewsShort
from src.exceptions import ForbiddenException

current_user = fastapi_users.current_user()

router = APIRouter()


@router.get("/", response_model=List[NewsShort])
async def list_news(
    session: AsyncSession = Depends(get_session),
):
    news_list = await service.get_all_news(session)
    return news_list


@router.get("/{news_id}", response_model=NewsOut)
async def get_news(
    news_id: int,
    session: AsyncSession = Depends(get_session),
):
    news = await service.get_news_by_id(news_id, session)
    return news


@router.post("/", response_model=NewsOut, status_code=status.HTTP_201_CREATED)
async def create_news(
    news_data: NewsCreate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException("Только администраторы могут создавать новости")
    
    news = await service.create_news(
        title=news_data.title,
        content=news_data.content,
        summary=news_data.summary,
        image_url=news_data.image_url,
        created_by=user.id,
        session=session
    )
    return news


@router.patch("/{news_id}", response_model=NewsOut)
async def update_news(
    news_id: int,
    news_data: NewsUpdate,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException("Только администраторы могут редактировать новости")
    
    news = await service.update_news(
        news_id=news_id,
        data=news_data.model_dump(exclude_none=True),
        session=session
    )
    return news


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(
    news_id: int,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
):
    if not user.is_superuser:
        raise ForbiddenException("Только администраторы могут удалять новости")
    
    await service.delete_news(news_id, session)