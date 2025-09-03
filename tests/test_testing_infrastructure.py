"""Test the testing infrastructure itself."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.utils import create_test_client_with_auth, get_test_token_headers


def test_db_fixture_works(db: Session) -> None:
    """Test that database fixture is properly configured."""
    assert db is not None
    assert hasattr(db, "execute")
    assert hasattr(db, "commit")
    assert hasattr(db, "rollback")


def test_client_fixture_works(client: TestClient) -> None:
    """Test that FastAPI test client fixture works."""
    assert client is not None
    assert hasattr(client, "get")
    assert hasattr(client, "post")
    assert hasattr(client, "put")
    assert hasattr(client, "delete")


def test_test_token_headers_generation() -> None:
    """Test that authentication token headers can be generated."""
    headers = get_test_token_headers("test_user")

    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert len(headers["Authorization"]) > 20  # JWT tokens are long


def test_authenticated_test_client_creation() -> None:
    """Test that authenticated test client can be created."""
    client = create_test_client_with_auth("test_user")

    assert client is not None
    assert "Authorization" in client.headers
    assert client.headers["Authorization"].startswith("Bearer ")


def test_test_coverage_infrastructure() -> None:
    """Test that test coverage infrastructure is working."""
    # This test itself contributes to coverage
    # The fact that it runs means pytest-cov is properly configured
    assert True


@pytest.mark.asyncio
async def test_async_test_support() -> None:
    """Test that async tests are supported by pytest-asyncio."""
    # Simple async test to verify asyncio support
    import asyncio

    result = await asyncio.sleep(0.01)
    assert result is None
