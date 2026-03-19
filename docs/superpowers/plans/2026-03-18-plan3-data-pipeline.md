# Plan 3: Data Pipeline Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add background data collectors (Sports/NBA/BTC) and 12 REST endpoints under `/api/v1/data/` that serve the collected data.

**Architecture:** Three `asyncio` lifespan tasks poll Polymarket Gamma, ESPN, and CoinGecko every 30–300s and upsert/append into three PostgreSQL tables. Twelve API endpoints read from those tables with staleness detection. All endpoints require `X-API-Key` + `data:read` scope.

**Tech Stack:** FastAPI lifespan tasks, SQLAlchemy 2 async, `sqlalchemy.dialects.postgresql.insert` for upserts, `httpx` for HTTP, PostgreSQL JSONB for outcomes/resolution.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `api/data/__init__.py` | Create | Package marker |
| `api/data/sports/__init__.py` | Create | Package marker |
| `api/data/sports/models.py` | Create | `SportsEvent` ORM model |
| `api/data/sports/schemas.py` | Create | Pydantic response shapes |
| `api/data/sports/router.py` | Create | 4 sports endpoints |
| `api/data/nba/__init__.py` | Create | Package marker |
| `api/data/nba/models.py` | Create | `NbaGame` ORM model |
| `api/data/nba/schemas.py` | Create | Pydantic response shapes |
| `api/data/nba/router.py` | Create | 4 NBA endpoints |
| `api/data/btc/__init__.py` | Create | Package marker |
| `api/data/btc/models.py` | Create | `BtcSnapshot` ORM model |
| `api/data/btc/schemas.py` | Create | Pydantic response shapes |
| `api/data/btc/router.py` | Create | 4 BTC endpoints |
| `data_pipeline/__init__.py` | Create | Package marker |
| `data_pipeline/base.py` | Create | `BaseCollector` poll loop |
| `data_pipeline/sports_collector.py` | Create | Polls Polymarket Gamma for sports markets |
| `data_pipeline/nba_collector.py` | Create | Polls ESPN + Polymarket Gamma; computes bias |
| `data_pipeline/btc_collector.py` | Create | Polls CoinGecko + Polymarket Gamma |
| `api/deps.py` | Modify | Add `require_scope()` helper |
| `api/main.py` | Modify | Register 3 routers; start/stop collector tasks in lifespan |
| `db/postgres.py` | Modify | Register 3 new ORM models in `_register_models()` |
| `core/config.py` | Modify | Add `espn_api_base`, `coingecko_api_base`, `disable_collectors` |
| `tests/conftest.py` | Modify | Import 3 new models in `setup_test_db` |
| `.env.test` | Modify | Add `DISABLE_COLLECTORS=true` |
| `tests/test_data/__init__.py` | Create | Package marker |
| `tests/test_data/test_data_models.py` | Create | ORM model CRUD tests |
| `tests/test_data/test_sports_collector.py` | Create | SportsCollector unit tests |
| `tests/test_data/test_nba_collector.py` | Create | NbaCollector unit tests |
| `tests/test_data/test_btc_collector.py` | Create | BtcCollector unit tests |
| `tests/test_data/test_sports_api.py` | Create | Sports endpoint HTTP tests |
| `tests/test_data/test_nba_api.py` | Create | NBA endpoint HTTP tests |
| `tests/test_data/test_btc_api.py` | Create | BTC endpoint HTTP tests |

---

### Task 1: ORM Models + DB Registration

**Files:**
- Create: `api/data/__init__.py`, `api/data/sports/__init__.py`, `api/data/nba/__init__.py`, `api/data/btc/__init__.py`
- Create: `api/data/sports/models.py`
- Create: `api/data/nba/models.py`
- Create: `api/data/btc/models.py`
- Modify: `db/postgres.py`
- Modify: `tests/conftest.py`
- Modify: `.env.test`
- Create: `tests/test_data/__init__.py`
- Create: `tests/test_data/test_data_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_data/__init__.py` (empty) and `tests/test_data/test_data_models.py`:

```python
# tests/test_data/test_data_models.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC, date
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_sports_event_crud(test_db_session):
    from api.data.sports.models import SportsEvent
    event = SportsEvent(
        market_id="mkt_sports_001",
        sport_slug="nba",
        question="Will Lakers win?",
        outcomes=[{"name": "Yes", "price": 0.72}],
        status="active",
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()
    await test_db_session.refresh(event)
    assert event.id is not None
    result = await test_db_session.scalar(
        select(SportsEvent).where(SportsEvent.market_id == "mkt_sports_001")
    )
    assert result.sport_slug == "nba"


async def test_nba_game_crud(test_db_session):
    from api.data.nba.models import NbaGame
    game = NbaGame(
        game_id="espn_game_001",
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        game_date=date(2026, 3, 18),
        game_status="live",
        score_home=87,
        score_away=94,
        quarter=3,
        time_remaining="4:22",
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(game)
    await test_db_session.commit()
    await test_db_session.refresh(game)
    assert game.id is not None
    result = await test_db_session.scalar(
        select(NbaGame).where(NbaGame.game_id == "espn_game_001")
    )
    assert result.home_team == "Los Angeles Lakers"


async def test_btc_snapshot_crud(test_db_session):
    from api.data.btc.models import BtcSnapshot
    snap = BtcSnapshot(
        timeframe="5m",
        price_usd=Decimal("67420.50"),
        market_id="btc_mkt_001",
        prediction_prob=Decimal("0.6100"),
        recorded_at=datetime.now(UTC),
    )
    test_db_session.add(snap)
    await test_db_session.commit()
    await test_db_session.refresh(snap)
    assert snap.id is not None
    result = await test_db_session.scalar(
        select(BtcSnapshot).where(BtcSnapshot.timeframe == "5m")
    )
    assert result.price_usd == Decimal("67420.50")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "/Users/ocean/Documents/产品代码开发/Polymarket Broker"
source .venv/bin/activate
ENV_FILE=.env.test pytest tests/test_data/test_data_models.py -v --tb=short
```
Expected: `ImportError` — modules don't exist yet.

- [ ] **Step 3: Create package markers**

```bash
touch "api/data/__init__.py"
touch "api/data/sports/__init__.py"
touch "api/data/nba/__init__.py"
touch "api/data/btc/__init__.py"
touch "tests/test_data/__init__.py"
```

- [ ] **Step 4: Create `api/data/sports/models.py`**

```python
# api/data/sports/models.py
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class SportsEvent(Base):
    __tablename__ = "sports_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    market_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    sport_slug: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    outcomes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    resolution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    volume: Mapped[float | None] = mapped_column(Numeric(20, 6), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
```

- [ ] **Step 5: Create `api/data/nba/models.py`**

```python
# api/data/nba/models.py
from datetime import datetime, UTC, date
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, Date
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class NbaGame(Base):
    __tablename__ = "nba_games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    home_team: Mapped[str] = mapped_column(String(100), nullable=False)
    away_team: Mapped[str] = mapped_column(String(100), nullable=False)
    game_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    game_status: Mapped[str] = mapped_column(String(20), nullable=False)
    score_home: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quarter: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_remaining: Mapped[str | None] = mapped_column(String(10), nullable=True)
    market_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_win_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    away_win_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    last_trade_price: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    bias_direction: Mapped[str | None] = mapped_column(String(30), nullable=True)
    bias_magnitude_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    data_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
```

