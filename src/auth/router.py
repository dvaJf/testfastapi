from src.auth.schemas import UserCreate, UserRead, UserUpdate
from src.auth.service import auth_backend, fastapi_users
from fastapi import APIRouter
router = APIRouter()

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    tags=["auth"],
)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)