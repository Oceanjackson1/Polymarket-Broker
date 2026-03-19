# api/webhooks/router.py
import secrets
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.webhooks.models import Webhook
from api.webhooks.schemas import WebhookCreateRequest, WebhookResponse, VALID_EVENTS

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _generate_webhook_id() -> str:
    return f"wh_{secrets.token_hex(12)}"


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: WebhookCreateRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Register a new webhook endpoint."""
    require_scope(auth, "webhooks:write")

    tier = auth.get("tier", "free")
    if tier not in ("pro", "enterprise"):
        raise HTTPException(403, detail="WEBHOOKS_REQUIRE_PRO_TIER")

    invalid = set(body.events) - VALID_EVENTS
    if invalid:
        raise HTTPException(400, detail=f"INVALID_EVENTS: {sorted(invalid)}")

    wh = Webhook(
        id=_generate_webhook_id(),
        user_id=auth["user_id"],
        url=body.url,
        events=body.events,
        secret=body.secret,
        status="active",
    )
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """List all webhooks for the authenticated user."""
    require_scope(auth, "webhooks:write")
    result = await db.execute(
        select(Webhook).where(Webhook.user_id == auth["user_id"])
    )
    return list(result.scalars().all())


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Delete a webhook."""
    require_scope(auth, "webhooks:write")
    result = await db.execute(
        delete(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == auth["user_id"],
        )
    )
    if result.rowcount == 0:
        raise HTTPException(404, detail="WEBHOOK_NOT_FOUND")
    await db.commit()
