from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.auth.router import router as auth_router
from src.races.router import router as races_router
from src.news.router import router as news_router
from src.leaderboard.router import router as leaderboard_router
from src.auth.utils import create_first_admin
from src.config import settings
from src.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    if settings.FIRST_ADMIN_EMAIL:
        await create_first_admin(settings.FIRST_ADMIN_EMAIL)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers


# Static files (CSS, JS assets)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


# ==========================================
# PAGE ROUTES
# ==========================================

@app.get("/")
async def serve_index():
    return FileResponse("frontend/index.html")


@app.get("/news")
async def serve_news():
    return FileResponse("frontend/news.html")


@app.get("/news/{news_id:int}")
async def serve_news_detail(news_id: int):
    return FileResponse("frontend/news-detail.html")


@app.get("/races/{race_id:int}")
async def serve_race_detail(race_id: int):
    return FileResponse("frontend/race-detail.html")


@app.get("/download")
async def serve_download():
    return FileResponse("frontend/download.html")


@app.get("/rating")
async def serve_rating():
    return FileResponse("frontend/rating.html")


@app.get("/info")
async def serve_info():
    return FileResponse("frontend/info.html")


@app.get("/profile")
async def serve_profile():
    return FileResponse("frontend/profile.html")

app.include_router(leaderboard_router, prefix="/api/auth/users", tags=["leaderboard"])
app.include_router(auth_router,        prefix="/api/auth")
app.include_router(races_router,       prefix="/api/races",      tags=["races"])
app.include_router(news_router,        prefix="/api/news",       tags=["news"])