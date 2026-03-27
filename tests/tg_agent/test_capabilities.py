import pytest
from tg_agent.capabilities import CapabilityRegistry, Capability


def test_register_and_list():
    registry = CapabilityRegistry()

    cap = Capability(
        name="market_query",
        description="Search and query prediction markets",
        parameters={"query": {"type": "string", "required": True}},
        examples=["What markets are trending?", "Search for Bitcoin markets"],
    )
    registry.register(cap)

    assert "market_query" in registry.list_names()
    assert registry.get("market_query") is cap


def test_get_unknown_returns_none():
    registry = CapabilityRegistry()
    assert registry.get("nonexistent") is None


def test_export_schema():
    registry = CapabilityRegistry()
    registry.register(Capability(
        name="place_order",
        description="Place a trade order",
        parameters={"market_id": {"type": "string"}, "side": {"type": "string"}},
        examples=["Buy YES on Trump winning"],
    ))
    schema = registry.export_schema()
    assert len(schema) == 1
    assert schema[0]["name"] == "place_order"
    assert "parameters" in schema[0]
