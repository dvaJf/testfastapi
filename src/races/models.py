from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from src.database import Base
from sqlalchemy.orm import relationship

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer,primary_key=True, autoincrement=True)
    name = Column(String)
    race = Column(String)
    time = Column(DateTime)
    maxuser = Column(Integer, default=20)
    users = Column(Integer, default=0)
    status = Column(String)
    about = Column(String)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    creator = relationship(
        "User",
        back_populates="created_races", 
        foreign_keys=[created_by]
    )
    results = relationship(
        "RaceResult",
        back_populates="race",
        foreign_keys="RaceResult.race_id"
    )
    
class RaceResult(Base):
    __tablename__ = "raceresult"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    position = Column(Integer, nullable=True)
    race = relationship(
        "Race",
        back_populates="results",
        foreign_keys=[race_id]
    )
    user = relationship(
        "User",
        back_populates="race_results",
        foreign_keys=[user_id]
    )