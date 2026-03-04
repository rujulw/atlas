from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_returns_stub_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"].startswith("stub-token-for")


def test_register_is_not_implemented() -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "password123", "full_name": "Atlas User"},
    )

    assert response.status_code == 501
