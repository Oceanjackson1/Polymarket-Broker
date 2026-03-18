import pytest
from unittest.mock import AsyncMock, patch

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_collectors_disabled_in_test_env(client):
    """DISABLE_COLLECTORS=true means no collector tasks are started."""
    import asyncio
    from core.config import get_settings
    settings = get_settings()
    assert settings.disable_collectors is True

    # Verify no data_pipeline collector tasks are running
    # (checks our specific collector modules, not pytest's own Collector class)
    data_pipeline_running = any(
        "data_pipeline" in repr(t.get_coro())
        for t in asyncio.all_tasks()
    )
    assert not data_pipeline_running, "data_pipeline tasks should not run when DISABLE_COLLECTORS=true"


async def test_data_routers_registered(client):
    """All 3 data routers respond (routes exist)."""
    resp = await client.get("/api/v1/data/sports/categories")
    # No auth → 422 (missing X-API-Key header) proves route exists
    assert resp.status_code == 422

    resp = await client.get("/api/v1/data/nba/games")
    assert resp.status_code == 422

    resp = await client.get("/api/v1/data/btc/predictions")
    assert resp.status_code == 422
