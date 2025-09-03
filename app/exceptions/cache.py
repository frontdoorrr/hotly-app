"""
Cache-related exception classes.

Follows domain-driven design with specific cache exceptions.
"""

from app.exceptions.base import HotlyException


class CacheConnectionError(HotlyException):
    """Cache connection failed."""

    def __init__(self, message: str = "Cache connection failed"):
        super().__init__(message)


class CacheLockTimeoutError(HotlyException):
    """Cache distributed lock timeout."""

    def __init__(self, message: str = "Cache lock acquisition timeout"):
        super().__init__(message)


class CacheSerializationError(HotlyException):
    """Cache data serialization/deserialization failed."""

    def __init__(self, message: str = "Cache data serialization failed"):
        super().__init__(message)
