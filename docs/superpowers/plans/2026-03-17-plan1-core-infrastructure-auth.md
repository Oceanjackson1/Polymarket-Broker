# Plan 1: Core Infrastructure + Auth

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable FastAPI skeleton with PostgreSQL/Redis connections, Polymarket API clients migrated from Trade-Infra, and a fully-tested auth layer (API key CRUD + wallet challenge/verify/refresh).

**Architecture:** Monorepo with `api/` (FastAPI routers), `core/` (pure business logic, no HTTP), and `db/` (connection factories). Auth state in PostgreSQL; rate-limit counters and session nonces in Redis. JWT 15-min access + 30-day refresh. API keys Fernet AES-256 encrypted at rest.

**Tech Stack:** Python 3.12+, FastAPI, SQLAlchemy 2 (async), asyncpg, redis-py (async), pydantic-settings, python-jose[cryptography], cryptography, eth-account, httpx, pytest-asyncio, Docker Compose.

**Note:** Turso/libSQL is Plan 2+ (first needed for the ledger). Not included here.

**Spec:** `docs/superpowers/specs/2026-03-17-polymarket-broker-design.md` Sections 1–5, 10, 12, 13.

**Task ordering:** Each task depends on the previous. Do not skip or reorder.

---

## File Map

```
polymarket-broker/
├── api/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app factory, lifespan, router mount
│   ├── deps.py                      # Shared FastAPI dependencies (db session, current user)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py                # Route handlers for /api/v1/auth/*
│   │   ├── service.py               # Auth business logic (pure, no HTTP)
│   │   ├── schemas.py               # Pydantic request/response models
│   │   └── models.py                # SQLAlchemy ORM models (User, ApiKey, RefreshToken)
│   └── middleware/
│       ├── __init__.py
│       ├── rate_limit.py            # Redis daily rate limiter
│       └── error_handler.py         # Standard error envelope { error: { code, message } }
├── core/
│   ├── __init__.py
│   ├── config.py                    # pydantic-settings Settings class
│   ├── security.py                  # Fernet encrypt/decrypt, JWT encode/decode, HMAC
│   └── polymarket/
│       ├── __init__.py
│       ├── clob_client.py           # Async CLOB API client (migrated from Trade-Infra)
│       ├── gamma_client.py          # Async Gamma API client
│       └── eip712.py                # EIP-712 order signing utilities
├── db/
│   ├── __init__.py
│   ├── postgres.py                  # SQLAlchemy async engine + session factory
│   └── redis_client.py              # Redis async connection pool
├── tests/
│   ├── conftest.py                  # pytest fixtures: test app, test db, test redis
│   ├── test_auth/
│   │   ├── __init__.py
│   │   ├── test_register_login.py
│   │   ├── test_api_keys.py
│   │   └── test_wallet_auth.py
│   ├── test_core/
│   │   ├── __init__.py
│   │   ├── test_security.py
│   │   ├── test_models.py
│   │   └── test_polymarket_clients.py
│   └── test_middleware/
│       ├── __init__.py
│       └── test_rate_limit.py
├── .env.example
├── .env.test
├── pyproject.toml                   # pytest config (asyncio_mode = auto)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `pyproject.toml`
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `.env.example`
- Create: `core/config.py`
- Create: `api/main.py`
- Create all `__init__.py` files listed in the file map

- [ ] **Step 1: Create `requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
redis[hiredis]==5.0.8
pydantic-settings==2.4.0
pydantic[email]==2.8.0
python-jose[cryptography]==3.3.0
cryptography==43.0.0
httpx==0.27.2
passlib[bcrypt]==1.7.4
eth-account==0.11.0

# Test
pytest==8.3.2
pytest-asyncio==0.24.0
pytest-cov==5.0.0
```

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
env_files = [".env.test"]
testpaths = ["tests"]
```

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: broker
      POSTGRES_PASSWORD: broker
      POSTGRES_DB: broker
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U broker"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

- [ ] **Step 4: Create `Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 5: Create `.env.example`**

```env
# Database
DATABASE_URL=postgresql+asyncpg://broker:broker@localhost:5432/broker
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=change-me-32-chars-minimum-required!!
FERNET_KEY=generate-with-cryptography-fernet-generate-key

# Polymarket
POLYMARKET_CLOB_HOST=https://clob.polymarket.com
POLYMARKET_GAMMA_HOST=https://gamma-api.polymarket.com
POLYMARKET_PRIVATE_KEY=0x...
POLYMARKET_CHAIN_ID=137
POLYMARKET_RPC_URL=https://polygon-rpc.com/
POLYMARKET_FEE_ADDRESS=0x...

# App
ENVIRONMENT=development
API_V1_PREFIX=/api/v1
```

- [ ] **Step 6: Create `core/config.py`**

```python
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


