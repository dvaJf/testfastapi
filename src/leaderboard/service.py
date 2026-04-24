from sqlalchemy import select, func, case

async def get_leaderboard(session):
    users_q = await session.execute(select(User).order_by(User.score.desc()))
    users = users_q.scalars().all()

    stats_q = await session.execute(
        select(
            RaceResult.user_id,
            func.count(RaceResult.id).label("races_completed"),
            func.min(case((RaceResult.position > 0, RaceResult.position), else_=None)).label("best_position")  # ← только положительные
        )
        .where(RaceResult.position.isnot(None))
        .group_by(RaceResult.user_id)
    )
    stats_map = {
        row.user_id: {"races_completed": row.races_completed, "best_position": row.best_position} for row in stats_q
    }

    return [
        {
            "position": idx + 1,
            "user_id": u.id,
            "email": u.email,
            "score": u.score,
            "avatar_url": u.avatar_url,
            "nickname": u.nickname,
            **stats_map.get(u.id, {"races_completed": 0, "best_position": None}),
        }
        for idx, u in enumerate(users)
    ]