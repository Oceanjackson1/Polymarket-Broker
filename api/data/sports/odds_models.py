# api/data/sports/odds_models.py
"""Sports odds from external bookmakers — supplements Polymarket data."""
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class SportsOdds(Base):
    __tablename__ = "sports_odds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sport_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. "soccer_epl"
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    commence_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Aggregated odds (from The Odds API — 40+ bookmakers)
    bookmaker_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    home_odds_avg: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    draw_odds_avg: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    away_odds_avg: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    home_implied_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    away_implied_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)

    # Full bookmaker breakdown
    bookmakers_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Polymarket link (if matched)
    polymarket_market_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    polymarket_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)

    # Bias: bookmaker consensus vs Polymarket
    bias_direction: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bias_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class SportsScore(Base):
    __tablename__ = "sports_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sport_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    home_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed: Mapped[bool] = mapped_column(default=False)
    last_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scores_json: Mapped[list | None] = mapped_column(JSON, nullable=True)  # period scores

    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
