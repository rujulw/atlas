"""Auth service interfaces and temporary stub implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TokenService(Protocol):
    def issue_access_token(self, subject: str) -> str:
        """Create an access token for the provided subject."""


@dataclass
class StubTokenService:
    """Temporary token service used until real JWT signing is implemented."""

    prefix: str = "stub-token-for"

    def issue_access_token(self, subject: str) -> str:
        sanitized_subject = subject.replace("@", "_at_")
        return f"{self.prefix}-{sanitized_subject}"
