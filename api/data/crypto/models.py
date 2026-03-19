# api/data/crypto/models.py
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class CryptoDerivatives(Base):
    __tablename__ = "crypto_derivatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Funding Rate
    funding_rate_avg: Mapped[Decimal | None] = mapped_column(Numeric(12, 8), nullable=True)
    funding_rate_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 8), nullable=True)
    funding_rate_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 8), nullable=True)
    funding_rates_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    next_funding_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Open Interest
    oi_total_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    oi_change_pct_5m: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    oi_change_pct_15m: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    oi_change_pct_1h: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    oi_change_pct_4h: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    oi_change_pct_24h: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    oi_exchanges_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Liquidation (rolling windows)
    liq_long_1h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    liq_short_1h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    liq_long_4h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    liq_short_4h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    liq_long_24h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    liq_short_24h_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)

    # Taker Buy/Sell Volume
    taker_buy_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    taker_sell_ratio: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    taker_buy_vol_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    taker_sell_vol_usd: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)

    # Market Sentiment
    fear_greed_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True
    )
