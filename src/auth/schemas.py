import uuid
from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate

class UserRead(BaseUser[uuid.UUID]):
    score: int

class UserCreate(BaseUserCreate):
    score: int = 0

class UserUpdate(BaseUserUpdate):
    score: int | None = None