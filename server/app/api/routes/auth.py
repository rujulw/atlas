"""Authentication routes."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.models.session import RefreshSession
from app.repositories.session import (
    RefreshSessionRepository,
    SQLAlchemyRefreshSessionRepository,
)
from app.repositories.user import SQLAlchemyUserRepository, UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshSessionListResponse,
    RefreshSessionResponse,
    RefreshTokenRequest,
    RegisterRequest,
    RevokeAllSessionsResponse,
    RevokeSessionResponse,
    TokenResponse,
)
from app.services.auth import (
    JWTAccessTokenService,
    OpaqueRefreshTokenService,
    PasswordService,
    PBKDF2PasswordService,
    RefreshTokenService,
    RefreshTokenValidationError,
    TokenService,
    TokenValidationError,
)
from app.services.identity import (
    BlindIndexService,
    HMACSHA256BlindIndexService,
    normalize_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


def get_token_service() -> TokenService:
    return JWTAccessTokenService(
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_password_service() -> PasswordService:
    return PBKDF2PasswordService()


def get_refresh_token_service() -> RefreshTokenService:
    return OpaqueRefreshTokenService(
        expires_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def get_blind_index_service() -> BlindIndexService:
    return HMACSHA256BlindIndexService(key=settings.IDENTITY_BLIND_INDEX_KEY)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db=db)


def get_refresh_session_repository(
    db: Session = Depends(get_db),
) -> RefreshSessionRepository:
    return SQLAlchemyRefreshSessionRepository(db=db)


def get_current_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    token_service: TokenService = Depends(get_token_service),
) -> int:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        subject = token_service.verify_access_token(credentials.credentials)
    except TokenValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    try:
        return int(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def _resolve_current_user(
    current_subject: int,
    user_repository: UserRepository,
) -> int:
    user = user_repository.get_by_id(current_subject)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user not found.",
        )
    return user.id


def _issue_token_pair(
    *,
    request: Request,
    user_id: int,
    token_service: TokenService,
    refresh_token_service: RefreshTokenService,
    refresh_session_repository: RefreshSessionRepository,
    device_name: str | None = None,
    user_agent: str | None = None,
    last_seen_ip: str | None = None,
    last_used_at: datetime | None = None,
) -> TokenResponse:
    access_token = token_service.issue_access_token(subject=str(user_id))
    refresh_token = refresh_token_service.issue_refresh_token()
    refresh_session_repository.create(
        session_identifier=refresh_token.session_identifier,
        user_id=user_id,
        refresh_token_hash=refresh_token.token_hash,
        expires_at=refresh_token.expires_at,
        device_name=device_name or request.headers.get("X-Device-Name"),
        user_agent=user_agent or request.headers.get("user-agent"),
        last_seen_ip=last_seen_ip
        or (request.client.host if request.client is not None else None),
        last_used_at=last_used_at,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token.token,
    )


def _raise_refresh_token_unauthorized(detail: str = "Invalid refresh token.") -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _serialize_refresh_session(refresh_session: RefreshSession) -> RefreshSessionResponse:
    is_active = (
        refresh_session.revoked_at is None
        and datetime.now(tz=UTC) < refresh_session.expires_at
    )
    return RefreshSessionResponse(
        session_identifier=refresh_session.session_identifier,
        device_name=refresh_session.device_name,
        user_agent=refresh_session.user_agent,
        last_seen_ip=refresh_session.last_seen_ip,
        created_at=refresh_session.created_at,
        last_used_at=refresh_session.last_used_at,
        expires_at=refresh_session.expires_at,
        revoked_at=refresh_session.revoked_at,
        replaced_by_session_identifier=refresh_session.replaced_by_session_identifier,
        is_active=is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    payload: LoginRequest,
    token_service: TokenService = Depends(get_token_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    refresh_session_repository: RefreshSessionRepository = Depends(
        get_refresh_session_repository
    ),
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    blind_index_service: BlindIndexService = Depends(get_blind_index_service),
) -> TokenResponse:
    normalized_email = normalize_email(payload.email)
    email_blind_index = blind_index_service.derive(normalized_email)
    user = user_repository.get_by_email_blind_index(email_blind_index)
    if user is None:
        user = user_repository.get_by_email(normalized_email)

    if user is None or not password_service.verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _issue_token_pair(
        request=request,
        user_id=user.id,
        token_service=token_service,
        refresh_token_service=refresh_token_service,
        refresh_session_repository=refresh_session_repository,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    payload: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service),
    refresh_token_service: RefreshTokenService = Depends(get_refresh_token_service),
    refresh_session_repository: RefreshSessionRepository = Depends(
        get_refresh_session_repository
    ),
) -> TokenResponse:
    try:
        session_identifier = refresh_token_service.parse_session_identifier(
            payload.refresh_token
        )
        refresh_token_hash = refresh_token_service.hash_refresh_token(payload.refresh_token)
    except RefreshTokenValidationError as exc:
        _raise_refresh_token_unauthorized(str(exc))

    refresh_session = refresh_session_repository.get_by_session_identifier(
        session_identifier
    )
    if refresh_session is None:
        _raise_refresh_token_unauthorized()

    if refresh_session.refresh_token_hash != refresh_token_hash:
        refresh_session_repository.revoke_all_for_user(refresh_session.user_id)
        _raise_refresh_token_unauthorized()

    now = datetime.now(tz=UTC)
    if refresh_session.revoked_at is not None:
        if refresh_session.replaced_by_session_identifier is not None:
            refresh_session_repository.revoke_all_for_user(refresh_session.user_id)
        _raise_refresh_token_unauthorized()

    if now >= refresh_session.expires_at:
        refresh_session_repository.revoke(refresh_session.session_identifier)
        _raise_refresh_token_unauthorized("Refresh token has expired.")

    replacement_token = refresh_token_service.issue_refresh_token()
    refresh_session_repository.revoke(
        refresh_session.session_identifier,
        replaced_by_session_identifier=replacement_token.session_identifier,
    )
    refresh_session_repository.create(
        session_identifier=replacement_token.session_identifier,
        user_id=refresh_session.user_id,
        refresh_token_hash=replacement_token.token_hash,
        expires_at=replacement_token.expires_at,
        device_name=refresh_session.device_name or request.headers.get("X-Device-Name"),
        user_agent=request.headers.get("user-agent") or refresh_session.user_agent,
        last_seen_ip=(
            request.client.host if request.client is not None else refresh_session.last_seen_ip
        ),
        last_used_at=now,
    )

    access_token = token_service.issue_access_token(subject=str(refresh_session.user_id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=replacement_token.token,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
    blind_index_service: BlindIndexService = Depends(get_blind_index_service),
) -> dict[str, str]:
    normalized_email = normalize_email(payload.email)
    email_blind_index = blind_index_service.derive(normalized_email)

    existing_user = user_repository.get_by_email_blind_index(email_blind_index)
    if existing_user is None:
        existing_user = user_repository.get_by_email(normalized_email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        )

    hashed_password = password_service.hash_password(payload.password)
    user_repository.create(
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=payload.full_name,
        email_blind_index=email_blind_index,
        identity_key_version=settings.IDENTITY_KEY_VERSION,
    )

    return {"detail": "User registered successfully."}


@router.get("/me")
async def read_current_user_email(
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
) -> dict[str, str]:
    user = user_repository.get_by_id(_resolve_current_user(current_subject, user_repository))
    assert user is not None
    return {"email": user.email}


@router.get("/sessions", response_model=RefreshSessionListResponse)
async def list_refresh_sessions(
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_session_repository: RefreshSessionRepository = Depends(
        get_refresh_session_repository
    ),
) -> RefreshSessionListResponse:
    user_id = _resolve_current_user(current_subject, user_repository)
    refresh_sessions = refresh_session_repository.list_for_user(user_id)
    return RefreshSessionListResponse(
        sessions=[
            _serialize_refresh_session(refresh_session)
            for refresh_session in refresh_sessions
        ]
    )


@router.delete("/sessions", response_model=RevokeAllSessionsResponse)
async def revoke_all_refresh_sessions(
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_session_repository: RefreshSessionRepository = Depends(
        get_refresh_session_repository
    ),
) -> RevokeAllSessionsResponse:
    user_id = _resolve_current_user(current_subject, user_repository)
    revoked_sessions = refresh_session_repository.revoke_all_for_user(user_id)
    return RevokeAllSessionsResponse(
        detail="All sessions revoked.",
        revoked_sessions=revoked_sessions,
    )


@router.delete(
    "/sessions/{session_identifier}",
    response_model=RevokeSessionResponse,
)
async def revoke_refresh_session(
    session_identifier: str,
    current_subject: int = Depends(get_current_subject),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_session_repository: RefreshSessionRepository = Depends(
        get_refresh_session_repository
    ),
) -> RevokeSessionResponse:
    user_id = _resolve_current_user(current_subject, user_repository)
    refresh_session = refresh_session_repository.get_by_session_identifier(
        session_identifier
    )
    if refresh_session is None or refresh_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    refresh_session_repository.revoke(session_identifier)
    return RevokeSessionResponse(detail="Session revoked.")
