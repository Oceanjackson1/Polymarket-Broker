from pydantic import BaseModel, EmailStr
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    tier: str
    display_name: str | None = None
    avatar_url: str | None = None
    wallet_address: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = []


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key: str
    key_hint: str
    scopes: list[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ApiKeyListItem(BaseModel):
    id: str
    name: str
    key: str
    key_hint: str
    scopes: list[str]
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