- [ ] **Step 6: Create `api/data/btc/models.py`**

```python
# api/data/btc/models.py
from datetime import datetime, UTC
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db.postgres import Base


class BtcSnapshot(Base):
    __tablename__ = "btc_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    price_usd: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    market_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prediction_prob: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), nullable=True)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), index=True
    )
```

- [ ] **Step 7: Register models in `db/postgres.py`**

Add to `_register_models()`:

```python
def _register_models():
    from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
    from api.orders.models import Order  # noqa: F401
    from api.data.sports.models import SportsEvent  # noqa: F401
    from api.data.nba.models import NbaGame  # noqa: F401
    from api.data.btc.models import BtcSnapshot  # noqa: F401
```

- [ ] **Step 8: Update `tests/conftest.py` — import new models in `setup_test_db`**

In the try block inside `setup_test_db`, add:

```python
    try:
        from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
        from api.orders.models import Order  # noqa: F401
        from api.data.sports.models import SportsEvent  # noqa: F401
        from api.data.nba.models import NbaGame  # noqa: F401
        from api.data.btc.models import BtcSnapshot  # noqa: F401
    except ImportError:
        pass
```

- [ ] **Step 9: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_data_models.py -v --tb=short
```
Expected: `3 passed`

- [ ] **Step 10: Run full suite to confirm no regressions**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `73 passed` (70 existing + 3 new)

- [ ] **Step 11: Commit**

```bash
git add api/data/ tests/test_data/ db/postgres.py tests/conftest.py
git commit -m "feat: add SportsEvent, NbaGame, BtcSnapshot ORM models"
```

---

### Task 2: BaseCollector + SportsCollector

**Files:**
- Create: `data_pipeline/__init__.py`
- Create: `data_pipeline/base.py`
- Create: `data_pipeline/sports_collector.py`
- Create: `tests/test_data/test_sports_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_sports_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_sports_collector_upserts_market(test_db_session):
    """Collector fetches Gamma markets and upserts to sports_events."""
    from data_pipeline.sports_collector import SportsCollector
    from api.data.sports.models import SportsEvent

    mock_markets = [
        {
            "id": "mkt_nba_test_001",
            "question": "Will Lakers win vs Warriors?",
            "active": True,
            "tags": ["sports", "nba"],
            "outcomes": [{"name": "Yes"}, {"name": "No"}],
            "volume": "5000.0",
        }
    ]

    collector = SportsCollector()
    with patch("data_pipeline.sports_collector.GammaClient") as MockGamma:
        inst = MockGamma.return_value
        # First call returns markets, second call returns empty (stop pagination)
        inst.get_markets = AsyncMock(side_effect=[mock_markets, []])
        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(SportsEvent).where(SportsEvent.market_id == "mkt_nba_test_001")
    )
    assert result is not None
    assert result.sport_slug == "nba"
    assert result.question == "Will Lakers win vs Warriors?"
    assert result.status == "active"


async def test_sports_collector_upsert_is_idempotent(test_db_session):
    """Running collect twice doesn't create duplicates."""
    from data_pipeline.sports_collector import SportsCollector
    from api.data.sports.models import SportsEvent
    from sqlalchemy import func, select as sa_select

    mock_markets = [
        {"id": "mkt_nba_test_002", "question": "Q2", "active": True, "tags": ["nba"], "outcomes": []}
    ]

    collector = SportsCollector()
    for _ in range(2):
        with patch("data_pipeline.sports_collector.GammaClient") as MockGamma:
            inst = MockGamma.return_value
            inst.get_markets = AsyncMock(side_effect=[mock_markets, []])
            await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        sa_select(func.count()).where(SportsEvent.market_id == "mkt_nba_test_002")
    )
    assert count == 1


async def test_parse_sport_slug_extracts_from_tags():
    from data_pipeline.sports_collector import _parse_sport_slug
    assert _parse_sport_slug(["sports", "nba"]) == "nba"
    assert _parse_sport_slug(["nfl"]) == "nfl"
    assert _parse_sport_slug(["sports"]) == "sports"
    assert _parse_sport_slug([]) == "sports"
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_sports_collector.py -v --tb=short
```
Expected: `ImportError` — `data_pipeline` doesn't exist yet.

- [ ] **Step 3: Create `data_pipeline/__init__.py`** (empty)

```bash
touch data_pipeline/__init__.py
```

- [ ] **Step 4: Create `data_pipeline/base.py`**

```python
# data_pipeline/base.py
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaseCollector:
    """
    Base class for background data collectors.

    Subclasses implement `collect(db)` with one polling cycle.
    `run(db_factory)` loops forever, calling collect() every interval_seconds.
    Errors in a single cycle are caught and logged — the loop continues.

    db_factory: async_sessionmaker instance (AsyncSessionLocal from db/postgres.py)
    """
    name: str = "base_collector"
    interval_seconds: int = 60

    async def collect(self, db: AsyncSession) -> None:
        raise NotImplementedError

    async def run(self, db_factory) -> None:
        logger.info(f"[{self.name}] starting (interval={self.interval_seconds}s)")
        while True:
            try:
                async with db_factory() as db:
                    await self.collect(db)
                    logger.debug(f"[{self.name}] collect cycle complete")
            except asyncio.CancelledError:
                logger.info(f"[{self.name}] stopped")
                raise
            except Exception as e:
                logger.error(f"[{self.name}] collect failed: {e}")
            await asyncio.sleep(self.interval_seconds)
```

- [ ] **Step 5: Create `data_pipeline/sports_collector.py`**

```python
# data_pipeline/sports_collector.py
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.sports.models import SportsEvent
from core.polymarket.gamma_client import GammaClient


def _parse_sport_slug(tags: list) -> str:
    """Extract sport slug from Polymarket market tags.
    Returns the first non-'sports' tag, or 'sports' as fallback.
    """
    for tag in tags:
        if tag and tag.lower() != "sports":
            return tag.lower()
    return "sports"


