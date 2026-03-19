from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Register all ORM models so Base.metadata includes their tables
def _register_models():
    from api.auth.models import User, ApiKey, RefreshToken  # noqa: F401
    from api.orders.models import Order  # noqa: F401
    from api.data.sports.models import SportsEvent  # noqa: F401
    from api.data.nba.models import NbaGame  # noqa: F401
    from api.data.btc.models import BtcSnapshot  # noqa: F401
    from api.data.crypto.models import CryptoDerivatives  # noqa: F401
    from api.data.dome.models import MarketSnapshot, CrossPlatformSpread, WalletSnapshot  # noqa: F401

_register_models()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
