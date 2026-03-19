import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime

import pytest

from app.services.auth import (
    InternalServicePrincipal,
    JWTAccessTokenService,
    OpaqueRefreshTokenService,
    RefreshTokenValidationError,
    TokenValidationError,
)


def _decode_base64url(value: str) -> dict[str, str | int]:
    padded = value + "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def _encode_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def test_issue_access_token_produces_signed_jwt() -> None:
    issued_at = datetime(2026, 3, 4, 12, 0, 0, tzinfo=UTC)
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        now_provider=lambda: issued_at,
    )

    token = token_service.issue_access_token(subject="1")
    encoded_header, encoded_payload, encoded_signature = token.split(".")
    header = _decode_base64url(encoded_header)
    payload = _decode_base64url(encoded_payload)

    assert header == {"alg": "HS256", "typ": "JWT"}
    assert payload["sub"] == "1"
    assert payload["iss"] == "atlas"
    assert payload["aud"] == "atlas-api"
    assert payload["iat"] == int(issued_at.timestamp())
    assert payload["exp"] == int(issued_at.timestamp()) + (30 * 60)

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = hmac.new(
        b"test-secret",
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    assert encoded_signature == _encode_base64url(expected_signature)


def test_verify_access_token_returns_subject() -> None:
    issued_at = datetime(2026, 3, 4, 12, 0, 0, tzinfo=UTC)
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        now_provider=lambda: issued_at,
    )
    token = token_service.issue_access_token(subject="1")

    verified_subject = token_service.verify_access_token(token)

    assert verified_subject == "1"


def test_verify_access_token_rejects_expired_token() -> None:
    issued_at = datetime(2026, 3, 4, 12, 0, 0, tzinfo=UTC)
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        now_provider=lambda: issued_at,
    )
    token = token_service.issue_access_token(subject="1")

    validator = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        now_provider=lambda: datetime(2026, 3, 4, 12, 40, 0, tzinfo=UTC),
    )

    with pytest.raises(TokenValidationError, match="expired"):
        validator.verify_access_token(token)


def test_issue_refresh_token_produces_opaque_token_and_hash() -> None:
    issued_at = datetime(2026, 3, 18, 12, 0, 0, tzinfo=UTC)
    refresh_token_service = OpaqueRefreshTokenService(
        expires_days=14,
        now_provider=lambda: issued_at,
    )

    issued_token = refresh_token_service.issue_refresh_token()
    session_identifier = refresh_token_service.parse_session_identifier(issued_token.token)

    assert issued_token.session_identifier == session_identifier
    assert issued_token.token.startswith(f"{session_identifier}.")
    assert issued_token.token_hash == hashlib.sha256(
        issued_token.token.encode("utf-8")
    ).hexdigest()
    assert issued_token.expires_at == datetime(2026, 4, 1, 12, 0, 0, tzinfo=UTC)


def test_parse_session_identifier_rejects_invalid_refresh_token() -> None:
    refresh_token_service = OpaqueRefreshTokenService(expires_days=14)

    with pytest.raises(RefreshTokenValidationError, match="format"):
        refresh_token_service.parse_session_identifier("invalid-token")


def test_verify_access_token_rejects_wrong_issuer_or_audience() -> None:
    issued_at = datetime(2026, 3, 4, 12, 0, 0, tzinfo=UTC)
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        now_provider=lambda: issued_at,
    )
    token = token_service.issue_access_token(subject="1")

    with pytest.raises(TokenValidationError, match="issuer"):
        JWTAccessTokenService(
            secret_key="test-secret",
            expires_minutes=30,
            issuer="different-issuer",
            audience="atlas-api",
            now_provider=lambda: issued_at,
        ).verify_access_token(token)

    with pytest.raises(TokenValidationError, match="audience"):
        JWTAccessTokenService(
            secret_key="test-secret",
            expires_minutes=30,
            issuer="atlas",
            audience="different-audience",
            now_provider=lambda: issued_at,
        ).verify_access_token(token)


def test_issue_and_verify_internal_service_token() -> None:
    issued_at = datetime(2026, 3, 18, 12, 0, 0, tzinfo=UTC)
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        internal_service_expires_minutes=5,
        now_provider=lambda: issued_at,
    )
    principal = InternalServicePrincipal(
        service_name="media-service",
        audience="atlas-internal",
        can_act_as_user=True,
    )

    token = token_service.issue_service_token(
        principal,
        acting_user_id="42",
    )
    claims = token_service.verify_service_token(
        token,
        expected_audience="atlas-internal",
    )

    assert claims.principal.service_name == "media-service"
    assert claims.audience == ("atlas-internal",)
    assert claims.acting_user_id == "42"
    assert claims.subject == "service:media-service"
    assert claims.issuer == "atlas"


def test_issue_service_token_rejects_unauthorized_acting_user_context() -> None:
    token_service = JWTAccessTokenService(
        secret_key="test-secret",
        expires_minutes=30,
        internal_service_expires_minutes=5,
    )
    principal = InternalServicePrincipal(
        service_name="indexer",
        audience="atlas-internal",
        can_act_as_user=False,
    )

    with pytest.raises(ValueError, match="cannot act as a user"):
        token_service.issue_service_token(
            principal,
            acting_user_id="42",
        )
