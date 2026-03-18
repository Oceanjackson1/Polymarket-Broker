# api/data/nba/router.py
import base64
from datetime import datetime, UTC, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.nba.models import NbaGame
from api.data.nba.schemas import (
    NbaGameResponse, NbaGameDetailResponse, NbaFusionResponse, PaginatedNbaGames,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/nba", tags=["data-nba"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 120  # 2 minutes


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/games", response_model=PaginatedNbaGames)
async def list_nba_games(
    game_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    conditions = []
    target_date = game_date or date.today()
    conditions.append(NbaGame.game_date == target_date)
    if status:
        conditions.append(NbaGame.game_status == status)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(base64.b64decode(cursor).decode())
            conditions.append(NbaGame.data_updated_at < cursor_dt)
        except Exception:
            pass

    stmt = (
        select(NbaGame)
        .where(and_(*conditions))
        .order_by(desc(NbaGame.data_updated_at))
        .limit(limit + 1)
    )
    result = await db.execute(stmt)
    games = list(result.scalars().all())

    has_more = len(games) > limit
    if has_more:
        games = games[:limit]

    next_cursor = None
    if has_more and games:
        next_cursor = base64.b64encode(games[-1].data_updated_at.isoformat().encode()).decode()

    return PaginatedNbaGames(
        data=[NbaGameResponse.model_validate(g) for g in games],
        pagination={"cursor": next_cursor, "has_more": has_more, "limit": limit},
    )


@router.get("/games/{game_id}", response_model=NbaGameDetailResponse)
async def get_nba_game(
    game_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game:
        raise HTTPException(404, detail="GAME_NOT_FOUND")
    return NbaGameDetailResponse(
        stale=_is_stale(game.data_updated_at),
        data_updated_at=game.data_updated_at,
        data=NbaGameResponse.model_validate(game),
    )


@router.get("/games/{game_id}/fusion", response_model=NbaFusionResponse)
async def get_nba_fusion(
    game_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game:
        raise HTTPException(404, detail="GAME_NOT_FOUND")
    return NbaFusionResponse(
        game_id=game.game_id,
        score={
            "home": game.score_home,
            "away": game.score_away,
            "quarter": game.quarter,
            "time_remaining": game.time_remaining,
        },
        polymarket={
            "home_win_prob": float(game.home_win_prob) if game.home_win_prob else None,
            "away_win_prob": float(game.away_win_prob) if game.away_win_prob else None,
            "last_trade_price": float(game.last_trade_price) if game.last_trade_price else None,
        },
        bias_signal={
            "direction": game.bias_direction,
            "magnitude_bps": game.bias_magnitude_bps,
        },
        stale=_is_stale(game.data_updated_at),
        data_updated_at=game.data_updated_at,
    )


@router.get("/games/{game_id}/orderbook")
async def get_nba_orderbook(
    game_id: str,
    token_id: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game or not game.market_id:
        raise HTTPException(404, detail="GAME_NOT_FOUND_OR_NO_MARKET")
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