def _env_file() -> str:
    """Allow ENV_FILE env var to override which .env file to load.
    Enables: ENV_FILE=.env.test pytest ...
    """
    return os.getenv("ENV_FILE", ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_env_file(), extra="ignore")

    # Database
    database_url: str
    redis_url: str

    # Security
    secret_key: str
    fernet_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # Polymarket
    polymarket_clob_host: str = "https://clob.polymarket.com"
    polymarket_gamma_host: str = "https://gamma-api.polymarket.com"
    polymarket_private_key: str = ""
    polymarket_chain_id: int = 137
    polymarket_rpc_url: str = "https://polygon-rpc.com/"
    polymarket_fee_address: str = ""

    # App
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 7: Create `api/main.py`**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import get_settings
from db.postgres import init_db
from db.redis_client import get_redis_pool
from api.middleware.error_handler import register_error_handlers
from api.auth.router import router as auth_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.redis = await get_redis_pool()
    yield
    await app.state.redis.aclose()


app = FastAPI(
    title="Polymarket Broker API",
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
```

- [ ] **Step 8: Create all `__init__.py` files**

```bash
touch api/__init__.py
touch api/auth/__init__.py
touch api/middleware/__init__.py
touch core/__init__.py
touch core/polymarket/__init__.py
touch db/__init__.py
mkdir -p tests/test_auth tests/test_core tests/test_middleware
touch tests/__init__.py tests/test_auth/__init__.py
touch tests/test_core/__init__.py tests/test_middleware/__init__.py
```

- [ ] **Step 9: Install and verify imports**

```bash
pip install -r requirements.txt
python -c "from api.main import app; print('OK')"
```

Expected: `OK`

- [ ] **Step 10: Commit**

```bash
git init
git add .
git commit -m "feat: project scaffold — FastAPI, Docker Compose, config, package structure"
```

---

## Task 2: Database Connections (PostgreSQL + Redis)

**Files:**
- Create: `db/postgres.py`
- Create: `db/redis_client.py`
- Create: `tests/conftest.py`
- Create: `.env.test`

- [ ] **Step 1: Create `.env.test`**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Copy output as FERNET_KEY below
```

```env
DATABASE_URL=postgresql+asyncpg://broker:broker@localhost:5432/broker_test
REDIS_URL=redis://localhost:6379/1
SECRET_KEY=test-secret-key-32-chars-minimum!!
FERNET_KEY=<paste output from command above>
POLYMARKET_CLOB_HOST=https://clob.polymarket.com
POLYMARKET_GAMMA_HOST=https://gamma-api.polymarket.com
```

- [ ] **Step 2: Write failing connection tests**

```python
# tests/test_core/test_connections.py
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_postgres_connection(test_db_session):
    result = await test_db_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.mark.asyncio
async def test_redis_connection(test_redis):
    await test_redis.set("ping", "pong", ex=5)
    val = await test_redis.get("ping")
    assert val == "pong"
```

- [ ] **Step 3: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_connections.py -v
```

Expected: `ImportError` or `fixture 'test_db_session' not found`

- [ ] **Step 4: Create `db/postgres.py`**

```python
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 5: Create `db/redis_client.py`**

```python
import redis.asyncio as aioredis
from core.config import get_settings

settings = get_settings()
_pool: aioredis.Redis | None = None


async def get_redis_pool() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


async def get_redis() -> aioredis.Redis:
    return await get_redis_pool()
```

- [ ] **Step 6: Create `tests/conftest.py`**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import redis.asyncio as aioredis
import os

os.environ.setdefault("ENV_FILE", ".env.test")

from api.main import app
from db.postgres import Base, get_session
from db.redis_client import get_redis

TEST_DB_URL = "postgresql+asyncpg://broker:broker@localhost:5432/broker_test"
TEST_REDIS_URL = "redis://localhost:6379/1"

test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Import models so Base.metadata knows about them
    from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_db_session() -> AsyncSession:
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_redis():
    r = aioredis.from_url(TEST_REDIS_URL, decode_responses=True)
    yield r
    await r.flushdb()
    await r.aclose()


@pytest_asyncio.fixture
async def client(test_db_session, test_redis):
    # Override get_session with a generator that yields the test session
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = lambda: test_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

- [ ] **Step 7: Start infrastructure**

```bash
docker compose up postgres redis -d
# Create test database
docker compose exec postgres psql -U broker -c "CREATE DATABASE broker_test;"
```

Expected: `CREATE DATABASE`

- [ ] **Step 8: Run tests — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_connections.py -v
```

Expected: 2 PASSED

- [ ] **Step 9: Commit**

```bash
git add db/ tests/conftest.py tests/test_core/test_connections.py .env.test pyproject.toml
git commit -m "feat: PostgreSQL + Redis connection factories, test fixtures"
```

---

## Task 3: Security Utilities (JWT, Fernet, HMAC)

**Files:**
- Create: `core/security.py`
- Create: `tests/test_core/test_security.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_core/test_security.py
import pytest
from core.security import (
    encrypt_api_key, decrypt_api_key,
    create_access_token, decode_access_token,
    create_refresh_token, decode_refresh_token,
    hmac_sign, hmac_verify,
    generate_api_key_value,
)


def test_fernet_roundtrip():
    plaintext = "pm_live_sk_abc123xyz"
    encrypted = encrypt_api_key(plaintext)
    assert encrypted != plaintext
    assert decrypt_api_key(encrypted) == plaintext


def test_access_token_roundtrip():
    token = create_access_token({"sub": "user_123", "tier": "free"})
    payload = decode_access_token(token)
    assert payload["sub"] == "user_123"
    assert payload["type"] == "access"


def test_access_token_expired_raises():
    token = create_access_token({"sub": "x"}, expires_minutes=-1)
    with pytest.raises(ValueError, match="Invalid token"):
        decode_access_token(token)


def test_refresh_token_roundtrip():
    token = create_refresh_token("user_456")
    payload = decode_refresh_token(token)
    assert payload["sub"] == "user_456"
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_hmac_sign_verify():
    secret = "webhook_secret_key"
    body = b'{"event": "order.filled"}'
    sig = hmac_sign(secret, body)
    assert sig.startswith("sha256=")
    assert hmac_verify(secret, body, sig) is True
    assert hmac_verify(secret, body, "sha256=badsig") is False


def test_generate_api_key_has_correct_prefix():
    key = generate_api_key_value("pm_live_sk")
    assert key.startswith("pm_live_sk_")
    assert len(key) > 20
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_security.py -v
```

Expected: `ImportError: cannot import name 'encrypt_api_key'`

- [ ] **Step 3: Implement `core/security.py`**

```python
import hmac as _hmac
import hashlib
import secrets
from datetime import datetime, timedelta, UTC

from cryptography.fernet import Fernet
from jose import jwt, JWTError

from core.config import get_settings

settings = get_settings()
_fernet = Fernet(settings.fernet_key.encode())


def encrypt_api_key(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_api_key(ciphertext: str) -> str:
    return _fernet.decrypt(ciphertext.encode()).decode()


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    mins = expires_minutes if expires_minutes is not None else settings.access_token_expire_minutes
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=mins)
    payload["type"] = "access"
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


def decode_access_token(token: str) -> dict:
    payload = _decode_token(token)
    if payload.get("type") != "access":
        raise ValueError("Invalid token: not an access token")
    return payload


def decode_refresh_token(token: str) -> dict:
    payload = _decode_token(token)
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token: not a refresh token")
    return payload


def generate_api_key_value(prefix: str = "pm_live_sk") -> str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"


def hmac_sign(secret: str, body: bytes) -> str:
    sig = _hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def hmac_verify(secret: str, body: bytes, signature: str) -> bool:
    expected = hmac_sign(secret, body)
    return _hmac.compare_digest(expected, signature)
```

- [ ] **Step 4: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_security.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add core/security.py tests/test_core/test_security.py
git commit -m "feat: JWT, Fernet AES-256, HMAC security utilities"
```

---

## Task 4: Polymarket API Clients (Migrate from Trade-Infra)

**Files:**
- Create: `core/polymarket/clob_client.py`
- Create: `core/polymarket/gamma_client.py`
- Create: `core/polymarket/eip712.py`
- Create: `tests/test_core/test_polymarket_clients.py`

- [ ] **Step 1: Write failing tests (mocked HTTP — no real API calls)**

```python
# tests/test_core/test_polymarket_clients.py
import pytest
from unittest.mock import AsyncMock, patch
from core.polymarket.gamma_client import GammaClient
from core.polymarket.clob_client import ClobClient
from core.polymarket.eip712 import build_order_struct


@pytest.mark.asyncio
async def test_gamma_get_markets_returns_list():
    client = GammaClient()
    mock_data = [{"id": "0xabc", "question": "Will X happen?"}]
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_data)):
        markets = await client.get_markets(limit=10)
    assert isinstance(markets, list)
    assert markets[0]["id"] == "0xabc"


@pytest.mark.asyncio
async def test_clob_get_orderbook_returns_bids_asks():
    client = ClobClient()
    mock_ob = {"bids": [{"price": "0.65", "size": "100"}], "asks": []}
    with patch.object(client, "_get", new=AsyncMock(return_value=mock_ob)):
        ob = await client.get_orderbook(token_id="21742633abc")
    assert "bids" in ob
    assert ob["bids"][0]["price"] == "0.65"


def test_eip712_order_struct_required_fields():
    order = build_order_struct(
        maker="0xabc123",
        token_id="21742633abc",
        price=0.65,
        size=100.0,
        side="BUY",
        fee_rate_bps=10,
        nonce=0,
    )
    for field in ["maker", "tokenId", "makerAmount", "takerAmount", "side", "feeRateBps", "nonce"]:
        assert field in order, f"Missing field: {field}"


def test_eip712_buy_amounts():
    order = build_order_struct(
        maker="0xabc", token_id="tok", price=0.5, size=200.0,
        side="BUY", fee_rate_bps=10, nonce=0,
    )
    # BUY: makerAmount = size * price * 10^6, takerAmount = size * 10^6
    assert order["makerAmount"] == str(int(200.0 * 0.5 * 1_000_000))
    assert order["takerAmount"] == str(int(200.0 * 1_000_000))
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_polymarket_clients.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Create `core/polymarket/gamma_client.py`**

```python
import httpx
from typing import Any
from core.config import get_settings

settings = get_settings()


class GammaClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.polymarket_gamma_host
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)

    async def _get(self, path: str, params: dict = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def get_markets(self, limit: int = 100, offset: int = 0, **filters) -> list:
        return await self._get("/markets", params={"limit": limit, "offset": offset, **filters})

    async def get_market(self, market_id: str) -> dict:
        return await self._get(f"/markets/{market_id}")

    async def get_events(self, **filters) -> list:
        return await self._get("/events", params=filters)

    async def close(self):
        await self._client.aclose()
```

- [ ] **Step 4: Create `core/polymarket/clob_client.py`**

```python
import httpx
from typing import Any
from core.config import get_settings

settings = get_settings()


class ClobClient:
    def __init__(self, base_url: str | None = None):
        self._base_url = base_url or settings.polymarket_clob_host
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)

    async def _get(self, path: str, params: dict = None) -> Any:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _post(self, path: str, json: dict, headers: dict = None) -> Any:
        resp = await self._client.post(path, json=json, headers=headers or {})
        resp.raise_for_status()
        return resp.json()

    async def get_orderbook(self, token_id: str) -> dict:
        return await self._get("/book", params={"token_id": token_id})

    async def get_midpoint(self, token_id: str) -> dict:
        return await self._get("/midpoint", params={"token_id": token_id})

    async def get_trades(self, market_id: str, **params) -> list:
        return await self._get("/trades", params={"market": market_id, **params})

    async def post_order(self, signed_order: dict, api_key: str) -> dict:
        import time
        headers = {
            "POLY_API_KEY": api_key,
            "POLY_TIMESTAMP": str(int(time.time())),
        }
        return await self._post("/order", json=signed_order, headers=headers)

    async def cancel_order(self, order_id: str, api_key: str) -> dict:
        import time
        headers = {"POLY_API_KEY": api_key, "POLY_TIMESTAMP": str(int(time.time()))}
        return await self._post("/cancel", json={"orderID": order_id}, headers=headers)

    async def close(self):
        await self._client.aclose()
