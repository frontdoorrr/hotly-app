"""
End-to-End Test Template

E2E tests verify complete user workflows from start to finish.
They test the entire application stack including UI, API, services, and database.

Use this template for testing:
- Complete user journeys
- Critical business workflows
- System integration points
- Performance under realistic conditions
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.main import app


class TestUserJourneyE2E:
    """
    Template for testing complete user journeys.

    E2E tests should:
    1. Test realistic user scenarios
    2. Use real API endpoints and database
    3. Mock only external services (payment, email, etc.)
    4. Verify system behavior under normal load
    """

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client for E2E API testing."""
        return TestClient(app)

    @pytest.fixture(scope="class")
    def browser(self):
        """Selenium WebDriver for UI testing."""
        # Use headless browser for CI/CD
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)

        yield driver

        driver.quit()

    def test_link_analysis_complete_workflow_userSuccess(self, client):
        """
        Test complete link analysis workflow from user perspective.

        User Journey:
        1. User submits Instagram link for analysis
        2. System extracts content from Instagram
        3. AI analyzes content to identify place information
        4. System returns place recommendations
        5. User can save place to favorites
        """
        # Given - User has a link to analyze
        instagram_url = "https://instagram.com/p/restaurant_post/"

        # Mock external services (Instagram API, Google AI)
        with patch(
            "app.services.content_extractor.InstagramExtractor"
        ) as mock_instagram, patch(
            "app.services.ai.gemini_analyzer.GeminiAnalyzer"
        ) as mock_ai:
            # Setup realistic mock responses
            mock_instagram.return_value.extract.return_value = {
                "title": "Amazing Korean BBQ Night! 🥩",
                "description": "Had the most incredible Korean BBQ experience at this hidden gem in Gangnam! The meat quality was outstanding and the banchan was endless. Perfect for date night! #korean #bbq #gangnam #datenight #seoul",
                "images": [
                    "https://instagram.com/image1.jpg",
                    "https://instagram.com/image2.jpg",
                ],
                "hashtags": ["korean", "bbq", "gangnam", "datenight", "seoul"],
                "author": "seoul_foodie_2024",
                "posted_at": "2024-01-15T19:30:00Z",
            }

            mock_ai.return_value.analyze.return_value = {
                "place_name": "Gangnam Premium Korean BBQ",
                "category": "restaurant",
                "address": "123 Gangnam-daero, Gangnam-gu, Seoul",
                "description": "Premium Korean BBQ restaurant known for high-quality meat",
                "confidence": 0.94,
                "keywords": ["korean", "bbq", "premium", "gangnam", "date"],
            }

            # When - User submits link for analysis
            response = client.post(
                "/api/v1/links/analyze",
                json={"url": instagram_url, "force_refresh": False},
            )

            # Then - System successfully analyzes and returns place info
            assert response.status_code == 200
            result = response.json()

            # Verify complete workflow result
            assert result["success"] is True
            assert result["status"] == "completed"

            place_info = result["result"]["placeInfo"]
            assert place_info["name"] == "Gangnam Premium Korean BBQ"
            assert place_info["category"] == "restaurant"
            assert place_info["confidence"] >= 0.9
            assert "gangnam" in place_info["address"].lower()

            # Verify content metadata is included
            content_meta = result["result"]["contentMetadata"]
            assert "Korean BBQ" in content_meta["title"]
            assert len(content_meta["images"]) > 0

            # Step 2: User saves place to favorites
            place_id = place_info.get("id")
            if place_id:
                save_response = client.post(
                    f"/api/v1/places/{place_id}/favorite",
                    headers={"Authorization": "Bearer test_token"},
                )

                # Should successfully save (or handle auth appropriately)
                assert save_response.status_code in [
                    200,
                    201,
                    401,
                ]  # 401 if auth needed

    def test_user_onboarding_complete_flow_guidesUserThroughSetup(self, client):
        """
        Test complete user onboarding workflow.

        User Journey:
        1. New user signs up
        2. System guides through preference setup
        3. User provides location and interests
        4. System generates personalized recommendations
        5. User completes onboarding successfully
        """
        # Given - New user registration data
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "name": "Test User",
        }

        # Step 1: User registration
        signup_response = client.post("/api/v1/auth/signup", json=user_data)
        assert signup_response.status_code in [201, 409]  # 201 created, 409 if exists

        if signup_response.status_code == 201:
            user_id = signup_response.json()["user_id"]

            # Step 2: Start onboarding process
            onboarding_response = client.post(
                f"/api/v1/onboarding/start", json={"user_id": user_id}
            )
            assert onboarding_response.status_code == 200

            session_id = onboarding_response.json()["session_id"]

            # Step 3: User provides preferences
            preferences_data = {
                "categories": ["restaurant", "cafe", "culture"],
                "budget_level": "medium",
                "location": {
                    "lat": 37.5665,
                    "lng": 126.9780,
                    "address": "Gangnam-gu, Seoul",
                },
                "interests": ["korean_food", "coffee", "art"],
            }

            prefs_response = client.post(
                f"/api/v1/onboarding/{session_id}/preferences", json=preferences_data
            )
            assert prefs_response.status_code == 200

            # Step 4: Complete onboarding
            complete_response = client.post(f"/api/v1/onboarding/{session_id}/complete")
            assert complete_response.status_code == 200

            completion_data = complete_response.json()
            assert completion_data["status"] == "completed"
            assert "recommendations" in completion_data
            assert len(completion_data["recommendations"]) > 0

    @pytest.mark.slow
    def test_performance_under_load_handlesMultipleUsers(self, client):
        """
        Test system performance with multiple concurrent users.

        Simulates realistic load:
        - 10 concurrent users
        - Each performing link analysis
        - System should handle load gracefully
        """
        import concurrent.futures
        import time

        # Given - Multiple URLs to analyze concurrently
        test_urls = [f"https://instagram.com/p/test_post_{i}/" for i in range(10)]

        def analyze_link(url):
            """Single user link analysis."""
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

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(analyze_link, url) for url in test_urls]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        total_time = time.time() - start_time

        # Then - System handles load within performance requirements
        successful_requests = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["response_time"] for r in results) / len(results)

        # Performance assertions
        assert successful_requests >= 8  # At least 80% success rate
        assert total_time < 30.0  # All requests complete within 30 seconds
        assert avg_response_time < 10.0  # Average response under 10 seconds
        assert max(r["response_time"] for r in results) < 20.0  # No request over 20s

    def test_error_recovery_workflow_handlesFailuresGracefully(self, client):
        """
        Test system recovery from various failure scenarios.

        Error Scenarios:
        1. External service failures (Instagram API down)
        2. AI service unavailable
        3. Database connection issues
        4. Network timeouts
        """
        # Scenario 1: External service failure
        with patch("app.services.content_extractor.ContentExtractor") as mock_extractor:
            mock_extractor.return_value.extract_content.side_effect = ConnectionError(
                "Instagram API unavailable"
            )

            response = client.post(
                "/api/v1/links/analyze", json={"url": "https://instagram.com/p/test/"}
            )

            # System should handle gracefully
            assert response.status_code in [503, 502, 500]
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data

        # Scenario 2: AI service failure with fallback
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_ai:
            # Content extraction succeeds
            mock_extractor.return_value.extract_content.return_value = Mock(
                title="Test Restaurant",
                description="Test description",
                platform="instagram",
                success=True,
            )

            # AI analysis fails
            mock_ai.return_value.analyze_content.side_effect = Exception(
                "AI service temporarily unavailable"
            )

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/ai_fail/"},
            )

            # Should return error but not crash
            assert response.status_code in [503, 500]

    @pytest.mark.integration
    def test_cache_behavior_across_requests_maintainsPerformance(self, client):
        """
        Test caching behavior in realistic usage patterns.

        Cache Scenarios:
        1. First request (cache miss) - slower
        2. Repeat request (cache hit) - faster
        3. Cache expiration - back to slower
        4. Force refresh - bypasses cache
        """
        test_url = "https://instagram.com/p/cache_test/"

        # First request - cache miss
        start_time = time.time()
        response1 = client.post("/api/v1/links/analyze", json={"url": test_url})
        first_time = time.time() - start_time

        assert response1.status_code == 200
        result1 = response1.json()
        assert result1["cached"] is False

        # Second request - should be cached and faster
        start_time = time.time()
        response2 = client.post("/api/v1/links/analyze", json={"url": test_url})
        second_time = time.time() - start_time

        assert response2.status_code == 200
        result2 = response2.json()
        assert result2["cached"] is True
        assert second_time < first_time  # Cache hit should be faster

        # Force refresh - bypasses cache
        start_time = time.time()
        response3 = client.post(
            "/api/v1/links/analyze", json={"url": test_url, "force_refresh": True}
        )
        third_time = time.time() - start_time

        assert response3.status_code == 200
        result3 = response3.json()
        assert result3["cached"] is False
        assert third_time > second_time  # Should be slower than cache hit


