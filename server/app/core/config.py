"""Application settings loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str
    PROJECT_VERSION: str
    API_V1_PREFIX: str
    DATABASE_URL: str
    SECRET_KEY: str
    TOKEN_ISSUER: str
    USER_ACCESS_TOKEN_AUDIENCE: str
    INTERNAL_SERVICE_TOKEN_AUDIENCE: str
    INTERNAL_SERVICE_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    IDENTITY_ENCRYPTION_KEY: str
    IDENTITY_BLIND_INDEX_KEY: str
    IDENTITY_KEY_VERSION: str
    STORAGE_ROOT_PATH: str


settings = Settings(
    PROJECT_NAME=os.getenv("PROJECT_NAME", "Atlas API"),
    PROJECT_VERSION=os.getenv("PROJECT_VERSION", "0.1.0"),
    API_V1_PREFIX=os.getenv("API_V1_PREFIX", "/api/v1"),
    DATABASE_URL=os.getenv("DATABASE_URL", "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"),
    SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
    TOKEN_ISSUER=os.getenv("TOKEN_ISSUER", "atlas"),
    USER_ACCESS_TOKEN_AUDIENCE=os.getenv("USER_ACCESS_TOKEN_AUDIENCE", "atlas-api"),
    INTERNAL_SERVICE_TOKEN_AUDIENCE=os.getenv(
        "INTERNAL_SERVICE_TOKEN_AUDIENCE",
        "atlas-internal",
    ),
    INTERNAL_SERVICE_TOKEN_EXPIRE_MINUTES=int(
        os.getenv("INTERNAL_SERVICE_TOKEN_EXPIRE_MINUTES", "5")
    ),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "14")),
    IDENTITY_ENCRYPTION_KEY=os.getenv("IDENTITY_ENCRYPTION_KEY", "dev-identity-encryption-key"),
    IDENTITY_BLIND_INDEX_KEY=os.getenv("IDENTITY_BLIND_INDEX_KEY", "dev-identity-blind-index-key"),
    IDENTITY_KEY_VERSION=os.getenv("IDENTITY_KEY_VERSION", "v1"),
    STORAGE_ROOT_PATH=os.getenv("STORAGE_ROOT_PATH", "/tmp/atlas-storage"),
)
