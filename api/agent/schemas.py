from __future__ import annotations
from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    capability: str = Field(..., description="Capability name to invoke")
    params: dict = Field(default_factory=dict, description="Parameters for the capability")
    conversation_id: str | None = Field(None, description="Optional conversation context ID")


class InvokeResponse(BaseModel):
    success: bool
    data: dict | None = None
    error: str | None = None


class CapabilityInfo(BaseModel):
    name: str
    description: str
    parameters: dict
    examples: list[str] = []


class CapabilitiesResponse(BaseModel):
    agent_name: str = "polydesk"
    version: str = "1.0.0"
    capabilities: list[CapabilityInfo]


class MessageRequest(BaseModel):
    message: str = Field(..., description="Natural language message")
    conversation_id: str | None = None
