"""
Comprehensive test suite for SNS Link Analysis system.

This module tests the complete link analysis workflow with all components
integrated, including edge cases, error scenarios, and performance requirements.
"""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.schemas.link_analysis import AnalysisStatus
from app.services.places.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisComprehensive:
    """Comprehensive test suite for the complete link analysis system."""

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
    def instagram_sample_data(self):
        """Instagram sample content and analysis."""
        content = ContentExtractResult(
            url="https://instagram.com/p/CxxxxxxxxxxxX/",
            title="🍕 Pizza Night in Hongdae! 🎉",
            description="Finally found the best pizza place in Seoul! The margherita was incredible 😍 #hongdae #pizza #seoul #foodie #bestpizza #nightout",
            images=[
                "https://scontent-nrt1-1.cdninstagram.com/pizza1.jpg",
                "https://scontent-nrt1-1.cdninstagram.com/pizza2.jpg",
                "https://scontent-nrt1-1.cdninstagram.com/interior.jpg",
            ],
            platform="instagram",
            extraction_time=0.8,
            success=True,
            hashtags=["hongdae", "pizza", "seoul", "foodie", "bestpizza", "nightout"],
            author="food_explorer_seoul",
            posted_at="2024-01-20T19:30:00Z",
        )

        place_info = PlaceInfo(
            name="Hongdae Pizza House",
            category="restaurant",
            address="서울시 마포구 홍익로 123, 홍대입구역 2번 출구",
            description="홍대 최고의 수제 피자 전문점. 신선한 재료와 전통 이탈리안 방식으로 만든 피자가 유명",
            phone="02-332-5678",
            website="https://hongdaepizza.com",
            keywords=["피자", "홍대", "이탈리안", "데이트", "야식", "맥주"],
            confidence=0.94,
        )

        analysis_result = PlaceAnalysisResult(
            success=True,
            place_info=place_info,
            confidence=0.94,
            analysis_time=2.3,
            model_version="gemini-pro-1.0",
            error=None,
        )

        return content, analysis_result

    @pytest.fixture
    def twitter_sample_data(self):
        """Twitter sample content and analysis."""
        content = ContentExtractResult(
            url="https://twitter.com/user/status/1234567890",
            title="Amazing coffee shop discovery ☕",
            description="Found this hidden gem in Gangnam! Best latte art I've ever seen ✨ #gangnam #coffee #latte #hiddengen #seoul",
            images=["https://pbs.twimg.com/media/coffee1.jpg"],
            platform="twitter",
            extraction_time=0.6,
            success=True,
            hashtags=["gangnam", "coffee", "latte", "hiddengem", "seoul"],
            author="coffee_lover_kr",
            posted_at="2024-01-21T10:15:00Z",
        )

        place_info = PlaceInfo(
            name="Hidden Bean Cafe",
            category="cafe",
            address="서울시 강남구 테헤란로 456, 강남역 3번 출구",
            description="강남 숨은 카페 맛집. 전문 바리스타의 라떼아트와 직접 로스팅한 원두가 특징",
            phone="02-567-1234",
            website="https://hiddenbean.co.kr",
            keywords=["카페", "강남", "라떼아트", "원두", "브런치", "디저트"],
            confidence=0.88,
        )

        analysis_result = PlaceAnalysisResult(
            success=True,
            place_info=place_info,
            confidence=0.88,
            analysis_time=1.9,
            model_version="gemini-pro-1.0",
            error=None,
        )

        return content, analysis_result

    def test_complete_workflow_instagram(self, client, instagram_sample_data):
        """Test complete workflow with Instagram content."""
        content_data, analysis_result = instagram_sample_data

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = analysis_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None  # Cache miss
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Execute analysis
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/CxxxxxxxxxxxX/"},
            )

            # Verify response structure
            assert response.status_code == 200
            data = response.json()

            # Basic validation
            assert data["success"] is True
            assert data["status"] == "completed"
            assert data["cached"] is False
            assert "analysisId" in data
            assert data["processingTime"] > 0

            # Result validation
            result = data["result"]
            assert result["confidence"] == 0.94

            # Place info validation
            place = result["placeInfo"]
            assert place["name"] == "Hongdae Pizza House"
            assert place["category"] == "restaurant"
            assert place["address"] == "서울시 마포구 홍익로 123, 홍대입구역 2번 출구"
            assert place["confidence"] == 0.94
            assert len(place["keywords"]) == 6
            assert "피자" in place["keywords"]
            assert "홍대" in place["keywords"]

            # Content metadata validation
            content_meta = result["contentMetadata"]
            assert content_meta["title"] == "🍕 Pizza Night in Hongdae! 🎉"
            assert "best pizza place" in content_meta["description"]
            assert len(content_meta["images"]) <= 3  # Should limit images
            assert content_meta["extractionTime"] == 0.8

            # Verify service calls
            mock_extractor_instance.extract_content.assert_called_once()
            mock_analysis_instance.analyze_content.assert_called_once()

            # Verify analysis ID can be used for status lookup
            analysis_id = data["analysisId"]
            status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["analysisId"] == analysis_id
            assert status_data["status"] == "completed"

    def test_cache_behavior_comprehensive(self, client, twitter_sample_data):
        """Test comprehensive caching behavior."""
        content_data, analysis_result = twitter_sample_data

        # Step 1: First request (cache miss)
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup for cache miss
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = analysis_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None  # Cache miss
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            start_time = time.time()
            response1 = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://twitter.com/user/status/1234567890"},
            )
            uncached_time = time.time() - start_time

            assert response1.status_code == 200
            data1 = response1.json()
            assert data1["cached"] is False

            # Verify cache was called for set operation (background task)
            mock_cache_instance.get.assert_called_once()

        # Step 2: Second request (cache hit)
        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            cached_result = {
                "place_info": analysis_result.place_info.dict(),
                "confidence": analysis_result.confidence,
                "analysis_time": analysis_result.analysis_time,
                "content_metadata": {
                    "title": content_data.title,
                    "description": content_data.description,
                    "images": content_data.images[:3],
                    "extraction_time": content_data.extraction_time,
                },
            }

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = cached_result
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            start_time = time.time()
            response2 = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://twitter.com/user/status/1234567890"},
            )
            cached_time = time.time() - start_time

            assert response2.status_code == 200
            data2 = response2.json()
            assert data2["cached"] is True

            # Cache hit should be significantly faster
            assert cached_time < uncached_time * 0.5
            assert cached_time < 1.0  # Should be under 1 second

            # Results should be identical
            assert (
                data2["result"]["placeInfo"]["name"]
                == data1["result"]["placeInfo"]["name"]
            )
            assert data2["result"]["confidence"] == data1["result"]["confidence"]

        # Step 3: Force refresh (bypass cache)
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = analysis_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response3 = client.post(
                "/api/v1/links/analyze",
                json={
                    "url": "https://twitter.com/user/status/1234567890",
                    "force_refresh": True,
                },
            )

            assert response3.status_code == 200
            data3 = response3.json()
            assert data3["cached"] is False

            # Cache should not be checked when force_refresh=True
            mock_cache_instance.get.assert_not_called()

    def test_error_scenarios_comprehensive(self, client):
        """Test comprehensive error handling scenarios."""

        # Test 1: Invalid URL format
        response = client.post("/api/v1/links/analyze", json={"url": "not-a-valid-url"})
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("URL must start with http" in str(err) for err in error_detail)

        # Test 2: Content extraction failure
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.side_effect = Exception(
                "Content extraction failed"
            )
            mock_extractor.return_value = mock_extractor_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/extraction_fail/"},
            )
            assert response.status_code == 500

        # Test 3: AI analysis failure
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_content = ContentExtractResult(
                url="https://instagram.com/p/ai_fail/",
                title="Test",
                description="Test",
                images=[],
                platform="instagram",
                extraction_time=0.5,
                success=True,
            )

            failed_analysis = PlaceAnalysisResult(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=0.5,
                model_version="gemini-pro-1.0",
                error="AI service temporarily unavailable",
            )

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = failed_analysis
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/ai_fail/"},
            )
            assert response.status_code == 503
            assert "AI analysis service unavailable" in response.json()["detail"]

        # Test 4: Rate limiting
        from app.exceptions.ai import RateLimitError

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_content = ContentExtractResult(
                url="https://instagram.com/p/rate_limit/",
                title="Test",
                description="Test",
                images=[],
                platform="instagram",
                extraction_time=0.5,
                success=True,
            )

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.side_effect = RateLimitError(
                "Rate limit exceeded"
            )
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/rate_limit/"},
            )
            assert response.status_code == 429
            assert "rate limit exceeded" in response.json()["detail"]

    def test_async_webhook_workflow(self, client):
        """Test async processing with webhook notifications."""

        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Start async analysis
            response = client.post(
                "/api/v1/links/analyze",
                json={
                    "url": "https://instagram.com/p/async_webhook_test/",
                    "webhook_url": "https://myapp.com/webhook/analysis_complete",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["status"] == "in_progress"
            assert data["result"] is None

            analysis_id = data["analysisId"]

            # Check initial status
            status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            assert status_data["analysisId"] == analysis_id
            assert status_data["status"] == "in_progress"
            assert "estimatedCompletion" in status_data

            # Test cancellation
            cancel_response = client.delete(f"/api/v1/links/analyses/{analysis_id}")
            assert cancel_response.status_code == 200

            cancel_data = cancel_response.json()
            assert cancel_data["success"] is True
            assert "cancelled successfully" in cancel_data["message"]

            # Verify status changed to cancelled
            final_status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
            assert final_status_response.status_code == 200

            final_status_data = final_status_response.json()
            assert final_status_data["status"] == "cancelled"

    def test_bulk_analysis_comprehensive(self, client):
        """Test comprehensive bulk analysis functionality."""

        # Test 1: Valid bulk request
        valid_urls = [
            "https://instagram.com/p/bulk1/",
            "https://instagram.com/p/bulk2/",
            "https://twitter.com/user/status/bulk3",
        ]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": valid_urls})

        assert response.status_code == 200
        data = response.json()

        assert "batchId" in data
        assert data["totalUrls"] == 3
        assert len(data["acceptedUrls"]) == 3
        assert len(data["rejectedUrls"]) == 0
        assert "estimatedCompletion" in data

        batch_id = data["batchId"]

        # Verify batch is tracked in analysis store
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        assert batch_id in analysis_store
        batch_data = analysis_store[batch_id]
        assert batch_data["type"] == "batch"
        assert batch_data["status"] == AnalysisStatus.IN_PROGRESS
        assert batch_data["total_urls"] == 3

        # Test 2: Mixed valid/invalid URLs
        mixed_urls = [
            "https://instagram.com/p/valid1/",
            "invalid-url-format",
            "https://twitter.com/user/status/valid2",
            "ftp://unsupported.com/file",
        ]

        response = client.post("/api/v1/links/bulk-analyze", json={"urls": mixed_urls})

        assert response.status_code == 200
        data = response.json()

        assert data["totalUrls"] == 2  # Only valid URLs
        assert len(data["acceptedUrls"]) == 2
        assert len(data["rejectedUrls"]) == 2

        # Verify rejection reasons
        rejected_urls = {r["url"]: r["reason"] for r in data["rejectedUrls"]}
        assert "invalid-url-format" in rejected_urls
        assert "ftp://unsupported.com/file" in rejected_urls

        # Test 3: All invalid URLs
        invalid_urls = ["bad-url", "another-bad-url"]

        response = client.post(
            "/api/v1/links/bulk-analyze", json={"urls": invalid_urls}
        )

        assert response.status_code == 400
        assert "No valid URLs" in response.json()["detail"]

        # Test 4: Empty URL list
        response = client.post("/api/v1/links/bulk-analyze", json={"urls": []})

        assert response.status_code == 422

    def test_performance_requirements(self, client, instagram_sample_data):
        """Test that system meets performance requirements."""
        content_data, analysis_result = instagram_sample_data

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup fast mocks
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = analysis_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Test single request performance
            start_time = time.time()
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/performance_test/"},
            )
            end_time = time.time()

            processing_time = end_time - start_time

            assert response.status_code == 200
            assert processing_time < 10.0  # Should complete within 10 seconds

            data = response.json()
            assert data["processingTime"] > 0

            # Test cache hit performance
            cached_result = {
                "place_info": analysis_result.place_info.dict(),
                "confidence": analysis_result.confidence,
                "analysis_time": analysis_result.analysis_time,
                "content_metadata": {
                    "title": content_data.title,
                    "description": content_data.description,
                    "images": content_data.images[:3],
                    "extraction_time": content_data.extraction_time,
                },
            }

            mock_cache_instance.get.return_value = cached_result

            start_time = time.time()
            cache_response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cache_performance/"},
            )
            cache_time = time.time() - start_time

            assert cache_response.status_code == 200
            assert cache_time < 1.0  # Cache hits should be under 1 second
            assert cache_response.json()["cached"] is True

    def test_data_quality_and_validation(self, client):
        """Test data quality validation throughout the system."""

        # Test high-quality result
        high_quality_content = ContentExtractResult(
            url="https://instagram.com/p/high_quality/",
            title="Best Korean BBQ in Seoul 🥩",
            description="Incredible hanwoo beef at this traditional Korean BBQ restaurant in Gangnam. The marbling was perfect and the service was exceptional! #koreanbbq #hanwoo #gangnam #seoul #foodie",
            images=[
                "https://example.com/high_quality_food.jpg",
                "https://example.com/restaurant_interior.jpg",
            ],
            platform="instagram",
            extraction_time=0.7,
            success=True,
            hashtags=["koreanbbq", "hanwoo", "gangnam", "seoul", "foodie"],
            author="seoul_food_critic",
            posted_at="2024-01-22T18:45:00Z",
        )

        high_quality_result = PlaceAnalysisResult(
            success=True,
            place_info=PlaceInfo(
                name="Premium Hanwoo House",
                category="restaurant",
                address="서울시 강남구 테헤란로 789, 강남역 1번 출구 도보 5분",
                description="프리미엄 한우 전문점으로 최고급 한우와 전통 한식을 제공합니다.",
                phone="02-1234-5678",
                website="https://premiumhanwoo.co.kr",
                keywords=["한우", "고기", "강남", "프리미엄", "전통", "한식"],
                confidence=0.96,
            ),
            confidence=0.96,
            analysis_time=2.1,
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
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = high_quality_content
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = high_quality_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/high_quality/"},
            )

            assert response.status_code == 200
            data = response.json()

            # Validate response structure
            assert data["success"] is True
            assert data["status"] == "completed"

            result = data["result"]

            # Validate confidence scores
            assert result["confidence"] >= 0.9  # High confidence threshold

            # Validate place information completeness
            place = result["placeInfo"]
            assert place["name"] is not None and len(place["name"]) > 0
            assert place["category"] in [
                "restaurant",
                "cafe",
                "bar",
                "tourist_attraction",
                "shopping",
                "accommodation",
                "entertainment",
                "other",
            ]
            assert place["address"] is not None and len(place["address"]) > 0
            assert isinstance(place["keywords"], list) and len(place["keywords"]) > 0
            assert place["confidence"] == result["confidence"]

            # Validate content metadata
            content_meta = result["contentMetadata"]
            assert content_meta["title"] is not None
            assert content_meta["description"] is not None
            assert isinstance(content_meta["images"], list)
            assert content_meta["extractionTime"] > 0

            # Validate analysis metrics
            assert result["analysisTime"] > 0

    def test_monitoring_and_observability(self, client):
        """Test monitoring and observability features."""

        # Test service status endpoint
        response = client.get("/api/v1/links/status")
        assert response.status_code == 200

        status_data = response.json()
        required_fields = [
            "service",
            "status",
            "cache_connection",
            "active_analyses",
            "total_analyses",
            "timestamp",
        ]

        for field in required_fields:
            assert field in status_data

        assert status_data["service"] == "Link Analysis API"
        assert status_data["status"] in ["healthy", "degraded"]
        assert isinstance(status_data["active_analyses"], int)
        assert isinstance(status_data["total_analyses"], int)

        # Test cache statistics endpoint
        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            from app.services.monitoring.cache_manager import CacheStats

            mock_cache_instance = AsyncMock()
            mock_stats = CacheStats(
                cache_hits=150,
                cache_misses=30,
                l1_hits=100,
                l2_hits=50,
                total_requests=180,
            )
            mock_cache_instance.get_stats.return_value = mock_stats
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            response = client.get("/api/v1/links/cache/stats")
            assert response.status_code == 200

            stats_data = response.json()

            # Verify all required statistics are present
            required_stats = [
                "cache_hits",
                "cache_misses",
                "l1_hits",
                "l2_hits",
                "hit_rate",
                "l1_hit_rate",
                "l2_hit_rate",
                "total_requests",
            ]

            for stat in required_stats:
                assert stat in stats_data

            assert stats_data["cache_hits"] == 150
            assert stats_data["cache_misses"] == 30
            assert stats_data["total_requests"] == 180
            assert 0 <= stats_data["hit_rate"] <= 1
            assert 0 <= stats_data["l1_hit_rate"] <= 1
            assert 0 <= stats_data["l2_hit_rate"] <= 1

    @pytest.mark.asyncio
    async def test_concurrent_analysis_load(self, async_client):
        """Test system behavior under concurrent load."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks for concurrent testing
            mock_content = ContentExtractResult(
                url="https://instagram.com/p/concurrent_test/",
                title="Concurrent Test",
                description="Testing concurrent requests",
                images=["test.jpg"],
                platform="instagram",
                extraction_time=0.3,
                success=True,
            )

            mock_result = PlaceAnalysisResult(
                success=True,
                place_info=PlaceInfo(
                    name="Concurrent Test Place",
                    category="restaurant",
                    address="Test Address",
                    confidence=0.8,
                ),
                confidence=0.8,
                analysis_time=0.5,
                model_version="gemini-pro-1.0",
                error=None,
            )

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = mock_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Create concurrent requests
            async def make_request(request_id):
                response = await async_client.post(
                    "/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/concurrent_{request_id}/"},
                )
                return response

            # Test with 15 concurrent requests
            start_time = time.time()
            tasks = [make_request(i) for i in range(15)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()

            total_time = end_time - start_time

            # Analyze results
            successful_responses = [
                r
                for r in responses
                if hasattr(r, "status_code") and r.status_code == 200
            ]

            # Verify performance under load
            assert len(successful_responses) >= 12  # At least 80% success rate
            assert total_time < 30.0  # Should handle 15 requests in under 30 seconds

            # Verify response consistency
            for response in successful_responses:
                data = response.json()
                assert data["success"] is True
                assert "analysisId" in data
                assert "result" in data or data["status"] == "in_progress"

    def test_system_resilience(self, client):
        """Test system resilience and recovery capabilities."""

        # Test 1: Cache failure recovery
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_content = ContentExtractResult(
                url="https://instagram.com/p/resilience_test/",
                title="Resilience Test",
                description="Testing system resilience",
                images=["test.jpg"],
                platform="instagram",
                extraction_time=0.4,
                success=True,
            )

            mock_result = PlaceAnalysisResult(
                success=True,
                place_info=PlaceInfo(
                    name="Resilience Test Place",
                    category="cafe",
                    address="Resilience Street 123",
                    confidence=0.85,
                ),
                confidence=0.85,
                analysis_time=1.0,
                model_version="gemini-pro-1.0",
                error=None,
            )

            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = mock_content
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = mock_result
            mock_analysis.return_value = mock_analysis_instance

            # Simulate cache failure
            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.side_effect = Exception("Cache connection failed")
            mock_cache_instance.initialize.side_effect = Exception("Cache unavailable")
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # System should still work without cache
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/resilience_test/"},
            )

            # Should succeed despite cache failure (graceful degradation)
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["cached"] is False

    def test_end_to_end_data_flow(self, client, instagram_sample_data):
        """Test complete end-to-end data flow validation."""
        content_data, analysis_result = instagram_sample_data

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            mock_extractor_instance = AsyncMock()
            mock_extractor_instance.extract_content.return_value = content_data
            mock_extractor.return_value = mock_extractor_instance

            mock_analysis_instance = AsyncMock()
            mock_analysis_instance.analyze_content.return_value = analysis_result
            mock_analysis.return_value = mock_analysis_instance

            mock_cache_instance = AsyncMock()
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Execute complete workflow
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/CxxxxxxxxxxxX/"},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify complete data transformation pipeline

            # 1. URL Input -> Content Extraction
            mock_extractor_instance.extract_content.assert_called_once_with(
                "https://instagram.com/p/CxxxxxxxxxxxX/"
            )

            # 2. Content Extraction -> AI Analysis
            call_args = mock_analysis_instance.analyze_content.call_args
            content_metadata = call_args[0][0]

            assert content_metadata.title == content_data.title
            assert content_metadata.description == content_data.description
            assert content_metadata.images == content_data.images

            # 3. AI Analysis -> Final Response
            result = data["result"]

            # Verify data integrity through the pipeline
            assert result["confidence"] == analysis_result.confidence
            assert result["analysisTime"] == analysis_result.analysis_time

            place_info = result["placeInfo"]
            assert place_info["name"] == analysis_result.place_info.name
            assert place_info["category"] == analysis_result.place_info.category
            assert place_info["confidence"] == analysis_result.place_info.confidence

            content_meta = result["contentMetadata"]
            assert content_meta["title"] == content_data.title
            assert content_meta["extractionTime"] == content_data.extraction_time

            # 4. Response Format Validation (camelCase conversion)
            assert "analysisId" in data  # snake_case -> camelCase
            assert "processingTime" in data
            assert "placeInfo" in result
            assert "contentMetadata" in result

            print("✅ End-to-end data flow validation completed successfully")

    def teardown_method(self):
        """Clean up after each test."""
        # Clear analysis store
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        analysis_store.clear()
