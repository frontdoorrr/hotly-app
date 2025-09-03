"""External service exceptions."""

from .base import HotlyException


class UnsupportedPlatformError(HotlyException):
    """Raised when a platform is not supported for content extraction."""


class ExternalServiceError(HotlyException):
    """Raised when external service calls fail."""