```

- [ ] **Step 5: Create `core/polymarket/eip712.py`**

```python
"""
EIP-712 order struct builder for Polymarket CLOB.
Migrated from Polymarket-Trade-Infra / py-clob-client patterns.
"""
from decimal import Decimal

USDC_DECIMALS = 6


def to_units(value: float) -> int:
    """Convert float to USDC contract units (6 decimals)."""
    return int(Decimal(str(value)) * Decimal(10 ** USDC_DECIMALS))


def build_order_struct(
    maker: str,
    token_id: str,
    price: float,
    size: float,
    side: str,          # "BUY" or "SELL"
    fee_rate_bps: int,
    nonce: int = 0,
    expiration: int = 0,
) -> dict:
    """
    Builds the unsigned EIP-712 order dict.
    BUY:  makerAmount = size * price (USDC spent), takerAmount = size (tokens received)
    SELL: makerAmount = size (tokens spent),        takerAmount = size * price (USDC received)
    """
    if side == "BUY":
        maker_amount = to_units(size * price)
        taker_amount = to_units(size)
    else:
        maker_amount = to_units(size)
        taker_amount = to_units(size * price)

    return {
        "salt": nonce,
        "maker": maker,
        "signer": maker,
        "taker": "0x0000000000000000000000000000000000000000",
        "tokenId": token_id,
        "makerAmount": str(maker_amount),
        "takerAmount": str(taker_amount),
        "expiration": str(expiration),
        "nonce": str(nonce),
        "feeRateBps": str(fee_rate_bps),
        "side": 0 if side == "BUY" else 1,
        "signatureType": 0,
    }
