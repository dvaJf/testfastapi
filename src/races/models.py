from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
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
    created_by = Column(Integer, ForeignKey("user.id"))
    scores_awarded = Column(Boolean, default=False)
    creator = relationship("User", back_populates="created_races")
    results = relationship("RaceResult", back_populates="race")
    reviews = relationship("OrganizerReview", back_populates="race")


class RaceResult(Base):
    __tablename__ = "raceresult"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    position = Column(Integer, nullable=True)
    race = relationship("Race", back_populates="results")
    user = relationship("User", back_populates="race_results")


class OrganizerReview(Base):
    __tablename__ = "organizer_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"))
    voter_id = Column(Integer, ForeignKey("user.id"))
    organizer_id = Column(Integer, ForeignKey("user.id"))
    vote = Column(Integer)
    __table_args__ = (UniqueConstraint("race_id", "voter_id", name="uq_review_race_voter"),)
    race = relationship("Race", back_populates="reviews")
    voter = relationship("User", foreign_keys=[voter_id], back_populates="given_reviews")
    organizer = relationship("User", foreign_keys=[organizer_id], back_populates="received_reviews")