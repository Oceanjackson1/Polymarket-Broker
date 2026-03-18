# api/data/btc/models.py
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class BtcSnapshot(Base):
    __tablename__ = "btc_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    market_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prediction_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True
    )
