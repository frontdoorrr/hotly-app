"""
End-to-End tests for Link Analysis workflow.

Tests the complete flow from URL input to final result storage.
"""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.services.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisE2E:
    """End-to-End test suite for link analysis workflow."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def sample_instagram_content(self):
        """Sample Instagram content extraction result."""
        return ContentExtractResult(
            url="https://instagram.com/p/CXXXXXXXXXx/",
            title="맛집 탐방 🍽️",
            description="강남 맛집 발견! 정말 맛있었어요 #강남맛집 #데이트코스 #추천",
            images=[
                "https://scontent-nrt1-1.cdninstagram.com/image1.jpg",
                "https://scontent-nrt1-1.cdninstagram.com/image2.jpg",
            ],
            platform="instagram",
            extraction_time=0.8,
            success=True,
            hashtags=["강남맛집", "데이트코스", "추천"],
            author="food_lover_123",
            posted_at="2024-01-15T14:30:00Z",
        )

    @pytest.fixture
    def sample_place_info(self):
        """Sample place information."""
        return PlaceInfo(
            name="강남 한우정",
            category="restaurant",
            address="서울시 강남구 테헤란로 123",
            description="프리미엄 한우 전문점",
            phone="02-1234-5678",
            website="https://gangnam-hanwoo.com",
            keywords=["한우", "고기", "강남", "데이트", "고급"],
            confidence=0.92,
        )

    @pytest.fixture
    def sample_analysis_result(self, sample_place_info):
        """Sample AI analysis result."""
        return PlaceAnalysisResult(
            success=True,
            place_info=sample_place_info,
            confidence=0.92,
            analysis_time=2.1,
            model_version="gemini-pro-1.0",
            error=None,
        )

    def test_complete_analysis_flow_instagram(
        self, client, sample_instagram_content, sample_analysis_result
    ):
        """Test complete analysis flow for Instagram post."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = (
                sample_instagram_content
            )

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = sample_analysis_result

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None  # Cache miss
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Execute analysis
            start_time = time.time()
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/CXXXXXXXXXx/"},
            )
            end_time = time.time()

            # Verify response
            assert response.status_code == 200
            data = response.json()

            # Basic response structure
            assert data["success"] is True
            assert data["status"] == "completed"
            assert data["cached"] is False
            assert "analysisId" in data

            # Processing time should be reasonable
            processing_time = end_time - start_time
            assert processing_time < 10.0  # Should complete within 10 seconds
            assert data["processingTime"] > 0

            # Result content verification
            result = data["result"]
            assert result["confidence"] == 0.92

            place_info = result["placeInfo"]
            assert place_info["name"] == "강남 한우정"
            assert place_info["category"] == "restaurant"
            assert place_info["address"] == "서울시 강남구 테헤란로 123"
            assert len(place_info["keywords"]) == 5

            content_metadata = result["contentMetadata"]
            assert content_metadata["title"] == "맛집 탐방 🍽️"
            assert "강남 맛집 발견" in content_metadata["description"]
            assert len(content_metadata["images"]) <= 3  # Should limit to 3 images

            # Verify service calls
            mock_extractor_instance.extract_content.assert_called_once_with(
                "https://instagram.com/p/CXXXXXXXXXx/"
            )
            mock_analysis_instance.analyze_content.assert_called_once()

    def test_cached_result_retrieval_flow(self, client):
        """Test retrieval of cached analysis results."""

        cached_data = {
            "place_info": {
                "name": "Cached Restaurant",
                "category": "restaurant",
                "address": "Cached Address",
                "description": "Cached Description",
                "keywords": ["cached", "test"],
                "confidence": 0.85,
            },
            "confidence": 0.85,
            "analysis_time": 1.5,
            "content_metadata": {
                "title": "Cached Post",
                "description": "This is from cache",
                "images": ["cached_image.jpg"],
                "extraction_time": 0.5,
            },
        }

        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = cached_data
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            start_time = time.time()
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cached_post/"},
            )
            end_time = time.time()

            # Cache hit should be very fast
            processing_time = end_time - start_time
            assert processing_time < 1.0

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["cached"] is True
            assert data["result"]["confidence"] == 0.85
            assert data["result"]["placeInfo"]["name"] == "Cached Restaurant"

    def test_error_recovery_flow(self, client, sample_instagram_content):
        """Test error handling and recovery in analysis flow."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup content extraction success but AI analysis failure
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = (
                sample_instagram_content
            )

            failed_analysis = PlaceAnalysisResult(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=0.5,
                model_version="gemini-pro-1.0",
                error="Temporary AI service unavailable",
            )

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = failed_analysis

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/error_test/"},
            )

            # Should return proper error response
            assert response.status_code == 503
            assert "AI analysis service unavailable" in response.json()["detail"]

    def test_async_webhook_flow(self, client):
        """Test asynchronous analysis with webhook notification."""

        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Request async analysis with webhook
            response = client.post(
                "/api/v1/links/analyze",
                json={
                    "url": "https://instagram.com/p/async_test/",
                    "webhook_url": "https://example.com/webhook/callback",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Should return immediately with in_progress status
            assert data["success"] is True
            assert data["status"] == "in_progress"
            assert data["result"] is None
            analysis_id = data["analysisId"]

            # Check status endpoint
            status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["analysisId"] == analysis_id
            assert status_data["status"] in ["in_progress", "completed"]

    def test_bulk_analysis_flow(self, client):
        """Test bulk analysis workflow."""

        urls = [
            "https://instagram.com/p/bulk1/",
            "https://instagram.com/p/bulk2/",
            "https://twitter.com/user/status/123456",
        ]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": urls})

        assert response.status_code == 200
        data = response.json()

        assert "batchId" in data
        assert data["totalUrls"] == 3
        assert len(data["acceptedUrls"]) == 3
        assert len(data["rejectedUrls"]) == 0
        assert "estimatedCompletion" in data

        batch_id = data["batchId"]

        # Check batch status (would be in progress in real scenario)
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        assert batch_id in analysis_store
        batch_data = analysis_store[batch_id]
        assert batch_data["type"] == "batch"
        assert batch_data["total_urls"] == 3

    def test_performance_requirements_e2e(
        self, client, sample_instagram_content, sample_analysis_result
    ):
        """Test that E2E flow meets performance requirements."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup fast mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = (
                sample_instagram_content
            )

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = sample_analysis_result

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Test multiple sequential requests
            response_times = []

            for i in range(5):
                start_time = time.time()
                response = client.post(
                    "/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/perf_test_{i}/"},
                )
                end_time = time.time()

                assert response.status_code == 200
                response_times.append(end_time - start_time)

            # Performance requirements
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)

            # All requests should complete within 10 seconds
            assert max_response_time < 10.0
            # Average should be much faster
            assert avg_response_time < 5.0

            print(f"Average response time: {avg_response_time:.2f}s")
            print(f"Max response time: {max_response_time:.2f}s")

    def test_concurrent_requests_e2e(self, client):
        """Test handling concurrent analysis requests."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = (
                self.sample_instagram_content()
            )

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = (
                self.sample_analysis_result()
            )

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Simulate concurrent requests
            import concurrent.futures

            def make_request(i):
                return client.post(
                    "/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/concurrent_{i}/"},
                )

            start_time = time.time()

            # Use ThreadPoolExecutor to simulate concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request, i) for i in range(10)]
                responses = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            end_time = time.time()
            total_time = end_time - start_time

            # All requests should succeed
            assert len(responses) == 10
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

            # Concurrent processing should be faster than sequential
            assert total_time < 20.0  # Should handle 10 requests in under 20 seconds

            print(f"Concurrent processing time for 10 requests: {total_time:.2f}s")

    def test_cache_efficiency_e2e(self, client):
        """Test cache efficiency in real scenario."""

        cached_data = {
            "place_info": {
                "name": "Efficient Cache Test",
                "category": "restaurant",
                "address": "Cache Street 123",
                "confidence": 0.9,
            },
            "confidence": 0.9,
            "analysis_time": 1.0,
            "content_metadata": {
                "title": "Cache Test",
                "description": "Testing cache efficiency",
                "images": ["cache_img.jpg"],
                "extraction_time": 0.3,
            },
        }

        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # First request: cache miss
            mock_cache_instance.get.return_value = None

            with patch("app.services.content_extractor.ContentExtractor"), patch(
                "app.services.place_analysis_service.PlaceAnalysisService"
            ):
                response1 = client.post(
                    "/api/v1/links/analyze",
                    json={"url": "https://instagram.com/p/cache_test/"},
                )

                assert response1.status_code == 200
                assert response1.json()["cached"] is False

            # Second request: cache hit
            mock_cache_instance.get.return_value = cached_data

            start_time = time.time()
            response2 = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cache_test/"},
            )
            end_time = time.time()

            cache_response_time = end_time - start_time

            assert response2.status_code == 200
            data = response2.json()
            assert data["cached"] is True
            assert data["result"]["placeInfo"]["name"] == "Efficient Cache Test"

            # Cache hit should be very fast (sub-second)
            assert cache_response_time < 1.0

            print(f"Cache hit response time: {cache_response_time:.3f}s")

    def test_data_quality_validation_e2e(self, client, sample_instagram_content):
        """Test data quality validation throughout the E2E flow."""

        # Create analysis result with varying quality
        high_quality_result = PlaceAnalysisResult(
            success=True,
            place_info=PlaceInfo(
                name="High Quality Restaurant",
                category="restaurant",
                address="Complete Address, Seoul, South Korea",
                description="Detailed description with context",
                phone="+82-2-1234-5678",
                website="https://restaurant.com",
                keywords=["korean", "traditional", "fine-dining", "seoul"],
                confidence=0.95,
            ),
            confidence=0.95,
            analysis_time=1.8,
            model_version="gemini-pro-1.0",
            error=None,
        )

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = (
                sample_instagram_content
            )

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = high_quality_result

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/quality_test/"},
            )

            assert response.status_code == 200
            data = response.json()

            # Validate data quality
            result = data["result"]
            place_info = result["placeInfo"]

            # High confidence should be preserved
            assert result["confidence"] >= 0.9

            # Complete place information
            assert place_info["name"] is not None
            assert place_info["category"] in ["restaurant", "cafe", "bar", "attraction"]
            assert place_info["address"] is not None
            assert len(place_info["keywords"]) > 0

            # Data consistency
            assert place_info["confidence"] == result["confidence"]

            # Performance metrics
            assert result["analysisTime"] > 0
            content_meta = result["contentMetadata"]
            assert content_meta["extractionTime"] > 0
