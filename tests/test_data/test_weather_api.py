# tests/test_data/test_weather_api.py
import pytest
from datetime import datetime, UTC, date
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Weather Key", ["data:read"])
    return result["key"]


async def _seed_weather_event(test_db_session, city: str = "tokyo", event_date_str: str = "2026-03-20"):
    from api.data.weather.models import WeatherEvent
    d = date.fromisoformat(event_date_str)
    slug = f"highest-temperature-in-{city}-on-march-{d.day}-{d.year}"
    event = WeatherEvent(
        event_slug=slug,
        city=city,
        event_date=d,
        polymarket_event_id="evt_123",
        temp_unit="celsius",
        bins_json=[
            {"range": "17C", "market_id": "mkt_4", "market_prob": 0.15, "forecast_prob": 0.20, "bias_direction": "NEUTRAL", "bias_bps": 200},
            {"range": "18C", "market_id": "mkt_5", "market_prob": 0.15, "forecast_prob": 0.40, "bias_direction": "FORECAST_HIGHER", "bias_bps": 2500},
            {"range": "19C", "market_id": "mkt_6", "market_prob": 0.20, "forecast_prob": 0.20, "bias_direction": "NEUTRAL", "bias_bps": 0},
        ],
        max_bias_range="18C",
        max_bias_direction="FORECAST_HIGHER",
        max_bias_bps=2500,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()


async def test_get_weather_dates(client, test_db_session):
    key = await _create_data_key(test_db_session, "weather_dates@example.com")
    await _seed_weather_event(test_db_session, "tokyo", "2026-03-20")

    resp = await client.get("/api/v1/data/weather/dates", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(d["date"] == "2026-03-20" for d in data)


async def test_get_weather_cities(client, test_db_session):
    key = await _create_data_key(test_db_session, "weather_cities@example.com")
    await _seed_weather_event(test_db_session, "seoul", "2026-03-20")

    resp = await client.get("/api/v1/data/weather/dates/2026-03-20/cities", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    cities = [c["city"] for c in data]
    assert "tokyo" in cities or "seoul" in cities


async def test_get_weather_fusion(client, test_db_session):
    key = await _create_data_key(test_db_session, "weather_fusion@example.com")

    resp = await client.get(
        "/api/v1/data/weather/dates/2026-03-20/cities/tokyo/fusion",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "tokyo"
    assert "temp_bins" in data
    assert "max_bias" in data
    assert len(data["temp_bins"]) >= 1


async def test_get_weather_fusion_not_found(client, test_db_session):
    key = await _create_data_key(test_db_session, "weather_404@example.com")

    resp = await client.get(
        "/api/v1/data/weather/dates/2026-03-20/cities/antarctica/fusion",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 404


async def test_weather_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("weather_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/weather/dates", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
