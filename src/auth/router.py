from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_users.db import SQLAlchemyUserDatabase
from src.auth.service import auth_backend, fastapi_users, UserManager
from src.auth.schemas import UserCreate, UserRead, UserUpdate
from src.auth.models import User
from src.auth.config import SECRET, ACCESS_TOKEN_EXPIRE
from src.database import session_maker
from src.config import settings
from fastapi_users.jwt import generate_jwt
import httpx

router = APIRouter()

# === Стандартные роутеры fastapi-users ===
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

# === DISCORD OAUTH ===

DISCORD_AUTH_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_API_URL = "https://discord.com/api/users/@me"

CALLBACK_URL = f"{settings.API_BASE_URL}/auth/discord/callback"

@router.get("/discord/authorize")
async def discord_authorize():
    params = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "redirect_uri": CALLBACK_URL,
        "response_type": "code",
        "scope": "identify",
    }
    query = urlencode(params)
    url = f"{DISCORD_AUTH_URL}?{query}"
    return RedirectResponse(url=url)

@router.get("/discord/callback")
async def discord_callback(code: str | None = None):
    if not code:
        raise HTTPException(status_code=400, detail="No code")
    
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            DISCORD_TOKEN_URL,
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": CALLBACK_URL,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Discord token exchange failed")
        
        discord_access_token = token_resp.json()["access_token"]
        
        user_resp = await client.get(
            DISCORD_API_URL,
            headers={"Authorization": f"Bearer {discord_access_token}"},
        )
        
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Discord user")
        
        discord_user = user_resp.json()
    
    discord_id = discord_user.get("id")
    username = discord_user.get("username")
    avatar = discord_user.get("avatar")
    
    if not username:
        raise HTTPException(status_code=400, detail="Discord username not available")
    
    fake_email = f"{username}@discord.local"
    
    async with session_maker() as session:
        user_db = SQLAlchemyUserDatabase(session, User)
        manager = UserManager(user_db)
        
        try:
            user = await manager.get_by_email(fake_email)
            user_exists = True
        except Exception:
            user_exists = False
        
        if not user_exists:
            user = await manager.create(
                UserCreate(
                    email=fake_email,
                    password=settings.SECRET + discord_id,
                    is_verified=False,
                    score=0,
                    nickname=username,
                )
            )
            if avatar:
                user.avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png"
            await session.commit()
        else:
            if username and not user.nickname:
                user.nickname = username
            if avatar and not user.avatar_url:
                user.avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png"
                await session.commit()
    
    token_data = {
        "sub": str(user.id),
        "aud": ["fastapi-users:auth"],
    }
    jwt_token = generate_jwt(token_data, SECRET, int(ACCESS_TOKEN_EXPIRE))
    
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/?access_token={jwt_token}",
        status_code=302
    )