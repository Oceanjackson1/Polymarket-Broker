# api/data/btc/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class BtcSnapshotResponse(BaseModel):
    id: int
    timeframe: str
    price_usd: Decimal
    market_id: str | None
    prediction_prob: Decimal | None
    volume: Decimal | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class BtcTimeframeResponse(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[BtcSnapshotResponse]


class BtcHistoryResponse(BaseModel):
    data: list[BtcSnapshotResponse]
    pagination: dict