class TestMobileAppE2E:
    """Template for mobile-specific E2E tests using Selenium."""

    @pytest.fixture
    def mobile_browser(self):
        """Mobile browser simulation."""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone 12"})

        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_mobile_link_sharing_workflow_worksOnMobile(self, mobile_browser):
        """
        Test link sharing workflow on mobile device.

        Mobile Journey:
        1. User opens shared link on mobile
        2. Mobile-optimized page loads
        3. User can view place details
        4. User can save to favorites
        """
        # Given - Mobile browser and shared link
        shared_link = "https://hotly-app.com/places/share/abc123"

        # When - User opens link on mobile
        mobile_browser.get(shared_link)

        # Then - Mobile page loads correctly
        wait = WebDriverWait(mobile_browser, 10)

        # Verify mobile-responsive design
        place_title = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "place-title"))
        )
        assert place_title.is_displayed()

        # Verify mobile navigation works
        save_button = mobile_browser.find_element(By.ID, "save-place-btn")
        assert save_button.is_displayed()

        # Test mobile interaction
        save_button.click()

        # Verify feedback (may require login)
        success_message = wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.CLASS_NAME, "success-message")),
                EC.presence_of_element_located((By.CLASS_NAME, "login-required")),
            )
        )
        assert success_message.is_displayed()