```

- [ ] **Step 6: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_polymarket_clients.py -v
```

Expected: 4 PASSED

- [ ] **Step 7: Commit**

```bash
git add core/polymarket/ tests/test_core/test_polymarket_clients.py
git commit -m "feat: async Polymarket CLOB + Gamma clients, EIP-712 order struct builder"
```

---

## Task 5: ORM Models + DB Tables

**Files:**
- Create: `api/auth/models.py`
- Create: `tests/test_core/test_models.py`
- Modify: `db/postgres.py` (register models)

- [ ] **Step 1: Write failing model tests**

```python
# tests/test_core/test_models.py
import pytest
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncConnection


@pytest.mark.asyncio
async def test_users_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='users'")
    )
    assert result.scalar() == "users"


@pytest.mark.asyncio
async def test_api_keys_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='api_keys'")
    )
    assert result.scalar() == "api_keys"


@pytest.mark.asyncio
async def test_refresh_tokens_table_exists(test_db_session):
    result = await test_db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name='refresh_tokens'")
    )
    assert result.scalar() == "refresh_tokens"


@pytest.mark.asyncio
async def test_user_row_roundtrip(test_db_session):
    from api.auth.models import User
    from sqlalchemy import select
    user = User(email="model_test@test.com", hashed_password="hashed")
    test_db_session.add(user)
    await test_db_session.flush()
    fetched = await test_db_session.scalar(select(User).where(User.email == "model_test@test.com"))
    assert fetched is not None
    assert fetched.tier == "free"
    assert fetched.is_active is True
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_models.py -v
```

Expected: `ImportError` or table not found

