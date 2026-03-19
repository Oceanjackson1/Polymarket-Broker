# Plan 4A: Weather Forecast × Polymarket Temperature Fusion

> **For agentic workers:** REQUIRED: Use superpowers:executing-plans to implement this plan.

**Goal:** Add Open-Meteo ensemble forecast data fused with Polymarket temperature prediction markets. 4 endpoints under `/api/v1/data/weather/`, 1 background collector, 2 ORM models.

**Core differentiator:** Only platform combining 51-member ensemble weather forecast probabilities with Polymarket temperature market prices to surface pricing bias.

---

## API Research Summary (verified 2026-03-19)

### Open-Meteo Ensemble API
- **URL:** `https://ensemble-api.open-meteo.com/v1/ensemble`
- **Model:** `ecmwf_ifs025` (50 members + control = 51 total)
- **Rate limit:** 10,000/day (free), 600/min
- **No API key required**
- **Response:** `hourly.temperature_2m` (control) + `temperature_2m_member01..50`

### Polymarket Temperature Markets
- **~223 active daily temperature markets** across 20+ cities
- **Event slug pattern:** `highest-temperature-in-{city}-on-{month}-{day}-{year}`
- **11 sub-markets per event** — each is a 1°C/1°F temperature bin
- **negRisk: true** — mutually exclusive outcomes, exactly one resolves Yes
- **outcomePrices** = implied probability per bin
- **Cities:** Seoul, Tokyo, Hong Kong, Shanghai, Singapore, London, Toronto, NYC, Miami, Dallas, Chicago, Atlanta, Seattle, Tel Aviv, Wellington, Sao Paulo, Ankara, Milan
- **US cities use Fahrenheit**, international use Celsius

### Bias Calculation
For each temperature bin:
```
forecast_prob = count(ensemble members where max_temp rounds to bin) / 51
market_prob = float(outcomePrices[0])  # Yes price
bias_bps = abs(forecast_prob - market_prob) * 10000
direction = FORECAST_HIGHER if forecast_prob > market_prob else MARKET_HIGHER
```
Threshold: 300 bps → below = NEUTRAL

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `api/data/weather/__init__.py` | Create | Package marker |
| `api/data/weather/models.py` | Create | `WeatherEvent`, `CityCoordinate` ORM models |
| `api/data/weather/schemas.py` | Create | Pydantic response schemas |
| `api/data/weather/router.py` | Create | 4 weather endpoints |
| `data_pipeline/weather_collector.py` | Create | Polls Open-Meteo + Polymarket Gamma |
| `db/postgres.py` | Modify | Register new models |
| `api/main.py` | Modify | Register weather router + WeatherCollector in lifespan |
| `tests/conftest.py` | Modify | Import new models |
| `tests/test_data/test_weather_models.py` | Create | ORM CRUD tests |
| `tests/test_data/test_weather_collector.py` | Create | Collector unit tests |
| `tests/test_data/test_weather_api.py` | Create | Endpoint HTTP tests |

---

### Task 1: ORM Models + DB Registration

**Files:** Create `api/data/weather/models.py`, modify `db/postgres.py`, `tests/conftest.py`

- [ ] **Step 1: Write the failing test**

Create `api/data/weather/__init__.py` (empty) and `tests/test_data/test_weather_models.py`:

```python
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
            {"range": "13°C or below", "market_id": "mkt_1", "market_prob": 0.02, "forecast_prob": 0.00, "bias_direction": "NEUTRAL", "bias_bps": 200},
            {"range": "18°C", "market_id": "mkt_6", "market_prob": 0.15, "forecast_prob": 0.25, "bias_direction": "FORECAST_HIGHER", "bias_bps": 1000},
        ],
        max_bias_range="18°C",
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_weather_models.py -v --tb=short
```

- [ ] **Step 3: Create package + models**

Create `api/data/weather/__init__.py` (empty).

Create `api/data/weather/models.py`:

```python
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
```

- [ ] **Step 4: Register models in `db/postgres.py`**

Add to `_register_models()`:
```python
    from api.data.weather.models import WeatherEvent, CityCoordinate  # noqa: F401
```

- [ ] **Step 5: Update `tests/conftest.py`**

Add to the try block in `setup_test_db`:
```python
        from api.data.weather.models import WeatherEvent, CityCoordinate  # noqa: F401
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_weather_models.py -v --tb=short
```
Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add api/data/weather/ db/postgres.py tests/conftest.py tests/test_data/test_weather_models.py
git commit -m "feat: add WeatherEvent and CityCoordinate ORM models"
```

---

### Task 2: WeatherCollector

**Files:** Create `data_pipeline/weather_collector.py`, `tests/test_data/test_weather_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_weather_collector.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, datetime, UTC
from decimal import Decimal
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")

