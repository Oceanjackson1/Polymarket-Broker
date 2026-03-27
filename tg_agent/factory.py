from __future__ import annotations
from typing import Any
from tg_agent.orchestrator import AgentOrchestrator
from tg_agent.intent_parser import IntentParser
from tg_agent.capabilities import CapabilityRegistry, Capability


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(Capability(
        name="market_query",
        description="Search prediction markets, get details, orderbooks",
        parameters={"action": {"type": "string"}, "query": {"type": "string"}, "market_id": {"type": "string"}},
        examples=["Show me bitcoin markets", "What's the orderbook for abc123?"],
    ))
    registry.register(Capability(
        name="place_order",
        description="Place a buy or sell order on a prediction market",
        parameters={"token_id": {"type": "string"}, "side": {"type": "string"}, "price": {"type": "number"}, "size": {"type": "number"}},
        examples=["Buy 100 YES at 0.65 on market abc"],
    ))
    registry.register(Capability(
        name="cancel_order",
        description="Cancel an existing order",
        parameters={"order_id": {"type": "string"}},
        examples=["Cancel order xyz"],
    ))
    registry.register(Capability(
        name="portfolio",
        description="View positions, balance, and P&L",
        parameters={"action": {"type": "string"}},
        examples=["What are my positions?", "Show my balance"],
    ))
    registry.register(Capability(
        name="analysis",
        description="AI-powered market analysis and Q&A",
        parameters={"action": {"type": "string"}, "question": {"type": "string"}, "market_id": {"type": "string"}},
        examples=["Analyze the Trump market", "What markets are mispriced?"],
    ))
    registry.register(Capability(
        name="data_feed",
        description="Get sports, NBA, BTC, crypto, or weather data",
        parameters={"feed": {"type": "string"}, "query": {"type": "string"}},
        examples=["Show me NBA scores", "BTC price predictions"],
    ))
    return registry


def build_orchestrator(ai_client: Any, model: str = "deepseek-chat") -> AgentOrchestrator:
    parser = IntentParser(ai_client=ai_client, model=model)
    orch = AgentOrchestrator(intent_parser=parser)

    from tg_agent.handlers.market import handle_market_query
    from tg_agent.handlers.order import handle_place_order
    from tg_agent.handlers.portfolio import handle_portfolio
    from tg_agent.handlers.analysis import handle_analysis

    async def _market_handler(params, user_id, context):
        return await handle_market_query(params=params, gamma_client=context.get("gamma_client"), dome_client=context.get("dome_client"))

    async def _order_handler(params, user_id, context):
        return await handle_place_order(params=params, db_session=context.get("db_session"), user_id=user_id)

    async def _portfolio_handler(params, user_id, context):
        return await handle_portfolio(params=params, db_session=context.get("db_session"), user_id=user_id)

    async def _analysis_handler(params, user_id, context):
        return await handle_analysis(params=params, redis=context.get("redis"), user_id=user_id)

    orch.register_handler("market_query", _market_handler)
    orch.register_handler("place_order", _order_handler)
    orch.register_handler("portfolio", _portfolio_handler)
    orch.register_handler("analysis", _analysis_handler)
    return orch
