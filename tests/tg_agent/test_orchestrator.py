import pytest
from unittest.mock import AsyncMock, MagicMock
from tg_agent.orchestrator import AgentOrchestrator


@pytest.mark.asyncio
async def test_handle_natural_language():
    mock_parser = AsyncMock()
    mock_parser.parse.return_value = {
        "capability": "market_query",
        "params": {"action": "search", "query": "bitcoin"},
        "confidence": 0.95,
    }

    mock_handler = AsyncMock(return_value={"success": True, "markets": [{"question": "BTC 100k?"}]})

    orch = AgentOrchestrator(intent_parser=mock_parser)
    orch.register_handler("market_query", mock_handler)

    result = await orch.handle_message(
        text="show me bitcoin markets",
        user_id="u1",
        context={},
    )

    assert result["success"] is True
    assert "markets" in result


@pytest.mark.asyncio
async def test_handle_structured_invoke():
    mock_handler = AsyncMock(return_value={"success": True, "positions": []})

    orch = AgentOrchestrator(intent_parser=AsyncMock())
    orch.register_handler("portfolio", mock_handler)

    result = await orch.invoke(
        capability="portfolio",
        params={"action": "positions"},
        user_id="u1",
        context={},
    )

    assert result["success"] is True
    mock_handler.assert_called_once()


@pytest.mark.asyncio
async def test_low_confidence_asks_clarification():
    mock_parser = AsyncMock()
    mock_parser.parse.return_value = {
        "capability": "unknown",
        "params": {},
        "confidence": 0.2,
    }

    orch = AgentOrchestrator(intent_parser=mock_parser)
    result = await orch.handle_message(text="asdf", user_id="u1", context={})

    assert result["success"] is False
    assert "clarify" in result.get("error", "").lower() or "understand" in result.get("error", "").lower()
