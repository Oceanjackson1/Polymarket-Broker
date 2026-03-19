# Plan 4: Weather Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `WeatherCollector` that polls Polymarket Gamma for temperature markets and Open-Meteo Ensemble API for forecast probabilities, computes bias signals, and serves 4 REST endpoints under `/api/v1/data/weather/`.

**Architecture:** One `asyncio` lifespan task polls every 5 minutes. It dynamically discovers active temperature markets from Polymarket, parses city/date from standardized titles (`"Highest temperature in [City] on [Date]?"`), fetches 51-member ensemble forecasts from Open-Meteo, computes per-bin probabilities, and upserts into `weather_markets` table. City coordinates are resolved via built-in mapping table with Open-Meteo Geocoding API fallback cached in `city_coordinates` table.

**Tech Stack:** Same as Plan 3 — FastAPI lifespan tasks, SQLAlchemy 2 async, `pg_insert` upserts, `httpx` for HTTP, PostgreSQL JSONB for temp_bins.

**Spec Reference:** Section 7.5 of `docs/superpowers/specs/2026-03-17-polymarket-broker-design.md`.

---

## Design Decisions

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | Poll every 5 minutes | Matches SportsCollector; weather forecasts don't change sub-minute |
| 2 | Dynamic city discovery from Polymarket | Only collect data for markets that actually exist; zero waste |
| 3 | Built-in coords + Geocoding fallback + DB cache | Startup-ready for 20+ known cities; auto-adapts to new ones |
| 4 | Ensemble API (51 members) for probabilities | Most accurate; direct statistical distribution, no model assumptions |
| 5 | Bias threshold 300 bps (same as NBA) | Consistency; will revisit via backtesting |
| 6 | Date as primary API dimension | Users ask "which city has opportunities today?" not "what dates does Tokyo have?" |
| 7 | Single table upsert (no history) | YAGNI; no consumer needs forecast change tracking yet |
| 8 | temp_bins as JSONB column | Flexible; bin count may vary per event |
| 9 | Serial HTTP requests per city | 20 cities × ~0.5s = ~10s total; 5-min interval makes parallel unnecessary |
| 10 | Reuse `compute_bias` from NBA | Same logic, same threshold, consistent signal semantics |

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `api/data/weather/__init__.py` | Create | Package marker |
| `api/data/weather/models.py` | Create | `WeatherMarket` + `CityCoordinate` ORM models |
| `api/data/weather/schemas.py` | Create | Pydantic response shapes |
| `api/data/weather/router.py` | Create | 4 weather endpoints |
| `data_pipeline/weather_collector.py` | Create | Polls Polymarket Gamma + Open-Meteo Ensemble |
| `data_pipeline/weather_coords.py` | Create | `BUILTIN_COORDS` + `get_coordinates()` + geocoding fallback |
| `api/main.py` | Modify | Register weather router; add WeatherCollector to lifespan |
| `db/postgres.py` | Modify | Register 2 new ORM models in `_register_models()` |
| `core/config.py` | Modify | Add `open_meteo_ensemble_base`, `open_meteo_geocoding_base` |
| `tests/conftest.py` | Modify | Import 2 new models in `setup_test_db` |
| `tests/test_data/test_weather_parser.py` | Create | Title parsing + probability computation (pure functions) |
| `tests/test_data/test_weather_coordinates.py` | Create | Coordinate resolution tests |
| `tests/test_data/test_weather_collector.py` | Create | WeatherCollector unit tests |
| `tests/test_data/test_weather_api.py` | Create | Weather endpoint HTTP tests |

---

### Task 1: ORM Models + DB Registration

**Files:**
- Create: `api/data/weather/__init__.py`
- Create: `api/data/weather/models.py`
- Modify: `db/postgres.py`
- Modify: `tests/conftest.py`
- Create: `tests/test_data/test_weather_models.py`

- [ ] **Step 1: Write the failing test**

Create `api/data/weather/__init__.py` (empty) and `tests/test_data/test_weather_models.py`:

