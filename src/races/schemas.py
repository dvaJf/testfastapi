from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RaceShort(BaseModel):
    id: int
    name: str
    race: str
    time: datetime
    status: str
    maxuser: int
    users: int
    class Config:
        from_attributes = True

class RaceOut(BaseModel):
    id: int
    name: str
    race: str
    about: Optional[str]
    time: datetime
    status: str
    maxuser: int
    users: int
    class Config:
        from_attributes = True

class RaceCreate(BaseModel):
    name: str
    race: str
    about: Optional[str] = None
    time: datetime
    maxuser: int = 20
    status: str = "Регистрация"

class RaceResultOut(BaseModel):
    user_id: int
    username: str
    position: Optional[int]    
    class Config:
        from_attributes = True
        
class RaceResultsOut(BaseModel):
    race_id: int
    race_name: str
    results: list[RaceResultOut]