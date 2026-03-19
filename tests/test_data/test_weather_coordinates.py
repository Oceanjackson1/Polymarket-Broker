# tests/test_data/test_weather_coordinates.py
import pytest
from unittest.mock import AsyncMock, patch
from decimal import Decimal

pytestmark = pytest.mark.asyncio(loop_scope="session")


def test_builtin_coords_has_known_cities():
    from data_pipeline.weather_coords import BUILTIN_COORDS
    assert "Tokyo" in BUILTIN_COORDS
    assert "NYC" in BUILTIN_COORDS
    assert len(BUILTIN_COORDS) >= 20


def test_builtin_coords_values_are_tuples():
    from data_pipeline.weather_coords import BUILTIN_COORDS
    for city, coords in BUILTIN_COORDS.items():
        assert isinstance(coords, tuple)
        assert len(coords) == 2
        lat, lon = coords
        assert -90 <= lat <= 90
        assert -180 <= lon <= 180


async def test_get_coordinates_builtin(test_db_session):
    from data_pipeline.weather_coords import get_coordinates
    coords = await get_coordinates("Tokyo", test_db_session)
    assert coords == pytest.approx((35.68, 139.69), abs=0.01)


async def test_get_coordinates_geocoding_fallback(test_db_session):
    from data_pipeline.weather_coords import get_coordinates
    from api.data.weather.models import CityCoordinate
    from sqlalchemy import select

    mock_resp = AsyncMock()
    mock_resp.json.return_value = {
        "results": [{"latitude": 64.13, "longitude": -21.90, "timezone": "Atlantic/Reykjavik"}]
    }
    # json() is sync in httpx, so use a plain MagicMock
    from unittest.mock import MagicMock
    mock_resp.json = MagicMock(return_value={
        "results": [{"latitude": 64.13, "longitude": -21.90, "timezone": "Atlantic/Reykjavik"}]
    })
    mock_resp.raise_for_status = MagicMock()

    with patch("data_pipeline.weather_coords.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_resp
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        coords = await get_coordinates("Reykjavik_geo", test_db_session)
        assert coords[0] == pytest.approx(64.13, abs=0.01)

    # Verify cached in DB
    result = await test_db_session.execute(
        select(CityCoordinate).where(CityCoordinate.city_name == "Reykjavik_geo")
    )
    cached = result.scalar_one()
    assert cached.timezone == "Atlantic/Reykjavik"


async def test_get_coordinates_cached_in_db(test_db_session):
    from data_pipeline.weather_coords import get_coordinates
    from api.data.weather.models import CityCoordinate

    # Pre-insert into DB
    coord = CityCoordinate(
        city_name="TestCityCoord", latitude=Decimal("10.0"), longitude=Decimal("20.0"),
        timezone="UTC",
    )
    test_db_session.add(coord)
    await test_db_session.commit()

    # Should return from DB without calling geocoding API
    coords = await get_coordinates("TestCityCoord", test_db_session)
    assert coords == pytest.approx((10.0, 20.0), abs=0.01)
