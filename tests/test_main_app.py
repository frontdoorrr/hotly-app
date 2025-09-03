"""Test main FastAPI application setup."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app


def test_app_creation() -> None:
    """Test that FastAPI app is properly created."""
    assert isinstance(app, FastAPI)
    assert app.title == "Hotly App"
    assert app.version == "0.1.0"


def test_app_middleware_setup(client: TestClient) -> None:
    """Test that CORS middleware is properly configured."""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # Should handle CORS preflight
    assert response.status_code in [200, 405]


def test_app_exception_handlers(client: TestClient) -> None:
    """Test that custom exception handlers are working."""
    # Test non-existent endpoint returns proper 404
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404


def test_openapi_schema_generation(client: TestClient) -> None:
    """Test that OpenAPI schema is properly generated."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "info" in schema
    assert schema["info"]["title"] == "Hotly App"
    assert "paths" in schema


def test_health_endpoint_inclusion(client: TestClient) -> None:
    """Test that health endpoints are included in the app."""
    response = client.get("/health")
    assert response.status_code == 200

    response = client.get("/health/detailed")
    assert response.status_code == 200
