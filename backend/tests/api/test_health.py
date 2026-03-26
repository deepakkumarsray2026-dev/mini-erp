from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_has_status_field():
    response = client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]


def test_info_returns_modules():
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "modules" in data
    assert "workforce" in data["modules"]
