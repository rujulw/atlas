"""Auth service interfaces and implementations."""

from __future__ import annotations

import binascii
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Protocol


class TokenService(Protocol):
    def issue_access_token(self, subject: str) -> str:
        """Create an access token for the provided subject."""


class PasswordService(Protocol):
    def hash_password(self, password: str) -> str:
        """Create a one-way hash for a plaintext password."""

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Validate plaintext password against a stored hash."""


@dataclass(frozen=True)
class PBKDF2PasswordService:
    """PBKDF2-HMAC password hashing service with per-password random salt."""

    iterations: int = 390_000
    salt_bytes: int = 16
    algorithm: str = "sha256"

    def hash_password(self, password: str) -> str:
        salt = secrets.token_bytes(self.salt_bytes)
        digest = hashlib.pbkdf2_hmac(
            self.algorithm,
            password.encode("utf-8"),
            salt,
            self.iterations,
        )
        return ":".join(
            [
                "pbkdf2",
                self.algorithm,
                str(self.iterations),
                salt.hex(),
                digest.hex(),
            ]
        )

    def verify_password(self, password: str, password_hash: str) -> bool:
        parts = password_hash.split(":")
        if len(parts) != 5:
            return False

        scheme, algorithm, iterations_raw, salt_raw, digest_raw = parts
        if scheme != "pbkdf2":
            return False

        try:
            iterations = int(iterations_raw)
            salt = binascii.unhexlify(salt_raw.encode("ascii"))
            expected_digest = binascii.unhexlify(digest_raw.encode("ascii"))
        except (ValueError, binascii.Error):
            return False

        candidate_digest = hashlib.pbkdf2_hmac(
            algorithm,
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(candidate_digest, expected_digest)


@dataclass
class StubTokenService:
    """Temporary token service used until real JWT signing is implemented."""

    prefix: str = "stub-token-for"

    def issue_access_token(self, subject: str) -> str:
        sanitized_subject = subject.replace("@", "_at_")
        return f"{self.prefix}-{sanitized_subject}"
