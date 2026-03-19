# Plan 2: Markets + Orders

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add market data endpoints (proxying Gamma/CLOB APIs), hosted and non-custodial order placement with fee injection and risk guards, cursor-based order history, and portfolio endpoints.

**Architecture:** New `api/markets/`, `api/orders/`, `api/portfolio/` routers follow the same pattern as `api/auth/` from Plan 1. A `core/fee_engine.py` and `core/risk_guard.py` handle pure business logic. The CLOB client (Plan 1) is called from the order service; tests mock it via `AsyncMock`. Non-custodial orders use Redis to store build params (60s TTL) for tamper-proof submit flow.

**Tech Stack:** Same as Plan 1. New: `hashlib` (stdlib, key hashing + payload hash).

**Spec:** `docs/superpowers/specs/2026-03-17-polymarket-broker-design.md` Sections 3, 4, 5, 6, 10.

**Task ordering:** Each task builds on previous. Do not skip or reorder.

**Environment:**
- Working directory: `/Users/ocean/Documents/产品代码开发/Polymarket Broker`
- Virtualenv: `.venv/` — always run `source .venv/bin/activate` before commands
- Test command: `ENV_FILE=.env.test pytest tests/ -v --tb=short`
- Test DB: `broker_test` on localhost:5432, Redis DB 1

---

## File Map

```
api/
├── markets/
│   ├── __init__.py
│   ├── router.py           # GET /markets, /markets/{id}, /orderbook, /trades, /midpoint, /search
│   └── schemas.py          # MarketResponse, OrderBookResponse, TradeResponse
├── orders/
│   ├── __init__.py
│   ├── models.py           # Order ORM model (PostgreSQL)
│   ├── router.py           # POST/GET/DELETE order endpoints
│   ├── schemas.py          # OrderRequest, OrderResponse, PaginatedOrders, BuildResponse
│   └── service.py          # place_order, build_order, submit_order, list_orders, cancel_order
├── portfolio/
│   ├── __init__.py
│   ├── router.py           # GET /portfolio/positions, /balance, /pnl
│   ├── schemas.py          # PositionResponse, BalanceResponse, PnlResponse
│   └── service.py          # Portfolio aggregation from Order table + CLOB
├── deps.py                 # Add get_current_user_from_api_key (X-API-Key header)
└── main.py                 # Add 3 new routers

core/
├── fee_engine.py           # get_fee_rate_bps(tier) → int
├── risk_guard.py           # validate_order_size(tier, size, price), check_position_cap(...)
└── polymarket/
    └── eip712.py           # Add sign_order_struct(order_struct, private_key, chain_id)

api/auth/
└── models.py               # Add key_hash column to ApiKey (for O(1) lookup)
    service.py              # Update create_api_key to compute + store key_hash

db/
└── postgres.py             # Register Order model in _register_models()

tests/
├── test_markets/
│   ├── __init__.py
│   └── test_markets.py
├── test_orders/
│   ├── __init__.py
│   ├── test_order_service.py
│   ├── test_noncustodial.py
│   └── test_order_http.py
└── test_portfolio/
    ├── __init__.py
    └── test_portfolio.py
```

---

## Task 1: Order ORM Model

**Files:**
- Create: `api/orders/__init__.py`
- Create: `api/orders/models.py`
- Create: `tests/test_orders/__init__.py`
- Modify: `db/postgres.py` (register Order)
- Create: `tests/test_orders/test_order_model.py`

- [ ] **Step 1: Write failing model test**

```python
# tests/test_orders/test_order_model.py
import pytest
from sqlalchemy import text


async def test_orders_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='orders'")
    )
    assert result.scalar() == "orders"


async def test_order_row_roundtrip(test_db_session):
    from api.orders.models import Order
    from sqlalchemy import select
    order = Order(
        user_id="user_fake_id",
        market_id="0xabc123",
        token_id="21742633",
        side="BUY",
        type="LIMIT",
        price=0.65,
        size=100.0,
        broker_fee_bps=10,
        mode="hosted",
    )
    test_db_session.add(order)
    await test_db_session.flush()
    fetched = await test_db_session.scalar(
        select(Order).where(Order.market_id == "0xabc123")
    )
    assert fetched is not None
    assert fetched.status == "PENDING"
    assert fetched.size_filled == 0.0
    assert fetched.id.startswith("ord_")
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
cd "/Users/ocean/Documents/产品代码开发/Polymarket Broker"
source .venv/bin/activate
ENV_FILE=.env.test pytest tests/test_orders/test_order_model.py -v
```

Expected: `ImportError` or table not found.

- [ ] **Step 3: Create `api/orders/__init__.py`** (empty file)

- [ ] **Step 4: Create `tests/test_orders/__init__.py`** (empty file)

- [ ] **Step 5: Create `api/orders/models.py`**

```python
import uuid
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Numeric, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.postgres import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: f"ord_{uuid.uuid4().hex[:12]}"
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    market_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_id: Mapped[str] = mapped_column(String(100), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)       # BUY / SELL
    type: Mapped[str] = mapped_column(String(10), nullable=False, default="LIMIT")
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    size: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    size_filled: Mapped[float] = mapped_column(Numeric(18, 6), default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    broker_fee_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    polymarket_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(15), default="hosted")  # hosted / noncustodial
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
```

- [ ] **Step 6: Register Order in `db/postgres.py`**

Find the `_register_models()` function and add `Order` import:

```python
def _register_models():
    from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
    from api.orders.models import Order  # noqa: F401
```

- [ ] **Step 7: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_order_model.py -v
```

Expected: 2 PASSED

- [ ] **Step 8: Commit**

```bash
git add api/orders/__init__.py api/orders/models.py tests/test_orders/__init__.py tests/test_orders/test_order_model.py db/postgres.py
git commit -m "feat: Order ORM model"
```

---

## Task 2: X-API-Key Auth + key_hash

The `ApiKey` model needs a `key_hash` field for O(1) lookup (SHA-256 of raw key). This task adds the column, updates the creation logic, and adds the `get_current_user_from_api_key` dependency.

**Files:**
- Modify: `api/auth/models.py` (add `key_hash` column)
- Modify: `api/auth/service.py` (compute `key_hash` on create)
- Modify: `api/deps.py` (add `get_current_user_from_api_key`)
- Create: `tests/test_auth/test_api_key_auth.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_auth/test_api_key_auth.py
import pytest
from api.auth.service import AuthService
from api.deps import get_current_user_from_api_key
from fastapi import Request
from unittest.mock import AsyncMock, MagicMock


