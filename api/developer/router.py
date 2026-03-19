# api/developer/router.py
from datetime import datetime, UTC, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_from_api_key
from api.developer.schemas import (
    UsageResponse, BillingResponse, UpgradeRequest, UpgradeResponse,
    WebhookHealthResponse, RiskResetResponse,
)
from api.auth.models import User
from core.config import get_settings

router = APIRouter(prefix="/developer", tags=["developer"])
settings = get_settings()

TIER_LIMITS = {"free": 500, "pro": 0, "enterprise": 0}  # 0 = unlimited
TIER_PRICES = {"free": 0, "pro": 9900, "enterprise": 0}  # cents


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    auth: dict = Depends(get_current_user_from_api_key),
    redis=Depends(get_redis),
):
    """API usage stats for today."""
    tier = auth.get("tier", "free")
    daily_limit = TIER_LIMITS.get(tier, 500)

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    key = f"rate_limit:{auth['user_id']}:{today}"
    count = await redis.get(key)
    calls_today = int(count) if count else 0

    remaining = None
    if daily_limit > 0:
        remaining = max(0, daily_limit - calls_today)

    # Next midnight UTC
    now = datetime.now(UTC)
    reset_at = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    return UsageResponse(
        calls_today=calls_today,
        calls_remaining=remaining,
        tier=tier,
        reset_at=reset_at,
    )


@router.get("/billing", response_model=BillingResponse)
async def get_billing(
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Current billing status."""
    tier = auth.get("tier", "free")
    amount = TIER_PRICES.get(tier, 0)

    next_billing = None
    if tier != "free":
        now = datetime.now(UTC)
        next_billing = (now.replace(day=1) + timedelta(days=32)).replace(day=1)

    return BillingResponse(
        tier=tier,
        next_billing_date=next_billing,
        amount_due_cents=amount,
    )


@router.post("/billing/upgrade", response_model=UpgradeResponse)
async def upgrade_tier(
    body: UpgradeRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Upgrade subscription tier."""
    if body.tier not in ("pro", "enterprise"):
        raise HTTPException(400, detail="INVALID_TIER: must be 'pro' or 'enterprise'")

    current_tier = auth.get("tier", "free")
    if body.tier == current_tier:
        raise HTTPException(400, detail="ALREADY_ON_THIS_TIER")

    # Update user tier
    user = await db.scalar(select(User).where(User.id == auth["user_id"]))
    if not user:
        raise HTTPException(404, detail="USER_NOT_FOUND")

    previous = user.tier
    user.tier = body.tier
    await db.commit()

    return UpgradeResponse(
        previous_tier=previous,
        new_tier=body.tier,
        message=f"Upgraded from {previous} to {body.tier}. Billing will start next cycle.",
    )


@router.get("/webhooks", response_model=list[WebhookHealthResponse])
async def get_webhook_health(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Webhook health status for all registered webhooks."""
    from api.webhooks.models import Webhook
    result = await db.execute(
        select(Webhook).where(Webhook.user_id == auth["user_id"])
    )
    webhooks = list(result.scalars().all())
    return [
        WebhookHealthResponse(
            webhook_id=wh.id,
            url=wh.url,
            status=wh.status,
            failure_count=wh.failure_count,
            events=wh.events or [],
        )
        for wh in webhooks
    ]


@router.post("/risk/reset", response_model=RiskResetResponse)
async def reset_risk(
    auth: dict = Depends(get_current_user_from_api_key),
    redis=Depends(get_redis),
):
    """Reset daily drawdown circuit breaker."""
    user_id = auth["user_id"]
    circuit_key = f"circuit_breaker:{user_id}"
    existed = await redis.delete(circuit_key)

    return RiskResetResponse(
        user_id=user_id,
        circuit_breaker_reset=existed > 0,
        message="Circuit breaker reset." if existed else "No active circuit breaker found.",
    )
