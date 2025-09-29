"""
Test utility helpers for TDD and testing infrastructure.

Provides common testing utilities, mock factories, and helper functions
to support TDD development and reduce test code duplication.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock

from app.models.place import Place, PlaceCategory, PlaceStatus
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult, ContentMetadata
from app.schemas.link_analysis import (
    AnalysisStatus,
    LinkAnalyzeRequest,
    LinkAnalyzeResponse,
)
from app.schemas.place import PlaceCreate
from app.services.place_analysis_service import PlaceAnalysisResult


class MockFactory:
    """Factory for creating mock objects with realistic test data."""

    @staticmethod
    def create_content_extract_result(
        url: str = "https://instagram.com/p/test123/",
        title: str = "Test Restaurant Post",
        description: str = "Amazing restaurant experience! #restaurant #food",
        platform: str = "instagram",
        success: bool = True,
        **kwargs,
    ) -> ContentExtractResult:
        """Create ContentExtractResult with default or custom values."""
        return ContentExtractResult(
            url=url,
            title=title,
            description=description,
            images=kwargs.get("images", ["https://example.com/image1.jpg"]),
            platform=platform,
            extraction_time=kwargs.get("extraction_time", 0.8),
            success=success,
            hashtags=kwargs.get("hashtags", ["restaurant", "food"]),
            author=kwargs.get("author", "test_user"),
            posted_at=kwargs.get("posted_at", "2024-01-15T14:30:00Z"),
        )

    @staticmethod
    def create_place_info(
        name: str = "Test Restaurant",
        category: str = "restaurant",
        confidence: float = 0.85,
        **kwargs,
    ) -> PlaceInfo:
        """Create PlaceInfo with default or custom values."""
        return PlaceInfo(
            name=name,
            category=category,
            address=kwargs.get("address", "123 Test Street, Seoul"),
            description=kwargs.get("description", "Test restaurant description"),
            phone=kwargs.get("phone", "+82-2-555-1234"),
            website=kwargs.get("website", "https://test-restaurant.com"),
            keywords=kwargs.get("keywords", ["restaurant", "food", "korean"]),
            confidence=confidence,
        )

    @staticmethod
    def create_place_analysis_result(
        success: bool = True,
        confidence: float = 0.85,
        place_info: Optional[PlaceInfo] = None,
        **kwargs,
    ) -> PlaceAnalysisResult:
        """Create PlaceAnalysisResult with default or custom values."""
        if place_info is None and success:
            place_info = MockFactory.create_place_info(confidence=confidence)

        return PlaceAnalysisResult(
            success=success,
            place_info=place_info,
            confidence=confidence,
            analysis_time=kwargs.get("analysis_time", 2.1),
            model_version=kwargs.get("model_version", "gemini-pro-1.0"),
            error=kwargs.get("error", None if success else "Analysis failed"),
        )

    @staticmethod
    def create_content_metadata(
        title: str = "Test Content",
        description: str = "Test description #test",
        **kwargs,
    ) -> ContentMetadata:
        """Create ContentMetadata with default or custom values."""
        return ContentMetadata(
            title=title,
            description=description,
            images=kwargs.get("images", ["https://example.com/image.jpg"]),
            hashtags=kwargs.get("hashtags", ["test"]),
        )

    @staticmethod
    def create_link_analyze_request(
        url: str = "https://instagram.com/p/test123/",
        force_refresh: bool = False,
        **kwargs,
    ) -> LinkAnalyzeRequest:
        """Create LinkAnalyzeRequest with default or custom values."""
        return LinkAnalyzeRequest(
            url=url, force_refresh=force_refresh, webhook_url=kwargs.get("webhook_url")
        )

    @staticmethod
    def create_link_analyze_response(
        success: bool = True,
        status: AnalysisStatus = AnalysisStatus.COMPLETED,
        **kwargs,
    ) -> LinkAnalyzeResponse:
        """Create LinkAnalyzeResponse with default or custom values."""
        result_data = None
        if success and status == AnalysisStatus.COMPLETED:
            place_info = MockFactory.create_place_info()
            result_data = {
                "place_info": place_info.dict(),
                "confidence": place_info.confidence,
                "analysis_time": 2.1,
                "content_metadata": {
                    "title": "Test Post",
                    "description": "Test description",
                    "images": ["image.jpg"],
                    "extraction_time": 0.8,
                },
            }

        return LinkAnalyzeResponse(
            success=success,
            analysis_id=kwargs.get("analysis_id", str(uuid.uuid4())),
            status=status,
            result=result_data,
            cached=kwargs.get("cached", False),
            processing_time=kwargs.get("processing_time", 1.5),
        )

    @staticmethod
    def create_place_model(
        name: str = "Test Restaurant",
        category: PlaceCategory = PlaceCategory.RESTAURANT,
        user_id: Optional[str] = None,
        place_id: Optional[str] = None,
        **kwargs,
    ) -> Mock:
        """Create a mock Place model instance."""
        mock_place = Mock(spec=Place)
        mock_place.id = uuid.UUID(place_id) if place_id else uuid.uuid4()
        mock_place.user_id = uuid.UUID(user_id) if user_id else uuid.uuid4()
        mock_place.name = name
        mock_place.category = category
        mock_place.description = kwargs.get("description", "Test place description")
        mock_place.address = kwargs.get("address", "123 Test Street, Seoul")
        mock_place.phone = kwargs.get("phone", "+82-2-555-1234")
        mock_place.website = kwargs.get("website", "https://test-place.com")
        mock_place.opening_hours = kwargs.get("opening_hours", "09:00-22:00")
        mock_place.price_range = kwargs.get("price_range", "₩₩")
        mock_place.tags = kwargs.get("tags", ["test", "restaurant"])
        mock_place.keywords = kwargs.get("keywords", ["test", "place"])
        mock_place.coordinates = kwargs.get("coordinates")
        mock_place.latitude = kwargs.get("latitude", 37.5665)
        mock_place.longitude = kwargs.get("longitude", 126.9780)
        mock_place.ai_confidence = kwargs.get("ai_confidence", 0.85)
        mock_place.ai_model_version = kwargs.get("ai_model_version", "v1.0")
        mock_place.recommendation_score = kwargs.get("recommendation_score", 8)
        mock_place.source_url = kwargs.get("source_url")
        mock_place.source_platform = kwargs.get("source_platform")
        mock_place.source_content_hash = kwargs.get("source_content_hash")
        mock_place.status = kwargs.get("status", PlaceStatus.ACTIVE)
        mock_place.is_verified = kwargs.get("is_verified", False)
        mock_place.created_at = kwargs.get("created_at", datetime.utcnow())
        mock_place.updated_at = kwargs.get("updated_at", datetime.utcnow())
        return mock_place

    @staticmethod
    def create_place_create(
        name: str = "Test Restaurant",
        category: PlaceCategory = PlaceCategory.RESTAURANT,
        **kwargs,
    ) -> PlaceCreate:
        """Create PlaceCreate schema instance."""
        return PlaceCreate(
            name=name,
            description=kwargs.get("description", "Test place description"),
            address=kwargs.get("address", "123 Test Street, Seoul"),
            phone=kwargs.get("phone", "+82-2-555-1234"),
            website=kwargs.get("website", "https://test-place.com"),
            opening_hours=kwargs.get("opening_hours", "09:00-22:00"),
            price_range=kwargs.get("price_range", "₩₩"),
            category=category,
            tags=kwargs.get("tags", ["test", "restaurant"]),
            keywords=kwargs.get("keywords", ["test", "place"]),
            latitude=kwargs.get("latitude", 37.5665),
            longitude=kwargs.get("longitude", 126.9780),
            source_url=kwargs.get("source_url"),
            source_platform=kwargs.get("source_platform"),
            ai_confidence=kwargs.get("ai_confidence", 0.85),
            ai_model_version=kwargs.get("ai_model_version", "v1.0"),
            recommendation_score=kwargs.get("recommendation_score", 8),
        )

    @staticmethod
    def create_duplicate_result(
        is_duplicate: bool = False,
        confidence: float = 0.0,
        match_type: str = "no_match",
        matched_place_index: int = -1,
    ):
        """Create DuplicateResult mock."""
        from app.services.duplicate_detector import DuplicateResult

        return DuplicateResult(
            is_duplicate=is_duplicate,
            confidence=confidence,
            match_type=match_type,
            matched_place_index=matched_place_index,
        )

    @staticmethod
    def create_classification_result(
        predicted_category,
        confidence: float = 0.85,
        classification_time: float = 0.05,
        needs_manual_review: bool = False,
    ):
        """Create ClassificationResult mock."""
        from app.services.place_classifier import ClassificationResult

        return ClassificationResult(
            predicted_category=predicted_category,
            confidence=confidence,
            classification_time=classification_time,
            needs_manual_review=needs_manual_review,
        )


class TestDataBuilder:
    """Builder class for creating complex test data scenarios."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset builder to default state."""
        self._data = {}
        return self

    def with_high_quality_content(self):
        """Configure builder for high-quality content scenario."""
        self._data.update(
            {
                "title": "Michelin-starred Korean Restaurant - Exceptional Dining Experience",
                "description": "Extraordinary fine dining experience at this Michelin-starred Korean restaurant in Gangnam. Chef's innovative approach to traditional Korean cuisine with modern presentation. Each course was expertly crafted with premium ingredients. The tasting menu showcased the best of Korean flavors with contemporary techniques. Service was impeccable and the atmosphere elegant. Perfect for special occasions. Located in the heart of Gangnam district. Reservations essential. #michelin #korean #finedining #gangnam #chef #tasting #premium",
                "confidence": 0.95,
                "keywords": [
                    "michelin",
                    "korean",
                    "finedining",
                    "premium",
                    "chef",
                    "gangnam",
                ],
                "category": "restaurant",
                "images": [
                    "https://example.com/michelin_dish1.jpg",
                    "https://example.com/michelin_dish2.jpg",
                    "https://example.com/michelin_interior.jpg",
                ],
            }
        )
        return self

    def with_low_quality_content(self):
        """Configure builder for low-quality content scenario."""
        self._data.update(
            {
                "title": "Food",
                "description": "Ate something #food",
                "confidence": 0.25,
                "keywords": ["food"],
                "category": "restaurant",
                "images": [],
            }
        )
        return self

    def with_cafe_content(self):
        """Configure builder for cafe content scenario."""
        self._data.update(
            {
                "title": "Perfect Study Spot - Cozy Cafe in Hongdae",
                "description": "Found the perfect study cafe in Hongdae! Great coffee, comfortable seating, and reliable WiFi. The atmosphere is quiet and conducive to productivity. They have excellent pastries and the baristas are skilled. Popular with students and remote workers. Open late which is perfect for night study sessions. #cafe #coffee #study #hongdae #wifi #students",
                "confidence": 0.88,
                "keywords": ["cafe", "coffee", "study", "hongdae", "wifi"],
                "category": "cafe",
                "name": "Hongdae Study Cafe",
            }
        )
        return self

    def with_korean_bbq_content(self):
        """Configure builder for Korean BBQ content scenario."""
        self._data.update(
            {
                "title": "Best Korean BBQ in Gangnam! 🥩",
                "description": "Amazing Korean BBQ experience at this hidden gem in Gangnam! The meat quality was outstanding - perfectly marbled wagyu that melted in your mouth. The banchan selection was incredible with over 15 different side dishes. The service was attentive and they grilled the meat perfectly for us. The atmosphere was traditional yet modern. Perfect for date nights or group dining. Located just 5 minutes from Gangnam Station. Highly recommended! #korean #bbq #gangnam #wagyu #banchan #datenight",
                "confidence": 0.92,
                "keywords": [
                    "korean",
                    "bbq",
                    "wagyu",
                    "gangnam",
                    "traditional",
                    "datenight",
                ],
                "category": "restaurant",
                "name": "Gangnam Premium Korean BBQ",
            }
        )
        return self

    def with_error_scenario(self, error_type: str = "content_extraction"):
        """Configure builder for error scenario."""
        error_messages = {
            "content_extraction": "Post is private or deleted",
            "ai_analysis": "AI service temporarily unavailable",
            "rate_limit": "Rate limit exceeded",
            "network": "Network timeout occurred",
        }

        self._data.update(
            {
                "success": False,
                "error": error_messages.get(error_type, "Unknown error"),
                "confidence": 0.0,
            }
        )
        return self

    def build_content_result(self) -> ContentExtractResult:
        """Build ContentExtractResult with configured data."""
        return MockFactory.create_content_extract_result(**self._data)

    def build_place_info(self) -> PlaceInfo:
        """Build PlaceInfo with configured data."""
        return MockFactory.create_place_info(**self._data)

    def build_analysis_result(self) -> PlaceAnalysisResult:
        """Build PlaceAnalysisResult with configured data."""
        return MockFactory.create_place_analysis_result(**self._data)

    def build_place_create(self) -> PlaceCreate:
        """Build PlaceCreate schema with configured data."""
        return MockFactory.create_place_create(**self._data)

    def build_place_model(self) -> Mock:
        """Build Place model mock with configured data."""
        return MockFactory.create_place_model(**self._data)


