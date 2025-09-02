"""Validation exceptions."""

from .base import HotlyException


class ValidationError(HotlyException):
    """Raised when input validation fails."""

