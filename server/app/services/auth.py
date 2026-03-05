"""Auth service interfaces and implementations."""

from __future__ import annotations

import binascii
import json
import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Callable, Protocol


class TokenService(Protocol):
    def issue_access_token(self, subject: str) -> str:
        """Create an access token for the provided subject."""


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _b64url_encode(data: bytes) -> str:
    return binascii.b2a_base64(data, newline=False).decode("ascii").rstrip("=").replace("+", "-").replace("/", "_")


@dataclass(frozen=True)
class JWTAccessTokenService:
    """Issue signed JWT access tokens using HS256."""

    secret_key: str
    expires_minutes: int
    algorithm: str = "HS256"
    now_provider: Callable[[], datetime] = field(default=_utc_now)

    def issue_access_token(self, subject: str) -> str:
        now = self.now_provider()
        expires_at = now + timedelta(minutes=self.expires_minutes)

        header = {"alg": self.algorithm, "typ": "JWT"}
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }

        encoded_header = _b64url_encode(
            json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        encoded_payload = _b64url_encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signing_input = f"{encoded_header}.{encoded_payload}"
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        encoded_signature = _b64url_encode(signature)

        return f"{signing_input}.{encoded_signature}"


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
