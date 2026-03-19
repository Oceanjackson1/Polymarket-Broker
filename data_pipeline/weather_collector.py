# data_pipeline/weather_collector.py
import logging
import re
from datetime import datetime, UTC, date
from decimal import Decimal
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.weather.models import WeatherEvent, CityCoordinate
from core.polymarket.gamma_client import GammaClient

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
BIAS_THRESHOLD_BPS = 300

KNOWN_CITIES = {
    "tokyo": {"lat": 35.6762, "lon": 139.6503, "tz": "Asia/Tokyo", "unit": "celsius"},
    "seoul": {"lat": 37.5665, "lon": 126.9780, "tz": "Asia/Seoul", "unit": "celsius"},
    "hong-kong": {"lat": 22.3193, "lon": 114.1694, "tz": "Asia/Hong_Kong", "unit": "celsius"},
    "shanghai": {"lat": 31.2304, "lon": 121.4737, "tz": "Asia/Shanghai", "unit": "celsius"},
    "singapore": {"lat": 1.3521, "lon": 103.8198, "tz": "Asia/Singapore", "unit": "celsius"},
    "london": {"lat": 51.5074, "lon": -0.1278, "tz": "Europe/London", "unit": "celsius"},
    "toronto": {"lat": 43.6532, "lon": -79.3832, "tz": "America/Toronto", "unit": "celsius"},
    "wellington": {"lat": -41.2865, "lon": 174.7762, "tz": "Pacific/Auckland", "unit": "celsius"},
    "sao-paulo": {"lat": -23.5505, "lon": -46.6333, "tz": "America/Sao_Paulo", "unit": "celsius"},
    "ankara": {"lat": 39.9334, "lon": 32.8597, "tz": "Europe/Istanbul", "unit": "celsius"},
    "milan": {"lat": 45.4642, "lon": 9.1900, "tz": "Europe/Rome", "unit": "celsius"},
    "tel-aviv": {"lat": 32.0853, "lon": 34.7818, "tz": "Asia/Jerusalem", "unit": "celsius"},
    "new-york-city": {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York", "unit": "fahrenheit"},
    "nyc": {"lat": 40.7128, "lon": -74.0060, "tz": "America/New_York", "unit": "fahrenheit"},
    "miami": {"lat": 25.7617, "lon": -80.1918, "tz": "America/New_York", "unit": "fahrenheit"},
    "dallas": {"lat": 32.7767, "lon": -96.7970, "tz": "America/Chicago", "unit": "fahrenheit"},
    "chicago": {"lat": 41.8781, "lon": -87.6298, "tz": "America/Chicago", "unit": "fahrenheit"},
    "atlanta": {"lat": 33.7490, "lon": -84.3880, "tz": "America/New_York", "unit": "fahrenheit"},
    "seattle": {"lat": 47.6062, "lon": -122.3321, "tz": "America/Los_Angeles", "unit": "fahrenheit"},
}


async def seed_known_cities(db: AsyncSession) -> None:
    for city_name, info in KNOWN_CITIES.items():
        stmt = pg_insert(CityCoordinate).values(
            city_name=city_name,
            latitude=Decimal(str(info["lat"])),
            longitude=Decimal(str(info["lon"])),
            timezone=info["tz"],
            temp_unit=info["unit"],
        ).on_conflict_do_update(
            index_elements=["city_name"],
            set_={"latitude": Decimal(str(info["lat"])), "longitude": Decimal(str(info["lon"]))},
        )
        await db.execute(stmt)
    await db.commit()


def parse_event_slug(slug: str) -> tuple[str, date]:
    match = re.match(r"highest-temperature-in-(.+)-on-(.+)-(\d+)-(\d{4})", slug)
    if not match:
        raise ValueError(f"Cannot parse slug: {slug}")
    city = match.group(1)
    month_str = match.group(2)
    day = int(match.group(3))
    year = int(match.group(4))
    months = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
              "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
    month = months.get(month_str.lower(), 1)
    return city, date(year, month, day)


def compute_ensemble_probs(member_maxes: list[float], bins: list[str], temp_unit: str = "celsius") -> dict[str, float]:
    n = len(member_maxes)
    if n == 0:
        return {b: 0.0 for b in bins}

    unit_suffix = "F" if temp_unit == "fahrenheit" else "C"
    bin_values = []
    for b in bins:
        cleaned = b.replace(f"°{unit_suffix}", "").replace(f"{unit_suffix}", "").strip()
        if "or below" in cleaned:
            bin_values.append(("below", int(cleaned.split()[0])))
        elif "or higher" in cleaned:
            bin_values.append(("above", int(cleaned.split()[0])))
        else:
            bin_values.append(("exact", int(cleaned)))

    counts = {b: 0 for b in bins}
    for temp in member_maxes:
        rounded = round(temp)
        for i, (kind, val) in enumerate(bin_values):
            if kind == "below" and rounded <= val:
                counts[bins[i]] += 1
                break
            elif kind == "exact" and rounded == val:
                counts[bins[i]] += 1
                break
            elif kind == "above" and rounded >= val:
                counts[bins[i]] += 1
                break

    return {b: counts[b] / n for b in bins}


def compute_weather_bias(forecast_prob: float, market_prob: float) -> tuple[str, int]:
    delta_bps = int(abs(forecast_prob - market_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if forecast_prob > market_prob:
        return "FORECAST_HIGHER", delta_bps
    return "MARKET_HIGHER", delta_bps


class WeatherCollector(BaseCollector):
    name = "weather_collector"
    interval_seconds = 300

    def __init__(self):
        self._gamma = GammaClient()
        self._seeded = False

    async def teardown(self) -> None:
        await self._gamma.close()

    async def collect(self, db: AsyncSession) -> None:
        if not self._seeded:
            await seed_known_cities(db)
            self._seeded = True

        events = await self._gamma.get_events(tag="temperature", limit=100, active=True)
        if not events:
            return

        async with httpx.AsyncClient(timeout=15.0) as client:
            for event in events:
                try:
                    await self._process_event(db, client, event)
                except Exception as e:
                    logger.warning(f"[weather] failed to process {event.get('slug', '?')}: {e}")

        await db.commit()

    async def _process_event(self, db: AsyncSession, client: httpx.AsyncClient, event: dict) -> None:
        slug = event.get("slug", "")
        if not slug.startswith("highest-temperature-in-"):
            return

        city, event_date = parse_event_slug(slug)
        city_info = KNOWN_CITIES.get(city)
        if not city_info:
            return

        markets = event.get("markets", [])
        if not markets:
            return

        markets.sort(key=lambda m: int(m.get("groupItemThreshold", 0)))
        bins = [m.get("groupItemTitle", "") for m in markets]
        market_probs = {}
        for m in markets:
            title = m.get("groupItemTitle", "")
            prices = m.get("outcomePrices", ["0", "1"])
            market_probs[title] = float(prices[0]) if prices else 0.0

        forecast_days = (event_date - date.today()).days + 1
        if forecast_days < 1 or forecast_days > 16:
            return

        resp = await client.get(OPEN_METEO_URL, params={
            "latitude": city_info["lat"],
            "longitude": city_info["lon"],
            "hourly": "temperature_2m",
            "models": "ecmwf_ifs025",
            "forecast_days": min(forecast_days, 16),
            "temperature_unit": city_info["unit"],
        })
        resp.raise_for_status()
        ensemble_data = resp.json()

        member_maxes = self._extract_member_maxes(ensemble_data, event_date)
        if not member_maxes:
            return

        forecast_probs = compute_ensemble_probs(member_maxes, bins, city_info["unit"])

        bins_result = []
        max_bias_bps = 0
        max_bias_range = None
        max_bias_direction = "NEUTRAL"

        for m in markets:
            title = m.get("groupItemTitle", "")
            mp = market_probs.get(title, 0.0)
            fp = forecast_probs.get(title, 0.0)
            direction, bps = compute_weather_bias(fp, mp)

            bins_result.append({
                "range": title,
                "market_id": m.get("id"),
                "market_prob": mp,
                "forecast_prob": round(fp, 4),
                "bias_direction": direction,
                "bias_bps": bps,
            })

            if bps > max_bias_bps:
                max_bias_bps = bps
                max_bias_range = title
                max_bias_direction = direction

        stmt = pg_insert(WeatherEvent).values(
            event_slug=slug,
            city=city,
            event_date=event_date,
            polymarket_event_id=event.get("id"),
            temp_unit=city_info["unit"],
            bins_json=bins_result,
            max_bias_range=max_bias_range,
            max_bias_direction=max_bias_direction,
            max_bias_bps=max_bias_bps,
            data_updated_at=datetime.now(UTC),
        ).on_conflict_do_update(
            index_elements=["event_slug"],
            set_={
                "bins_json": bins_result,
                "max_bias_range": max_bias_range,
                "max_bias_direction": max_bias_direction,
                "max_bias_bps": max_bias_bps,
                "data_updated_at": datetime.now(UTC),
            },
        )
        await db.execute(stmt)

    def _extract_member_maxes(self, ensemble_data: dict, target_date: date) -> list[float]:
        hourly = ensemble_data.get("hourly", {})
        times = hourly.get("time", [])
        target_str = target_date.isoformat()

        indices = [i for i, t in enumerate(times) if t.startswith(target_str)]
        if not indices:
            return []

        maxes = []
        control = hourly.get("temperature_2m", [])
        if control:
            vals = [control[i] for i in indices if i < len(control) and control[i] is not None]
            if vals:
                maxes.append(max(vals))

        for key in sorted(hourly.keys()):
            if key.startswith("temperature_2m_member"):
                member_data = hourly[key]
                vals = [member_data[i] for i in indices if i < len(member_data) and member_data[i] is not None]
                if vals:
                    maxes.append(max(vals))

        return maxes
