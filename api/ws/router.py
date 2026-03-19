# api/ws/router.py
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from db.postgres import AsyncSessionLocal
from sqlalchemy import select, desc
from api.data.nba.models import NbaGame
from api.data.btc.models import BtcSnapshot
from core.polymarket.clob_client import ClobClient

logger = logging.getLogger(__name__)
router = APIRouter()

_clob = ClobClient()


@router.websocket("/ws/markets/{token_id}")
async def market_orderbook_live(websocket: WebSocket, token_id: str):
    """Stream real-time orderbook for any Polymarket market every 3s."""
    await websocket.accept()
    try:
        while True:
            try:
                book = await _clob.get_orderbook(token_id=token_id)
                mid = await _clob.get_midpoint(token_id=token_id)
                await websocket.send_json({
                    "type": "orderbook_update",
                    "token_id": token_id,
                    "bids": book.get("bids", []),
                    "asks": book.get("asks", []),
                    "midpoint": mid.get("mid", None),
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Upstream error: {e}",
                })
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: markets/{token_id}")
    except Exception as e:
        logger.error(f"WebSocket error markets/{token_id}: {e}")


@router.websocket("/ws/nba/{game_id}/live")
async def nba_live(websocket: WebSocket, game_id: str):
    """Stream live NBA game data — score + odds + bias every 5s."""
    await websocket.accept()
    try:
        while True:
            async with AsyncSessionLocal() as db:
                game = await db.scalar(
                    select(NbaGame).where(NbaGame.game_id == game_id)
                )
                if game:
                    data = {
                        "type": "nba_update",
                        "game_id": game.game_id,
                        "home_team": game.home_team,
                        "away_team": game.away_team,
                        "score_home": game.score_home,
                        "score_away": game.score_away,
                        "quarter": game.quarter,
                        "time_remaining": game.time_remaining,
                        "game_status": game.game_status,
                        "home_win_prob": float(game.home_win_prob) if game.home_win_prob else None,
                        "away_win_prob": float(game.away_win_prob) if game.away_win_prob else None,
                        "bias_direction": game.bias_direction,
                        "bias_magnitude_bps": game.bias_magnitude_bps,
                        "data_updated_at": game.data_updated_at.isoformat() if game.data_updated_at else None,
                    }
                    await websocket.send_json(data)
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: nba/{game_id}")
    except Exception as e:
        logger.error(f"WebSocket error nba/{game_id}: {e}")


@router.websocket("/ws/btc/live")
async def btc_live(websocket: WebSocket):
    """Stream latest BTC predictions across all timeframes every 5s."""
    await websocket.accept()
    try:
        while True:
            async with AsyncSessionLocal() as db:
                # Get latest snapshot per timeframe
                snapshots = []
                for tf in ["5m", "15m", "1h", "4h"]:
                    snap = await db.scalar(
                        select(BtcSnapshot)
                        .where(BtcSnapshot.timeframe == tf)
                        .order_by(desc(BtcSnapshot.recorded_at))
                    )
                    if snap:
                        snapshots.append({
                            "timeframe": snap.timeframe,
                            "price_usd": str(snap.price_usd),
                            "prediction_prob": str(snap.prediction_prob) if snap.prediction_prob else None,
                            "volume": str(snap.volume) if snap.volume else None,
                            "recorded_at": snap.recorded_at.isoformat() if snap.recorded_at else None,
                        })
                await websocket.send_json({"type": "btc_update", "data": snapshots})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: btc/live")
    except Exception as e:
        logger.error(f"WebSocket error btc/live: {e}")


@router.websocket("/ws/portfolio/live")
async def portfolio_live(websocket: WebSocket):
    """Stream portfolio updates every 10s. Note: no auth for simplicity in v1."""
    await websocket.accept()
    try:
        while True:
            # In v1, just send a heartbeat. Real implementation would query user positions.
            await websocket.send_json({"type": "heartbeat", "status": "connected"})
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: portfolio/live")