# Mock Polymarket Gamma response for temperature events
MOCK_GAMMA_EVENTS = [
    {
        "id": "272241",
        "slug": "highest-temperature-in-tokyo-on-march-20-2026",
        "title": "Highest temperature in Tokyo on March 20?",
        "markets": [
            {"id": "mkt_0", "groupItemTitle": "13°C or below", "groupItemThreshold": "0", "outcomePrices": ["0.02", "0.98"], "clobTokenIds": ["tok_0a", "tok_0b"]},
            {"id": "mkt_1", "groupItemTitle": "14°C", "groupItemThreshold": "1", "outcomePrices": ["0.03", "0.97"], "clobTokenIds": ["tok_1a", "tok_1b"]},
            {"id": "mkt_2", "groupItemTitle": "15°C", "groupItemThreshold": "2", "outcomePrices": ["0.05", "0.95"], "clobTokenIds": ["tok_2a", "tok_2b"]},
            {"id": "mkt_3", "groupItemTitle": "16°C", "groupItemThreshold": "3", "outcomePrices": ["0.10", "0.90"], "clobTokenIds": ["tok_3a", "tok_3b"]},
            {"id": "mkt_4", "groupItemTitle": "17°C", "groupItemThreshold": "4", "outcomePrices": ["0.15", "0.85"], "clobTokenIds": ["tok_4a", "tok_4b"]},
            {"id": "mkt_5", "groupItemTitle": "18°C", "groupItemThreshold": "5", "outcomePrices": ["0.25", "0.75"], "clobTokenIds": ["tok_5a", "tok_5b"]},
            {"id": "mkt_6", "groupItemTitle": "19°C", "groupItemThreshold": "6", "outcomePrices": ["0.20", "0.80"], "clobTokenIds": ["tok_6a", "tok_6b"]},
            {"id": "mkt_7", "groupItemTitle": "20°C", "groupItemThreshold": "7", "outcomePrices": ["0.10", "0.90"], "clobTokenIds": ["tok_7a", "tok_7b"]},
            {"id": "mkt_8", "groupItemTitle": "21°C", "groupItemThreshold": "8", "outcomePrices": ["0.05", "0.95"], "clobTokenIds": ["tok_8a", "tok_8b"]},
            {"id": "mkt_9", "groupItemTitle": "22°C", "groupItemThreshold": "9", "outcomePrices": ["0.03", "0.97"], "clobTokenIds": ["tok_9a", "tok_9b"]},
            {"id": "mkt_10", "groupItemTitle": "23°C or higher", "groupItemThreshold": "10", "outcomePrices": ["0.02", "0.98"], "clobTokenIds": ["tok_10a", "tok_10b"]},
        ],
    }
]

# Mock Open-Meteo ensemble response (simplified: 5 members instead of 51)
def _make_mock_ensemble(temps_by_member: list[list[float]]):
    """Generate mock Open-Meteo response. Each inner list = 24 hourly temps for one day."""
    hourly = {
        "time": [f"2026-03-20T{h:02d}:00" for h in range(24)],
        "temperature_2m": temps_by_member[0],  # control
    }
    for i, temps in enumerate(temps_by_member[1:], 1):
        hourly[f"temperature_2m_member{i:02d}"] = temps
    return {
        "latitude": 35.75,
        "longitude": 139.75,
        "hourly": hourly,
    }


# 5 members: daily maxes will be [18, 19, 18, 17, 20] → most common max = 18°C
MOCK_ENSEMBLE = _make_mock_ensemble([
    [10 + i * 0.5 for i in range(24)],  # control: max = 21.5 → rounds to 18 (just example)
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10, 10, 10, 10, 10, 10],  # max=18
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10, 10, 10, 10, 10],  # max=19
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10, 10, 10, 10, 10, 10],  # max=18
    [10, 11, 12, 13, 14, 15, 16, 17, 17, 17, 16, 15, 14, 13, 12, 11, 10, 10, 10, 10, 10, 10, 10, 10],  # max=17
])


async def test_seed_known_cities(test_db_session):
    """WeatherCollector seeds the city_coordinates table with known cities."""
    from data_pipeline.weather_collector import seed_known_cities
    from api.data.weather.models import CityCoordinate

    await seed_known_cities(test_db_session)
    result = await test_db_session.scalar(
        select(CityCoordinate).where(CityCoordinate.city_name == "Tokyo")
    )
    assert result is not None
    assert float(result.latitude) == pytest.approx(35.6762, abs=0.01)


