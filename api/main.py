import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from api.data.crypto.router import router as crypto_data_router
from api.data.dome.router import router as dome_data_router
from api.data.weather.router import router as weather_data_router
from api.analysis.router import router as analysis_router
from api.strategies.router import router as strategies_router
from api.webhooks.router import router as webhooks_router
from api.ws.router import router as ws_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    app.state.redis = await get_redis_pool()

    # ── Build Dome stack (optional — graceful if no keys configured) ──
    dome_client = None
    dome_ws = None
    try:
        from core.dome.factory import build_dome_key_pool, build_dome_client, build_dome_ws, get_tracked_wallets

        pool = build_dome_key_pool()
        if pool:
            dome_client = build_dome_client(pool)
            app.state.dome_client = dome_client
            logger.info("dome client initialised (%d REST keys, %d WS keys)", pool.rest_key_count, pool.ws_key_count)

            if settings.dome_ws_enabled:
                dome_ws = build_dome_ws(pool)
                await dome_ws.start()
                app.state.dome_ws = dome_ws
        else:
            logger.info("dome api keys not configured — dome features disabled")
    except Exception:
        logger.warning("failed to initialise dome stack", exc_info=True)

    # ── Start collectors ──
    tasks = []
    if not settings.disable_collectors:
        from data_pipeline.sports_collector import SportsCollector
        from data_pipeline.nba_collector import NbaCollector
        from data_pipeline.btc_collector import BtcCollector
        from db.postgres import AsyncSessionLocal

        from data_pipeline.coinglass_collector import CoinGlassCollector
        from data_pipeline.weather_collector import WeatherCollector

        tasks = [
            asyncio.create_task(SportsCollector(dome_client=dome_client).run(AsyncSessionLocal)),
            asyncio.create_task(NbaCollector(dome_client=dome_client).run(AsyncSessionLocal)),
            asyncio.create_task(BtcCollector(dome_client=dome_client).run(AsyncSessionLocal)),
            asyncio.create_task(CoinGlassCollector().run(AsyncSessionLocal)),
            asyncio.create_task(WeatherCollector().run(AsyncSessionLocal)),
        ]

        # Dome-powered collectors (only if keys present).
        if dome_client:
            from data_pipeline.dome_market_collector import DomeMarketCollector
            from data_pipeline.kalshi_collector import KalshiCollector
            from data_pipeline.wallet_tracker import WalletTracker
            from core.dome.factory import get_tracked_wallets

            tasks.append(asyncio.create_task(DomeMarketCollector(dome_client).run(AsyncSessionLocal)))
            tasks.append(asyncio.create_task(KalshiCollector(dome_client).run(AsyncSessionLocal)))

            wallets = get_tracked_wallets()
            if wallets:
                tasks.append(asyncio.create_task(WalletTracker(dome_client, wallets).run(AsyncSessionLocal)))

    yield

    # ── Shutdown ──
    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    if dome_ws:
        await dome_ws.stop()
    if dome_client:
        await dome_client.close()

    await app.state.redis.aclose()


app = FastAPI(
    title="Polymarket Broker API",
    version="1.0.0",
    lifespan=lifespan,
)

register_error_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(markets_router, prefix=settings.api_v1_prefix)
app.include_router(orders_router, prefix=settings.api_v1_prefix)
app.include_router(portfolio_router, prefix=settings.api_v1_prefix)
app.include_router(sports_data_router, prefix=settings.api_v1_prefix)
app.include_router(nba_data_router, prefix=settings.api_v1_prefix)
app.include_router(btc_data_router, prefix=settings.api_v1_prefix)
app.include_router(crypto_data_router, prefix=settings.api_v1_prefix)
app.include_router(dome_data_router, prefix=settings.api_v1_prefix)
app.include_router(weather_data_router, prefix=settings.api_v1_prefix)
app.include_router(analysis_router, prefix=settings.api_v1_prefix)
app.include_router(strategies_router, prefix=settings.api_v1_prefix)
app.include_router(webhooks_router, prefix=settings.api_v1_prefix)
app.include_router(ws_router)  # No prefix — WebSocket paths start with /ws/
