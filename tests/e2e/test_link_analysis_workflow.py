"""
End-to-End tests for complete link analysis user workflow.

Tests the entire user journey from link submission to getting place recommendations.
Validates the complete system integration including API, services, cache, and error handling.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from tests.utils.test_helpers import (
    MockFactory,
    PerformanceTestHelpers,
    TestDataBuilder,
    ValidationHelpers,
)

from app.main import app


class TestLinkAnalysisUserWorkflowE2E:
    """End-to-end tests for complete link analysis user workflow."""

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client for E2E testing."""
        return TestClient(app)

    @pytest.fixture
    def realistic_mocks(self):
        """Setup realistic mocks for external dependencies."""
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup realistic content extraction
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content = AsyncMock()

            # Setup realistic AI analysis
            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content = AsyncMock()

            # Setup realistic cache behavior
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.initialize = AsyncMock()
            mock_cache_instance.close = AsyncMock()
            mock_cache_instance.get = AsyncMock()
            mock_cache_instance.set = AsyncMock()

            yield {
                "extractor": mock_extractor_instance,
                "analysis": mock_analysis_instance,
                "cache": mock_cache_instance,
            }

    def test_complete_user_workflow_instagramRestaurant_success(
        self, client, realistic_mocks
    ):
        """
        Test complete user workflow: Instagram restaurant post → place recommendation.

        User Journey:
        1. User discovers restaurant on Instagram
        2. User copies Instagram URL
        3. User submits URL to Hotly app
        4. System extracts content from Instagram
        5. AI analyzes content to identify restaurant
        6. System returns detailed place information
        7. User can save place or get directions
        """
        # Given - User found interesting restaurant on Instagram
        instagram_url = "https://instagram.com/p/amazing_korean_bbq/"

        # Setup realistic scenario: High-quality Korean BBQ restaurant
        builder = TestDataBuilder()
        content_result = builder.with_korean_bbq_content().build_content_result()
        content_result.url = instagram_url

        analysis_result = builder.build_analysis_result()

        realistic_mocks["cache"].get.return_value = None  # Cache miss
        realistic_mocks["extractor"].extract_content.return_value = content_result
        realistic_mocks["analysis"].analyze_content.return_value = analysis_result

        # When - User submits Instagram URL to app
        start_time = time.time()
        response = client.post(
            "/api/v1/links/analyze", json={"url": instagram_url, "force_refresh": False}
        )
        end_time = time.time()

        # Then - System provides comprehensive place information
        assert response.status_code == 200
        result = response.json()

        # Validate complete workflow success
        ValidationHelpers.assert_api_response_structure(
            result, ["success", "status", "analysisId", "result", "processingTime"]
        )

        assert result["success"] is True
        assert result["status"] == "completed"
        assert result["cached"] is False

        # Validate place information quality
        place_info = result["result"]["placeInfo"]
        ValidationHelpers.assert_valid_place_info(
            MockFactory.create_place_info(**place_info), min_confidence=0.8
        )

        # Validate content metadata preservation
        content_metadata = result["result"]["contentMetadata"]
        assert "Korean BBQ" in content_metadata["title"]
        assert "gangnam" in content_metadata["description"].lower()
        assert len(content_metadata["images"]) > 0

        # Validate performance requirements
        processing_time = end_time - start_time
        PerformanceTestHelpers.assert_performance_metrics(
            processing_time, 10.0, "Complete Analysis Workflow"
        )

        # Verify service integration chain
        realistic_mocks["extractor"].extract_content.assert_called_once_with(
            instagram_url
        )
        realistic_mocks["analysis"].analyze_content.assert_called_once()
        realistic_mocks["cache"].set.assert_called_once()

    def test_user_workflow_with_cache_hit_fasterResponse(self, client, realistic_mocks):
        """
        Test user workflow with cache hit scenario.

        User Journey:
        1. User submits URL that was previously analyzed
        2. System finds cached result
        3. System returns cached data immediately
        4. User gets instant response
        """
        # Given - URL that was previously analyzed and cached
        cached_url = "https://instagram.com/p/previously_analyzed/"

        cached_result = {
            "place_info": {
                "name": "Previously Analyzed Restaurant",
                "category": "restaurant",
                "address": "Seoul, Korea",
                "confidence": 0.91,
            },
            "confidence": 0.91,
            "analysis_time": 2.1,
            "content_metadata": {
                "title": "Cached Restaurant Post",
                "description": "This was analyzed before",
                "images": ["cached_image.jpg"],
                "extraction_time": 0.8,
            },
        }

        realistic_mocks["cache"].get.return_value = cached_result

        # When - User submits previously analyzed URL
        start_time = time.time()
        response = client.post("/api/v1/links/analyze", json={"url": cached_url})
        end_time = time.time()

        # Then - System returns cached result quickly
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["cached"] is True
        assert result["result"]["placeInfo"]["name"] == "Previously Analyzed Restaurant"

        # Cache hit should be very fast
        cache_response_time = end_time - start_time
        assert cache_response_time < 2.0  # Should be under 2 seconds

        # Verify only cache was accessed, no extraction/analysis
        realistic_mocks["cache"].get.assert_called_once()
        realistic_mocks["extractor"].extract_content.assert_not_called()
        realistic_mocks["analysis"].analyze_content.assert_not_called()

    def test_user_workflow_error_recovery_gracefulHandling(
        self, client, realistic_mocks
    ):
        """
        Test user workflow error recovery scenarios.

        Error Scenarios:
        1. Content extraction fails (private post)
        2. AI analysis fails (service down)
        3. Network timeout
        4. Invalid URL format
        """
        # Scenario 1: Content extraction fails
        realistic_mocks["cache"].get.return_value = None
        realistic_mocks["extractor"].extract_content.side_effect = Exception(
            "Post is private or deleted"
        )

        response = client.post(
            "/api/v1/links/analyze",
            json={"url": "https://instagram.com/p/private_post/"},
        )

        assert response.status_code in [500, 422, 503]
        error_data = response.json()
        assert "detail" in error_data or "error" in error_data

        # Scenario 2: AI analysis fails
        realistic_mocks["extractor"].extract_content.side_effect = None
        realistic_mocks[
            "extractor"
        ].extract_content.return_value = MockFactory.create_content_extract_result()

        failed_analysis = MockFactory.create_place_analysis_result(
            success=False, place_info=None, error="AI service temporarily unavailable"
        )
        realistic_mocks["analysis"].analyze_content.return_value = failed_analysis

        response = client.post(
            "/api/v1/links/analyze", json={"url": "https://instagram.com/p/ai_failure/"}
        )

        assert response.status_code == 503
        assert "AI analysis service unavailable" in response.json()["detail"]

    def test_async_workflow_with_webhook_backgroundProcessing(
        self, client, realistic_mocks
    ):
        """
        Test asynchronous workflow with webhook notification.

        User Journey:
        1. User submits URL with webhook for async processing
        2. System immediately returns analysis ID
        3. System processes in background
        4. User can check status via analysis ID
        5. System sends webhook when complete
        """
        # Given - User wants async processing with webhook
        async_url = "https://instagram.com/p/async_processing/"
        webhook_url = "https://user-app.com/webhook/analysis-complete"

        # Setup mocks for async processing
        realistic_mocks["cache"].get.return_value = None

        # When - User submits request with webhook
        response = client.post(
            "/api/v1/links/analyze", json={"url": async_url, "webhook_url": webhook_url}
        )

        # Then - System immediately returns with in-progress status
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["status"] == "in_progress"
        assert result["result"] is None  # No immediate result
        assert "analysisId" in result

        analysis_id = result["analysisId"]

        # User can check status
        status_response = client.get(f"/api/v1/links/analyses/{analysis_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["analysisId"] == analysis_id
        assert status_data["status"] in ["in_progress", "completed"]

    def test_bulk_analysis_workflow_multipleLinks(self, client, realistic_mocks):
        """
        Test bulk analysis workflow for multiple links.

        User Journey:
        1. User has multiple Instagram links from food tour
        2. User submits all links for batch processing
        3. System processes all links efficiently
        4. User gets batch ID to track progress
        5. System provides results as they complete
        """
        # Given - User has multiple food-related links
        food_tour_urls = [
            "https://instagram.com/p/korean_bbq_spot/",
            "https://instagram.com/p/amazing_cafe_find/",
            "https://instagram.com/p/street_food_heaven/",
            "https://instagram.com/p/dessert_paradise/",
        ]

        # When - User submits batch analysis
        response = client.post(
            "/api/v1/links/bulk-analyze",
            json={
                "urls": food_tour_urls,
                "webhook_url": "https://user-app.com/webhook/batch-complete",
            },
        )

        # Then - System accepts batch and provides tracking info
        assert response.status_code == 200
        result = response.json()

        assert "batchId" in result
        assert result["totalUrls"] == 4
        assert len(result["acceptedUrls"]) == 4
        assert len(result["rejectedUrls"]) == 0
        assert "estimatedCompletion" in result

        batch_id = result["batchId"]

        # Verify batch is tracked in system
        from app.api.api_v1.endpoints.link_analysis import analysis_store

        assert batch_id in analysis_store
        batch_data = analysis_store[batch_id]
        assert batch_data["type"] == "batch"
        assert batch_data["total_urls"] == 4

    def test_mobile_user_workflow_optimizedForMobile(self, client, realistic_mocks):
        """
        Test mobile user workflow with mobile-specific considerations.

        Mobile User Journey:
        1. User shares Instagram link from mobile app
        2. Link opens in mobile browser
        3. System detects mobile and optimizes response
        4. User gets mobile-friendly place information
        5. User can quickly save or share place
        """
        # Given - Mobile user agent and mobile-optimized content
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
        }

        mobile_url = "https://instagram.com/p/mobile_restaurant/"

        # Setup mobile-optimized content
        builder = TestDataBuilder()
        content_result = builder.with_korean_bbq_content().build_content_result()
        content_result.url = mobile_url

        analysis_result = builder.build_analysis_result()

        realistic_mocks["cache"].get.return_value = None
        realistic_mocks["extractor"].extract_content.return_value = content_result
        realistic_mocks["analysis"].analyze_content.return_value = analysis_result

        # When - Mobile user submits link
        response = client.post(
            "/api/v1/links/analyze", json={"url": mobile_url}, headers=mobile_headers
        )

        # Then - System provides mobile-optimized response
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True

        # Verify mobile considerations
        content_metadata = result["result"]["contentMetadata"]
        assert len(content_metadata["images"]) <= 3  # Limited images for mobile

        place_info = result["result"]["placeInfo"]
        assert place_info["name"] is not None
        assert place_info["address"] is not None

    def test_performance_under_concurrent_users_scalability(
        self, client, realistic_mocks
    ):
        """
        Test system performance under concurrent user load.

        Load Test Scenario:
        1. 20 concurrent users submit different links
        2. System processes all requests efficiently
        3. All users get responses within acceptable time
        4. System maintains stability under load
        """
        # Given - Multiple concurrent users with different links
        concurrent_urls = [
            f"https://instagram.com/p/concurrent_user_{i}/" for i in range(20)
        ]

        # Setup mocks for load testing
        realistic_mocks["cache"].get.return_value = None
        realistic_mocks[
            "extractor"
        ].extract_content.return_value = MockFactory.create_content_extract_result()
        realistic_mocks[
            "analysis"
        ].analyze_content.return_value = MockFactory.create_place_analysis_result()

        def make_request(url):
            """Single user request."""
            start_time = time.time()
            response = client.post("/api/v1/links/analyze", json={"url": url})
            end_time = time.time()

            return {
                "url": url,
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # When - Execute concurrent requests
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, url) for url in concurrent_urls]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Then - Verify performance under load
        successful_requests = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)

        # Performance assertions
        assert successful_requests >= 18  # At least 90% success rate
        assert total_time < 30.0  # All requests complete within 30 seconds
        assert avg_response_time < 5.0  # Average response under 5 seconds
        assert max_response_time < 15.0  # No request over 15 seconds

        print(f"Load test results: {successful_requests}/{len(results)} successful")
        print(f"Average response time: {avg_response_time:.2f}s")
        print(f"Max response time: {max_response_time:.2f}s")

    def test_data_quality_end_to_end_highConfidenceResults(
        self, client, realistic_mocks
    ):
        """
        Test data quality throughout the complete workflow.

        Quality Assurance:
        1. High-quality content produces high-confidence results
        2. Place information is accurate and complete
        3. Content metadata is preserved correctly
        4. Confidence scores reflect actual quality
        """
        # Given - High-quality Michelin restaurant content
        michelin_url = "https://instagram.com/p/michelin_restaurant/"

        builder = TestDataBuilder()
        content_result = builder.with_high_quality_content().build_content_result()
        content_result.url = michelin_url

        analysis_result = builder.build_analysis_result()

        realistic_mocks["cache"].get.return_value = None
        realistic_mocks["extractor"].extract_content.return_value = content_result
        realistic_mocks["analysis"].analyze_content.return_value = analysis_result

        # When - User submits high-quality content
        response = client.post("/api/v1/links/analyze", json={"url": michelin_url})

        # Then - System provides high-quality results
        assert response.status_code == 200
        result = response.json()

        # Validate high-quality output
        assert result["result"]["confidence"] >= 0.9

        place_info = result["result"]["placeInfo"]
        assert place_info["confidence"] >= 0.9
        assert place_info["name"] is not None
        assert place_info["category"] == "restaurant"
        assert place_info["address"] is not None
        assert len(place_info["keywords"]) >= 5

        # Validate content preservation
        content_metadata = result["result"]["contentMetadata"]
        assert "Michelin" in content_metadata["title"]
        assert len(content_metadata["description"]) > 100  # Rich description

    def test_error_boundary_workflow_systemResilience(self, client, realistic_mocks):
        """
        Test system resilience with various error boundary conditions.

        Error Boundaries:
        1. Malformed requests
        2. System overload
        3. Service dependencies failing
        4. Data corruption scenarios
        """
        # Test 1: Malformed requests
        malformed_requests = [
            {},  # Empty request
            {"url": ""},  # Empty URL
            {"url": "not-a-url"},  # Invalid URL
            {"url": "https://unsupported.com/post"},  # Unsupported platform
        ]

        for request_data in malformed_requests:
            response = client.post("/api/v1/links/analyze", json=request_data)
            assert response.status_code in [400, 422]  # Proper validation error

        # Test 2: Service dependency failures
        realistic_mocks["cache"].get.side_effect = Exception("Cache service down")

        response = client.post(
            "/api/v1/links/analyze",
            json={"url": "https://instagram.com/p/cache_error/"},
        )

        # System should handle cache failure gracefully
        # May succeed without cache or return appropriate error
        assert response.status_code in [200, 503]

    def test_accessibility_workflow_inclusiveDesign(self, client, realistic_mocks):
        """
        Test workflow accessibility for users with different needs.

        Accessibility Considerations:
        1. API responses include all necessary metadata
        2. Error messages are clear and actionable
        3. Content descriptions are comprehensive
        4. Alternative text for images is provided
        """
        # Given - User with accessibility needs submitting content
        accessible_url = "https://instagram.com/p/accessible_content/"

        # Setup content with accessibility considerations
        content_result = MockFactory.create_content_extract_result(
            url=accessible_url,
            title="Accessible Restaurant Experience - Full Description",
            description="Detailed description of restaurant experience including accessibility features, ambiance details, and complete menu information for screen reader users",
        )

        analysis_result = MockFactory.create_place_analysis_result(
            place_info=MockFactory.create_place_info(
                name="Accessible Restaurant",
                description="Restaurant with full accessibility features and detailed descriptions",
            )
        )

        realistic_mocks["cache"].get.return_value = None
        realistic_mocks["extractor"].extract_content.return_value = content_result
        realistic_mocks["analysis"].analyze_content.return_value = analysis_result

        # When - User requests analysis
        response = client.post("/api/v1/links/analyze", json={"url": accessible_url})

        # Then - Response includes comprehensive accessibility information
        assert response.status_code == 200
        result = response.json()

        # Verify comprehensive information available
        place_info = result["result"]["placeInfo"]
        assert place_info["name"] is not None
        assert place_info["description"] is not None
        assert len(place_info["description"]) > 50  # Detailed description

        content_metadata = result["result"]["contentMetadata"]
        assert len(content_metadata["description"]) > 100  # Rich content description


