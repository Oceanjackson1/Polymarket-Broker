# api/strategies/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class StrategyInfo(BaseModel):
    slug: str
    name: str
    description: str
    min_tier: str


class ConvergenceOpportunity(BaseModel):
    market_id: str
    question: str
    current_price: Decimal
    estimated_true_prob: Decimal
    edge_bps: int
    expiry: datetime | None
    volume: Decimal | None


class ConvergenceExecuteRequest(BaseModel):
    market_id: str
    token_id: str
    size: Decimal
    side: str = "BUY"


class ConvergenceExecuteResponse(BaseModel):
    order_id: str
    market_id: str
    side: str
    price: Decimal
    size: Decimal
    strategy: str
    status: str
    executed_at: datetime


class ConvergencePosition(BaseModel):
    order_id: str
    market_id: str
    question: str | None
    side: str
    entry_price: Decimal
    size: Decimal
    current_price: Decimal | None
    unrealized_pnl: Decimal | None
    status: str
    opened_at: datetime
