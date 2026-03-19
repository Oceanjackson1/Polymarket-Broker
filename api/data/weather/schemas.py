# api/data/weather/schemas.py
from pydantic import BaseModel
from datetime import datetime, date


class WeatherDateResponse(BaseModel):
    date: date
    city_count: int
    event_count: int


class WeatherCityResponse(BaseModel):
    city: str
    event_date: date
    max_bias_range: str | None
    max_bias_direction: str | None
    max_bias_bps: int | None
    data_updated_at: datetime


class TempBin(BaseModel):
    range: str
    market_id: str | None
    market_prob: float
    forecast_prob: float
    bias_direction: str
    bias_bps: int


class WeatherFusionResponse(BaseModel):
    city: str
    date: date
    event_slug: str
    temp_unit: str
    temp_bins: list[TempBin]
    max_bias: dict
    stale: bool
    data_updated_at: datetime
