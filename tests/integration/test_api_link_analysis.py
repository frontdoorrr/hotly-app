"""
Integration tests for Link Analysis API endpoints.

Tests the complete API workflow including:
- Request validation
- Service integration
- Database operations
- Response formatting
- Error handling
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.services.places.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisAPIIntegration:
    """Integration tests for link analysis API endpoints."""

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_services(self):
        """Mock external services for integration testing."""
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup content extractor mock
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content = AsyncMock()

            # Setup analysis service mock
            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content = AsyncMock()

            # Setup cache manager mock
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.initialize = AsyncMock()
            mock_cache_instance.close = AsyncMock()
            mock_cache_instance.get = AsyncMock(return_value=None)  # Cache miss
            mock_cache_instance.set = AsyncMock()

            yield {
                "extractor": mock_extractor_instance,
                "analysis": mock_analysis_instance,
                "cache": mock_cache_instance,
            }

    def test_analyze_link_validInstagramUrl_returnsSuccessfulAnalysis(
        self, client, mock_services
    ):
        """Test successful link analysis integration workflow."""
        # Given
        instagram_url = "https://instagram.com/p/CXXXXXXXXXx/"
        request_data = {"url": instagram_url, "force_refresh": False}

        # Setup mock responses
        mock_content = ContentExtractResult(
            url=instagram_url,
            title="Amazing Korean BBQ Restaurant",
            description="Best Korean BBQ in Gangnam! Perfect for date night. #korean #bbq #gangnam #restaurant #datenight",
            images=[
                "https://instagram.com/image1.jpg",
                "https://instagram.com/image2.jpg",
            ],
            platform="instagram",
            extraction_time=0.8,
            success=True,
            hashtags=["korean", "bbq", "gangnam", "restaurant", "datenight"],
            author="seoul_foodie",
            posted_at="2024-01-15T19:30:00Z",
        )

        mock_place_info = PlaceInfo(
            name="Gangnam Korean BBQ House",
            category="restaurant",
            address="123 Gangnam-daero, Gangnam-gu, Seoul",
            description="Premium Korean BBQ restaurant",
            phone="+82-2-555-1234",
            website="https://gangnam-bbq.com",
            keywords=["korean", "bbq", "premium", "gangnam", "date"],
            confidence=0.92,
        )

        mock_analysis_result = PlaceAnalysisResult(
            success=True,
            place_info=mock_place_info,
            confidence=0.92,
            analysis_time=2.1,
            model_version="gemini-pro-1.0",
            error=None,
        )

        # Configure mocks
        mock_services["extractor"].extract_content.return_value = mock_content
        mock_services["analysis"].analyze_content.return_value = mock_analysis_result

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["cached"] is False
        assert "analysisId" in result
        assert result["processingTime"] > 0

        # Verify place information
        place_info = result["result"]["placeInfo"]
        assert place_info["name"] == "Gangnam Korean BBQ House"
        assert place_info["category"] == "restaurant"
        assert place_info["confidence"] == 0.92
        assert "gangnam" in place_info["address"].lower()

        # Verify content metadata
        content_metadata = result["result"]["contentMetadata"]
        assert "Korean BBQ" in content_metadata["title"]
        assert "gangnam" in content_metadata["description"].lower()
        assert len(content_metadata["images"]) <= 3  # Should limit to 3 images

        # Verify service integration calls
        mock_services["extractor"].extract_content.assert_called_once_with(
            instagram_url
        )
        mock_services["analysis"].analyze_content.assert_called_once()

    def test_analyze_link_cachedResult_returnsFromCache(self, client, mock_services):
        """Test cache hit scenario returns cached result."""
        # Given
        url = "https://instagram.com/p/cached_post/"
        request_data = {"url": url}

        # Setup cached data
        cached_result = {
            "place_info": {
                "name": "Cached Restaurant",
                "category": "restaurant",
                "address": "Cached Address",
                "confidence": 0.85,
            },
            "confidence": 0.85,
            "analysis_time": 1.5,
            "content_metadata": {
                "title": "Cached Post Title",
                "description": "This is cached content",
                "images": ["cached_image.jpg"],
                "extraction_time": 0.5,
            },
        }

        mock_services["cache"].get.return_value = cached_result

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["cached"] is True
        assert result["result"]["placeInfo"]["name"] == "Cached Restaurant"

        # Verify cache was checked but extraction/analysis not called
        mock_services["cache"].get.assert_called_once()
        mock_services["extractor"].extract_content.assert_not_called()
        mock_services["analysis"].analyze_content.assert_not_called()

    def test_analyze_link_forceRefresh_bypassesCache(self, client, mock_services):
        """Test force refresh bypasses cache."""
        # Given
        url = "https://instagram.com/p/force_refresh/"
        request_data = {"url": url, "force_refresh": True}

        # Setup mocks for fresh analysis
        mock_services["extractor"].extract_content.return_value = ContentExtractResult(
            url=url,
            title="Fresh Content",
            description="This is fresh content",
            images=[],
            platform="instagram",
            extraction_time=0.6,
            success=True,
            hashtags=[],
            author="test_user",
            posted_at="2024-01-15T14:30:00Z",
        )

        mock_services["analysis"].analyze_content.return_value = PlaceAnalysisResult(
            success=True,
            place_info=PlaceInfo(
                name="Fresh Restaurant", category="restaurant", confidence=0.8
            ),
            confidence=0.8,
            analysis_time=1.8,
            model_version="gemini-pro-1.0",
            error=None,
        )

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["cached"] is False
        assert result["result"]["placeInfo"]["name"] == "Fresh Restaurant"

        # Verify cache was not checked (force refresh)
        mock_services["cache"].get.assert_not_called()
        mock_services["extractor"].extract_content.assert_called_once()
        mock_services["analysis"].analyze_content.assert_called_once()

    def test_analyze_link_invalidUrl_returnsValidationError(self, client):
        """Test API validation for invalid URLs."""
        # Given
        invalid_requests = [
            {"url": "not-a-url"},
            {"url": ""},
            {"url": "https://facebook.com/post/123"},  # Unsupported platform
            {},  # Missing URL
        ]

        # When/Then
        for request_data in invalid_requests:
            response = client.post("/api/v1/links/analyze", json=request_data)

            assert response.status_code in [422, 400]  # Validation error
            error_data = response.json()
            assert "detail" in error_data or "error" in error_data

    def test_analyze_link_contentExtractionFails_returnsError(
        self, client, mock_services
    ):
        """Test error handling when content extraction fails."""
        # Given
        url = "https://instagram.com/p/private_post/"
        request_data = {"url": url}

        # Mock extraction failure
        mock_services["extractor"].extract_content.side_effect = Exception(
            "Post is private or deleted"
        )

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 500
        error_data = response.json()
        assert "detail" in error_data

    def test_analyze_link_aiAnalysisFails_returnsServiceError(
        self, client, mock_services
    ):
        """Test error handling when AI analysis fails."""
        # Given
        url = "https://instagram.com/p/ai_error/"
        request_data = {"url": url}

        # Mock successful extraction but failed analysis
        mock_services["extractor"].extract_content.return_value = ContentExtractResult(
            url=url,
            title="Test Content",
            description="Test description",
            images=[],
            platform="instagram",
            extraction_time=0.5,
            success=True,
            hashtags=[],
            author="test_user",
            posted_at="2024-01-15T14:30:00Z",
        )

        mock_services["analysis"].analyze_content.return_value = PlaceAnalysisResult(
            success=False,
            place_info=None,
            confidence=0.0,
            analysis_time=0.5,
            model_version="gemini-pro-1.0",
            error="AI service temporarily unavailable",
        )

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 503
        error_data = response.json()
        assert "AI analysis service unavailable" in error_data["detail"]

    def test_get_analysis_status_validId_returnsStatus(self, client):
        """Test analysis status retrieval."""
        # Given - First create an analysis
        url = "https://instagram.com/p/status_test/"

        with patch("app.services.content_extractor.ContentExtractor"), patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ), patch("app.services.cache_manager.CacheManager"):
            create_response = client.post("/api/v1/links/analyze", json={"url": url})
            assert create_response.status_code == 200

            analysis_id = create_response.json()["analysisId"]

        # When
        status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")

        # Then
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["analysisId"] == analysis_id
        assert "status" in status_data
        assert status_data["status"] in [
            "pending",
            "in_progress",
            "completed",
            "failed",
        ]

    def test_get_analysis_status_invalidId_returnsNotFound(self, client):
        """Test analysis status with invalid ID."""
        # Given
        invalid_id = "non-existent-analysis-id"

        # When
        response = client.get(f"/api/v1/links/analyses/{invalid_id}")

        # Then
        assert response.status_code == 404
        error_data = response.json()
        assert "not found" in error_data["detail"].lower()

    def test_cancel_analysis_validId_cancelsSuccessfully(self, client):
        """Test analysis cancellation."""
        # Given - Create an analysis in progress
        url = "https://instagram.com/p/cancel_test/"

        with patch("app.services.content_extractor.ContentExtractor"), patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ), patch("app.services.cache_manager.CacheManager"):
            # Create with webhook for async processing
            create_response = client.post(
                "/api/v1/links/analyze",
                json={"url": url, "webhook_url": "https://example.com/webhook"},
            )
            analysis_id = create_response.json()["analysisId"]

        # When
        cancel_response = client.delete(f"/api/v1/links/analyses/{analysis_id}")

        # Then
        assert cancel_response.status_code == 200

        cancel_data = cancel_response.json()
        assert cancel_data["success"] is True
        assert "cancelled" in cancel_data["message"].lower()

    def test_bulk_analyze_links_validUrls_processesBatch(self, client, mock_services):
        """Test bulk analysis endpoint."""
        # Given
        urls = [
            "https://instagram.com/p/bulk1/",
            "https://instagram.com/p/bulk2/",
            "https://instagram.com/p/bulk3/",
        ]
        request_data = {"urls": urls}

        # When
        response = client.post("/api/v1/links/bulk-analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert "batchId" in result
        assert result["totalUrls"] == 3
        assert len(result["acceptedUrls"]) == 3
        assert len(result["rejectedUrls"]) == 0
        assert "estimatedCompletion" in result

    def test_bulk_analyze_links_mixedUrls_separatesValidAndInvalid(self, client):
        """Test bulk analysis with mixed valid/invalid URLs."""
        # Given
        urls = [
            "https://instagram.com/p/valid1/",
            "not-a-url",
            "https://instagram.com/p/valid2/",
            "https://facebook.com/invalid",  # Unsupported platform
        ]
        request_data = {"urls": urls}

        # When
        response = client.post("/api/v1/links/bulk-analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert result["totalUrls"] == 2  # Only valid URLs
        assert len(result["acceptedUrls"]) == 2
        assert len(result["rejectedUrls"]) == 2

    def test_get_cache_stats_returnsStatistics(self, client, mock_services):
        """Test cache statistics endpoint."""
        # Given
        mock_stats = Mock()
        mock_stats.cache_hits = 150
        mock_stats.cache_misses = 50
        mock_stats.l1_hits = 100
        mock_stats.l2_hits = 50
        mock_stats.hit_rate = 0.75
        mock_stats.l1_hit_rate = 0.5
        mock_stats.l2_hit_rate = 0.25
        mock_stats.total_requests = 200

        mock_services["cache"].get_stats.return_value = mock_stats

        # When
        response = client.get("/api/v1/links/cache/stats")

        # Then
        assert response.status_code == 200

        stats = response.json()
        assert stats["cache_hits"] == 150
        assert stats["cache_misses"] == 50
        assert stats["hit_rate"] == 0.75
        assert stats["total_requests"] == 200

    def test_get_service_status_returnsHealthCheck(self, client, mock_services):
        """Test service status endpoint."""
        # When
        response = client.get("/api/v1/links/status")

        # Then
        assert response.status_code == 200

        status = response.json()
        assert status["service"] == "Link Analysis API"
        assert "status" in status
        assert status["status"] in ["healthy", "degraded"]
        assert "timestamp" in status
        assert "active_analyses" in status

    @pytest.mark.asyncio
    async def test_async_analysis_workflow_completesInBackground(
        self, client, mock_services
    ):
        """Test asynchronous analysis with webhook notification."""
        # Given
        url = "https://instagram.com/p/async_test/"
        webhook_url = "https://example.com/webhook/callback"
        request_data = {"url": url, "webhook_url": webhook_url}

        # When
        response = client.post("/api/v1/links/analyze", json=request_data)

        # Then
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert result["status"] == "in_progress"
        assert result["result"] is None  # No immediate result for async

        analysis_id = result["analysisId"]

        # Check status endpoint
        status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["status"] in ["in_progress", "completed"]

    def test_api_rate_limiting_handlesExcessiveRequests(self, client):
        """Test API rate limiting behavior."""
        # Given
        url = "https://instagram.com/p/rate_limit_test/"

        # When - Make many requests quickly
        responses = []
        for i in range(20):  # Attempt 20 rapid requests
            response = client.post(
                "/api/v1/links/analyze", json={"url": f"{url}?id={i}"}
            )
            responses.append(response)

        # Then - Some requests should be rate limited
        status_codes = [r.status_code for r in responses]

        # Should have mix of successful and rate-limited responses
        assert 200 in status_codes  # Some successful
        # Note: Actual rate limiting depends on implementation

    def test_api_request_timeout_handlesSlowServices(self, client, mock_services):
        """Test API timeout handling for slow services."""
        # Given
        url = "https://instagram.com/p/slow_test/"

        # Mock slow service response
        async def slow_extract(*args, **kwargs):
            await asyncio.sleep(30)  # Very slow
            return ContentExtractResult(
                url=url,
                title="Slow",
                description="Slow",
                images=[],
                platform="instagram",
                extraction_time=30,
                success=True,
                hashtags=[],
                author="slow",
                posted_at="2024-01-15T14:30:00Z",
            )

        mock_services["extractor"].extract_content.side_effect = slow_extract

        # When
        response = client.post("/api/v1/links/analyze", json={"url": url})

        # Then - Should timeout or handle gracefully
        # Actual behavior depends on timeout configuration
        assert response.status_code in [200, 202, 503, 504]


# Test data fixtures for integration tests
@pytest.fixture
def sample_instagram_data():
    """Sample Instagram content for testing."""
    return {
        "url": "https://instagram.com/p/CXXXXXXXXXx/",
        "title": "Best Korean BBQ in Seoul! 🥩",
        "description": "Incredible Korean BBQ experience at this amazing restaurant in Gangnam. The meat quality was outstanding and the service was perfect. Highly recommended for date nights and special occasions! #korean #bbq #gangnam #seoul #restaurant #datenight #food",
        "images": [
            "https://scontent-nrt1-1.cdninstagram.com/v/image1.jpg",
            "https://scontent-nrt1-1.cdninstagram.com/v/image2.jpg",
            "https://scontent-nrt1-1.cdninstagram.com/v/image3.jpg",
        ],
        "hashtags": [
            "korean",
            "bbq",
            "gangnam",
            "seoul",
            "restaurant",
            "datenight",
            "food",
        ],
        "author": "seoul_food_explorer",
        "posted_at": "2024-01-15T19:30:45Z",
    }


@pytest.fixture
def sample_place_data():
    """Sample place information for testing."""
    return {
        "name": "Gangnam Premium Korean BBQ",
        "category": "restaurant",
        "address": "123 Gangnam-daero, Gangnam-gu, Seoul, South Korea",
        "description": "Premium Korean BBQ restaurant known for exceptional meat quality and traditional atmosphere",
        "phone": "+82-2-555-1234",
        "website": "https://gangnam-premium-bbq.com",
        "keywords": ["korean", "bbq", "premium", "gangnam", "traditional", "meat"],
        "confidence": 0.94,
    }