```python
# tests/test_data/test_weather_models.py
import pytest
from datetime import datetime, UTC, date
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_weather_market_crud(test_db_session):
    from api.data.weather.models import WeatherMarket

    db = test_db_session
    market = WeatherMarket(
        city="Tokyo",
        date=date(2026, 3, 19),
        event_id="evt_123",
        temp_unit="C",
        temp_bins=[
            {"range": "18°C", "market_id": "0x1", "market_prob": 0.15,
             "forecast_prob": 0.25, "bias_direction": "FORECAST_HIGHER", "bias_bps": 1000},
        ],
        max_bias_range="18°C",
        max_bias_direction="FORECAST_HIGHER",
        max_bias_bps=1000,
        data_updated_at=datetime.now(UTC),
    )
    db.add(market)
    await db.commit()

    result = await db.execute(select(WeatherMarket).where(WeatherMarket.city == "Tokyo"))
    row = result.scalar_one()
    assert row.city == "Tokyo"
    assert row.date == date(2026, 3, 19)
    assert row.max_bias_bps == 1000
    assert len(row.temp_bins) == 1
    assert row.temp_bins[0]["range"] == "18°C"


async def test_weather_market_upsert(test_db_session):
    from api.data.weather.models import WeatherMarket
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    db = test_db_session
    values = dict(
        city="NYC", date=date(2026, 3, 19), event_id="evt_456",
        temp_bins=[{"range": "15°C", "market_prob": 0.10, "forecast_prob": 0.08}],
        max_bias_range="15°C", max_bias_direction="NEUTRAL", max_bias_bps=200,
        data_updated_at=datetime.now(UTC),
    )
    stmt = pg_insert(WeatherMarket).values(**values).on_conflict_do_update(
        constraint="uq_weather_city_date",
        set_={"max_bias_bps": 500, "data_updated_at": datetime.now(UTC)},
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(WeatherMarket).where(WeatherMarket.city == "NYC")
    )
    row = result.scalar_one()
    assert row.max_bias_bps == 500


async def test_city_coordinate_crud(test_db_session):
    from api.data.weather.models import CityCoordinate

    db = test_db_session
    coord = CityCoordinate(
        city="Reykjavik",
        latitude=64.13,
        longitude=-21.90,
        source="geocoding_api",
        created_at=datetime.now(UTC),
    )
    db.add(coord)
    await db.commit()

    result = await db.execute(
        select(CityCoordinate).where(CityCoordinate.city == "Reykjavik")
    )
    row = result.scalar_one()
    assert row.latitude == pytest.approx(64.13, abs=0.01)
    assert row.source == "geocoding_api"
```

- [ ] **Step 2: Write the models**

Create `api/data/weather/models.py`:

```python
# api/data/weather/models.py
from datetime import datetime, date as date_type
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from db.postgres import Base


class WeatherMarket(Base):
    __tablename__ = "weather_markets"

    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    event_id = Column(String)
    temp_unit = Column(String, default="C")
    temp_bins = Column(JSONB, nullable=False)  # [{range, market_id, market_prob, forecast_prob, bias_direction, bias_bps}]
    max_bias_range = Column(String)
    max_bias_direction = Column(String, default="NEUTRAL")
    max_bias_bps = Column(Integer, default=0)
    data_updated_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("city", "date", name="uq_weather_city_date"),
    )


class CityCoordinate(Base):
    __tablename__ = "city_coordinates"

    city = Column(String, primary_key=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source = Column(String)   # "builtin" or "geocoding_api"
    created_at = Column(DateTime(timezone=True))
```

- [ ] **Step 3: Register models + run tests**

Modify `db/postgres.py`: add `from api.data.weather.models import WeatherMarket, CityCoordinate` to `_register_models()`.

Modify `tests/conftest.py`: add the same import to `setup_test_db`.

Run: `pytest tests/test_data/test_weather_models.py -v` — all 3 tests must pass.

---

### Task 2: City Coordinates Module