class SportsCollector(BaseCollector):
    name = "sports_collector"
    interval_seconds = 300

    async def collect(self, db: AsyncSession) -> None:
        client = GammaClient()
        offset = 0
        while True:
            markets = await client.get_markets(
                limit=100, offset=offset, tag="sports", active=True
            )
            if not markets:
                break
            for market in markets:
                sport_slug = _parse_sport_slug(market.get("tags") or [])
                stmt = pg_insert(SportsEvent).values(
                    market_id=market["id"],
                    sport_slug=sport_slug,
                    question=market.get("question", ""),
                    outcomes=market.get("outcomes") or [],
                    status="active" if market.get("active") else "closed",
                    resolution=market.get("resolution"),
                    volume=market.get("volume"),
                    end_date=market.get("endDate"),
                    data_updated_at=datetime.now(UTC),
                ).on_conflict_do_update(
                    index_elements=["market_id"],
                    set_={
                        "sport_slug": sport_slug,
                        "question": market.get("question", ""),
                        "outcomes": market.get("outcomes") or [],
                        "status": "active" if market.get("active") else "closed",
                        "resolution": market.get("resolution"),
                        "volume": market.get("volume"),
                        "end_date": market.get("endDate"),
                        "data_updated_at": datetime.now(UTC),
                    }
                )
                await db.execute(stmt)
            await db.commit()
            if len(markets) < 100:
                break
            offset += 100
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_sports_collector.py -v --tb=short
```
Expected: `3 passed`

- [ ] **Step 7: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `76 passed`

- [ ] **Step 8: Commit**

```bash
git add data_pipeline/ tests/test_data/test_sports_collector.py
git commit -m "feat: add BaseCollector and SportsCollector"
```

---

### Task 3: NbaCollector

**Files:**
- Create: `data_pipeline/nba_collector.py`
- Create: `tests/test_data/test_nba_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_nba_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_nba_collector_upserts_game(test_db_session):
    """Collector fetches ESPN scoreboard + Polymarket NBA markets and upserts nba_games."""
    from data_pipeline.nba_collector import NbaCollector
    from api.data.nba.models import NbaGame

    mock_espn_response = {
        "events": [{
            "id": "espn_test_nba_001",
            "competitions": [{
                "competitors": [
                    {"homeAway": "home", "team": {"displayName": "Los Angeles Lakers"}, "score": "94"},
                    {"homeAway": "away", "team": {"displayName": "Golden State Warriors"}, "score": "87"},
                ],
                "status": {
                    "type": {"state": "in", "description": "In Progress"},
                    "displayClock": "4:22",
                    "period": 3,
                }
            }]
        }]
    }
    mock_gamma_markets = [
        {"id": "mkt_nba_lal_gsw", "question": "Will Lakers beat Warriors?",
         "active": True, "outcomePrices": ["0.69", "0.31"]}
    ]

    collector = NbaCollector()
    with patch("data_pipeline.nba_collector.httpx") as mock_httpx, \
         patch("data_pipeline.nba_collector.GammaClient") as MockGamma:

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_espn_response
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        inst = MockGamma.return_value
        inst.get_markets = AsyncMock(return_value=mock_gamma_markets)

        await collector.collect(test_db_session)

    result = await test_db_session.scalar(
        select(NbaGame).where(NbaGame.game_id == "espn_test_nba_001")
    )
    assert result is not None
    assert result.home_team == "Los Angeles Lakers"
    assert result.score_home == 94
    assert result.score_away == 87
    assert result.quarter == 3


def test_estimate_win_prob_neutral_at_start():
    from data_pipeline.nba_collector import estimate_win_prob
    # Tied at 0-0 in Q1 → 0.5
    prob = estimate_win_prob(0, 0, 1, "12:00")
    assert abs(prob - 0.5) < 0.01


def test_estimate_win_prob_increases_with_lead():
    from data_pipeline.nba_collector import estimate_win_prob
    # Home leads by 20 in Q4 with 1 min left → high prob
    prob = estimate_win_prob(80, 60, 4, "1:00")
    assert prob > 0.85


def test_compute_bias_home_underpriced():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(0.75, 0.55)
    assert direction == "HOME_UNDERPRICED"
    assert bps == 2000


def test_compute_bias_neutral_when_small_delta():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(0.52, 0.51)
    assert direction == "NEUTRAL"


def test_compute_bias_none_prob():
    from data_pipeline.nba_collector import compute_bias
    direction, bps = compute_bias(None, 0.6)
    assert direction == "NEUTRAL"
    assert bps == 0
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_nba_collector.py -v --tb=short
```
Expected: `ImportError`

- [ ] **Step 3: Create `data_pipeline/nba_collector.py`**

```python
# data_pipeline/nba_collector.py
from datetime import datetime, UTC
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data_pipeline.base import BaseCollector
from api.data.nba.models import NbaGame
from core.polymarket.gamma_client import GammaClient

ESPN_SCOREBOARD_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
BIAS_THRESHOLD_BPS = 300


def estimate_win_prob(
    score_home: int, score_away: int, quarter: int, time_remaining: str
) -> float:
    """
    Simplified linear win probability model.
    Returns probability that home team wins.
    - At game start (Q1, 12:00 tied): returns 0.5
    - Score differential and time elapsed drive the estimate
    """
    try:
        parts = time_remaining.split(":")
        mins = int(parts[0])
        secs = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, AttributeError, IndexError):
        mins, secs = 6, 0  # default mid-quarter

    # Total minutes elapsed in game
    elapsed = (max(quarter, 1) - 1) * 12.0 + (12.0 - mins - secs / 60.0)
    elapsed = max(0.0, min(elapsed, 48.0))
    time_fraction = elapsed / 48.0

    # Score component: normalize to [-1, 1]
    diff = score_home - score_away
    score_component = max(-1.0, min(1.0, diff / 40.0))

    # As game progresses, score matters more
    prob = 0.5 + score_component * time_fraction * 0.45
    return max(0.05, min(0.95, prob))


def compute_bias(
    statistical_prob: float | None, polymarket_prob: float | None
) -> tuple[str, int]:
    """Returns (direction, magnitude_bps). Direction is from home team's perspective."""
    if statistical_prob is None or polymarket_prob is None:
        return "NEUTRAL", 0
    delta_bps = int(abs(statistical_prob - polymarket_prob) * 10000)
    if delta_bps < BIAS_THRESHOLD_BPS:
        return "NEUTRAL", delta_bps
    if statistical_prob > polymarket_prob:
        return "HOME_UNDERPRICED", delta_bps
    return "AWAY_UNDERPRICED", delta_bps


def _find_market_for_game(home: str, away: str, markets: list) -> dict | None:
    """Fuzzy match: find a Polymarket market whose question contains both team last names."""
    home_last = home.split()[-1].lower()
    away_last = away.split()[-1].lower()
    for m in markets:
        q = m.get("question", "").lower()
        if home_last in q and away_last in q:
            return m
    return None


def _parse_prob_from_market(market: dict, side: str) -> float | None:
    """Extract implied probability from outcomePrices list. side: 'home'=index 0, 'away'=index 1."""
    prices = market.get("outcomePrices", [])
    idx = 0 if side == "home" else 1
    try:
        return float(prices[idx])
    except (IndexError, ValueError, TypeError):
        return None


