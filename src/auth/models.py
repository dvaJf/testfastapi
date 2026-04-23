from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Text
from src.database import Base
from fastapi_users.db import SQLAlchemyBaseUserTable

class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "user"
    
    email = Column(String(100), nullable=False, unique=True)
    id = Column(Integer, primary_key=True, autoincrement=True)
    score = Column(Integer, default=0)
    nickname = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    hashed_password = Column(String(500), nullable=False)
    is_active = Column(Integer, default=1)
    is_superuser = Column(Integer, default=0)
    is_verified = Column(Integer, default=0)
    
    race_results = relationship("RaceResult", back_populates="user")
    created_races = relationship("Race", back_populates="creator")
    given_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.voter_id", back_populates="voter")
    received_reviews = relationship("OrganizerReview", foreign_keys="OrganizerReview.organizer_id", back_populates="organizer")