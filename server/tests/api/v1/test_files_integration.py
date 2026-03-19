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
from app.models.session import RefreshSession
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
    Base.metadata.create_all(
        bind=engine,
        tables=[User.__table__, File.__table__, RefreshSession.__table__],
    )

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
    Base.metadata.drop_all(
        bind=engine,
        tables=[RefreshSession.__table__, File.__table__, User.__table__],
    )


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


def _register_and_login_as(
    client: TestClient,
    email: str,
    password: str,
    full_name: str,
) -> str:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
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


def test_list_files_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/files")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token."


def test_list_files_returns_paginated_owner_scoped_results_with_sorting(
    client: TestClient,
) -> None:
    owner_access_token = _register_and_login_as(
        client=client,
        email="owner@example.com",
        password="password123",
        full_name="Owner User",
    )
    intruder_access_token = _register_and_login_as(
        client=client,
        email="intruder@example.com",
        password="password123",
        full_name="Intruder User",
    )

    owner_upload_one = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {owner_access_token}"},
        files={"file": ("zeta.txt", b"zeta", "text/plain")},
    )
    owner_upload_two = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {owner_access_token}"},
        files={"file": ("alpha.txt", b"alpha", "text/plain")},
    )
    intruder_upload = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {intruder_access_token}"},
        files={"file": ("intruder.txt", b"intruder", "text/plain")},
    )

    assert owner_upload_one.status_code == 201
    assert owner_upload_two.status_code == 201
    assert intruder_upload.status_code == 201

    response = client.get(
        "/api/v1/files",
        headers={"Authorization": f"Bearer {owner_access_token}"},
        params={
            "limit": 1,
            "offset": 0,
            "sort_field": "original_name",
            "sort_direction": "asc",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["limit"] == 1
    assert payload["offset"] == 0
    assert payload["sort_field"] == "original_name"
    assert payload["sort_direction"] == "asc"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["original_name"] == "alpha.txt"
    assert payload["items"][0]["owner_id"] == 1

    second_page_response = client.get(
        "/api/v1/files",
        headers={"Authorization": f"Bearer {owner_access_token}"},
        params={
            "limit": 1,
            "offset": 1,
            "sort_field": "original_name",
            "sort_direction": "asc",
        },
    )

    assert second_page_response.status_code == 200
    second_page_payload = second_page_response.json()
    assert len(second_page_payload["items"]) == 1
    assert second_page_payload["items"][0]["original_name"] == "zeta.txt"


def test_download_returns_file_for_owner(client: TestClient) -> None:
    access_token = _register_and_login(client)
    upload_response = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("hello.txt", b"hello atlas", "text/plain")},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    download_response = client.get(
        f"/api/v1/files/{file_id}/download",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert download_response.status_code == 200
    assert download_response.content == b"hello atlas"
    assert download_response.headers["content-type"].startswith("text/plain")
    assert download_response.headers["content-disposition"] == 'attachment; filename="hello.txt"'
    assert (
        download_response.headers["x-checksum-sha256"]
        == hashlib.sha256(b"hello atlas").hexdigest()
    )


def test_download_rejects_invalid_owner_access(client: TestClient) -> None:
    owner_access_token = _register_and_login_as(
        client=client,
        email="owner@example.com",
        password="password123",
        full_name="Owner User",
    )
    intruder_access_token = _register_and_login_as(
        client=client,
        email="intruder@example.com",
        password="password123",
        full_name="Intruder User",
    )

    upload_response = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {owner_access_token}"},
        files={"file": ("secret.txt", b"owner-only", "text/plain")},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    intruder_download_response = client.get(
        f"/api/v1/files/{file_id}/download",
        headers={"Authorization": f"Bearer {intruder_access_token}"},
    )

    assert intruder_download_response.status_code == 404
    assert intruder_download_response.json()["detail"] == "File not found."


def test_download_returns_not_found_when_blob_missing(client: TestClient, tmp_path: Path) -> None:
    access_token = _register_and_login(client)
    upload_response = client.post(
        "/api/v1/files/upload",
        headers={"Authorization": f"Bearer {access_token}"},
        files={"file": ("hello.txt", b"hello atlas", "text/plain")},
    )
    assert upload_response.status_code == 201

    payload = upload_response.json()
    stored_path = tmp_path / payload["storage_key"]
    stored_path.unlink()

    download_response = client.get(
        f"/api/v1/files/{payload['id']}/download",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert download_response.status_code == 404
    assert download_response.json()["detail"] == "File content not found."
