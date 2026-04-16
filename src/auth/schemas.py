from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate

class UserRead(BaseUser[int]):
    email: str
    score: int

class UserCreate(BaseUserCreate):
    email: str
    score: int = 0

class UserUpdate(BaseUserUpdate):
    email: str | None = None
    score: int | None = None