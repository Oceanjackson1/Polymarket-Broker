# api/fees/schemas.py
from pydantic import BaseModel


class CategoryFeeInfo(BaseModel):
    category: str
    fee_rate: float
    exponent: int
    maker_rebate: float
    poly_retention: float
    fee_at_p50: float  # taker fee rate when p=0.50
    fee_at_p80: float
    fee_at_p95: float


class FeeScheduleResponse(BaseModel):
    formula: str
    categories: list[CategoryFeeInfo]


class FeeEstimateResponse(BaseModel):
    category: str
    price: float
    volume: float
    polymarket_fee_rate: float
    polymarket_fee_bps: int
    polymarket_fee_amount: float
    broker_fee_bps: int
    broker_fee_amount: float
    total_fee_amount: float
    total_fee_bps: int
    gross_profit_if_win: float
    net_profit_if_win: float


class MarketFeeResponse(BaseModel):
    token_id: str
    market_question: str | None
    detected_category: str
    midpoint_price: float | None
    fee_estimate: FeeEstimateResponse | None
