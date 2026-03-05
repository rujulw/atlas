from collections.abc import Generator
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.api.routes.files import get_blob_storage_service
from app.db.base_class import Base
from app.main import app
from app.models.file import File
from app.models.user import User
from app.services.storage import LocalBlobStorageService


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine, tables=[User.__table__, File.__table__])

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_blob_storage_service] = lambda: LocalBlobStorageService(
        root_path=tmp_path
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine, tables=[File.__table__, User.__table__])


def _register_and_login(client: TestClient) -> str:
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
    return login_response.json()["access_token"]


def test_upload_persists_metadata_and_writes_blob(client: TestClient, tmp_path: Path) -> None:
    access_token = _register_and_login(client)
    upload_response = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("hello.txt", b"hello atlas", "text/plain")},
    )

    assert upload_response.status_code == 201
    payload = upload_response.json()
    assert payload["owner_id"] == 1
    assert payload["original_name"] == "hello.txt"
    assert payload["mime_type"] == "text/plain"
    assert payload["size_bytes"] == 11
    assert payload["checksum_sha256"] == hashlib.sha256(b"hello atlas").hexdigest()
    assert "storage_key" in payload
    assert "created_at" in payload

    stored_file_path = tmp_path / payload["storage_key"]
    assert stored_file_path.exists()
    assert stored_file_path.read_bytes() == b"hello atlas"


def test_upload_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/files/upload",
        files={"file": ("hello.txt", b"hello atlas", "text/plain")},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."


def test_upload_rejects_invalid_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": "Bearer invalid-token"},
        files={"file": ("hello.txt", b"hello atlas", "text/plain")},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token format."
