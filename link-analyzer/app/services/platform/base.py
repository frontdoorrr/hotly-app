"""Base interface for platform-specific metadata extraction."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms."""

    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ContentType(str, Enum):
    """Content type classification."""

    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"


class PlatformExtractor(ABC):
    """Base interface for platform-specific metadata extraction."""

    @abstractmethod
    async def extract_metadata(self, url: str) -> Dict[str, Any]:
        """
        Extract metadata from platform URL.

        Args:
            url: Platform-specific URL to analyze

        Returns:
            Dictionary containing:
                - platform: Platform enum value
                - content_type: ContentType enum value
                - url: Original URL
                - title: Content title
                - description: Content description
                - hashtags: List of hashtags
                - media_urls: Optional list of downloaded media file paths
                - metadata: Platform-specific additional information

        Raises:
            ValueError: If URL is invalid or cannot be processed
            HTTPException: If platform API returns an error
        """
        pass

    @staticmethod
    def detect_platform(url: str) -> Optional[Platform]:
        """
        Auto-detect platform from URL.

        Args:
            url: URL to analyze

        Returns:
            Platform enum if detected, None otherwise

        Examples:
            >>> PlatformExtractor.detect_platform("https://youtube.com/watch?v=abc")
            Platform.YOUTUBE
            >>> PlatformExtractor.detect_platform("https://instagram.com/p/abc/")
            Platform.INSTAGRAM
        """
        if "youtube.com" in url or "youtu.be" in url:
            return Platform.YOUTUBE
        elif "instagram.com" in url:
            return Platform.INSTAGRAM
        elif "tiktok.com" in url:
            return Platform.TIKTOK
        return None
