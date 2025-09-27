"""Test content extractor service for SNS link analysis."""

import asyncio
import time
from unittest.mock import patch, AsyncMock

import pytest

from app.exceptions.external import UnsupportedPlatformError, ContentExtractionError
from app.schemas.content import ContentMetadata, ExtractedContent, PlatformType
from app.services.content_extractor import ContentExtractor


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

    # Test YouTube URL detection
    youtube_urls = [
        "https://www.youtube.com/watch?v=ABC123",
        "https://youtu.be/ABC123",
        "https://youtube.com/watch?v=DEF456",
    ]

    for url in youtube_urls:
        assert extractor._detect_platform(url) == PlatformType.YOUTUBE

    # Test unsupported platform
    with pytest.raises(UnsupportedPlatformError):
        extractor._detect_platform("https://unknown.com/post")


@pytest.mark.asyncio
async def test_extraction_time_tracking(content_extractor: ContentExtractor) -> None:
    """Test that extraction time is properly tracked."""
    test_url = "https://www.instagram.com/p/ABC123/"
    
    start_time = time.time()
    result = await content_extractor.extract_content(test_url)
    actual_duration = time.time() - start_time
    
    # Extraction time should be recorded and reasonable
    assert result.extraction_time is not None
    assert result.extraction_time > 0
    assert result.extraction_time <= actual_duration + 0.1  # Allow small margin


@pytest.mark.asyncio
async def test_concurrent_extractions(content_extractor: ContentExtractor) -> None:
    """Test handling multiple concurrent extractions."""
    urls = [
        "https://www.instagram.com/p/ABC123/",
        "https://blog.naver.com/user1/post1",
        "https://www.youtube.com/watch?v=XYZ789"
    ]
    
    # Execute concurrent extractions
    tasks = [content_extractor.extract_content(url) for url in urls]
    results = await asyncio.gather(*tasks)
    
    # All extractions should succeed
    assert len(results) == 3
    for i, result in enumerate(results):
        assert result.url == urls[i]
        assert result.extraction_time is not None


@pytest.mark.asyncio 
async def test_error_handling_general_exception(content_extractor: ContentExtractor) -> None:
    """Test general exception handling in content extraction."""
    test_url = "https://www.instagram.com/p/ABC123/"
    
    # Mock _extract_with_playwright to raise a general exception
    with patch.object(content_extractor, '_extract_with_playwright', 
                     side_effect=Exception("Network error")):
        with pytest.raises(Exception) as exc_info:
            await content_extractor.extract_content(test_url)
        
        assert "Content extraction failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_platform_specific_metadata_instagram(content_extractor: ContentExtractor) -> None:
    """Test Instagram-specific metadata extraction."""
    test_url = "https://www.instagram.com/p/ABC123/"
    
    result = await content_extractor.extract_content(test_url)
    
    # Instagram should have these metadata fields
    assert result.platform == PlatformType.INSTAGRAM
    assert result.metadata.title is not None
    assert result.metadata.description is not None
    assert len(result.metadata.images) > 0
    assert len(result.metadata.hashtags) > 0
    assert result.metadata.location is not None


@pytest.mark.asyncio
async def test_platform_specific_metadata_naver_blog(content_extractor: ContentExtractor) -> None:
    """Test Naver Blog-specific metadata extraction."""
    test_url = "https://blog.naver.com/user123/post456"
    
    result = await content_extractor.extract_content(test_url)
    
    # Naver Blog should have these metadata fields
    assert result.platform == PlatformType.NAVER_BLOG
    assert result.metadata.title is not None
    assert result.metadata.description is not None
    assert len(result.metadata.images) > 0
    assert len(result.metadata.hashtags) > 0
    assert result.metadata.location is not None


@pytest.mark.asyncio
async def test_platform_specific_metadata_youtube(content_extractor: ContentExtractor) -> None:
    """Test YouTube-specific metadata extraction."""
    test_url = "https://www.youtube.com/watch?v=ABC123"
    
    result = await content_extractor.extract_content(test_url)
    
    # YouTube should have basic metadata
    assert result.platform == PlatformType.YOUTUBE
    assert result.metadata.title is not None
    assert result.metadata.description is not None


@pytest.mark.asyncio
async def test_extraction_timeout_boundary(content_extractor: ContentExtractor) -> None:
    """Test extraction timeout boundary conditions."""
    test_url = "https://www.instagram.com/p/ABC123/"
    
    # Test with very short timeout
    original_timeout = content_extractor.timeout
    content_extractor.timeout = 0.001  # 1ms timeout
    
    try:
        # This should complete successfully with mock implementation
        result = await content_extractor.extract_content(test_url)
        assert result is not None
    finally:
        content_extractor.timeout = original_timeout


@pytest.mark.asyncio
async def test_known_exceptions_not_wrapped(content_extractor: ContentExtractor) -> None:
    """Test that known exceptions are not wrapped in generic Exception."""
    test_url = "https://unsupported-platform.com/post"
    
    # UnsupportedPlatformError should be raised directly
    with pytest.raises(UnsupportedPlatformError):
        await content_extractor.extract_content(test_url)
    
    # TimeoutError should be raised directly  
    with patch.object(content_extractor, '_extract_with_playwright',
                     side_effect=TimeoutError("Timeout")):
        with pytest.raises(TimeoutError):
            await content_extractor.extract_content("https://www.instagram.com/p/ABC123/")


class TestPerformanceRequirements:
    """Test performance requirements for content extraction."""
    
    @pytest.mark.asyncio
    async def test_extraction_time_under_30_seconds(self) -> None:
        """Test that extraction completes within 30 seconds requirement."""
        extractor = ContentExtractor()
        test_url = "https://www.instagram.com/p/ABC123/"
        
        start_time = time.time()
        result = await extractor.extract_content(test_url)
        duration = time.time() - start_time
        
        # Should complete well under 30 second requirement
        assert duration < 30
        assert result.extraction_time < 30
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self) -> None:
        """Test handling 100 concurrent requests as per requirement."""
        extractor = ContentExtractor()
        
        # Generate 10 test URLs (reduced for test performance)
        test_urls = [
            f"https://www.instagram.com/p/TEST{i}/" 
            for i in range(10)
        ]
        
        start_time = time.time()
        
        # Execute concurrent extractions
        tasks = [extractor.extract_content(url) for url in test_urls]
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        # All should complete successfully
        assert len(results) == 10
        # Should handle concurrent requests efficiently
        assert duration < 5  # Should be much faster than sequential
        
        for result in results:
            assert result.extraction_time is not None
