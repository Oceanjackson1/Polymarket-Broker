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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once per session, drop at the end."""
    # Import models so Base.metadata knows about them (models created in Task 5)
    try:
        from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
        from api.orders.models import Order  # noqa: F401
        from api.data.sports.models import SportsEvent  # noqa: F401
        from api.data.nba.models import NbaGame  # noqa: F401
        from api.data.btc.models import BtcSnapshot  # noqa: F401
        from api.data.crypto.models import CryptoDerivatives  # noqa: F401
        from api.data.dome.models import MarketSnapshot, CrossPlatformSpread, WalletSnapshot  # noqa: F401
        from api.data.weather.models import WeatherEvent, CityCoordinate  # noqa: F401
    except ImportError:
        pass

    engine = create_async_engine(TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_db_session(setup_test_db) -> AsyncSession:
    """Session-scoped DB session (same event loop as setup_test_db)."""
    engine = setup_test_db
    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def test_redis():
    r = aioredis.from_url(TEST_REDIS_URL, decode_responses=True)
    yield r
    await r.flushdb()
    await r.aclose()


@pytest_asyncio.fixture(scope="session")
async def client(test_db_session, test_redis):
    # Override get_session with a generator that yields the test session
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_redis] = lambda: test_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
