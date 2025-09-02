"""External service exceptions."""

from .base import HotlyException


class ExternalServiceError(HotlyException):
    """Raised when external service calls fail."""

