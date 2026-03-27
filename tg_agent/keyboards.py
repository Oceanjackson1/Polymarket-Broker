from __future__ import annotations
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo


def market_actions_keyboard(condition_id: str, miniapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Orderbook", callback_data=f"orderbook:{condition_id}"),
            InlineKeyboardButton(text="AI Analysis", callback_data=f"analyze:{condition_id}"),
        ],
    ]
    if miniapp_url:
        rows.append([
            InlineKeyboardButton(
                text="Trade",
                web_app=WebAppInfo(url=f"{miniapp_url}/trade/{condition_id}"),
            ),
        ])
    else:
        rows.append([
            InlineKeyboardButton(text="Buy YES", callback_data=f"buy_yes:{condition_id}"),
            InlineKeyboardButton(text="Buy NO", callback_data=f"buy_no:{condition_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def quick_order_keyboard(condition_id: str, side: str, price: float, miniapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="10 USDC", callback_data=f"quick:{condition_id}:{side}:{price}:10"),
            InlineKeyboardButton(text="50 USDC", callback_data=f"quick:{condition_id}:{side}:{price}:50"),
            InlineKeyboardButton(text="100 USDC", callback_data=f"quick:{condition_id}:{side}:{price}:100"),
        ],
    ]
    if miniapp_url:
        rows.append([
            InlineKeyboardButton(
                text="Custom Amount",
                web_app=WebAppInfo(url=f"{miniapp_url}/trade/{condition_id}?side={side}"),
            ),
        ])
    rows.append([
        InlineKeyboardButton(text="Cancel", callback_data="cancel_action"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_order_keyboard(order_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Confirm", callback_data=f"confirm:{order_key}"),
            InlineKeyboardButton(text="Cancel", callback_data="cancel_action"),
        ],
    ])


def portfolio_keyboard(miniapp_url: str = "") -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Refresh", callback_data="portfolio:refresh")]]
    if miniapp_url:
        rows.append([
            InlineKeyboardButton(
                text="Full Dashboard",
                web_app=WebAppInfo(url=f"{miniapp_url}/portfolio"),
            ),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
