from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from typing import Optional
from pydantic import field_validator

class UserCreate(BaseUserCreate):
    email: str
    score: int = 0
    nickname: Optional[str] = None

    @field_validator('email')
    @classmethod
    def allow_any_email(cls, v):
        # Разрешаем любую строку как "email" (никнейм)
        return v

class UserRead(BaseUser[int]):
    email: str
    score: int
    nickname: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class UserUpdate(BaseUserUpdate):
    score: Optional[int] = None
    nickname: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None