# api/data/nba/schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from typing import Any


class NbaGameResponse(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    game_date: date
    game_status: str
    score_home: int | None
    score_away: int | None
    quarter: int | None
    time_remaining: str | None
    market_id: str | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class NbaGameDetailResponse(BaseModel):
    stale: bool
    data_updated_at: datetime
    data: NbaGameResponse


class NbaFusionResponse(BaseModel):
    game_id: str
    score: dict
    polymarket: dict
    bias_signal: dict
    stale: bool
    data_updated_at: datetime


class PaginatedNbaGames(BaseModel):
    data: list[NbaGameResponse]
    pagination: dict
