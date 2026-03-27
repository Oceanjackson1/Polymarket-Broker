from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class OrderRequest(BaseModel):
    market_id: str
    token_id: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    type: str = Field(default="LIMIT", pattern="^(LIMIT|MARKET|GTD)$")
    price: float = Field(..., gt=0, lt=1)
    size: float = Field(..., gt=0)
    expires_at: datetime | None = None


class OrderResponse(BaseModel):
    order_id: str
    market_id: str
    token_id: str
    side: str
    type: str
    price: float
    size: float
    size_filled: float
    size_remaining: float
    status: str
    broker_fee_bps: int
    market_category: str | None = None
    polymarket_fee_bps: int | None = None
    polymarket_order_id: str | None
    mode: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    data: list[OrderResponse]
    pagination: dict


class BuildOrderRequest(BaseModel):
    market_id: str
    token_id: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    price: float = Field(..., gt=0, lt=1)
    size: float = Field(..., gt=0)


class BuildOrderResponse(BaseModel):
    eip712_payload: dict
    payload_hash: str


class SubmitOrderRequest(BaseModel):
    payload_hash: str
    signature: str
