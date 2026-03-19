"""Convenience factory: create DomeKeyPool, DomeClient, and DomeWebSocketManager from Settings."""

from core.config import get_settings
from core.dome.key_pool import DomeKeyPool
from core.dome.client import DomeClient
from core.dome.websocket import DomeWebSocketManager


def build_dome_key_pool() -> DomeKeyPool | None:
    """Return a DomeKeyPool from settings, or None if no keys are configured."""
    s = get_settings()
    raw = s.dome_api_keys.strip()
    if not raw:
        return None
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        return None
    return DomeKeyPool(
        keys=keys,
        cooldown_seconds=s.dome_cooldown_seconds,
        ws_key_count=s.dome_ws_key_count,
    )


def build_dome_client(pool: DomeKeyPool) -> DomeClient:
    s = get_settings()
    return DomeClient(key_pool=pool, base_url=s.dome_api_base)


def build_dome_ws(pool: DomeKeyPool) -> DomeWebSocketManager:
    return DomeWebSocketManager(key_pool=pool)


def get_tracked_wallets() -> list[str]:
    s = get_settings()
    raw = s.tracked_wallets.strip()
    if not raw:
        return []
    return [w.strip() for w in raw.split(",") if w.strip()]
