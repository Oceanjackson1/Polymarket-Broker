from __future__ import annotations


def format_markets_response(data: dict) -> str:
    markets = data.get("markets", [])
    if not markets:
        return "Found 0 markets matching your query."

    lines = ["Markets Found:\n"]
    for i, m in enumerate(markets, 1):
        price = m.get("best_price")
        price_str = f"${price:.2f}" if price is not None else "N/A"
        lines.append(f"{i}. {m['question']}\n   Price: {price_str} | ID: {m.get('condition_id', 'N/A')}")
    return "\n".join(lines)


def format_portfolio_response(data: dict) -> str:
    positions = data.get("positions", [])
    if not positions:
        return "No open positions."

    lines = ["Your Positions:\n"]
    for p in positions:
        pnl = ""
        if "avg_price" in p and "current_price" in p:
            diff = p["current_price"] - p["avg_price"]
            sign = "+" if diff >= 0 else ""
            pnl = f" | PnL: {sign}{diff:.2f}"
        lines.append(f"- {p.get('market', '?')} | {p.get('side', '?')} x{p.get('size', 0)}{pnl}")
    return "\n".join(lines)


def format_analysis_response(data: dict) -> str:
    answer = data.get("answer", "No analysis available.")
    return f"AI Analysis:\n\n{answer}"


def format_error(data: dict) -> str:
    return f"Error: {data.get('error', 'Something went wrong.')}"
