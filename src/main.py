from contextlib import asynccontextmanager
from fastapi import APIRouter, Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional

from src.auth.router import router as auth_router
from src.races.router import router as races_router
from src.auth.utils import create_first_admin
from src.config import settings
from src.database import engine, Base, get_session
from src.auth.models import User
from src.races.models import RaceResult
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    if settings.FIRST_ADMIN_EMAIL:
        await create_first_admin(settings.FIRST_ADMIN_EMAIL)
    
    yield


class LeaderboardEntry(BaseModel):
    position: int
    user_id: int
    email: str
    score: int
    races_completed: Optional[int] = 0
    best_position: Optional[int] = None


async def get_leaderboard(session: AsyncSession = Depends(get_session)):
    users_q = await session.execute(
        select(User).order_by(User.score.desc())
    )
    users = users_q.scalars().all()

    stats_q = await session.execute(
        select(
            RaceResult.user_id,
            func.count(RaceResult.id).label("races_completed"),
            func.min(RaceResult.position).label("best_position"),
        )
        .where(RaceResult.position.isnot(None))
        .group_by(RaceResult.user_id)
    )
    stats_map = {
        row.user_id: {
            "races_completed": row.races_completed,
            "best_position": row.best_position,
        }
        for row in stats_q
    }

    return [
        LeaderboardEntry(
            position=idx + 1,
            user_id=u.id,
            email=u.email,
            score=u.score,
            races_completed=stats_map.get(u.id, {}).get("races_completed", 0),
            best_position=stats_map.get(u.id, {}).get("best_position"),
        )
        for idx, u in enumerate(users)
    ]


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.get("/auth/users/leaderboard", response_model=list[LeaderboardEntry], tags=["users"])(get_leaderboard)
app.include_router(auth_router, prefix="/auth")
app.include_router(races_router, prefix="/races",tags=["races"])

@app.get("/")
async def serve_index():
    return FileResponse("index.html")