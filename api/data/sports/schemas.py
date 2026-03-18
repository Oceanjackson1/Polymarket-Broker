# api/data/sports/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any


class SportsCategoryResponse(BaseModel):
    slug: str
    active_events: int


class SportsEventResponse(BaseModel):
    market_id: str
    sport_slug: str
    question: str
    outcomes: list
    status: str
    resolution: Any | None
    volume: float | None
    end_date: datetime | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedSportsEvents(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[SportsEventResponse]
    pagination: dict


class RealizedResponse(BaseModel):
    stale: bool
    data_updated_at: datetime
    data: dict
