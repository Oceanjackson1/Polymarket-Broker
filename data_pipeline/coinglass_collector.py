# data_pipeline/coinglass_collector.py
import logging
from datetime import datetime, UTC
from decimal import Decimal
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from data_pipeline.base import BaseCollector
from api.data.crypto.models import CryptoDerivatives
from core.config import get_settings

logger = logging.getLogger(__name__)

SYMBOLS = ["BTC", "ETH", "SOL"]


class CoinGlassCollector(BaseCollector):
    name = "coinglass_collector"
    interval_seconds = 30

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.coinglass_api_key
        self._base = settings.coinglass_api_base

    async def collect(self, db: AsyncSession) -> None:
        headers = {"CG-API-KEY": self._api_key}

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            # Shared calls (return all symbols at once)
            liquidation_data = await self._fetch_liquidations(client)
            fear_greed = await self._fetch_fear_greed(client)

            # Per-symbol calls
            for symbol in SYMBOLS:
                funding = await self._fetch_funding(client, symbol)
                oi = await self._fetch_open_interest(client, symbol)
                liq = self._extract_liquidation(liquidation_data, symbol)
                taker = await self._fetch_taker_volume(client, symbol)

                row = CryptoDerivatives(
                    symbol=symbol,
                    funding_rate_avg=funding.get("avg"),
                    funding_rate_max=funding.get("max"),
                    funding_rate_min=funding.get("min"),
                    funding_rates_json=funding.get("exchanges"),
                    next_funding_time=funding.get("next_time"),
                    oi_total_usd=oi.get("total_usd"),
                    oi_change_pct_5m=oi.get("change_5m"),
                    oi_change_pct_15m=oi.get("change_15m"),
                    oi_change_pct_1h=oi.get("change_1h"),
                    oi_change_pct_4h=oi.get("change_4h"),
                    oi_change_pct_24h=oi.get("change_24h"),
                    oi_exchanges_json=oi.get("exchanges"),
                    liq_long_1h_usd=liq.get("long_1h"),
                    liq_short_1h_usd=liq.get("short_1h"),
                    liq_long_4h_usd=liq.get("long_4h"),
                    liq_short_4h_usd=liq.get("short_4h"),
                    liq_long_24h_usd=liq.get("long_24h"),
                    liq_short_24h_usd=liq.get("short_24h"),
                    taker_buy_ratio=taker.get("buy_ratio"),
                    taker_sell_ratio=taker.get("sell_ratio"),
                    taker_buy_vol_usd=taker.get("buy_vol"),
                    taker_sell_vol_usd=taker.get("sell_vol"),
                    fear_greed_index=fear_greed,
                    recorded_at=datetime.now(UTC),
                )
                db.add(row)

        await db.commit()

    async def _fetch_funding(self, client: httpx.AsyncClient, symbol: str) -> dict:
        try:
            resp = await client.get(
                f"{self._base}/api/futures/funding-rate/exchange-list",
                params={"symbol": symbol},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                return {}
            entries = data[0].get("stablecoin_margin_list", [])
            rates = [e["funding_rate"] for e in entries if "funding_rate" in e]
            if not rates:
                return {}
            exchanges = [
                {
                    "exchange": e.get("exchange"),
                    "rate": e.get("funding_rate"),
                    "interval": e.get("funding_rate_interval"),
                }
                for e in entries
            ]
            return {
                "avg": Decimal(str(sum(rates) / len(rates))),
                "max": Decimal(str(max(rates))),
                "min": Decimal(str(min(rates))),
                "exchanges": exchanges,
                "next_time": entries[0].get("next_funding_time"),
            }
        except Exception as e:
            logger.warning(f"[coinglass] funding-rate/{symbol} failed: {e}")
            return {}

    async def _fetch_open_interest(self, client: httpx.AsyncClient, symbol: str) -> dict:
        try:
            resp = await client.get(
                f"{self._base}/api/futures/open-interest/exchange-list",
                params={"symbol": symbol},
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            if not data:
                return {}
            agg = next((d for d in data if d.get("exchange") == "All"), data[0])
            exchanges = [
                {"exchange": d["exchange"], "oi_usd": d.get("open_interest_usd")}
                for d in data if d.get("exchange") != "All"
            ]
            return {
                "total_usd": Decimal(str(agg.get("open_interest_usd", 0))),
                "change_5m": Decimal(str(agg.get("open_interest_change_percent_5m", 0))),
                "change_15m": Decimal(str(agg.get("open_interest_change_percent_15m", 0))),
                "change_1h": Decimal(str(agg.get("open_interest_change_percent_1h", 0))),
                "change_4h": Decimal(str(agg.get("open_interest_change_percent_4h", 0))),
                "change_24h": Decimal(str(agg.get("open_interest_change_percent_24h", 0))),
                "exchanges": exchanges[:10],
            }
        except Exception as e:
            logger.warning(f"[coinglass] open-interest/{symbol} failed: {e}")
            return {}

    async def _fetch_liquidations(self, client: httpx.AsyncClient) -> list:
        try:
            resp = await client.get(f"{self._base}/api/futures/liquidation/coin-list")
            resp.raise_for_status()
            return resp.json().get("data", [])
        except Exception as e:
            logger.warning(f"[coinglass] liquidation/coin-list failed: {e}")
            return []

    def _extract_liquidation(self, all_data: list, symbol: str) -> dict:
        entry = next((d for d in all_data if d.get("symbol") == symbol), None)
        if not entry:
            return {}
        return {
            "long_1h": Decimal(str(entry.get("long_liquidation_usd_1h", 0))),
            "short_1h": Decimal(str(entry.get("short_liquidation_usd_1h", 0))),
            "long_4h": Decimal(str(entry.get("long_liquidation_usd_4h", 0))),
            "short_4h": Decimal(str(entry.get("short_liquidation_usd_4h", 0))),
            "long_24h": Decimal(str(entry.get("long_liquidation_usd_24h", 0))),
            "short_24h": Decimal(str(entry.get("short_liquidation_usd_24h", 0))),
        }

    async def _fetch_taker_volume(self, client: httpx.AsyncClient, symbol: str) -> dict:
        try:
            resp = await client.get(
                f"{self._base}/api/futures/taker-buy-sell-volume/exchange-list",
                params={"symbol": symbol, "range": "1h"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            if not data:
                return {}
            return {
                "buy_ratio": Decimal(str(data.get("buy_ratio", 0))),
                "sell_ratio": Decimal(str(data.get("sell_ratio", 0))),
                "buy_vol": Decimal(str(data.get("buy_vol_usd", 0))),
                "sell_vol": Decimal(str(data.get("sell_vol_usd", 0))),
            }
        except Exception as e:
            logger.warning(f"[coinglass] taker-volume/{symbol} failed: {e}")
            return {}

    async def _fetch_fear_greed(self, client: httpx.AsyncClient) -> int | None:
        try:
            resp = await client.get(
                f"{self._base}/api/index/fear-greed-history",
                params={"limit": 1},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            data_list = data.get("data_list", [])
            return int(data_list[0]) if data_list else None
        except Exception as e:
            logger.warning(f"[coinglass] fear-greed failed: {e}")
            return None
