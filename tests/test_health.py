"""
Tests for root and health/diagnostic endpoints.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "FastAPI-python-Antigravity"
    assert data["status"] == "running"
    assert "docs" in data


def test_healthz_endpoint(client: TestClient):
    response = client.get("/healthz")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "success"
    assert json_data["data"]["status"] == "healthy"
    assert "uptime_seconds" in json_data["data"]
    assert "python_version" in json_data["data"]


def test_system_info_endpoint(client: TestClient):
    response = client.get("/api/v1/system/info")
    assert response.status_code == 200
    json_data = response.json()
    assert "architecture" in json_data["data"]
    assert "endpoints_worked_on" in json_data["data"]
    assert len(json_data["data"]["endpoints_worked_on"]) >= 3
