# api/data/weather/models.py
from datetime import datetime, UTC, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class CityCoordinate(Base):
    __tablename__ = "city_coordinates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    city_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    temp_unit: Mapped[str] = mapped_column(String(10), nullable=False, default="celsius")


class WeatherEvent(Base):
    __tablename__ = "weather_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_slug: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    polymarket_event_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    temp_unit: Mapped[str] = mapped_column(String(10), nullable=False, default="celsius")

    # Fusion data: array of {range, market_id, market_prob, forecast_prob, bias_direction, bias_bps}
    bins_json: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Max bias summary (for sorting/filtering)
    max_bias_range: Mapped[str | None] = mapped_column(String(30), nullable=True)
    max_bias_direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    max_bias_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