class NbaCollector(BaseCollector):
    name = "nba_collector"
    interval_seconds = 30

    async def collect(self, db: AsyncSession) -> None:
        # 1. Fetch ESPN scoreboard
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(ESPN_SCOREBOARD_URL)
            resp.raise_for_status()
            espn_data = resp.json()

        events = espn_data.get("events", [])
        if not events:
            return

        # 2. Fetch Polymarket NBA markets
        gamma = GammaClient()
        nba_markets = await gamma.get_markets(limit=50, tag="nba", active=True)

        # 3. Process each game
        for event in events:
            game_id = event["id"]
            competitions = event.get("competitions", [])
            if not competitions:
                continue
            comp = competitions[0]

            # Parse teams and scores
            home_team = away_team = ""
            score_home = score_away = 0
            for competitor in comp.get("competitors", []):
                name = competitor.get("team", {}).get("displayName", "")
                score = int(competitor.get("score", 0) or 0)
                if competitor.get("homeAway") == "home":
                    home_team, score_home = name, score
                else:
                    away_team, score_away = name, score

            # Parse game status
            status_obj = comp.get("status", {})
            state = status_obj.get("type", {}).get("state", "pre")
            game_status = {"pre": "scheduled", "in": "live", "post": "final"}.get(state, "scheduled")
            quarter = status_obj.get("period", None)
            time_remaining = status_obj.get("displayClock", "")

            # Find matching Polymarket market
            matched_market = _find_market_for_game(home_team, away_team, nba_markets)
            market_id = matched_market["id"] if matched_market else None

            home_prob = away_prob = last_trade = None
            if matched_market:
                home_prob = _parse_prob_from_market(matched_market, "home")
                away_prob = _parse_prob_from_market(matched_market, "away")
                last_trade = home_prob  # approximation

            # Compute bias (only for live games)
            stat_prob = None
            if game_status == "live" and quarter and time_remaining:
                stat_prob = estimate_win_prob(score_home, score_away, quarter, time_remaining)
            bias_direction, bias_bps = compute_bias(stat_prob, home_prob)

            # Upsert to nba_games
            stmt = pg_insert(NbaGame).values(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                game_date=datetime.now(UTC).date(),
                game_status=game_status,
                score_home=score_home,
                score_away=score_away,
                quarter=quarter,
                time_remaining=time_remaining,
                market_id=market_id,
                home_win_prob=home_prob,
                away_win_prob=away_prob,
                last_trade_price=last_trade,
                bias_direction=bias_direction,
                bias_magnitude_bps=bias_bps,
                data_updated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                index_elements=["game_id"],
                set_={
                    "home_team": home_team,
                    "away_team": away_team,
                    "game_status": game_status,
                    "score_home": score_home,
                    "score_away": score_away,
                    "quarter": quarter,
                    "time_remaining": time_remaining,
                    "market_id": market_id,
                    "home_win_prob": home_prob,
                    "away_win_prob": away_prob,
                    "last_trade_price": last_trade,
                    "bias_direction": bias_direction,
                    "bias_magnitude_bps": bias_bps,
                    "data_updated_at": datetime.now(UTC),
                }
            )
            await db.execute(stmt)
        await db.commit()
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_nba_collector.py -v --tb=short
```
Expected: `6 passed`

- [ ] **Step 5: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `82 passed`

- [ ] **Step 6: Commit**

```bash
git add data_pipeline/nba_collector.py tests/test_data/test_nba_collector.py
git commit -m "feat: add NbaCollector with ESPN fusion and bias signal"
```

---

### Task 4: BtcCollector

**Files:**
- Create: `data_pipeline/btc_collector.py`
- Create: `tests/test_data/test_btc_collector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_btc_collector.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select, func

pytestmark = pytest.mark.asyncio(loop_scope="session")

TIMEFRAMES = ["5m", "15m", "1h", "4h"]


async def test_btc_collector_appends_snapshots(test_db_session):
    """Collector appends 4 rows (one per timeframe) on each collect cycle."""
    from data_pipeline.btc_collector import BtcCollector
    from api.data.btc.models import BtcSnapshot

    mock_coingecko = {"bitcoin": {"usd": 67420.50}}
    mock_gamma_markets = [
        {"id": f"btc_mkt_{tf}", "question": f"BTC up {tf}?", "active": True, "outcomePrices": ["0.61", "0.39"]}
        for tf in TIMEFRAMES
    ]

    collector = BtcCollector()
    with patch("data_pipeline.btc_collector.httpx") as mock_httpx, \
         patch("data_pipeline.btc_collector.GammaClient") as MockGamma:

        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_coingecko
        mock_resp.raise_for_status = MagicMock()
        mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)

        inst = MockGamma.return_value
        inst.get_markets = AsyncMock(return_value=mock_gamma_markets)

        await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        select(func.count()).select_from(BtcSnapshot).where(BtcSnapshot.price_usd == 67420.50)
    )
    assert count == 4  # one per timeframe


async def test_btc_collector_appends_on_each_cycle(test_db_session):
    """append-only: two cycles → two rows per timeframe."""
    from data_pipeline.btc_collector import BtcCollector
    from api.data.btc.models import BtcSnapshot
    from sqlalchemy import func

    mock_coingecko = {"bitcoin": {"usd": 68000.00}}
    mock_gamma_markets = [
        {"id": f"btc_append_{tf}", "question": f"BTC {tf}", "active": True, "outcomePrices": ["0.55", "0.45"]}
        for tf in TIMEFRAMES
    ]

    collector = BtcCollector()
    for _ in range(2):
        with patch("data_pipeline.btc_collector.httpx") as mock_httpx, \
             patch("data_pipeline.btc_collector.GammaClient") as MockGamma:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_coingecko
            mock_resp.raise_for_status = MagicMock()
            mock_httpx.AsyncClient.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
            inst = MockGamma.return_value
            inst.get_markets = AsyncMock(return_value=mock_gamma_markets)
            await collector.collect(test_db_session)

    count = await test_db_session.scalar(
        select(func.count()).select_from(BtcSnapshot).where(BtcSnapshot.price_usd == 68000.00)
    )
    assert count == 8  # 4 timeframes × 2 cycles
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_btc_collector.py -v --tb=short
```
Expected: `ImportError`

- [ ] **Step 3: Create `data_pipeline/btc_collector.py`**

```python
# data_pipeline/btc_collector.py
from datetime import datetime, UTC
from decimal import Decimal
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from data_pipeline.base import BaseCollector
from api.data.btc.models import BtcSnapshot
from core.polymarket.gamma_client import GammaClient

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
TIMEFRAMES = ["5m", "15m", "1h", "4h"]


def _find_market_for_timeframe(timeframe: str, markets: list) -> dict | None:
    """Find the Polymarket BTC prediction market for the given timeframe."""
    for m in markets:
        q = m.get("question", "").lower()
        if timeframe in q:
            return m
    return None


def _parse_prob(market: dict) -> Decimal | None:
    prices = market.get("outcomePrices", [])
    try:
        return Decimal(str(prices[0]))
    except (IndexError, Exception):
        return None


class BtcCollector(BaseCollector):
    name = "btc_collector"
    interval_seconds = 30

    async def collect(self, db: AsyncSession) -> None:
        # 1. Fetch BTC price from CoinGecko
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(COINGECKO_URL)
            resp.raise_for_status()
            data = resp.json()

        price_usd = Decimal(str(data["bitcoin"]["usd"]))

        # 2. Fetch BTC prediction markets from Polymarket Gamma
        gamma = GammaClient()
        btc_markets = await gamma.get_markets(limit=20, tag="crypto", active=True)

        # 3. Append one row per timeframe
        for timeframe in TIMEFRAMES:
            matched = _find_market_for_timeframe(timeframe, btc_markets)
            market_id = matched["id"] if matched else None
            prediction_prob = _parse_prob(matched) if matched else None
            volume = Decimal(str(matched.get("volume", 0) or 0)) if matched else None

            snapshot = BtcSnapshot(
                timeframe=timeframe,
                price_usd=price_usd,
                market_id=market_id,
                prediction_prob=prediction_prob,
                volume=volume,
                recorded_at=datetime.now(UTC),
            )
            db.add(snapshot)

        await db.commit()
```

- [ ] **Step 4: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_btc_collector.py -v --tb=short
```
Expected: `2 passed`

- [ ] **Step 5: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `84 passed`

- [ ] **Step 6: Commit**

```bash
git add data_pipeline/btc_collector.py tests/test_data/test_btc_collector.py
git commit -m "feat: add BtcCollector (CoinGecko + Polymarket Gamma, append-only)"
```

---

### Task 5: Sports API Endpoints (4)

