"""Auth request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshSessionResponse(BaseModel):
    session_identifier: str
    device_name: str | None = None
    user_agent: str | None = None
    last_seen_ip: str | None = None
    created_at: datetime
    last_used_at: datetime | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    replaced_by_session_identifier: str | None = None
    is_active: bool


class RefreshSessionListResponse(BaseModel):
    sessions: list[RefreshSessionResponse]


class RevokeSessionResponse(BaseModel):
    detail: str


class RevokeAllSessionsResponse(BaseModel):
    detail: str
    revoked_sessions: int
