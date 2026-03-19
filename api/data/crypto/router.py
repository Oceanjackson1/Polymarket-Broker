# api/data/crypto/router.py
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.crypto.models import CryptoDerivatives
from api.data.crypto.schemas import (
    FundingRateResponse, FundingRateHistoryResponse, FundingRateHistoryItem,
    OpenInterestResponse, OiHistoryResponse, OiHistoryItem,
    LiquidationResponse, TakerVolumeResponse, SentimentResponse,
    CryptoOverviewResponse,
)

router = APIRouter(prefix="/data/crypto", tags=["data-crypto"])

VALID_SYMBOLS = {"BTC", "ETH", "SOL"}
STALE_THRESHOLD_SECONDS = 120


def _is_stale(recorded_at: datetime) -> bool:
    now = datetime.now(UTC)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)
    return (now - recorded_at).total_seconds() > STALE_THRESHOLD_SECONDS


def _validate_symbol(symbol: str) -> str:
    s = symbol.upper()
    if s not in VALID_SYMBOLS:
        raise HTTPException(400, detail=f"INVALID_SYMBOL: must be one of {sorted(VALID_SYMBOLS)}")
    return s


async def _get_latest(db: AsyncSession, symbol: str) -> CryptoDerivatives:
    result = await db.scalar(
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == symbol)
        .order_by(desc(CryptoDerivatives.recorded_at))
    )
    if not result:
        raise HTTPException(404, detail=f"NO_DATA_FOR_{symbol}")
    return result


def _fear_greed_label(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value <= 25:
        return "extreme_fear"
    if value <= 45:
        return "fear"
    if value <= 55:
        return "neutral"
    if value <= 75:
        return "greed"
    return "extreme_greed"


@router.get("/funding-rates", response_model=FundingRateResponse)
async def get_funding_rates(
    symbol: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    row = await _get_latest(db, sym)
    return FundingRateResponse(
        symbol=sym,
        aggregated={
            "avg": row.funding_rate_avg,
            "min": row.funding_rate_min,
            "max": row.funding_rate_max,
        },
        exchanges=row.funding_rates_json or [],
        next_funding_time=row.next_funding_time,
        stale=_is_stale(row.recorded_at),
        recorded_at=row.recorded_at,
    )


@router.get("/funding-rates/history", response_model=FundingRateHistoryResponse)
async def get_funding_rates_history(
    symbol: str = Query(...),
    limit: int = Query(default=100, ge=1, le=1000),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    stmt = (
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == sym)
        .order_by(desc(CryptoDerivatives.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return FundingRateHistoryResponse(
        data=[FundingRateHistoryItem(
            funding_rate_avg=r.funding_rate_avg,
            recorded_at=r.recorded_at,
        ) for r in rows],
        pagination={"limit": limit, "count": len(rows)},
    )


@router.get("/open-interest", response_model=OpenInterestResponse)
async def get_open_interest(
    symbol: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    row = await _get_latest(db, sym)
    return OpenInterestResponse(
        symbol=sym,
        total_usd=row.oi_total_usd,
        changes={
            "5m": row.oi_change_pct_5m,
            "15m": row.oi_change_pct_15m,
            "1h": row.oi_change_pct_1h,
            "4h": row.oi_change_pct_4h,
            "24h": row.oi_change_pct_24h,
        },
        exchanges=row.oi_exchanges_json or [],
        stale=_is_stale(row.recorded_at),
        recorded_at=row.recorded_at,
    )


@router.get("/open-interest/history", response_model=OiHistoryResponse)
async def get_open_interest_history(
    symbol: str = Query(...),
    limit: int = Query(default=100, ge=1, le=1000),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    stmt = (
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == sym)
        .order_by(desc(CryptoDerivatives.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return OiHistoryResponse(
        data=[OiHistoryItem(
            oi_total_usd=r.oi_total_usd,
            oi_change_pct_1h=r.oi_change_pct_1h,
            recorded_at=r.recorded_at,
        ) for r in rows],
        pagination={"limit": limit, "count": len(rows)},
    )


@router.get("/liquidations", response_model=LiquidationResponse)
async def get_liquidations(
    symbol: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    row = await _get_latest(db, sym)
    return LiquidationResponse(
        symbol=sym,
        windows={
            "1h": {"long_usd": row.liq_long_1h_usd, "short_usd": row.liq_short_1h_usd},
            "4h": {"long_usd": row.liq_long_4h_usd, "short_usd": row.liq_short_4h_usd},
            "24h": {"long_usd": row.liq_long_24h_usd, "short_usd": row.liq_short_24h_usd},
        },
        stale=_is_stale(row.recorded_at),
        recorded_at=row.recorded_at,
    )


@router.get("/taker-volume", response_model=TakerVolumeResponse)
async def get_taker_volume(
    symbol: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    row = await _get_latest(db, sym)
    return TakerVolumeResponse(
        symbol=sym,
        buy_ratio=row.taker_buy_ratio,
        sell_ratio=row.taker_sell_ratio,
        buy_vol_usd=row.taker_buy_vol_usd,
        sell_vol_usd=row.taker_sell_vol_usd,
        stale=_is_stale(row.recorded_at),
        recorded_at=row.recorded_at,
    )


@router.get("/sentiment", response_model=SentimentResponse)
async def get_sentiment(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    row = await db.scalar(
        select(CryptoDerivatives)
        .where(CryptoDerivatives.fear_greed_index.isnot(None))
        .order_by(desc(CryptoDerivatives.recorded_at))
    )
    if not row:
        raise HTTPException(404, detail="NO_SENTIMENT_DATA")
    return SentimentResponse(
        fear_greed={"value": row.fear_greed_index, "label": _fear_greed_label(row.fear_greed_index)},
        recorded_at=row.recorded_at,
    )


@router.get("/overview", response_model=CryptoOverviewResponse)
async def get_overview(
    symbol: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    sym = _validate_symbol(symbol)
    row = await _get_latest(db, sym)
    return CryptoOverviewResponse(
        symbol=sym,
        funding={
            "avg": row.funding_rate_avg,
            "min": row.funding_rate_min,
            "max": row.funding_rate_max,
            "exchanges": row.funding_rates_json or [],
        },
        open_interest={
            "total_usd": row.oi_total_usd,
            "changes": {
                "5m": row.oi_change_pct_5m,
                "1h": row.oi_change_pct_1h,
                "4h": row.oi_change_pct_4h,
                "24h": row.oi_change_pct_24h,
            },
        },
        liquidations={
            "1h": {"long_usd": row.liq_long_1h_usd, "short_usd": row.liq_short_1h_usd},
            "4h": {"long_usd": row.liq_long_4h_usd, "short_usd": row.liq_short_4h_usd},
            "24h": {"long_usd": row.liq_long_24h_usd, "short_usd": row.liq_short_24h_usd},
        },
        taker_volume={
            "buy_ratio": row.taker_buy_ratio,
            "sell_ratio": row.taker_sell_ratio,
            "buy_vol_usd": row.taker_buy_vol_usd,
            "sell_vol_usd": row.taker_sell_vol_usd,
        },
        fear_greed=row.fear_greed_index,
        stale=_is_stale(row.recorded_at),
        recorded_at=row.recorded_at,
    )
