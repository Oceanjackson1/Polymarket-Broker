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


def test_parse_event_slug_invalid():
    from data_pipeline.weather_collector import parse_event_slug
    with pytest.raises(ValueError):
        parse_event_slug("warriors-vs-celtics")


def test_extract_member_maxes():
    from data_pipeline.weather_collector import WeatherCollector

    collector = WeatherCollector()
    d = date(2026, 3, 19)
    ensemble_data = {
        "hourly": {
            "time": ["2026-03-19T00:00", "2026-03-19T06:00", "2026-03-19T12:00", "2026-03-19T18:00"],
            "temperature_2m": [10.0, 15.0, 20.0, 18.0],
            "temperature_2m_member01": [11.0, 16.0, 21.0, 17.0],
            "temperature_2m_member02": [9.0, 14.0, 19.0, 16.0],
        }
    }
    maxes = collector._extract_member_maxes(ensemble_data, d)
    assert len(maxes) == 3  # control + 2 members
    assert maxes[0] == 20.0  # control max
    assert maxes[1] == 21.0  # member01 max
    assert maxes[2] == 19.0  # member02 max


def test_extract_member_maxes_no_matching_date():
    from data_pipeline.weather_collector import WeatherCollector

    collector = WeatherCollector()
    d = date(2026, 3, 20)
    ensemble_data = {
        "hourly": {
            "time": ["2026-03-19T00:00", "2026-03-19T12:00"],
            "temperature_2m": [10.0, 20.0],
        }
    }
    maxes = collector._extract_member_maxes(ensemble_data, d)
    assert maxes == []


async def test_collector_collect_upserts(test_db_session):
    from unittest.mock import AsyncMock, MagicMock, patch
    from datetime import timedelta
    from data_pipeline.weather_collector import WeatherCollector
    from api.data.weather.models import WeatherEvent

    d = date.today() + timedelta(days=3)
    month_names = {1: "january", 2: "february", 3: "march", 4: "april", 5: "may", 6: "june",
                   7: "july", 8: "august", 9: "september", 10: "october", 11: "november", 12: "december"}
    slug = f"highest-temperature-in-tokyo-on-{month_names[d.month]}-{d.day}-{d.year}"

    collector = WeatherCollector()
    collector._seeded = True
    collector._gamma = AsyncMock()
    collector._gamma.get_events = AsyncMock(return_value=[
        {
            "id": "evt_collect_test",
            "slug": slug,
            "markets": [
                {"id": "mkt_1", "groupItemTitle": "13°C or below", "groupItemThreshold": 0,
                 "outcomePrices": ["0.02", "0.98"]},
                {"id": "mkt_2", "groupItemTitle": "18°C", "groupItemThreshold": 18,
                 "outcomePrices": ["0.25", "0.75"]},
                {"id": "mkt_3", "groupItemTitle": "23°C or higher", "groupItemThreshold": 99,
                 "outcomePrices": ["0.02", "0.98"]},
            ],
        },
    ])

    target_str = d.isoformat()
    times = [f"{target_str}T{h:02d}:00" for h in range(24)]
    ensemble_resp = {
        "hourly": {
            "time": times,
            "temperature_2m": [15.0 + h * 0.15 for h in range(24)],
            "temperature_2m_member01": [16.0 + h * 0.13 for h in range(24)],
        }
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = ensemble_resp
    mock_resp.raise_for_status = MagicMock()

    with patch("data_pipeline.weather_collector.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_resp
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        await collector.collect(test_db_session)

    result = await test_db_session.execute(
        select(WeatherEvent).where(WeatherEvent.event_slug == slug)
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.city == "tokyo"
    assert event.event_date == d
    assert len(event.bins_json) == 3
    assert event.max_bias_bps >= 0


async def test_collector_skips_non_weather_slug(test_db_session):
    from unittest.mock import AsyncMock
    from data_pipeline.weather_collector import WeatherCollector

    collector = WeatherCollector()
    collector._seeded = True
    collector._gamma = AsyncMock()
    collector._gamma.get_events = AsyncMock(return_value=[
        {"id": "evt_1", "slug": "warriors-vs-celtics", "markets": []},
    ])

    # Should not raise
    await collector.collect(test_db_session)
