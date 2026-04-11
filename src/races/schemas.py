from pydantic import BaseModel,  ConfigDict
from datetime import datetime
from typing import Optional,Literal
RaceStatus = Literal["Регистрация", "Завершена", "Отменена"]

class RaceShort(BaseModel):
    id: int
    name: str
    race: str
    time: datetime
    status: str
    maxuser: int
    users: int
    model_config = ConfigDict(from_attributes=True)

class RaceOut(BaseModel):
    id: int
    name: str
    race: str
    about: Optional[str]
    time: datetime
    status: str
    maxuser: int
    users: int
    model_config = ConfigDict(from_attributes=True)

class RaceCreate(BaseModel):
    name: str
    race: str
    about: Optional[str] = None
    time: datetime
    maxuser: int = 20
    status: RaceStatus = "Регистрация"

class RaceResultOut(BaseModel):
    user_id: int
    username: str
    position: Optional[int]    
    model_config = ConfigDict(from_attributes=True)
        
class RaceResultsOut(BaseModel):
    race_id: int
    race_name: str
    results: list[RaceResultOut]

class SetResultItem(BaseModel):
    user_id: int
    position: int

class SetResultsIn(BaseModel):
    results: list[SetResultItem]

class RaceUpdate(BaseModel):
    name: Optional[str] = None
    race: Optional[str] = None
    about: Optional[str] = None
    time: Optional[datetime] = None
    maxuser: Optional[int] = None
    status: Optional[RaceStatus] = None