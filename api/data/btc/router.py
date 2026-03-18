# api/data/btc/router.py
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.btc.models import BtcSnapshot
from api.data.btc.schemas import BtcSnapshotResponse, BtcTimeframeResponse, BtcHistoryResponse
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/btc", tags=["data-btc"])

clob_client = ClobClient()

VALID_TIMEFRAMES = {"5m", "15m", "1h", "4h"}
STALE_THRESHOLD_SECONDS = 120  # 2 minutes


def _is_stale(recorded_at: datetime) -> bool:
    now = datetime.now(UTC)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)
    return (now - recorded_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/predictions", response_model=list[BtcSnapshotResponse])
async def get_btc_predictions_all(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Latest snapshot for all 4 timeframes."""
    require_scope(auth, "data:read")
    # Use a subquery to get the latest recorded_at per timeframe
    subq = (
        select(BtcSnapshot.timeframe, func.max(BtcSnapshot.recorded_at).label("max_recorded"))
        .group_by(BtcSnapshot.timeframe)
        .subquery()
    )
    stmt = select(BtcSnapshot).join(
        subq,
        (BtcSnapshot.timeframe == subq.c.timeframe) &
        (BtcSnapshot.recorded_at == subq.c.max_recorded)
    ).order_by(BtcSnapshot.timeframe)
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())
    return [BtcSnapshotResponse.model_validate(s) for s in snaps]


@router.get("/predictions/{timeframe}", response_model=BtcTimeframeResponse)
async def get_btc_predictions_timeframe(
    timeframe: str,
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(400, detail=f"INVALID_TIMEFRAME: must be one of {sorted(VALID_TIMEFRAMES)}")

    stmt = (
        select(BtcSnapshot)
        .where(BtcSnapshot.timeframe == timeframe)
        .order_by(desc(BtcSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())

    most_recent = snaps[0].recorded_at if snaps else None
    stale = _is_stale(most_recent) if most_recent else True

    return BtcTimeframeResponse(
        stale=stale,
        data_updated_at=most_recent,
        data=[BtcSnapshotResponse.model_validate(s) for s in snaps],
    )


@router.get("/onchain")
async def get_btc_onchain(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Proxy: latest on-chain BTC Polymarket trades via ClobClient."""
    require_scope(auth, "data:read")
    # Resolve market_id from the most recent 5m snapshot
    latest = await db.scalar(
        select(BtcSnapshot)
        .where(BtcSnapshot.timeframe == "5m", BtcSnapshot.market_id.isnot(None))
        .order_by(desc(BtcSnapshot.recorded_at))
    )
    if not latest or not latest.market_id:
        raise HTTPException(503, detail="BTC_MARKET_ID_NOT_COLLECTED_YET")
    try:
        return await clob_client.get_trades(market_id=latest.market_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/history", response_model=BtcHistoryResponse)
async def get_btc_history(
    timeframe: str = Query(...),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(400, detail=f"INVALID_TIMEFRAME: must be one of {sorted(VALID_TIMEFRAMES)}")

    conditions = [BtcSnapshot.timeframe == timeframe]
    if from_:
        try:
            conditions.append(BtcSnapshot.recorded_at >= datetime.fromisoformat(from_))
        except ValueError:
            raise HTTPException(400, detail="INVALID_FROM_DATETIME")
    if to:
        try:
            conditions.append(BtcSnapshot.recorded_at <= datetime.fromisoformat(to))
        except ValueError:
            raise HTTPException(400, detail="INVALID_TO_DATETIME")

    stmt = (
        select(BtcSnapshot)
        .where(and_(*conditions))
        .order_by(desc(BtcSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())
    return BtcHistoryResponse(
        data=[BtcSnapshotResponse.model_validate(s) for s in snaps],
        pagination={"limit": limit, "count": len(snaps)},
    )