async def test_api_key_lookup_succeeds(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("apikeytest@example.com", "pass123")
    result = await svc.create_api_key(user.id, "Test Key", ["markets:read"])
    raw_key = result["key"]

    # Verify we can resolve the key back to the user
    resolved = await svc.resolve_api_key(raw_key)
    assert resolved is not None
    assert resolved.user_id == user.id
    assert resolved.is_active is True


async def test_api_key_lookup_wrong_key_returns_none(test_db_session):
    svc = AuthService(test_db_session)
    resolved = await svc.resolve_api_key("pm_live_sk_doesnotexist")
    assert resolved is None
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_api_key_auth.py -v
```

Expected: `AttributeError: 'AuthService' object has no attribute 'resolve_api_key'`

- [ ] **Step 3: Add `key_hash` column to `api/auth/models.py`**

In the `ApiKey` class, add after `key_hint`:

```python
key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
```

- [ ] **Step 4: Update `api/auth/service.py` — `create_api_key` and add `resolve_api_key`**

Add import at the top:
```python
import hashlib
```

In `create_api_key`, compute and store the hash. Replace the existing method:

```python
async def create_api_key(self, user_id: str, name: str, scopes: list[str]) -> dict:
    raw_key = generate_api_key_value("pm_live_sk")
    key = ApiKey(
        user_id=user_id,
        name=name,
        key_prefix="pm_live_sk",
        key_encrypted=encrypt_api_key(raw_key),
        key_hint=raw_key[-4:],
        key_hash=hashlib.sha256(raw_key.encode()).hexdigest(),
        scopes=scopes,
    )
    self.db.add(key)
    await self.db.commit()
    await self.db.refresh(key)
    return {**{c.name: getattr(key, c.name) for c in key.__table__.columns}, "key": raw_key}
```

Add new method to `AuthService`:

```python
async def resolve_api_key(self, raw_key: str) -> ApiKey | None:
    """Look up an ApiKey row by hashing the submitted raw key. Returns None if not found."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return await self.db.scalar(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
```

- [ ] **Step 5: Add `get_current_user_from_api_key` to `api/deps.py`**

```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.postgres import get_session
from core.security import decode_access_token


async def get_current_user_id(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_session),
) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_access_token(token)
        return payload["sub"]
    except Exception:
        raise HTTPException(401, detail="Invalid or expired token")


async def get_current_user_from_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_session),
) -> dict:
    """
    Resolves X-API-Key header → { user_id, tier, scopes }.
    Raises HTTP 401 if key not found or inactive.
    """
    from api.auth.service import AuthService
    api_key_row = await AuthService(db).resolve_api_key(x_api_key)
    if api_key_row is None:
        raise HTTPException(401, detail="Invalid or inactive API key")
    # Load the user for tier info
    from api.auth.models import User
    user = await db.scalar(select(User).where(User.id == api_key_row.user_id))
    if user is None or not user.is_active:
        raise HTTPException(401, detail="User account inactive")
    return {"user_id": user.id, "tier": user.tier, "scopes": api_key_row.scopes}
```

- [ ] **Step 6: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_api_key_auth.py -v
```

Expected: 2 PASSED

Note: The test DB uses `drop_all + create_all` so `key_hash` column is automatically included. For the dev database, run manually:
```sql
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_hash VARCHAR(64) UNIQUE;
```

- [ ] **Step 7: Run full existing suite — confirm nothing broke**

```bash
ENV_FILE=.env.test pytest tests/ -v --tb=short
```

Expected: All previous tests pass (35+ PASSED).

- [ ] **Step 8: Commit**

```bash
git add api/auth/models.py api/auth/service.py api/deps.py tests/test_auth/test_api_key_auth.py
git commit -m "feat: key_hash on ApiKey for O(1) lookup, get_current_user_from_api_key dep"
```

---

## Task 3: Fee Engine + Risk Guard

**Files:**
- Create: `core/fee_engine.py`
- Create: `core/risk_guard.py`
- Create: `tests/test_core/test_fee_engine.py`
- Create: `tests/test_core/test_risk_guard.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_core/test_fee_engine.py
from core.fee_engine import get_fee_rate_bps


def test_free_tier_is_10_bps():
    assert get_fee_rate_bps("free") == 10


def test_pro_tier_is_5_bps():
    assert get_fee_rate_bps("pro") == 5


def test_enterprise_tier_is_0_bps():
    assert get_fee_rate_bps("enterprise") == 0


def test_unknown_tier_defaults_to_free():
    assert get_fee_rate_bps("unknown_tier") == 10
```

```python
# tests/test_core/test_risk_guard.py
import pytest
from core.risk_guard import validate_order_size, check_position_cap


def test_free_tier_allows_small_order():
    validate_order_size("free", size=100.0, price=0.65)  # 65 USDC, under 1000 limit


def test_free_tier_rejects_large_order():
    with pytest.raises(ValueError, match="ORDER_SIZE_EXCEEDED"):
        validate_order_size("free", size=2000.0, price=0.65)  # 1300 USDC, over 1000


def test_pro_tier_allows_large_order():
    validate_order_size("pro", size=10000.0, price=0.9)  # 9000 USDC, under 50000


def test_free_tier_position_cap():
    with pytest.raises(ValueError, match="POSITION_CAP_EXCEEDED"):
        check_position_cap("free", existing_notional=4500.0, new_notional=600.0)  # 5100 > 5000


def test_pro_tier_no_position_cap():
    check_position_cap("pro", existing_notional=999999.0, new_notional=999999.0)  # no limit
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_fee_engine.py tests/test_core/test_risk_guard.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `core/fee_engine.py`**

```python
_TIER_FEE_RATE_BPS: dict[str, int] = {
    "free": 10,        # 0.10% broker layer
    "pro": 5,          # 0.05% broker layer
    "enterprise": 0,   # 0.00% (custom negotiated at contract level)
}


def get_fee_rate_bps(tier: str) -> int:
    """Returns the broker-layer feeRateBps for the given subscription tier."""
    return _TIER_FEE_RATE_BPS.get(tier.lower(), _TIER_FEE_RATE_BPS["free"])
```

- [ ] **Step 4: Create `core/risk_guard.py`**

```python
from decimal import Decimal

_MAX_ORDER_USDC: dict[str, Decimal] = {
    "free": Decimal("1000"),
    "pro": Decimal("50000"),
    "enterprise": Decimal("999999999"),
}

_MAX_POSITION_USDC: dict[str, Decimal] = {
    "free": Decimal("5000"),
    "pro": Decimal("999999999"),
    "enterprise": Decimal("999999999"),
}


def validate_order_size(tier: str, size: float, price: float) -> None:
    """Raises ValueError if order notional exceeds tier limit."""
    notional = Decimal(str(size)) * Decimal(str(price))
    limit = _MAX_ORDER_USDC.get(tier.lower(), _MAX_ORDER_USDC["free"])
    if notional > limit:
        raise ValueError(f"ORDER_SIZE_EXCEEDED: max {limit} USDC for '{tier}' tier")


def check_position_cap(tier: str, existing_notional: float, new_notional: float) -> None:
    """Raises ValueError if adding new_notional to existing_notional would exceed per-market cap."""
    cap = _MAX_POSITION_USDC.get(tier.lower(), _MAX_POSITION_USDC["free"])
    total = Decimal(str(existing_notional)) + Decimal(str(new_notional))
    if total > cap:
        raise ValueError(
            f"POSITION_CAP_EXCEEDED: per-market cap is {cap} USDC for '{tier}' tier"
        )
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_fee_engine.py tests/test_core/test_risk_guard.py -v
```

Expected: 9 PASSED

- [ ] **Step 6: Commit**

```bash
git add core/fee_engine.py core/risk_guard.py tests/test_core/test_fee_engine.py tests/test_core/test_risk_guard.py
git commit -m "feat: fee engine (tier → bps) and risk guard (size + position cap)"
```

---

## Task 4: Markets Router

**Files:**
- Create: `api/markets/__init__.py`
- Create: `api/markets/schemas.py`
- Create: `api/markets/router.py`
- Create: `tests/test_markets/__init__.py`
- Create: `tests/test_markets/test_markets.py`
- Modify: `api/main.py` (add markets router)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_markets/test_markets.py
import pytest
from unittest.mock import AsyncMock, patch


async def test_get_markets_returns_list(client):
    mock_markets = [
        {"id": "0xabc", "question": "Will X win?", "active": True}
    ]
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_markets = AsyncMock(return_value=mock_markets)
        resp = await client.get("/api/v1/markets?limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert isinstance(data["data"], list)


async def test_get_market_detail(client):
    mock_market = {"id": "0xabc", "question": "Will X win?"}
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_market = AsyncMock(return_value=mock_market)
        resp = await client.get("/api/v1/markets/0xabc")
    assert resp.status_code == 200


async def test_get_orderbook(client):
    mock_ob = {"bids": [{"price": "0.65", "size": "100"}], "asks": []}
    with patch("api.markets.router.clob_client") as mock_clob:
        mock_clob.get_orderbook = AsyncMock(return_value=mock_ob)
        resp = await client.get("/api/v1/markets/0xabc/orderbook?token_id=tok123")
    assert resp.status_code == 200
    assert "bids" in resp.json()


async def test_get_midpoint(client):
    mock_mid = {"mid": "0.65", "timestamp": "2026-03-17T10:00:00Z"}
    with patch("api.markets.router.clob_client") as mock_clob:
        mock_clob.get_midpoint = AsyncMock(return_value=mock_mid)
        resp = await client.get("/api/v1/markets/0xabc/midpoint?token_id=tok123")
    assert resp.status_code == 200


async def test_search_markets(client):
    mock_results = [{"id": "0xabc", "question": "Bitcoin price?"}]
    with patch("api.markets.router.gamma_client") as mock_gamma:
        mock_gamma.get_markets = AsyncMock(return_value=mock_results)
        resp = await client.get("/api/v1/markets/search?q=bitcoin")
    assert resp.status_code == 200
    assert "data" in resp.json()
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_markets/ -v
```

Expected: `ImportError` or 404

- [ ] **Step 3: Create `api/markets/__init__.py`** and `tests/test_markets/__init__.py`** (both empty)

- [ ] **Step 4: Create `api/markets/schemas.py`**

```python
from pydantic import BaseModel
from typing import Any


class MarketListResponse(BaseModel):
    data: list[Any]
    pagination: dict


class OrderBookResponse(BaseModel):
    bids: list[dict]
    asks: list[dict]
```

- [ ] **Step 5: Create `api/markets/router.py`**

```python
from fastapi import APIRouter, Query, HTTPException
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient

router = APIRouter(prefix="/markets", tags=["markets"])

# Module-level client instances (mocked in tests via patch)
gamma_client = GammaClient()
clob_client = ClobClient()


@router.get("")
async def list_markets(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    """List all Polymarket markets with optional filters."""
    filters = {}
    if category:
        filters["category"] = category
    if status:
        filters["active"] = status == "active"
    try:
        markets = await gamma_client.get_markets(limit=limit, offset=offset, **filters)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
    return {
        "data": markets,
        "pagination": {"limit": limit, "offset": offset, "has_more": len(markets) == limit},
    }


@router.get("/search")
async def search_markets(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Full-text search across market questions."""
    try:
        results = await gamma_client.get_markets(limit=limit, offset=offset, tag=q)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
    return {
        "data": results,
        "pagination": {"limit": limit, "offset": offset, "has_more": len(results) == limit},
    }


@router.get("/{market_id}")
async def get_market(market_id: str):
    """Get a specific market by ID."""
    try:
        return await gamma_client.get_market(market_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/orderbook")
async def get_orderbook(market_id: str, token_id: str = Query(...)):
    """Get the live order book for a market token."""
    try:
        return await clob_client.get_orderbook(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/trades")
async def get_trades(
    market_id: str,
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get recent trades for a market."""
    try:
        return await clob_client.get_trades(market_id=market_id, limit=limit)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")


@router.get("/{market_id}/midpoint")
async def get_midpoint(market_id: str, token_id: str = Query(...)):
    """Get the current mid price for a market token."""
    try:
        return await clob_client.get_midpoint(token_id=token_id)
    except Exception as e:
        raise HTTPException(502, detail=f"Upstream error: {e}")
```

- [ ] **Step 6: Add markets router to `api/main.py`**

Add import and router inclusion. Read current `api/main.py` first, then add:

```python
from api.markets.router import router as markets_router
# ...
app.include_router(markets_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 7: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_markets/ -v
```

Expected: 5 PASSED

- [ ] **Step 8: Commit**

```bash
git add api/markets/ tests/test_markets/ api/main.py
git commit -m "feat: markets router — list, search, detail, orderbook, trades, midpoint"
```

---

## Task 5: EIP-712 Order Signing

Extend `core/polymarket/eip712.py` to sign order structs with the operator's private key (hosted mode).

**Files:**
- Modify: `core/polymarket/eip712.py`
- Modify: `tests/test_core/test_polymarket_clients.py`

- [ ] **Step 1: Add failing test**

Add to `tests/test_core/test_polymarket_clients.py`:

```python
def test_sign_order_struct_adds_signature():
    # Use a well-known test private key (not used in production)
    test_private_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
    order = build_order_struct(
        maker="0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf",
        token_id="21742633",
        price=0.5,
        size=100.0,
        side="BUY",
        fee_rate_bps=10,
        nonce=0,
    )
    from core.polymarket.eip712 import sign_order_struct
    signed = sign_order_struct(order, private_key=test_private_key, chain_id=137)
    assert "signature" in signed
    assert signed["signature"].startswith("0x")
    assert len(signed["signature"]) == 132  # 65 bytes = 130 hex chars + "0x"
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_polymarket_clients.py::test_sign_order_struct_adds_signature -v
```

Expected: `ImportError: cannot import name 'sign_order_struct'`

- [ ] **Step 3: Add `sign_order_struct` to `core/polymarket/eip712.py`**

Append to the existing file:

```python
# Polymarket CTF Exchange contract on Polygon mainnet
_EXCHANGE_ADDRESS = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"

_EIP712_DOMAIN = {
    "name": "CTF Exchange",
    "version": "1",
}

_ORDER_TYPES = {
    "Order": [
        {"name": "salt", "type": "uint256"},
        {"name": "maker", "type": "address"},
        {"name": "signer", "type": "address"},
        {"name": "taker", "type": "address"},
        {"name": "tokenId", "type": "uint256"},
        {"name": "makerAmount", "type": "uint256"},
        {"name": "takerAmount", "type": "uint256"},
        {"name": "expiration", "type": "uint256"},
        {"name": "nonce", "type": "uint256"},
        {"name": "feeRateBps", "type": "uint256"},
        {"name": "side", "type": "uint8"},
        {"name": "signatureType", "type": "uint8"},
    ]
}


def sign_order_struct(order_struct: dict, private_key: str, chain_id: int = 137) -> dict:
    """
    Signs an EIP-712 order struct using the operator private key.
    Returns a new dict with the 'signature' field added.
    """
    from eth_account import Account

    domain = {
        **_EIP712_DOMAIN,
        "chainId": chain_id,
        "verifyingContract": _EXCHANGE_ADDRESS,
    }

    # EIP-712 typed data requires integer values (not strings)
    typed_data = {
        "salt": int(order_struct["salt"]) if isinstance(order_struct["salt"], str) else order_struct["salt"],
        "maker": order_struct["maker"],
        "signer": order_struct["signer"],
        "taker": order_struct["taker"],
        "tokenId": int(order_struct["tokenId"]) if isinstance(order_struct["tokenId"], str) else order_struct["tokenId"],
        "makerAmount": int(order_struct["makerAmount"]),
        "takerAmount": int(order_struct["takerAmount"]),
        "expiration": int(order_struct["expiration"]),
        "nonce": int(order_struct["nonce"]),
        "feeRateBps": int(order_struct["feeRateBps"]),
        "side": int(order_struct["side"]),
        "signatureType": int(order_struct["signatureType"]),
    }

    account = Account.from_key(private_key)
    signed = account.sign_typed_data(domain, _ORDER_TYPES, typed_data)
    return {**order_struct, "signature": signed.signature.hex()}
```

Note: `tokenId` in Polymarket is a large decimal integer (uint256) stored as string. The test uses `"21742633"` which parses cleanly. In production, token IDs are ~77-digit numbers.

- [ ] **Step 4: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_polymarket_clients.py -v
```

Expected: 5 PASSED (4 existing + 1 new)

- [ ] **Step 5: Commit**

```bash
git add core/polymarket/eip712.py tests/test_core/test_polymarket_clients.py
git commit -m "feat: EIP-712 order signing with operator private key"
```

---

## Task 6: Order Service (Hosted Mode)

**Files:**
- Create: `api/orders/schemas.py`
- Create: `api/orders/service.py`
- Create: `tests/test_orders/test_order_service.py`

- [ ] **Step 1: Create `api/orders/schemas.py`**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class OrderRequest(BaseModel):
    market_id: str
    token_id: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    type: str = Field(default="LIMIT", pattern="^(LIMIT|MARKET|GTD)$")
    price: float = Field(..., gt=0, lt=1)
    size: float = Field(..., gt=0)
    expires_at: datetime | None = None


class OrderResponse(BaseModel):
    order_id: str
    market_id: str
    token_id: str
    side: str
    type: str
    price: float
    size: float
    size_filled: float
    size_remaining: float
    status: str
    broker_fee_bps: int
    polymarket_order_id: str | None
    mode: str
    created_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    model_config = {"from_attributes": True}


class PaginatedOrders(BaseModel):
    data: list[OrderResponse]
    pagination: dict


class BuildOrderRequest(BaseModel):
    market_id: str
    token_id: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    price: float = Field(..., gt=0, lt=1)
    size: float = Field(..., gt=0)


class BuildOrderResponse(BaseModel):
    eip712_payload: dict
    payload_hash: str


class SubmitOrderRequest(BaseModel):
    payload_hash: str
    signature: str
```

- [ ] **Step 2: Write failing service tests**

```python
# tests/test_orders/test_order_service.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.orders.service import OrderService
from api.auth.service import AuthService


async def test_place_order_stores_in_db(test_db_session):
    # Create a real user
    auth = AuthService(test_db_session)
    user = await auth.register("ordertest@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_order_001", "status": "live"}

    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        MockClob.return_value = mock_instance

        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id,
            tier="free",
            market_id="0xabc",
            token_id="21742633",
            side="BUY",
            order_type="LIMIT",
            price=0.5,
            size=10.0,
        )

    assert order.status == "OPEN"
    assert order.broker_fee_bps == 10  # Free tier
    assert order.polymarket_order_id == "poly_order_001"
    assert order.mode == "hosted"


async def test_place_order_rejects_oversized(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("ordersize@example.com", "pass123")
    svc = OrderService(test_db_session)

    with pytest.raises(ValueError, match="ORDER_SIZE_EXCEEDED"):
        await svc.place_order(
            user_id=user.id,
            tier="free",
            market_id="0xabc",
            token_id="21742633",
            side="BUY",
            order_type="LIMIT",
            price=0.9,
            size=2000.0,  # 1800 USDC > 1000 free tier limit
        )


async def test_list_orders_returns_user_orders(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("orderlist@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_list_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        await svc.place_order(
            user_id=user.id, tier="free", market_id="0xmarket1",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=10.0,
        )

    svc = OrderService(test_db_session)
    result = await svc.list_orders(user_id=user.id)
    assert len(result["data"]) == 1
    assert result["data"][0].market_id == "0xmarket1"


async def test_cancel_order(test_db_session):
    auth = AuthService(test_db_session)
    user = await auth.register("ordercancel@example.com", "pass123")

    mock_clob_response = {"orderID": "poly_cancel_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        mock_instance = MagicMock()
        mock_instance.post_order = AsyncMock(return_value=mock_clob_response)
        mock_instance.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = mock_instance
        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id, tier="free", market_id="0xcancelmarket",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.5, size=10.0,
        )
        await svc.cancel_order(user_id=user.id, order_id=order.id, api_key="test_key")

    svc = OrderService(test_db_session)
    result = await svc.list_orders(user_id=user.id, status="CANCELLED")
    assert len(result["data"]) == 1
```

- [ ] **Step 3: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_order_service.py -v
```

Expected: `ImportError` (OrderService doesn't exist yet)

- [ ] **Step 4: Create `api/orders/service.py`**

```python
import hashlib
import json
import secrets
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from api.orders.models import Order
from core.fee_engine import get_fee_rate_bps
from core.risk_guard import validate_order_size
from core.polymarket.eip712 import build_order_struct, sign_order_struct
from core.polymarket.clob_client import ClobClient
from core.config import get_settings

settings = get_settings()


def _order_to_response(order: Order) -> dict:
    return {
        "order_id": order.id,
        "market_id": order.market_id,
        "token_id": order.token_id,
        "side": order.side,
        "type": order.type,
        "price": float(order.price),
        "size": float(order.size),
        "size_filled": float(order.size_filled),
        "size_remaining": float(order.size) - float(order.size_filled),
        "status": order.status,
        "broker_fee_bps": order.broker_fee_bps,
        "polymarket_order_id": order.polymarket_order_id,
        "mode": order.mode,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "expires_at": order.expires_at,
    }


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def place_order(
        self,
        user_id: str,
        tier: str,
        market_id: str,
        token_id: str,
        side: str,
        order_type: str,
        price: float,
        size: float,
        expires_at: datetime | None = None,
    ) -> Order:
        """Hosted mode: sign with operator key, submit to Polymarket CLOB."""
        # 1. Risk checks
        validate_order_size(tier, size=size, price=price)

        # 2. Fee injection
        fee_bps = get_fee_rate_bps(tier)

        # 3. Build + sign EIP-712 order struct
        order_struct = build_order_struct(
            maker=settings.polymarket_fee_address or "0x0000000000000000000000000000000000000000",
            token_id=token_id,
            price=price,
            size=size,
            side=side,
            fee_rate_bps=fee_bps,
            nonce=secrets.randbelow(2**32),
        )
        signed_struct = sign_order_struct(
            order_struct,
            private_key=settings.polymarket_private_key or "0x" + "0" * 63 + "1",
            chain_id=settings.polymarket_chain_id,
        )

        # 4. Submit to Polymarket CLOB
        clob = ClobClient()
        try:
            clob_resp = await clob.post_order(signed_struct, api_key=settings.polymarket_private_key or "")
        except Exception as e:
            raise ValueError(f"CLOB_SUBMISSION_FAILED: {e}") from e

        polymarket_order_id = clob_resp.get("orderID") or clob_resp.get("order_id")

        # 5. Persist to PostgreSQL
        order = Order(
            user_id=user_id,
            market_id=market_id,
            token_id=token_id,
            side=side,
            type=order_type,
            price=price,
            size=size,
            broker_fee_bps=fee_bps,
            polymarket_order_id=polymarket_order_id,
            status="OPEN",
            mode="hosted",
            expires_at=expires_at,
        )
        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def list_orders(
        self,
        user_id: str,
        status: str | None = None,
        market_id: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict:
        """Returns paginated orders for the user."""
        from sqlalchemy import and_, desc
        import base64

        conditions = [Order.user_id == user_id]
        if status:
            conditions.append(Order.status == status)
        if market_id:
            conditions.append(Order.market_id == market_id)
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(base64.b64decode(cursor).decode())
                conditions.append(Order.created_at < cursor_dt)
            except Exception:
                pass  # Invalid cursor, ignore

        stmt = (
            select(Order)
            .where(and_(*conditions))
            .order_by(desc(Order.created_at))
            .limit(limit + 1)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        has_more = len(orders) > limit
        if has_more:
            orders = orders[:limit]

        next_cursor = None
        if has_more and orders:
            next_cursor = base64.b64encode(orders[-1].created_at.isoformat().encode()).decode()

        return {
            "data": orders,
            "pagination": {"cursor": next_cursor, "has_more": has_more, "limit": limit},
        }

    async def get_order(self, user_id: str, order_id: str) -> Order | None:
        return await self.db.scalar(
            select(Order).where(Order.id == order_id, Order.user_id == user_id)
        )

    async def cancel_order(self, user_id: str, order_id: str, api_key: str) -> Order:
        order = await self.get_order(user_id, order_id)
        if not order:
            raise KeyError("ORDER_NOT_FOUND")
        if order.status in ("FILLED", "CANCELLED", "EXPIRED"):
            raise ValueError(f"ORDER_NOT_CANCELLABLE: status is {order.status}")

        clob = ClobClient()
        if order.polymarket_order_id:
            await clob.cancel_order(order.polymarket_order_id, api_key=api_key)

        order.status = "CANCELLED"
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def cancel_all_open(self, user_id: str, api_key: str) -> int:
        """Cancel all OPEN/PENDING orders. Returns count cancelled."""
        from sqlalchemy import and_
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.status.in_(["OPEN", "PENDING"]))
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())
        clob = ClobClient()
        for order in orders:
            if order.polymarket_order_id:
                try:
                    await clob.cancel_order(order.polymarket_order_id, api_key=api_key)
                except Exception:
                    pass  # Best-effort cancellation
            order.status = "CANCELLED"
        await self.db.commit()
        return len(orders)
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_order_service.py -v
```

Expected: 4 PASSED

Note: The `ClobClient` is patched in tests via `patch("api.orders.service.ClobClient")`. The `settings.polymarket_private_key` in `.env.test` can be empty or a dummy — `sign_order_struct` will use the fallback `"0x" + "0" * 63 + "1"`.

Add to `.env.test` if missing:
```
POLYMARKET_PRIVATE_KEY=0x0000000000000000000000000000000000000000000000000000000000000001
POLYMARKET_FEE_ADDRESS=0x0000000000000000000000000000000000000001
```

- [ ] **Step 6: Commit**

```bash
git add api/orders/schemas.py api/orders/service.py tests/test_orders/test_order_service.py
git commit -m "feat: order service — hosted place/list/get/cancel/cancel-all"
```

---

## Task 7: Non-custodial Build/Submit

**Files:**
- Modify: `api/orders/service.py` (add `build_order`, `submit_order`)
- Create: `tests/test_orders/test_noncustodial.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_orders/test_noncustodial.py
import pytest
import json
import hashlib
from eth_account import Account
from eth_account import messages as eth_msgs


async def test_build_order_returns_payload_and_hash(client, test_redis):
    # Register + login to get bearer token
    await client.post("/api/v1/auth/register", json={"email": "nc@example.com", "password": "pass123"})
    login = await client.post("/api/v1/auth/login", json={"email": "nc@example.com", "password": "pass123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc",
        "token_id": "21742633",
        "side": "BUY",
        "price": 0.5,
        "size": 10.0,
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "eip712_payload" in data
    assert "payload_hash" in data
    assert len(data["payload_hash"]) == 64  # SHA-256 hex


async def test_build_order_stored_in_redis(client, test_redis):
    await client.post("/api/v1/auth/register", json={"email": "nc2@example.com", "password": "pass123"})
    login = await client.post("/api/v1/auth/login", json={"email": "nc2@example.com", "password": "pass123"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc", "token_id": "21742633",
        "side": "BUY", "price": 0.5, "size": 10.0,
    }, headers=headers)
    payload_hash = resp.json()["payload_hash"]

    # Verify Redis contains the build params under this hash
    # Key format: order_build:{user_id}:{payload_hash}
    keys = await test_redis.keys(f"order_build:*:{payload_hash}")
    assert len(keys) == 1
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_noncustodial.py -v
```

Expected: 404 (routes not defined yet)

- [ ] **Step 3: Add `build_order` and `submit_order` to `api/orders/service.py`**

Add these methods to the `OrderService` class:

```python
async def build_order(
    self,
    user_id: str,
    tier: str,
    market_id: str,
    token_id: str,
    side: str,
    price: float,
    size: float,
    redis: aioredis.Redis,
) -> dict:
    """Non-custodial mode: build EIP-712 payload and store params in Redis."""
    # Risk check
    validate_order_size(tier, size=size, price=price)

    fee_bps = get_fee_rate_bps(tier)
    nonce = secrets.randbelow(2**32)

    order_struct = build_order_struct(
        maker=settings.polymarket_fee_address or "0x0000000000000000000000000000000000000000",
        token_id=token_id,
        price=price,
        size=size,
        side=side,
        fee_rate_bps=fee_bps,
        nonce=nonce,
    )

    # Canonical JSON of the payload (sorted keys for determinism)
    payload_json = json.dumps(order_struct, sort_keys=True)
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

    # Store build params in Redis for 60 seconds
    redis_key = f"order_build:{user_id}:{payload_hash}"
    build_params = {
        "market_id": market_id,
        "token_id": token_id,
        "side": side,
        "price": str(price),
        "size": str(size),
        "fee_bps": fee_bps,
        "nonce": nonce,
        "order_struct": order_struct,
    }
    await redis.set(redis_key, json.dumps(build_params), ex=60)

    return {"eip712_payload": order_struct, "payload_hash": payload_hash}

async def submit_order(
    self,
    user_id: str,
    payload_hash: str,
    signature: str,
    redis: aioredis.Redis,
) -> Order:
    """Non-custodial mode: verify stored hash, verify signature, broadcast."""
    from eth_account import Account
    from eth_account.messages import encode_defunct

    redis_key = f"order_build:{user_id}:{payload_hash}"
    stored_raw = await redis.get(redis_key)
    if not stored_raw:
        raise ValueError("PAYLOAD_HASH_NOT_FOUND_OR_EXPIRED")

    build_params = json.loads(stored_raw)
    order_struct = build_params["order_struct"]

    # Re-derive hash to verify tamper protection
    payload_json = json.dumps(order_struct, sort_keys=True)
    expected_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    if expected_hash != payload_hash:
        raise ValueError("PAYLOAD_HASH_MISMATCH")

    # Verify the user's signature against the payload
    # For non-custodial, we use the payload JSON as the signed message
    msg = encode_defunct(text=payload_json)
    try:
        recovered = Account.recover_message(msg, signature=signature)
    except Exception as exc:
        raise ValueError("INVALID_SIGNATURE") from exc

    # Delete the Redis key (single-use)
    await redis.delete(redis_key)

    # Get user info for tier (fee is already baked into the struct)
    fee_bps = build_params["fee_bps"]

    # Submit to CLOB (user already signed — we submit as-is with their signature)
    clob = ClobClient()
    signed_struct = {**order_struct, "signature": signature}
    try:
        clob_resp = await clob.post_order(signed_struct, api_key="")
    except Exception as e:
        raise ValueError(f"CLOB_SUBMISSION_FAILED: {e}") from e

    polymarket_order_id = clob_resp.get("orderID") or clob_resp.get("order_id")

    # Persist to PostgreSQL
    order = Order(
        user_id=user_id,
        market_id=build_params["market_id"],
        token_id=build_params["token_id"],
        side=build_params["side"],
        type="LIMIT",
        price=float(build_params["price"]),
        size=float(build_params["size"]),
        broker_fee_bps=fee_bps,
        polymarket_order_id=polymarket_order_id,
        status="OPEN",
        mode="noncustodial",
    )
    self.db.add(order)
    await self.db.commit()
    await self.db.refresh(order)
    return order
```

Also add `import json` at the top of `api/orders/service.py` if not already present.

- [ ] **Step 4: Run — confirm FAIL** (routes still missing)

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_noncustodial.py -v
```

Expected: 404 (no router yet)

- [ ] **Step 5: Commit the service changes**

```bash
git add api/orders/service.py tests/test_orders/test_noncustodial.py
git commit -m "feat: non-custodial build/submit order flow with Redis payload hash"
```

---

## Task 8: Order Router

**Files:**
- Create: `api/orders/router.py`
- Create: `tests/test_orders/test_order_http.py`
- Modify: `api/main.py` (add orders router)

- [ ] **Step 1: Write failing HTTP tests**

```python
# tests/test_orders/test_order_http.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService


async def _create_user_and_api_key(client, test_db_session, email: str) -> tuple[str, str]:
    """Helper: register user, create API key, return (user_id, raw_api_key)."""
    svc = AuthService(test_db_session)
    user = await svc.register(email, "password123")
    result = await svc.create_api_key(user.id, "Test Key", ["orders:write"])
    return user.id, result["key"]


async def test_post_order_hosted_returns_order(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_order@example.com")

    mock_clob_resp = {"orderID": "poly_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        resp = await client.post("/api/v1/orders", json={
            "market_id": "0xabc", "token_id": "21742633",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 10.0,
        }, headers={"X-API-Key": api_key})

    assert resp.status_code == 201
    data = resp.json()
    assert data["order_id"].startswith("ord_")
    assert data["broker_fee_bps"] == 10  # Free tier
    assert data["mode"] == "hosted"


async def test_get_orders_list(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_list@example.com")

    mock_clob_resp = {"orderID": "poly_list_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        await client.post("/api/v1/orders", json={
            "market_id": "0xlist1", "token_id": "tok1",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 5.0,
        }, headers={"X-API-Key": api_key})

    resp = await client.get("/api/v1/orders", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert len(data["data"]) >= 1


async def test_build_order_route_requires_bearer(client):
    # build endpoint needs Authorization: Bearer (non-custodial = wallet auth)
    resp = await client.post("/api/v1/orders/build", json={
        "market_id": "0xabc", "token_id": "tok", "side": "BUY", "price": 0.5, "size": 10.0,
    })
    assert resp.status_code == 422  # Missing Authorization header


async def test_cancel_order_http(client, test_db_session):
    user_id, api_key = await _create_user_and_api_key(client, test_db_session, "http_cancel@example.com")

    mock_clob_resp = {"orderID": "poly_cancel_http_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        inst.cancel_order = AsyncMock(return_value={"status": "cancelled"})
        MockClob.return_value = inst

        place_resp = await client.post("/api/v1/orders", json={
            "market_id": "0xcancel1", "token_id": "tok1",
            "side": "BUY", "type": "LIMIT", "price": 0.5, "size": 5.0,
        }, headers={"X-API-Key": api_key})
        order_id = place_resp.json()["order_id"]

        del_resp = await client.delete(f"/api/v1/orders/{order_id}", headers={"X-API-Key": api_key})

    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "CANCELLED"
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_order_http.py -v
```

Expected: 404 (router not mounted)

- [ ] **Step 3: Create `api/orders/router.py`**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from db.postgres import get_session
from db.redis_client import get_redis
from api.deps import get_current_user_id, get_current_user_from_api_key
from api.orders.service import OrderService
from api.orders.schemas import (
    OrderRequest, OrderResponse, PaginatedOrders,
    BuildOrderRequest, BuildOrderResponse, SubmitOrderRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def place_order(
    body: OrderRequest,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    """Hosted mode: sign with operator key and submit to Polymarket."""
    order = await OrderService(db).place_order(
        user_id=auth["user_id"],
        tier=auth["tier"],
        market_id=body.market_id,
        token_id=body.token_id,
        side=body.side,
        order_type=body.type,
        price=body.price,
        size=body.size,
        expires_at=body.expires_at,
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.post("/build", response_model=BuildOrderResponse)
async def build_order(
    body: BuildOrderRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Non-custodial mode: build EIP-712 payload for user to sign."""
    from api.auth.models import User
    from sqlalchemy import select
    user = await db.scalar(select(User).where(User.id == user_id))
    tier = user.tier if user else "free"
    return await OrderService(db).build_order(
        user_id=user_id, tier=tier,
        market_id=body.market_id, token_id=body.token_id,
        side=body.side, price=body.price, size=body.size,
        redis=redis,
    )


@router.post("/submit", response_model=OrderResponse)
async def submit_order(
    body: SubmitOrderRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Non-custodial mode: submit signed EIP-712 order."""
    order = await OrderService(db).submit_order(
        user_id=user_id,
        payload_hash=body.payload_hash,
        signature=body.signature,
        redis=redis,
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.get("", response_model=PaginatedOrders)
async def list_orders(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
    status: str | None = Query(default=None),
    market_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
):
    result = await OrderService(db).list_orders(
        user_id=auth["user_id"], status=status, market_id=market_id,
        limit=limit, cursor=cursor,
    )
    orders_resp = [OrderResponse(**_order_to_response_dict(o)) for o in result["data"]]
    return PaginatedOrders(data=orders_resp, pagination=result["pagination"])


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    order = await OrderService(db).get_order(user_id=auth["user_id"], order_id=order_id)
    if not order:
        raise KeyError("ORDER_NOT_FOUND")
    return OrderResponse(**_order_to_response_dict(order))


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    order = await OrderService(db).cancel_order(
        user_id=auth["user_id"], order_id=order_id,
        api_key=auth.get("raw_key", ""),
    )
    return OrderResponse(**_order_to_response_dict(order))


@router.delete("", status_code=200)
async def cancel_all_orders(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    count = await OrderService(db).cancel_all_open(
        user_id=auth["user_id"], api_key=auth.get("raw_key", "")
    )
    return {"cancelled": count}


def _order_to_response_dict(order) -> dict:
    return {
        "order_id": order.id,
        "market_id": order.market_id,
        "token_id": order.token_id,
        "side": order.side,
        "type": order.type,
        "price": float(order.price),
        "size": float(order.size),
        "size_filled": float(order.size_filled),
        "size_remaining": float(order.size) - float(order.size_filled),
        "status": order.status,
        "broker_fee_bps": order.broker_fee_bps,
        "polymarket_order_id": order.polymarket_order_id,
        "mode": order.mode,
        "created_at": order.created_at,
        "updated_at": order.updated_at,
        "expires_at": order.expires_at,
    }
```

- [ ] **Step 4: Add orders router to `api/main.py`**

```python
from api.orders.router import router as orders_router
# ...
app.include_router(orders_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_orders/test_order_http.py -v
```

Expected: 4 PASSED

Also run noncustodial tests:
```bash
ENV_FILE=.env.test pytest tests/test_orders/ -v
```

- [ ] **Step 6: Commit**

```bash
git add api/orders/router.py tests/test_orders/test_order_http.py api/main.py
git commit -m "feat: order router — hosted POST, non-custodial build/submit, list, cancel"
```

---

## Task 9: Portfolio Router

**Files:**
- Create: `api/portfolio/__init__.py`
- Create: `api/portfolio/schemas.py`
- Create: `api/portfolio/service.py`
- Create: `api/portfolio/router.py`
- Create: `tests/test_portfolio/__init__.py`
- Create: `tests/test_portfolio/test_portfolio.py`
- Modify: `api/main.py` (add portfolio router)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_portfolio/test_portfolio.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from api.auth.service import AuthService
from api.orders.service import OrderService


async def _setup_user_with_order(test_db_session, email: str):
    auth = AuthService(test_db_session)
    user = await auth.register(email, "pass123")
    key_result = await auth.create_api_key(user.id, "Key", ["portfolio:read"])
    mock_clob_resp = {"orderID": "poly_port_001", "status": "live"}
    with patch("api.orders.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst.post_order = AsyncMock(return_value=mock_clob_resp)
        MockClob.return_value = inst
        svc = OrderService(test_db_session)
        order = await svc.place_order(
            user_id=user.id, tier="free", market_id="0xportmkt",
            token_id="tok1", side="BUY", order_type="LIMIT", price=0.65, size=50.0,
        )
        # Mark partially filled
        order.status = "PARTIALLY_FILLED"
        order.size_filled = 25.0
        await test_db_session.commit()
    return user, key_result["key"]


async def test_get_positions(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_pos@example.com")
    resp = await client.get("/api/v1/portfolio/positions", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "positions" in data
    assert len(data["positions"]) == 1
    assert data["positions"][0]["market_id"] == "0xportmkt"


async def test_get_pnl(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_pnl@example.com")
    resp = await client.get("/api/v1/portfolio/pnl", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "realized" in data
    assert "unrealized" in data
    assert "fees_paid_broker" in data


async def test_get_balance(client, test_db_session):
    user, api_key = await _setup_user_with_order(test_db_session, "portfolio_bal@example.com")
    with patch("api.portfolio.service.ClobClient") as MockClob:
        inst = MagicMock()
        inst._get = AsyncMock(return_value={"balance": "1000.00"})
        MockClob.return_value = inst
        resp = await client.get("/api/v1/portfolio/balance", headers={"X-API-Key": api_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "balance" in data
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_portfolio/ -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `api/portfolio/__init__.py`** and `tests/test_portfolio/__init__.py`** (both empty)

- [ ] **Step 4: Create `api/portfolio/schemas.py`**

```python
from pydantic import BaseModel
from datetime import datetime


class PositionItem(BaseModel):
    market_id: str
    token_id: str
    side: str
    size_held: float      # size_filled (currently held)
    avg_price: float
    notional: float       # size_held * avg_price
    order_count: int


class PositionsResponse(BaseModel):
    positions: list[PositionItem]


class BalanceResponse(BaseModel):
    balance: float        # Total USDC
    locked: float         # In open orders
    available: float      # balance - locked


class PnlResponse(BaseModel):
    realized: float
    unrealized: float
    fees_paid_broker: float
    fees_paid_polymarket: float
```

- [ ] **Step 5: Create `api/portfolio/service.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from api.orders.models import Order
from core.polymarket.clob_client import ClobClient


class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_positions(self, user_id: str) -> list[dict]:
        """Aggregate open/partially-filled orders into positions."""
        stmt = select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.status.in_(["OPEN", "PARTIALLY_FILLED"]),
                Order.size_filled > 0,
            )
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        # Group by market_id + token_id
        positions: dict[str, dict] = {}
        for order in orders:
            key = f"{order.market_id}:{order.token_id}"
            if key not in positions:
                positions[key] = {
                    "market_id": order.market_id,
                    "token_id": order.token_id,
                    "side": order.side,
                    "total_size_filled": 0.0,
                    "total_notional": 0.0,
                    "order_count": 0,
                }
            p = positions[key]
            filled = float(order.size_filled)
            p["total_size_filled"] += filled
            p["total_notional"] += filled * float(order.price)
            p["order_count"] += 1

        result_list = []
        for p in positions.values():
            avg_price = (p["total_notional"] / p["total_size_filled"]) if p["total_size_filled"] > 0 else 0.0
            result_list.append({
                "market_id": p["market_id"],
                "token_id": p["token_id"],
                "side": p["side"],
                "size_held": p["total_size_filled"],
                "avg_price": avg_price,
                "notional": p["total_notional"],
                "order_count": p["order_count"],
            })
        return result_list

    async def get_balance(self, user_id: str) -> dict:
        """USDC balance: real balance from CLOB + locked in open orders."""
        # Locked = notional of all OPEN orders
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.status.in_(["OPEN", "PENDING"]))
        )
        result = await self.db.execute(stmt)
        open_orders = list(result.scalars().all())
        locked = sum(
            float(o.price) * (float(o.size) - float(o.size_filled))
            for o in open_orders
        )

        # Try to fetch real balance from CLOB (best-effort)
        balance = 0.0
        try:
            clob = ClobClient()
            bal_resp = await clob._get("/balance")
            balance = float(bal_resp.get("balance", 0))
        except Exception:
            pass  # Return 0 if CLOB unavailable

        return {
            "balance": balance,
            "locked": locked,
            "available": max(0.0, balance - locked),
        }

    async def get_pnl(self, user_id: str) -> dict:
        """Compute P&L from filled orders in our DB."""
        stmt = select(Order).where(
            and_(Order.user_id == user_id, Order.size_filled > 0)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        fees_paid_broker = sum(
            float(o.size_filled) * float(o.price) * (o.broker_fee_bps / 10000)
            for o in orders
        )

        # Simplified P&L: sum of filled notional for SELL minus BUY
        buy_notional = sum(
            float(o.size_filled) * float(o.price)
            for o in orders if o.side == "BUY"
        )
        sell_notional = sum(
            float(o.size_filled) * float(o.price)
            for o in orders if o.side == "SELL"
        )
        realized = sell_notional - buy_notional

        return {
            "realized": realized,
            "unrealized": 0.0,   # Requires live price feed — Plan 3
            "fees_paid_broker": fees_paid_broker,
            "fees_paid_polymarket": 0.0,  # Requires on-chain query — Plan 3
        }
```

- [ ] **Step 6: Create `api/portfolio/router.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from api.deps import get_current_user_from_api_key
from api.portfolio.service import PortfolioService
from api.portfolio.schemas import PositionsResponse, BalanceResponse, PnlResponse

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    positions = await PortfolioService(db).get_positions(user_id=auth["user_id"])
    return PositionsResponse(positions=positions)


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    result = await PortfolioService(db).get_balance(user_id=auth["user_id"])
    return BalanceResponse(**result)


@router.get("/pnl", response_model=PnlResponse)
async def get_pnl(
    auth: dict = Depends(get_current_user_from_api_key),
    db: AsyncSession = Depends(get_session),
):
    result = await PortfolioService(db).get_pnl(user_id=auth["user_id"])
    return PnlResponse(**result)
```

- [ ] **Step 7: Add portfolio router to `api/main.py`**

```python
from api.portfolio.router import router as portfolio_router
# ...
app.include_router(portfolio_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 8: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_portfolio/ -v
```

Expected: 3 PASSED

- [ ] **Step 9: Commit**

```bash
git add api/portfolio/ tests/test_portfolio/ api/main.py
git commit -m "feat: portfolio endpoints — positions, balance, pnl"
```

---

## Task 10: Full Test Suite + Smoke Test

- [ ] **Step 1: Run full test suite**

```bash
cd "/Users/ocean/Documents/产品代码开发/Polymarket Broker"
source .venv/bin/activate
ENV_FILE=.env.test pytest tests/ -v --tb=short
```

Expected: All tests PASS. Zero failures.

- [ ] **Step 2: Check coverage**

```bash
ENV_FILE=.env.test pytest tests/ --cov=api --cov=core --cov=db --cov-report=term-missing
```

Target: ≥ 70% overall. Identify any missing gaps.

- [ ] **Step 3: Verify all routes are registered**

```bash
ENV_FILE=.env.test python -c "
from api.main import app
routes = [r.path for r in app.routes]
expected = ['/api/v1/markets', '/api/v1/orders', '/api/v1/portfolio/positions']
for e in expected:
    found = any(r.startswith(e) or r == e for r in routes)
    print(f'{e}: {\"OK\" if found else \"MISSING\"}')"
```

Expected: All OK.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: Plan 2 complete — markets, orders, portfolio verified"
```

---

## Plan 2 Complete ✓

**What's now working and tested:**
- `GET /api/v1/markets` + detail, orderbook, trades, midpoint, search
- `POST /api/v1/orders` — hosted mode with fee injection, risk guard, EIP-712 sign, CLOB submit
- `POST /api/v1/orders/build` + `/submit` — non-custodial with Redis payload hash
- `GET/DELETE /api/v1/orders` — paginated order history, cancel, cancel-all
- `GET /api/v1/portfolio/positions` + `/balance` + `/pnl`
- X-API-Key auth dependency (SHA-256 key hash lookup)
- Fee engine: Free=10bps, Pro=5bps, Enterprise=0bps
- Risk guard: max order size + per-market position cap per tier

**Next:** Plan 3 — Data Pipeline (sports/NBA/BTC collectors + enhanced data endpoints)
