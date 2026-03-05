import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime

from app.services.auth import JWTAccessTokenService


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
        now_provider=lambda: issued_at,
    )

    token = token_service.issue_access_token(subject="user@example.com")
    encoded_header, encoded_payload, encoded_signature = token.split(".")
    header = _decode_base64url(encoded_header)
    payload = _decode_base64url(encoded_payload)

    assert header == {"alg": "HS256", "typ": "JWT"}
    assert payload["sub"] == "user@example.com"
    assert payload["iat"] == int(issued_at.timestamp())
    assert payload["exp"] == int(issued_at.timestamp()) + (30 * 60)

    signing_input = f"{encoded_header}.{encoded_payload}"
    expected_signature = hmac.new(
        b"test-secret",
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    assert encoded_signature == _encode_base64url(expected_signature)