- [ ] **Step 3: Create `api/auth/models.py`**

```python
import uuid
from datetime import datetime, UTC
from sqlalchemy import String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.postgres import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    wallet_address: Mapped[str | None] = mapped_column(String(42), unique=True, nullable=True, index=True)
    tier: Mapped[str] = mapped_column(String(20), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(20), nullable=False)
    key_encrypted: Mapped[str] = mapped_column(String(500), nullable=False)
    key_hint: Mapped[str] = mapped_column(String(10), nullable=False)
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="api_keys")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
```

- [ ] **Step 4: Register models in `db/postgres.py`**

Add these two lines after the `Base` class definition in `db/postgres.py`:

```python
# Register all ORM models so Base.metadata includes their tables
def _register_models():
    from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401

_register_models()
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_core/test_models.py -v
```

Expected: 4 PASSED

- [ ] **Step 6: Commit**

```bash
git add api/auth/models.py db/postgres.py tests/test_core/test_models.py
git commit -m "feat: User, ApiKey, RefreshToken ORM models"
```

---

## Task 6: Auth Service (Register, Login, API Key CRUD)

**Files:**
- Create: `api/auth/schemas.py`
- Create: `api/auth/service.py`
- Create: `tests/test_auth/test_register_login.py`
- Create: `tests/test_auth/test_api_keys.py`

- [ ] **Step 1: Create `api/auth/schemas.py`**

```python
from pydantic import BaseModel, EmailStr
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    tier: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = ["markets:read"]


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key: str
    key_hint: str
    scopes: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ApiKeyListItem(BaseModel):
    id: str
    name: str
    key_hint: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Create `api/auth/service.py`**

```python
from datetime import datetime, UTC
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from api.auth.models import User, ApiKey, RefreshToken
from core.security import (
    encrypt_api_key,
    create_access_token, create_refresh_token,
    decode_refresh_token,
    generate_api_key_value,
)

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str) -> User:
        existing = await self.db.scalar(select(User).where(User.email == email))
        if existing:
            raise ValueError("EMAIL_ALREADY_EXISTS")
        user = User(email=email, hashed_password=pwd_ctx.hash(password))
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, email: str, password: str) -> dict:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user or not pwd_ctx.verify(password, user.hashed_password):
            raise PermissionError("INVALID_CREDENTIALS")
        access = create_access_token({"sub": user.id, "tier": user.tier})
        refresh = create_refresh_token(user.id)
        refresh_payload = decode_refresh_token(refresh)
        rt = RefreshToken(
            jti=refresh_payload["jti"],
            user_id=user.id,
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], UTC),
        )
        self.db.add(rt)
        await self.db.commit()
        return {"access_token": access, "refresh_token": refresh}

    async def create_api_key(self, user_id: str, name: str, scopes: list[str]) -> dict:
        raw_key = generate_api_key_value("pm_live_sk")
        key = ApiKey(
            user_id=user_id,
            name=name,
            key_prefix="pm_live_sk",
            key_encrypted=encrypt_api_key(raw_key),
            key_hint=raw_key[-4:],
            scopes=scopes,
        )
        self.db.add(key)
        await self.db.commit()
        await self.db.refresh(key)
        return {**{c.name: getattr(key, c.name) for c in key.__table__.columns}, "key": raw_key}

    async def list_api_keys(self, user_id: str) -> list[ApiKey]:
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
        )
        return list(result.scalars().all())

    async def delete_api_key(self, user_id: str, key_id: str) -> None:
        key = await self.db.scalar(
            select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
        )
        if not key:
            raise KeyError("API_KEY_NOT_FOUND")
        key.is_active = False
        await self.db.commit()
```

- [ ] **Step 3: Write failing service tests (direct service calls — no HTTP)**

```python
# tests/test_auth/test_register_login.py
import pytest
from api.auth.service import AuthService


