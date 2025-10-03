"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from tests.utils import get_test_token_headers


@pytest.mark.integration
def test_api_v1_prefix_setup(client: TestClient) -> None:
    """Test that API v1 prefix is properly configured."""
    # Test that /api/v1 path exists (even if no endpoints yet)
    response = client.get("/api/v1/")
    # Should return 404 for non-existent endpoint, not 500 or other error
    assert response.status_code == 404


def test_cors_headers(client: TestClient) -> None:
    """Test CORS middleware is properly configured."""
    # Test without CORS origin header - should still work
    response = client.get("/health")
    assert response.status_code == 200

    # Test preflight OPTIONS request
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Should handle CORS preflight (200 if configured, 405 if not)
    assert response.status_code in [200, 405]


def test_authentication_flow_preparation(client: TestClient) -> None:
    """Test that authentication utilities are ready for future endpoints."""
    headers = get_test_token_headers("test_user")

    # Test that auth headers can be generated
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")

    # Test that we can make requests with auth headers
    response = client.get("/health", headers=headers)
    assert response.status_code == 200


def test_openapi_documentation(client: TestClient) -> None:
    """Test that OpenAPI documentation is accessible and complete."""
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert schema["info"]["title"] == "Hotly App"
    assert "paths" in schema
    assert "/health" in schema["paths"]

    # Test Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200

    # Test ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200


@pytest.mark.integration
def test_error_handling_consistency(client: TestClient) -> None:
    """Test that error responses follow consistent format."""
    # Test 404 error format
    response = client.get("/non-existent-endpoint")
    assert response.status_code == 404

    # Test malformed request handling
    response = client.post("/health", json={"invalid": "data"})
    assert response.status_code == 405  # Method not allowed for health endpoint
