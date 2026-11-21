"""Tests for root and health check endpoints."""

def test_root_endpoint(client):
    """Test GET / returns operational status and welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "FreshTrace" in data["message"]
    assert "docs" in data


def test_health_endpoint(client):
    """Test GET /health returns database status and provider configuration state."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database_connected" in data
    assert "providers" in data
    assert "bifrost" in data["providers"]
    assert "tavily" in data["providers"]
