"""TG Agent context provider — manages shared infra objects for handler invocations."""
from __future__ import annotations

from typing import Any


class TgContextProvider:
    """Provides infrastructure objects for TG handler context dicts.

    Long-lived clients (dome_client, redis, gamma_client) are initialised once.
    DB sessions are created per-invocation via get_context().
    """

    def __init__(
        self,
        dome_client: Any | None = None,
        redis: Any | None = None,
        gamma_client: Any | None = None,
    ):
        self._dome_client = dome_client
        self._redis = redis
        self._gamma_client = gamma_client

    async def get_context(self, chat_id: int | None = None) -> dict:
        """Build a context dict with a fresh DB session + shared clients."""
        from db.postgres import AsyncSessionLocal

        db_session = AsyncSessionLocal()
        return {
            "source": "telegram",
            "chat_id": chat_id,
            "db_session": db_session,
            "dome_client": self._dome_client,
            "redis": self._redis,
            "gamma_client": self._gamma_client,
        }

    @staticmethod
    async def cleanup_context(context: dict) -> None:
        """Close the per-request DB session."""
        db = context.get("db_session")
        if db:
            await db.close()
