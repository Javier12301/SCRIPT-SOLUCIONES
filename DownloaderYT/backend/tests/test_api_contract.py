from __future__ import annotations

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


def test_register_requires_admin(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert response.status_code == 401


def test_admin_can_register_user_and_user_can_login(client: TestClient) -> None:
    login_admin = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "admin1234"},
    )
    assert login_admin.status_code == 200

    register_response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["user"]["username"] == "newuser"
    assert register_response.json()["user"]["role"] == "user"

    duplicate_response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert duplicate_response.status_code == 409

    client.post("/api/auth/logout")
    user_login = client.post(
        "/api/auth/login",
        json={"username": "newuser", "password": "newuser123"},
    )
    assert user_login.status_code == 200

    forbidden_register = client.post(
        "/api/auth/register",
        json={"username": "otheruser", "password": "otheruser123"},
    )
    assert forbidden_register.status_code == 403
