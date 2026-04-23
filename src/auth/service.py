from fastapi import Depends
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.manager import BaseUserManager, IntegerIDMixin
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.config import SECRET, ACCESS_TOKEN_EXPIRE
from src.auth.models import User
from src.database import get_session
from httpx_oauth.clients.discord import DiscordOAuth2
from src.config import settings

discord_oauth_client = DiscordOAuth2(
    settings.DISCORD_CLIENT_ID,
    settings.DISCORD_CLIENT_SECRET,
)

async def get_user_db(session: AsyncSession = Depends(get_session)):
    yield SQLAlchemyUserDatabase(session, User)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET
    
    # Отключаем валидацию email
    async def validate_password(self, password: str, user) -> None:
        # Минимальная валидация пароля
        if len(password) < 3:
            raise ValueError("Пароль слишком короткий")
    
    async def create(self, user_create, safe: bool = False, request=None):
        # Переопределяем создание, чтобы не валидировать email
        return await super().create(user_create, safe=safe, request=request)


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=BearerTransport(tokenUrl="/auth/login"),
    get_strategy=lambda: JWTStrategy(secret=SECRET, lifetime_seconds=ACCESS_TOKEN_EXPIRE),
)

fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])