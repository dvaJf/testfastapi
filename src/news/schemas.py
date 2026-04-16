from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class NewsBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    image_url: Optional[str] = None


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None


class NewsOut(NewsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: int
    model_config = ConfigDict(from_attributes=True)


class NewsShort(BaseModel):
    id: int
    title: str
    summary: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)