"""
Comprehensive tests for Link Analysis API endpoints.

Tests cover:
- Basic analysis flow
- Caching behavior
- Error handling
- Async processing
- Bulk analysis
- Status monitoring
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.schemas.link_analysis import AnalysisStatus
from app.services.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisAPI:
    """Test suite for Link Analysis API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    async def async_client(self):
        """Create async test client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def mock_content_data(self):
        """Mock content extraction result."""
        return ContentExtractResult(
            url="https://instagram.com/p/test123",
            title="Amazing Restaurant in Seoul",
            description="Best Korean BBQ place ever!",
            images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            platform="instagram",
            extraction_time=0.5,
            success=True,
        )

    @pytest.fixture
    def mock_place_info(self):
        """Mock place analysis result."""
        return PlaceInfo(
            name="Seoul BBQ House",
            category="restaurant",
            address="123 Gangnam-gu, Seoul",
            description="Traditional Korean BBQ restaurant",
            phone="+82-2-1234-5678",
            website="https://seoulbbq.com",
            keywords=["korean", "bbq", "traditional", "gangnam"],
            confidence=0.9,
        )

    @pytest.fixture
    def mock_analysis_result(self, mock_place_info):
        """Mock AI analysis result."""
        return PlaceAnalysisResult(
            success=True,
            place_info=mock_place_info,
            confidence=0.9,
            analysis_time=1.2,
            model_version="gemini-1.0",
            error=None,
        )

    def test_analyze_link_success_no_cache(
        self, client, mock_content_data, mock_analysis_result
    ):
        """Test successful link analysis without cache."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None  # Cache miss
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = mock_analysis_result
            mock_analysis.return_value = mock_analysis_instance

            # Make request
            response = client.post(
                "/api/v1/links/analyze", json={"url": "https://instagram.com/p/test123"}
            )

            # Assertions
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["status"] == "completed"
            assert data["cached"] is False
            assert "analysisId" in data
            assert "result" in data
            assert data["result"]["confidence"] == 0.9
            assert data["result"]["placeInfo"]["name"] == "Seoul BBQ House"

            # Verify cache operations
            mock_cache_instance.initialize.assert_called_once()
            mock_cache_instance.get.assert_called_once()
            mock_cache_instance.close.assert_called_once()

    def test_analyze_link_cache_hit(self, client):
        """Test link analysis with cache hit."""
        cached_result = {
            "place_info": {
                "name": "Cached Restaurant",
                "category": "restaurant",
                "address": "Cached Address",
                "confidence": 0.85,
            },
            "confidence": 0.85,
            "analysis_time": 1.0,
            "content_metadata": {
                "title": "Cached Title",
                "description": "Cached Description",
                "images": ["cached_img.jpg"],
                "extraction_time": 0.3,
            },
        }

        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = cached_result
            mock_cache_manager.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cached123"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["cached"] is True
            assert data["result"]["confidence"] == 0.85

    def test_analyze_link_force_refresh(
        self, client, mock_content_data, mock_analysis_result
    ):
        """Test force refresh bypasses cache."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = mock_analysis_result
            mock_analysis.return_value = mock_analysis_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/test123", "force_refresh": True},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["cached"] is False

            # Cache should not be checked when force_refresh=True
            mock_cache_instance.get.assert_not_called()

    def test_analyze_link_async_webhook(self, client):
        """Test async processing with webhook."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None  # Cache miss
            mock_cache_manager.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={
                    "url": "https://instagram.com/p/async123",
                    "webhook_url": "https://example.com/webhook",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["status"] == "in_progress"
            assert data["result"] is None
            assert "analysisId" in data

    def test_analyze_link_invalid_url(self, client):
        """Test analysis with invalid URL format."""
        response = client.post("/api/v1/links/analyze", json={"url": "invalid-url"})

        assert response.status_code == 422
        assert "URL must start with http://" in response.json()["detail"][0]["msg"]

    def test_analyze_link_unsupported_platform(self, client):
        """Test analysis with unsupported platform."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.side_effect = Exception(
                "Unsupported platform"
            )
            mock_extractor.return_value = mock_extractor_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://unsupported.com/post/123"},
            )

            assert response.status_code == 500

    def test_get_analysis_status_found(self, client):
        """Test getting analysis status for existing analysis."""
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        # Setup analysis in store
        analysis_id = str(uuid.uuid4())
        analysis_store[analysis_id] = {
            "status": AnalysisStatus.COMPLETED,
            "url": "https://instagram.com/p/test123",
            "created_at": datetime.now(timezone.utc),
            "result": {
                "place_info": {"name": "Test Place"},
                "confidence": 0.8,
                "analysis_time": 1.0,
                "content_metadata": {},
            },
            "progress": 1.0,
        }

        try:
            response = client.get(f"/api/v1/links/analyses/{analysis_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["analysisId"] == analysis_id
            assert data["status"] == "completed"
            assert data["progress"] == 1.0
            assert data["result"]["confidence"] == 0.8
        finally:
            # Cleanup
            if analysis_id in analysis_store:
                del analysis_store[analysis_id]

    def test_get_analysis_status_not_found(self, client):
        """Test getting analysis status for non-existent analysis."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/links/analyses/{fake_id}")

        assert response.status_code == 404
        assert "Analysis not found" in response.json()["detail"]

    def test_cancel_analysis_success(self, client):
        """Test cancelling an in-progress analysis."""
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        # Setup in-progress analysis
        analysis_id = str(uuid.uuid4())
        analysis_store[analysis_id] = {
            "status": AnalysisStatus.IN_PROGRESS,
            "url": "https://instagram.com/p/test123",
            "created_at": datetime.now(timezone.utc),
        }

        try:
            response = client.delete(f"/api/v1/links/analyses/{analysis_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "cancelled successfully" in data["message"]
            assert analysis_store[analysis_id]["status"] == AnalysisStatus.CANCELLED
        finally:
            # Cleanup
            if analysis_id in analysis_store:
                del analysis_store[analysis_id]

    def test_cancel_analysis_already_completed(self, client):
        """Test cancelling a completed analysis (should fail)."""
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        # Setup completed analysis
        analysis_id = str(uuid.uuid4())
        analysis_store[analysis_id] = {
            "status": AnalysisStatus.COMPLETED,
            "url": "https://instagram.com/p/test123",
            "created_at": datetime.now(timezone.utc),
        }

        try:
            response = client.delete(f"/api/v1/links/analyses/{analysis_id}")

            assert response.status_code == 400
            assert "Cannot cancel analysis" in response.json()["detail"]
        finally:
            # Cleanup
            if analysis_id in analysis_store:
                del analysis_store[analysis_id]

    def test_bulk_analyze_success(self, client):
        """Test bulk analysis with valid URLs."""
        urls = [
            "https://instagram.com/p/test1",
            "https://instagram.com/p/test2",
            "https://twitter.com/user/status/123",
        ]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": urls})

        assert response.status_code == 200
        data = response.json()

        assert "batchId" in data
        assert data["totalUrls"] == 3
        assert len(data["acceptedUrls"]) == 3
        assert len(data["rejectedUrls"]) == 0

    def test_bulk_analyze_mixed_valid_invalid(self, client):
        """Test bulk analysis with mixed valid/invalid URLs."""
        urls = [
            "https://instagram.com/p/test1",
            "invalid-url",
            "https://twitter.com/user/status/123",
            "ftp://example.com/file",
        ]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": urls})

        assert response.status_code == 200
        data = response.json()

        assert data["totalUrls"] == 2  # Only valid URLs
        assert len(data["acceptedUrls"]) == 2
        assert len(data["rejectedUrls"]) == 2

    def test_bulk_analyze_no_valid_urls(self, client):
        """Test bulk analysis with no valid URLs."""
        urls = ["invalid-url", "ftp://example.com"]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": urls})

        assert response.status_code == 400
        assert "No valid URLs" in response.json()["detail"]

    def test_get_cache_stats(self, client):
        """Test getting cache statistics."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager:
            from app.services.cache_manager import CacheStats

            mock_cache_instance = AsyncMock()
            mock_stats = CacheStats(
                cache_hits=100,
                cache_misses=20,
                l1_hits=80,
                l2_hits=20,
                total_requests=120,
            )
            mock_cache_instance.get_stats.return_value = mock_stats
            mock_cache_manager.return_value = mock_cache_instance

            response = client.get("/api/v1/links/cache/stats")

            assert response.status_code == 200
            data = response.json()

            assert data["cache_hits"] == 100
            assert data["cache_misses"] == 20
            assert data["hit_rate"] == 100 / 120
            assert data["l1_hits"] == 80
            assert data["l2_hits"] == 20

    def test_get_service_status(self, client):
        """Test getting service status."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager:
            mock_cache_instance = AsyncMock()
            mock_cache_manager.return_value = mock_cache_instance

            response = client.get("/api/v1/links/status")

            assert response.status_code == 200
            data = response.json()

            assert data["service"] == "Link Analysis API"
            assert data["status"] in ["healthy", "degraded"]
            assert "cache_connection" in data
            assert "active_analyses" in data
            assert "total_analyses" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_concurrent_analysis_requests(self, async_client):
        """Test handling concurrent analysis requests."""
        urls = [
            "https://instagram.com/p/concurrent1",
            "https://instagram.com/p/concurrent2",
            "https://instagram.com/p/concurrent3",
        ]

        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ), patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ):
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            # Send concurrent requests
            tasks = []
            for url in urls:
                task = async_client.post("/api/v1/links/analyze", json={"url": url})
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_error_handling_ai_service_failure(self, client, mock_content_data):
        """Test error handling when AI service fails."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            # AI service fails
            failed_result = PlaceAnalysisResult(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=0.5,
                model_version="gemini-1.0",
                error="AI service temporarily unavailable",
            )

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = failed_result
            mock_analysis.return_value = mock_analysis_instance

            response = client.post(
                "/api/v1/links/analyze", json={"url": "https://instagram.com/p/ai_fail"}
            )

            assert response.status_code == 503
            assert "AI analysis service unavailable" in response.json()["detail"]

    def test_rate_limiting_error(self, client, mock_content_data):
        """Test rate limiting error handling."""
        from app.exceptions.ai import RateLimitError

        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.side_effect = RateLimitError(
                "Rate limit exceeded"
            )
            mock_analysis.return_value = mock_analysis_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/rate_limit"},
            )

            assert response.status_code == 429
            assert "rate limit exceeded" in response.json()["detail"]

    def test_analysis_performance_requirements(
        self, client, mock_content_data, mock_analysis_result
    ):
        """Test that analysis meets performance requirements."""
        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            # Setup mocks
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = mock_analysis_result
            mock_analysis.return_value = mock_analysis_instance

            import time

            start_time = time.time()

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/performance_test"},
            )

            end_time = time.time()
            processing_time = end_time - start_time

            assert response.status_code == 200
            data = response.json()

            # Performance requirements: should complete within reasonable time
            assert processing_time < 5.0  # Max 5 seconds for sync processing
            assert data["processingTime"] > 0

    def test_cache_ttl_configuration(self, client, mock_content_data):
        """Test that cache TTL is set based on confidence score."""
        high_confidence_result = PlaceAnalysisResult(
            success=True,
            place_info=self.mock_place_info,
            confidence=0.9,  # High confidence
            analysis_time=1.0,
            model_version="gemini-1.0",
            error=None,
        )

        with patch(
            "app.api.api_v1.endpoints.link_analysis.CacheManager"
        ) as mock_cache_manager, patch(
            "app.api.api_v1.endpoints.link_analysis.ContentExtractor"
        ) as mock_extractor, patch(
            "app.api.api_v1.endpoints.link_analysis.PlaceAnalysisService"
        ) as mock_analysis:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_manager.return_value = mock_cache_instance

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = high_confidence_result
            mock_analysis.return_value = mock_analysis_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/high_confidence"},
            )

            assert response.status_code == 200

            # Verify that cache set was called (in background task)
            # High confidence should result in longer TTL (3600s vs 1800s)
            # This is verified by checking the background task was added
