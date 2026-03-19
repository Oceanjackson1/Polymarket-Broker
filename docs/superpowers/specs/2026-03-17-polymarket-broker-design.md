# Polymarket Broker API Platform — Design Spec

**Date**: 2026-03-17
**Status**: Approved
**Author**: Ocean Jackson

---

## 1. Overview

A **Polymarket Broker API Platform** that wraps Polymarket's native CLOB + Gamma APIs, adds value through enhanced data infrastructure and AI analysis, and exposes a clean versioned REST API to two types of consumers simultaneously:

1. **Own terminal products** — Telegram Bot, Web Dashboard
2. **Third-party developers** — building their own apps on top of the Broker API

**Revenue model**: Transaction fee (Broker fee layered on top of Polymarket's native fees) + subscription tiers.

**Core differentiation**: The only Broker that provides NBA×Polymarket real-time fusion data, 145-sport historical full order books, BTC multi-timeframe on-chain prediction data, and AI pricing-bias analysis — data unavailable via Polymarket directly.

---

## 2. Architecture

### System Layers

```
┌──────────────────────────────────────────────────────┐
│                  Consumers                            │
│  [Telegram Bot]   [Web App]   [Third-party Devs]     │
└────────────────────┬─────────────────────────────────┘
                     │  HTTP / WebSocket
                     ▼
┌──────────────────────────────────────────────────────┐
│           Broker API v1 (FastAPI)                     │
│  auth │ markets │ orders │ portfolio │ data │ analysis│
└──┬───────────────────────────────────────────────────┘
   │                        │
   ▼                        ▼
┌──────────────────┐  ┌─────────────────────────────┐
│ Polymarket APIs  │  │  Enhanced Data Layer         │
│ CLOB + Gamma +   │  │  Sports / NBA / BTC Pipeline │
│ Polygon chain    │  │  (background collectors)     │
└──────────────────┘  └─────────────────────────────┘
```

### Key Principle
All consumers — own Telegram Bot, own Web App, third-party developers — call the **identical API**. The Broker dogfoods its own API. No separate internal paths.

---

## 3. API Domain Map

```
/api/v1/
├── auth/           User registration, API key CRUD, wallet auth
├── markets/        All Polymarket events (all categories, all markets)
├── orders/         Order placement, cancellation, history
├── portfolio/      Positions, balance, P&L
├── data/
│   ├── sports/     145-sport enhanced order book data
│   ├── nba/        NBA live score × Polymarket odds fusion
│   ├── btc/        BTC multi-timeframe prediction data
│   └── weather/    Weather forecast × Polymarket temperature market fusion
├── analysis/       AI-powered market analysis (DeepSeek)
├── strategies/     Pre-built executable strategies
├── webhooks/       Event subscriptions
└── developer/      Usage stats, billing, tier management
```

**Scope**: `markets/` and `orders/` cover **all Polymarket event categories** (politics, sports, finance, crypto, technology, etc.). The `data/` sub-routes are additive enhanced layers, not restrictions on tradeable markets.

**v1 Strategies**: Convergence arbitrage only at launch. `GET /api/v1/strategies` returns the list of available strategy slugs with metadata; currently `["convergence"]`.

---

## 4. Authentication

### Two Auth Paths

**Path A — API Key (Hosted Mode)**
```
Header: X-API-Key: pm_live_sk_xxxx
→ Server checks key in PostgreSQL, resolves user + tier + scopes
→ Broker backend holds Polymarket operator credentials
→ Signs and submits orders on behalf of user
→ Use for: all POST /api/v1/orders calls
```

**Path B — Wallet Auth (Non-custodial Mode)**
```
POST /api/v1/auth/wallet/challenge   → { nonce, expires_at }
Wallet signs nonce (EIP-191)
POST /api/v1/auth/wallet/verify      → { access_token, refresh_token }
  access_token: JWT, 15-minute TTL
  refresh_token: opaque, 30-day TTL
POST /api/v1/auth/wallet/refresh     → { access_token }
Header: Authorization: Bearer <access_token>
POST /api/v1/orders/build            → returns unsigned EIP-712 payload
User signs locally
POST /api/v1/orders/submit           → broker verifies + broadcasts
```

**Mode selection**: Requests to `POST /api/v1/orders` (hosted) require `X-API-Key`. Requests to `POST /api/v1/orders/build` and `POST /api/v1/orders/submit` (non-custodial) require `Authorization: Bearer`. These are two distinct endpoints — no ambiguity at the router level.

### Auth Endpoints

```
POST   /api/v1/auth/register                  # Email + password registration
POST   /api/v1/auth/login                     # Email + password → JWT
POST   /api/v1/auth/wallet/challenge           # Get nonce for wallet signing
POST   /api/v1/auth/wallet/verify             # Verify wallet signature → JWT
POST   /api/v1/auth/wallet/refresh            # Refresh access token

GET    /api/v1/auth/keys                      # List all API keys for account
POST   /api/v1/auth/keys                      # Create new API key { name, scopes }
DELETE /api/v1/auth/keys/{key_id}             # Revoke API key
```

### API Key Format
```
pm_live_sk_xxxxxxxxxxxxxxxx   # Production, full trading
pm_test_sk_xxxxxxxxxxxxxxxx   # Testnet (Polygon Amoy)
pm_live_ro_xxxxxxxxxxxxxxxx   # Read-only, no trading
```

### Scopes
| Scope | Description |
|---|---|
| `markets:read` | Query markets, orderbooks, trades |
| `orders:write` | Place and cancel orders |
| `portfolio:read` | View positions, balance |
| `data:read` | Enhanced data (sports/NBA/BTC) |
| `analysis:read` | AI analysis endpoints |
| `strategies:execute` | Run pre-built strategies |
| `webhooks:write` | Register webhooks |

### Subscription Tiers
| Tier | API Calls/Day | Per-min Burst | Taker Broker Fee | Webhook | AI Analysis | Strategies |
|---|---|---|---|---|---|---|
| **Free** | 500 | 20 req/min | +10 bps (0.1%) | ✗ | 10/day (shared across all `/analysis/*`) | ✗ |
| **Pro** ($99/mo) | Unlimited | 300 req/min | +5 bps (0.05%) | ✓ | Unlimited | ✓ |
| **Enterprise** | Unlimited | Custom | Custom | ✓ | Unlimited | ✓ |

**Maker fee**: 0% Broker-layer additional fee at all tiers. Note: Polymarket's own protocol may have separate maker/taker implications; the 0% refers solely to the Broker's additive `feeRateBps` on maker-side fills.

**AI Analysis quota**: 10/day on Free applies per API key, shared across all `/analysis/` endpoints (`/market/`, `/nba/`, `/ask`, `/scan`).

### Rate Limit Response Headers
```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 347
X-RateLimit-Reset: 1742169600      # Unix timestamp of next reset
X-RateLimit-Burst-Limit: 20
```
When exceeded: `HTTP 429 Too Many Requests` with `Retry-After` header.
WebSocket connections are not counted against the daily call quota.

---

## 5. Standard Error Response

All errors return a consistent envelope:

```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "USDC balance too low to place this order.",
    "details": {}
  }
}
```

### Common HTTP Status Codes
| Status | Meaning |
|---|---|
| 400 | Bad request — validation error; `details` contains field-level errors |
| 401 | Missing or invalid API key / JWT |
| 403 | Valid credentials but insufficient scope |
| 404 | Resource not found |
| 422 | Request body parseable but semantically invalid |
| 429 | Rate limit exceeded |
| 502 | Polymarket upstream API error |
| 503 | Polymarket CLOB temporarily unavailable |

---

## 6. Trading Layer

### Order Object Schema
All order endpoints return or reference the Order object:

```json
{
  "order_id": "ord_abc123",
  "market_id": "0x...",
  "token_id": "217426331...",
  "side": "BUY",
  "type": "LIMIT",
  "price": 0.72,
  "size": 100.0,
  "size_filled": 45.0,
  "size_remaining": 55.0,
  "status": "PARTIALLY_FILLED",
  "broker_fee_bps": 10,
  "polymarket_order_id": "0x...",
  "created_at": "2026-03-17T10:00:00Z",
  "updated_at": "2026-03-17T10:01:00Z",
  "expires_at": null
}
```

Status values: `PENDING`, `OPEN`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `EXPIRED`

### Order Lifecycle — Hosted Mode
```
POST /api/v1/orders { market_id, side, price, size, type, [expires_at] }
  → validate params + market rules
  → inject feeRateBps (from user's tier)
  → EIP-712 sign (operator key)
  → submit to Polymarket CLOB API
  → write to PostgreSQL (order state) + Turso (ledger entry)
  → return Order object
```

### Order Lifecycle — Non-custodial Mode
```
POST /api/v1/orders/build { market_id, side, price, size }
  → construct canonical EIP-712 payload with feeRateBps
  → store payload hash in Redis (60s TTL) keyed to user session
  → return { eip712_payload, payload_hash }

POST /api/v1/orders/submit { payload_hash, signature }
  → re-derive expected payload from stored hash
  → verify submitted payload_hash matches stored hash (tamper protection)
  → verify signature against payload
  → broadcast to Polymarket CLOB
  → return Order object
```

**Fee tamper protection**: The server re-derives the canonical payload from stored parameters and rejects any `submit` request where the submitted hash doesn't match. Users cannot modify `feeRateBps` between build and submit.

### Order Types
| Type | Description | Notes |
|---|---|---|
| `LIMIT` | Limit order, GTC | Default |
| `MARKET` | Market order, FOK | Immediate fill or cancel |
| `GTD` | Limit with expiry | Requires `expires_at` field |
| `TWAP` | Time-weighted split | Broker-level: parent order with child legs |

### TWAP Semantics
- `POST /api/v1/orders` with `type: TWAP` returns a parent Order with `order_id = ord_twap_xxx`
- Response includes `{ ..., "child_legs": ["ord_leg_1", "ord_leg_2", ...] }`
- `DELETE /api/v1/orders/ord_twap_xxx` cancels all unfilled child legs; filled legs are settled
- `GET /api/v1/orders/ord_twap_xxx` returns parent object with aggregate `size_filled` and individual `child_legs` status

### Order Endpoints
```
POST   /api/v1/orders                    # Hosted mode: place order → Order
POST   /api/v1/orders/build              # Non-custodial: build EIP-712 → { eip712_payload, payload_hash }
POST   /api/v1/orders/submit             # Non-custodial: submit signed order → Order
GET    /api/v1/orders                    # List orders (paginated)
GET    /api/v1/orders/{order_id}         # Order detail → Order
DELETE /api/v1/orders/{order_id}         # Cancel order
DELETE /api/v1/orders                    # Cancel all open orders

GET    /api/v1/portfolio/positions       # Current positions
GET    /api/v1/portfolio/balance         # USDC balance { balance, locked, available }
GET    /api/v1/portfolio/pnl            # P&L { realized, unrealized, fees_paid_broker, fees_paid_polymarket }
```

### Pagination (all list endpoints)
```
GET /api/v1/orders?cursor=xxx&limit=50&status=OPEN&market_id=0x...&sort=created_at:desc

Response:
{
  "data": [ ...Order objects... ],
  "pagination": {
    "cursor": "next_cursor_token",
    "has_more": true,
    "limit": 50
  }
}
```
Default limit: 20. Maximum limit: 100. Cursor-based pagination throughout.

### Fee Collection
Fees collected via `feeRateBps` field in Polymarket order struct, directed to Broker's fee recipient address. Settled on-chain at order fill time (Polygon).

### Risk Controls (reuse `Trading-Agents/risk_guard.py`)
- Maximum single-order size limit (configurable per tier)
- Per-market position cap
- Daily drawdown circuit breaker (suspends trading, requires manual reset via `/developer/risk/reset`)
- Abnormal order frequency detection (API key abuse / runaway bot protection)

---

## 7. Data Infrastructure

### 7.1 General Market Data (All Categories)
Source: Polymarket Gamma API + CLOB API + `Real-Time-Scraping-Of-Polymarket-Events`

```
GET  /api/v1/markets                              # All markets (filter: category, status, tag)
GET  /api/v1/markets/{market_id}                  # Market detail
GET  /api/v1/markets/{market_id}/orderbook        # Live order book
GET  /api/v1/markets/{market_id}/trades           # Historical trades (paginated)
GET  /api/v1/markets/{market_id}/midpoint         # Mid price { mid, timestamp }
GET  /api/v1/markets/search?q=                    # Full-text search (paginated)
WS   /ws/markets/{market_id}                      # Real-time orderbook stream
```

### 7.2 Sports Enhanced Data
Source: `Polymarket-Sports-Data` — 145 sport/esport categories

**Sport identifier format**: URL-safe slug string, e.g., `nba`, `nfl`, `epl`, `ufc`, `cs2`.
Full list returned by `/data/sports/categories`.

```
GET  /api/v1/data/sports/categories
     → [{ "slug": "nba", "name": "NBA Basketball", "active_events": 12 }, ...]

GET  /api/v1/data/sports/{sport}/events           # e.g., /data/sports/nba/events
GET  /api/v1/data/sports/{sport}/events/{event_id}/orderbook
GET  /api/v1/data/sports/{sport}/events/{event_id}/realized
```

**Differentiator**: Full historical order books per event — unavailable via Polymarket directly.

### 7.3 NBA Fusion Data
Source: `NBA-Data-Polymarket` — ESPN + NBA Official × Polymarket CLOB/WebSocket

```
GET  /api/v1/data/nba/games                        # Today/upcoming NBA games
GET  /api/v1/data/nba/games/{game_id}              # Game detail (live score + status)
GET  /api/v1/data/nba/games/{game_id}/fusion       # ★ Live score × Polymarket implied prob + bias signal
GET  /api/v1/data/nba/games/{game_id}/orderbook    # Polymarket orderbook for this game
WS   /ws/data/nba/{game_id}/live                   # Real-time score + odds sync
```

**Fusion response example**:
```json
{
  "game_id": "nba_2026_gsw_lal",
  "score": { "home": 87, "away": 94, "quarter": 3, "time_remaining": "4:22" },
  "polymarket": {
    "home_win_prob": 0.31,
    "away_win_prob": 0.69,
    "last_trade_price": 0.69
  },
  "bias_signal": { "direction": "HOME_UNDERPRICED", "magnitude_bps": 420 },
  "updated_at": "2026-03-17T22:14:05Z"
}
```

### 7.4 BTC Prediction Data
Source: `BTC-UpDown-MultiTimeframe-Trade-Scraper` + `Dome-API-Data` + on-chain Polygon

```
GET  /api/v1/data/btc/predictions                  # BTC prediction market list
GET  /api/v1/data/btc/predictions/{timeframe}      # 5m / 15m / 1h / 4h
GET  /api/v1/data/btc/onchain                      # Polygon on-chain trades (ms precision)
GET  /api/v1/data/btc/history                      # Historical backfill (Gamma API)
```

Note: `/data/btc/onchain` is a top-level route (not under `/predictions/{timeframe}`) to avoid router collision with the `{timeframe}` path parameter.

### 7.5 Weather Forecast Data
Source: Open-Meteo Ensemble API × Polymarket temperature markets

**Market format**: Polymarket hosts standardized temperature prediction markets: `"Highest temperature in [City] on [Date]?"` with ~11 outcome markets per event, each representing a 1°C temperature range (e.g., "13°C or below", "14°C", "15°C", ..., "23°C or higher"). ~110 active events across 20+ global cities with ~$3.6M daily volume.

**Resolution source**: Weather Underground historical station data (specified per event by Polymarket).

**Data source**: Open-Meteo Ensemble API — 51-member ensemble forecast providing probabilistic temperature distributions. Free, no API key, ~10K requests/day.

**City coordinate resolution**: Built-in mapping table for known cities (20+) with Open-Meteo Geocoding API fallback for new cities, cached in PostgreSQL `city_coordinates` table.

```
GET  /api/v1/data/weather/dates                                    # Active dates with weather markets
GET  /api/v1/data/weather/dates/{date}/cities                      # Cities with markets on that date, sorted by bias
GET  /api/v1/data/weather/dates/{date}/cities/{city}/fusion        # ★ Forecast prob × market price × bias per temp bin
GET  /api/v1/data/weather/dates/{date}/cities/{city}/orderbook     # Polymarket orderbook for this event
```

**Fusion response example**:
```json
{
  "city": "Tokyo",
  "date": "2026-03-19",
  "event_id": "evt_xxx",
  "temp_bins": [
    {
      "range": "13°C or below",
      "market_id": "0x...",
      "market_prob": 0.02,
      "forecast_prob": 0.00,
      "bias_direction": "NEUTRAL",
      "bias_bps": 200
    },
    {
      "range": "18°C",
      "market_id": "0x...",
      "market_prob": 0.15,
      "forecast_prob": 0.25,
      "bias_direction": "FORECAST_HIGHER",
      "bias_bps": 1000
    }
  ],
  "max_bias": { "range": "18°C", "direction": "FORECAST_HIGHER", "magnitude_bps": 1000 },
  "data_updated_at": "2026-03-19T14:05:00Z"
}
```

**Bias signal**: Same `compute_bias` logic as NBA fusion (threshold: 300 bps). Direction values: `FORECAST_HIGHER` (ensemble model gives higher probability than market price), `MARKET_HIGHER`, `NEUTRAL`.

**Differentiator**: Only platform combining ensemble weather forecast probabilities with Polymarket temperature market prices to surface pricing bias — weather data unavailable via Polymarket directly.

### 7.6 AI Analysis
Source: `Polymind-AI` + `BTC-Up-Down-Polymarket-Agent` (DeepSeek)

**Signal delivery**: All consumers (own apps and third-party developers) receive signals simultaneously. No internal priority queue. The Broker's own Telegram Bot calls the same `/analysis/` endpoints with no advance access.

```
GET  /api/v1/analysis/market/{market_id}           # AI probability estimate vs current market price
POST /api/v1/analysis/scan                         # Full-market scan: top pricing-bias opportunities
GET  /api/v1/analysis/nba/{game_id}                # AI directional suggestion (uses fusion data)
POST /api/v1/analysis/ask                          # Natural language query
```

### 7.7 Strategies
Source: `Polymarket-Trading-Agents` — strategy logic reused directly

v1 ships with convergence arbitrage only.

```
GET  /api/v1/strategies                                          # [{ "slug": "convergence", "description": "..." }]
GET  /api/v1/strategies/convergence/opportunities                # Markets: prob ≥ 95%, expiry ≤ 3 days
POST /api/v1/strategies/convergence/execute { market_id, size } # Place convergence trade
GET  /api/v1/strategies/convergence/positions                    # Active convergence positions
```

---

## 8. Webhooks

### Registration
```
POST   /api/v1/webhooks     { url, events: ["order.filled", ...], secret }
GET    /api/v1/webhooks
DELETE /api/v1/webhooks/{webhook_id}
```

### Delivery
- Method: `POST` to registered URL
- Content-Type: `application/json`
- Signed with HMAC-SHA256 using `secret` provided at registration
- Signature header: `X-Broker-Signature: sha256=<hex>`
- Consumers verify: `HMAC-SHA256(secret, raw_body) == signature`

### Retry Policy
- On non-2xx response: retry with exponential backoff — 1s, 5s, 30s, 5min, 30min (5 attempts total)
- After 5 failures: webhook marked `FAILED`, owner notified via `/developer/webhooks` status endpoint
- No dead-letter queue in v1; failed events are logged but not replayed after 5 attempts

### Payload Envelope
```json
{
  "event": "order.filled",
  "webhook_id": "wh_abc123",
  "timestamp": "2026-03-17T10:01:00Z",
  "data": { ...event-specific object... }
}
```

### Event Types
| Event | Trigger |
|---|---|
| `order.filled` | Order fully filled |
| `order.cancelled` | Order cancelled (user or expiry) |
| `market.resolved` | Market settled on-chain |
| `position.opened` | New position opened |
| `position.closed` | Position fully closed |
| `strategy.executed` | Strategy order placed |
| `analysis.signal` | AI pricing-bias alert triggered |

---

## 9. Developer Endpoints

```
GET  /api/v1/developer/usage              # { calls_today, calls_remaining, tier, reset_at }
GET  /api/v1/developer/billing            # { tier, next_billing_date, amount_due }
POST /api/v1/developer/billing/upgrade    # { tier: "pro" } → upgrade subscription
GET  /api/v1/developer/webhooks           # Webhook health status
POST /api/v1/developer/risk/reset         # Reset daily drawdown circuit breaker (manual)
```

---

## 10. Data Residency

| Data | Storage | Rationale |
|---|---|---|
| Users, API keys, scopes, tiers | PostgreSQL | Multi-user relational data |
| Order state (status, fills) | PostgreSQL | Consistent with user data, transactional |
| Ledger (P&L, fee breakdown) | Turso (libSQL) | Distributed, already used in Trading-Agents |
| Rate limit counters | Redis | High-throughput, TTL-native |
| Session nonces + payload hashes | Redis | Short TTL, eviction acceptable |
| Enhanced data (sports, NBA, BTC, weather) | PostgreSQL | Queryable, time-series friendly |
| City coordinates cache | PostgreSQL | Geocoding API fallback results |

PostgreSQL is source of truth for order lifecycle. Turso holds the append-only financial ledger. No data spans both stores — they are separate concerns.

---

## 11. Data Pipeline Operational Model

The four background collectors (`sports_collector.py`, `nba_collector.py`, `btc_collector.py`, `weather_collector.py`) run as **separate Docker containers** alongside the FastAPI container in the same Docker Compose stack.

**Staleness handling**: All enhanced data endpoints return a `data_updated_at` timestamp. If the collector for that data source has not pushed a fresh update within its expected interval (NBA: 30s, Sports: 5min, BTC: 30s, Weather: 5min), the API returns `HTTP 200` with `{ "stale": true, "data_updated_at": "...", "data": {...} }`. Consumers are responsible for handling stale signals.

---

## 12. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| API Framework | FastAPI (Python) | Consistent with all existing repos; auto-generates OpenAPI |
| Database | PostgreSQL | Multi-user support (replaces SQLite) |
| Cache / Rate Limit | Redis | Sliding window rate limiting, response caching, nonce store |
| Ledger | libSQL / Turso | Already used in Trading-Agents; distributed-friendly |
| API Key Encryption | Fernet AES-256 | Already implemented in NBA-AI-Agent auth module |
| Docs | Mintlify | Modern developer portal, OpenAPI-native |
| Deploy | Docker Compose + Tencent Cloud | Existing infrastructure reused |
| Frontend | Vercel (Next.js) | Existing Trading-Agents dashboard pattern |

---

## 13. Repository Structure

```
polymarket-broker/
├── api/                        # FastAPI — Broker API v1
│   ├── main.py
│   ├── auth/
│   ├── markets/
│   ├── orders/
│   ├── portfolio/
│   ├── data/
│   │   ├── sports/
│   │   ├── nba/
│   │   ├── btc/
│   │   └── weather/
│   ├── analysis/
│   ├── strategies/
│   ├── webhooks/
│   └── developer/
├── core/                       # Shared business logic (no HTTP)
│   ├── polymarket/             # ← from Polymarket-Trade-Infra
│   │   ├── clob_client.py
│   │   ├── gamma_client.py
│   │   └── eip712.py
│   ├── fee_engine.py
│   ├── risk_guard.py           # ← from Polymarket-Trading-Agents
│   └── ledger.py               # libSQL/Turso
├── data_pipeline/              # Background data collectors (separate Docker containers)
│   ├── sports_collector.py     # ← from Polymarket-Sports-Data
│   ├── nba_collector.py        # ← from NBA-Data-Polymarket
│   ├── btc_collector.py        # ← from BTC scrapers
│   └── weather_collector.py    # Open-Meteo ensemble × Polymarket temperature markets
├── consumers/
│   ├── telegram_bot/           # ← from Polymarket-NBA-AI-Agent bot layer
│   └── web/                    # ← from Polymarket-Trading-Agents dashboard
├── docs/                       # Mintlify source
├── tests/
├── deploy/
│   ├── docker-compose.yml      # ← from SwapCat Docker config
│   └── tencent/                # ← from Polymarket-Trading-Agents Tencent skeleton
└── openapi.json                # CI: FastAPI export → Mintlify sync
```

---

## 14. Existing Repo → Module Migration Map

| Existing Repo | Target Module | Reuse Level |
|---|---|---|
| `Polymarket-Trade-Infra` | `core/polymarket/` + `api/orders/` | Direct migration |
| `Polymarket-Trading-Agents` | `api/strategies/` + `api/portfolio/` + `core/risk_guard.py` | Logic reuse |
| `Polymarket-NBA-AI-Agent` | `data_pipeline/nba_collector.py` + `api/data/nba/` + `consumers/telegram_bot/` | Data + bot layer reuse |
| `Polymarket-Sports-Data` | `data_pipeline/sports_collector.py` + `api/data/sports/` | Direct migration |
| `Polymind-AI` | `api/analysis/` | AI analysis layer reuse |
| `Polymarket-BTC-UpDown-MultiTimeframe-Trade-Scraper` | `data_pipeline/btc_collector.py` + `api/data/btc/` | Direct migration |
| `Real-Time-Scraping-Of-Polymarket-Events` | `api/markets/` real-time layer | Direct migration |

---

## 15. Differentiation Summary

| User Type | Why They Come Here vs Direct Polymarket |
|---|---|
| **Retail (Telegram)** | Chinese-friendly UI, AI analysis, one-click convergence trading, no need to understand on-chain ops |
| **Developers** | NBA×Polymarket fusion endpoint, weather forecast×temperature market bias, 145-sport historical order books, AI bias scanner, Maker 0% Broker fee — none available via Polymarket directly |
| **Quant traders** | Pre-built strategy API (convergence, TWAP), real-time WebSocket with ms-level BTC on-chain data, simultaneous signal delivery guarantee |
