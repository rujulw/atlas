from collections.abc import Generator
import base64
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.db.base_class import Base
from app.main import app
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
    Base.metadata.create_all(bind=engine, tables=[User.__table__])

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
    Base.metadata.drop_all(bind=engine, tables=[User.__table__])


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
