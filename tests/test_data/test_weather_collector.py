# tests/test_data/test_weather_collector.py
import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_seed_known_cities(test_db_session):
    from data_pipeline.weather_collector import seed_known_cities
    from api.data.weather.models import CityCoordinate

    await seed_known_cities(test_db_session)
    result = await test_db_session.scalar(
        select(CityCoordinate).where(CityCoordinate.city_name == "tokyo")
    )
    assert result is not None
    assert float(result.latitude) == pytest.approx(35.6762, abs=0.01)


async def test_compute_ensemble_probs():
    from data_pipeline.weather_collector import compute_ensemble_probs

    # 5 members with max temps: 18, 19, 18, 17, 20
    member_maxes = [18.0, 19.0, 18.0, 17.0, 20.0]
    bins = ["13C or below", "14C", "15C", "16C", "17C", "18C", "19C", "20C", "21C", "22C", "23C or higher"]

    probs = compute_ensemble_probs(member_maxes, bins, temp_unit="celsius")
    assert probs["17C"] == pytest.approx(0.2, abs=0.01)
    assert probs["18C"] == pytest.approx(0.4, abs=0.01)
    assert probs["19C"] == pytest.approx(0.2, abs=0.01)
    assert probs["20C"] == pytest.approx(0.2, abs=0.01)
    assert probs["14C"] == 0.0


def test_compute_bias():
    from data_pipeline.weather_collector import compute_weather_bias
    direction, bps = compute_weather_bias(0.40, 0.25)
    assert direction == "FORECAST_HIGHER"
    assert bps == 1500

    direction, bps = compute_weather_bias(0.10, 0.20)
    assert direction == "MARKET_HIGHER"
    assert bps == 1000

    direction, bps = compute_weather_bias(0.10, 0.12)
    assert direction == "NEUTRAL"


def test_parse_event_slug():
    from data_pipeline.weather_collector import parse_event_slug
    city, d = parse_event_slug("highest-temperature-in-tokyo-on-march-19-2026")
    assert city == "tokyo"
    assert d == date(2026, 3, 19)

    city, d = parse_event_slug("highest-temperature-in-tel-aviv-on-march-16-2026")
    assert city == "tel-aviv"
    assert d == date(2026, 3, 16)
