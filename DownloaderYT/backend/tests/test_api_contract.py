from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_healthcheck_endpoint(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_me_logout_flow(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["username"] == "admin"

    me_response = client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.json()["user"]["role"] == "admin"

    logout_response = client.post("/api/auth/logout")
    assert logout_response.status_code == 200
    assert "logout ok" in logout_response.json()["message"]

    me_after_logout = client.get("/api/auth/me")
    assert me_after_logout.status_code == 401


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "bad-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_me_requires_auth_cookie(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.parametrize(
    ("method", "path", "expected_message"),
    [
        ("post", "/api/jobs", "Fase 4: create job pendiente"),
        ("get", "/api/jobs", "Fase 4: list jobs pendiente"),
        ("get", "/api/jobs/123", "Fase 4: get job pendiente"),
        ("post", "/api/jobs/123/cancel", "Fase 4: cancel job pendiente"),
        ("post", "/api/items/9/retry", "Fase 4: retry item pendiente"),
        ("get", "/api/items/9/download", "Fase 4: download item pendiente"),
        ("get", "/api/events", "Fase 4: SSE pendiente"),
    ],
)
def test_phase4_placeholders_remain(method: str, path: str, expected_message: str, client: TestClient) -> None:
    response = getattr(client, method)(path)
    assert response.status_code == 200
    assert response.json()["message"] == expected_message


def test_admin_endpoint_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/admin/update-extractor")
    assert response.status_code == 401


def test_admin_endpoint_allows_admin_user(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    assert login_response.status_code == 200

    response = client.post("/api/admin/update-extractor")
    assert response.status_code == 200
    assert response.json()["message"] == "Fase 4: admin update extractor pendiente"
