# api/data/sports/router.py
import base64
from datetime import datetime, UTC, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.sports.models import SportsEvent
from api.data.sports.schemas import (
    SportsCategoryResponse, PaginatedSportsEvents, SportsEventResponse, RealizedResponse,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/sports", tags=["data-sports"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 600  # 10 minutes


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/categories", response_model=list[SportsCategoryResponse])
async def get_categories(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    result = await db.execute(
        select(SportsEvent.sport_slug, func.count(SportsEvent.id).label("active_events"))
        .where(SportsEvent.status == "active")
        .group_by(SportsEvent.sport_slug)
        .order_by(SportsEvent.sport_slug)
    )
    return [{"slug": r.sport_slug, "active_events": r.active_events} for r in result.all()]


@router.get("/{sport}/events", response_model=PaginatedSportsEvents)
async def get_sport_events(
    sport: str,
    status: str | None = Query(default="active"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    conditions = [SportsEvent.sport_slug == sport]
    if status:
        conditions.append(SportsEvent.status == status)
    if cursor:
        try:
            decoded = base64.b64decode(cursor).decode()
            cursor_dt_str, cursor_id_str = decoded.split("|")
            cursor_dt = datetime.fromisoformat(cursor_dt_str)
            cursor_id = int(cursor_id_str)
            conditions.append(or_(
                SportsEvent.data_updated_at < cursor_dt,
                and_(SportsEvent.data_updated_at == cursor_dt, SportsEvent.id < cursor_id),
            ))
        except Exception:
            pass

    stmt = (
        select(SportsEvent)
        .where(and_(*conditions))
        .order_by(desc(SportsEvent.data_updated_at), desc(SportsEvent.id))
        .limit(limit + 1)
    )
    result = await db.execute(stmt)
    events = list(result.scalars().all())

    has_more = len(events) > limit
    if has_more:
        events = events[:limit]

    next_cursor = None
    if has_more and events:
        last = events[-1]
        next_cursor = base64.b64encode(
            f"{last.data_updated_at.isoformat()}|{last.id}".encode()
        ).decode()

    most_recent = max((e.data_updated_at for e in events), default=None)
    stale = _is_stale(most_recent) if most_recent else True

    return PaginatedSportsEvents(
        stale=stale,
        data_updated_at=most_recent,
        data=[SportsEventResponse.model_validate(e) for e in events],
        pagination={"cursor": next_cursor, "has_more": has_more, "limit": limit},
    )


@router.get("/{sport}/events/{market_id}/orderbook")
async def get_event_orderbook(
    sport: str,
    market_id: str,
    token_id: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{sport}/events/{market_id}/realized", response_model=RealizedResponse)
async def get_event_realized(
    sport: str,
    market_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(SportsEvent).where(
            SportsEvent.market_id == market_id,
            SportsEvent.status == "resolved",
        )
    )
    if not event:
        raise HTTPException(404, detail="MARKET_NOT_RESOLVED")
    return RealizedResponse(
        stale=_is_stale(event.data_updated_at),
        data_updated_at=event.data_updated_at,
        data={
            "market_id": event.market_id,
            "question": event.question,
            "resolution": event.resolution,
        },
    )
