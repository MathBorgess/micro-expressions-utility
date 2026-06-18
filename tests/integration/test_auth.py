"""Testes do endpoint de login."""

from fastapi.testclient import TestClient

from app.security import verify_token


def test_login_success_returns_token(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "vendedor", "password": "changeme"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert verify_token(body["access_token"], "dev-secret-change-me") == "vendedor"


def test_login_wrong_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "vendedor", "password": "errada"},
    )
    assert response.status_code == 401


def test_login_validation_error(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={"username": "x"})
    assert response.status_code == 422
