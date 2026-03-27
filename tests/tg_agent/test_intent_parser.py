import pytest
import json
from unittest.mock import AsyncMock
from tg_agent.intent_parser import IntentParser


@pytest.mark.asyncio
async def test_parse_market_search():
    mock_ai = AsyncMock()
    mock_ai.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps({
            "capability": "market_query",
            "params": {"action": "search", "query": "bitcoin"},
            "confidence": 0.95,
        })))]
    )

    parser = IntentParser(ai_client=mock_ai, model="deepseek-chat")
    intent = await parser.parse("Show me bitcoin markets")

    assert intent["capability"] == "market_query"
    assert intent["params"]["query"] == "bitcoin"
    assert intent["confidence"] >= 0.8


@pytest.mark.asyncio
async def test_parse_order():
    mock_ai = AsyncMock()
    mock_ai.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps({
            "capability": "place_order",
            "params": {"token_id": "abc123", "side": "BUY", "price": 0.65, "size": 100},
            "confidence": 0.9,
        })))]
    )

    parser = IntentParser(ai_client=mock_ai, model="deepseek-chat")
    intent = await parser.parse("Buy 100 shares of YES at 0.65 on market abc123")

    assert intent["capability"] == "place_order"
    assert intent["params"]["side"] == "BUY"


@pytest.mark.asyncio
async def test_parse_unknown_returns_fallback():
    mock_ai = AsyncMock()
    mock_ai.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content=json.dumps({
            "capability": "unknown",
            "params": {},
            "confidence": 0.2,
        })))]
    )

    parser = IntentParser(ai_client=mock_ai, model="deepseek-chat")
    intent = await parser.parse("Tell me a joke")

    assert intent["capability"] == "unknown"
    assert intent["confidence"] < 0.5
