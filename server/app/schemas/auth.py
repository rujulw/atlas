"""Auth request and response schemas."""

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
    token_type: str = "bearer"
