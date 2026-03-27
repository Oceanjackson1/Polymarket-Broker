import pytest
from api.agent.schemas import InvokeRequest, InvokeResponse, CapabilityInfo, MessageRequest


def test_invoke_request_schema():
    body = {
        "capability": "market_query",
        "params": {"action": "search", "query": "bitcoin"},
    }
    req = InvokeRequest(**body)
    assert req.capability == "market_query"


def test_invoke_response_schema():
    resp = InvokeResponse(success=True, data={"markets": []})
    assert resp.success is True


def test_capability_info_schema():
    cap = CapabilityInfo(
        name="market_query",
        description="Query markets",
        parameters={"query": {"type": "string"}},
        examples=["Search bitcoin"],
    )
    assert cap.name == "market_query"


def test_message_request_schema():
    req = MessageRequest(message="show me bitcoin markets")
    assert req.message == "show me bitcoin markets"
