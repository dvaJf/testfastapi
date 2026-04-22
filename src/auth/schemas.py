from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate



class UserCreate(BaseUserCreate):
    email: str
    score: int = 0


from typing import Optional

class UserRead(BaseUser[int]):
    email: str
    score: int
    nickname: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None

class UserUpdate(BaseUserUpdate):
    email: Optional[str] = None
    score: Optional[int] = None
    nickname: Optional[str] = None
    description: Optional[str] = None
    avatar_url: Optional[str] = None
