from __future__ import annotations
from typing import Any


async def handle_analysis(
    params: dict[str, Any],
    redis: Any,
    user_id: str,
) -> dict:
    """AI-powered market analysis."""
    from api.analysis.service import AnalysisService

    svc = AnalysisService(redis=redis)
    action = params.get("action", "ask")

    if action == "ask":
        answer = await svc.ask(user_id=user_id, question=params.get("question", ""))
        return {"success": True, "answer": answer}

    if action == "scan":
        results = await svc.scan(user_id=user_id)
        return {"success": True, "opportunities": results}

    return {"success": False, "error": f"Unknown action: {action}"}
