from pydantic import BaseModel
from typing import Any


class MarketListResponse(BaseModel):
    data: list[Any]
    pagination: dict


class OrderBookResponse(BaseModel):
    bids: list[dict]
    asks: list[dict]
