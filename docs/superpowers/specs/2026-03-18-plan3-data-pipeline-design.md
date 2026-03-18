# Plan 3: Data Pipeline Design Spec

**Date**: 2026-03-18
**Status**: Approved
**Scope**: Background data collectors (Sports / NBA / BTC) + `/api/v1/data/` REST endpoints

---

## 1. Goal

Add a data layer to the Polymarket Broker API that:
1. Continuously collects sports, NBA fusion, and BTC prediction data from Polymarket + free external APIs
2. Stores snapshots in PostgreSQL
3. Exposes 11 new REST endpoints under `/api/v1/data/`

This is the core differentiating layer of the platform — data unavailable via Polymarket directly.

---

## 2. Architecture

### Collector Runtime

Collectors run as **FastAPI lifespan `asyncio` tasks** (not separate containers). Three tasks start on app startup and are cancelled on shutdown. Each task runs an infinite poll loop with error isolation — a single failed collect cycle logs the error and retries after the interval, never crashing the loop.

```
FastAPI lifespan startup
  ├── asyncio.create_task(SportsCollector().run(db_factory))   # every 300s
  ├── asyncio.create_task(NbaCollector().run(db_factory))      # every 30s
  └── asyncio.create_task(BtcCollector().run(db_factory))      # every 30s

PostgreSQL (shared with API)
  ├── sports_events    ← SportsCollector writes (upsert)
  ├── nba_games        ← NbaCollector writes (upsert)
  └── btc_snapshots    ← BtcCollector writes (append-only)

GET /api/v1/data/sports/**  → reads sports_events
GET /api/v1/data/nba/**     → reads nba_games
GET /api/v1/data/btc/**     → reads btc_snapshots
```

Collectors and API are fully decoupled — collectors only write, API only reads.

### Data Sources

| Collector | External Source | Auth Required |
|---|---|---|
| Sports | Polymarket Gamma API (`/markets?tag=sports`) | No |
| NBA | ESPN unofficial API (`site.api.espn.com`) + Polymarket Gamma | No |
| BTC | CoinGecko free API (`/simple/price`) + Polymarket Gamma | No |

All three collectors work without paid API keys or account registration.

---

## 3. File Structure

### New Files

```
data_pipeline/
├── __init__.py
├── base.py               # BaseCollector: shared poll loop + error handling
├── sports_collector.py   # SportsCollector(BaseCollector)
├── nba_collector.py      # NbaCollector(BaseCollector)
└── btc_collector.py      # BtcCollector(BaseCollector)

api/data/
├── __init__.py
├── sports/
│   ├── __init__.py
│   ├── models.py         # SQLAlchemy ORM: SportsEvent
│   ├── schemas.py        # Pydantic response models
│   └── router.py         # 3 endpoints
├── nba/
│   ├── __init__.py
│   ├── models.py         # NbaGame
│   ├── schemas.py
│   └── router.py         # 4 endpoints
└── btc/
    ├── __init__.py
    ├── models.py         # BtcSnapshot
    ├── schemas.py
    └── router.py         # 4 endpoints
```

### Modified Files

| File | Change |
|---|---|
| `api/main.py` | Add lifespan context manager; register 3 new routers |
| `db/postgres.py` | Register SportsEvent, NbaGame, BtcSnapshot models |
| `core/config.py` | Add `espn_api_base`, `coingecko_api_base` (defaults, no keys needed) |

---

## 4. Database Schema

### `sports_events` (upsert on `market_id`)

```sql
CREATE TABLE sports_events (
    id              SERIAL PRIMARY KEY,
    market_id       TEXT NOT NULL UNIQUE,
    sport_slug      TEXT NOT NULL,       -- 'nba', 'nfl', 'epl', 'ufc', ...
    question        TEXT NOT NULL,
    outcomes        JSONB NOT NULL,      -- [{"name":"Yes","price":0.72,"token_id":"..."}]
    status          TEXT NOT NULL,       -- 'active' | 'resolved' | 'closed'
    volume          NUMERIC(20, 6),
    end_date        TIMESTAMPTZ,
    data_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON sports_events (sport_slug);
CREATE INDEX ON sports_events (data_updated_at);
```

