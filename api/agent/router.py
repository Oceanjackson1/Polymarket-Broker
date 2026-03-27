from __future__ import annotations
import logging
from fastapi import APIRouter, Depends, Request
from api.auth.dependencies import get_current_user_from_api_key
from api.agent.schemas import (
    InvokeRequest,
    InvokeResponse,
    MessageRequest,
    CapabilitiesResponse,
    CapabilityInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def list_capabilities(request: Request):
    """Discovery endpoint -- returns all capabilities this agent exposes.
    No auth required so other agents can discover before authenticating."""
    registry = request.app.state.capability_registry
    return CapabilitiesResponse(
        capabilities=[
            CapabilityInfo(**cap) for cap in registry.export_schema()
        ],
    )


@router.post("/invoke", response_model=InvokeResponse)
async def invoke_capability(
    body: InvokeRequest,
    request: Request,
    auth: dict = Depends(get_current_user_from_api_key),
):
    """A2A endpoint -- external agents invoke capabilities with structured JSON."""
    orchestrator = request.app.state.agent_orchestrator
    result = await orchestrator.invoke(
        capability=body.capability,
        params=body.params,
        user_id=auth["user_id"],
        context={"source": "a2a", "conversation_id": body.conversation_id},
    )
    if result.get("success"):
        return InvokeResponse(success=True, data=result)
    return InvokeResponse(success=False, error=result.get("error", "Unknown error"))


@router.post("/message", response_model=InvokeResponse)
async def send_message(
    body: MessageRequest,
    request: Request,
    auth: dict = Depends(get_current_user_from_api_key),
):
    """A2A natural-language endpoint -- send text, get structured response."""
    orchestrator = request.app.state.agent_orchestrator
    result = await orchestrator.handle_message(
        text=body.message,
        user_id=auth["user_id"],
        context={"source": "a2a", "conversation_id": body.conversation_id},
    )
    if result.get("success"):
        return InvokeResponse(success=True, data=result)
    return InvokeResponse(success=False, error=result.get("error"))