async def test_compute_ensemble_probs():
    """Convert ensemble members to probability distribution over temperature bins."""
    from data_pipeline.weather_collector import compute_ensemble_probs

    # 5 members with max temps: 18, 19, 18, 17, 20
    member_maxes = [18.0, 19.0, 18.0, 17.0, 20.0]
    bins = ["13°C or below", "14°C", "15°C", "16°C", "17°C", "18°C", "19°C", "20°C", "21°C", "22°C", "23°C or higher"]

    probs = compute_ensemble_probs(member_maxes, bins, temp_unit="celsius")
    assert probs["17°C"] == pytest.approx(0.2, abs=0.01)  # 1/5
    assert probs["18°C"] == pytest.approx(0.4, abs=0.01)  # 2/5
    assert probs["19°C"] == pytest.approx(0.2, abs=0.01)  # 1/5
    assert probs["20°C"] == pytest.approx(0.2, abs=0.01)  # 1/5
    assert probs["14°C"] == 0.0


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
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_weather_collector.py -v --tb=short
```

- [ ] **Step 3: Create `data_pipeline/weather_collector.py`**

```python
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

# Known cities with coordinates and temperature units
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
    """Upsert known cities into city_coordinates table."""
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
    """Extract city and date from slug like 'highest-temperature-in-tokyo-on-march-19-2026'."""
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
    """Convert list of max temperatures (one per ensemble member) to probability per bin."""
    n = len(member_maxes)
    if n == 0:
        return {b: 0.0 for b in bins}

    # Parse bin boundaries
    bin_values = []
    for b in bins:
        cleaned = b.replace("°C", "").replace("°F", "").strip()
        if "or below" in cleaned:
            bin_values.append(("below", int(cleaned.split()[0])))
        elif "or higher" in cleaned:
            bin_values.append(("above", int(cleaned.split()[0])))
        else:
            bin_values.append(("exact", int(cleaned)))

    counts = {b: 0 for b in bins}
    for temp in member_maxes:
        rounded = round(temp)
        matched = False
        for i, (kind, val) in enumerate(bin_values):
            if kind == "below" and rounded <= val:
                counts[bins[i]] += 1
                matched = True
                break
            elif kind == "exact" and rounded == val:
                counts[bins[i]] += 1
                matched = True
                break
            elif kind == "above" and rounded >= val:
                counts[bins[i]] += 1
                matched = True
                break
        if not matched:
            # Shouldn't happen if bins cover full range, but assign to nearest
            pass

    return {b: counts[b] / n for b in bins}


