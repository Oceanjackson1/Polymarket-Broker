import uuid
from decimal import Decimal
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: f"ord_{uuid.uuid4().hex[:12]}"
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    market_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)       # BUY / SELL
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="LIMIT")
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    size: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    size_filled: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=Decimal("0"))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    broker_fee_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    polymarket_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(15), default="hosted", nullable=False)  # hosted / noncustodial
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
