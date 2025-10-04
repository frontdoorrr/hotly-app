"""
Unit tests for PlaceAnalysisService.

Tests AI-powered place information extraction from content.
Focuses on business logic, error handling, and service integration.
"""

from unittest.mock import Mock, patch

import pytest

from app.exceptions.ai import AIAnalysisError, RateLimitError
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentMetadata
from app.services.places.place_analysis_service import (
    PlaceAnalysisResult,
    PlaceAnalysisService,
)


class TestPlaceAnalysisService:
    """Unit tests for PlaceAnalysisService."""

    def setup_method(self):
        """Setup before each test."""
        self.service = PlaceAnalysisService()

    # Success path tests
    @pytest.mark.asyncio
    async def test_analyze_content_restaurantContent_returnsPlaceInfo(self):
        """Test successful place analysis for restaurant content."""
        # Given
        content = ContentMetadata(
            title="Amazing Korean BBQ Restaurant",
            description="Best Korean BBQ in Gangnam! Great atmosphere and delicious meat. Located near Gangnam Station. #korean #bbq #gangnam #restaurant",
            images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            hashtags=["korean", "bbq", "gangnam", "restaurant"],
        )

        expected_place_info = PlaceInfo(
            name="Gangnam Korean BBQ House",
            category="restaurant",
            address="Gangnam-gu, Seoul, South Korea",
            description="Korean BBQ restaurant known for high-quality meat",
            phone="+82-2-555-1234",
            website="https://gangnam-bbq.com",
            keywords=["korean", "bbq", "meat", "gangnam", "dining"],
            confidence=0.92,
        )

        # Mock the AI analyzer
        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.return_value = expected_place_info

            # When
            result = await self.service.analyze_content(content, content.images)

            # Then
            assert isinstance(result, PlaceAnalysisResult)
            assert result.success is True
            assert result.place_info == expected_place_info
            assert result.confidence == 0.92
            assert result.analysis_time > 0
            assert result.model_version is not None
            assert result.error is None

            # Verify AI analyzer was called correctly
            mock_analyzer.analyze_place_content.assert_called_once()
            call_args = mock_analyzer.analyze_place_content.call_args
            assert call_args[0][0] == content  # First argument is content
            assert call_args[0][1] == content.images  # Second argument is images

    @pytest.mark.asyncio
    async def test_analyze_content_cafeContent_returnsCafeInfo(self):
        """Test place analysis for cafe content."""
        # Given
        content = ContentMetadata(
            title="Cozy Coffee Shop in Hongdae",
            description="Perfect spot for studying and meetings. Great coffee and quiet atmosphere. #cafe #coffee #hongdae #study",
            images=["https://example.com/cafe1.jpg"],
            hashtags=["cafe", "coffee", "hongdae", "study"],
        )

        expected_place_info = PlaceInfo(
            name="Hongdae Study Cafe",
            category="cafe",
            address="Hongdae, Mapo-gu, Seoul",
            description="Quiet cafe perfect for studying and work",
            keywords=["cafe", "coffee", "study", "quiet", "hongdae"],
            confidence=0.87,
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.return_value = expected_place_info

            # When
            result = await self.service.analyze_content(content, content.images)

            # Then
            assert result.success is True
            assert result.place_info.category == "cafe"
            assert result.place_info.name == "Hongdae Study Cafe"
            assert result.confidence == 0.87

    # Error handling tests
    @pytest.mark.asyncio
    async def test_analyze_content_aiServiceUnavailable_returnsFailureResult(self):
        """Test error handling when AI service is unavailable."""
        # Given
        content = ContentMetadata(
            title="Test Restaurant",
            description="Test description",
            images=[],
            hashtags=[],
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.side_effect = AIAnalysisError(
                "AI service temporarily unavailable"
            )

            # When
            result = await self.service.analyze_content(content, [])

            # Then
            assert result.success is False
            assert result.place_info is None
            assert result.confidence == 0.0
            assert "AI service temporarily unavailable" in result.error
            assert result.analysis_time > 0

    @pytest.mark.asyncio
    async def test_analyze_content_rateLimitExceeded_returnsFailureResult(self):
        """Test error handling for rate limit exceeded."""
        # Given
        content = ContentMetadata(
            title="Test Content", description="Test description", images=[], hashtags=[]
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.side_effect = RateLimitError(
                "Rate limit exceeded"
            )

            # When
            result = await self.service.analyze_content(content, [])

            # Then
            assert result.success is False
            assert result.error == "Rate limit exceeded"
            assert result.place_info is None

    @pytest.mark.asyncio
    async def test_analyze_content_lowConfidenceResult_returnsLowConfidenceResult(self):
        """Test handling of low confidence AI results."""
        # Given
        content = ContentMetadata(
            title="Unclear location post",
            description="Had food somewhere... not sure where #food",
            images=[],
            hashtags=["food"],
        )

        low_confidence_place = PlaceInfo(
            name="Unknown Restaurant",
            category="restaurant",
            address="Unknown location",
            description="Restaurant with unclear details",
            keywords=["food"],
            confidence=0.25,  # Low confidence
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.return_value = low_confidence_place

            # When
            result = await self.service.analyze_content(content, [])

            # Then
            assert result.success is True  # Still successful, but low confidence
            assert result.confidence == 0.25
            assert result.place_info.confidence == 0.25

    # Content validation tests
    def test_validate_content_validContent_returnsTrue(self):
        """Test content validation with valid data."""
        # Given
        valid_content = ContentMetadata(
            title="Valid Restaurant Post",
            description="This is a valid restaurant description with enough content",
            images=["https://example.com/image1.jpg"],
            hashtags=["restaurant", "food"],
        )

        # When
        is_valid = self.service._validate_content(valid_content)

        # Then
        assert is_valid is True

    def test_validate_content_emptyContent_returnsFalse(self):
        """Test content validation with insufficient data."""
        # Given
        invalid_contents = [
            ContentMetadata(title="", description="", images=[], hashtags=[]),
            ContentMetadata(
                title="A", description="B", images=[], hashtags=[]
            ),  # Too short
            ContentMetadata(title=None, description=None, images=[], hashtags=[]),
        ]

        # When/Then
        for content in invalid_contents:
            is_valid = self.service._validate_content(content)
            assert is_valid is False

    # Performance and timeout tests
    @pytest.mark.asyncio
    async def test_analyze_content_slowAiResponse_timesOutGracefully(self):
        """Test timeout handling for slow AI responses."""
        # Given
        content = ContentMetadata(
            title="Test Content", description="Test description", images=[], hashtags=[]
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            # Simulate slow AI response
            async def slow_analyze(*args, **kwargs):
                import asyncio

                await asyncio.sleep(100)  # Very slow response
                return PlaceInfo(name="Test", category="restaurant", confidence=0.8)

            mock_analyzer.analyze_place_content = slow_analyze

            # When
            result = await self.service.analyze_content(
                content, [], timeout=1
            )  # 1 second timeout

            # Then
            assert result.success is False
            assert "timeout" in result.error.lower()

    # Image processing tests
    @pytest.mark.asyncio
    async def test_analyze_content_withImages_processesImagesCorrectly(self):
        """Test that images are processed and passed to AI analyzer."""
        # Given
        content = ContentMetadata(
            title="Restaurant with Photos",
            description="Great restaurant with food photos",
            images=["https://example.com/food1.jpg", "https://example.com/food2.jpg"],
            hashtags=["restaurant", "food"],
        )

        expected_place_info = PlaceInfo(
            name="Photo Restaurant",
            category="restaurant",
            confidence=0.95,  # Higher confidence due to images
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer, patch.object(
            self.service, "_preprocess_images"
        ) as mock_preprocess:
            mock_preprocess.return_value = [
                "processed_image1.jpg",
                "processed_image2.jpg",
            ]
            mock_analyzer.analyze_place_content.return_value = expected_place_info

            # When
            result = await self.service.analyze_content(content, content.images)

            # Then
            assert result.success is True
            assert result.confidence == 0.95

            # Verify image preprocessing was called
            mock_preprocess.assert_called_once_with(content.images)

            # Verify AI analyzer received processed images
            call_args = mock_analyzer.analyze_place_content.call_args
            assert call_args[0][1] == ["processed_image1.jpg", "processed_image2.jpg"]

    @pytest.mark.asyncio
    async def test_analyze_content_tooManyImages_limitsImageCount(self):
        """Test that excessive images are limited to reasonable count."""
        # Given
        content = ContentMetadata(
            title="Restaurant Post",
            description="Restaurant with many photos",
            images=[
                f"https://example.com/image{i}.jpg" for i in range(20)
            ],  # 20 images
            hashtags=["restaurant"],
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            mock_analyzer.analyze_place_content.return_value = PlaceInfo(
                name="Test Restaurant", category="restaurant", confidence=0.8
            )

            # When
            result = await self.service.analyze_content(content, content.images)

            # Then
            assert result.success is True

            # Verify only first 5 images were passed (service should limit)
            call_args = mock_analyzer.analyze_place_content.call_args
            passed_images = call_args[0][1]
            assert len(passed_images) <= 5

    # Confidence scoring tests
    @pytest.mark.parametrize(
        "title,description,hashtags,expected_min_confidence",
        [
            (
                "Gangnam BBQ Restaurant - 강남 갈비집",
                "Amazing Korean BBQ restaurant in Gangnam with authentic flavors. Address: 123 Gangnam-daero, Seoul. Phone: 02-1234-5678",
                ["restaurant", "bbq", "korean", "gangnam", "seoul"],
                0.85,
            ),
            ("Cafe somewhere", "Had coffee #cafe", ["cafe"], 0.3),
            ("Food was good", "Ate something tasty", ["food"], 0.2),
        ],
    )
    @pytest.mark.asyncio
    async def test_analyze_content_variousContentQuality_returnsAppropriateConfidence(
        self, title, description, hashtags, expected_min_confidence
    ):
        """Test that confidence scores reflect content quality."""
        # Given
        content = ContentMetadata(
            title=title, description=description, images=[], hashtags=hashtags
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer:
            # Mock AI to return confidence based on content quality
            confidence = max(expected_min_confidence, 0.1)
            mock_analyzer.analyze_place_content.return_value = PlaceInfo(
                name="Test Place", category="restaurant", confidence=confidence
            )

            # When
            result = await self.service.analyze_content(content, [])

            # Then
            assert result.success is True
            assert result.confidence >= expected_min_confidence

    # Caching and optimization tests
    @pytest.mark.asyncio
    async def test_analyze_content_duplicateContent_usesCachedResult(self):
        """Test caching of analysis results for duplicate content."""
        # Given
        content = ContentMetadata(
            title="Cached Restaurant",
            description="This content should be cached",
            images=[],
            hashtags=["restaurant"],
        )

        expected_place_info = PlaceInfo(
            name="Cached Restaurant", category="restaurant", confidence=0.8
        )

        with patch.object(self.service, "ai_analyzer") as mock_analyzer, patch.object(
            self.service, "_get_content_hash"
        ) as mock_hash, patch.object(self.service, "_get_cached_result") as mock_cache:
            content_hash = "content_hash_123"
            mock_hash.return_value = content_hash

            # First call: cache miss
            mock_cache.return_value = None
            mock_analyzer.analyze_place_content.return_value = expected_place_info

            # When - First analysis
            result1 = await self.service.analyze_content(content, [])

            # Then
            assert result1.success is True
            assert mock_analyzer.analyze_place_content.call_count == 1

            # Setup cache hit for second call
            mock_cache.return_value = PlaceAnalysisResult(
                success=True,
                place_info=expected_place_info,
                confidence=0.8,
                analysis_time=0.001,  # Very fast cached result
                model_version="cached",
                error=None,
            )

            # When - Second analysis (should use cache)
            result2 = await self.service.analyze_content(content, [])

            # Then
            assert result2.success is True
            assert result2.analysis_time < 0.01  # Cached result is much faster
            assert (
                mock_analyzer.analyze_place_content.call_count == 1
            )  # No additional AI calls


# Test fixtures and helper functions
@pytest.fixture
def high_quality_restaurant_content():
    """High-quality restaurant content for testing."""
    return ContentMetadata(
        title="Michelin-starred Korean Restaurant - Jungsik",
        description="Exceptional Korean fine dining experience at Jungsik in Gangnam. Chef Jun Lee creates innovative Korean cuisine with modern techniques. Address: 11 Seolleung-ro 158-gil, Gangnam-gu, Seoul. Reservations recommended. #jungsik #michelin #korean #finedining #gangnam #seoul",
        images=[
            "https://example.com/jungsik_exterior.jpg",
            "https://example.com/jungsik_dish1.jpg",
            "https://example.com/jungsik_interior.jpg",
        ],
        hashtags=["jungsik", "michelin", "korean", "finedining", "gangnam", "seoul"],
    )


@pytest.fixture
def low_quality_content():
    """Low-quality content for testing."""
    return ContentMetadata(
        title="Food", description="Ate something", images=[], hashtags=["food"]
    )


@pytest.fixture
def mock_place_analysis_service():
    """Mock PlaceAnalysisService for integration testing."""
    service = Mock(spec=PlaceAnalysisService)

    # Default successful response
    service.analyze_content.return_value = PlaceAnalysisResult(
        success=True,
        place_info=PlaceInfo(
            name="Mock Restaurant",
            category="restaurant",
            address="Mock Address",
            confidence=0.8,
        ),
        confidence=0.8,
        analysis_time=1.5,
        model_version="mock-1.0",
        error=None,
    )

    return service
