from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.auth.router import router as auth_router
from src.races.router import router as races_router
from src.news.router import router as news_router
from src.leaderboard.router import router as leaderboard_router
from src.bets.router import router as bets_router
from src.auth.utils import create_first_admin
from src.config import settings
from src.database import engine, Base

import json
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

class DiscordOAuthRedirectMiddleware(BaseHTTPMiddleware):
    """Перехватывает JSON-ответ от /api/auth/discord/callback и редиректит на фронт с токеном в URL"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Проверяем только callback Discord OAuth
        if request.url.path != "/api/auth/discord/callback":
            return response
        
        # Проверяем что ответ успешный и содержит JSON
        if response.status_code != 200:
            return response
            
        # Читаем тело ответа
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        try:
            data = json.loads(body)
            access_token = data.get("access_token")
            
            if access_token:
                # Редиректим на фронт с токеном в query params
                frontend_url = settings.FRONTEND_URL
                redirect_url = f"{frontend_url}/?access_token={access_token}"
                return RedirectResponse(url=redirect_url, status_code=302)
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Если что-то пошло не так — возвращаем оригинальный ответ
        # Нужно восстановить response, т.к. мы уже прочитали body
        from starlette.responses import Response
        return Response(content=body, status_code=response.status_code, headers=dict(response.headers))



@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.FIRST_ADMIN_EMAIL:
        await create_first_admin(settings.FIRST_ADMIN_EMAIL)
    yield


app = FastAPI(lifespan=lifespan)
# Configure CORS based on environment
if settings.ENVIRONMENT == "production":
    # In production, restrict origins to your frontend domain
    origins = [
        settings.FRONTEND_URL,
        # Add other production origins as needed
    ]
else:
    # In development, allow all origins for convenience
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(DiscordOAuthRedirectMiddleware)
# API routers


import os
from pathlib import Path

# Get the base directory for more reliable path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Static files (CSS, JS assets)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


# ==========================================
# PAGE ROUTES
# ==========================================

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/api/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy"}


@app.get("/news", include_in_schema=False)
async def serve_news():
    return FileResponse(FRONTEND_DIR / "news.html")


@app.get("/news/{news_id:int}", include_in_schema=False)
async def serve_news_detail(news_id: int):
    return FileResponse(FRONTEND_DIR / "news-detail.html")


@app.get("/races/{race_id:int}", include_in_schema=False)
async def serve_race_detail(race_id: int):
    return FileResponse(FRONTEND_DIR / "race-detail.html")


@app.get("/download", include_in_schema=False)
async def serve_download():
    return FileResponse(FRONTEND_DIR / "download.html")


@app.get("/rating", include_in_schema=False)
async def serve_rating():
    return FileResponse(FRONTEND_DIR / "rating.html")


@app.get("/info", include_in_schema=False)
async def serve_info():
    return FileResponse(FRONTEND_DIR / "info.html")


@app.get("/profile", include_in_schema=False)
async def serve_profile():
    return FileResponse(FRONTEND_DIR / "profile.html")

@app.get("/bets", include_in_schema=False)
async def serve_bets():
    return FileResponse(FRONTEND_DIR / "bets.html")

app.include_router(leaderboard_router, prefix="/api/auth/users", tags=["leaderboard"])
app.include_router(bets_router, prefix="/api/bets", tags=["bets"])
app.include_router(auth_router,        prefix="/api/auth")
app.include_router(races_router,       prefix="/api/races",      tags=["races"])
app.include_router(news_router,        prefix="/api/news",       tags=["news"])