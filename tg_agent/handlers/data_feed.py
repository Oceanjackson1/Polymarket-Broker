"""Data feed handler — routes data_feed capability to 12 domain sub-handlers.

Each sub-handler mirrors the DB query logic from the corresponding API router,
bypassing the HTTP layer for direct SQLAlchemy access.
"""
from __future__ import annotations
from datetime import datetime, UTC, date
from typing import Any

from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession


# ══════════════════════════════════════════════════════════════
#  Main dispatcher
# ══════════════════════════════════════════════════════════════

async def handle_data_feed(
    params: dict[str, Any],
    db_session: Any,
    dome_client: Any | None = None,
    gamma_client: Any | None = None,
    user_id: str = "",
) -> dict:
    """Route to the appropriate feed sub-handler."""
    feed = params.get("feed", "")
    handler = _FEED_HANDLERS.get(feed)
    if not handler:
        available = ", ".join(sorted(_FEED_HANDLERS.keys()))
        return {"success": False, "error": f"Unknown feed: {feed}. Available: {available}"}
    try:
        return await handler(params, db_session, dome_client)
    except Exception as e:
        return {"success": False, "error": f"Feed {feed} error: {e}"}


# ══════════════════════════════════════════════════════════════
#  NBA — DB: NbaGame
# ══════════════════════════════════════════════════════════════

