"""Link analyzer service for extracting information from URLs."""
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import httpx

from app.schemas.link import LinkAnalysisResponse


class LinkAnalyzerService:
    """Service for analyzing URLs and extracting information."""

    PLATFORM_PATTERNS = {
        "instagram": r"instagram\.com",
        "naver_blog": r"blog\.naver\.com",
        "tistory": r"tistory\.com",
        "youtube": r"youtube\.com|youtu\.be",
        "kakao": r"map\.kakao\.com|place\.map\.kakao\.com",
    }

    async def analyze_url(self, url: str) -> LinkAnalysisResponse:
        """
        Analyze a URL and extract relevant information.

        Args:
            url: URL to analyze

        Returns:
            LinkAnalysisResponse with extracted information

        Raises:
            ValueError: If URL is invalid or cannot be analyzed
        """
        # Detect platform
        platform = self._detect_platform(url)

        # Extract basic information
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()

                # Extract title and description from HTML
                title = self._extract_title(response.text)
                description = self._extract_description(response.text)

        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch URL: {str(e)}")

        # Build metadata
        metadata = {
            "final_url": str(response.url),
            "status_code": response.status_code,
        }

        return LinkAnalysisResponse(
            url=url,
            title=title,
            description=description,
            platform=platform,
            content_type=None,  # To be enhanced with AI analysis
            metadata=metadata,
        )

    def _detect_platform(self, url: str) -> Optional[str]:
        """
        Detect the platform from URL.

        Args:
            url: URL to analyze

        Returns:
            Platform name or None
        """
        for platform, pattern in self.PLATFORM_PATTERNS.items():
            if re.search(pattern, url, re.IGNORECASE):
                return platform
        return None

    def _extract_title(self, html: str) -> Optional[str]:
        """
        Extract title from HTML.

        Args:
            html: HTML content

        Returns:
            Title or None
        """
        # Try og:title first
        og_title = re.search(
            r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']',
            html,
            re.IGNORECASE
        )
        if og_title:
            return og_title.group(1)

        # Fall back to <title> tag
        title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        if title:
            return title.group(1)

        return None

    def _extract_description(self, html: str) -> Optional[str]:
        """
        Extract description from HTML.

        Args:
            html: HTML content

        Returns:
            Description or None
        """
        # Try og:description first
        og_desc = re.search(
            r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']',
            html,
            re.IGNORECASE
        )
        if og_desc:
            return og_desc.group(1)

        # Fall back to meta description
        meta_desc = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
            html,
            re.IGNORECASE
        )
        if meta_desc:
            return meta_desc.group(1)

        return None
