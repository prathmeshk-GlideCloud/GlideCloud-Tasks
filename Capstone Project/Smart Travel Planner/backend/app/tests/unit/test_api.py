"""
Integration tests for API endpoints
"""
import pytest


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_google_maps_health(client):
    """Test Google Maps health check"""
    response = client.get("/api/health/google-maps")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"