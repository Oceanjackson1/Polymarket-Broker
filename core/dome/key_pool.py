"""Round-robin API key pool with per-key rate-limit cooldown."""

import asyncio
import logging
import time

logger = logging.getLogger(__name__)

# Cooldown duration when a key gets rate-limited (429).
_DEFAULT_COOLDOWN_SECONDS = 10.0


class DomeKeyPool:
    """Distributes requests across multiple Dome API keys.

    Keys are rotated round-robin. When a key receives a 429 response,
    call `report_rate_limit(key)` to put it in cooldown — it will be
    skipped until the cooldown expires.

    Usage::

        pool = DomeKeyPool(["key1", "key2", ...])
        key = pool.next_key()
        # ... use key for request ...
        # if you get 429:
        pool.report_rate_limit(key)
    """

    def __init__(
        self,
        keys: list[str],
        cooldown_seconds: float = _DEFAULT_COOLDOWN_SECONDS,
        ws_key_count: int = 2,
    ):
        if not keys:
            raise ValueError("DomeKeyPool requires at least one API key")
        self._keys = list(keys)
        self._cooldown_seconds = cooldown_seconds
        # Split: last `ws_key_count` keys reserved for WebSocket connections.
        self._ws_key_count = min(ws_key_count, len(keys))
        self._rest_keys = self._keys[: len(keys) - self._ws_key_count] or self._keys
        self._ws_keys = self._keys[len(keys) - self._ws_key_count :] if self._ws_key_count else self._keys[:1]
        # Round-robin counters.
        self._rest_index = 0
        self._ws_index = 0
        # key -> earliest time it becomes available again.
        self._cooldowns: dict[str, float] = {}

    @property
    def rest_key_count(self) -> int:
        return len(self._rest_keys)

    @property
    def ws_key_count(self) -> int:
        return len(self._ws_keys)

    @property
    def total_key_count(self) -> int:
        return len(self._keys)

    # ── public API ──────────────────────────────────────────────

    def next_key(self) -> str:
        """Return the next available REST key (round-robin, skip cooled-down keys)."""
        return self._pick(self._rest_keys, "rest")

    def next_ws_key(self) -> str:
        """Return the next available WebSocket key."""
        return self._pick(self._ws_keys, "ws")

    def report_rate_limit(self, key: str) -> None:
        """Mark *key* as rate-limited; it will be skipped for `cooldown_seconds`."""
        until = time.monotonic() + self._cooldown_seconds
        self._cooldowns[key] = until
        logger.warning(
            "dome key …%s rate-limited, cooldown %.0fs",
            key[-6:],
            self._cooldown_seconds,
        )

    # ── internals ───────────────────────────────────────────────

    def _pick(self, keys: list[str], label: str) -> str:
        now = time.monotonic()
        n = len(keys)
        # Try each key once; fall back to the first key if all are cooling down.
        for _ in range(n):
            if label == "rest":
                idx = self._rest_index % n
                self._rest_index += 1
            else:
                idx = self._ws_index % n
                self._ws_index += 1
            key = keys[idx]
            cooldown_until = self._cooldowns.get(key, 0)
            if now >= cooldown_until:
                return key
        # All keys in cooldown — return the one that expires soonest.
        logger.warning("all %s dome keys in cooldown, using least-cooled", label)
        return min(keys, key=lambda k: self._cooldowns.get(k, 0))