class AsyncTestHelpers:
    """Helpers for async testing scenarios."""

    @staticmethod
    async def run_with_timeout(coro, timeout: float = 5.0):
        """Run coroutine with timeout for testing."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise AssertionError(f"Operation timed out after {timeout} seconds")

    @staticmethod
    async def simulate_slow_operation(result: Any, delay: float = 0.1):
        """Simulate slow async operation for testing."""
        await asyncio.sleep(delay)
        return result

    @staticmethod
    def create_async_mock(
        return_value: Any = None, side_effect: Any = None
    ) -> AsyncMock:
        """Create AsyncMock with specified return value or side effect."""
        mock = AsyncMock()
        if return_value is not None:
            mock.return_value = return_value
        if side_effect is not None:
            mock.side_effect = side_effect
        return mock


class MockServiceFactory:
    """Factory for creating mock services with realistic behavior."""

    @staticmethod
    def create_content_extractor_mock(
        success: bool = True,
        extraction_time: float = 0.8,
        content_data: Optional[Dict] = None,
    ) -> Mock:
        """Create mock ContentExtractor with configurable behavior."""
        mock = Mock()

        if success:
            if content_data is None:
                content_data = {
                    "title": "Mock Restaurant Post",
                    "description": "Mock restaurant description #restaurant",
                    "images": ["mock_image.jpg"],
                    "author": "mock_user",
                    "posted_at": "2024-01-15T14:30:00Z",
                    "hashtags": ["restaurant"],
                }

            mock_result = MockFactory.create_content_extract_result(
                extraction_time=extraction_time, **content_data
            )
            mock.extract_content = AsyncTestHelpers.create_async_mock(
                return_value=mock_result
            )
        else:
            mock.extract_content = AsyncTestHelpers.create_async_mock(
                side_effect=Exception("Content extraction failed")
            )

        return mock

    @staticmethod
    def create_analysis_service_mock(
        success: bool = True, confidence: float = 0.85, analysis_time: float = 2.1
    ) -> Mock:
        """Create mock PlaceAnalysisService with configurable behavior."""
        mock = Mock()

        if success:
            mock_result = MockFactory.create_place_analysis_result(
                success=success, confidence=confidence, analysis_time=analysis_time
            )
            mock.analyze_content = AsyncTestHelpers.create_async_mock(
                return_value=mock_result
            )
        else:
            mock_result = MockFactory.create_place_analysis_result(
                success=False, confidence=0.0, place_info=None
            )
            mock.analyze_content = AsyncTestHelpers.create_async_mock(
                return_value=mock_result
            )

        return mock

    @staticmethod
    def create_cache_manager_mock(
        cache_hit: bool = False, cached_data: Optional[Dict] = None
    ) -> Mock:
        """Create mock CacheManager with configurable behavior."""
        mock = Mock()

        # Setup cache behavior
        if cache_hit and cached_data:
            mock.get = AsyncTestHelpers.create_async_mock(return_value=cached_data)
        else:
            mock.get = AsyncTestHelpers.create_async_mock(return_value=None)

        mock.set = AsyncTestHelpers.create_async_mock(return_value=True)
        mock.initialize = AsyncTestHelpers.create_async_mock()
        mock.close = AsyncTestHelpers.create_async_mock()
        mock.invalidate = AsyncTestHelpers.create_async_mock()

        return mock


class PerformanceTestHelpers:
    """Helpers for performance testing scenarios."""

    @staticmethod
    async def measure_execution_time(coro):
        """Measure execution time of async operation."""
        import time

        start_time = time.time()
        result = await coro
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    async def run_concurrent_operations(operations: List, max_workers: int = 10):
        """Run multiple operations concurrently and return results."""
        import asyncio

        semaphore = asyncio.Semaphore(max_workers)

        async def run_with_semaphore(operation):
            async with semaphore:
                return await operation

        return await asyncio.gather(*[run_with_semaphore(op) for op in operations])

    @staticmethod
    def assert_performance_metrics(
        execution_time: float, max_time: float, operation_name: str = "Operation"
    ):
        """Assert performance metrics meet requirements."""
        assert (
            execution_time <= max_time
        ), f"{operation_name} took {execution_time:.3f}s, expected <= {max_time}s"

    @staticmethod
    def create_load_test_data(count: int = 100) -> List[Dict]:
        """Create test data for load testing."""
        return [
            {
                "url": f"https://instagram.com/p/load_test_{i}/",
                "title": f"Load Test Post {i}",
                "description": f"Load testing content {i} #test #load",
                "expected_confidence": 0.8 + (i % 20) / 100,  # Vary confidence
            }
            for i in range(count)
        ]


class ValidationHelpers:
    """Helpers for data validation in tests."""

    @staticmethod
    def assert_valid_place_info(place_info: PlaceInfo, min_confidence: float = 0.7):
        """Assert PlaceInfo contains valid data."""
        assert place_info.name is not None and len(place_info.name) > 0
        assert place_info.category in [
            "restaurant",
            "cafe",
            "bar",
            "attraction",
            "hotel",
        ]
        assert place_info.confidence >= min_confidence
        assert place_info.confidence <= 1.0
        assert isinstance(place_info.keywords, list)
        assert len(place_info.keywords) > 0

    @staticmethod
    def assert_valid_content_result(content: ContentExtractResult):
        """Assert ContentExtractResult contains valid data."""
        assert content.url is not None
        assert content.title is not None
        assert content.platform in ["instagram", "naver_blog", "youtube"]
        assert content.extraction_time > 0
        assert isinstance(content.images, list)
        assert isinstance(content.hashtags, list)

    @staticmethod
    def assert_valid_analysis_result(result: PlaceAnalysisResult):
        """Assert PlaceAnalysisResult contains valid data."""
        assert isinstance(result.success, bool)
        assert result.analysis_time > 0
        assert result.model_version is not None

        if result.success:
            assert result.place_info is not None
            ValidationHelpers.assert_valid_place_info(result.place_info)
            assert result.confidence > 0
        else:
            assert result.error is not None
            assert result.confidence == 0.0

    @staticmethod
    def assert_api_response_structure(response_data: Dict, expected_fields: List[str]):
        """Assert API response has expected structure."""
        for field in expected_fields:
            assert field in response_data, f"Missing required field: {field}"

    @staticmethod
    def assert_datetime_format(datetime_str: str):
        """Assert datetime string is in correct ISO format."""
        try:
            datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
        except ValueError:
            raise AssertionError(f"Invalid datetime format: {datetime_str}")


# Test data constants
TEST_URLS = {
    "instagram": [
        "https://instagram.com/p/CXXXXXXXXXx/",
        "https://www.instagram.com/p/test123/",
        "https://instagram.com/p/restaurant_post/",
    ],
    "naver_blog": [
        "https://blog.naver.com/foodlover/123456789",
        "https://blog.naver.com/user/987654321",
    ],
    "youtube": ["https://youtube.com/watch?v=dQw4w9WgXcQ", "https://youtu.be/test123"],
    "unsupported": [
        "https://facebook.com/post/123",
        "https://twitter.com/user/status/456",
        "https://example.com/page",
    ],
}

SAMPLE_PLACES = {
    "korean_restaurant": {
        "name": "Gangnam Korean BBQ House",
        "category": "restaurant",
        "address": "123 Gangnam-daero, Seoul",
        "keywords": ["korean", "bbq", "gangnam"],
        "confidence": 0.92,
    },
    "cafe": {
        "name": "Hongdae Study Cafe",
        "category": "cafe",
        "address": "456 Hongik-ro, Seoul",
        "keywords": ["cafe", "coffee", "study"],
        "confidence": 0.88,
    },
    "fine_dining": {
        "name": "Jungsik",
        "category": "restaurant",
        "address": "11 Seolleung-ro 158-gil, Seoul",
        "keywords": ["michelin", "korean", "finedining"],
        "confidence": 0.98,
    },
}

# Export commonly used test utilities
__all__ = [
    "MockFactory",
    "TestDataBuilder",
    "AsyncTestHelpers",
    "MockServiceFactory",
    "PerformanceTestHelpers",
    "ValidationHelpers",
    "TEST_URLS",
    "SAMPLE_PLACES",
]
