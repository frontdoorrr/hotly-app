"""Content extraction service for SNS link analysis."""

import asyncio
import time
from urllib.parse import urlparse

from app.exceptions.external import UnsupportedPlatformError
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType


class ContentExtractor:
    """Extract content and metadata from SNS links."""

    def __init__(self) -> None:
        """Initialize content extractor."""
        self.timeout = 30  # 30 seconds timeout

    def _detect_platform(self, url: str) -> PlatformType:
        """Detect platform from URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if "instagram.com" in domain:
            return PlatformType.INSTAGRAM
        elif "blog.naver.com" in domain:
            return PlatformType.NAVER_BLOG
        elif "youtube.com" in domain or "youtu.be" in domain:
            return PlatformType.YOUTUBE
        else:
            raise UnsupportedPlatformError(f"Unsupported platform: {domain}")

    async def extract_content(self, url: str) -> ExtractedContent:
        """Extract content from URL."""
        start_time = time.time()

        try:
            platform = self._detect_platform(url)
            content = await self._extract_with_playwright(url, platform)

            # Calculate extraction time
            extraction_time = time.time() - start_time
            content.extraction_time = extraction_time

            return content

        except Exception as e:
            # Re-raise known exceptions without wrapping
            if isinstance(e, (UnsupportedPlatformError, TimeoutError)):
                raise
            # Wrap other exceptions
            raise Exception(f"Content extraction failed: {str(e)}")

    async def _extract_with_playwright(
        self, url: str, platform: PlatformType
    ) -> ExtractedContent:
        """Extract content using Playwright (mock implementation for testing)."""
        # This is a mock implementation for testing
        # Real implementation would use Playwright to scrape content

        # Simulate async processing
        await asyncio.sleep(0.1)

        # Return mock content based on platform
        if platform == PlatformType.INSTAGRAM:
            metadata = ContentMetadata(
                title="Amazing restaurant in Seoul",
                description="Great food and atmosphere!",
                images=["https://instagram.com/image1.jpg"],
                location="Seoul, South Korea",
                hashtags=["#food", "#seoul", "#restaurant"],
            )
        elif platform == PlatformType.NAVER_BLOG:
            metadata = ContentMetadata(
                title="Best places to visit in Gangnam",
                description="Food tour guide in Gangnam",
                images=["https://blog.image.jpg"],
                location="Gangnam, Seoul",
                hashtags=["#gangnam", "#food", "#travel"],
            )
        else:
            metadata = ContentMetadata(
                title="Content title", description="Content description"
            )

        return ExtractedContent(url=url, platform=platform, metadata=metadata)
