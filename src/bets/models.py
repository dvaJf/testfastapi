from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from src.database import Base
from datetime import datetime, UTC


class Bet(Base):
    __tablename__ = "bets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_by = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    closes_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(50), default="открыта", index=True)
    winning_option_id = Column(Integer, nullable=True)

    creator = relationship("User", back_populates="created_bets")
    options = relationship("BetOption", back_populates="bet", cascade="all, delete-orphan", foreign_keys="[BetOption.bet_id]")
    user_bets = relationship("UserBet", back_populates="bet", cascade="all, delete-orphan")


class BetOption(Base):
    __tablename__ = "bet_options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bet_id = Column(Integer, ForeignKey("bets.id"), index=True, nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    bet = relationship("Bet", back_populates="options")
    user_bets = relationship("UserBet", back_populates="option")

    __table_args__ = (
        UniqueConstraint("bet_id", "label", name="uq_bet_option_label"),
    )


class UserBet(Base):
    __tablename__ = "user_bets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bet_id = Column(Integer, ForeignKey("bets.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    option_id = Column(Integer, ForeignKey("bet_options.id"), index=True, nullable=False)
    stake = Column(Integer, nullable=False)
    placed_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    bet = relationship("Bet", back_populates="user_bets")
    user = relationship("User", back_populates="user_bets")
    option = relationship("BetOption", back_populates="user_bets")

    __table_args__ = (
        UniqueConstraint("bet_id", "user_id", name="uq_user_bet"),
    )