**Files:**
- Modify: `api/deps.py` — add `require_scope()`
- Create: `api/data/sports/schemas.py`
- Create: `api/data/sports/router.py`
- Create: `tests/test_data/test_sports_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_sports_api.py
import pytest
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Data Key", ["data:read"])
    return result["key"]


async def _seed_sports_event(test_db_session, market_id: str, sport_slug: str, status: str = "active"):
    from api.data.sports.models import SportsEvent
    event = SportsEvent(
        market_id=market_id,
        sport_slug=sport_slug,
        question=f"Test question for {market_id}",
        outcomes=[{"name": "Yes"}, {"name": "No"}],
        status=status,
        resolution={"winner": "Yes", "settled_at": "2026-03-18T10:00:00Z"} if status == "resolved" else None,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(event)
    await test_db_session.commit()


async def test_get_categories(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_cat@example.com")
    await _seed_sports_event(test_db_session, "mkt_cat_001", "nba")
    await _seed_sports_event(test_db_session, "mkt_cat_002", "nfl")

    resp = await client.get("/api/v1/data/sports/categories", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    slugs = [c["slug"] for c in data]
    assert "nba" in slugs
    assert "nfl" in slugs


async def test_get_categories_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("sports_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope Key", ["orders:write"])
    key = result["key"]

    resp = await client.get("/api/v1/data/sports/categories", headers={"X-API-Key": key})
    assert resp.status_code == 403


async def test_get_sport_events(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_events@example.com")
    await _seed_sports_event(test_db_session, "mkt_events_001", "nba")

    resp = await client.get("/api/v1/data/sports/nba/events", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) >= 1


async def test_get_sport_events_stale(client, test_db_session):
    """Event with old data_updated_at returns stale=True."""
    key = await _create_data_key(test_db_session, "sports_stale@example.com")
    from api.data.sports.models import SportsEvent
    old_event = SportsEvent(
        market_id="mkt_stale_001", sport_slug="epl",
        question="Old match", outcomes=[],
        status="active",
        data_updated_at=datetime.now(UTC) - timedelta(hours=1),
    )
    test_db_session.add(old_event)
    await test_db_session.commit()

    resp = await client.get("/api/v1/data/sports/epl/events", headers={"X-API-Key": key})
    assert resp.status_code == 200
    assert resp.json()["stale"] is True


async def test_get_orderbook_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_ob@example.com")
    await _seed_sports_event(test_db_session, "mkt_ob_001", "nba")

    mock_ob = {"bids": [], "asks": []}
    with patch("api.data.sports.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get(
            "/api/v1/data/sports/nba/events/mkt_ob_001/orderbook?token_id=tok123",
            headers={"X-API-Key": key}
        )
    assert resp.status_code == 200


async def test_get_realized_resolved(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_resolved@example.com")
    await _seed_sports_event(test_db_session, "mkt_resolved_001", "nba", status="resolved")

    resp = await client.get(
        "/api/v1/data/sports/nba/events/mkt_resolved_001/realized",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["resolution"]["winner"] == "Yes"


async def test_get_realized_not_resolved_returns_404(client, test_db_session):
    key = await _create_data_key(test_db_session, "sports_notresolved@example.com")
    await _seed_sports_event(test_db_session, "mkt_active_001", "nba", status="active")

    resp = await client.get(
        "/api/v1/data/sports/nba/events/mkt_active_001/realized",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_sports_api.py -v --tb=short
```
Expected: `ImportError` or `404 Not Found` for routes.

- [ ] **Step 3: Add `require_scope` to `api/deps.py`**

Append to the end of `api/deps.py`:

```python
def require_scope(auth: dict, scope: str) -> None:
    """Raise HTTP 403 if the required scope is not present in auth['scopes']."""
    if scope not in auth.get("scopes", []):
        raise HTTPException(403, detail=f"SCOPE_REQUIRED: {scope}")
```

- [ ] **Step 4: Create `api/data/sports/schemas.py`**

```python
# api/data/sports/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any


class SportsCategoryResponse(BaseModel):
    slug: str
    active_events: int


class SportsEventResponse(BaseModel):
    market_id: str
    sport_slug: str
    question: str
    outcomes: list
    status: str
    resolution: Any | None
    volume: float | None
    end_date: datetime | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedSportsEvents(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[SportsEventResponse]
    pagination: dict


class RealizedResponse(BaseModel):
    stale: bool
    data_updated_at: datetime
    data: dict
```

- [ ] **Step 5: Create `api/data/sports/router.py`**

```python
# api/data/sports/router.py
import base64
from datetime import datetime, UTC, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.sports.models import SportsEvent
from api.data.sports.schemas import (
    SportsCategoryResponse, PaginatedSportsEvents, SportsEventResponse, RealizedResponse,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/sports", tags=["data-sports"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 600  # 10 minutes


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/categories", response_model=list[SportsCategoryResponse])
async def get_categories(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    result = await db.execute(
        select(SportsEvent.sport_slug, func.count(SportsEvent.id).label("active_events"))
        .where(SportsEvent.status == "active")
        .group_by(SportsEvent.sport_slug)
        .order_by(SportsEvent.sport_slug)
    )
    return [{"slug": r.sport_slug, "active_events": r.active_events} for r in result.all()]


@router.get("/{sport}/events", response_model=PaginatedSportsEvents)
async def get_sport_events(
    sport: str,
    status: str | None = Query(default="active"),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    conditions = [SportsEvent.sport_slug == sport]
    if status:
        conditions.append(SportsEvent.status == status)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(base64.b64decode(cursor).decode())
            conditions.append(SportsEvent.data_updated_at < cursor_dt)
        except Exception:
            pass

    stmt = (
        select(SportsEvent)
        .where(and_(*conditions))
        .order_by(desc(SportsEvent.data_updated_at))
        .limit(limit + 1)
    )
    result = await db.execute(stmt)
    events = list(result.scalars().all())

    has_more = len(events) > limit
    if has_more:
        events = events[:limit]

    next_cursor = None
    if has_more and events:
        next_cursor = base64.b64encode(events[-1].data_updated_at.isoformat().encode()).decode()

    most_recent = max((e.data_updated_at for e in events), default=None)
    stale = _is_stale(most_recent) if most_recent else True

    return PaginatedSportsEvents(
        stale=stale,
        data_updated_at=most_recent,
        data=[SportsEventResponse.model_validate(e) for e in events],
        pagination={"cursor": next_cursor, "has_more": has_more, "limit": limit},
    )


@router.get("/{sport}/events/{market_id}/orderbook")
async def get_event_orderbook(
    sport: str,
    market_id: str,
    token_id: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{sport}/events/{market_id}/realized", response_model=RealizedResponse)
async def get_event_realized(
    sport: str,
    market_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    event = await db.scalar(
        select(SportsEvent).where(
            SportsEvent.market_id == market_id,
            SportsEvent.status == "resolved",
        )
    )
    if not event:
        raise HTTPException(404, detail="MARKET_NOT_RESOLVED")
    return RealizedResponse(
        stale=_is_stale(event.data_updated_at),
        data_updated_at=event.data_updated_at,
        data={
            "market_id": event.market_id,
            "question": event.question,
            "resolution": event.resolution,
        },
    )
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_sports_api.py -v --tb=short
```

> **Note:** These tests require the sports router to be registered in `api/main.py`. Add this temporarily before running:
> ```python
> from api.data.sports.router import router as sports_data_router
> app.include_router(sports_data_router, prefix=settings.api_v1_prefix)
> ```
> (Full main.py wiring is in Task 8; for now add just this one router to unblock the test.)

