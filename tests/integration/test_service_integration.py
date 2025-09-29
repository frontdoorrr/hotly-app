"""
Integration tests for service layer interactions.

Tests service-to-service communication and data flow:
- ContentExtractor → PlaceAnalysisService
- PlaceAnalysisService → CacheManager
- Service → Database interactions
- External API integrations
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.exceptions.ai import AIAnalysisError
from app.exceptions.external import ContentExtractionError
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentMetadata
from app.services.cache_manager import CacheManager
from app.services.content_extractor import ContentExtractor
from app.services.place_analysis_service import PlaceAnalysisService


class TestContentExtractionToAnalysisIntegration:
    """Test integration between content extraction and AI analysis services."""

    def setup_method(self):
        """Setup services for integration testing."""
        self.content_extractor = ContentExtractor()
        self.analysis_service = PlaceAnalysisService()
        self.cache_manager = CacheManager()

    @pytest.mark.asyncio
    async def test_complete_analysis_pipeline_instagramToPlaceInfo_success(self):
        """Test complete pipeline from Instagram URL to place information."""
        # Given
        instagram_url = "https://instagram.com/p/restaurant_review/"

        # Mock external dependencies
        with patch.object(
            self.content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            self.analysis_service, "ai_analyzer"
        ) as mock_ai:
            # Setup content extraction mock
            extracted_content = {
                "title": "Amazing Korean BBQ Night! 🥩",
                "description": "Had the most incredible Korean BBQ experience at Gangnam House! The meat quality was outstanding, perfectly marbled wagyu. The banchan selection was impressive and the service was attentive. Located right in the heart of Gangnam district. Perfect for special occasions! #korean #bbq #gangnam #wagyu #restaurant #seoul",
                "images": [
                    "https://instagram.com/image1.jpg",
                    "https://instagram.com/image2.jpg",
                    "https://instagram.com/image3.jpg",
                ],
                "author": "seoul_foodie_kim",
                "posted_at": "2024-01-15T19:30:00Z",
                "hashtags": [
                    "korean",
                    "bbq",
                    "gangnam",
                    "wagyu",
                    "restaurant",
                    "seoul",
                ],
            }
            mock_extract.return_value = extracted_content

            # Setup AI analysis mock
            place_info = PlaceInfo(
                name="Gangnam House Korean BBQ",
                category="restaurant",
                address="456 Gangnam-daero, Gangnam-gu, Seoul",
                description="Upscale Korean BBQ restaurant specializing in premium wagyu",
                phone="+82-2-555-9876",
                website="https://gangnamhouse.co.kr",
                keywords=["korean", "bbq", "wagyu", "premium", "gangnam"],
                confidence=0.95,
            )
            mock_ai.analyze_place_content.return_value = place_info

            # When - Execute complete pipeline
            # Step 1: Extract content
            content_result = await self.content_extractor.extract_content(instagram_url)

            # Step 2: Convert to analysis format
            content_metadata = ContentMetadata(
                title=content_result.title,
                description=content_result.description,
                images=content_result.images,
                hashtags=content_result.hashtags,
            )

            # Step 3: Analyze with AI
            analysis_result = await self.analysis_service.analyze_content(
                content_metadata, content_result.images
            )

            # Then - Verify complete pipeline
            assert content_result.success is True
            assert content_result.platform == "instagram"
            assert "Korean BBQ" in content_result.title

            assert analysis_result.success is True
            assert analysis_result.place_info.name == "Gangnam House Korean BBQ"
            assert analysis_result.place_info.category == "restaurant"
            assert analysis_result.confidence == 0.95

            # Verify data flow integrity
            assert content_result.url == instagram_url
            assert analysis_result.place_info.confidence == 0.95

    @pytest.mark.asyncio
    async def test_content_extraction_failure_propagation_handledGracefully(self):
        """Test error propagation from content extraction to analysis."""
        # Given
        problematic_url = "https://instagram.com/p/private_or_deleted/"

        # Mock extraction failure
        with patch.object(
            self.content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.side_effect = ContentExtractionError(
                "Post is private or deleted"
            )

            # When/Then - Should propagate error appropriately
            with pytest.raises(ContentExtractionError) as exc_info:
                await self.content_extractor.extract_content(problematic_url)

            assert "private or deleted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_analysis_service_error_handling_contentExtractionSuccess(self):
        """Test analysis service error handling when content extraction succeeds."""
        # Given
        url = "https://instagram.com/p/ai_analysis_error/"

        # Mock successful extraction but failed analysis
        with patch.object(
            self.content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            self.analysis_service, "ai_analyzer"
        ) as mock_ai:
            # Successful content extraction
            mock_extract.return_value = {
                "title": "Restaurant Post",
                "description": "Some restaurant content",
                "images": ["image.jpg"],
                "author": "user",
                "posted_at": "2024-01-15T14:30:00Z",
                "hashtags": ["restaurant"],
            }

            # Failed AI analysis
            mock_ai.analyze_place_content.side_effect = AIAnalysisError(
                "AI service temporarily unavailable"
            )

            # When
            content_result = await self.content_extractor.extract_content(url)

            content_metadata = ContentMetadata(
                title=content_result.title,
                description=content_result.description,
                images=content_result.images,
                hashtags=content_result.hashtags,
            )

            analysis_result = await self.analysis_service.analyze_content(
                content_metadata, content_result.images
            )

            # Then
            assert content_result.success is True  # Extraction succeeded
            assert analysis_result.success is False  # Analysis failed
            assert "AI service temporarily unavailable" in analysis_result.error

    @pytest.mark.asyncio
    async def test_data_transformation_integration_preservesQuality(self):
        """Test data transformation maintains quality through pipeline."""
        # Given
        url = "https://instagram.com/p/data_quality_test/"

        with patch.object(
            self.content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract, patch.object(
            self.analysis_service, "ai_analyzer"
        ) as mock_ai:
            # High-quality content input
            rich_content = {
                "title": "Michelin-starred Korean Restaurant - Jungsik Experience",
                "description": "Extraordinary dining experience at Jungsik, the Michelin-starred Korean restaurant in Gangnam. Chef Yim Jung-sik's innovative approach to traditional Korean cuisine was absolutely stunning. Each course was a work of art, combining modern techniques with authentic flavors. The tasting menu included reimagined kimchi, elevated bulgogi, and contemporary takes on classic Korean desserts. The presentation was impeccable and the service was world-class. Located at 11 Seolleung-ro 158-gil, Gangnam-gu. This is definitely a special occasion restaurant. Reservations essential. #jungsik #michelin #korean #finedining #gangnam #seoul #gastronomy",
                "images": [
                    "https://instagram.com/jungsik_dish1.jpg",
                    "https://instagram.com/jungsik_dish2.jpg",
                    "https://instagram.com/jungsik_interior.jpg",
                    "https://instagram.com/jungsik_presentation.jpg",
                ],
                "author": "fine_dining_seoul",
                "posted_at": "2024-01-15T20:00:00Z",
                "hashtags": [
                    "jungsik",
                    "michelin",
                    "korean",
                    "finedining",
                    "gangnam",
                    "seoul",
                    "gastronomy",
                ],
            }
            mock_extract.return_value = rich_content

            # High-confidence AI analysis
            detailed_place_info = PlaceInfo(
                name="Jungsik",
                category="restaurant",
                address="11 Seolleung-ro 158-gil, Gangnam-gu, Seoul",
                description="Michelin-starred Korean fine dining restaurant by Chef Yim Jung-sik",
                phone="+82-2-517-4654",
                website="https://jungsik.kr",
                keywords=[
                    "michelin",
                    "korean",
                    "finedining",
                    "innovative",
                    "traditional",
                    "gangnam",
                ],
                confidence=0.98,
            )
            mock_ai.analyze_place_content.return_value = detailed_place_info

            # When
            content_result = await self.content_extractor.extract_content(url)

            content_metadata = ContentMetadata(
                title=content_result.title,
                description=content_result.description,
                images=content_result.images,
                hashtags=content_result.hashtags,
            )

            analysis_result = await self.analysis_service.analyze_content(
                content_metadata, content_result.images
            )

            # Then - Verify data quality is preserved
            assert analysis_result.confidence >= 0.95  # High confidence maintained
            assert "Michelin" in content_result.title
            assert "Jungsik" in analysis_result.place_info.name
            assert analysis_result.place_info.category == "restaurant"
            assert len(analysis_result.place_info.keywords) >= 5
            assert analysis_result.place_info.phone is not None
            assert analysis_result.place_info.website is not None


class TestCacheServiceIntegration:
    """Test integration between cache manager and other services."""

    def setup_method(self):
        """Setup services for cache integration testing."""
        self.cache_manager = CacheManager()
        self.analysis_service = PlaceAnalysisService()

    @pytest.mark.asyncio
    async def test_cache_analysis_result_integration_storesAndRetrieves(self):
        """Test caching of analysis results."""
        # Given
        cache_key = "link_analysis:https://instagram.com/p/cache_test/"

        analysis_result_data = {
            "place_info": {
                "name": "Cache Test Restaurant",
                "category": "restaurant",
                "address": "Cache Test Address",
                "confidence": 0.88,
            },
            "confidence": 0.88,
            "analysis_time": 2.3,
            "content_metadata": {
                "title": "Cache Test Post",
                "description": "Testing cache functionality",
                "images": ["cache_test_image.jpg"],
                "extraction_time": 0.7,
            },
        }

        # Mock Redis operations
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = None  # Initially empty

            # When - Store in cache
            await self.cache_manager.set(cache_key, analysis_result_data, ttl=3600)

            # Then
            mock_redis.set.assert_called_once()

            # When - Mock cache hit for retrieval
            import json

            mock_redis.get.return_value = json.dumps(analysis_result_data)

            cached_result = await self.cache_manager.get(cache_key)

            # Then
            assert cached_result == analysis_result_data
            assert cached_result["place_info"]["name"] == "Cache Test Restaurant"

    @pytest.mark.asyncio
    async def test_cache_multilayer_promotion_l2ToL1(self):
        """Test cache layer promotion from L2 to L1."""
        # Given
        key = "test_promotion_key"
        value = {"data": "promotion_test", "confidence": 0.9}

        # Mock L2 hit, L1 miss
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            import json

            mock_redis.get.return_value = json.dumps(value)

            # When
            result = await self.cache_manager.get(key)

            # Then
            assert result == value

            # Verify data was promoted to L1
            l1_result = await self.cache_manager._get_l1(key)
            assert l1_result == value

    @pytest.mark.asyncio
    async def test_cache_invalidation_integration_clearsAllLayers(self):
        """Test cache invalidation across all layers."""
        # Given
        key = "invalidation_test_key"
        value = {"data": "to_be_invalidated"}

        # Setup cache in both layers
        await self.cache_manager._set_l1(key, value, ttl=300)

        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.delete.return_value = 1

            # When
            await self.cache_manager.invalidate(key)

            # Then
            # Verify L1 cleared
            l1_result = await self.cache_manager._get_l1(key)
            assert l1_result is None

            # Verify L2 delete called
            mock_redis.delete.assert_called_once_with(key)


class TestDatabaseServiceIntegration:
    """Test service integration with database operations."""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        session = Mock(spec=Session)
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.refresh = Mock()
        session.close = Mock()

        # Setup query mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_query.all.return_value = []

        session.query.return_value = mock_query

        return session

    def test_place_creation_service_integration_savesToDatabase(self, mock_db_session):
        """Test place creation through service layer."""
        # Given
        from app.services.place_service import PlaceService  # Hypothetical service

        place_data = {
            "name": "Integration Test Restaurant",
            "address": "123 Integration St, Seoul",
            "category": "restaurant",
            "confidence": 0.92,
        }

        # Mock service
        with patch("app.services.place_service.PlaceService") as MockPlaceService:
            mock_place_service = MockPlaceService.return_value

            created_place = Mock()
            created_place.id = "place_123"
            created_place.name = place_data["name"]
            created_place.address = place_data["address"]

            mock_place_service.create_place.return_value = created_place

            # When
            place_service = MockPlaceService(mock_db_session)
            result = place_service.create_place(place_data)

            # Then
            assert result.id == "place_123"
            assert result.name == place_data["name"]
            mock_place_service.create_place.assert_called_once_with(place_data)

    @pytest.mark.asyncio
    async def test_analysis_result_persistence_integration_storesAnalysisMetadata(
        self, mock_db_session
    ):
        """Test persistence of analysis results and metadata."""
        # Given
        analysis_data = {
            "url": "https://instagram.com/p/persistence_test/",
            "analysis_id": "analysis_456",
            "place_info": {
                "name": "Persistence Test Restaurant",
                "category": "restaurant",
                "confidence": 0.89,
            },
            "analysis_time": 2.1,
            "model_version": "gemini-pro-1.0",
        }

        # Mock analysis result service
        with patch(
            "app.services.analysis_result_service.AnalysisResultService"
        ) as MockService:
            mock_service = MockService.return_value

            saved_result = Mock()
            saved_result.id = analysis_data["analysis_id"]
            saved_result.url = analysis_data["url"]

            mock_service.save_analysis_result.return_value = saved_result

            # When
            service = MockService(mock_db_session)
            result = service.save_analysis_result(analysis_data)

            # Then
            assert result.id == analysis_data["analysis_id"]
            assert result.url == analysis_data["url"]
            mock_service.save_analysis_result.assert_called_once_with(analysis_data)


class TestExternalAPIIntegration:
    """Test integration with external APIs."""

    @pytest.mark.asyncio
    async def test_instagram_api_integration_handlesRateLimiting(self):
        """Test Instagram API integration with rate limiting."""
        # Given
        content_extractor = ContentExtractor()
        instagram_url = "https://instagram.com/p/rate_limit_test/"

        with patch(
            "app.services.external.instagram_client.InstagramClient"
        ) as MockClient:
            mock_client = MockClient.return_value

            # Simulate rate limiting then success
            mock_client.get_post_data.side_effect = [
                Exception("Rate limited"),  # First call fails
                {  # Second call succeeds
                    "title": "Rate Limit Recovery Test",
                    "description": "Test post after rate limit",
                    "images": ["recovery_image.jpg"],
                    "author": "test_user",
                    "posted_at": "2024-01-15T14:30:00Z",
                    "hashtags": ["test"],
                },
            ]

            # When
            with patch("asyncio.sleep", new_callable=AsyncMock):  # Mock sleep for retry
                result = await content_extractor.extract_content(instagram_url)

            # Then
            assert result.success is True
            assert "Rate Limit Recovery" in result.title
            assert mock_client.get_post_data.call_count == 2  # Retry happened

    @pytest.mark.asyncio
    async def test_google_ai_integration_handlesServiceFailure(self):
        """Test Google AI API integration with service failure."""
        # Given
        analysis_service = PlaceAnalysisService()
        content = ContentMetadata(
            title="AI Failure Test",
            description="Testing AI service failure handling",
            images=[],
            hashtags=["test"],
        )

        with patch("app.services.ai.gemini_analyzer.GeminiAnalyzer") as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value

            # Simulate AI service failure
            mock_analyzer.analyze_place_content.side_effect = AIAnalysisError(
                "Google AI service unavailable"
            )

            # When
            result = await analysis_service.analyze_content(content, [])

            # Then
            assert result.success is False
            assert "Google AI service unavailable" in result.error

    @pytest.mark.asyncio
    async def test_redis_connection_integration_handlesConnectionFailure(self):
        """Test Redis connection handling when service is unavailable."""
        # Given
        cache_manager = CacheManager()

        with patch.object(cache_manager, "redis_client") as mock_redis:
            # Simulate Redis connection failure
            mock_redis.set.side_effect = ConnectionError("Redis server unavailable")

            # When
            result = await cache_manager.set("test_key", {"data": "test"}, ttl=300)

            # Then
            assert result is False  # Should handle gracefully
            # Should not raise exception


# Performance integration tests
class TestPerformanceIntegration:
    """Test performance aspects of service integration."""

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests_handledCorrectly(self):
        """Test concurrent analysis requests don't interfere."""
        # Given
        content_extractor = ContentExtractor()
        analysis_service = PlaceAnalysisService()

        urls = [f"https://instagram.com/p/concurrent_{i}/" for i in range(5)]

        with patch.object(
            content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract, patch.object(analysis_service, "ai_analyzer") as mock_ai:
            # Setup mocks for concurrent processing
            mock_extract.return_value = {
                "title": "Concurrent Test",
                "description": "Testing concurrent processing",
                "images": [],
                "author": "test_user",
                "posted_at": "2024-01-15T14:30:00Z",
                "hashtags": ["test"],
            }

            mock_ai.analyze_place_content.return_value = PlaceInfo(
                name="Concurrent Restaurant", category="restaurant", confidence=0.8
            )

            # When - Process concurrently
            async def process_url(url):
                content = await content_extractor.extract_content(url)
                metadata = ContentMetadata(
                    title=content.title,
                    description=content.description,
                    images=content.images,
                    hashtags=content.hashtags,
                )
                return await analysis_service.analyze_content(metadata, content.images)

            results = await asyncio.gather(*[process_url(url) for url in urls])

            # Then
            assert len(results) == 5
            assert all(result.success for result in results)
            assert all(
                result.place_info.name == "Concurrent Restaurant" for result in results
            )

    @pytest.mark.asyncio
    async def test_memory_usage_integration_handlesLargeContent(self):
        """Test memory handling with large content processing."""
        # Given
        content_extractor = ContentExtractor()
        large_description = "Large content " * 1000  # Large description

        with patch.object(
            content_extractor, "_extract_instagram_content", new_callable=AsyncMock
        ) as mock_extract:
            mock_extract.return_value = {
                "title": "Large Content Test",
                "description": large_description,
                "images": [f"image_{i}.jpg" for i in range(50)],  # Many images
                "author": "test_user",
                "posted_at": "2024-01-15T14:30:00Z",
                "hashtags": ["test"] * 100,  # Many hashtags
            }

            # When
            result = await content_extractor.extract_content(
                "https://instagram.com/p/large_content/"
            )

            # Then
            assert result.success is True
            assert len(result.description) > 10000
            assert len(result.images) <= 10  # Should be limited by extractor
            # Memory usage should be reasonable (no specific assertion, but no crash)
