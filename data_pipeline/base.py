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
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                logger.info(f"[{self.name}] stopped")
                raise