Expected: `6 passed`

- [ ] **Step 7: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `90 passed`

- [ ] **Step 8: Commit**

```bash
git add api/data/sports/ api/deps.py tests/test_data/test_sports_api.py api/main.py
git commit -m "feat: add sports data API endpoints (4 endpoints, data:read scope)"
```

---

### Task 6: NBA API Endpoints (4)

**Files:**
- Create: `api/data/nba/schemas.py`
- Create: `api/data/nba/router.py`
- Create: `tests/test_data/test_nba_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_nba_api.py
import pytest
from datetime import datetime, UTC, timedelta, date
from unittest.mock import AsyncMock, patch
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Data Key", ["data:read"])
    return result["key"]


async def _seed_nba_game(test_db_session, game_id: str, game_status: str = "live", market_id: str | None = "mkt_nba_001") -> None:
    from api.data.nba.models import NbaGame
    game = NbaGame(
        game_id=game_id,
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        game_date=date.today(),
        game_status=game_status,
        score_home=94,
        score_away=87,
        quarter=3,
        time_remaining="4:22",
        market_id=market_id,
        home_win_prob=0.69,
        away_win_prob=0.31,
        last_trade_price=0.69,
        bias_direction="HOME_UNDERPRICED",
        bias_magnitude_bps=420,
        data_updated_at=datetime.now(UTC),
    )
    test_db_session.add(game)
    await test_db_session.commit()


async def test_list_nba_games(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_list@example.com")
    await _seed_nba_game(test_db_session, "espn_list_001")

    resp = await client.get("/api/v1/data/nba/games", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert len(data["data"]) >= 1


async def test_get_nba_game_detail(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_detail@example.com")
    await _seed_nba_game(test_db_session, "espn_detail_001")

    resp = await client.get("/api/v1/data/nba/games/espn_detail_001", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["game_id"] == "espn_detail_001"
    assert "stale" in data


async def test_get_nba_game_not_found(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_notfound@example.com")
    resp = await client.get("/api/v1/data/nba/games/nonexistent_game", headers={"X-API-Key": key})
    assert resp.status_code == 404


async def test_get_nba_fusion(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_fusion@example.com")
    await _seed_nba_game(test_db_session, "espn_fusion_001")

    resp = await client.get("/api/v1/data/nba/games/espn_fusion_001/fusion", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "polymarket" in data
    assert "bias_signal" in data
    assert "stale" in data


async def test_get_nba_orderbook_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_ob@example.com")
    await _seed_nba_game(test_db_session, "espn_ob_001", market_id="mkt_nba_ob")

    mock_ob = {"bids": [], "asks": []}
    with patch("api.data.nba.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get(
            "/api/v1/data/nba/games/espn_ob_001/orderbook?token_id=tok123",
            headers={"X-API-Key": key}
        )
    assert resp.status_code == 200


async def test_get_nba_orderbook_no_market_returns_404(client, test_db_session):
    key = await _create_data_key(test_db_session, "nba_ob_null@example.com")
    await _seed_nba_game(test_db_session, "espn_ob_null_001", market_id=None)

    resp = await client.get(
        "/api/v1/data/nba/games/espn_ob_null_001/orderbook?token_id=tok123",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 404


async def test_nba_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("nba_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/nba/games", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_nba_api.py -v --tb=short
```
Expected: `404` on routes or `ImportError`.

- [ ] **Step 3: Create `api/data/nba/schemas.py`**

```python
# api/data/nba/schemas.py
from pydantic import BaseModel
from datetime import datetime, date
from decimal import Decimal
from typing import Any


class NbaGameResponse(BaseModel):
    game_id: str
    home_team: str
    away_team: str
    game_date: date
    game_status: str
    score_home: int | None
    score_away: int | None
    quarter: int | None
    time_remaining: str | None
    market_id: str | None
    data_updated_at: datetime

    class Config:
        from_attributes = True


class NbaGameDetailResponse(BaseModel):
    stale: bool
    data_updated_at: datetime
    data: NbaGameResponse


class NbaFusionResponse(BaseModel):
    game_id: str
    score: dict
    polymarket: dict
    bias_signal: dict
    stale: bool
    data_updated_at: datetime


class PaginatedNbaGames(BaseModel):
    data: list[NbaGameResponse]
    pagination: dict
```

- [ ] **Step 4: Create `api/data/nba/router.py`**

```python
# api/data/nba/router.py
from datetime import datetime, UTC, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.nba.models import NbaGame
from api.data.nba.schemas import (
    NbaGameResponse, NbaGameDetailResponse, NbaFusionResponse, PaginatedNbaGames,
)
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/nba", tags=["data-nba"])

clob_client = ClobClient()

STALE_THRESHOLD_SECONDS = 120  # 2 minutes


def _is_stale(updated_at: datetime) -> bool:
    now = datetime.now(UTC)
    if updated_at.tzinfo is None:
        updated_at = updated_at.replace(tzinfo=UTC)
    return (now - updated_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/games", response_model=PaginatedNbaGames)
async def list_nba_games(
    game_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    import base64
    conditions = []
    target_date = game_date or date.today()
    conditions.append(NbaGame.game_date == target_date)
    if status:
        conditions.append(NbaGame.game_status == status)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(base64.b64decode(cursor).decode())
            conditions.append(NbaGame.data_updated_at < cursor_dt)
        except Exception:
            pass

    stmt = (
        select(NbaGame)
        .where(and_(*conditions))
        .order_by(desc(NbaGame.data_updated_at))
        .limit(limit + 1)
    )
    result = await db.execute(stmt)
    games = list(result.scalars().all())

    has_more = len(games) > limit
    if has_more:
        games = games[:limit]

    next_cursor = None
    if has_more and games:
        next_cursor = base64.b64encode(games[-1].data_updated_at.isoformat().encode()).decode()

    return PaginatedNbaGames(
        data=[NbaGameResponse.model_validate(g) for g in games],
        pagination={"cursor": next_cursor, "has_more": has_more, "limit": limit},
    )


@router.get("/games/{game_id}", response_model=NbaGameDetailResponse)
async def get_nba_game(
    game_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game:
        raise HTTPException(404, detail="GAME_NOT_FOUND")
    return NbaGameDetailResponse(
        stale=_is_stale(game.data_updated_at),
        data_updated_at=game.data_updated_at,
        data=NbaGameResponse.model_validate(game),
    )


@router.get("/games/{game_id}/fusion", response_model=NbaFusionResponse)
async def get_nba_fusion(
    game_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game:
        raise HTTPException(404, detail="GAME_NOT_FOUND")
    return NbaFusionResponse(
        game_id=game.game_id,
        score={
            "home": game.score_home,
            "away": game.score_away,
            "quarter": game.quarter,
            "time_remaining": game.time_remaining,
        },
        polymarket={
            "home_win_prob": float(game.home_win_prob) if game.home_win_prob else None,
            "away_win_prob": float(game.away_win_prob) if game.away_win_prob else None,
            "last_trade_price": float(game.last_trade_price) if game.last_trade_price else None,
        },
        bias_signal={
            "direction": game.bias_direction,
            "magnitude_bps": game.bias_magnitude_bps,
        },
        stale=_is_stale(game.data_updated_at),
        data_updated_at=game.data_updated_at,
    )


@router.get("/games/{game_id}/orderbook")
async def get_nba_orderbook(
    game_id: str,
    token_id: str = Query(...),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
    if not game or not game.market_id:
        raise HTTPException(404, detail="GAME_NOT_FOUND_OR_NO_MARKET")
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
```