### `nba_games` (upsert on `game_id`)

```sql
CREATE TABLE nba_games (
    id                  SERIAL PRIMARY KEY,
    game_id             TEXT NOT NULL UNIQUE,   -- ESPN game ID
    home_team           TEXT NOT NULL,
    away_team           TEXT NOT NULL,
    game_date           DATE NOT NULL,
    game_status         TEXT NOT NULL,          -- 'scheduled' | 'live' | 'final'
    score_home          INT,
    score_away          INT,
    quarter             INT,
    time_remaining      TEXT,                   -- e.g. "4:22"
    market_id           TEXT,                   -- Polymarket market_id
    home_win_prob       NUMERIC(6, 4),          -- Polymarket implied prob
    away_win_prob       NUMERIC(6, 4),
    last_trade_price    NUMERIC(6, 4),
    bias_direction      TEXT,                   -- 'HOME_UNDERPRICED' | 'AWAY_UNDERPRICED' | 'NEUTRAL'
    bias_magnitude_bps  INT,
    data_updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON nba_games (game_date);
CREATE INDEX ON nba_games (data_updated_at);
```

### `btc_snapshots` (append-only time series)

```sql
CREATE TABLE btc_snapshots (
    id              BIGSERIAL PRIMARY KEY,
    timeframe       TEXT NOT NULL,           -- '5m' | '15m' | '1h' | '4h'
    price_usd       NUMERIC(20, 2) NOT NULL,
    market_id       TEXT,                    -- Polymarket prediction market ID
    prediction_prob NUMERIC(6, 4),           -- Polymarket implied prob (up)
    volume          NUMERIC(20, 6),
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX ON btc_snapshots (timeframe, recorded_at DESC);
```

---

## 5. Collector Design

### `data_pipeline/base.py`

```python
class BaseCollector:
    name: str
    interval_seconds: int

    async def collect(self, db: AsyncSession) -> None:
        raise NotImplementedError

    async def run(self, db_factory) -> None:
        while True:
            try:
                async with db_factory() as db:
                    await self.collect(db)
            except Exception as e:
                logger.error(f"[{self.name}] collect failed: {e}")
            await asyncio.sleep(self.interval_seconds)
```

### `SportsCollector` (interval: 300s)

1. `GET /markets?tag=sports&active=true` from Polymarket Gamma API (paginated, limit=100)
2. Parse `sport_slug` from market tags
3. Upsert each market into `sports_events` by `market_id`
4. Update `data_updated_at = NOW()`

### `NbaCollector` (interval: 30s)

1. `GET site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard` → today's games
2. `GET /markets?tag=nba` from Polymarket Gamma → NBA prediction markets
3. Match ESPN games to Polymarket markets by fuzzy team name comparison
4. Compute `bias_signal`:
   - `statistical_prob = estimate_win_prob(score_home, score_away, quarter, time_remaining)`
   - `delta_bps = abs(statistical_prob - polymarket_home_win_prob) * 10000`
   - `bias_direction`: `HOME_UNDERPRICED` / `AWAY_UNDERPRICED` / `NEUTRAL` (threshold: 300 bps)
5. Upsert into `nba_games` by `game_id`

`estimate_win_prob()` — v1 simplified linear model based on score differential and time elapsed. No external libraries.

### `BtcCollector` (interval: 30s)

1. `GET api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd` → BTC price
2. `GET /markets?tag=crypto&q=BTC` from Polymarket Gamma → 4 BTC prediction markets (5m/15m/1h/4h)
3. Append 4 rows to `btc_snapshots` (one per timeframe)

---

## 6. API Endpoints

