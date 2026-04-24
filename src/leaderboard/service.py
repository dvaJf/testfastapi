from sqlalchemy import select, func
from src.auth.models import User
from src.races.models import RaceResult


async def get_leaderboard(session):
    # Загружаем всех пользователей
    users_q = await session.execute(select(User))
    users = users_q.scalars().all()

    # Все гонки с результатом (для подсчёта количества)
    count_q = await session.execute(
        select(
            RaceResult.user_id,
            func.count(RaceResult.id).label("races_completed")
        )
        .where(RaceResult.position.isnot(None))
        .group_by(RaceResult.user_id)
    )
    count_map = {row.user_id: row.races_completed for row in count_q}

    # Лучшая позиция только среди реальных финишей (> 0)
    best_q = await session.execute(
    select(
        RaceResult.user_id,
        func.min(RaceResult.position).label("best_position")
    )
    .where(RaceResult.position.isnot(None))
    .where(RaceResult.position.between(1, 20))  # только реальные финиши
    .group_by(RaceResult.user_id)
)
    best_map = {row.user_id: row.best_position for row in best_q}

    # Собираем записи только для пилотов с 5+ гонками, считаем среднее
    entries = []
    for u in users:
        races_completed = count_map.get(u.id, 0) or 0
        if races_completed < 1:
            continue
        avg_score = round(u.score / races_completed, 2) if races_completed > 0 else 0.0
        entries.append({
            "user_id": u.id,
            "email": u.email,
            "score": u.score,
            "avatar_url": u.avatar_url,
            "nickname": u.nickname,
            "races_completed": races_completed,
            "best_position": best_map.get(u.id),
            "avg_score": avg_score,
        })

    # Сортируем по среднему очку за гонку (убывание)
    entries.sort(key=lambda x: (-x["avg_score"], -x["score"], x["best_position"] or 999))

    # Проставляем позиции
    for idx, entry in enumerate(entries):
        entry["position"] = idx + 1

    return entries