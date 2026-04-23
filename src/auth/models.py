from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer,String, Text
from src.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTable

class User(SQLAlchemyBaseUserTable[int], Base):
    email = Column(String)
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, default=0)
    nickname = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    race_results = relationship("RaceResult", back_populates="user")
    created_races = relationship("Race", back_populates="creator")
    given_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.voter_id",back_populates="voter")
    received_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.organizer_id", back_populates="organizer") 