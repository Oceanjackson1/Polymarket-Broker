# api/data/sports/odds_schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class SportsOddsResponse(BaseModel):
    sport_key: str
    event_id: str
    home_team: str
    away_team: str
    commence_time: datetime | None
    bookmaker_count: int | None
    home_odds_avg: Decimal | None
    draw_odds_avg: Decimal | None
    away_odds_avg: Decimal | None
    home_implied_prob: Decimal | None
    away_implied_prob: Decimal | None
    polymarket_market_id: str | None
    polymarket_prob: Decimal | None
    bias_direction: str | None
    bias_bps: int | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class SportsScoreResponse(BaseModel):
    sport_key: str
    event_id: str
    home_team: str
    away_team: str
    home_score: int | None
    away_score: int | None
    completed: bool
    scores_json: list | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class SportsSummaryResponse(BaseModel):
    sport_key: str
    total_events: int
    events_with_polymarket: int
    avg_bias_bps: int | None
    top_bias_events: list[dict]


class AvailableSportsResponse(BaseModel):
    key: str
    title: str
    active: bool
