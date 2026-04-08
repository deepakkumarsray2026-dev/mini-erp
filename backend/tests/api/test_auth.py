from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_endpoint_exists():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "wrong"},
    )
    # 401 means endpoint exists and auth is working
    assert response.status_code == 401


def test_me_requires_auth():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_refresh_invalid_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"},
    )
    assert response.status_code == 401


def test_logout_invalid_token():
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "invalid.token.here"},
    )
    # Logout with invalid token should still succeed gracefully
    assert response.status_code in [200, 401]
