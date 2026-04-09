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
        description="Cancel an existing order or all open orders",
        parameters={"order_id": {"type": "string"}, "cancel_all": {"type": "boolean"}},
        examples=["Cancel order xyz", "Cancel all orders"],
    ))
    registry.register(Capability(
        name="portfolio",
        description="View positions, balance, P&L, and order history",
        parameters={"action": {"type": "string"}, "status": {"type": "string"}},
        examples=["What are my positions?", "Show my balance", "My PnL", "Show my orders"],
    ))
    registry.register(Capability(
        name="analysis",
        description="AI-powered market analysis and Q&A",
        parameters={"action": {"type": "string"}, "question": {"type": "string"}, "market_id": {"type": "string"}},
        examples=["Analyze the Trump market", "What markets are mispriced?"],
    ))
    registry.register(Capability(
        name="strategy",
        description="Automated trading strategies: scan convergence opportunities, view positions",
        parameters={"action": {"type": "string"}, "strategy_name": {"type": "string"}},
        examples=["Show convergence opportunities", "List strategies", "My convergence positions"],
    ))
    registry.register(Capability(
        name="data_feed",
        description="Query data: NBA, BTC, crypto derivatives, weather, sports, sports odds, Kalshi, arbitrage, wallets, Dome markets",
        parameters={
            "feed": {"type": "string", "enum": [
                "nba", "btc", "crypto", "weather", "sports", "sports_odds",
                "dome_markets", "dome_arbitrage", "dome_wallets", "dome_crypto",
                "dome_events", "kalshi",
            ]},
            "action": {"type": "string"},
            "symbol": {"type": "string"},
            "sport": {"type": "string"},
            "game_id": {"type": "string"},
            "timeframe": {"type": "string"},
            "wallet_address": {"type": "string"},
            "date": {"type": "string"},
            "query": {"type": "string"},
        },
        examples=[
            "Show me NBA games today",
            "BTC 5m fusion",
            "ETH funding rates",
            "Weather dates",
            "Kalshi markets Trump",
            "Arbitrage opportunities",
            "Sports odds basketball_nba",
            "Bias opportunities",
        ],
    ))
    return registry


def build_orchestrator(ai_client: Any, model: str = "deepseek-chat") -> AgentOrchestrator:
    parser = IntentParser(ai_client=ai_client, model=model)
    orch = AgentOrchestrator(intent_parser=parser)

    from tg_agent.handlers.market import handle_market_query
    from tg_agent.handlers.order import handle_place_order
    from tg_agent.handlers.cancel_order import handle_cancel_order
    from tg_agent.handlers.portfolio import handle_portfolio
    from tg_agent.handlers.analysis import handle_analysis
    from tg_agent.handlers.data_feed import handle_data_feed
    from tg_agent.handlers.strategy import handle_strategy

    async def _market_handler(params, user_id, context):
        return await handle_market_query(
            params=params,
            gamma_client=context.get("gamma_client"),
            dome_client=context.get("dome_client"),
        )

    async def _order_handler(params, user_id, context):
        return await handle_place_order(
            params=params,
            db_session=context.get("db_session"),
            user_id=user_id,
        )

    async def _cancel_order_handler(params, user_id, context):
        return await handle_cancel_order(
            params=params,
            db_session=context.get("db_session"),
            user_id=user_id,
        )

    async def _portfolio_handler(params, user_id, context):
        return await handle_portfolio(
            params=params,
            db_session=context.get("db_session"),
            user_id=user_id,
        )

    async def _analysis_handler(params, user_id, context):
        return await handle_analysis(
            params=params,
            redis=context.get("redis"),
            user_id=user_id,
        )

    async def _data_feed_handler(params, user_id, context):
        return await handle_data_feed(
            params=params,
            db_session=context.get("db_session"),
            dome_client=context.get("dome_client"),
            gamma_client=context.get("gamma_client"),
            user_id=user_id,
        )

    async def _strategy_handler(params, user_id, context):
        return await handle_strategy(
            params=params,
            db_session=context.get("db_session"),
            gamma_client=context.get("gamma_client"),
            user_id=user_id,
        )

    orch.register_handler("market_query", _market_handler)
    orch.register_handler("place_order", _order_handler)
    orch.register_handler("cancel_order", _cancel_order_handler)
    orch.register_handler("portfolio", _portfolio_handler)
    orch.register_handler("analysis", _analysis_handler)
    orch.register_handler("data_feed", _data_feed_handler)
    orch.register_handler("strategy", _strategy_handler)
    return orch
