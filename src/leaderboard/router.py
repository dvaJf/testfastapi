from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session
from src.leaderboard.schemas import LeaderboardEntry
from src.leaderboard.service import get_leaderboard
from src.auth.models import User
from src.races.models import RaceResult
from sqlalchemy import select, func
from fastapi import HTTPException

router = APIRouter()

@router.get("/leaderboard", response_model=list[LeaderboardEntry], tags=["leaderboard"])
async def leaderboard(session: AsyncSession = Depends(get_session)):
    return await get_leaderboard(session)


@router.get("/{user_id}/public")
async def get_public_profile(user_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count_q = await session.execute(
        select(func.count(RaceResult.id).label("races_completed"))
        .where(RaceResult.user_id == user_id)
        .where(RaceResult.position.isnot(None))
    )
    best_q = await session.execute(
        select(func.min(RaceResult.position).label("best_position"))
        .where(RaceResult.user_id == user_id)
        .where(RaceResult.position.isnot(None))
        .where(RaceResult.position > 0)
    )
    races_completed = count_q.scalar() or 0
    best_position = best_q.scalar()

    return {
    "id": user.id,
    "email": user.email,
    "score": user.score,
    "is_superuser": user.is_superuser,
    "is_verified": user.is_verified,
    "races_completed": races_completed,
    "best_position": best_position,
    "nickname": user.nickname,
    "description": user.description,
    "avatar_url": user.avatar_url,
}