def compute_weather_bias(forecast_prob: float, market_prob: float) -> tuple[str, int]:
    """Returns (direction, magnitude_bps)."""
    delta_bps = int(abs(forecast_prob - market_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if forecast_prob > market_prob:
        return "FORECAST_HIGHER", delta_bps
    return "MARKET_HIGHER", delta_bps


class WeatherCollector(BaseCollector):
    name = "weather_collector"
    interval_seconds = 300  # 5 minutes

    def __init__(self):
        self._gamma = GammaClient()
        self._seeded = False

    async def teardown(self) -> None:
        await self._gamma.close()

    async def collect(self, db: AsyncSession) -> None:
        # Seed cities on first run
        if not self._seeded:
            await seed_known_cities(db)
            self._seeded = True

        # 1. Fetch temperature events from Polymarket
        events = await self._gamma.get_events(tag="temperature", limit=100, active=True)
        if not events:
            return

        # 2. Process each event
        async with httpx.AsyncClient(timeout=15.0) as client:
            for event in events:
                try:
                    await self._process_event(db, client, event)
                except Exception as e:
                    logger.warning(f"[weather] failed to process event {event.get('slug', '?')}: {e}")

        await db.commit()

    async def _process_event(self, db: AsyncSession, client: httpx.AsyncClient, event: dict) -> None:
        slug = event.get("slug", "")
        if not slug.startswith("highest-temperature-in-"):
            return

        city, event_date = parse_event_slug(slug)
        city_info = KNOWN_CITIES.get(city)
        if not city_info:
            return  # Unknown city, skip

        markets = event.get("markets", [])
        if not markets:
            return

        # Sort markets by groupItemThreshold
        markets.sort(key=lambda m: int(m.get("groupItemThreshold", 0)))
        bins = [m.get("groupItemTitle", "") for m in markets]
        market_probs = {}
        for m in markets:
            title = m.get("groupItemTitle", "")
            prices = m.get("outcomePrices", ["0", "1"])
            market_probs[title] = float(prices[0]) if prices else 0.0

        # Fetch ensemble forecast
        forecast_days = (event_date - date.today()).days + 1
        if forecast_days < 1 or forecast_days > 16:
            return  # Out of forecast range

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

        # Extract max temperature per member for the target date
        member_maxes = self._extract_member_maxes(ensemble_data, event_date)
        if not member_maxes:
            return

        # Compute forecast probabilities
        forecast_probs = compute_ensemble_probs(member_maxes, bins, city_info["unit"])

        # Build bins with bias
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

        # Upsert to weather_events
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
        """Extract max temperature for each ensemble member on the target date."""
        hourly = ensemble_data.get("hourly", {})
        times = hourly.get("time", [])
        target_str = target_date.isoformat()

        # Find indices for the target date
        indices = [i for i, t in enumerate(times) if t.startswith(target_str)]
        if not indices:
            return []

        maxes = []
        # Control run
        control = hourly.get("temperature_2m", [])
        if control:
            vals = [control[i] for i in indices if i < len(control) and control[i] is not None]
            if vals:
                maxes.append(max(vals))

        # Members
        for key in sorted(hourly.keys()):
            if key.startswith("temperature_2m_member"):
                member_data = hourly[key]
                vals = [member_data[i] for i in indices if i < len(member_data) and member_data[i] is not None]
                if vals:
                    maxes.append(max(vals))

        return maxes
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_weather_collector.py -v --tb=short
```
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add data_pipeline/weather_collector.py tests/test_data/test_weather_collector.py
git commit -m "feat: add WeatherCollector (Open-Meteo ensemble × Polymarket temperature fusion)"
```

---

### Task 3: Weather API Endpoints (4) + Lifespan Wiring

**Files:** Create `api/data/weather/schemas.py`, `api/data/weather/router.py`, `tests/test_data/test_weather_api.py`. Modify `api/main.py`.

- [ ] **Step 1: Write the failing test**

```python
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


async def _seed_weather_event(test_db_session, city: str = "tokyo", event_date: str = "2026-03-20"):
    from api.data.weather.models import WeatherEvent
    d = date.fromisoformat(event_date)
    slug = f"highest-temperature-in-{city}-on-march-{d.day}-{d.year}"
    event = WeatherEvent(
        event_slug=slug,
        city=city,
        event_date=d,
        polymarket_event_id="evt_123",
        temp_unit="celsius",
        bins_json=[
            {"range": "17°C", "market_id": "mkt_4", "market_prob": 0.15, "forecast_prob": 0.20, "bias_direction": "NEUTRAL", "bias_bps": 200},
            {"range": "18°C", "market_id": "mkt_5", "market_prob": 0.15, "forecast_prob": 0.40, "bias_direction": "FORECAST_HIGHER", "bias_bps": 2500},
            {"range": "19°C", "market_id": "mkt_6", "market_prob": 0.20, "forecast_prob": 0.20, "bias_direction": "NEUTRAL", "bias_bps": 0},
        ],
        max_bias_range="18°C",
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
        "/api/v1/data/weather/dates/2026-03-20/cities/antartica/fusion",
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 404


async def test_weather_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("weather_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/weather/dates", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
```

- [ ] **Step 2: Run to verify it fails**

- [ ] **Step 3: Create `api/data/weather/schemas.py`**

```python
# api/data/weather/schemas.py
from pydantic import BaseModel
from datetime import datetime, date


class WeatherDateResponse(BaseModel):
    date: date
    city_count: int
    event_count: int


class WeatherCityResponse(BaseModel):
    city: str
    event_date: date
    max_bias_range: str | None
    max_bias_direction: str | None
    max_bias_bps: int | None
    data_updated_at: datetime


class TempBin(BaseModel):
    range: str
    market_id: str | None
    market_prob: float
    forecast_prob: float
    bias_direction: str
    bias_bps: int


class WeatherFusionResponse(BaseModel):
    city: str
    date: date
    event_slug: str
    temp_unit: str
    temp_bins: list[TempBin]
    max_bias: dict
    stale: bool
    data_updated_at: datetime
```

- [ ] **Step 4: Create `api/data/weather/router.py`**

```python
# api/data/weather/router.py
from datetime import datetime, UTC, date as date_type
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.weather.models import WeatherEvent
from api.data.weather.schemas import (
    WeatherDateResponse, WeatherCityResponse, WeatherFusionResponse, TempBin,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/weather", tags=["data-weather"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 600  # 10 minutes


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/dates", response_model=list[WeatherDateResponse])
async def get_weather_dates(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Active dates with weather markets."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(
            WeatherEvent.event_date,
            func.count(func.distinct(WeatherEvent.city)).label("city_count"),
            func.count(WeatherEvent.id).label("event_count"),
        )
        .where(WeatherEvent.event_date >= date_type.today())
        .group_by(WeatherEvent.event_date)
        .order_by(WeatherEvent.event_date)
    )
    return [
        WeatherDateResponse(date=r.event_date, city_count=r.city_count, event_count=r.event_count)
        for r in result.all()
    ]


@router.get("/dates/{event_date}/cities", response_model=list[WeatherCityResponse])
async def get_weather_cities(
    event_date: date_type = Path(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Cities with markets on that date, sorted by max bias."""
    require_scope(auth, "data:read")
    result = await db.execute(
        select(WeatherEvent)
        .where(WeatherEvent.event_date == event_date)
        .order_by(desc(WeatherEvent.max_bias_bps))
    )
    events = list(result.scalars().all())
    return [
        WeatherCityResponse(
            city=e.city,
            event_date=e.event_date,
            max_bias_range=e.max_bias_range,
            max_bias_direction=e.max_bias_direction,
            max_bias_bps=e.max_bias_bps,
            data_updated_at=e.data_updated_at,
        )
        for e in events
    ]


@router.get("/dates/{event_date}/cities/{city}/fusion", response_model=WeatherFusionResponse)
async def get_weather_fusion(
    event_date: date_type = Path(...),
    city: str = Path(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Forecast prob × market price × bias per temperature bin."""
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(WeatherEvent).where(
            WeatherEvent.city == city.lower(),
            WeatherEvent.event_date == event_date,
        )
    )
    if not event:
        raise HTTPException(404, detail="WEATHER_EVENT_NOT_FOUND")

    temp_bins = [TempBin(**b) for b in (event.bins_json or [])]

    return WeatherFusionResponse(
        city=event.city,
        date=event.event_date,
        event_slug=event.event_slug,
        temp_unit=event.temp_unit,
        temp_bins=temp_bins,
        max_bias={
            "range": event.max_bias_range,
            "direction": event.max_bias_direction,
            "magnitude_bps": event.max_bias_bps,
        },
        stale=_is_stale(event.data_updated_at),
        data_updated_at=event.data_updated_at,
    )


@router.get("/dates/{event_date}/cities/{city}/orderbook")
async def get_weather_orderbook(
    event_date: date_type = Path(...),
    city: str = Path(...),
    token_id: str = "",
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Polymarket orderbook for a weather event."""
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(WeatherEvent).where(
            WeatherEvent.city == city.lower(),
            WeatherEvent.event_date == event_date,
        )
    )
    if not event:
        raise HTTPException(404, detail="WEATHER_EVENT_NOT_FOUND")
    if not token_id:
        # Return all bin prices from stored data
        return {"bins": event.bins_json or [], "event_slug": event.event_slug}
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
```

- [ ] **Step 5: Register weather router + collector in `api/main.py`**

Add import:
```python
from api.data.weather.router import router as weather_data_router
```

Add router registration:
```python
app.include_router(weather_data_router, prefix=settings.api_v1_prefix)
```

Add WeatherCollector to lifespan tasks:
```python
        from data_pipeline.weather_collector import WeatherCollector
        # ... in tasks list:
        asyncio.create_task(WeatherCollector().run(AsyncSessionLocal)),
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_weather_api.py -v --tb=short
```
Expected: `5 passed`

- [ ] **Step 7: Run full data test suite**

```bash
ENV_FILE=.env.test pytest tests/test_data/ -q --tb=short
```

- [ ] **Step 8: Commit**

```bash
git add api/data/weather/ tests/test_data/test_weather_api.py api/main.py
git commit -m "feat: add weather forecast fusion endpoints (Open-Meteo × Polymarket temperature markets)"
```

---

## Summary

| Task | New Files | Tests Added |
|---|---|---|
| 1: ORM Models | weather/models.py | 2 |
| 2: WeatherCollector | weather_collector.py | 5 |
| 3: Weather API + Lifespan | weather/schemas.py + router.py | 5 |
| **Total** | | **~12 new tests** |

After all tasks: `ENV_FILE=.env.test pytest tests/ -v --tb=short`
