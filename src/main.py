from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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

app.include_router(leaderboard_router, prefix="/auth/users", tags=["leaderboard"])
app.include_router(auth_router, prefix="/auth")
app.include_router(races_router, prefix="/races", tags=["races"])
app.include_router(news_router, prefix="/news", tags=["news"])

@app.get("/")
async def serve_index():
    return FileResponse("index.html")