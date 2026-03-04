"""Authentication route stubs."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth import StubTokenService, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_token_service() -> TokenService:
    return StubTokenService()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    token_service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    access_token = token_service.issue_access_token(subject=payload.email)
    return TokenResponse(access_token=access_token)


@router.post("/register")
async def register(payload: RegisterRequest) -> dict[str, str]:
    _ = payload
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Registration flow not implemented yet.",
    )
