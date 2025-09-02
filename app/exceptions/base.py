"""Base exception classes for the application."""
from typing import Any, Dict, Optional


class HotlyException(Exception):
    """Base exception for all Hotly app exceptions."""

    def __init__(
        self, 
        message: str, 
        code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