@pytest.mark.asyncio
async def test_register_creates_user(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("svc_test@example.com", "password123")
    assert user.email == "svc_test@example.com"
    assert user.id is not None
    assert user.tier == "free"


@pytest.mark.asyncio
async def test_register_duplicate_raises(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("dup@example.com", "pass")
    with pytest.raises(ValueError, match="EMAIL_ALREADY_EXISTS"):
        await svc.register("dup@example.com", "pass")


@pytest.mark.asyncio
async def test_login_returns_tokens(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("login@example.com", "mypassword123")
    result = await svc.login("login@example.com", "mypassword123")
    assert "access_token" in result
    assert "refresh_token" in result


@pytest.mark.asyncio
async def test_login_wrong_password_raises(test_db_session):
    svc = AuthService(test_db_session)
    await svc.register("badpw@example.com", "correct")
    with pytest.raises(PermissionError):
        await svc.login("badpw@example.com", "wrong")
```

```python
# tests/test_auth/test_api_keys.py
import pytest
from api.auth.service import AuthService


@pytest.mark.asyncio
async def test_create_api_key_returns_full_key(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("keyowner@example.com", "pass123")
    result = await svc.create_api_key(user.id, "My Bot", ["markets:read", "orders:write"])
    assert result["key"].startswith("pm_live_sk_")
    assert result["name"] == "My Bot"
    assert result["scopes"] == ["markets:read", "orders:write"]


@pytest.mark.asyncio
async def test_list_keys_returns_created_key(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("listkeys@example.com", "pass123")
    await svc.create_api_key(user.id, "Bot1", ["markets:read"])
    keys = await svc.list_api_keys(user.id)
    assert len(keys) == 1
    assert keys[0].name == "Bot1"


@pytest.mark.asyncio
async def test_delete_key_deactivates(test_db_session):
    svc = AuthService(test_db_session)
    user = await svc.register("deletekey@example.com", "pass")
    result = await svc.create_api_key(user.id, "ToDelete", ["markets:read"])
    await svc.delete_api_key(user.id, result["id"])
    keys = await svc.list_api_keys(user.id)
    assert len(keys) == 0
```

- [ ] **Step 4: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_auth/ -v
```

Expected: `ImportError` or service errors

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_register_login.py tests/test_auth/test_api_keys.py -v
```

Expected: 7 PASSED

- [ ] **Step 6: Commit**

```bash
git add api/auth/schemas.py api/auth/service.py tests/test_auth/test_register_login.py tests/test_auth/test_api_keys.py
git commit -m "feat: auth service — register, login, API key CRUD"
```

---

## Task 7: Auth Router + Error Handler + Deps

**Files:**
- Create: `api/middleware/error_handler.py`
- Create: `api/deps.py`
- Create: `api/auth/router.py`

- [ ] **Step 1: Write failing HTTP-level tests**

```python
# tests/test_auth/test_http_auth.py
import pytest


@pytest.mark.asyncio
async def test_http_register_returns_201(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "http_test@example.com", "password": "strongpassword123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "http_test@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_http_register_duplicate_returns_409(client):
    payload = {"email": "http_dup@example.com", "password": "pass123456"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_http_login_returns_tokens(client):
    await client.post("/api/v1/auth/register", json={
        "email": "http_login@example.com", "password": "mypassword123"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "http_login@example.com", "password": "mypassword123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_http_create_and_list_keys(client):
    await client.post("/api/v1/auth/register", json={
        "email": "http_keys@example.com", "password": "password123"
    })
    login = await client.post("/api/v1/auth/login", json={
        "email": "http_keys@example.com", "password": "password123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/api/v1/auth/keys",
        json={"name": "My Bot", "scopes": ["markets:read"]}, headers=headers)
    assert create_resp.status_code == 201
    assert create_resp.json()["key"].startswith("pm_live_sk_")

    list_resp = await client.get("/api/v1/auth/keys", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
```

- [ ] **Step 2: Run — confirm FAIL (routes not yet defined)**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_http_auth.py -v
```

Expected: 404 or `ImportError`

- [ ] **Step 3: Create `api/middleware/error_handler.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def _err(code: str, message: str, status: int, details: dict = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or {}}}
    )


def register_error_handlers(app: FastAPI):
    @app.exception_handler(ValueError)
    async def value_error_handler(req: Request, exc: ValueError):
        code = str(exc)
        status = 409 if "EXISTS" in code else 400
        return _err(code, str(exc), status)

    @app.exception_handler(PermissionError)
    async def permission_error_handler(req: Request, exc: PermissionError):
        return _err(str(exc), "Authentication failed.", 401)

    @app.exception_handler(KeyError)
    async def key_error_handler(req: Request, exc: KeyError):
        return _err(str(exc).strip("'"), "Resource not found.", 404)

    @app.exception_handler(Exception)
    async def generic_handler(req: Request, exc: Exception):
        return _err("INTERNAL_ERROR", "An unexpected error occurred.", 500)
```

- [ ] **Step 4: Create `api/deps.py`**

```python
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
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
```

- [ ] **Step 5: Create `api/auth/router.py`**

```python
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from db.postgres import get_session
from api.deps import get_current_user_id
from api.auth.service import AuthService
from api.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, UserResponse,
    ApiKeyCreateRequest, ApiKeyCreatedResponse, ApiKeyListItem,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_session)):
    return await AuthService(db).register(body.email, body.password)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_session)):
    tokens = await AuthService(db).login(body.email, body.password)
    return {**tokens, "token_type": "bearer"}


@router.get("/keys", response_model=list[ApiKeyListItem])
async def list_keys(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    return await AuthService(db).list_api_keys(user_id)


@router.post("/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_key(
    body: ApiKeyCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    return await AuthService(db).create_api_key(user_id, body.name, body.scopes)


@router.delete("/keys/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_session),
):
    await AuthService(db).delete_api_key(user_id, key_id)
    return Response(status_code=204)
```

- [ ] **Step 6: Run all auth tests — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_auth/ -v
```

Expected: All PASSED

- [ ] **Step 7: Commit**

```bash
git add api/middleware/error_handler.py api/deps.py api/auth/router.py tests/test_auth/test_http_auth.py
git commit -m "feat: auth HTTP router, error handler, Bearer token dependency"
```

---

## Task 8: Wallet Auth (Challenge / Verify / Refresh)

**Files:**
- Modify: `api/auth/service.py` (add wallet methods)
- Modify: `api/auth/router.py` (add wallet routes)
- Create: `tests/test_auth/test_wallet_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_auth/test_wallet_auth.py
import pytest
from eth_account import Account
from eth_account.messages import encode_defunct


@pytest.mark.asyncio
async def test_wallet_challenge_returns_nonce(client):
    account = Account.create()
    resp = await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": account.address})
    assert resp.status_code == 200
    data = resp.json()
    assert "nonce" in data
    assert "expires_at" in data
    assert len(data["nonce"]) == 32  # 16 bytes hex


@pytest.mark.asyncio
async def test_wallet_verify_valid_signature(client, test_redis):
    account = Account.create()
    address = account.address

    challenge = await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": address})
    nonce = challenge.json()["nonce"]

    msg = encode_defunct(text=f"Sign in to Polymarket Broker\nNonce: {nonce}")
    signed = account.sign_message(msg)

    verify = await client.post("/api/v1/auth/wallet/verify", json={
        "wallet_address": address,
        "signature": signed.signature.hex(),
    })
    assert verify.status_code == 200
    assert "access_token" in verify.json()
    assert "refresh_token" in verify.json()


@pytest.mark.asyncio
async def test_wallet_verify_bad_signature_returns_401(client):
    account = Account.create()
    await client.post("/api/v1/auth/wallet/challenge",
        json={"wallet_address": account.address})
    resp = await client.post("/api/v1/auth/wallet/verify", json={
        "wallet_address": account.address,
        "signature": "0x" + "ab" * 65,
    })
    assert resp.status_code == 401
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_wallet_auth.py -v
```

Expected: 404 (routes not yet defined)

- [ ] **Step 3: Add wallet methods to `api/auth/service.py`**

Add these imports at the top of `service.py`:

```python
import secrets
from datetime import timedelta
import redis.asyncio as aioredis
from eth_account import Account
from eth_account.messages import encode_defunct
```

Then add these methods to the `AuthService` class:

```python
async def create_wallet_challenge(
    self, wallet_address: str, redis: aioredis.Redis
) -> dict:
    nonce = secrets.token_hex(16)
    key = f"wallet_nonce:{wallet_address.lower()}"
    await redis.set(key, nonce, ex=300)
    expires_at = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()
    return {"nonce": nonce, "expires_at": expires_at}

async def verify_wallet_signature(
    self, wallet_address: str, signature: str, redis: aioredis.Redis
) -> dict:
    key = f"wallet_nonce:{wallet_address.lower()}"
    nonce = await redis.get(key)
    if not nonce:
        raise PermissionError("NONCE_EXPIRED_OR_NOT_FOUND")

    msg = encode_defunct(text=f"Sign in to Polymarket Broker\nNonce: {nonce}")
    try:
        recovered = Account.recover_message(msg, signature=signature)
    except Exception as exc:
        raise PermissionError("INVALID_SIGNATURE") from exc

    if recovered.lower() != wallet_address.lower():
        raise PermissionError("SIGNATURE_MISMATCH")

    await redis.delete(key)  # Nonce is single-use

    user = await self.db.scalar(
        select(User).where(User.wallet_address == wallet_address.lower())
    )
    if not user:
        user = User(
            email=f"{wallet_address.lower()}@wallet.local",
            hashed_password="",
            wallet_address=wallet_address.lower(),
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

    access = create_access_token({"sub": user.id, "tier": user.tier})
    refresh = create_refresh_token(user.id)
    refresh_payload = decode_refresh_token(refresh)
    rt = RefreshToken(
        jti=refresh_payload["jti"],
        user_id=user.id,
        expires_at=datetime.fromtimestamp(refresh_payload["exp"], UTC),
    )
    self.db.add(rt)
    await self.db.commit()
    return {"access_token": access, "refresh_token": refresh}
```

- [ ] **Step 4: Add wallet routes to `api/auth/router.py`**

Add this import at the top of `router.py`:

```python
import redis.asyncio as aioredis
from db.redis_client import get_redis
```

Then add these routes:

```python
@router.post("/wallet/challenge")
async def wallet_challenge(
    body: dict,
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    return await AuthService(db).create_wallet_challenge(body["wallet_address"], redis)


@router.post("/wallet/verify", response_model=TokenResponse)
async def wallet_verify(
    body: dict,
    db: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
):
    tokens = await AuthService(db).verify_wallet_signature(
        body["wallet_address"], body["signature"], redis
    )
    return {**tokens, "token_type": "bearer"}
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_auth/test_wallet_auth.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add api/auth/service.py api/auth/router.py tests/test_auth/test_wallet_auth.py
git commit -m "feat: wallet challenge/verify auth with EIP-191 signature verification"
```

---

## Task 9: Rate Limiting Middleware

**Files:**
- Create: `api/middleware/rate_limit.py`
- Modify: `api/main.py` (register middleware)
- Create: `tests/test_middleware/test_rate_limit.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_middleware/test_rate_limit.py
import pytest


@pytest.mark.asyncio
async def test_rate_limit_headers_on_normal_request(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "rl_test@test.com", "password": "pass123"
    })
    assert resp.status_code in (201, 409)
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers
    assert "X-RateLimit-Reset" in resp.headers


@pytest.mark.asyncio
async def test_rate_limit_remaining_decrements(client, test_redis):
    await test_redis.delete("ratelimit:ip:testclient:calls")
    resp1 = await client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "x"})
    resp2 = await client.post("/api/v1/auth/login", json={"email": "x@x.com", "password": "x"})
    remaining1 = int(resp1.headers.get("X-RateLimit-Remaining", 999))
    remaining2 = int(resp2.headers.get("X-RateLimit-Remaining", 999))
    assert remaining2 <= remaining1


@pytest.mark.asyncio
async def test_rate_limit_returns_429_when_exceeded(client, test_redis):
    # Manually exceed the daily limit
    await test_redis.set("ratelimit:ip:testclient:calls", 600, ex=60)
    resp = await client.get("/api/v1/auth/keys", headers={"Authorization": "Bearer invalid"})
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
```

- [ ] **Step 2: Run — confirm FAIL**

```bash
ENV_FILE=.env.test pytest tests/test_middleware/test_rate_limit.py -v
```

Expected: tests fail — `X-RateLimit-Limit` not in headers, or middleware not present

- [ ] **Step 3: Create `api/middleware/rate_limit.py`**

```python
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


DAILY_LIMIT_FREE = 500   # Free tier daily call limit


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        redis = getattr(request.app.state, "redis", None)
        if redis is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        day_key = f"ratelimit:ip:{ip}:calls"

        calls_today = await redis.incr(day_key)
        if calls_today == 1:
            await redis.expire(day_key, 86400)

        ttl = await redis.ttl(day_key)
        reset_at = int(time.time()) + max(ttl, 0)
        remaining = max(0, DAILY_LIMIT_FREE - calls_today)

        if calls_today > DAILY_LIMIT_FREE:
            return JSONResponse(
                status_code=429,
                content={"error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Daily API limit reached. Upgrade to Pro for unlimited access.",
                    "details": {}
                }},
                headers={
                    "Retry-After": "3600",
                    "X-RateLimit-Limit": str(DAILY_LIMIT_FREE),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(DAILY_LIMIT_FREE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response
```

Note: This implements the daily limit for the Free tier. Per-minute burst limiting and tier-aware limits are Plan 2 (requires user tier lookup per request, which needs the auth middleware to run first).

- [ ] **Step 4: Register middleware in `api/main.py`**

Add after the `app = FastAPI(...)` line:

```python
from api.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)
```

- [ ] **Step 5: Run — confirm PASS**

```bash
ENV_FILE=.env.test pytest tests/test_middleware/test_rate_limit.py -v
```

Expected: 3 PASSED

- [ ] **Step 6: Commit**

```bash
git add api/middleware/rate_limit.py api/main.py tests/test_middleware/test_rate_limit.py
git commit -m "feat: Redis daily rate limiter middleware with X-RateLimit-* headers"
```

---

## Task 10: Full Test Suite + Docker Smoke Test

- [ ] **Step 1: Run full test suite**

```bash
ENV_FILE=.env.test pytest tests/ -v --tb=short
```

Expected: All tests PASS. Zero failures.

- [ ] **Step 2: Check coverage**

```bash
ENV_FILE=.env.test pytest tests/ --cov=api --cov=core --cov=db --cov-report=term-missing
```

Target: ≥ 75% on `api/auth/` and `core/security.py`. Identify gaps for follow-up.

- [ ] **Step 3: Start full Docker stack**

```bash
# Copy .env.example to .env and fill in values
cp .env.example .env
# Edit .env: set DATABASE_URL, REDIS_URL, SECRET_KEY, FERNET_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste FERNET_KEY into .env

docker compose up --build -d
sleep 10
```

- [ ] **Step 4: Confirm app is live**

```bash
curl -s http://localhost:8000/docs | grep -c "Polymarket Broker API"
```

Expected: `1`

- [ ] **Step 5: Smoke test register + login via curl**

```bash
# Register
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"password123"}' | python3 -m json.tool

# Login — should return access_token and refresh_token
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"password123"}' | python3 -m json.tool
```

Expected: `access_token` and `refresh_token` in login response.

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "chore: Plan 1 complete — core infra, auth, rate limiting verified"
```

---

## Plan 1 Complete ✓

**What's now working and tested:**
- FastAPI app on Docker Compose (PostgreSQL + Redis)
- Async Polymarket CLOB + Gamma API clients
- EIP-712 order struct builder (migrated from Trade-Infra)
- JWT access tokens (15 min) + refresh tokens (30 days) with type validation
- Fernet AES-256 encrypted API keys
- HMAC-SHA256 webhook signing utilities
- Full auth layer: email/password register + login, wallet challenge/verify, API key CRUD
- Redis daily rate limiter with X-RateLimit-* headers
- Standard error envelope `{ error: { code, message, details } }`

**Next:** [Plan 2 — Markets + Orders](2026-03-17-plan2-markets-orders.md) — market data endpoints, hosted + non-custodial order placement, fee engine, risk guard, portfolio endpoints.
