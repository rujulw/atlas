"""Authentication route stubs."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.repositories.user import SQLAlchemyUserRepository, UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth import JWTAccessTokenService, PBKDF2PasswordService, PasswordService, TokenService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_token_service() -> TokenService:
    return JWTAccessTokenService(
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_password_service() -> PasswordService:
    return PBKDF2PasswordService()


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return SQLAlchemyUserRepository(db=db)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    token_service: TokenService = Depends(get_token_service),
) -> TokenResponse:
    access_token = token_service.issue_access_token(subject=payload.email)
    return TokenResponse(access_token=access_token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    user_repository: UserRepository = Depends(get_user_repository),
    password_service: PasswordService = Depends(get_password_service),
) -> dict[str, str]:
    existing_user = user_repository.get_by_email(payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists.",
        )

    hashed_password = password_service.hash_password(payload.password)
    user_repository.create(
        email=payload.email,
        hashed_password=hashed_password,
        full_name=payload.full_name,
    )

    return {"detail": "User registered successfully."}
