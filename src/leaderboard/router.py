from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.leaderboard.schemas import LeaderboardEntry
from src.leaderboard.service import get_leaderboard

router = APIRouter()

@router.get("/leaderboard", response_model=list[LeaderboardEntry], tags=["leaderboard"])
async def leaderboard(session: AsyncSession = Depends(get_session)):
    return await get_leaderboard(session)