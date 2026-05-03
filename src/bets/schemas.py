from pydantic import BaseModel, ConfigDict, field_validator, Field
from datetime import datetime
from typing import Optional


class BetOptionCreate(BaseModel):
    label: str
    description: Optional[str] = None


class BetOptionOut(BaseModel):
    id: int
    bet_id: int
    label: str
    description: Optional[str] = None
    total_stakes: int = 0

    model_config = ConfigDict(from_attributes=True)


class BetCreate(BaseModel):
    title: str
    description: Optional[str] = None
    closes_at: datetime
    options: list[BetOptionCreate]


class BetOptionUpdate(BaseModel):
    id: Optional[int] = None
    label: str
    description: Optional[str] = None


class BetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    closes_at: Optional[datetime] = None
    status: Optional[str] = None
    options: Optional[list[BetOptionUpdate]] = None


class BetShort(BaseModel):
    id: int
    title: str
    status: str
    closes_at: datetime
    creator_email: Optional[str] = None
    total_pool: int = 0
    options_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class BetOut(BetShort):
    description: Optional[str] = None
    created_at: datetime
    created_by: int
    winning_option_id: Optional[int] = None
    options: list[BetOptionOut] = []

    model_config = ConfigDict(from_attributes=True)


class UserBetCreate(BaseModel):
    option_id: int
    stake: int = Field(ge=1)

    @field_validator("stake")
    @classmethod
    def stake_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Ставка должна быть не менее 1 очка")
        return v


class UserBetOut(BaseModel):
    id: int
    bet_id: int
    option_id: int
    option_label: str
    stake: int
    placed_at: datetime
    username: str

    model_config = ConfigDict(from_attributes=True)


class BetResolve(BaseModel):
    winning_option_id: int
