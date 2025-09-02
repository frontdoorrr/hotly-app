"""Test basic API functionality."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_api_root_exists(client: TestClient) -> None:
    """Test that API root endpoint exists."""
    response = client.get("/")
    # Should not return 404
    assert response.status_code != 404


def test_api_docs_accessible(client: TestClient) -> None:
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_api_health_endpoint_exists(client: TestClient) -> None:
    """Test that health endpoint exists."""
    response = client.get("/health")
    # Health endpoint is now implemented
    assert response.status_code == 200
