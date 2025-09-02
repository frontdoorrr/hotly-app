"""Test custom exception classes."""
import pytest

from app.exceptions.base import HotlyException
from app.exceptions.auth import AuthenticationError, AuthorizationError


def test_base_exception() -> None:
    """Test base exception class functionality."""
    # Test basic exception creation
    ex = HotlyException("Test error message")
    assert str(ex) == "Test error message"
    assert ex.message == "Test error message"
    assert ex.code == "HotlyException"
    assert ex.details == {}
    
    # Test exception with code and details
    details = {"field": "email", "value": "invalid"}
    ex_with_details = HotlyException(
        "Custom error", 
        code="CUSTOM_ERROR", 
        details=details
    )
    assert ex_with_details.message == "Custom error"
    assert ex_with_details.code == "CUSTOM_ERROR"
    assert ex_with_details.details == details


def test_auth_exceptions() -> None:
    """Test authentication exception hierarchy."""
    # Authentication error
    auth_ex = AuthenticationError("Authentication failed")
    assert str(auth_ex) == "Authentication failed"
    assert auth_ex.code == "AuthenticationError"
    assert isinstance(auth_ex, HotlyException)
    
    # Authorization error
    authz_ex = AuthorizationError("Insufficient permissions")
    assert str(authz_ex) == "Insufficient permissions"
    assert authz_ex.code == "AuthorizationError"
    assert isinstance(authz_ex, HotlyException)


def test_exception_inheritance() -> None:
    """Test that all exceptions inherit from HotlyException."""
    auth_ex = AuthenticationError("test")
    authz_ex = AuthorizationError("test")
    
    assert isinstance(auth_ex, HotlyException)
    assert isinstance(authz_ex, HotlyException)
    assert isinstance(auth_ex, Exception)
    assert isinstance(authz_ex, Exception)


def test_exception_with_custom_details() -> None:
    """Test exceptions with custom details."""
    details = {
        "user_id": "123",
        "attempted_action": "delete_post",
        "required_role": "admin"
    }
    
    ex = AuthorizationError(
        "User cannot delete post",
        code="INSUFFICIENT_ROLE",
        details=details
    )
    
    assert ex.message == "User cannot delete post"
    assert ex.code == "INSUFFICIENT_ROLE"
    assert ex.details["user_id"] == "123"
    assert ex.details["required_role"] == "admin"