"""Authentication and authorization exceptions."""

from .base import HotlyException


class AuthenticationError(HotlyException):
    """Raised when authentication fails."""


class AuthorizationError(HotlyException):
    """Raised when user lacks required permissions."""
