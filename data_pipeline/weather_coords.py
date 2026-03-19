# data_pipeline/weather_coords.py
from datetime import datetime, UTC
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.data.weather.models import CityCoordinate
from core.config import get_settings as _get_settings

GEOCODING_URL = f"{_get_settings().open_meteo_geocoding_base}/v1/search"

BUILTIN_COORDS: dict[str, tuple[float, float]] = {
    "NYC":          (40.78, -73.97),
    "Tokyo":        (35.68, 139.69),
    "Shanghai":     (31.23, 121.47),
    "Seoul":        (37.57, 126.98),
    "London":       (51.51, -0.13),
    "Tel Aviv":     (32.01, 34.88),
    "Hong Kong":    (22.32, 114.17),
    "Atlanta":      (33.75, -84.39),
    "Dallas":       (32.78, -96.80),
    "Chicago":      (41.88, -87.63),
    "Miami":        (25.76, -80.19),
    "Seattle":      (47.61, -122.33),
    "Toronto":      (43.65, -79.38),
    "Sao Paulo":    (-23.55, -46.63),
    "Ankara":       (39.93, 32.86),
    "Wellington":   (-41.29, 174.78),
    "Singapore":    (1.35, 103.82),
    "Lucknow":      (26.85, 80.95),
    "Buenos Aires": (-34.60, -58.38),
    "Paris":        (48.86, 2.35),
    "Milan":        (45.46, 9.19),
}


async def get_coordinates(
    city: str, db: AsyncSession
) -> tuple[float, float] | None:
    """Resolve city name to (lat, lon). Lookup order: builtin -> DB -> Geocoding API."""
    # 1. Built-in
    if city in BUILTIN_COORDS:
        return BUILTIN_COORDS[city]

    # 2. DB cache
    result = await db.execute(
        select(CityCoordinate).where(CityCoordinate.city_name == city)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return (float(cached.latitude), float(cached.longitude))

    # 3. Geocoding API fallback
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(GEOCODING_URL, params={"name": city, "count": 1})
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None

    lat = results[0]["latitude"]
    lon = results[0]["longitude"]
    tz = results[0].get("timezone", "UTC")

    # Cache in DB
    coord = CityCoordinate(
        city_name=city, latitude=lat, longitude=lon,
        timezone=tz,
    )
    db.add(coord)
    await db.commit()

    return (lat, lon)
