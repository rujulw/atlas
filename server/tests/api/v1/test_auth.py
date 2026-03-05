from fastapi.testclient import TestClient

from app.api.routes.auth import get_user_repository
from app.main import app

client = TestClient(app)


class FakeUserRepository:
    def __init__(self) -> None:
        self.users_by_email: dict[str, dict[str, str | None]] = {}

    def get_by_email(self, email: str) -> dict[str, str | None] | None:
        return self.users_by_email.get(email)

    def create(
        self,
        email: str,
        hashed_password: str,
        full_name: str | None = None,
    ) -> dict[str, str | None]:
        user = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
        }
        self.users_by_email[email] = user
        return user


def test_login_returns_stub_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"].startswith("stub-token-for")


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
    assert persisted_user["email"] == "user@example.com"
    assert persisted_user["full_name"] == "Atlas User"
    assert persisted_user["hashed_password"] != "password123"


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