# Utility functions for E2E tests
def wait_for_analysis_completion(client, analysis_id, timeout=30):
    """Wait for async analysis to complete."""
    import time

    start_time = time.time()
    while time.time() - start_time < timeout:
        response = client.get(f"/api/v1/links/analyses/{analysis_id}")
        if response.status_code == 200:
            data = response.json()
            if data["status"] in ["completed", "failed"]:
                return data

        time.sleep(1)

    raise TimeoutError(f"Analysis {analysis_id} did not complete within {timeout}s")


def create_test_user(client, email="test@example.com"):
    """Create test user for E2E scenarios."""
    user_data = {"email": email, "password": "testpassword123", "name": "Test User"}

    response = client.post("/api/v1/auth/signup", json=user_data)
    if response.status_code == 409:  # User already exists
        # Login instead
        login_response = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "testpassword123"}
        )
        return login_response.json()

    return response.json()


# Test data fixtures for E2E tests
@pytest.fixture
def sample_user_journey_data():
    """Complete user journey test data."""
    return {
        "user": {
            "email": "journey_test@example.com",
            "name": "Journey Test User",
            "password": "journeytest123",
        },
        "preferences": {
            "categories": ["restaurant", "cafe", "culture"],
            "budget_level": "medium",
            "location": {
                "lat": 37.5665,
                "lng": 126.9780,
                "address": "Seoul, South Korea",
            },
        },
        "test_links": [
            "https://instagram.com/p/restaurant1/",
            "https://blog.naver.com/cafe_review/123",
            "https://youtube.com/watch?v=seoul_food_tour",
        ],
    }


@pytest.fixture
def performance_test_data():
    """Data for performance testing scenarios."""
    return {
        "concurrent_users": 10,
        "test_duration": 60,  # seconds
        "max_response_time": 10,  # seconds
        "min_success_rate": 0.95,
        "test_urls": [f"https://instagram.com/p/perf_test_{i}/" for i in range(50)],
    }
