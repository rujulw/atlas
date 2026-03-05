"""Auth service interfaces and implementations."""

from __future__ import annotations

import binascii
import base64
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

    def verify_access_token(self, token: str) -> str:
        """Validate token and return its subject when valid."""


class TokenValidationError(ValueError):
    """Raised when access token validation fails."""


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


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

    def verify_access_token(self, token: str) -> str:
        token_parts = token.split(".")
        if len(token_parts) != 3:
            raise TokenValidationError("Invalid access token format.")

        encoded_header, encoded_payload, encoded_signature = token_parts
        signing_input = f"{encoded_header}.{encoded_payload}"

        expected_signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(encoded_signature, _b64url_encode(expected_signature)):
            raise TokenValidationError("Invalid access token signature.")

        try:
            header = json.loads(_b64url_decode(encoded_header).decode("utf-8"))
            payload = json.loads(_b64url_decode(encoded_payload).decode("utf-8"))
        except (ValueError, binascii.Error, json.JSONDecodeError) as exc:
            raise TokenValidationError("Invalid access token payload.") from exc

        if not isinstance(header, dict) or header.get("alg") != self.algorithm:
            raise TokenValidationError("Invalid access token header.")

        subject = payload.get("sub") if isinstance(payload, dict) else None
        expires_at = payload.get("exp") if isinstance(payload, dict) else None
        if not isinstance(subject, str) or not subject:
            raise TokenValidationError("Invalid access token subject.")
        if not isinstance(expires_at, int):
            raise TokenValidationError("Invalid access token expiry.")

        now = int(self.now_provider().timestamp())
        if now >= expires_at:
            raise TokenValidationError("Access token has expired.")

        return subject


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

    def verify_access_token(self, token: str) -> str:
        token_prefix = f"{self.prefix}-"
        if not token.startswith(token_prefix):
            raise TokenValidationError("Invalid access token signature.")

        sanitized_subject = token.removeprefix(token_prefix)
        return sanitized_subject.replace("_at_", "@")
