import base64
import json
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base_class import Base
from app.main import app
from app.models.session import RefreshSession
from app.models.user import User
from app.services.auth import JWTAccessTokenService, PBKDF2PasswordService
from app.services.identity import HMACSHA256BlindIndexService, normalize_email


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine, tables=[User.__table__, RefreshSession.__table__])

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine, tables=[RefreshSession.__table__, User.__table__])


def _decode_access_token_payload(token: str) -> dict[str, str | int]:
    encoded_payload = token.split(".")[1]
    padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def test_register_login_and_access_protected_route(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    assert "refresh_token" in login_response.json()

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json() == {"email": "user@example.com"}


def test_login_token_subject_uses_internal_user_id(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200

    payload = _decode_access_token_payload(login_response.json()["access_token"])

    assert payload["sub"] == "1"


def test_login_persists_refresh_session_and_returns_refresh_token(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"User-Agent": "atlas-integration-test"},
    )
    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]
    session_identifier, secret = refresh_token.split(".", maxsplit=1)

    with next(client.app.dependency_overrides[get_db]()) as db:
        stored_session = (
            db.query(RefreshSession)
            .filter(RefreshSession.session_identifier == session_identifier)
            .one()
        )

    assert secret
    assert stored_session.user_id == 1
    assert stored_session.refresh_token_hash != refresh_token
    assert stored_session.user_agent == "atlas-integration-test"


def test_refresh_rotates_session_and_rejects_old_refresh_token(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"User-Agent": "atlas-rotation-test", "X-Device-Name": "Laptop"},
    )
    assert login_response.status_code == 200

    original_refresh_token = login_response.json()["refresh_token"]
    original_session_identifier = original_refresh_token.split(".", maxsplit=1)[0]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
        headers={"User-Agent": "atlas-rotation-test", "X-Device-Name": "Laptop"},
    )
    assert refresh_response.status_code == 200

    rotated_refresh_token = refresh_response.json()["refresh_token"]
    rotated_session_identifier = rotated_refresh_token.split(".", maxsplit=1)[0]
    assert rotated_refresh_token != original_refresh_token

    with next(client.app.dependency_overrides[get_db]()) as db:
        original_session = (
            db.query(RefreshSession)
            .filter(RefreshSession.session_identifier == original_session_identifier)
            .one()
        )
        rotated_session = (
            db.query(RefreshSession)
            .filter(RefreshSession.session_identifier == rotated_session_identifier)
            .one()
        )

    assert original_session.revoked_at is not None
    assert (
        original_session.replaced_by_session_identifier
        == rotated_session.session_identifier
    )
    assert rotated_session.revoked_at is None
    assert rotated_session.last_used_at is not None
    assert rotated_session.device_name == "Laptop"

    reused_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert reused_refresh_response.status_code == 401
    assert reused_refresh_response.json()["detail"] == "Invalid refresh token."


def test_refresh_reuse_revokes_rotated_session_chain(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200

    first_refresh_token = login_response.json()["refresh_token"]
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh_token},
    )
    assert refresh_response.status_code == 200

    second_refresh_token = refresh_response.json()["refresh_token"]
    second_session_identifier = second_refresh_token.split(".", maxsplit=1)[0]

    reuse_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh_token},
    )
    assert reuse_response.status_code == 401

    invalidated_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": second_refresh_token},
    )

    assert invalidated_response.status_code == 401
    assert invalidated_response.json()["detail"] == "Invalid refresh token."

    with next(client.app.dependency_overrides[get_db]()) as db:
        current_session = (
            db.query(RefreshSession)
            .filter(RefreshSession.session_identifier == second_session_identifier)
            .one()
        )

    assert current_session.revoked_at is not None


