"""Application configuration placeholders.

Environment-backed settings are introduced in a later commit.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    PROJECT_NAME: str = "Atlas API"
    PROJECT_VERSION: str = "0.1.0"


settings = Settings()
