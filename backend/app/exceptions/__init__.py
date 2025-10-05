"""Domain-specific exception classes."""

from .auth import AuthenticationError, AuthorizationError
from .base import HotlyException
from .database import DatabaseError
from .external import ExternalServiceError
from .validation import ValidationError

__all__ = [
    "HotlyException",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "DatabaseError",
    "ExternalServiceError",
]