async def _handle_nba(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.nba.models import NbaGame

    action = params.get("action", "list")
    game_id = params.get("game_id")

    if action == "detail" and game_id:
        game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
        if not game:
            return {"success": False, "error": f"NBA game {game_id} not found."}
        return {
            "success": True, "_type": "nba_detail",
            "data": _nba_game_dict(game),
        }

    if action == "fusion" and game_id:
        game = await db.scalar(select(NbaGame).where(NbaGame.game_id == game_id))
        if not game:
            return {"success": False, "error": f"NBA game {game_id} not found."}
        return {
            "success": True, "_type": "nba_fusion",
            "data": {
                **_nba_game_dict(game),
                "polymarket": {
                    "home_win_prob": float(game.home_win_prob) if game.home_win_prob else None,
                    "away_win_prob": float(game.away_win_prob) if game.away_win_prob else None,
                },
                "bias_signal": {
                    "direction": game.bias_direction,
                    "magnitude_bps": game.bias_magnitude_bps,
                },
            },
        }

    # Default: list today's games
    target_date = date.today()
    stmt = (
        select(NbaGame)
        .where(NbaGame.game_date == target_date)
        .order_by(desc(NbaGame.data_updated_at))
        .limit(20)
    )
    result = await db.execute(stmt)
    games = list(result.scalars().all())
    return {
        "success": True, "_type": "nba_games",
        "data": [_nba_game_dict(g) for g in games],
        "date": target_date.isoformat(),
    }


def _nba_game_dict(game) -> dict:
    return {
        "game_id": game.game_id,
        "home_team": game.home_team,
        "away_team": game.away_team,
        "score_home": game.score_home,
        "score_away": game.score_away,
        "quarter": game.quarter,
        "time_remaining": game.time_remaining,
        "game_status": game.game_status,
        "game_date": game.game_date.isoformat() if game.game_date else None,
    }


# ══════════════════════════════════════════════════════════════
#  BTC — DB: BtcSnapshot + CryptoDerivatives
# ══════════════════════════════════════════════════════════════

async def _handle_btc(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.btc.models import BtcSnapshot

    action = params.get("action", "list")
    timeframe = params.get("timeframe")

    if action == "fusion" and timeframe:
        from api.data.crypto.models import CryptoDerivatives

        snap = await db.scalar(
            select(BtcSnapshot)
            .where(BtcSnapshot.timeframe == timeframe)
            .order_by(desc(BtcSnapshot.recorded_at))
        )
        if not snap:
            return {"success": False, "error": f"No BTC data for {timeframe}."}

        deriv = await db.scalar(
            select(CryptoDerivatives)
            .where(CryptoDerivatives.symbol == "BTC")
            .order_by(desc(CryptoDerivatives.recorded_at))
        )
        derivatives_data = {}
        if deriv:
            derivatives_data = {
                "funding_rate_avg": deriv.funding_rate_avg,
                "oi_total_usd": deriv.oi_total_usd,
                "taker_buy_ratio": deriv.taker_buy_ratio,
                "fear_greed_index": deriv.fear_greed_index,
            }
        return {
            "success": True, "_type": "btc_fusion",
            "data": {
                "timeframe": timeframe,
                "up_prob": snap.prediction_prob,
                "price_usd": snap.price_usd,
                "volume": snap.volume,
                "derivatives": derivatives_data,
                "recorded_at": snap.recorded_at.isoformat(),
            },
        }

    if action == "detail" and timeframe:
        stmt = (
            select(BtcSnapshot)
            .where(BtcSnapshot.timeframe == timeframe)
            .order_by(desc(BtcSnapshot.recorded_at))
            .limit(20)
        )
        result = await db.execute(stmt)
        snaps = list(result.scalars().all())
        return {
            "success": True, "_type": "btc_predictions",
            "data": [_btc_snap_dict(s) for s in snaps],
        }

    # Default: latest across all timeframes
    subq = (
        select(BtcSnapshot.timeframe, func.max(BtcSnapshot.recorded_at).label("max_ts"))
        .group_by(BtcSnapshot.timeframe)
        .subquery()
    )
    stmt = select(BtcSnapshot).join(
        subq,
        (BtcSnapshot.timeframe == subq.c.timeframe) &
        (BtcSnapshot.recorded_at == subq.c.max_ts)
    ).order_by(BtcSnapshot.timeframe)
    result = await db.execute(stmt)
    snaps = list(result.scalars().all())
    return {
        "success": True, "_type": "btc_predictions",
        "data": [_btc_snap_dict(s) for s in snaps],
    }


def _btc_snap_dict(s) -> dict:
    return {
        "timeframe": s.timeframe,
        "prediction_prob": s.prediction_prob,
        "price_usd": s.price_usd,
        "volume": s.volume,
        "market_id": s.market_id,
        "recorded_at": s.recorded_at.isoformat(),
    }


# ══════════════════════════════════════════════════════════════
#  Crypto Derivatives — DB: CryptoDerivatives
# ══════════════════════════════════════════════════════════════

async def _handle_crypto(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.crypto.models import CryptoDerivatives

    action = params.get("action", "overview")
    symbol = (params.get("symbol") or "BTC").upper()

    row = await db.scalar(
        select(CryptoDerivatives)
        .where(CryptoDerivatives.symbol == symbol)
        .order_by(desc(CryptoDerivatives.recorded_at))
    )
    if not row:
        return {"success": False, "error": f"No crypto data for {symbol}."}

    if action == "funding":
        return {
            "success": True, "_type": "crypto_funding",
            "data": {
                "symbol": symbol,
                "funding_rate_avg": row.funding_rate_avg,
                "funding_rate_min": row.funding_rate_min,
                "funding_rate_max": row.funding_rate_max,
                "exchanges": row.funding_rates_json or [],
                "recorded_at": row.recorded_at.isoformat(),
            },
        }

    if action == "oi":
        return {
            "success": True, "_type": "crypto_oi",
            "data": {
                "symbol": symbol,
                "total_usd": row.oi_total_usd,
                "change_1h": row.oi_change_pct_1h,
                "change_4h": row.oi_change_pct_4h,
                "change_24h": row.oi_change_pct_24h,
                "recorded_at": row.recorded_at.isoformat(),
            },
        }

    if action == "liquidations":
        return {
            "success": True, "_type": "crypto_liquidations",
            "data": {
                "symbol": symbol,
                "1h": {"long_usd": row.liq_long_1h_usd, "short_usd": row.liq_short_1h_usd},
                "4h": {"long_usd": row.liq_long_4h_usd, "short_usd": row.liq_short_4h_usd},
                "24h": {"long_usd": row.liq_long_24h_usd, "short_usd": row.liq_short_24h_usd},
                "recorded_at": row.recorded_at.isoformat(),
            },
        }

    if action == "sentiment":
        return {
            "success": True, "_type": "crypto_sentiment",
            "data": {
                "fear_greed_index": row.fear_greed_index,
                "recorded_at": row.recorded_at.isoformat(),
            },
        }

    # Default: overview
    return {
        "success": True, "_type": "crypto_overview",
        "data": {
            "symbol": symbol,
            "funding_rate_avg": row.funding_rate_avg,
            "oi_total_usd": row.oi_total_usd,
            "oi_change_1h": row.oi_change_pct_1h,
            "liq_long_1h_usd": row.liq_long_1h_usd,
            "liq_short_1h_usd": row.liq_short_1h_usd,
            "taker_buy_ratio": row.taker_buy_ratio,
            "taker_sell_ratio": row.taker_sell_ratio,
            "fear_greed_index": row.fear_greed_index,
            "recorded_at": row.recorded_at.isoformat(),
        },
    }


# ══════════════════════════════════════════════════════════════
#  Weather — DB: WeatherEvent
# ══════════════════════════════════════════════════════════════

async def _handle_weather(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.weather.models import WeatherEvent

    action = params.get("action", "dates")
    event_date = params.get("date")
    city = params.get("city")

    if action == "fusion" and event_date and city:
        event = await db.scalar(
            select(WeatherEvent).where(
                WeatherEvent.city == city.lower(),
                WeatherEvent.event_date == event_date,
            )
        )
        if not event:
            return {"success": False, "error": f"No weather event for {city} on {event_date}."}
        return {
            "success": True, "_type": "weather_fusion",
            "data": {
                "city": event.city,
                "date": event.event_date.isoformat(),
                "temp_unit": event.temp_unit,
                "bins": event.bins_json or [],
                "max_bias": {
                    "range": event.max_bias_range,
                    "direction": event.max_bias_direction,
                    "magnitude_bps": event.max_bias_bps,
                },
            },
        }

    if action == "cities" and event_date:
        result = await db.execute(
            select(WeatherEvent)
            .where(WeatherEvent.event_date == event_date)
            .order_by(desc(WeatherEvent.max_bias_bps))
        )
        events = list(result.scalars().all())
        return {
            "success": True, "_type": "weather_cities",
            "data": [
                {
                    "city": e.city,
                    "max_bias_range": e.max_bias_range,
                    "max_bias_direction": e.max_bias_direction,
                    "max_bias_bps": e.max_bias_bps,
                }
                for e in events
            ],
            "date": str(event_date),
        }

    # Default: list dates
    result = await db.execute(
        select(
            WeatherEvent.event_date,
            func.count(func.distinct(WeatherEvent.city)).label("city_count"),
        )
        .group_by(WeatherEvent.event_date)
        .order_by(WeatherEvent.event_date)
    )
    return {
        "success": True, "_type": "weather_dates",
        "data": [
            {"date": r.event_date.isoformat(), "city_count": r.city_count}
            for r in result.all()
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Sports — DB: SportsEvent
# ══════════════════════════════════════════════════════════════

async def _handle_sports(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.sports.models import SportsEvent

    action = params.get("action", "categories")
    sport = params.get("sport")

    if action == "list" and sport:
        stmt = (
            select(SportsEvent)
            .where(SportsEvent.sport_slug == sport, SportsEvent.status == "active")
            .order_by(desc(SportsEvent.data_updated_at))
            .limit(20)
        )
        result = await db.execute(stmt)
        events = list(result.scalars().all())
        return {
            "success": True, "_type": "sports_events",
            "data": [
                {
                    "market_id": e.market_id,
                    "question": e.question,
                    "sport_slug": e.sport_slug,
                    "status": e.status,
                }
                for e in events
            ],
        }

    # Default: categories
    result = await db.execute(
        select(SportsEvent.sport_slug, func.count(SportsEvent.id).label("active_events"))
        .where(SportsEvent.status == "active")
        .group_by(SportsEvent.sport_slug)
        .order_by(SportsEvent.sport_slug)
    )
    return {
        "success": True, "_type": "sports_categories",
        "data": [{"slug": r.sport_slug, "active_events": r.active_events} for r in result.all()],
    }


# ══════════════════════════════════════════════════════════════
#  Sports Odds — DB: SportsOdds / SportsScore
# ══════════════════════════════════════════════════════════════

async def _handle_sports_odds(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.sports.odds_models import SportsOdds, SportsScore

    action = params.get("action", "sports")
    sport = params.get("sport")

    if action == "odds" and sport:
        result = await db.execute(
            select(SportsOdds)
            .where(SportsOdds.sport_key == sport)
            .order_by(desc(SportsOdds.data_updated_at))
            .limit(20)
        )
        rows = list(result.scalars().all())
        return {
            "success": True, "_type": "sports_odds",
            "data": [
                {
                    "event_id": r.event_id,
                    "home_team": r.home_team,
                    "away_team": r.away_team,
                    "home_implied_prob": float(r.home_implied_prob) if r.home_implied_prob else None,
                    "polymarket_prob": float(r.polymarket_prob) if r.polymarket_prob else None,
                    "bias_direction": r.bias_direction,
                    "bias_bps": r.bias_bps,
                }
                for r in rows
            ],
        }

    if action == "scores" and sport:
        result = await db.execute(
            select(SportsScore)
            .where(SportsScore.sport_key == sport)
            .order_by(desc(SportsScore.data_updated_at))
            .limit(20)
        )
        rows = list(result.scalars().all())
        return {
            "success": True, "_type": "sports_scores",
            "data": [
                {
                    "event_id": r.event_id,
                    "home_team": r.home_team,
                    "away_team": r.away_team,
                    "scores": r.scores_json,
                    "completed": r.completed,
                }
                for r in rows
            ],
        }

    if action == "opportunities":
        min_bias = params.get("min_bias_bps", 500)
        result = await db.execute(
            select(SportsOdds)
            .where(
                SportsOdds.bias_bps >= min_bias,
                SportsOdds.polymarket_market_id.isnot(None),
            )
            .order_by(desc(SportsOdds.bias_bps))
            .limit(20)
        )
        rows = list(result.scalars().all())
        return {
            "success": True, "_type": "sports_bias_opportunities",
            "data": [
                {
                    "event_id": r.event_id,
                    "sport_key": r.sport_key,
                    "home_team": r.home_team,
                    "away_team": r.away_team,
                    "bookmaker_prob": float(r.home_implied_prob) if r.home_implied_prob else None,
                    "polymarket_prob": float(r.polymarket_prob) if r.polymarket_prob else None,
                    "bias_direction": r.bias_direction,
                    "bias_bps": r.bias_bps,
                }
                for r in rows
            ],
        }

    # Default: list tracked sports
    result = await db.execute(
        select(SportsOdds.sport_key, func.count(SportsOdds.id).label("event_count"))
        .group_by(SportsOdds.sport_key)
        .order_by(SportsOdds.sport_key)
    )
    return {
        "success": True, "_type": "sports_odds_sports",
        "data": [{"sport_key": r.sport_key, "event_count": r.event_count} for r in result.all()],
    }


# ══════════════════════════════════════════════════════════════
#  Dome Markets — DB: MarketSnapshot
# ══════════════════════════════════════════════════════════════

async def _handle_dome_markets(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.dome.models import MarketSnapshot

    action = params.get("action", "list")
    market_slug = params.get("market_slug") or params.get("query")

    if action == "candlesticks" and market_slug:
        stmt = (
            select(MarketSnapshot)
            .where(MarketSnapshot.market_slug == market_slug, MarketSnapshot.open.isnot(None))
            .order_by(desc(MarketSnapshot.recorded_at))
            .limit(60)
        )
        result = await db.execute(stmt)
        rows = list(result.scalars().all())
        return {
            "success": True, "_type": "dome_candlesticks",
            "data": [
                {
                    "open": float(r.open) if r.open else None,
                    "high": float(r.high) if r.high else None,
                    "low": float(r.low) if r.low else None,
                    "close": float(r.close) if r.close else None,
                    "recorded_at": r.recorded_at.isoformat(),
                }
                for r in reversed(rows)
            ],
            "market_slug": market_slug,
        }

    # Default: latest snapshots
    if market_slug:
        stmt = (
            select(MarketSnapshot)
            .where(MarketSnapshot.market_slug == market_slug)
            .order_by(desc(MarketSnapshot.recorded_at))
            .limit(20)
        )
    else:
        subq = (
            select(
                MarketSnapshot.market_slug,
                func.max(MarketSnapshot.recorded_at).label("max_ts"),
            )
            .group_by(MarketSnapshot.market_slug)
            .subquery()
        )
        stmt = (
            select(MarketSnapshot)
            .join(subq, and_(
                MarketSnapshot.market_slug == subq.c.market_slug,
                MarketSnapshot.recorded_at == subq.c.max_ts,
            ))
            .order_by(desc(MarketSnapshot.recorded_at))
            .limit(20)
        )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return {
        "success": True, "_type": "dome_markets",
        "data": [
            {
                "market_slug": r.market_slug,
                "question": getattr(r, "question", None),
                "price": float(r.close) if r.close else None,
                "volume": getattr(r, "volume", None),
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in rows
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Dome Arbitrage — DB: CrossPlatformSpread
# ══════════════════════════════════════════════════════════════

async def _handle_dome_arb(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.dome.models import CrossPlatformSpread

    action = params.get("action", "spreads")
    min_bps = params.get("min_spread_bps", 0)

    subq = (
        select(
            CrossPlatformSpread.polymarket_slug,
            CrossPlatformSpread.kalshi_ticker,
            func.max(CrossPlatformSpread.recorded_at).label("max_ts"),
        )
        .group_by(CrossPlatformSpread.polymarket_slug, CrossPlatformSpread.kalshi_ticker)
        .subquery()
    )

    if action == "opportunities":
        min_bps = params.get("min_spread_bps", 50)
        stmt = (
            select(CrossPlatformSpread)
            .join(subq, and_(
                CrossPlatformSpread.polymarket_slug == subq.c.polymarket_slug,
                CrossPlatformSpread.kalshi_ticker == subq.c.kalshi_ticker,
                CrossPlatformSpread.recorded_at == subq.c.max_ts,
            ))
            .where(CrossPlatformSpread.spread_bps >= min_bps)
            .order_by(desc(CrossPlatformSpread.spread_bps))
            .limit(10)
        )
    else:
        conditions = [
            CrossPlatformSpread.polymarket_slug == subq.c.polymarket_slug,
            CrossPlatformSpread.kalshi_ticker == subq.c.kalshi_ticker,
            CrossPlatformSpread.recorded_at == subq.c.max_ts,
        ]
        stmt = (
            select(CrossPlatformSpread)
            .join(subq, and_(*conditions))
            .order_by(desc(CrossPlatformSpread.spread_bps))
            .limit(20)
        )

    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    return {
        "success": True,
        "_type": "dome_spreads" if action == "spreads" else "dome_opportunities",
        "data": [
            {
                "polymarket_slug": r.polymarket_slug,
                "kalshi_ticker": r.kalshi_ticker,
                "sport": r.sport,
                "poly_price": float(r.poly_price),
                "kalshi_price": float(r.kalshi_price),
                "spread_bps": r.spread_bps,
                "direction": r.direction,
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in rows
        ],
    }


# ══════════════════════════════════════════════════════════════
#  Dome Wallets — DB: WalletSnapshot
# ══════════════════════════════════════════════════════════════

async def _handle_dome_wallets(params: dict, db: AsyncSession, dome: Any) -> dict:
    from api.data.dome.models import WalletSnapshot

    action = params.get("action", "positions")
    address = params.get("wallet_address", "")

    if not address:
        return {"success": False, "error": "wallet_address is required."}

    if action == "pnl":
        stmt = (
            select(
                WalletSnapshot.recorded_at,
                WalletSnapshot.total_pnl,
                WalletSnapshot.position_count,
            )
            .where(WalletSnapshot.wallet_address == address)
            .order_by(desc(WalletSnapshot.recorded_at))
            .limit(30)
        )
        result = await db.execute(stmt)
        rows = result.all()
        if not rows:
            return {"success": False, "error": f"Wallet {address} not tracked."}
        return {
            "success": True, "_type": "dome_wallet_pnl",
            "data": [
                {
                    "recorded_at": r.recorded_at.isoformat(),
                    "total_pnl": float(r.total_pnl) if r.total_pnl else None,
                    "position_count": r.position_count,
                }
                for r in reversed(rows)
            ],
            "wallet_address": address,
        }

    # Default: positions
    stmt = (
        select(WalletSnapshot)
        .where(WalletSnapshot.wallet_address == address)
        .order_by(desc(WalletSnapshot.recorded_at))
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = list(result.scalars().all())
    if not rows:
        return {"success": False, "error": f"Wallet {address} not tracked."}
    return {
        "success": True, "_type": "dome_wallet_positions",
        "data": [
            {
                "recorded_at": r.recorded_at.isoformat(),
                "total_pnl": float(r.total_pnl) if r.total_pnl else None,
                "position_count": r.position_count,
            }
            for r in rows
        ],
        "wallet_address": address,
    }


# ══════════════════════════════════════════════════════════════
#  Dome Crypto Prices — DomeClient proxy
# ══════════════════════════════════════════════════════════════

async def _handle_dome_crypto(params: dict, db: AsyncSession, dome: Any) -> dict:
    if not dome:
        return {"success": False, "error": "Dome client not configured."}

    symbol = (params.get("symbol") or "btc").lower()
    source = params.get("source", "binance")

    currency_map = {
        "binance": {"btc": "btcusdt", "eth": "ethusdt", "sol": "solusdt"},
        "chainlink": {"btc": "btc/usd", "eth": "eth/usd", "sol": "sol/usd"},
    }
    mapped = currency_map.get(source, {}).get(symbol, symbol)

    try:
        if source == "chainlink":
            resp = await dome.get_chainlink_price(mapped, limit=1)
        else:
            resp = await dome.get_binance_price(mapped, limit=1)

        from core.dome.client import extract_list
        prices = extract_list(resp)
        if not prices:
            return {"success": False, "error": f"No price data for {symbol}."}
        latest = prices[0]
        return {
            "success": True, "_type": "dome_crypto_price",
            "data": {
                "symbol": symbol.upper(),
                "source": source,
                "price": latest.get("value") or latest.get("price"),
                "timestamp": latest.get("timestamp"),
            },
        }
    except Exception as e:
        return {"success": False, "error": f"Dome price error: {e}"}


# ══════════════════════════════════════════════════════════════
#  Dome Events — DomeClient proxy
# ══════════════════════════════════════════════════════════════

async def _handle_dome_events(params: dict, db: AsyncSession, dome: Any) -> dict:
    if not dome:
        return {"success": False, "error": "Dome client not configured."}

    action = params.get("action", "list")

    try:
        if action == "activity":
            resp = await dome.get_activity(limit=20)
            return {"success": True, "_type": "dome_activity", "data": resp}

        resp = await dome.get_events(limit=20)
        return {"success": True, "_type": "dome_events", "data": resp}
    except Exception as e:
        return {"success": False, "error": f"Dome events error: {e}"}


# ══════════════════════════════════════════════════════════════
#  Kalshi — DomeClient proxy
# ══════════════════════════════════════════════════════════════

async def _handle_kalshi(params: dict, db: AsyncSession, dome: Any) -> dict:
    if not dome:
        return {"success": False, "error": "Dome client not configured."}

    action = params.get("action", "markets")
    query = params.get("query")
    ticker = params.get("ticker") or params.get("market_id")

    try:
        if action == "price" and ticker:
            resp = await dome.get_kalshi_price(ticker)
            return {"success": True, "_type": "kalshi_price", "data": resp}

        if action == "trades":
            resp = await dome.get_kalshi_trades(ticker=ticker, limit=20)
            return {"success": True, "_type": "kalshi_trades", "data": resp}

        if action == "orderbook" and ticker:
            resp = await dome.get_kalshi_orderbook_snapshots(ticker, limit=10)
            return {"success": True, "_type": "kalshi_orderbook", "data": resp}

        # Default: list markets
        resp = await dome.get_kalshi_markets(search=query, limit=20)
        return {"success": True, "_type": "kalshi_markets", "data": resp}
    except Exception as e:
        return {"success": False, "error": f"Kalshi error: {e}"}


# ══════════════════════════════════════════════════════════════
#  Feed handler registry
# ══════════════════════════════════════════════════════════════

_FEED_HANDLERS = {
    "nba": _handle_nba,
    "btc": _handle_btc,
    "crypto": _handle_crypto,
    "weather": _handle_weather,
    "sports": _handle_sports,
    "sports_odds": _handle_sports_odds,
    "dome_markets": _handle_dome_markets,
    "dome_arbitrage": _handle_dome_arb,
    "dome_wallets": _handle_dome_wallets,
    "dome_crypto": _handle_dome_crypto,
    "dome_events": _handle_dome_events,
    "kalshi": _handle_kalshi,
}
