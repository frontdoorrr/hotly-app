"""Database exceptions."""

from .base import HotlyException


class DatabaseError(HotlyException):
    """Raised when database operations fail."""
