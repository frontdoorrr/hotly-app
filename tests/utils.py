"""Test utilities for common testing operations."""
from typing import Dict

from fastapi.testclient import TestClient

from app.core.security import create_access_token


def get_test_token_headers(user_id: str = "test_user") -> Dict[str, str]:
    """Generate test authentication headers."""
    access_token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {access_token}"}


def create_test_client_with_auth(user_id: str = "test_user") -> TestClient:
    """Create test client with authentication headers."""
    from app.main import app

    client = TestClient(app)
    headers = get_test_token_headers(user_id)
    client.headers.update(headers)
    return client
