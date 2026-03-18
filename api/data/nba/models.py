# api/data/nba/models.py
from datetime import datetime, UTC, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class NbaGame(Base):
    __tablename__ = "nba_games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    game_status: Mapped[str] = mapped_column(String(20), nullable=False)
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_remaining: Mapped[str | None] = mapped_column(String(10), nullable=True)
    market_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_win_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    away_win_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    last_trade_price: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    bias_direction: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bias_magnitude_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
