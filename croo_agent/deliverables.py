"""Standardized deliverable envelope for Croo orders.

Every Croo `deliver_order()` call must produce a JSON-serialisable text deliverable
with a stable shape so consumers can parse it deterministically:

  {
    "envelope_version": "1",
    "service": "analysis|strategy|data_feed|market_query",
    "order_id": "<croo order id>",
    "status": "ok" | "error",
    "generated_at": "<ISO-8601 UTC>",
    "request": { ...echo of validated requirement... },
    "result": { ...handler dict on success... },
    "error": { "code": "...", "message": "..." }   // only when status == "error"
  }
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, UTC, date
from decimal import Decimal
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)

ENVELOPE_VERSION = "1"
MAX_DELIVERABLE_BYTES = 64 * 1024  # 64 KiB safety guard
TRUNCATION_NOTICE_KEY = "truncated"

# Field names that should be stripped from result dicts before serialisation as a
# defence-in-depth measure (handlers don't return these today, but we never want to
# leak credentials into a public deliverable).
_FORBIDDEN_KEYS = frozenset({
    "private_key", "api_key", "sdk_key", "token", "session", "secret", "password",
})


def _safe_default(obj: Any) -> Any:
    """JSON encoder fallback for non-native types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (bytes, bytearray)):
        return obj.hex()
    if isinstance(obj, UUID):
        return str(obj)
    # Pydantic v2 models
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    # Pydantic v1 / dataclass-likes
    if hasattr(obj, "dict") and callable(obj.dict):
        try:
            return obj.dict()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
    return repr(obj)


def _scrub(value: Any) -> Any:
    """Recursively drop forbidden keys from dicts and lists."""
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items() if k not in _FORBIDDEN_KEYS}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    return value


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def build_envelope(
    *,
    service: str,
    order_id: str,
    request: dict | None,
    result: dict | None = None,
    error: tuple[str, str] | None = None,
) -> dict:
    """Build a standardized envelope.

    Pass `result` for success, `error=(code, message)` for failure.
    Mutually exclusive — if `error` is set the envelope's status becomes "error" and
    `result` is omitted.
    """
    envelope: dict[str, Any] = {
        "envelope_version": ENVELOPE_VERSION,
        "service": service,
        "order_id": order_id,
        "status": "error" if error else "ok",
        "generated_at": _now_iso(),
        "request": _scrub(request or {}),
    }
    if error:
        code, message = error
        envelope["error"] = {"code": code, "message": message}
        return envelope

    cleaned = _scrub(result or {})
    # Handlers return {"success": bool, ...}. Surface a non-True success as error.
    if isinstance(cleaned, dict) and cleaned.get("success") is False:
        envelope["status"] = "error"
        envelope["error"] = {
            "code": "HANDLER_FAILED",
            "message": str(cleaned.get("error") or "handler returned success=False"),
        }
        # Still echo the partial result for debugging
        partial = {k: v for k, v in cleaned.items() if k not in ("success", "error")}
        if partial:
            envelope["result"] = partial
        return envelope

    if isinstance(cleaned, dict):
        cleaned = {k: v for k, v in cleaned.items() if k != "success"}
    envelope["result"] = cleaned
    return envelope


def envelope_to_text(envelope: dict, max_bytes: int = MAX_DELIVERABLE_BYTES) -> str:
    """Serialize the envelope. Truncates oversized deliverables to fit `max_bytes`."""
    text = json.dumps(envelope, default=_safe_default, ensure_ascii=False)
    if len(text.encode("utf-8")) <= max_bytes:
        return text

    logger.warning(
        "Deliverable size %d exceeds %d bytes; truncating result for order %s",
        len(text), max_bytes, envelope.get("order_id"),
    )
    truncated = dict(envelope)
    truncated[TRUNCATION_NOTICE_KEY] = True
    truncated["result"] = {
        "_truncated": True,
        "_original_bytes": len(text.encode("utf-8")),
        "_note": "Result exceeded max deliverable size; partial preview only",
        "preview": json.dumps(envelope.get("result"), default=_safe_default, ensure_ascii=False)[:max_bytes // 2],
    }
    return json.dumps(truncated, default=_safe_default, ensure_ascii=False)
