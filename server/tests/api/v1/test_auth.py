import base64
import json
from dataclasses import dataclass

from fastapi.testclient import TestClient

from app.api.routes.auth import get_user_repository
from app.main import app
from app.services.auth import JWTAccessTokenService, PBKDF2PasswordService

client = TestClient(app)


@dataclass
class FakeUser:
    id: int
    email: str
    hashed_password: str
    full_name: str | None = None
    email_blind_index: str | None = None
    identity_key_version: str | None = None


class FakeUserRepository:
    def __init__(self) -> None:
        self.next_id = 1
        self.users_by_id: dict[int, FakeUser] = {}
        self.users_by_email: dict[str, FakeUser] = {}
        self.users_by_email_blind_index: dict[str, FakeUser] = {}

    def get_by_id(self, user_id: int) -> FakeUser | None:
        return self.users_by_id.get(user_id)

    def get_by_email(self, email: str) -> FakeUser | None:
        return self.users_by_email.get(email)

    def get_by_email_blind_index(self, email_blind_index: str) -> FakeUser | None:
        return self.users_by_email_blind_index.get(email_blind_index)

    def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
        *,
        email_ciphertext: str | None = None,
        email_blind_index: str | None = None,
        username_ciphertext: str | None = None,
        username_blind_index: str | None = None,
        full_name_ciphertext: str | None = None,
        identity_key_version: str | None = None,
    ) -> FakeUser:
        user = FakeUser(
            id=self.next_id,
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            email_blind_index=email_blind_index,
            identity_key_version=identity_key_version,
        )
        self.next_id += 1
        self.users_by_id[user.id] = user
        self.users_by_email[email] = user
        if email_blind_index is not None:
            self.users_by_email_blind_index[email_blind_index] = user
        return user


def _decode_base64url(value: str) -> dict[str, str | int]:
    padded = value + "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def test_login_returns_jwt_token() -> None:
    fake_user_repository = FakeUserRepository()
    password_service = PBKDF2PasswordService()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    token = response.json()["access_token"]
    token_parts = token.split(".")
    assert len(token_parts) == 3
    header = _decode_base64url(token_parts[0])
    payload = _decode_base64url(token_parts[1])
    assert header == {"alg": "HS256", "typ": "JWT"}
    assert payload["sub"] == "1"
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]


def test_me_requires_bearer_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."


def test_me_rejects_invalid_token() -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token format."


def test_me_rejects_token_with_non_integer_subject() -> None:
    token = JWTAccessTokenService(
        secret_key="change-me",
        expires_minutes=30,
    ).issue_access_token(subject="user@example.com")

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token subject."


def test_me_returns_subject_from_valid_token() -> None:
    fake_user_repository = FakeUserRepository()
    password_service = PBKDF2PasswordService()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    try:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"email": "user@example.com"}


def test_register_persists_user() -> None:
    fake_user_repository = FakeUserRepository()
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
                "full_name": "Atlas User",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {"detail": "User registered successfully."}
    persisted_user = fake_user_repository.get_by_email("user@example.com")
    assert persisted_user is not None
    assert persisted_user.email == "user@example.com"
    assert persisted_user.full_name == "Atlas User"
    assert persisted_user.hashed_password != "password123"


def test_register_rejects_duplicate_email() -> None:
    fake_user_repository = FakeUserRepository()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password="existing-hash",
        full_name="Atlas User",
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "password123",
                "full_name": "Atlas User",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "User already exists."


def test_register_persists_email_blind_index_for_lookup() -> None:
    fake_user_repository = FakeUserRepository()
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository

    try:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "User@Example.com",
                "password": "password123",
                "full_name": "Atlas User",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    persisted_user = fake_user_repository.get_by_email("user@example.com")
    assert persisted_user is not None
    assert persisted_user.email_blind_index is not None
    assert persisted_user.identity_key_version == "v1"
