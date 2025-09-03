"""Test content extractor service for SNS link analysis."""
from unittest.mock import patch

import pytest

from app.exceptions.external import UnsupportedPlatformError
from app.schemas.content import ContentMetadata, ExtractedContent
from app.services.content_extractor import ContentExtractor, PlatformType


@pytest.fixture
def content_extractor() -> ContentExtractor:
    """Create content extractor instance."""
    return ContentExtractor()


@pytest.mark.asyncio
async def test_extract_instagram_content(content_extractor: ContentExtractor) -> None:
    """Test Instagram content extraction."""
    # Mock Instagram URL
    instagram_url = "https://www.instagram.com/p/ABC123/"

    # Mock expected metadata
    expected_content = ExtractedContent(
        url=instagram_url,
        platform=PlatformType.INSTAGRAM,
        metadata=ContentMetadata(
            title="Amazing restaurant in Seoul",
            description="Great food and atmosphere!",
            images=["https://instagram.com/image1.jpg"],
            location="Seoul, South Korea",
            hashtags=["#food", "#seoul", "#restaurant"],
        ),
    )

    with patch.object(content_extractor, "_extract_with_playwright") as mock_extract:
        mock_extract.return_value = expected_content

        result = await content_extractor.extract_content(instagram_url)

        assert result.url == instagram_url
        assert result.platform == PlatformType.INSTAGRAM
        assert result.metadata.title == "Amazing restaurant in Seoul"
        assert len(result.metadata.images) > 0


@pytest.mark.asyncio
async def test_extract_blog_content(content_extractor: ContentExtractor) -> None:
    """Test blog content extraction."""
    blog_url = "https://blog.naver.com/user/post123"

    expected_content = ExtractedContent(
        url=blog_url,
        platform=PlatformType.NAVER_BLOG,
        metadata=ContentMetadata(
            title="Best places to visit in Gangnam",
            description="Food tour guide in Gangnam",
            images=["https://blog.image.jpg"],
            location="Gangnam, Seoul",
            hashtags=["#gangnam", "#food", "#travel"],
        ),
    )

    with patch.object(content_extractor, "_extract_with_playwright") as mock_extract:
        mock_extract.return_value = expected_content

        result = await content_extractor.extract_content(blog_url)

        assert result.platform == PlatformType.NAVER_BLOG
        assert result.metadata.location == "Gangnam, Seoul"


@pytest.mark.asyncio
async def test_unsupported_platform_error(content_extractor: ContentExtractor) -> None:
    """Test that unsupported platforms raise appropriate error."""
    unsupported_url = "https://unknown-platform.com/post/123"

    with pytest.raises(UnsupportedPlatformError) as exc_info:
        await content_extractor.extract_content(unsupported_url)

    assert "unsupported platform" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_extraction_timeout_handling(content_extractor: ContentExtractor) -> None:
    """Test that extraction handles timeouts gracefully."""
    test_url = "https://www.instagram.com/p/timeout/"

    with patch.object(content_extractor, "_extract_with_playwright") as mock_extract:
        mock_extract.side_effect = TimeoutError("Extraction timeout")

        with pytest.raises(TimeoutError):
            await content_extractor.extract_content(test_url)


def test_platform_detection() -> None:
    """Test URL platform detection."""
    extractor = ContentExtractor()

    # Test Instagram URL detection
    instagram_urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://instagram.com/p/DEF456/",
        "https://www.instagram.com/reel/GHI789/",
    ]

    for url in instagram_urls:
        assert extractor._detect_platform(url) == PlatformType.INSTAGRAM

    # Test Naver Blog URL detection
    blog_urls = [
        "https://blog.naver.com/user123/post456",
        "http://blog.naver.com/foodie/789",
    ]

    for url in blog_urls:
        assert extractor._detect_platform(url) == PlatformType.NAVER_BLOG

    # Test unsupported platform
    with pytest.raises(UnsupportedPlatformError):
        extractor._detect_platform("https://unknown.com/post")
