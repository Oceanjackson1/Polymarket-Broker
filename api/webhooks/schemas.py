# api/webhooks/schemas.py
from pydantic import BaseModel, HttpUrl
from datetime import datetime


VALID_EVENTS = {
    "order.filled", "order.cancelled", "market.resolved",
    "position.opened", "position.closed",
    "strategy.executed", "analysis.signal",
}


class WebhookCreateRequest(BaseModel):
    url: str
    events: list[str]
    secret: str


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: list[str]
    status: str
    failure_count: int
    created_at: datetime

    class Config:
        from_attributes = True
