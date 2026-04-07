from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, Integer
from src.database import Base

class User(SQLAlchemyBaseUserTableUUID, Base):
    score = Column(Integer, default=0)