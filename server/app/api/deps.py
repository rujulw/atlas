"""Shared FastAPI dependency providers."""

from collections.abc import Generator
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.auth import (
    JWTAccessTokenService,
    ServiceTokenClaims,
    TokenValidationError,
)

bearer_scheme = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_token_service() -> JWTAccessTokenService:
    return JWTAccessTokenService(
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        issuer=settings.TOKEN_ISSUER,
        audience=settings.USER_ACCESS_TOKEN_AUDIENCE,
        internal_service_expires_minutes=settings.INTERNAL_SERVICE_TOKEN_EXPIRE_MINUTES,
    )


@dataclass(frozen=True)
class AuthenticatedServiceContext:
    """Validated internal service identity for downstream private routes."""

    service_name: str
    audience: tuple[str, ...]
    acting_user_id: str | None
    claims: ServiceTokenClaims


def require_service_auth(
    *,
    expected_audience: str | None = None,
    allowed_service_names: tuple[str, ...] = (),
    require_acting_user: bool = False,
):
    """Create a dependency that validates Atlas-issued service credentials."""

    async def _get_authenticated_service_context(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
        token_service: JWTAccessTokenService = Depends(get_token_service),
    ) -> AuthenticatedServiceContext:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            claims = token_service.verify_service_token(
                credentials.credentials,
                expected_audience=expected_audience or settings.INTERNAL_SERVICE_TOKEN_AUDIENCE,
            )
        except TokenValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        if allowed_service_names and claims.principal.service_name not in allowed_service_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service principal is not allowed.",
            )

        if require_acting_user and claims.acting_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service principal must include acting user context.",
            )

        return AuthenticatedServiceContext(
            service_name=claims.principal.service_name,
            audience=claims.audience,
            acting_user_id=claims.acting_user_id,
            claims=claims,
        )

    return _get_authenticated_service_context
