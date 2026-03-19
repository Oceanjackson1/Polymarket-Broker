# api/data/crypto/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class FundingRateResponse(BaseModel):
    symbol: str
    aggregated: dict
    exchanges: list[dict]
    next_funding_time: int | None
    stale: bool
    recorded_at: datetime


class FundingRateHistoryItem(BaseModel):
    funding_rate_avg: Decimal | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class FundingRateHistoryResponse(BaseModel):
    data: list[FundingRateHistoryItem]
    pagination: dict


class OpenInterestResponse(BaseModel):
    symbol: str
    total_usd: Decimal | None
    changes: dict
    exchanges: list[dict]
    stale: bool
    recorded_at: datetime


class OiHistoryItem(BaseModel):
    oi_total_usd: Decimal | None
    oi_change_pct_1h: Decimal | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class OiHistoryResponse(BaseModel):
    data: list[OiHistoryItem]
    pagination: dict


class LiquidationResponse(BaseModel):
    symbol: str
    windows: dict
    stale: bool
    recorded_at: datetime


class TakerVolumeResponse(BaseModel):
    symbol: str
    buy_ratio: Decimal | None
    sell_ratio: Decimal | None
    buy_vol_usd: Decimal | None
    sell_vol_usd: Decimal | None
    stale: bool
    recorded_at: datetime


class SentimentResponse(BaseModel):
    fear_greed: dict
    recorded_at: datetime


class CryptoOverviewResponse(BaseModel):
    symbol: str
    funding: dict
    open_interest: dict
    liquidations: dict
    taker_volume: dict
    fear_greed: int | None
    stale: bool
    recorded_at: datetime
