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
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    STORAGE_ROOT_PATH: str


settings = Settings(
    PROJECT_NAME=os.getenv("PROJECT_NAME", "Atlas API"),
    PROJECT_VERSION=os.getenv("PROJECT_VERSION", "0.1.0"),
    API_V1_PREFIX=os.getenv("API_V1_PREFIX", "/api/v1"),
    DATABASE_URL=os.getenv("DATABASE_URL", "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"),
    SECRET_KEY=os.getenv("SECRET_KEY", "change-me"),
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
    STORAGE_ROOT_PATH=os.getenv("STORAGE_ROOT_PATH", "/tmp/atlas-storage"),
)
