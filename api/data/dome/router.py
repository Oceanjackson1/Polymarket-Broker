# api/data/dome/router.py
"""API routes for Dome-sourced data: market snapshots, cross-platform spreads, wallets."""

from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.dome.models import MarketSnapshot, CrossPlatformSpread, WalletSnapshot
from api.data.dome.schemas import (
    MarketSnapshotResponse,
    PaginatedSnapshots,
    SpreadResponse,
    PaginatedSpreads,
    WalletSnapshotResponse,
    PaginatedWallets,
)

router = APIRouter(prefix="/data/dome", tags=["data-dome"])

STALE_THRESHOLD_SECONDS = 180  # 3 minutes


def _is_stale(dt: datetime | None) -> bool:
    if dt is None:
        return True
    now = datetime.now(UTC)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return (now - dt).total_seconds() > STALE_THRESHOLD_SECONDS


# ══════════════════════════════════════════════════════════════════
#  Market Snapshots
# ══════════════════════════════════════════════════════════════════

@router.get("/markets", response_model=PaginatedSnapshots)
async def list_market_snapshots(
    market_slug: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Latest snapshot per market, optionally filtered by slug."""
    require_scope(auth, "data:read")

    if market_slug:
        stmt = (
            select(MarketSnapshot)
            .where(MarketSnapshot.market_slug == market_slug)
            .order_by(desc(MarketSnapshot.recorded_at))
            .limit(limit)
        )
    else:
        # Latest snapshot per market_slug.
        subq = (
            select(
                MarketSnapshot.market_slug,
                func.max(MarketSnapshot.recorded_at).label("max_ts"),
            )
            .group_by(MarketSnapshot.market_slug)
            .subquery()
        )
        stmt = (
            select(MarketSnapshot)
            .join(
                subq,
                and_(
                    MarketSnapshot.market_slug == subq.c.market_slug,
                    MarketSnapshot.recorded_at == subq.c.max_ts,
                ),
            )
            .order_by(desc(MarketSnapshot.recorded_at))
            .limit(limit)
        )

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    most_recent = rows[0].recorded_at if rows else None

    return PaginatedSnapshots(
        stale=_is_stale(most_recent),
        data_updated_at=most_recent,
        data=[MarketSnapshotResponse.model_validate(r) for r in rows],
        pagination={"limit": limit, "count": len(rows)},
    )


@router.get("/markets/{slug}/candlesticks")
async def get_candlesticks(
    slug: str,
    limit: int = Query(default=60, ge=1, le=200),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Historical OHLC snapshots for a market (from stored collector data)."""
    require_scope(auth, "data:read")
    stmt = (
        select(MarketSnapshot)
        .where(
            MarketSnapshot.market_slug == slug,
            MarketSnapshot.open.isnot(None),
        )
        .order_by(desc(MarketSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return {
        "market_slug": slug,
        "data": [
            {
                "open": float(r.open) if r.open else None,
                "high": float(r.high) if r.high else None,
                "low": float(r.low) if r.low else None,
                "close": float(r.close) if r.close else None,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in reversed(rows)
        ],
    }


# ══════════════════════════════════════════════════════════════════
#  Cross-Platform Arbitrage Spreads
# ══════════════════════════════════════════════════════════════════

@router.get("/arbitrage/spreads", response_model=PaginatedSpreads)
async def list_spreads(
    sport: str | None = Query(default=None),
    min_spread_bps: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Latest cross-platform price spreads, optionally filtered by sport or minimum spread."""
    require_scope(auth, "data:read")

    # Latest per pair.
    subq = (
        select(
            CrossPlatformSpread.polymarket_slug,
            CrossPlatformSpread.kalshi_ticker,
            func.max(CrossPlatformSpread.recorded_at).label("max_ts"),
        )
        .group_by(CrossPlatformSpread.polymarket_slug, CrossPlatformSpread.kalshi_ticker)
        .subquery()
    )
    conditions = [
        CrossPlatformSpread.polymarket_slug == subq.c.polymarket_slug,
        CrossPlatformSpread.kalshi_ticker == subq.c.kalshi_ticker,
        CrossPlatformSpread.recorded_at == subq.c.max_ts,
    ]
    if sport:
        conditions.append(CrossPlatformSpread.sport == sport)
    if min_spread_bps > 0:
        conditions.append(CrossPlatformSpread.spread_bps >= min_spread_bps)

    stmt = (
        select(CrossPlatformSpread)
        .join(subq, and_(*conditions[:3]))
        .where(and_(*conditions[3:]) if len(conditions) > 3 else True)
        .order_by(desc(CrossPlatformSpread.spread_bps))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    most_recent = rows[0].recorded_at if rows else None

    return PaginatedSpreads(
        stale=_is_stale(most_recent),
        data_updated_at=most_recent,
        data=[SpreadResponse.model_validate(r) for r in rows],
        pagination={"limit": limit, "count": len(rows)},
    )


@router.get("/arbitrage/opportunities")
async def get_opportunities(
    min_spread_bps: int = Query(default=50, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """High-spread opportunities (spread >= threshold)."""
    require_scope(auth, "data:read")

    subq = (
        select(
            CrossPlatformSpread.polymarket_slug,
            CrossPlatformSpread.kalshi_ticker,
            func.max(CrossPlatformSpread.recorded_at).label("max_ts"),
        )
        .group_by(CrossPlatformSpread.polymarket_slug, CrossPlatformSpread.kalshi_ticker)
        .subquery()
    )
    stmt = (
        select(CrossPlatformSpread)
        .join(
            subq,
            and_(
                CrossPlatformSpread.polymarket_slug == subq.c.polymarket_slug,
                CrossPlatformSpread.kalshi_ticker == subq.c.kalshi_ticker,
                CrossPlatformSpread.recorded_at == subq.c.max_ts,
            ),
        )
        .where(CrossPlatformSpread.spread_bps >= min_spread_bps)
        .order_by(desc(CrossPlatformSpread.spread_bps))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return {
        "min_spread_bps": min_spread_bps,
        "count": len(rows),
        "opportunities": [
            {
                "polymarket_slug": r.polymarket_slug,
                "kalshi_ticker": r.kalshi_ticker,
                "sport": r.sport,
                "poly_price": float(r.poly_price),
                "kalshi_price": float(r.kalshi_price),
                "spread_bps": r.spread_bps,
                "direction": r.direction,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in rows
        ],
    }


# ══════════════════════════════════════════════════════════════════
#  Wallet Tracking
# ══════════════════════════════════════════════════════════════════

@router.get("/wallets/{address}/positions", response_model=PaginatedWallets)
async def get_wallet_positions(
    address: str,
    limit: int = Query(default=10, ge=1, le=50),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Historical position snapshots for a tracked wallet."""
    require_scope(auth, "data:read")

    stmt = (
        select(WalletSnapshot)
        .where(WalletSnapshot.wallet_address == address)
        .order_by(desc(WalletSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    if not rows:
        raise HTTPException(404, detail="WALLET_NOT_TRACKED")

    return PaginatedWallets(
        data=[WalletSnapshotResponse.model_validate(r) for r in rows],
        pagination={"limit": limit, "count": len(rows)},
    )


@router.get("/wallets/{address}/pnl")
async def get_wallet_pnl(
    address: str,
    limit: int = Query(default=30, ge=1, le=200),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """PnL history for a tracked wallet."""
    require_scope(auth, "data:read")

    stmt = (
        select(
            WalletSnapshot.recorded_at,
            WalletSnapshot.total_pnl,
            WalletSnapshot.position_count,
        )
        .where(WalletSnapshot.wallet_address == address)
        .order_by(desc(WalletSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()
    if not rows:
        raise HTTPException(404, detail="WALLET_NOT_TRACKED")

    return {
        "wallet_address": address,
        "data": [
            {
                "recorded_at": r.recorded_at.isoformat(),
                "total_pnl": float(r.total_pnl) if r.total_pnl else None,
                "position_count": r.position_count,
            }
            for r in reversed(rows)
        ],
    }


# ══════════════════════════════════════════════════════════════════
#  Crypto Prices (proxy to Dome API for real-time data)
# ══════════════════════════════════════════════════════════════════

@router.get("/crypto/{symbol}/price")
async def get_crypto_price(
    symbol: str,
    auth: dict = Depends(get_current_user_from_api_key),
):
    """Real-time crypto price from Dome (Binance). Requires DomeClient on app.state."""
    require_scope(auth, "data:read")
    from fastapi import Request
    # DomeClient is attached to app.state during lifespan.
    # This is a lightweight proxy; no DB needed.
    raise HTTPException(501, detail="DOME_CLIENT_NOT_AVAILABLE_VIA_PROXY_YET")
