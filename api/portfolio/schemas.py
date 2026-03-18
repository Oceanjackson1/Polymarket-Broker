from pydantic import BaseModel


class PositionItem(BaseModel):
    market_id: str
    token_id: str
    side: str
    size_held: float
    avg_price: float
    notional: float
    order_count: int


class PositionsResponse(BaseModel):
    positions: list[PositionItem]


class BalanceResponse(BaseModel):
    balance: float
    locked: float
    available: float


class PnlResponse(BaseModel):
    realized: float
    unrealized: float
    fees_paid_broker: float
    fees_paid_polymarket: float
