"""Test security and authentication functionality."""

from datetime import timedelta

from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hashing() -> None:
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = get_password_hash(password)

    # Hash should be different from original password
    assert hashed != password

    # Should verify correctly
    assert verify_password(password, hashed) is True

    # Should fail with wrong password
    assert verify_password("wrong_password", hashed) is False


def test_jwt_token_creation() -> None:
    """Test JWT token creation."""
    subject = "test_user"
    token = create_access_token(subject=subject)

    # Token should be created
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_jwt_token_with_expiration() -> None:
    """Test JWT token creation with custom expiration."""
    subject = "test_user"
    expires_delta = timedelta(minutes=30)
    token = create_access_token(subject=subject, expires_delta=expires_delta)

    # Token should be created
    assert token is not None
    assert isinstance(token, str)
