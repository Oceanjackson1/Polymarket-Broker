# api/data/dome/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


# ── Market Snapshots ─────────────────────────────────────────────

class MarketSnapshotResponse(BaseModel):
    id: int
    market_slug: str
    condition_id: str
    token_id: str
    price: Decimal
    volume_24h: Decimal | None
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    bid_depth: Decimal | None
    ask_depth: Decimal | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class PaginatedSnapshots(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[MarketSnapshotResponse]
    pagination: dict


# ── Cross-Platform Spreads ───────────────────────────────────────

class SpreadResponse(BaseModel):
    id: int
    polymarket_slug: str
    kalshi_ticker: str
    sport: str
    poly_price: Decimal
    kalshi_price: Decimal
    spread_bps: int
    direction: str
    recorded_at: datetime

    class Config:
        from_attributes = True


class PaginatedSpreads(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[SpreadResponse]
    pagination: dict


# ── Wallet Snapshots ─────────────────────────────────────────────

class WalletSnapshotResponse(BaseModel):
    id: int
    wallet_address: str
    total_pnl: Decimal | None
    position_count: int | None
    positions_json: dict | list | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class PaginatedWallets(BaseModel):
    data: list[WalletSnapshotResponse]
    pagination: dict