# Test fixtures and data for E2E tests
@pytest.fixture
def real_world_test_scenarios():
    """Real-world test scenarios for comprehensive E2E testing."""
    return {
        "food_blogger_journey": {
            "persona": "Food blogger discovering restaurants",
            "urls": [
                "https://instagram.com/p/hidden_gem_restaurant/",
                "https://instagram.com/p/michelin_star_experience/",
                "https://instagram.com/p/street_food_tour/",
            ],
            "expected_categories": ["restaurant", "restaurant", "restaurant"],
            "min_confidence": 0.8,
        },
        "tourist_exploration": {
            "persona": "Tourist exploring Seoul attractions",
            "urls": [
                "https://instagram.com/p/gyeongbokgung_palace/",
                "https://instagram.com/p/hongdae_nightlife/",
                "https://instagram.com/p/namsan_tower_view/",
            ],
            "expected_categories": ["attraction", "bar", "attraction"],
            "min_confidence": 0.7,
        },
        "cafe_hopping": {
            "persona": "Remote worker finding study spots",
            "urls": [
                "https://instagram.com/p/perfect_study_cafe/",
                "https://instagram.com/p/aesthetic_coffee_shop/",
                "https://instagram.com/p/coworking_cafe/",
            ],
            "expected_categories": ["cafe", "cafe", "cafe"],
            "min_confidence": 0.75,
        },
    }
