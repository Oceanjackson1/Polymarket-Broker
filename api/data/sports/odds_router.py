# api/data/sports/odds_router.py
"""Enhanced sports data endpoints — odds from 40+ bookmakers × Polymarket fusion."""
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.sports.odds_models import SportsOdds, SportsScore
from api.data.sports.odds_schemas import (
    SportsOddsResponse, SportsScoreResponse, SportsSummaryResponse,
)

router = APIRouter(prefix="/data/sports-odds", tags=["data-sports-odds"])

STALE_THRESHOLD_SECONDS = 600


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/sports")
async def list_tracked_sports(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """List sports that have odds data collected."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(
            SportsOdds.sport_key,
            func.count(SportsOdds.id).label("event_count"),
        )
        .group_by(SportsOdds.sport_key)
        .order_by(SportsOdds.sport_key)
    )
    return [{"sport_key": r.sport_key, "event_count": r.event_count} for r in result.all()]


@router.get("/odds", response_model=list[SportsOddsResponse])
async def get_sports_odds(
    sport: str = Query(..., description="Sport key, e.g. soccer_epl"),
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Get aggregated odds for a sport with Polymarket matching."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(SportsOdds)
        .where(SportsOdds.sport_key == sport)
        .order_by(desc(SportsOdds.data_updated_at))
        .limit(limit)
    )
    return [SportsOddsResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/odds/{event_id}", response_model=SportsOddsResponse)
async def get_event_odds(
    event_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Get odds for a specific event with bookmaker breakdown."""
    require_scope(auth, "data:read")
    row = await db.scalar(select(SportsOdds).where(SportsOdds.event_id == event_id))
    if not row:
        raise HTTPException(404, detail="EVENT_NOT_FOUND")
    return SportsOddsResponse.model_validate(row)


@router.get("/odds/{event_id}/bookmakers")
async def get_event_bookmakers(
    event_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Full bookmaker breakdown for an event."""
    require_scope(auth, "data:read")
    row = await db.scalar(select(SportsOdds).where(SportsOdds.event_id == event_id))
    if not row:
        raise HTTPException(404, detail="EVENT_NOT_FOUND")
    return {
        "event_id": row.event_id,
        "home_team": row.home_team,
        "away_team": row.away_team,
        "bookmakers": row.bookmakers_json or [],
        "bookmaker_count": row.bookmaker_count,
    }


@router.get("/scores", response_model=list[SportsScoreResponse])
async def get_sports_scores(
    sport: str = Query(...),
    completed: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Get live/recent scores for a sport."""
    require_scope(auth, "data:read")
    conditions = [SportsScore.sport_key == sport]
    if completed is not None:
        conditions.append(SportsScore.completed == completed)
    result = await db.execute(
        select(SportsScore)
        .where(*conditions)
        .order_by(desc(SportsScore.data_updated_at))
        .limit(limit)
    )
    return [SportsScoreResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/bias-opportunities")
async def get_bias_opportunities(
    min_bias_bps: int = Query(default=500),
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Events where bookmaker consensus significantly differs from Polymarket price."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(SportsOdds)
        .where(
            SportsOdds.bias_bps >= min_bias_bps,
            SportsOdds.polymarket_market_id.isnot(None),
        )
        .order_by(desc(SportsOdds.bias_bps))
        .limit(limit)
    )
    rows = list(result.scalars().all())
    return [
        {
            "event_id": r.event_id,
            "sport_key": r.sport_key,
            "home_team": r.home_team,
            "away_team": r.away_team,
            "bookmaker_implied_prob": float(r.home_implied_prob) if r.home_implied_prob else None,
            "polymarket_prob": float(r.polymarket_prob) if r.polymarket_prob else None,
            "bias_direction": r.bias_direction,
            "bias_bps": r.bias_bps,
            "polymarket_market_id": r.polymarket_market_id,
        }
        for r in rows
    ]
