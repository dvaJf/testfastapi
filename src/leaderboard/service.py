from sqlalchemy import select, func
from src.auth.models import User
from src.races.models import RaceResult


async def get_leaderboard(session):
    users_q = await session.execute(select(User).order_by(User.score.desc()))
    users = users_q.scalars().all()

    stats_q = await session.execute(
        select(RaceResult.user_id, func.count(RaceResult.id).label("races_completed"), func.min(RaceResult.position).label("best_position")).where(RaceResult.position.isnot(None)).group_by(RaceResult.user_id))
    stats_map = {
        row.user_id: {"races_completed": row.races_completed, "best_position": row.best_position} for row in stats_q}

    return [{"position": idx + 1, "user_id": u.id, "email": u.email, "score": u.score, **stats_map.get(u.id, {"races_completed": 0, "best_position": None}), } for idx, u in enumerate(users)]