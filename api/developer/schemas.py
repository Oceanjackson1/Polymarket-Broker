# api/developer/schemas.py
from pydantic import BaseModel
from datetime import datetime


class UsageResponse(BaseModel):
    calls_today: int
    calls_remaining: int | None  # None = unlimited
    tier: str
    reset_at: datetime


class BillingResponse(BaseModel):
    tier: str
    next_billing_date: datetime | None
    amount_due_cents: int


class UpgradeRequest(BaseModel):
    tier: str  # "pro" or "enterprise"


class UpgradeResponse(BaseModel):
    previous_tier: str
    new_tier: str
    message: str


class WebhookHealthResponse(BaseModel):
    webhook_id: str
    url: str
    status: str
    failure_count: int
    events: list[str]


class RiskResetResponse(BaseModel):
    user_id: str
    circuit_breaker_reset: bool
    message: str
