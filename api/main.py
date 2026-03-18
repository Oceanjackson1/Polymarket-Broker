from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import get_settings
from db.postgres import init_db
from db.redis_client import get_redis_pool
from api.middleware.error_handler import register_error_handlers
from api.middleware.rate_limit import RateLimitMiddleware
from api.auth.router import router as auth_router
from api.markets.router import router as markets_router

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
app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(markets_router, prefix=settings.api_v1_prefix)
