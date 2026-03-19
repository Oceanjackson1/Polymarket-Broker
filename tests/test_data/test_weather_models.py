# tests/test_data/test_weather_models.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC, date

from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_city_coordinate_crud(test_db_session):
    from api.data.weather.models import CityCoordinate

    city = CityCoordinate(
        city_name="Tokyo",
        latitude=Decimal("35.6762"),
        longitude=Decimal("139.6503"),
        timezone="Asia/Tokyo",
        temp_unit="celsius",
    )
    test_db_session.add(city)
    await test_db_session.commit()
    await test_db_session.refresh(city)
    assert city.id is not None
    result = await test_db_session.scalar(
        select(CityCoordinate).where(CityCoordinate.city_name == "Tokyo")
    )
    assert result.latitude == Decimal("35.6762")
    assert result.temp_unit == "celsius"


async def test_weather_event_crud(test_db_session):
    from api.data.weather.models import WeatherEvent

    event = WeatherEvent(
        event_slug="highest-temperature-in-tokyo-on-march-19-2026",
        city="Tokyo",
        event_date=date(2026, 3, 19),
        polymarket_event_id="272241",
        temp_unit="celsius",
        bins_json=[
            {"range": "13C or below", "market_id": "mkt_1", "market_prob": 0.02, "forecast_prob": 0.00, "bias_direction": "NEUTRAL", "bias_bps": 200},
            {"range": "18C", "market_id": "mkt_6", "market_prob": 0.15, "forecast_prob": 0.25, "bias_direction": "FORECAST_HIGHER", "bias_bps": 1000},
        ],
        max_bias_range="18C",
        max_bias_direction="FORECAST_HIGHER",
        max_bias_bps=1000,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()
    await test_db_session.refresh(event)
    assert event.id is not None
    result = await test_db_session.scalar(
        select(WeatherEvent).where(WeatherEvent.event_slug == "highest-temperature-in-tokyo-on-march-19-2026")
    )
    assert result.city == "Tokyo"
    assert len(result.bins_json) == 2
    assert result.max_bias_bps == 1000