**Files:**
- Create: `data_pipeline/weather_coords.py`
- Create: `tests/test_data/test_weather_coordinates.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_weather_coordinates.py
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, UTC

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
    mock_resp.json.return_value = {"results": [{"latitude": 64.13, "longitude": -21.90}]}
    mock_resp.raise_for_status = lambda: None

    with patch("data_pipeline.weather_coords.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_resp
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        coords = await get_coordinates("Reykjavik", test_db_session)
        assert coords[0] == pytest.approx(64.13, abs=0.01)

    # Verify cached in DB
    result = await test_db_session.execute(
        select(CityCoordinate).where(CityCoordinate.city == "Reykjavik")
    )
    cached = result.scalar_one()
    assert cached.source == "geocoding_api"


async def test_get_coordinates_cached_in_db(test_db_session):
    from data_pipeline.weather_coords import get_coordinates
    from api.data.weather.models import CityCoordinate

    # Pre-insert into DB
    coord = CityCoordinate(
        city="TestCity", latitude=10.0, longitude=20.0,
        source="geocoding_api", created_at=datetime.now(UTC),
    )
    test_db_session.add(coord)
    await test_db_session.commit()

    # Should return from DB without calling geocoding API
    coords = await get_coordinates("TestCity", test_db_session)
    assert coords == (10.0, 20.0)
```

- [ ] **Step 2: Implement weather_coords.py**

```python
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
    """Resolve city name to (lat, lon). Lookup order: builtin → DB → Geocoding API."""
    # 1. Built-in
    if city in BUILTIN_COORDS:
        return BUILTIN_COORDS[city]

    # 2. DB cache
    result = await db.execute(
        select(CityCoordinate).where(CityCoordinate.city == city)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return (cached.latitude, cached.longitude)

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

    # Cache in DB
    coord = CityCoordinate(
        city=city, latitude=lat, longitude=lon,
        source="geocoding_api", created_at=datetime.now(UTC),
    )
    db.add(coord)
    await db.commit()

    return (lat, lon)
```

- [ ] **Step 3: Add config + run tests**

Modify `core/config.py`: add two fields to `Settings`:

```python
open_meteo_ensemble_base: str = "https://ensemble-api.open-meteo.com"
open_meteo_geocoding_base: str = "https://geocoding-api.open-meteo.com"
```

Run: `pytest tests/test_data/test_weather_coordinates.py -v` — all 4 tests must pass.

---

### Task 3: Title Parser + Probability Functions

**Files:**
- Create: `tests/test_data/test_weather_parser.py`

These are pure functions that will live in `data_pipeline/weather_collector.py`. Test them first.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_data/test_weather_parser.py
import pytest
from math import inf


def test_parse_weather_event_standard():
    from data_pipeline.weather_collector import parse_weather_event
    result = parse_weather_event("Highest temperature in Tokyo on March 19?")
    assert result == ("Tokyo", "March 19")


def test_parse_weather_event_multi_word_city():
    from data_pipeline.weather_collector import parse_weather_event
    result = parse_weather_event("Highest temperature in Tel Aviv on March 16?")
    assert result == ("Tel Aviv", "March 16")


def test_parse_weather_event_non_weather():
    from data_pipeline.weather_collector import parse_weather_event
    assert parse_weather_event("Warriors vs. Celtics") is None


def test_parse_weather_event_tornado():
    from data_pipeline.weather_collector import parse_weather_event
    assert parse_weather_event("How many Tornadoes in the US in March?") is None


def test_parse_date_str():
    from data_pipeline.weather_collector import parse_date_str
    from datetime import date
    # parse_date_str should handle "March 19" relative to current year
    result = parse_date_str("March 19")
    assert result.month == 3
    assert result.day == 19


def test_parse_temp_range():
    from data_pipeline.weather_collector import parse_temp_range
    assert parse_temp_range("Will the highest temperature in Tokyo be 18°C on March 19?") == 18
    assert parse_temp_range("Will the highest temperature in Tokyo be 13°C or below on March 19?") == 13
    assert parse_temp_range("Will the highest temperature in Tokyo be 23°C or higher on March 19?") == 23


