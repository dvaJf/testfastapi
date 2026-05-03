from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload
from src.auth.models import User
from src.races.models import RaceResult


async def get_leaderboard(session, limit: int = 100):
    # Оптимизированный запрос с агрегацией в БД
    query = (
        select(
            User.id,
            User.email,
            User.score,
            User.avatar_url,
            User.nickname,
            func.count(RaceResult.id).label("races_completed"),
            func.min(
                case(
                    (RaceResult.position.between(1, 20), RaceResult.position),
                    else_=None
                )
            ).label("best_position")
        )
        .outerjoin(RaceResult, (RaceResult.user_id == User.id) & (RaceResult.position.isnot(None)))
        .group_by(User.id, User.email, User.score, User.avatar_url, User.nickname)
        .having(func.count(RaceResult.id) >= 1)
        .order_by(
            (User.score / func.nullif(func.count(RaceResult.id), 0)).desc(),
            User.score.desc()
        )
        .limit(limit)
    )

    result = await session.execute(query)
    rows = result.all()

    entries = []
    for idx, row in enumerate(rows, 1):
        races_completed = row.races_completed or 0
        avg_score = round(row.score / races_completed, 2) if races_completed > 0 else 0.0
        entries.append({
            "user_id": row.id,
            "email": row.email,
            "score": row.score,
            "avatar_url": row.avatar_url,
            "nickname": row.nickname,
            "races_completed": races_completed,
            "best_position": row.best_position,
            "avg_score": avg_score,
            "position": idx,
        })

    return entries
