import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.routes.auth import get_refresh_session_repository, get_user_repository
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


@dataclass
class FakeRefreshSessionRecord:
    session_identifier: str
    user_id: int
    refresh_token_hash: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    device_name: str | None = None
    user_agent: str | None = None
    last_seen_ip: str | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    replaced_by_session_identifier: str | None = None


class FakeRefreshSessionRepository:
    def __init__(self) -> None:
        self.created_sessions: list[FakeRefreshSessionRecord] = []
        self.sessions_by_identifier: dict[str, FakeRefreshSessionRecord] = {}

    def create(
        self,
        *,
        session_identifier: str,
        user_id: int,
        refresh_token_hash: str,
        expires_at: object,
        device_name: str | None = None,
        user_agent: str | None = None,
        last_seen_ip: str | None = None,
        last_used_at: datetime | None = None,
    ) -> FakeRefreshSessionRecord:
        now = datetime.now(tz=UTC)
        session = FakeRefreshSessionRecord(
            session_identifier=session_identifier,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
            device_name=device_name,
            user_agent=user_agent,
            last_seen_ip=last_seen_ip,
            last_used_at=last_used_at,
        )
        self.created_sessions.append(session)
        self.sessions_by_identifier[session_identifier] = session
        return session

    def get_by_session_identifier(
        self,
        session_identifier: str,
    ) -> FakeRefreshSessionRecord | None:
        return self.sessions_by_identifier.get(session_identifier)

    def list_for_user(self, user_id: int) -> list[FakeRefreshSessionRecord]:
        return sorted(
            [
                session
                for session in self.sessions_by_identifier.values()
                if session.user_id == user_id
            ],
            key=lambda session: (session.created_at, session.session_identifier),
            reverse=True,
        )

    def revoke(
        self,
        session_identifier: str,
        *,
        revoked_at: datetime | None = None,
        replaced_by_session_identifier: str | None = None,
    ) -> FakeRefreshSessionRecord | None:
        session = self.get_by_session_identifier(session_identifier)
        if session is None:
            return None
        session.revoked_at = revoked_at or datetime.now(tz=UTC)
        session.replaced_by_session_identifier = replaced_by_session_identifier
        session.updated_at = session.revoked_at
        return session

    def revoke_all_for_user(
        self,
        user_id: int,
        *,
        revoked_at: datetime | None = None,
    ) -> int:
        timestamp = revoked_at or datetime.now(tz=UTC)
        count = 0
        for session in self.sessions_by_identifier.values():
            if session.user_id == user_id and session.revoked_at is None:
                session.revoked_at = timestamp
                session.updated_at = timestamp
                count += 1
        return count


def _decode_base64url(value: str) -> dict[str, str | int]:
    padded = value + "=" * (-len(value) % 4)
    raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    return json.loads(raw.decode("utf-8"))


def test_login_returns_jwt_token() -> None:
    fake_user_repository = FakeUserRepository()
    fake_refresh_session_repository = FakeRefreshSessionRepository()
    password_service = PBKDF2PasswordService()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[get_refresh_session_repository] = (
        lambda: fake_refresh_session_repository
    )

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert "refresh_token" in response.json()
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
    refresh_token = response.json()["refresh_token"]
    session_identifier, secret = refresh_token.split(".", maxsplit=1)
    assert session_identifier
    assert secret
    assert len(fake_refresh_session_repository.created_sessions) == 1
    assert (
        fake_refresh_session_repository.created_sessions[0].session_identifier
        == session_identifier
    )
    assert fake_refresh_session_repository.created_sessions[0].user_id == 1


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
    fake_refresh_session_repository = FakeRefreshSessionRepository()
    password_service = PBKDF2PasswordService()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[get_refresh_session_repository] = (
        lambda: fake_refresh_session_repository
    )

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


def test_refresh_rotates_refresh_token_pair() -> None:
    fake_user_repository = FakeUserRepository()
    fake_refresh_session_repository = FakeRefreshSessionRepository()
    password_service = PBKDF2PasswordService()
    fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[get_refresh_session_repository] = (
        lambda: fake_refresh_session_repository
    )

    try:
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "password123"},
        )
        issued_refresh_token = login_response.json()["refresh_token"]

        refresh_response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": issued_refresh_token},
        )
    finally:
        app.dependency_overrides.clear()

    assert refresh_response.status_code == 200
    rotated_refresh_token = refresh_response.json()["refresh_token"]
    assert rotated_refresh_token != issued_refresh_token

    original_session_identifier = issued_refresh_token.split(".", maxsplit=1)[0]
    rotated_session_identifier = rotated_refresh_token.split(".", maxsplit=1)[0]
    original_session = fake_refresh_session_repository.get_by_session_identifier(
        original_session_identifier
    )
    rotated_session = fake_refresh_session_repository.get_by_session_identifier(
        rotated_session_identifier
    )

    assert original_session is not None
    assert rotated_session is not None
    assert original_session.revoked_at is not None
    assert (
        original_session.replaced_by_session_identifier
        == rotated_session.session_identifier
    )


def test_list_sessions_returns_current_users_sessions() -> None:
    fake_user_repository = FakeUserRepository()
    fake_refresh_session_repository = FakeRefreshSessionRepository()
    password_service = PBKDF2PasswordService()
    user = fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    fake_refresh_session_repository.create(
        session_identifier="session-a",
        user_id=user.id,
        refresh_token_hash="hash-a",
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
        device_name="Laptop",
        user_agent="test-agent",
        last_seen_ip="127.0.0.1",
    )
    fake_refresh_session_repository.create(
        session_identifier="session-b",
        user_id=999,
        refresh_token_hash="hash-b",
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
    )
    access_token = JWTAccessTokenService(
        secret_key="change-me",
        expires_minutes=30,
    ).issue_access_token(subject=str(user.id))
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[get_refresh_session_repository] = (
        lambda: fake_refresh_session_repository
    )

    try:
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["sessions"]) == 1
    assert response.json()["sessions"][0]["session_identifier"] == "session-a"
    assert response.json()["sessions"][0]["device_name"] == "Laptop"
    assert response.json()["sessions"][0]["is_active"] is True


def test_revoke_session_marks_current_users_session_revoked() -> None:
    fake_user_repository = FakeUserRepository()
    fake_refresh_session_repository = FakeRefreshSessionRepository()
    password_service = PBKDF2PasswordService()
    user = fake_user_repository.create(
        email="user@example.com",
        hashed_password=password_service.hash_password("password123"),
    )
    fake_refresh_session_repository.create(
        session_identifier="session-a",
        user_id=user.id,
        refresh_token_hash="hash-a",
        expires_at=datetime.now(tz=UTC) + timedelta(days=1),
    )
    access_token = JWTAccessTokenService(
        secret_key="change-me",
        expires_minutes=30,
    ).issue_access_token(subject=str(user.id))
    app.dependency_overrides[get_user_repository] = lambda: fake_user_repository
    app.dependency_overrides[get_refresh_session_repository] = (
        lambda: fake_refresh_session_repository
    )

    try:
        response = client.delete(
            "/api/v1/auth/sessions/session-a",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"detail": "Session revoked."}
    assert (
        fake_refresh_session_repository.get_by_session_identifier("session-a").revoked_at
        is not None
    )


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
