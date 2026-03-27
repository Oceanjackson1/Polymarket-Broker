import pytest
from unittest.mock import AsyncMock, patch
from tg_agent.handlers.market import handle_market_query


@pytest.mark.asyncio
async def test_market_query_search():
    mock_gamma = AsyncMock()
    mock_gamma.get_markets.return_value = [
        {"condition_id": "abc", "question": "Will BTC hit 100k?", "tokens": [{"price": 0.65}]}
    ]

    result = await handle_market_query(
        params={"query": "bitcoin", "action": "search"},
        gamma_client=mock_gamma,
        dome_client=None,
    )

    assert result["success"] is True
    assert len(result["markets"]) == 1
    assert "BTC" in result["markets"][0]["question"]
