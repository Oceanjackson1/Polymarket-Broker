# api/webhooks/dispatcher.py
"""Webhook delivery with HMAC-SHA256 signing and exponential backoff retry."""
import hashlib
import hmac
import json
import logging
from datetime import datetime, UTC
import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.webhooks.models import Webhook

logger = logging.getLogger(__name__)

RETRY_DELAYS = [1, 5, 30, 300, 1800]  # seconds: 1s, 5s, 30s, 5min, 30min
MAX_FAILURES = 5


def sign_payload(secret: str, body: bytes) -> str:
    """HMAC-SHA256 signature for webhook payload."""
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def dispatch_event(
    db: AsyncSession,
    event_type: str,
    data: dict,
    user_id: str | None = None,
) -> int:
    """Send webhook to all active subscribers for this event type.
    
    Returns number of webhooks dispatched.
    """
    conditions = [
        Webhook.status == "active",
    ]
    if user_id:
        conditions.append(Webhook.user_id == user_id)

    result = await db.execute(select(Webhook).where(*conditions))
    webhooks = list(result.scalars().all())

    dispatched = 0
    for wh in webhooks:
        if event_type not in (wh.events or []):
            continue

        payload = {
            "event": event_type,
            "webhook_id": wh.id,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data,
        }
        body = json.dumps(payload).encode()
        signature = sign_payload(wh.secret, body)

        success = await _deliver(wh.url, body, signature)
        if success:
            dispatched += 1
            if wh.failure_count > 0:
                await db.execute(
                    update(Webhook).where(Webhook.id == wh.id).values(failure_count=0)
                )
        else:
            new_count = wh.failure_count + 1
            new_status = "failed" if new_count >= MAX_FAILURES else "active"
            await db.execute(
                update(Webhook).where(Webhook.id == wh.id).values(
                    failure_count=new_count, status=new_status
                )
            )
            if new_status == "failed":
                logger.warning(f"[webhook] {wh.id} marked FAILED after {MAX_FAILURES} failures")

    await db.commit()
    return dispatched


async def _deliver(url: str, body: bytes, signature: str) -> bool:
    """Attempt delivery with single try (retry logic is for background workers)."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                url,
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Broker-Signature": signature,
                },
            )
            return 200 <= resp.status_code < 300
    except Exception as e:
        logger.warning(f"[webhook] delivery to {url} failed: {e}")
        return False