All 11 endpoints require `X-API-Key` authentication (reuse `get_current_user_from_api_key`).

### Sports (3 endpoints)

```
GET /api/v1/data/sports/categories
→ List all sport slugs with active event count
→ Response: [{ "slug": "nba", "name": "NBA Basketball", "active_events": 12 }, ...]

GET /api/v1/data/sports/{sport}/events
→ Paginated list of active markets for this sport
→ Query: status, limit (default 20, max 100), cursor
→ Includes stale flag

GET /api/v1/data/sports/{sport}/events/{market_id}/orderbook
→ Proxy to Polymarket CLOB orderbook (live, not from DB)
→ Reuses ClobClient; same response shape as GET /markets/{market_id}/orderbook
```

### NBA (4 endpoints)

```
GET /api/v1/data/nba/games
→ Today's + recent NBA games list
→ Query: date (YYYY-MM-DD), status (scheduled|live|final), limit, cursor

GET /api/v1/data/nba/games/{game_id}
→ Single game detail (score, quarter, status)
→ Includes stale flag

GET /api/v1/data/nba/games/{game_id}/fusion
→ ★ Core differentiating endpoint
→ Response:
  {
    "game_id": "...",
    "score": { "home": 87, "away": 94, "quarter": 3, "time_remaining": "4:22" },
    "polymarket": { "home_win_prob": 0.31, "away_win_prob": 0.69, "last_trade_price": 0.69 },
    "bias_signal": { "direction": "HOME_UNDERPRICED", "magnitude_bps": 420 },
    "stale": false,
    "data_updated_at": "2026-03-18T22:14:05Z"
  }

GET /api/v1/data/nba/games/{game_id}/orderbook
→ Proxy to Polymarket CLOB orderbook for this game's market_id
```

### BTC (4 endpoints)

```
GET /api/v1/data/btc/predictions
→ Latest snapshot for all 4 timeframes
→ Response: [{ "timeframe": "5m", "price_usd": 67420.5, "prediction_prob": 0.61, ... }, ...]

GET /api/v1/data/btc/predictions/{timeframe}
→ Latest snapshot + recent history for one timeframe (5m | 15m | 1h | 4h)
→ Query: limit (default 20, max 100)

GET /api/v1/data/btc/onchain
→ Proxy to Polygon on-chain BTC-related Polymarket trades via ClobClient

GET /api/v1/data/btc/history
→ Historical btc_snapshots query
→ Query: timeframe, from, to (ISO 8601), limit
```

---

## 7. Staleness Handling

All DB-backed endpoints wrap their response in a staleness envelope:

```json
{
  "stale": false,
  "data_updated_at": "2026-03-18T10:00:00Z",
  "data": { ... }
}
```

| Domain | Update Interval | Stale Threshold |
|---|---|---|
| Sports | 5 min | `data_updated_at < now() - interval '10 minutes'` |
| NBA | 30 sec | `data_updated_at < now() - interval '2 minutes'` |
| BTC | 30 sec | `recorded_at < now() - interval '2 minutes'` |

`stale: true` returns HTTP 200 with the last collected data. Consumers decide whether to use stale data.

---

## 8. Testing Strategy

- **Collector unit tests**: Mock `collect()` method; verify upsert/insert SQL correctness and bias_signal calculation
- **API endpoint tests**: Pre-populate DB fixtures; verify response shape, staleness flag, pagination
- **Staleness tests**: Insert rows with old `data_updated_at`; verify `stale: true` in response
- **No real external API calls in tests**: All ESPN/CoinGecko/Polymarket calls mocked

Target: ~25 new tests, maintaining >75% coverage.

---

## 9. Tech Stack

No new dependencies beyond what's already installed. Uses:
- `httpx` (already in requirements) for async HTTP to ESPN/CoinGecko
- SQLAlchemy 2 async (existing) for DB operations
- `asyncio` (stdlib) for lifespan tasks