def test_compute_bin_probabilities_uniform():
    from data_pipeline.weather_collector import compute_bin_probabilities
    # 51 members: 17 at 18, 17 at 19, 17 at 20
    ensemble = [18.3] * 17 + [19.1] * 17 + [20.4] * 17
    bins = [(18, False), (19, False), (20, False)]  # (temp, is_boundary)
    probs = compute_bin_probabilities(ensemble, bins)
    assert len(probs) == 3
    assert all(abs(p - 17 / 51) < 0.001 for p in probs)


def test_compute_bin_probabilities_boundary():
    from data_pipeline.weather_collector import compute_bin_probabilities
    # All 51 members at 15.2 → rounds to 15
    ensemble = [15.2] * 51
    bins = [(13, True), (14, False), (15, False), (16, False), (23, True)]
    # "13 or below" = (-inf, 13], "23 or higher" = [23, inf)
    probs = compute_bin_probabilities(ensemble, bins)
    assert probs[2] == pytest.approx(1.0)  # all in 15°C bin
    assert probs[0] == 0.0
    assert probs[4] == 0.0


def test_compute_bias_reuse():
    """Verify weather uses same bias logic as NBA."""
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(0.25, 0.15)
    assert direction in ("HOME_UNDERPRICED", "AWAY_UNDERPRICED")
    assert bps == 1000
```

- [ ] **Step 2: Implement pure functions in weather_collector.py**

Add to `data_pipeline/weather_collector.py` (collector class comes in Task 4):

```python
import re
from datetime import date, datetime

TITLE_PATTERN = re.compile(
    r"Highest temperature in (.+?) on (.+)\?",
    re.IGNORECASE,
)

TEMP_PATTERN = re.compile(r"(\d+)°[CF]")


def parse_weather_event(title: str) -> tuple[str, str] | None:
    m = TITLE_PATTERN.match(title)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def parse_date_str(date_str: str) -> date:
    """Parse 'March 19' into a date object using current year."""
    now = datetime.now()
    dt = datetime.strptime(f"{date_str} {now.year}", "%B %d %Y")
    return dt.date()


def parse_temp_range(question: str) -> int | None:
    m = TEMP_PATTERN.search(question)
    if not m:
        return None
    return int(m.group(1))


def compute_bin_probabilities(
    ensemble_values: list[float],
    bins: list[tuple[int, bool]],
) -> list[float]:
    """
    Map 51 ensemble members to temperature bins.
    bins: [(temp, is_boundary), ...] where is_boundary=True for "X or below"/"X or higher".
    First bin with is_boundary=True is the lower boundary (≤ temp).
    Last bin with is_boundary=True is the upper boundary (≥ temp).
    """
    total = len(ensemble_values)
    if total == 0:
        return [0.0] * len(bins)

    rounded = [round(v) for v in ensemble_values]
    probs = []
    for i, (temp, is_boundary) in enumerate(bins):
        if is_boundary and i == 0:
            count = sum(1 for v in rounded if v <= temp)
        elif is_boundary and i == len(bins) - 1:
            count = sum(1 for v in rounded if v >= temp)
        else:
            count = sum(1 for v in rounded if v == temp)
        probs.append(count / total)
    return probs
```

Run: `pytest tests/test_data/test_weather_parser.py -v` — all tests must pass.

---

### Task 4: WeatherCollector

**Files:**
- Create (extend): `data_pipeline/weather_collector.py` (add `WeatherCollector` class)
- Create: `tests/test_data/test_weather_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_weather_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC, date
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _mock_gamma_events():
    """Fake Polymarket events response with one weather event."""
    return [
        {
            "id": "evt_weather_tokyo",
            "title": "Highest temperature in Tokyo on March 19?",
            "closed": False,
            "markets": [
                {"id": "0x_13below", "question": "Will the highest temperature in Tokyo be 13°C or below on March 19?",
                 "outcomePrices": ["0.02", "0.98"]},
                {"id": "0x_14", "question": "Will the highest temperature in Tokyo be 14°C on March 19?",
                 "outcomePrices": ["0.03", "0.97"]},
                {"id": "0x_18", "question": "Will the highest temperature in Tokyo be 18°C on March 19?",
                 "outcomePrices": ["0.25", "0.75"]},
                {"id": "0x_23above", "question": "Will the highest temperature in Tokyo be 23°C or higher on March 19?",
                 "outcomePrices": ["0.02", "0.98"]},
            ],
        },
        {
            "id": "evt_sports",
            "title": "Warriors vs. Celtics",
            "closed": False,
            "markets": [],
        },
    ]


