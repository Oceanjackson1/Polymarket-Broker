# api/data/dome/models.py
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class MarketSnapshot(Base):
    """Enriched market snapshot with candlestick and depth data from Dome."""

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    condition_id: Mapped[str] = mapped_column(String(100), nullable=False)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    volume_24h: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    open: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    high: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    low: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    close: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    bid_depth: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    ask_depth: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True,
    )


class CrossPlatformSpread(Base):
    """Price spread between matched Polymarket and Kalshi markets."""

    __tablename__ = "cross_platform_spreads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    polymarket_slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    kalshi_ticker: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sport: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    poly_price: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    kalshi_price: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    spread_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # POLY_CHEAP / KALSHI_CHEAP
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True,
    )


class WalletSnapshot(Base):
    """Periodic snapshot of a tracked wallet's positions and PnL."""

    __tablename__ = "wallet_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    total_pnl: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    position_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    positions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True,
    )