- [ ] **Step 5: Register NBA router in `api/main.py`** (add alongside sports router)

```python
from api.data.nba.router import router as nba_data_router
app.include_router(nba_data_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_nba_api.py -v --tb=short
```
Expected: `6 passed`

- [ ] **Step 7: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `96 passed`

- [ ] **Step 8: Commit**

```bash
git add api/data/nba/ tests/test_data/test_nba_api.py api/main.py
git commit -m "feat: add NBA data API endpoints (games, detail, fusion, orderbook)"
```

---

### Task 7: BTC API Endpoints (4)

**Files:**
- Create: `api/data/btc/schemas.py`
- Create: `api/data/btc/router.py`
- Create: `tests/test_data/test_btc_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_btc_api.py
import pytest
from decimal import Decimal
from datetime import datetime, UTC, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")

TIMEFRAMES = ["5m", "15m", "1h", "4h"]


async def _create_data_key(test_db_session, email: str) -> str:
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "BTC Key", ["data:read"])
    return result["key"]


async def _seed_btc_snapshots(test_db_session, price: float = 67000.0) -> None:
    from api.data.btc.models import BtcSnapshot
    for tf in TIMEFRAMES:
        snap = BtcSnapshot(
            timeframe=tf,
            price_usd=Decimal(str(price)),
            market_id=f"btc_{tf}_mkt",
            prediction_prob=Decimal("0.6100"),
            recorded_at=datetime.now(UTC),
        )
        test_db_session.add(snap)
    await test_db_session.commit()


async def test_get_btc_predictions_all(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_all@example.com")
    await _seed_btc_snapshots(test_db_session, price=67000.0)

    resp = await client.get("/api/v1/data/btc/predictions", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    returned_timeframes = [item["timeframe"] for item in data]
    for tf in TIMEFRAMES:
        assert tf in returned_timeframes


async def test_get_btc_predictions_by_timeframe(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_tf@example.com")
    await _seed_btc_snapshots(test_db_session, price=67500.0)

    resp = await client.get("/api/v1/data/btc/predictions/5m", headers={"X-API-Key": key})
    assert resp.status_code == 200
    data = resp.json()
    assert "stale" in data
    assert "data" in data
    assert len(data["data"]) >= 1
    assert data["data"][0]["timeframe"] == "5m"


async def test_get_btc_predictions_invalid_timeframe(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_invalid@example.com")
    resp = await client.get("/api/v1/data/btc/predictions/99m", headers={"X-API-Key": key})
    assert resp.status_code == 400


async def test_get_btc_history(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_hist@example.com")
    await _seed_btc_snapshots(test_db_session, price=68000.0)

    resp = await client.get(
        "/api/v1/data/btc/history?timeframe=1h&limit=10",
        headers={"X-API-Key": key}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert all(item["timeframe"] == "1h" for item in data["data"])


async def test_get_btc_onchain_proxy(client, test_db_session):
    key = await _create_data_key(test_db_session, "btc_onchain@example.com")
    await _seed_btc_snapshots(test_db_session, price=67000.0)

    mock_trades = [{"price": "0.62", "size": "100"}]
    with patch("api.data.btc.router.clob_client") as mock_clob:
        mock_clob.get_trades = AsyncMock(return_value=mock_trades)
        resp = await client.get("/api/v1/data/btc/onchain", headers={"X-API-Key": key})
    assert resp.status_code == 200


async def test_btc_requires_scope(client, test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("btc_noscope@example.com", "password123")
    result = await svc.create_api_key(user.id, "No Scope", ["orders:write"])
    resp = await client.get("/api/v1/data/btc/predictions", headers={"X-API-Key": result["key"]})
    assert resp.status_code == 403
```

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_btc_api.py -v --tb=short
```
Expected: `ImportError` or route 404.

- [ ] **Step 3: Create `api/data/btc/schemas.py`**

```python
# api/data/btc/schemas.py
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class BtcSnapshotResponse(BaseModel):
    id: int
    timeframe: str
    price_usd: Decimal
    market_id: str | None
    prediction_prob: Decimal | None
    volume: Decimal | None
    recorded_at: datetime

    class Config:
        from_attributes = True


class BtcTimeframeResponse(BaseModel):
    stale: bool
    data_updated_at: datetime | None
    data: list[BtcSnapshotResponse]


class BtcHistoryResponse(BaseModel):
    data: list[BtcSnapshotResponse]
    pagination: dict
```

- [ ] **Step 4: Create `api/data/btc/router.py`**

```python
# api/data/btc/router.py
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from db.postgres import get_session
from api.deps import get_current_user_from_api_key, require_scope
from api.data.btc.models import BtcSnapshot
from api.data.btc.schemas import BtcSnapshotResponse, BtcTimeframeResponse, BtcHistoryResponse
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/data/btc", tags=["data-btc"])

clob_client = ClobClient()

VALID_TIMEFRAMES = {"5m", "15m", "1h", "4h"}
STALE_THRESHOLD_SECONDS = 120  # 2 minutes


def _is_stale(recorded_at: datetime) -> bool:
    now = datetime.now(UTC)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=UTC)
    return (now - recorded_at).total_seconds() > STALE_THRESHOLD_SECONDS


