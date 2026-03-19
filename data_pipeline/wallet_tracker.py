# data_pipeline/wallet_tracker.py
"""Periodically snapshots tracked wallets' positions and PnL via Dome API."""

import logging
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.dome.client import DomeClient
from data_pipeline.base import BaseCollector
from api.data.dome.models import WalletSnapshot

logger = logging.getLogger(__name__)


class WalletTracker(BaseCollector):
    name = "wallet_tracker"
    interval_seconds = 300

    def __init__(self, dome_client: DomeClient, wallets: list[str]):
        self._dome = dome_client
        self._wallets = wallets

    async def collect(self, db: AsyncSession) -> None:
        if not self._wallets:
            return

        for addr in self._wallets:
            try:
                # Fetch PnL.
                pnl_resp = await self._dome.get_wallet_pnl(addr, granularity="all")
                pnl_data = pnl_resp.get("pnl_over_time", [])
                total_pnl = Decimal(str(pnl_data[-1].get("pnl", 0))) if pnl_data else None

                # Fetch positions.
                pos_resp = await self._dome.get_positions(addr, limit=100)
                positions = pos_resp.get("data", []) if isinstance(pos_resp, dict) else pos_resp
                position_count = len(positions)

                snapshot = WalletSnapshot(
                    wallet_address=addr,
                    total_pnl=total_pnl,
                    position_count=position_count,
                    positions_json=positions,
                    recorded_at=datetime.now(UTC),
                )
                db.add(snapshot)
            except Exception:
                logger.warning("wallet_tracker: failed for %s", addr, exc_info=True)

        await db.commit()
        logger.debug("wallet_tracker: snapshotted %d wallets", len(self._wallets))
