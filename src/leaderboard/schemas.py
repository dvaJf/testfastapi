from pydantic import BaseModel
from typing import Optional

class LeaderboardEntry(BaseModel):
    position: int
    user_id: int
    email: str
    score: int
    races_completed: Optional[int] = 0
    best_position: Optional[int] = None
    avatar_url: Optional[str] = None
    nickname: Optional[str] = None