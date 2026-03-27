import pytest
from unittest.mock import AsyncMock
from tg_agent.factory import build_orchestrator, build_registry

def test_build_registry_has_all_capabilities():
    registry = build_registry()
    names = registry.list_names()
    assert "market_query" in names
    assert "place_order" in names
    assert "portfolio" in names
    assert "analysis" in names
    assert "data_feed" in names

def test_build_orchestrator_has_all_handlers():
    orch = build_orchestrator(ai_client=AsyncMock(), model="test")
    assert "market_query" in orch._handlers
    assert "place_order" in orch._handlers
    assert "portfolio" in orch._handlers
    assert "analysis" in orch._handlers
