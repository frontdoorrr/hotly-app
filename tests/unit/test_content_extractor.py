"""
Unit tests for ContentExtractor service.

Following TDD principles:
1. Test business logic in isolation
2. Mock all external dependencies
3. Cover edge cases and error conditions
4. Use descriptive test names following methodName_condition_expectedResult
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.external import ContentExtractionError, UnsupportedPlatformError
from app.schemas.content import ContentExtractResult
from app.services.content_extractor import ContentExtractor, Platform


class TestContentExtractor:
    """Unit tests for ContentExtractor service."""

    def setup_method(self):
        """Setup before each test."""
        self.extractor = ContentExtractor()

    # Platform detection tests
    def test_detect_platform_instagramPost_returnsInstagram(self):
        """Test Instagram post URL detection."""
        # Given
        instagram_urls = [
            "https://instagram.com/p/CXXXXXXXXXx/",
            "https://www.instagram.com/p/CXXXXXXXXXx/",
            "https://instagram.com/p/CXXXXXXXXXx",
            "http://instagram.com/p/CXXXXXXXXXx/",
        ]

        # When/Then
        for url in instagram_urls:
            platform = self.extractor._detect_platform(url)
            assert platform == Platform.INSTAGRAM

    def test_detect_platform_naverBlogPost_returnsNaverBlog(self):
        """Test Naver Blog URL detection."""
        # Given
        naver_urls = [
            "https://blog.naver.com/user/123456789",
            "https://blog.naver.com/user/123456789?param=value",
            "http://blog.naver.com/user/123456789",
        ]

        # When/Then
        for url in naver_urls:
            platform = self.extractor._detect_platform(url)
            assert platform == Platform.NAVER_BLOG

    def test_detect_platform_youtubeVideo_returnsYoutube(self):
        """Test YouTube URL detection."""
        # Given
        youtube_urls = [
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        ]

        # When/Then
        for url in youtube_urls:
            platform = self.extractor._detect_platform(url)
            assert platform == Platform.YOUTUBE

    def test_detect_platform_unsupportedUrl_raisesUnsupportedPlatformError(self):
        """Test error handling for unsupported platforms."""
        # Given
        unsupported_urls = [
            "https://facebook.com/post/123",
            "https://twitter.com/user/status/123",
            "https://tiktok.com/@user/video/123",
            "https://example.com/page",
            "not-a-url",
            "",
        ]

        # When/Then
        for url in unsupported_urls:
            with pytest.raises(UnsupportedPlatformError) as exc_info:
                self.extractor._detect_platform(url)
            assert f"Unsupported platform for URL: {url}" in str(exc_info.value)

    # Content extraction tests with mocking
    @pytest.mark.asyncio
    async def test_extract_content_instagramUrl_returnsValidContent(self):
        """Test successful Instagram content extraction."""
        # Given
        url = "https://instagram.com/p/test123/"
        expected_content = {
            "title": "Delicious Korean BBQ",
            "description": "Amazing Korean BBQ restaurant in Gangnam! #korean #bbq #food",
            "images": [
                "https://instagram.com/image1.jpg",
                "https://instagram.com/image2.jpg",
            ],
            "author": "food_blogger",
            "posted_at": "2024-01-15T14:30:00Z",
            "hashtags": ["korean", "bbq", "food"],
        }

        # Mock the platform-specific extractor
        with patch.object(
            self.extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = expected_content

            # When
            result = await self.extractor.extract_content(url)

            # Then
            assert isinstance(result, ContentExtractResult)
            assert result.success is True
            assert result.url == url
            assert result.platform == "instagram"
            assert result.title == expected_content["title"]
            assert result.description == expected_content["description"]
            assert result.images == expected_content["images"]
            assert result.hashtags == expected_content["hashtags"]
            assert result.author == expected_content["author"]
            assert result.posted_at == expected_content["posted_at"]
            assert result.extraction_time > 0

            # Verify the correct extractor was called
            mock_extract.assert_called_once_with(url)

    @pytest.mark.asyncio
    async def test_extract_content_naverBlogUrl_returnsValidContent(self):
        """Test successful Naver Blog content extraction."""
        # Given
        url = "https://blog.naver.com/foodlover/123456789"
        expected_content = {
            "title": "서울 맛집 추천",
            "description": "서울 강남 맛집 추천 포스팅입니다. #맛집 #강남 #한식",
            "images": ["https://blogfiles.pstatic.net/image1.jpg"],
            "author": "foodlover",
            "posted_at": "2024-01-10T10:00:00Z",
            "hashtags": ["맛집", "강남", "한식"],
        }

        with patch.object(
            self.extractor, "_extract_naver_blog_content", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = expected_content

            # When
            result = await self.extractor.extract_content(url)

            # Then
            assert result.success is True
            assert result.platform == "naver_blog"
            assert result.title == expected_content["title"]
            assert "강남 맛집" in result.description
            assert len(result.hashtags) == 3

    @pytest.mark.asyncio
    async def test_extract_content_extractionFails_raisesContentExtractionError(self):
        """Test error handling when content extraction fails."""
        # Given
        url = "https://instagram.com/p/private_post/"

        with patch.object(
            self.extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.side_effect = ContentExtractionError(
                "Post is private or deleted"
            )

            # When/Then
            with pytest.raises(ContentExtractionError) as exc_info:
                await self.extractor.extract_content(url)

            assert "Post is private or deleted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_content_networkError_retriesAndFails(self):
        """Test retry logic on network errors."""
        # Given
        url = "https://instagram.com/p/network_error/"

        with patch.object(
            self.extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            # Simulate network error on all retry attempts
            mock_extract.side_effect = ConnectionError("Network timeout")

            # When/Then
            with pytest.raises(ContentExtractionError) as exc_info:
                await self.extractor.extract_content(url)

            assert "Failed to extract content after retries" in str(exc_info.value)
            # Verify retry attempts were made
            assert mock_extract.call_count == self.extractor.max_retries

    # Edge cases and error conditions
    def test_detect_platform_invalidUrl_raisesUnsupportedPlatformError(self):
        """Test error handling for invalid URLs."""
        # Given
        invalid_urls = [None, "", "not-a-url", "ftp://invalid.com"]

        # When/Then
        for invalid_url in invalid_urls:
            with pytest.raises(UnsupportedPlatformError):
                self.extractor._detect_platform(invalid_url)

    @pytest.mark.asyncio
    async def test_extract_content_emptyResponse_handlesGracefully(self):
        """Test handling of empty content responses."""
        # Given
        url = "https://instagram.com/p/empty_post/"

        with patch.object(
            self.extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            # Return minimal valid content
            mock_extract.return_value = {
                "title": "",
                "description": "",
                "images": [],
                "author": "unknown",
                "posted_at": datetime.utcnow().isoformat(),
                "hashtags": [],
            }

            # When
            result = await self.extractor.extract_content(url)

            # Then
            assert result.success is True
            assert result.title == ""
            assert result.description == ""
            assert result.images == []
            assert result.hashtags == []

    # Performance and rate limiting tests
    @pytest.mark.asyncio
    async def test_extract_content_rateLimited_retriesAfterDelay(self):
        """Test rate limit handling."""
        # Given
        url = "https://instagram.com/p/rate_limited/"

        with patch.object(
            self.extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract, patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # First call: rate limited, second call: success
            mock_extract.side_effect = [
                ContentExtractionError("Rate limited", retry_after=5),
                {
                    "title": "Success after retry",
                    "description": "Content extracted successfully",
                    "images": [],
                    "author": "test_user",
                    "posted_at": datetime.utcnow().isoformat(),
                    "hashtags": [],
                },
            ]

            # When
            result = await self.extractor.extract_content(url)

            # Then
            assert result.success is True
            assert result.title == "Success after retry"
            # Verify sleep was called with rate limit delay
            mock_sleep.assert_called_with(5)
            assert mock_extract.call_count == 2

    # Parameterized tests for multiple scenarios
    @pytest.mark.parametrize(
        "platform,url_pattern,expected_platform",
        [
            (Platform.INSTAGRAM, "https://instagram.com/p/{}/", "instagram"),
            (Platform.NAVER_BLOG, "https://blog.naver.com/user/{}", "naver_blog"),
            (Platform.YOUTUBE, "https://youtube.com/watch?v={}", "youtube"),
        ],
    )
    @pytest.mark.asyncio
    async def test_extract_content_variousPlatforms_returnsCorrectPlatform(
        self, platform, url_pattern, expected_platform
    ):
        """Parameterized test for different platforms."""
        # Given
        url = url_pattern.format("test123")

        # Mock platform-specific extraction
        extractor_method = f"_extract_{expected_platform}_content"
        with patch.object(
            self.extractor, extractor_method, new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = {
                "title": f"Test {expected_platform} content",
                "description": "Test description",
                "images": [],
                "author": "test_user",
                "posted_at": datetime.utcnow().isoformat(),
                "hashtags": [],
            }

            # When
            result = await self.extractor.extract_content(url)

            # Then
            assert result.platform == expected_platform
            assert f"Test {expected_platform} content" in result.title

    # Mock validation tests
    def test_extractor_initialization_defaultValues_setsCorrectDefaults(self):
        """Test extractor initialization with default values."""
        # When
        extractor = ContentExtractor()

        # Then
        assert extractor.timeout == 30
        assert extractor.max_retries == 3
        assert extractor.rate_limit_delay == 1.0
        assert hasattr(extractor, "supported_platforms")

    def test_extractor_initialization_customValues_setsCustomValues(self):
        """Test extractor initialization with custom values."""
        # Given
        custom_timeout = 60
        custom_retries = 5

        # When
        extractor = ContentExtractor(timeout=custom_timeout, max_retries=custom_retries)

        # Then
        assert extractor.timeout == custom_timeout
        assert extractor.max_retries == custom_retries


# Test fixtures specific to this module
@pytest.fixture
def sample_instagram_response():
    """Sample Instagram API response."""
    return {
        "title": "Amazing Korean BBQ Experience! 🥩",
        "description": "Had the most incredible Korean BBQ at this hidden gem in Gangnam! The meat quality was outstanding and the side dishes were endless. Perfect for a date night! #korean #bbq #gangnam #food #restaurant #datenight",
        "images": [
            "https://scontent-nrt1-1.cdninstagram.com/image1.jpg",
            "https://scontent-nrt1-1.cdninstagram.com/image2.jpg",
            "https://scontent-nrt1-1.cdninstagram.com/image3.jpg",
        ],
        "author": "seoul_foodie_2024",
        "posted_at": "2024-01-15T19:30:45Z",
        "hashtags": ["korean", "bbq", "gangnam", "food", "restaurant", "datenight"],
        "likes_count": 1247,
        "comments_count": 89,
    }


@pytest.fixture
def sample_naver_blog_response():
    """Sample Naver Blog response."""
    return {
        "title": "강남 숨은 맛집 - 한우 전문점 후기",
        "description": "강남역 근처에 위치한 한우 전문점을 다녀왔습니다. 정말 맛있었어요! 가격은 조금 비싸지만 그만한 가치가 있습니다. 특히 등심이 정말 부드럽고 맛있었습니다. #맛집 #강남 #한우 #고기 #데이트",
        "images": [
            "https://blogfiles.pstatic.net/MjAyNDAxMTV/image1.jpg",
            "https://blogfiles.pstatic.net/MjAyNDAxMTV/image2.jpg",
        ],
        "author": "food_lover_kim",
        "posted_at": "2024-01-15T14:20:00Z",
        "hashtags": ["맛집", "강남", "한우", "고기", "데이트"],
        "view_count": 2456,
    }