def test_list_sessions_returns_device_metadata_for_current_user(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"User-Agent": "atlas-session-list-test", "X-Device-Name": "Desk Mac"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    sessions_response = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert sessions_response.status_code == 200
    sessions = sessions_response.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["device_name"] == "Desk Mac"
    assert sessions[0]["user_agent"] == "atlas-session-list-test"
    assert sessions[0]["is_active"] is True
    assert sessions[0]["revoked_at"] is None


def test_revoke_single_session_blocks_future_refresh(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]
    session_identifier = refresh_token.split(".", maxsplit=1)[0]

    revoke_response = client.delete(
        f"/api/v1/auth/sessions/{session_identifier}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json() == {"detail": "Session revoked."}

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Invalid refresh token."


def test_revoke_all_sessions_blocks_future_refresh_and_marks_sessions_revoked(
    client: TestClient,
) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    first_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"X-Device-Name": "Laptop"},
    )
    second_login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
        headers={"X-Device-Name": "Phone"},
    )
    assert first_login_response.status_code == 200
    assert second_login_response.status_code == 200

    access_token = first_login_response.json()["access_token"]
    first_refresh_token = first_login_response.json()["refresh_token"]
    second_refresh_token = second_login_response.json()["refresh_token"]

    revoke_all_response = client.delete(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert revoke_all_response.status_code == 200
    assert revoke_all_response.json()["revoked_sessions"] == 2

    first_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": first_refresh_token},
    )
    second_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": second_refresh_token},
    )

    assert first_refresh_response.status_code == 401
    assert second_refresh_response.status_code == 401

    with next(client.app.dependency_overrides[get_db]()) as db:
        revoked_sessions = (
            db.query(RefreshSession)
            .filter(RefreshSession.user_id == 1)
            .all()
        )

    assert len(revoked_sessions) == 2
    assert all(refresh_session.revoked_at is not None for refresh_session in revoked_sessions)


def test_login_fails_for_unregistered_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_login_fails_for_wrong_password(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password."


def test_protected_route_fails_without_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."


def test_protected_route_fails_with_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token format."


def test_register_persists_email_blind_index_for_login_lookup(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "User@Example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    with next(client.app.dependency_overrides[get_db]()) as db:
        stored_user = db.query(User).filter(User.email == "user@example.com").one()
        blind_index = stored_user.email_blind_index
        db.delete(stored_user)
        db.commit()

        replacement_user = User(
            email="user@example.com",
            email_blind_index=blind_index,
            hashed_password=stored_user.hashed_password,
            full_name=stored_user.full_name,
            identity_key_version=stored_user.identity_key_version,
        )
        db.add(replacement_user)
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": " user@example.com ", "password": "password123"},
    )

    assert login_response.status_code == 200


def test_me_returns_email_after_internal_user_id_subject_login(client: TestClient) -> None:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "full_name": "Atlas User",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert me_response.status_code == 200
    assert me_response.json() == {"email": "user@example.com"}


def test_login_succeeds_for_user_with_encrypted_identity_fields_persisted(
    client: TestClient,
) -> None:
    password_service = PBKDF2PasswordService()
    blind_index_service = HMACSHA256BlindIndexService(key="dev-identity-blind-index-key")
    normalized_email = normalize_email("EncryptedUser@example.com")

    generator = client.app.dependency_overrides[get_db]()
    db = next(generator)
    try:
        user = User(
            email=normalized_email,
            email_ciphertext="enc:email",
            email_blind_index=blind_index_service.derive(normalized_email),
            full_name="Atlas User",
            full_name_ciphertext="enc:full-name",
            hashed_password=password_service.hash_password("password123"),
            identity_key_version="v1",
        )
        db.add(user)
        db.commit()
    finally:
        generator.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": " encrypteduser@example.com ", "password": "password123"},
    )

    assert login_response.status_code == 200


def test_me_rejects_valid_token_for_missing_internal_user(client: TestClient) -> None:
    token = JWTAccessTokenService(
        secret_key="change-me",
        expires_minutes=30,
    ).issue_access_token(subject="999")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authenticated user not found."
