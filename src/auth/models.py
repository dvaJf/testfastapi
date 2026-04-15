from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer
from src.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTable

class User(SQLAlchemyBaseUserTable[int], Base):
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, default=0)
    race_results = relationship("RaceResult", back_populates="user")
    created_races = relationship("Race", back_populates="creator")
    given_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.voter_id",back_populates="voter")
    received_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.organizer_id", back_populates="organizer")