@router.get("/predictions", response_model=list[BtcSnapshotResponse])
async def get_btc_predictions_all(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Latest snapshot for all 4 timeframes."""
    require_scope(auth, "data:read")
    # Use a subquery to get the latest recorded_at per timeframe
    subq = (
        select(BtcSnapshot.timeframe, func.max(BtcSnapshot.recorded_at).label("max_recorded"))
        .group_by(BtcSnapshot.timeframe)
        .subquery()
    )
    stmt = select(BtcSnapshot).join(
        subq,
        (BtcSnapshot.timeframe == subq.c.timeframe) &
        (BtcSnapshot.recorded_at == subq.c.max_recorded)
    ).order_by(BtcSnapshot.timeframe)
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())
    return [BtcSnapshotResponse.model_validate(s) for s in snaps]


@router.get("/predictions/{timeframe}", response_model=BtcTimeframeResponse)
async def get_btc_predictions_timeframe(
    timeframe: str,
    limit: int = Query(default=20, ge=1, le=100),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(400, detail=f"INVALID_TIMEFRAME: must be one of {sorted(VALID_TIMEFRAMES)}")

    stmt = (
        select(BtcSnapshot)
        .where(BtcSnapshot.timeframe == timeframe)
        .order_by(desc(BtcSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())

    most_recent = snaps[0].recorded_at if snaps else None
    stale = _is_stale(most_recent) if most_recent else True

    return BtcTimeframeResponse(
        stale=stale,
        data_updated_at=most_recent,
        data=[BtcSnapshotResponse.model_validate(s) for s in snaps],
    )


@router.get("/onchain")
async def get_btc_onchain(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Proxy: latest on-chain BTC Polymarket trades via ClobClient."""
    require_scope(auth, "data:read")
    # Resolve market_id from the most recent 5m snapshot
    latest = await db.scalar(
        select(BtcSnapshot)
        .where(BtcSnapshot.timeframe == "5m", BtcSnapshot.market_id.isnot(None))
        .order_by(desc(BtcSnapshot.recorded_at))
    )
    if not latest or not latest.market_id:
        raise HTTPException(503, detail="BTC_MARKET_ID_NOT_COLLECTED_YET")
    try:
        return await clob_client.get_trades(market_id=latest.market_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/history", response_model=BtcHistoryResponse)
async def get_btc_history(
    timeframe: str = Query(...),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    require_scope(auth, "data:read")
    if timeframe not in VALID_TIMEFRAMES:
        raise HTTPException(400, detail=f"INVALID_TIMEFRAME: must be one of {sorted(VALID_TIMEFRAMES)}")

    conditions = [BtcSnapshot.timeframe == timeframe]
    if from_:
        try:
            conditions.append(BtcSnapshot.recorded_at >= datetime.fromisoformat(from_))
        except ValueError:
            raise HTTPException(400, detail="INVALID_FROM_DATETIME")
    if to:
        try:
            conditions.append(BtcSnapshot.recorded_at <= datetime.fromisoformat(to))
        except ValueError:
            raise HTTPException(400, detail="INVALID_TO_DATETIME")

    from sqlalchemy import and_
    stmt = (
        select(BtcSnapshot)
        .where(and_(*conditions))
        .order_by(desc(BtcSnapshot.recorded_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())
    return BtcHistoryResponse(
        data=[BtcSnapshotResponse.model_validate(s) for s in snaps],
        pagination={"limit": limit, "count": len(snaps)},
    )
```

- [ ] **Step 5: Register BTC router in `api/main.py`**

```python
from api.data.btc.router import router as btc_data_router
app.include_router(btc_data_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 6: Run tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_btc_api.py -v --tb=short
```
Expected: `6 passed`

- [ ] **Step 7: Run full suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `102 passed`

- [ ] **Step 8: Commit**

```bash
git add api/data/btc/ tests/test_data/test_btc_api.py api/main.py
git commit -m "feat: add BTC data API endpoints (predictions, history, onchain)"
```

---

### Task 8: Lifespan Wiring + Config + Final main.py

**Files:**
- Modify: `core/config.py` — add `espn_api_base`, `coingecko_api_base`, `disable_collectors`
- Modify: `api/main.py` — complete lifespan with collectors; register all 3 routers cleanly
- Modify: `.env.test` — add `DISABLE_COLLECTORS=true`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_data/test_lifespan.py
import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_collectors_disabled_in_test_env(client):
    """DISABLE_COLLECTORS=true means no collector tasks are started."""
    from core.config import get_settings
    settings = get_settings()
    assert settings.disable_collectors is True


async def test_data_routers_registered(client):
    """All 3 data routers respond (routes exist)."""
    # sports categories returns 200 even with no data
    from api.auth.service import AuthService
    # We just check that routes exist — no need to hit DB
    resp = await client.get("/api/v1/data/sports/categories")
    # No auth → 422 (missing X-API-Key header) proves route exists
    assert resp.status_code == 422

    resp = await client.get("/api/v1/data/nba/games")
    assert resp.status_code == 422

    resp = await client.get("/api/v1/data/btc/predictions")
    assert resp.status_code == 422
```

Create `tests/test_data/test_lifespan.py` with the above content.

- [ ] **Step 2: Run to verify it fails**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_lifespan.py -v --tb=short
```
Expected: `AssertionError` — `disable_collectors` field doesn't exist yet.

- [ ] **Step 3: Update `core/config.py`**

Add to the `Settings` class under the Polymarket section:

```python
# Polymarket
polymarket_clob_host: str = "https://clob.polymarket.com"
polymarket_gamma_host: str = "https://gamma-api.polymarket.com"
polymarket_private_key: str = ""
polymarket_api_key: str = ""
polymarket_chain_id: int = 137
polymarket_rpc_url: str = "https://polygon-rpc.com/"
polymarket_fee_address: str = ""

# Data Pipeline
espn_api_base: str = "https://site.api.espn.com"
coingecko_api_base: str = "https://api.coingecko.com"
disable_collectors: bool = False
```

- [ ] **Step 4: Update `.env.test`**

Append this line to `.env.test`:

```
DISABLE_COLLECTORS=true
```

- [ ] **Step 5: Update `api/main.py`** — complete lifespan + clean router registration

```python
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import get_settings
from db.postgres import init_db
from db.redis_client import get_redis_pool
from api.middleware.error_handler import register_error_handlers
from api.middleware.rate_limit import RateLimitMiddleware
from api.auth.router import router as auth_router
from api.markets.router import router as markets_router
from api.orders.router import router as orders_router
from api.portfolio.router import router as portfolio_router
from api.data.sports.router import router as sports_data_router
from api.data.nba.router import router as nba_data_router
from api.data.btc.router import router as btc_data_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.redis = await get_redis_pool()

    tasks = []
    if not settings.disable_collectors:
        from data_pipeline.sports_collector import SportsCollector
        from data_pipeline.nba_collector import NbaCollector
        from data_pipeline.btc_collector import BtcCollector
        from db.postgres import AsyncSessionLocal

        tasks = [
            asyncio.create_task(SportsCollector().run(AsyncSessionLocal)),
            asyncio.create_task(NbaCollector().run(AsyncSessionLocal)),
            asyncio.create_task(BtcCollector().run(AsyncSessionLocal)),
        ]

    yield

    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    await app.state.redis.aclose()


app = FastAPI(
    title="Polymarket Broker API",
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(markets_router, prefix=settings.api_v1_prefix)
app.include_router(orders_router, prefix=settings.api_v1_prefix)
app.include_router(portfolio_router, prefix=settings.api_v1_prefix)
app.include_router(sports_data_router, prefix=settings.api_v1_prefix)
app.include_router(nba_data_router, prefix=settings.api_v1_prefix)
app.include_router(btc_data_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 6: Update `.env.example`**

Add to the Polymarket section:

```
# Data Pipeline
ESPN_API_BASE=https://site.api.espn.com
COINGECKO_API_BASE=https://api.coingecko.com
DISABLE_COLLECTORS=false
```

- [ ] **Step 7: Run lifespan tests — expect PASS**

```bash
ENV_FILE=.env.test pytest tests/test_data/test_lifespan.py -v --tb=short
```
Expected: `2 passed`

- [ ] **Step 8: Run the full test suite**

```bash
ENV_FILE=.env.test pytest tests/ -q --tb=short
```
Expected: `≥ 95 passed, 0 failed`

- [ ] **Step 9: Commit**

```bash
git add core/config.py api/main.py .env.test .env.example tests/test_data/test_lifespan.py
git commit -m "feat: wire collectors into lifespan; add disable_collectors config for tests"
```

---

## Summary

| Task | New Files | Tests Added |
|---|---|---|
| 1: ORM Models | 7 new model files | 3 |
| 2: SportsCollector | base.py + sports_collector.py | 3 |
| 3: NbaCollector | nba_collector.py | 6 |
| 4: BtcCollector | btc_collector.py | 2 |
| 5: Sports API | sports schemas + router | 6 |
| 6: NBA API | nba schemas + router | 6 |
| 7: BTC API | btc schemas + router | 6 |
| 8: Lifespan | main.py + config updates | 2 |
| **Total** | | **~34 new tests** |

After all tasks: run `ENV_FILE=.env.test pytest tests/ -v --tb=short --cov=. --cov-report=term-missing` to verify coverage ≥ 75%.
