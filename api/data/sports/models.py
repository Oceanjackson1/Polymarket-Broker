# api/data/sports/models.py
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class SportsEvent(Base):
    __tablename__ = "sports_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    sport_slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    outcomes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    resolution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    volume: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
