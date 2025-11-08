"""Unit tests for platform extractors."""

import pytest
from app.services.platform.base import PlatformExtractor, Platform, ContentType
from app.services.platform.youtube import YouTubeExtractor


class TestPlatformDetection:
    """Test platform auto-detection."""

    def test_detect_youtube(self):
        """YouTube URL detection."""
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/abc123",
        ]
        for url in urls:
            assert PlatformExtractor.detect_platform(url) == Platform.YOUTUBE

    def test_detect_instagram(self):
        """Instagram URL detection."""
        urls = [
            "https://www.instagram.com/p/abc123/",
            "https://instagram.com/reel/xyz789/",
        ]
        for url in urls:
            assert PlatformExtractor.detect_platform(url) == Platform.INSTAGRAM

    def test_detect_tiktok(self):
        """TikTok URL detection."""
        urls = [
            "https://www.tiktok.com/@user/video/123456",
            "https://tiktok.com/@user/video/789012",
        ]
        for url in urls:
            assert PlatformExtractor.detect_platform(url) == Platform.TIKTOK

    def test_unknown_platform(self):
        """Unknown platform returns None."""
        url = "https://twitter.com/status/123"
        assert PlatformExtractor.detect_platform(url) is None


class TestYouTubeExtractor:
    """Test YouTube extractor."""

    def test_extract_video_id_standard(self):
        """Extract video ID from standard URL."""
        extractor = YouTubeExtractor(api_key="fake_key")

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = extractor._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short(self):
        """Extract video ID from short URL."""
        extractor = YouTubeExtractor(api_key="fake_key")

        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = extractor._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_shorts(self):
        """Extract video ID from Shorts URL."""
        extractor = YouTubeExtractor(api_key="fake_key")

        url = "https://www.youtube.com/shorts/abc123"
        video_id = extractor._extract_video_id(url)
        assert video_id == "abc123"

    def test_extract_video_id_invalid(self):
        """Invalid URL raises ValueError."""
        extractor = YouTubeExtractor(api_key="fake_key")

        url = "https://www.youtube.com/invalid"
        with pytest.raises(ValueError, match="Could not extract video ID"):
            extractor._extract_video_id(url)

    def test_is_shorts(self):
        """Detect YouTube Shorts."""
        assert YouTubeExtractor.is_shorts("https://www.youtube.com/shorts/abc123")
        assert not YouTubeExtractor.is_shorts("https://www.youtube.com/watch?v=abc123")


# Note: Instagram and TikTok extractors require yt-dlp and network access
# Skip for now - will test in integration tests
