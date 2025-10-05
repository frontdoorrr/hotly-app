"""AI service exceptions."""

from .base import HotlyException


class AIAnalysisError(HotlyException):
    """Base exception for AI analysis operations."""


class RateLimitError(AIAnalysisError):
    """AI service rate limit exceeded."""


class InvalidResponseError(AIAnalysisError):
    """AI response format is invalid."""


class AIServiceUnavailableError(AIAnalysisError):
    """AI service is temporarily unavailable."""
