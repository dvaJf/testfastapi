from sqlalchemy import Column, Integer, String, DateTime, Text, Index
from src.database import Base
from datetime import datetime, UTC


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    created_by = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        Index('idx_news_created', 'created_at'),
    )