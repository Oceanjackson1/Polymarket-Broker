"""Croo service catalogue + per-service binding/validation.

This module defines a **fine-grained service split**: instead of one Croo
`Service` per `tg_agent` capability (e.g. one big `data_feed` covering 12 feeds),
each (capability, sub-action) pair is its own marketplace product. 39 services
total — see the `SPECS` list at the bottom for the full catalogue.

Each service is described by a `ServiceSpec` carrying:

- a **slug** (`nba_list`, `market_search`, …) — unique internal key persisted
  in `.credentials.json` mapped from `service_id`
- the underlying **capability** name (must match `tg_agent.factory.build_orchestrator()`)
- a **`preset_params` dict** that is automatically injected when dispatching
  the order — buyer never sees these and cannot override them. This is the
  trick that lets one capability (e.g. `data_feed`) be exposed as N independent
  services, each with its own `(feed, action)` pair.
- **`extra_required` / `extra_optional`** lists describing which additional
  fields the buyer is allowed to send in the negotiation `requirements` JSON
- pricing (defaults to **100 base units = 0.0001 USDC**) and SLA

`validate_against_binding()` and `merge_params()` are consumed by `dispatcher.py`:

  spec = SPECS_BY_SLUG[slug]
  validate_against_binding(spec, buyer_req)   # raises on schema violation
  final_params = merge_params(spec, buyer_req)  # preset always wins
  validate_requirement(spec.capability, final_params)  # capability-level safety net
  await orchestrator.invoke(spec.capability, final_params, ...)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# ──────────────────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────────────────

# Capability names — must match tg_agent.factory.build_orchestrator() registrations
CAP_MARKET_QUERY = "market_query"
CAP_DATA_FEED = "data_feed"
CAP_STRATEGY = "strategy"
CAP_ANALYSIS = "analysis"

# Allowed feed domains for data_feed (mirrors tg_agent.factory)
DATA_FEED_DOMAINS = [
    "nba", "btc", "crypto", "weather", "sports", "sports_odds",
    "dome_markets", "dome_arbitrage", "dome_wallets", "dome_crypto",
    "dome_events", "kalshi",
]

# Strategy actions exposed via Croo. `positions` and `execute` are explicitly NOT
# whitelisted because they are user-scoped and would leak/burn paid orders.
STRATEGY_ALLOWED_ACTIONS = {"list", "scan"}

# Market query actions
MARKET_QUERY_ALLOWED_ACTIONS = {"search", "detail"}

# Analysis actions
ANALYSIS_ALLOWED_ACTIONS = {"ask", "scan"}

# Default per-service price: 0.0001 USDC = 100 base units (USDC = 6 decimals)
DEFAULT_PRICE_BASE_UNITS = 100


class RequirementValidationError(ValueError):
    """Raised when a buyer-supplied requirement does not match the service schema."""


# ──────────────────────────────────────────────────────────────────────────────
#  ServiceSpec dataclass
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ServiceSpec:
    """Single Croo service definition for the fine-grained split."""
    slug: str                                           # internal unique key
    capability: str                                     # tg_agent capability name
    name: str                                           # marketplace display name
    description: str
    preset_params: dict = field(default_factory=dict)   # fixed routing params
    extra_required: list[str] = field(default_factory=list)
    extra_optional: list[str] = field(default_factory=list)
    price_base_units: int = DEFAULT_PRICE_BASE_UNITS
    sla_minutes: int = 1
    order_type: str = "one_time"
    deliverable_type: str = "text"

    def price_str(self) -> str:
        return str(self.price_base_units)

    def requirement_schema_json(self) -> str:
        """Build a JSON-schema-style string for the buyer-facing requirements."""
        properties: dict[str, dict] = {}
        for k in self.extra_required + self.extra_optional:
            properties[k] = {"type": "string"}
        schema = {
            "type": "object",
            "properties": properties,
            "required": list(self.extra_required),
            "additionalProperties": False,
        }
        return json.dumps(schema, ensure_ascii=False)

    def example_requirement(self) -> dict:
        """Build a minimal example requirements payload for buyer_smoke / docs."""
        return {k: _EXAMPLE_VALUES.get(k, f"<{k}>") for k in self.extra_required}


# Example placeholder values used by `example_requirement()` (buyer_smoke).
# Picked to be non-trivial but unlikely to fail validation downstream.
_EXAMPLE_VALUES: dict[str, str] = {
    "query": "bitcoin",
    "market_id": "0x...",
    "question": "What is the BTC market sentiment right now?",
    "game_id": "0021400001",
    "timeframe": "24H",
    "symbol": "BTC",
    "date": "2026-04-08",
    "city": "New York City",
    "sport": "basketball_nba",
    "wallet_address": "0x0000000000000000000000000000000000000000",
    "market_slug": "trump-2024-election",
    "ticker": "DUMMY-TICKER",
    "min_bias_bps": "300",
    "min_spread_bps": "50",
    "category": "crypto",
    "source": "binance",
}


# ──────────────────────────────────────────────────────────────────────────────
#  39-service catalogue
# ──────────────────────────────────────────────────────────────────────────────

SPECS: list[ServiceSpec] = [
    # ── Market (2) ────────────────────────────────────────────────────────────
    ServiceSpec(
        slug="market_search",
        capability=CAP_MARKET_QUERY,
        name="Polymarket Market Search",
        description=(
            "Search Polymarket prediction markets by keyword via the Gamma API. "
            "Returns the top 10 matches with `condition_id`, `question`, and best price."
        ),
        preset_params={"action": "search"},
        extra_required=["query"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="market_detail",
        capability=CAP_MARKET_QUERY,
        name="Polymarket Market Detail",
        description=(
            "Fetch the full Polymarket market object (question, outcomes, prices, tags, "
            "expiry, volume, …) by `market_id`."
        ),
        preset_params={"action": "detail"},
        extra_required=["market_id"],
        sla_minutes=1,
    ),

    # ── Strategy (2) ──────────────────────────────────────────────────────────
    ServiceSpec(
        slug="strategy_list",
        capability=CAP_STRATEGY,
        name="Polymarket Trading Strategies List",
        description=(
            "List the trading strategies offered by Polymarket Broker (currently: "
            "convergence arbitrage). Returns slug, name, description, and tier."
        ),
        preset_params={"action": "list"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="strategy_scan_convergence",
        capability=CAP_STRATEGY,
        name="Convergence Arbitrage Scanner",
        description=(
            "Scan active Polymarket markets for convergence-arbitrage opportunities — "
            "markets with implied probability >= 95% and expiry within 3 days. Returns "
            "a ranked list with edge in basis points."
        ),
        preset_params={"action": "scan"},
        sla_minutes=3,
    ),

    # ── Analysis (2) ──────────────────────────────────────────────────────────
    ServiceSpec(
        slug="analysis_ask",
        capability=CAP_ANALYSIS,
        name="AI Market Q&A (DeepSeek)",
        description=(
            "Ask a natural-language question about prediction markets, crypto, sports, "
            "or trading. Powered by DeepSeek; returns a concise data-driven answer."
        ),
        preset_params={"action": "ask"},
        extra_required=["question"],
        sla_minutes=5,
    ),
    ServiceSpec(
        slug="analysis_scan",
        capability=CAP_ANALYSIS,
        name="AI Mispricing Opportunity Scanner",
        description=(
            "Scan active Polymarket markets for AI-detected mispricing opportunities. "
            "Returns a ranked list with reasoning and confidence."
        ),
        preset_params={"action": "scan"},
        extra_optional=["category"],
        sla_minutes=5,
    ),

    # ── Data Feed: NBA (3) ────────────────────────────────────────────────────
    ServiceSpec(
        slug="nba_list",
        capability=CAP_DATA_FEED,
        name="NBA — Today's Games",
        description=(
            "List today's NBA games with live scores, quarter, and time remaining. "
            "No buyer input required."
        ),
        preset_params={"feed": "nba", "action": "list"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="nba_detail",
        capability=CAP_DATA_FEED,
        name="NBA — Game Detail",
        description="Fetch a single NBA game's detail by `game_id`.",
        preset_params={"feed": "nba", "action": "detail"},
        extra_required=["game_id"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="nba_fusion",
        capability=CAP_DATA_FEED,
        name="NBA — Game + Polymarket Win Probability Fusion",
        description=(
            "Fuse NBA game state with the corresponding Polymarket win probabilities "
            "and surface the bias signal (AI direction + magnitude in bps)."
        ),
        preset_params={"feed": "nba", "action": "fusion"},
        extra_required=["game_id"],
        sla_minutes=1,
    ),

    # ── Data Feed: BTC (3) ────────────────────────────────────────────────────
    ServiceSpec(
        slug="btc_list",
        capability=CAP_DATA_FEED,
        name="BTC — Latest Predictions Snapshot",
        description=(
            "Latest BTC up/down prediction snapshots across all timeframes (1H, 4H, 24H, …) "
            "from the Polymarket Broker DB."
        ),
        preset_params={"feed": "btc", "action": "list"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="btc_detail",
        capability=CAP_DATA_FEED,
        name="BTC — Predictions History",
        description="Up to 20 historical BTC snapshots filtered by `timeframe`.",
        preset_params={"feed": "btc", "action": "detail"},
        extra_required=["timeframe"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="btc_fusion",
        capability=CAP_DATA_FEED,
        name="BTC — Prediction + Crypto Derivatives Fusion",
        description=(
            "Latest BTC prediction fused with crypto derivatives signals (funding rate, "
            "open interest, taker buy ratio, fear & greed index)."
        ),
        preset_params={"feed": "btc", "action": "fusion"},
        extra_required=["timeframe"],
        sla_minutes=1,
    ),

    # ── Data Feed: Crypto Derivatives (5) ─────────────────────────────────────
    ServiceSpec(
        slug="crypto_overview",
        capability=CAP_DATA_FEED,
        name="Crypto Derivatives — Overview",
        description=(
            "Complete crypto derivatives snapshot for a symbol (default BTC): funding, "
            "OI, liquidations, taker ratios, and sentiment."
        ),
        preset_params={"feed": "crypto", "action": "overview"},
        extra_optional=["symbol"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="crypto_funding",
        capability=CAP_DATA_FEED,
        name="Crypto Derivatives — Funding Rates",
        description="Funding rates with per-exchange breakdown for a given symbol.",
        preset_params={"feed": "crypto", "action": "funding"},
        extra_optional=["symbol"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="crypto_oi",
        capability=CAP_DATA_FEED,
        name="Crypto Derivatives — Open Interest",
        description="Open interest with 1h/4h/24h percentage changes.",
        preset_params={"feed": "crypto", "action": "oi"},
        extra_optional=["symbol"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="crypto_liquidations",
        capability=CAP_DATA_FEED,
        name="Crypto Derivatives — Liquidations",
        description="Liquidation volumes broken down by 1h/4h/24h and direction (long/short).",
        preset_params={"feed": "crypto", "action": "liquidations"},
        extra_optional=["symbol"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="crypto_sentiment",
        capability=CAP_DATA_FEED,
        name="Crypto — Fear & Greed Index",
        description="Latest fear & greed index value.",
        preset_params={"feed": "crypto", "action": "sentiment"},
        extra_optional=["symbol"],
        sla_minutes=1,
    ),

    # ── Data Feed: Weather (3) ────────────────────────────────────────────────
    ServiceSpec(
        slug="weather_dates",
        capability=CAP_DATA_FEED,
        name="Polymarket Weather Markets — Available Dates",
        description="List all available weather event dates with city counts.",
        preset_params={"feed": "weather", "action": "dates"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="weather_cities",
        capability=CAP_DATA_FEED,
        name="Polymarket Weather Markets — Cities by Date",
        description="List cities with weather events for a given date, sorted by max bias.",
        preset_params={"feed": "weather", "action": "cities"},
        extra_required=["date"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="weather_fusion",
        capability=CAP_DATA_FEED,
        name="Polymarket Weather Markets — Bias Fusion",
        description=(
            "Fuse weather event with market bias signal and prediction bins for a "
            "specific city/date pair."
        ),
        preset_params={"feed": "weather", "action": "fusion"},
        extra_required=["date", "city"],
        sla_minutes=1,
    ),

    # ── Data Feed: Sports (2) ─────────────────────────────────────────────────
    ServiceSpec(
        slug="sports_categories",
        capability=CAP_DATA_FEED,
        name="Polymarket Sports — Active Categories",
        description="List all sports with active prediction-market events and counts.",
        preset_params={"feed": "sports", "action": "categories"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="sports_events",
        capability=CAP_DATA_FEED,
        name="Polymarket Sports — Events by Category",
        description="List active sports events for a given sport slug (up to 20).",
        preset_params={"feed": "sports", "action": "list"},
        extra_required=["sport"],
        sla_minutes=1,
    ),

    # ── Data Feed: Sports Odds (4) ────────────────────────────────────────────
    ServiceSpec(
        slug="sports_odds_sports",
        capability=CAP_DATA_FEED,
        name="Sports Odds — Tracked Sports",
        description="List sports tracked by The Odds API with event counts.",
        preset_params={"feed": "sports_odds", "action": "sports"},
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="sports_odds_bookmaker",
        capability=CAP_DATA_FEED,
        name="Sports Odds — Bookmaker vs Polymarket",
        description=(
            "Bookmaker odds for a sport vs the corresponding Polymarket implied "
            "probability, with bias direction and magnitude (up to 20)."
        ),
        preset_params={"feed": "sports_odds", "action": "odds"},
        extra_required=["sport"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="sports_odds_scores",
        capability=CAP_DATA_FEED,
        name="Sports Odds — Live Scores",
        description="Live game scores for a sport from The Odds API (up to 20).",
        preset_params={"feed": "sports_odds", "action": "scores"},
        extra_required=["sport"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="sports_odds_opportunities",
        capability=CAP_DATA_FEED,
        name="Sports Odds — Bias Arbitrage Opportunities",
        description=(
            "Cross-sport bias arbitrage opportunities (bookmaker vs Polymarket) above "
            "a configurable bias threshold (default 500 bps)."
        ),
        preset_params={"feed": "sports_odds", "action": "opportunities"},
        extra_optional=["min_bias_bps"],
        sla_minutes=1,
    ),

    # ── Data Feed: Dome Markets (2) ───────────────────────────────────────────
    ServiceSpec(
        slug="dome_markets_list",
        capability=CAP_DATA_FEED,
        name="Dome — Polymarket Markets Snapshot",
        description=(
            "Latest market snapshots from the Dome integration. Optionally filter by "
            "`market_slug` or search `query`."
        ),
        preset_params={"feed": "dome_markets", "action": "list"},
        extra_optional=["market_slug", "query"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="dome_markets_candles",
        capability=CAP_DATA_FEED,
        name="Dome — Polymarket Markets Candlesticks",
        description="60-item OHLC candlestick history for a Polymarket market via Dome.",
        preset_params={"feed": "dome_markets", "action": "candlesticks"},
        extra_required=["market_slug"],
        sla_minutes=1,
    ),

    # ── Data Feed: Dome Arbitrage (2) ─────────────────────────────────────────
    ServiceSpec(
        slug="dome_arb_spreads",
        capability=CAP_DATA_FEED,
        name="Polymarket–Kalshi Spreads",
        description=(
            "Latest cross-platform spreads between Polymarket and Kalshi for matched "
            "markets, with optional minimum spread filter."
        ),
        preset_params={"feed": "dome_arbitrage", "action": "spreads"},
        extra_optional=["min_spread_bps"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="dome_arb_opportunities",
        capability=CAP_DATA_FEED,
        name="Polymarket–Kalshi Arbitrage Opportunities",
        description=(
            "Exploitable Polymarket–Kalshi arbitrage opportunities (default min spread "
            "50 bps)."
        ),
        preset_params={"feed": "dome_arbitrage", "action": "opportunities"},
        extra_optional=["min_spread_bps"],
        sla_minutes=1,
    ),

    # ── Data Feed: Dome Wallets (2) ───────────────────────────────────────────
    ServiceSpec(
        slug="dome_wallet_positions",
        capability=CAP_DATA_FEED,
        name="Dome — Wallet Position Snapshots",
        description="Latest wallet position snapshots for a tracked Polymarket address.",
        preset_params={"feed": "dome_wallets", "action": "positions"},
        extra_required=["wallet_address"],
        sla_minutes=1,
    ),
    ServiceSpec(
        slug="dome_wallet_pnl",
        capability=CAP_DATA_FEED,
        name="Dome — Wallet PnL History",
        description="Up to 30 historical PnL snapshots for a tracked Polymarket wallet.",
        preset_params={"feed": "dome_wallets", "action": "pnl"},
        extra_required=["wallet_address"],
        sla_minutes=1,
    ),

    # ── Data Feed: Dome Crypto (1) ────────────────────────────────────────────
    ServiceSpec(
        slug="dome_crypto_price",
        capability=CAP_DATA_FEED,
        name="Live Crypto Prices via Dome",
        description=(
            "Live crypto price for a symbol (default BTC) sourced from Dome — choose "
            "between Binance and Chainlink as the upstream feed."
        ),
        preset_params={"feed": "dome_crypto"},
        extra_optional=["symbol", "source"],
        sla_minutes=1,
    ),

    # ── Data Feed: Dome Events (2) ────────────────────────────────────────────
    ServiceSpec(
        slug="dome_events_list",
        capability=CAP_DATA_FEED,
        name="Dome — Events List",
        description="Latest 20 events from the Dome `/events` endpoint.",
        preset_params={"feed": "dome_events", "action": "list"},
        sla_minutes=2,
    ),
    ServiceSpec(
        slug="dome_events_activity",
        capability=CAP_DATA_FEED,
        name="Dome — Activity Stream",
        description="Latest 20 activity records from the Dome `/activity` endpoint.",
        preset_params={"feed": "dome_events", "action": "activity"},
        sla_minutes=2,
    ),

    # ── Data Feed: Kalshi (4) ─────────────────────────────────────────────────
    ServiceSpec(
        slug="kalshi_markets",
        capability=CAP_DATA_FEED,
        name="Kalshi — Markets Search",
        description="Search Kalshi markets via Dome (up to 20 results, optional query filter).",
        preset_params={"feed": "kalshi", "action": "markets"},
        extra_optional=["query"],
        sla_minutes=2,
    ),
    ServiceSpec(
        slug="kalshi_price",
        capability=CAP_DATA_FEED,
        name="Kalshi — Market Price",
        description="Current price for a Kalshi ticker via Dome.",
        preset_params={"feed": "kalshi", "action": "price"},
        extra_required=["ticker"],
        sla_minutes=2,
    ),
    ServiceSpec(
        slug="kalshi_trades",
        capability=CAP_DATA_FEED,
        name="Kalshi — Recent Trades",
        description="Up to 20 recent trades for a Kalshi ticker via Dome.",
        preset_params={"feed": "kalshi", "action": "trades"},
        extra_required=["ticker"],
        sla_minutes=2,
    ),
    ServiceSpec(
        slug="kalshi_orderbook",
        capability=CAP_DATA_FEED,
        name="Kalshi — Orderbook Snapshot",
        description="Up to 10 orderbook snapshots for a Kalshi ticker via Dome.",
        preset_params={"feed": "kalshi", "action": "orderbook"},
        extra_required=["ticker"],
        sla_minutes=2,
    ),
]


# Sanity check on import — fail loud if we ever introduce a duplicate slug.
def _build_index() -> dict[str, ServiceSpec]:
    index: dict[str, ServiceSpec] = {}
    for spec in SPECS:
        if spec.slug in index:
            raise RuntimeError(f"Duplicate ServiceSpec slug: {spec.slug!r}")
        index[spec.slug] = spec
    return index


SPECS_BY_SLUG: dict[str, ServiceSpec] = _build_index()


# ──────────────────────────────────────────────────────────────────────────────
#  Public API consumed by setup_cli + dispatcher + buyer_smoke
# ──────────────────────────────────────────────────────────────────────────────

def get_service_specs() -> list[ServiceSpec]:
    """Canonical ordered list of services to register on Croo."""
    return list(SPECS)


def get_spec(slug: str) -> ServiceSpec:
    """Lookup a spec by slug; raises KeyError on miss."""
    return SPECS_BY_SLUG[slug]


def parse_requirement(requirement: str | dict | None) -> dict:
    """Parse a requirement payload (JSON string from Croo or already-decoded dict)."""
    if requirement is None or requirement == "":
        return {}
    if isinstance(requirement, dict):
        return requirement
    if isinstance(requirement, str):
        try:
            data = json.loads(requirement)
        except json.JSONDecodeError as exc:
            raise RequirementValidationError(f"Requirement is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise RequirementValidationError("Requirement JSON must decode to an object")
        return data
    raise RequirementValidationError(f"Unsupported requirement type: {type(requirement).__name__}")


def validate_against_binding(spec: ServiceSpec, buyer_req: dict) -> None:
    """Per-service requirement validation.

    Three checks:
      1. Buyer is not allowed to send any field that's already in `preset_params`
         (those are routing fields the seller controls).
      2. All `extra_required` fields must be present and non-empty.
      3. No unexpected fields outside `extra_required ∪ extra_optional`.
    """
    if not isinstance(buyer_req, dict):
        raise RequirementValidationError("buyer requirements must decode to a JSON object")

    forbidden = set(spec.preset_params.keys()) & set(buyer_req.keys())
    if forbidden:
        raise RequirementValidationError(
            f"buyer cannot override preset routing fields for service {spec.slug!r}: "
            f"{sorted(forbidden)}"
        )

    missing: list[str] = []
    for k in spec.extra_required:
        v = buyer_req.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            missing.append(k)
    if missing:
        raise RequirementValidationError(
            f"service {spec.slug!r} requires fields: {sorted(missing)}"
        )

    allowed = set(spec.extra_required) | set(spec.extra_optional)
    unexpected = set(buyer_req.keys()) - allowed
    if unexpected:
        raise RequirementValidationError(
            f"service {spec.slug!r} does not accept fields: {sorted(unexpected)} "
            f"(allowed: {sorted(allowed) or '(none)'})"
        )


def merge_params(spec: ServiceSpec, buyer_req: dict) -> dict[str, Any]:
    """Merge buyer requirements with the service preset.

    Preset always wins (placed last in the dict spread). Buyer fields outside
    `extra_required ∪ extra_optional` are dropped, even if they slipped through
    validation, as a defence-in-depth measure.
    """
    allowed = set(spec.extra_required) | set(spec.extra_optional)
    cleaned = {k: v for k, v in buyer_req.items() if k in allowed}
    return {**cleaned, **spec.preset_params}


def validate_requirement(capability: str, params: dict) -> dict:
    """Capability-level safety net validation.

    Runs after `validate_against_binding` + `merge_params` as a second line of
    defence. Mirrors the original capability-scoped validation rules so the
    handler-facing params are always within the contract each handler expects.
    """
    if capability == CAP_MARKET_QUERY:
        action = params.get("action")
        if action not in MARKET_QUERY_ALLOWED_ACTIONS:
            raise RequirementValidationError(
                f"market_query.action must be one of {sorted(MARKET_QUERY_ALLOWED_ACTIONS)}, "
                f"got {action!r}"
            )
        if action == "search" and not params.get("query"):
            raise RequirementValidationError("market_query.search requires `query`")
        if action == "detail" and not params.get("market_id"):
            raise RequirementValidationError("market_query.detail requires `market_id`")
        return params

    if capability == CAP_DATA_FEED:
        feed = params.get("feed")
        if feed not in DATA_FEED_DOMAINS:
            raise RequirementValidationError(
                f"data_feed.feed must be one of {DATA_FEED_DOMAINS}, got {feed!r}"
            )
        return params

    if capability == CAP_STRATEGY:
        action = params.get("action")
        if action not in STRATEGY_ALLOWED_ACTIONS:
            raise RequirementValidationError(
                f"strategy.action must be one of {sorted(STRATEGY_ALLOWED_ACTIONS)} "
                f"(action {action!r} is not exposed via Croo)"
            )
        return params

    if capability == CAP_ANALYSIS:
        action = params.get("action")
        if action not in ANALYSIS_ALLOWED_ACTIONS:
            raise RequirementValidationError(
                f"analysis.action must be one of {sorted(ANALYSIS_ALLOWED_ACTIONS)}, "
                f"got {action!r}"
            )
        if action == "ask" and not params.get("question"):
            raise RequirementValidationError("analysis.ask requires `question`")
        return params

    raise RequirementValidationError(f"Unknown capability: {capability!r}")


# ──────────────────────────────────────────────────────────────────────────────
#  Backwards-compat shim — old `requirement_to_params` function
# ──────────────────────────────────────────────────────────────────────────────

def requirement_to_params(capability: str, requirement: dict) -> dict[str, Any]:
    """Legacy helper kept only so existing imports / tests don't break.

    NEW CODE should call `merge_params(spec, buyer_req)` directly with the
    correct ServiceSpec — this function has no notion of `preset_params` and
    therefore cannot route to the right (feed, action) pair.
    """
    if capability == CAP_MARKET_QUERY:
        return {
            "action": requirement.get("action"),
            "query": requirement.get("query", ""),
            "market_id": requirement.get("market_id", ""),
        }
    if capability == CAP_DATA_FEED:
        return {k: requirement.get(k) for k in (
            "feed", "action", "symbol", "sport", "game_id",
            "timeframe", "wallet_address", "date", "query",
            "market_slug", "ticker", "city", "min_bias_bps",
            "min_spread_bps", "source",
        ) if requirement.get(k) is not None}
    if capability == CAP_STRATEGY:
        return {"action": requirement.get("action")}
    if capability == CAP_ANALYSIS:
        return {
            "action": requirement.get("action"),
            "question": requirement.get("question", ""),
            "category": requirement.get("category", ""),
        }
    raise RequirementValidationError(f"Unknown capability: {capability!r}")