def _mock_ensemble_response():
    """Fake Open-Meteo ensemble: 51 members clustered around 18°C."""
    return {
        "daily": {
            "temperature_2m_max": [18.1 + i * 0.05 for i in range(51)]
        }
    }


async def test_weather_collector_upserts(test_db_session):
    from data_pipeline.weather_collector import WeatherCollector
    from api.data.weather.models import WeatherMarket

    collector = WeatherCollector()

    # Mock Gamma
    collector._gamma = AsyncMock()
    collector._gamma.get_events = AsyncMock(return_value=_mock_gamma_events())

    # Mock Open-Meteo
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_ensemble_response()
    mock_resp.raise_for_status = lambda: None

    with patch("data_pipeline.weather_collector.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_resp
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        await collector.collect(test_db_session)

    result = await test_db_session.execute(select(WeatherMarket))
    markets = result.scalars().all()
    assert len(markets) == 1
    assert markets[0].city == "Tokyo"
    assert len(markets[0].temp_bins) == 4
    assert markets[0].max_bias_bps >= 0


async def test_weather_collector_skips_non_weather(test_db_session):
    from data_pipeline.weather_collector import WeatherCollector
    from api.data.weather.models import WeatherMarket

    collector = WeatherCollector()
    collector._gamma = AsyncMock()
    collector._gamma.get_events = AsyncMock(return_value=[
        {"id": "evt_1", "title": "Warriors vs. Celtics", "closed": False, "markets": []},
    ])

    await collector.collect(test_db_session)

    result = await test_db_session.execute(select(WeatherMarket))
    assert result.scalars().all() == []
```

- [ ] **Step 2: Implement WeatherCollector class**

Add to `data_pipeline/weather_collector.py`:

```python
from datetime import datetime, UTC
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from data_pipeline.weather_coords import get_coordinates
from api.data.weather.models import WeatherMarket
from core.polymarket.gamma_client import GammaClient
from core.config import get_settings as _get_settings

ENSEMBLE_URL = f"{_get_settings().open_meteo_ensemble_base}/v1/ensemble"
BIAS_THRESHOLD_BPS = 300


def _compute_weather_bias(
    forecast_prob: float | None, market_prob: float | None
) -> tuple[str, int]:
    if forecast_prob is None or market_prob is None:
        return "NEUTRAL", 0
    delta_bps = round(abs(forecast_prob - market_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if forecast_prob > market_prob:
        return "FORECAST_HIGHER", delta_bps
    return "MARKET_HIGHER", delta_bps


class WeatherCollector(BaseCollector):
    name = "weather_collector"
    interval_seconds = 300  # 5 min

    def __init__(self):
        self._gamma = GammaClient()

    async def teardown(self) -> None:
        await self._gamma.close()

    async def collect(self, db: AsyncSession) -> None:
        # 1. Fetch events from Polymarket
        events = await self._gamma.get_events(closed="false", limit=100)

        # 2. Filter to weather events
        weather_events = []
        for e in events:
            parsed = parse_weather_event(e.get("title", ""))
            if parsed:
                weather_events.append((parsed, e))

        if not weather_events:
            return

        # 3. Resolve coordinates (deduplicated by city)
        city_coords: dict[str, tuple[float, float] | None] = {}
        for (city, _date_str), _event in weather_events:
            if city not in city_coords:
                city_coords[city] = await get_coordinates(city, db)

        # 4. Process each weather event
        for (city, date_str), event in weather_events:
            coords = city_coords.get(city)
            if not coords:
                continue

            target_date = parse_date_str(date_str)
            markets = event.get("markets", [])
            if not markets:
                continue

            # 5. Fetch ensemble forecast
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(ENSEMBLE_URL, params={
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "daily": "temperature_2m_max",
                    "start_date": target_date.isoformat(),
                    "end_date": target_date.isoformat(),
                    "models": "icon_seamless",
                })
                resp.raise_for_status()
                ensemble_data = resp.json()

            ensemble_values = ensemble_data.get("daily", {}).get("temperature_2m_max", [])
            if not ensemble_values:
                continue

            # 6. Parse bins from market questions
            bins = []
            for m in markets:
                temp = parse_temp_range(m.get("question", ""))
                if temp is None:
                    continue
                q = m.get("question", "").lower()
                is_boundary = "or below" in q or "or higher" in q
                bins.append((temp, is_boundary))

            # 7. Compute forecast probabilities
            forecast_probs = compute_bin_probabilities(ensemble_values, bins)

            # 8. Build temp_bins and compute bias
            temp_bins = []
            for i, m in enumerate(markets):
                temp = parse_temp_range(m.get("question", ""))
                if temp is None:
                    continue
                market_prob = float(m.get("outcomePrices", ["0"])[0])
                fp = forecast_probs[i] if i < len(forecast_probs) else None
                bias_dir, bias_bps = _compute_weather_bias(fp, market_prob)
                q = m.get("question", "")
                range_label = f"{temp}°C"
                if "or below" in q.lower():
                    range_label = f"{temp}°C or below"
                elif "or higher" in q.lower():
                    range_label = f"{temp}°C or higher"
                temp_bins.append({
                    "range": range_label,
                    "market_id": m["id"],
                    "market_prob": market_prob,
                    "forecast_prob": fp,
                    "bias_direction": bias_dir,
                    "bias_bps": bias_bps,
                })

            if not temp_bins:
                continue

            max_bin = max(temp_bins, key=lambda b: b["bias_bps"])

            # 9. Upsert
            stmt = pg_insert(WeatherMarket).values(
                city=city,
                date=target_date,
                event_id=event["id"],
                temp_unit="C",
                temp_bins=temp_bins,
                max_bias_range=max_bin["range"],
                max_bias_direction=max_bin["bias_direction"],
                max_bias_bps=max_bin["bias_bps"],
                data_updated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                constraint="uq_weather_city_date",
                set_={
                    "event_id": event["id"],
                    "temp_bins": temp_bins,
                    "max_bias_range": max_bin["range"],
                    "max_bias_direction": max_bin["bias_direction"],
                    "max_bias_bps": max_bin["bias_bps"],
                    "data_updated_at": datetime.now(UTC),
                },
            )
            await db.execute(stmt)

        await db.commit()
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_data/test_weather_collector.py -v` — both tests must pass.

---

### Task 5: Pydantic Schemas + API Endpoints

**Files:**
- Create: `api/data/weather/schemas.py`
- Create: `api/data/weather/router.py`
- Modify: `api/main.py`
- Create: `tests/test_data/test_weather_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_weather_api.py
import pytest
from datetime import datetime, UTC, date

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture
async def seeded_weather_data(test_db_session):
    from api.data.weather.models import WeatherMarket

    market = WeatherMarket(
        city="Tokyo", date=date(2026, 3, 19), event_id="evt_123",
        temp_unit="C",
        temp_bins=[
            {"range": "18°C", "market_id": "0x1", "market_prob": 0.15,
             "forecast_prob": 0.25, "bias_direction": "FORECAST_HIGHER", "bias_bps": 1000},
            {"range": "19°C", "market_id": "0x2", "market_prob": 0.20,
             "forecast_prob": 0.22, "bias_direction": "NEUTRAL", "bias_bps": 200},
        ],
        max_bias_range="18°C", max_bias_direction="FORECAST_HIGHER", max_bias_bps=1000,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(market)
    await test_db_session.commit()
    return market


async def test_dates_endpoint(authed_client, seeded_weather_data):
    resp = await authed_client.get("/api/v1/data/weather/dates")
    assert resp.status_code == 200
    data = resp.json()
    assert "dates" in data
    assert len(data["dates"]) >= 1
    assert data["dates"][0]["date"] == "2026-03-19"
    assert data["dates"][0]["active_cities"] >= 1


async def test_cities_endpoint(authed_client, seeded_weather_data):
    resp = await authed_client.get("/api/v1/data/weather/dates/2026-03-19/cities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["date"] == "2026-03-19"
    assert len(data["cities"]) >= 1
    assert data["cities"][0]["city"] == "Tokyo"
    assert data["cities"][0]["max_bias_bps"] == 1000


async def test_fusion_endpoint(authed_client, seeded_weather_data):
    resp = await authed_client.get("/api/v1/data/weather/dates/2026-03-19/cities/Tokyo/fusion")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Tokyo"
    assert "temp_bins" in data
    assert len(data["temp_bins"]) == 2
    assert "max_bias" in data
    assert data["max_bias"]["magnitude_bps"] == 1000


async def test_fusion_city_not_found(authed_client, seeded_weather_data):
    resp = await authed_client.get("/api/v1/data/weather/dates/2026-03-19/cities/Atlantis/fusion")
    assert resp.status_code == 404


async def test_fusion_date_not_found(authed_client, seeded_weather_data):
    resp = await authed_client.get("/api/v1/data/weather/dates/2099-01-01/cities/Tokyo/fusion")
    assert resp.status_code == 404
```

- [ ] **Step 2: Implement schemas**

```python
# api/data/weather/schemas.py
from pydantic import BaseModel
from datetime import date as date_type


class TempBinSchema(BaseModel):
    range: str
    market_id: str | None = None
    market_prob: float | None = None
    forecast_prob: float | None = None
    bias_direction: str = "NEUTRAL"
    bias_bps: int = 0


class MaxBiasSchema(BaseModel):
    range: str
    direction: str
    magnitude_bps: int


class DateSummary(BaseModel):
    date: date_type
    active_cities: int
    max_bias_bps: int


class DatesResponse(BaseModel):
    dates: list[DateSummary]
    data_updated_at: str | None = None


class CitySummary(BaseModel):
    city: str
    max_bias_bps: int
    max_bias_range: str | None = None
    max_bias_direction: str = "NEUTRAL"


class CitiesResponse(BaseModel):
    date: date_type
    cities: list[CitySummary]
    data_updated_at: str | None = None


class FusionResponse(BaseModel):
    city: str
    date: date_type
    event_id: str | None = None
    temp_bins: list[TempBinSchema]
    max_bias: MaxBiasSchema
    data_updated_at: str | None = None
```

- [ ] **Step 3: Implement router**

```python
# api/data/weather/router.py
from datetime import date as date_type
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db, require_scope
from api.data.weather.models import WeatherMarket
from api.data.weather.schemas import (
    DatesResponse, DateSummary,
    CitiesResponse, CitySummary,
    FusionResponse, TempBinSchema, MaxBiasSchema,
)

router = APIRouter(
    prefix="/data/weather",
    tags=["weather"],
    dependencies=[Depends(require_scope("data:read"))],
)


@router.get("/dates", response_model=DatesResponse)
async def list_dates(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            WeatherMarket.date,
            func.count(WeatherMarket.id).label("active_cities"),
            func.max(WeatherMarket.max_bias_bps).label("max_bias_bps"),
        )
        .group_by(WeatherMarket.date)
        .order_by(WeatherMarket.date.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    dates = [
        DateSummary(date=r.date, active_cities=r.active_cities, max_bias_bps=r.max_bias_bps or 0)
        for r in rows
    ]

    # Get latest data_updated_at
    latest = await db.execute(
        select(func.max(WeatherMarket.data_updated_at))
    )
    updated_at = latest.scalar()

    return DatesResponse(
        dates=dates,
        data_updated_at=updated_at.isoformat() if updated_at else None,
    )


@router.get("/dates/{date}/cities", response_model=CitiesResponse)
async def list_cities(date: date_type, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(WeatherMarket)
        .where(WeatherMarket.date == date)
        .order_by(WeatherMarket.max_bias_bps.desc())
    )
    result = await db.execute(stmt)
    markets = result.scalars().all()
    if not markets:
        raise HTTPException(status_code=404, detail="No weather markets for this date")

    cities = [
        CitySummary(
            city=m.city,
            max_bias_bps=m.max_bias_bps or 0,
            max_bias_range=m.max_bias_range,
            max_bias_direction=m.max_bias_direction or "NEUTRAL",
        )
        for m in markets
    ]
    latest_update = max((m.data_updated_at for m in markets if m.data_updated_at), default=None)

    return CitiesResponse(
        date=date,
        cities=cities,
        data_updated_at=latest_update.isoformat() if latest_update else None,
    )


@router.get("/dates/{date}/cities/{city}/fusion", response_model=FusionResponse)
async def get_fusion(date: date_type, city: str, db: AsyncSession = Depends(get_db)):
    stmt = select(WeatherMarket).where(
        WeatherMarket.date == date,
        WeatherMarket.city == city,
    )
    result = await db.execute(stmt)
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail=f"No weather market for {city} on {date}")

    return FusionResponse(
        city=market.city,
        date=market.date,
        event_id=market.event_id,
        temp_bins=[TempBinSchema(**b) for b in market.temp_bins],
        max_bias=MaxBiasSchema(
            range=market.max_bias_range or "",
            direction=market.max_bias_direction or "NEUTRAL",
            magnitude_bps=market.max_bias_bps or 0,
        ),
        data_updated_at=market.data_updated_at.isoformat() if market.data_updated_at else None,
    )


@router.get("/dates/{date}/cities/{city}/orderbook")
async def get_orderbook(date: date_type, city: str, db: AsyncSession = Depends(get_db)):
    stmt = select(WeatherMarket).where(
        WeatherMarket.date == date,
        WeatherMarket.city == city,
    )
    result = await db.execute(stmt)
    market = result.scalar_one_or_none()
    if not market:
        raise HTTPException(status_code=404, detail=f"No weather market for {city} on {date}")

    # Proxy to Polymarket CLOB for the first market in temp_bins
    from core.polymarket.clob_client import ClobClient
    clob = ClobClient()
    try:
        if market.temp_bins and market.temp_bins[0].get("market_id"):
            book = await clob.get_orderbook(market.temp_bins[0]["market_id"])
            return book
        raise HTTPException(status_code=404, detail="No market_id available")
    finally:
        await clob.close()
```

- [ ] **Step 4: Register router + add collector to lifespan**

Modify `api/main.py`:
- Add `from api.data.weather.router import router as weather_router`
- Add `app.include_router(weather_router, prefix=settings.api_v1_prefix)`
- Add `WeatherCollector().run(AsyncSessionLocal)` to lifespan tasks list

- [ ] **Step 5: Run all tests**

Run: `pytest tests/test_data/test_weather_api.py -v` — all 5 tests must pass.

Run: `pytest tests/ -v` — full suite must pass with no regressions.

---

### Task 6: Integration Verification

- [ ] **Step 1: Verify config**

Ensure `.env.example` includes:
```
OPEN_METEO_ENSEMBLE_BASE=https://ensemble-api.open-meteo.com
OPEN_METEO_GEOCODING_BASE=https://geocoding-api.open-meteo.com
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all existing tests pass + 15–20 new weather tests pass.

- [ ] **Step 3: Verify model registration**

Confirm `db/postgres.py` `_register_models()` imports both `WeatherMarket` and `CityCoordinate`.

Confirm `tests/conftest.py` `setup_test_db` imports the same models.

---

## Summary

| Metric | Value |
|--------|-------|
| New files | 8 (models, schemas, router, collector, coords, 4 test files) |
| Modified files | 4 (main.py, postgres.py, config.py, conftest.py) |
| New DB tables | 2 (weather_markets, city_coordinates) |
| New API endpoints | 4 |
| New tests | ~18-22 |
| Estimated test coverage | ≥75% for new code |
| External APIs | Open-Meteo Ensemble (free, no key) + Open-Meteo Geocoding (free, no key) |
