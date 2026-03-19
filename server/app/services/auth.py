"""Auth service interfaces and implementations."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol


class TokenService(Protocol):
    def issue_access_token(self, subject: str) -> str:
        """Create an access token for the provided subject."""

    def verify_access_token(self, token: str) -> str:
        """Validate token and return its subject when valid."""


class TokenValidationError(ValueError):
    """Raised when access token validation fails."""


class RefreshTokenValidationError(ValueError):
    """Raised when refresh token format or contents are invalid."""


@dataclass(frozen=True)
class AccessTokenClaims:
    """Validated Atlas access-token claims."""

    subject: str
    issued_at: int
    expires_at: int
    issuer: str | None
    audience: tuple[str, ...]


@dataclass(frozen=True)
class InternalServicePrincipal:
    """Configuration scaffold for a trusted private subservice principal."""

    service_name: str
    audience: str
    can_act_as_user: bool = False


@dataclass(frozen=True)
class ServiceTokenClaims:
    """Validated claims for an Atlas-issued internal service token."""

    principal: InternalServicePrincipal
    issuer: str | None
    audience: tuple[str, ...]
    subject: str
    issued_at: int
    expires_at: int
    acting_user_id: str | None = None


def _utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _normalize_audience(
    audience: str | tuple[str, ...] | list[str] | None,
) -> tuple[str, ...]:
    if audience is None:
        return ()
    if isinstance(audience, str):
        return (audience,)
    return tuple(aud for aud in audience if aud)


@dataclass(frozen=True)
class JWTAccessTokenService:
    """Issue signed JWT access tokens using HS256."""

    secret_key: str
    expires_minutes: int
    algorithm: str = "HS256"
    issuer: str | None = None
    audience: tuple[str, ...] | str | None = None
    internal_service_expires_minutes: int = 5
    now_provider: Callable[[], datetime] = field(default=_utc_now)

    def issue_access_token(self, subject: str) -> str:
        return self._issue_jwt(
            subject=subject,
            expires_minutes=self.expires_minutes,
            audience=_normalize_audience(self.audience),
        )

    def issue_service_token(
        self,
        principal: InternalServicePrincipal,
        *,
        acting_user_id: str | None = None,
    ) -> str:
        if acting_user_id is not None and not principal.can_act_as_user:
            raise ValueError("Service principal cannot act as a user.")

        additional_claims: dict[str, str] = {
            "token_use": "service",
            "service_name": principal.service_name,
        }
        if acting_user_id is not None:
            additional_claims["acting_user_id"] = acting_user_id

        return self._issue_jwt(
            subject=f"service:{principal.service_name}",
            expires_minutes=self.internal_service_expires_minutes,
            audience=(principal.audience,),
            additional_claims=additional_claims,
        )

    def _issue_jwt(
        self,
        *,
        subject: str,
        expires_minutes: int,
        audience: tuple[str, ...] = (),
        additional_claims: dict[str, str] | None = None,
    ) -> str:
        now = self.now_provider()
        expires_at = now + timedelta(minutes=expires_minutes)

        header = {"alg": self.algorithm, "typ": "JWT"}
        payload = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
        }
        if self.issuer is not None:
            payload["iss"] = self.issuer
        if audience:
            payload["aud"] = audience[0] if len(audience) == 1 else list(audience)
        if additional_claims is not None:
            payload.update(additional_claims)

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
        claims = self.verify_access_token_claims(token)
        return claims.subject

    def verify_access_token_claims(self, token: str) -> AccessTokenClaims:
        payload = self._validate_token_payload(token)
        return AccessTokenClaims(
            subject=payload["sub"],
            issued_at=payload["iat"],
            expires_at=payload["exp"],
            issuer=payload.get("iss"),
            audience=_normalize_audience(payload.get("aud")),
        )

    def verify_service_token(
        self,
        token: str,
        *,
        expected_audience: str | None = None,
    ) -> ServiceTokenClaims:
        payload = self._validate_token_payload(
            token,
            expected_audience=expected_audience,
        )
        token_use = payload.get("token_use")
        service_name = payload.get("service_name")
        acting_user_id = payload.get("acting_user_id")

        if token_use != "service":
            raise TokenValidationError("Invalid service token use.")
        if not isinstance(service_name, str) or not service_name:
            raise TokenValidationError("Invalid service token principal.")
        if acting_user_id is not None and not isinstance(acting_user_id, str):
            raise TokenValidationError("Invalid acting user id.")

        audience = _normalize_audience(payload.get("aud"))
        return ServiceTokenClaims(
            principal=InternalServicePrincipal(
                service_name=service_name,
                audience=audience[0] if audience else "",
                can_act_as_user=acting_user_id is not None,
            ),
            issuer=payload.get("iss"),
            audience=audience,
            subject=payload["sub"],
            issued_at=payload["iat"],
            expires_at=payload["exp"],
            acting_user_id=acting_user_id,
        )

    def _validate_token_payload(
        self,
        token: str,
        *,
        expected_audience: str | None = None,
    ) -> dict[str, object]:
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

        if not isinstance(payload, dict):
            raise TokenValidationError("Invalid access token payload.")

        subject = payload.get("sub")
        issued_at = payload.get("iat")
        expires_at = payload.get("exp")
        if not isinstance(subject, str) or not subject:
            raise TokenValidationError("Invalid access token subject.")
        if not isinstance(issued_at, int):
            raise TokenValidationError("Invalid access token issued-at.")
        if not isinstance(expires_at, int):
            raise TokenValidationError("Invalid access token expiry.")
        if self.issuer is not None and payload.get("iss") != self.issuer:
            raise TokenValidationError("Invalid access token issuer.")

        expected_audiences = _normalize_audience(expected_audience) or _normalize_audience(
            self.audience
        )
        if expected_audiences:
            actual_audiences = _normalize_audience(payload.get("aud"))
            if not actual_audiences or not set(expected_audiences).intersection(actual_audiences):
                raise TokenValidationError("Invalid access token audience.")

        now = int(self.now_provider().timestamp())
        if now >= expires_at:
            raise TokenValidationError("Access token has expired.")

        return payload


@dataclass(frozen=True)
class IssuedRefreshToken:
    """Issued opaque refresh token plus persistence metadata."""

    token: str
    session_identifier: str
    token_hash: str
    expires_at: datetime


class RefreshTokenService(Protocol):
    def issue_refresh_token(self) -> IssuedRefreshToken:
        """Create a new opaque refresh token plus storage metadata."""

    def parse_session_identifier(self, token: str) -> str:
        """Extract the public session identifier from a refresh token."""

    def hash_refresh_token(self, token: str) -> str:
        """Derive the persistent hash representation of a refresh token."""


@dataclass(frozen=True)
class OpaqueRefreshTokenService:
    """Issue opaque refresh tokens as session-id and random-secret pairs."""

    expires_days: int
    session_identifier_bytes: int = 16
    secret_bytes: int = 32
    now_provider: Callable[[], datetime] = field(default=_utc_now)

    def issue_refresh_token(self) -> IssuedRefreshToken:
        session_identifier = secrets.token_hex(self.session_identifier_bytes)
        secret = secrets.token_urlsafe(self.secret_bytes)
        token = f"{session_identifier}.{secret}"
        expires_at = self.now_provider() + timedelta(days=self.expires_days)

        return IssuedRefreshToken(
            token=token,
            session_identifier=session_identifier,
            token_hash=self.hash_refresh_token(token),
            expires_at=expires_at,
        )

    def parse_session_identifier(self, token: str) -> str:
        session_identifier, _, secret = token.partition(".")
        if not session_identifier or not secret:
            raise RefreshTokenValidationError("Invalid refresh token format.")
        return session_identifier

    def hash_refresh_token(self, token: str) -> str:
        self.parse_session_identifier(token)
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
