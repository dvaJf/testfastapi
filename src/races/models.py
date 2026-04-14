from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from src.database import Base
from sqlalchemy.orm import relationship

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    race = Column(String)
    time = Column(DateTime)
    maxuser = Column(Integer, default=20)
    users = Column(Integer, default=0)
    status = Column(String)
    about = Column(String)
    created_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    creator = relationship("User", back_populates="created_races")
    results = relationship("RaceResult", back_populates="race")
    
class RaceResult(Base):
    __tablename__ = "raceresult"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    position = Column(Integer, nullable=True)
    race = relationship("Race", back_populates="results")
    user = relationship("User", back_populates="race_results")