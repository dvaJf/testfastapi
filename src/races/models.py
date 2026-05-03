from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint, Index
from src.database import Base
from sqlalchemy.orm import relationship

class Race(Base):
    __tablename__ = "races"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    race = Column(String(100))
    time = Column(DateTime)
    maxuser = Column(Integer, default=20)
    users = Column(Integer, default=0)
    status = Column(String(50))
    about = Column(String)
    created_by = Column(Integer, ForeignKey("user.id"), index=True)
    scores_awarded = Column(Boolean, default=False)
    creator = relationship("User", back_populates="created_races")
    results = relationship("RaceResult", back_populates="race")
    reviews = relationship("OrganizerReview", back_populates="race")

    __table_args__ = (
        Index('idx_race_status', 'status'),
        Index('idx_race_time', 'time'),
    )


class RaceResult(Base):
    __tablename__ = "raceresult"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    user_id = Column(Integer, ForeignKey("user.id"), index=True)
    position = Column(Integer, nullable=True)
    race = relationship("Race", back_populates="results")
    user = relationship("User", back_populates="race_results")

    __table_args__ = (
        Index('idx_result_race', 'race_id'),
        Index('idx_result_user', 'user_id'),
        Index('idx_result_position', 'position'),
    )


class OrganizerReview(Base):
    __tablename__ = "organizer_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, ForeignKey("races.id"), index=True)
    voter_id = Column(Integer, ForeignKey("user.id"), index=True)
    organizer_id = Column(Integer, ForeignKey("user.id"), index=True)
    vote = Column(Integer)
    __table_args__ = (
        UniqueConstraint("race_id", "voter_id", name="uq_review_race_voter"),
        Index('idx_review_organizer', 'organizer_id'),
    )
    race = relationship("Race", back_populates="reviews")
    voter = relationship("User", foreign_keys=[voter_id], back_populates="given_reviews")
    organizer = relationship("User", foreign_keys=[organizer_id], back_populates="received_reviews")