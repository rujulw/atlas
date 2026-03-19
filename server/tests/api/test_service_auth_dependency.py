from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.deps import AuthenticatedServiceContext, require_service_auth
from app.services.auth import InternalServicePrincipal, JWTAccessTokenService


def _make_service_token(
    *,
    service_name: str = "media-service",
    audience: str = "atlas-internal",
    can_act_as_user: bool = False,
    acting_user_id: str | None = None,
) -> str:
    token_service = JWTAccessTokenService(
        secret_key="change-me",
        expires_minutes=30,
        issuer="atlas",
        audience="atlas-api",
        internal_service_expires_minutes=5,
    )
    principal = InternalServicePrincipal(
        service_name=service_name,
        audience=audience,
        can_act_as_user=can_act_as_user,
    )
    return token_service.issue_service_token(
        principal,
        acting_user_id=acting_user_id,
    )


def test_service_auth_dependency_accepts_valid_service_token() -> None:
    app = FastAPI()

    @app.get("/internal")
    async def internal_route(
        service: AuthenticatedServiceContext = Depends(
            require_service_auth(
                expected_audience="atlas-internal",
                allowed_service_names=("media-service",),
            )
        ),
    ) -> dict[str, str | None]:
        return {
            "service_name": service.service_name,
            "acting_user_id": service.acting_user_id,
        }

    client = TestClient(app)
    token = _make_service_token(service_name="media-service", audience="atlas-internal")

    response = client.get(
        "/internal",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "service_name": "media-service",
        "acting_user_id": None,
    }


def test_service_auth_dependency_rejects_wrong_service_name() -> None:
    app = FastAPI()

    @app.get("/internal")
    async def internal_route(
        service: AuthenticatedServiceContext = Depends(
            require_service_auth(
                expected_audience="atlas-internal",
                allowed_service_names=("media-service",),
            )
        ),
    ) -> dict[str, str | None]:
        return {
            "service_name": service.service_name,
            "acting_user_id": service.acting_user_id,
        }

    client = TestClient(app)
    token = _make_service_token(service_name="indexer", audience="atlas-internal")

    response = client.get(
        "/internal",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Service principal is not allowed."


def test_service_auth_dependency_rejects_missing_acting_user_when_required() -> None:
    app = FastAPI()

    @app.get("/internal")
    async def internal_route(
        service: AuthenticatedServiceContext = Depends(
            require_service_auth(
                expected_audience="atlas-internal",
                allowed_service_names=("media-service",),
                require_acting_user=True,
            )
        ),
    ) -> dict[str, str | None]:
        return {
            "service_name": service.service_name,
            "acting_user_id": service.acting_user_id,
        }

    client = TestClient(app)
    token = _make_service_token(
        service_name="media-service",
        audience="atlas-internal",
        can_act_as_user=True,
    )

    response = client.get(
        "/internal",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Service principal must include acting user context."


def test_service_auth_dependency_accepts_acting_user_context_when_required() -> None:
    app = FastAPI()

    @app.get("/internal")
    async def internal_route(
        service: AuthenticatedServiceContext = Depends(
            require_service_auth(
                expected_audience="atlas-internal",
                allowed_service_names=("media-service",),
                require_acting_user=True,
            )
        ),
    ) -> dict[str, str | None]:
        return {
            "service_name": service.service_name,
            "acting_user_id": service.acting_user_id,
        }

    client = TestClient(app)
    token = _make_service_token(
        service_name="media-service",
        audience="atlas-internal",
        can_act_as_user=True,
        acting_user_id="42",
    )

    response = client.get(
        "/internal",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "service_name": "media-service",
        "acting_user_id": "42",
    }
