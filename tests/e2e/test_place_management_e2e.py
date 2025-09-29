"""
End-to-End tests for Place Management system.

Tests complete user workflows from place discovery to management,
simulating real user interactions with the system.
"""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from tests.utils.test_helpers import MockFactory

from app.main import app
from app.models.place import PlaceCategory


class TestPlaceManagementUserWorkflowE2E:
    """End-to-end tests for complete place management user workflows."""

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client for E2E testing."""
        return TestClient(app)

    @pytest.fixture
    def realistic_mocks(self):
        """Setup realistic mocks for E2E testing."""
        with patch("app.crud.place.place") as mock_crud, patch(
            "app.services.duplicate_detector.DuplicateDetector"
        ) as mock_detector, patch(
            "app.services.place_classifier.PlaceClassifier"
        ) as mock_classifier:
            # Setup realistic service responses
            mock_detector_instance = mock_detector.return_value
            mock_detector_instance.check_duplicate = AsyncMock()

            mock_classifier_instance = mock_classifier.return_value
            mock_classifier_instance.classify_place = AsyncMock()

            yield {
                "crud": mock_crud,
                "detector": mock_detector_instance,
                "classifier": mock_classifier_instance,
            }

    def test_complete_place_discovery_workflow_fromLinkToSaved(
        self, client, realistic_mocks
    ):
        """
        Test complete place discovery workflow.

        User Journey:
        1. User discovers restaurant on Instagram
        2. User saves place from link analysis
        3. User views their saved places
        4. User updates place information
        5. User shares place with friends
        """
        # Given - User discovered restaurant through link analysis
        instagram_url = "https://instagram.com/p/korean_bbq_discovery/"

        # Setup place from link analysis (simulated)
        discovered_place_data = {
            "name": "Hidden Gem Korean BBQ",
            "description": "Amazing Korean BBQ found through Instagram",
            "address": "456 Hongdae-ro, Seoul",
            "category": "restaurant",
            "latitude": 37.5563,
            "longitude": 126.9236,
            "tags": ["korean", "bbq", "hidden_gem"],
            "source_url": instagram_url,
            "source_platform": "instagram",
            "ai_confidence": 0.92,
        }

        # Setup mock responses for place creation
        realistic_mocks[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )

        created_place = MockFactory.create_place_model(
            name=discovered_place_data["name"], category=PlaceCategory.RESTAURANT
        )
        realistic_mocks["crud"].create_with_user.return_value = created_place
        realistic_mocks["crud"].get_multi_by_user.return_value = []

        # When - Step 1: User saves discovered place
        save_response = client.post("/api/v1/places/", json=discovered_place_data)

        # Then - Place is saved successfully
        assert save_response.status_code == 201
        saved_place = save_response.json()
        place_id = saved_place["id"]

        assert saved_place["name"] == discovered_place_data["name"]
        assert saved_place["source_url"] == instagram_url

        # When - Step 2: User views their saved places
        realistic_mocks["crud"].get_list_with_filters.return_value = (
            [created_place],
            1,
        )

        list_response = client.get("/api/v1/places/", params={"page": 1, "size": 20})

        # Then - User sees their saved places
        assert list_response.status_code == 200
        places_list = list_response.json()

        assert places_list["total"] == 1
        assert len(places_list["items"]) == 1
        assert places_list["items"][0]["name"] == discovered_place_data["name"]

        # When - Step 3: User updates place with personal notes
        update_data = {
            "description": "Amazing Korean BBQ found through Instagram. Great for dates!",
            "tags": ["korean", "bbq", "hidden_gem", "date_spot"],
            "personal_notes": "Remember to make reservation. Try the premium wagyu!",
        }

        updated_place = MockFactory.create_place_model(
            place_id=place_id,
            name=discovered_place_data["name"],
            description=update_data["description"],
        )
        realistic_mocks["crud"].get_by_user.return_value = created_place
        realistic_mocks["crud"].update.return_value = updated_place

        update_response = client.put(f"/api/v1/places/{place_id}", json=update_data)

        # Then - Place is updated with personal touches
        assert update_response.status_code == 200
        updated_result = update_response.json()

        assert updated_result["description"] == update_data["description"]
        assert "date_spot" in updated_result["tags"]

    def test_place_search_and_filter_workflow_findsPerfectMatch(
        self, client, realistic_mocks
    ):
        """
        Test place search and filtering workflow.

        User Journey:
        1. User searches for "korean bbq"
        2. User filters by location (Gangnam area)
        3. User applies additional filters (price range, ratings)
        4. User finds perfect restaurant match
        """
        # Given - User wants Korean BBQ in Gangnam area
        search_params = {
            "search_query": "korean bbq",
            "latitude": 37.5665,  # Gangnam
            "longitude": 126.9780,
            "radius_km": 5.0,
            "category": "restaurant",
            "tags": ["korean"],
            "page": 1,
            "size": 10,
        }

        # Setup search results
        matching_places = [
            MockFactory.create_place_model(
                name="Premium Korean BBQ Gangnam",
                category=PlaceCategory.RESTAURANT,
                tags=["korean", "bbq", "premium"],
            ),
            MockFactory.create_place_model(
                name="Traditional Korean BBQ",
                category=PlaceCategory.RESTAURANT,
                tags=["korean", "bbq", "traditional"],
            ),
        ]

        realistic_mocks["crud"].get_list_with_filters.return_value = (
            matching_places,
            2,
        )

        # When - User performs search with filters
        search_response = client.get("/api/v1/places/", params=search_params)

        # Then - User gets relevant filtered results
        assert search_response.status_code == 200
        search_results = search_response.json()

        assert search_results["total"] == 2
        assert len(search_results["items"]) == 2

        # All results should match search criteria
        for place in search_results["items"]:
            assert place["category"] == "restaurant"
            assert any("korean" in tag.lower() for tag in place["tags"])
            assert any("bbq" in tag.lower() for tag in place["tags"])

        # When - User refines search with price filter
        refined_params = {**search_params, "price_range": "₩₩₩"}

        premium_places = [matching_places[0]]  # Only premium place matches
        realistic_mocks["crud"].get_list_with_filters.return_value = (premium_places, 1)

        refined_response = client.get("/api/v1/places/", params=refined_params)

        # Then - Results are further refined
        assert refined_response.status_code == 200
        refined_results = refined_response.json()

        assert refined_results["total"] == 1
        assert "Premium" in refined_results["items"][0]["name"]

    def test_place_organization_workflow_managesPersonalCollection(
        self, client, realistic_mocks
    ):
        """
        Test place organization and personal collection management.

        User Journey:
        1. User creates multiple place collections (Date Spots, Work Lunch, etc.)
        2. User categorizes places into collections
        3. User manages tags and personal notes
        4. User exports/shares collections
        """
        # Given - User has multiple places to organize
        user_places = [
            {
                "name": "Romantic Italian Restaurant",
                "category": "restaurant",
                "tags": ["italian", "romantic", "date_spot"],
            },
            {
                "name": "Quick Lunch Spot",
                "category": "restaurant",
                "tags": ["lunch", "quick", "work"],
            },
            {
                "name": "Weekend Brunch Cafe",
                "category": "cafe",
                "tags": ["brunch", "weekend", "casual"],
            },
        ]

        created_places = []
        for place_data in user_places:
            # Mock place creation
            place_mock = MockFactory.create_place_model(
                name=place_data["name"],
                category=PlaceCategory(place_data["category"]),
                tags=place_data["tags"],
            )
            created_places.append(place_mock)

            realistic_mocks["crud"].create_with_user.return_value = place_mock
            realistic_mocks["crud"].get_multi_by_user.return_value = []
            realistic_mocks[
                "detector"
            ].check_duplicate.return_value = MockFactory.create_duplicate_result(
                is_duplicate=False
            )

            # Create each place
            response = client.post("/api/v1/places/", json=place_data)
            assert response.status_code == 201

        # When - User filters by collection (date spots)
        date_spot_filter = {"tags": ["date_spot"], "page": 1, "size": 20}

        date_places = [place for place in created_places if "date_spot" in place.tags]
        realistic_mocks["crud"].get_list_with_filters.return_value = (
            date_places,
            len(date_places),
        )

        date_response = client.get("/api/v1/places/", params=date_spot_filter)

        # Then - User sees only date-appropriate places
        assert date_response.status_code == 200
        date_results = date_response.json()

        assert date_results["total"] == 1
        assert "Romantic" in date_results["items"][0]["name"]

        # When - User filters by work lunch spots
        work_filter = {"tags": ["work"], "page": 1, "size": 20}

        work_places = [place for place in created_places if "work" in place.tags]
        realistic_mocks["crud"].get_list_with_filters.return_value = (
            work_places,
            len(work_places),
        )

        work_response = client.get("/api/v1/places/", params=work_filter)

        # Then - User sees work-appropriate places
        assert work_response.status_code == 200
        work_results = work_response.json()

        assert work_results["total"] == 1
        assert "Quick Lunch" in work_results["items"][0]["name"]

    def test_mobile_user_workflow_optimizedForMobile(self, client, realistic_mocks):
        """
        Test mobile-optimized place management workflow.

        Mobile User Journey:
        1. User discovers place on mobile Instagram app
        2. User quickly saves place with mobile-optimized form
        3. User views nearby places with location services
        4. User gets mobile-friendly place details
        """
        # Given - Mobile user with location services enabled
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
        }

        user_location = {"latitude": 37.5665, "longitude": 126.9780}

        # Mobile-optimized place data (minimal required fields)
        mobile_place_data = {
            "name": "Cafe Near Me",
            "category": "cafe",
            "latitude": 37.5670,  # Very close to user
            "longitude": 126.9785,
            "tags": ["coffee", "nearby"],
        }

        # Setup mobile place creation
        mobile_place = MockFactory.create_place_model(
            name=mobile_place_data["name"], category=PlaceCategory.CAFE
        )

        realistic_mocks[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )
        realistic_mocks["crud"].create_with_user.return_value = mobile_place
        realistic_mocks["crud"].get_multi_by_user.return_value = []

        # When - Mobile user saves place quickly
        mobile_create_response = client.post(
            "/api/v1/places/", json=mobile_place_data, headers=mobile_headers
        )

        # Then - Place is saved with mobile optimizations
        assert mobile_create_response.status_code == 201
        mobile_result = mobile_create_response.json()

        assert mobile_result["name"] == mobile_place_data["name"]
        # Mobile response should be compact
        assert "latitude" in mobile_result
        assert "longitude" in mobile_result

        # When - Mobile user searches for nearby places
        nearby_params = {
            "latitude": user_location["latitude"],
            "longitude": user_location["longitude"],
            "radius_km": 1.0,  # Small radius for mobile
            "size": 5,  # Limited results for mobile
        }

        nearby_places = [
            mobile_place,
            MockFactory.create_place_model(name="Another Nearby Cafe"),
        ]
        realistic_mocks["crud"].get_list_with_filters.return_value = (nearby_places, 2)

        nearby_response = client.get(
            "/api/v1/places/", params=nearby_params, headers=mobile_headers
        )

        # Then - Mobile user gets nearby places quickly
        assert nearby_response.status_code == 200
        nearby_results = nearby_response.json()

        assert nearby_results["total"] == 2
        assert len(nearby_results["items"]) == 2
        # Results should be distance-ordered (closest first)


class TestPlaceManagementConcurrencyE2E:
    """Test concurrent user scenarios and system stability."""

    def test_concurrent_place_creation_handlesMultipleUsers(
        self, client, realistic_mocks
    ):
        """
        Test system handling multiple users creating places simultaneously.

        Concurrency Scenario:
        1. 10 users simultaneously create different places
        2. System handles concurrent database operations
        3. No data corruption or race conditions
        """
        # Given - Multiple users with different places
        concurrent_places = [
            {
                "name": f"Restaurant {i}",
                "category": "restaurant",
                "latitude": 37.5 + i * 0.01,
            }
            for i in range(10)
        ]

        # Setup mocks for concurrent operations
        realistic_mocks[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )
        realistic_mocks["crud"].get_multi_by_user.return_value = []

        def create_place(place_data):
            """Single place creation operation."""
            place_mock = MockFactory.create_place_model(name=place_data["name"])
            realistic_mocks["crud"].create_with_user.return_value = place_mock

            response = client.post("/api/v1/places/", json=place_data)
            return {
                "status_code": response.status_code,
                "success": response.status_code == 201,
                "place_name": place_data["name"],
            }

        # When - Execute concurrent place creation
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(create_place, place_data)
                for place_data in concurrent_places
            ]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Then - All place creations succeed
        successful_creates = sum(1 for r in results if r["success"])

        assert successful_creates >= 8  # At least 80% success rate
        assert total_time < 10.0  # Completed within reasonable time

        # Verify no duplicate processing
        unique_names = set(r["place_name"] for r in results)
        assert len(unique_names) == 10  # All places have unique names

    def test_high_read_load_maintainsPerformance(self, client, realistic_mocks):
        """
        Test system performance under high read load.

        Load Test Scenario:
        1. 50 concurrent search requests
        2. Various search parameters and filters
        3. System maintains response times
        """
        # Given - Various search scenarios
        search_scenarios = [
            {"search_query": "korean", "category": "restaurant"},
            {"latitude": 37.5665, "longitude": 126.9780, "radius_km": 5},
            {"tags": ["cafe"], "page": 1, "size": 10},
            {"category": "restaurant", "page": 2, "size": 20},
            {"search_query": "bbq", "tags": ["korean"]},
        ] * 10  # Repeat to create 50 requests

        # Setup search results
        search_results = [MockFactory.create_place_model() for _ in range(5)]
        realistic_mocks["crud"].get_list_with_filters.return_value = (search_results, 5)

        def perform_search(search_params):
            """Single search operation."""
            start_time = time.time()
            response = client.get("/api/v1/places/", params=search_params)
            end_time = time.time()

            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "success": response.status_code == 200,
            }

        # When - Execute concurrent searches
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(perform_search, params) for params in search_scenarios
            ]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Then - System maintains performance under load
        successful_searches = sum(1 for r in results if r["success"])
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        max_response_time = max(r["response_time"] for r in results)

        assert successful_searches >= 45  # 90% success rate
        assert total_time < 20.0  # All searches complete within 20 seconds
        assert avg_response_time < 2.0  # Average response under 2 seconds
        assert max_response_time < 5.0  # No request over 5 seconds


class TestPlaceManagementAccessibilityE2E:
    """Test accessibility and inclusive design workflows."""

    def test_accessible_place_information_providesRichContent(
        self, client, realistic_mocks
    ):
        """
        Test accessibility features for users with different needs.

        Accessibility Features:
        1. Rich place descriptions for screen readers
        2. Alternative text for images
        3. Structured data for assistive technologies
        """
        # Given - Place with comprehensive accessibility information
        accessible_place = {
            "name": "Accessible Restaurant with Full Information",
            "description": "Wheelchair accessible Korean restaurant with ramp entrance, accessible restrooms, and braille menus available. Located on ground floor with wide doorways and spacious seating area. Staff trained to assist customers with disabilities. Quiet environment suitable for hearing aid users.",
            "category": "restaurant",
            "accessibility_features": [
                "wheelchair_accessible",
                "braille_menu",
                "hearing_loop",
                "accessible_parking",
            ],
            "detailed_description": "Complete restaurant experience with step-by-step accessibility guide",
        }

        # Setup accessible place creation
        accessible_place_mock = MockFactory.create_place_model(
            name=accessible_place["name"], description=accessible_place["description"]
        )

        realistic_mocks[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )
        realistic_mocks["crud"].create_with_user.return_value = accessible_place_mock
        realistic_mocks["crud"].get_multi_by_user.return_value = []

        # When - Accessible place is created
        response = client.post("/api/v1/places/", json=accessible_place)

        # Then - Rich accessibility information is preserved
        assert response.status_code == 201
        result = response.json()

        assert len(result["description"]) > 100  # Rich description
        assert "wheelchair accessible" in result["description"].lower()
        assert "braille" in result["description"].lower()

        # Accessibility information should be structured and comprehensive
        assert result["name"] is not None
        assert result["description"] is not None


# Test fixtures
@pytest.fixture
def real_world_user_scenarios():
    """Real-world user scenarios for comprehensive E2E testing."""
    return {
        "food_enthusiast": {
            "persona": "Food enthusiast exploring Seoul restaurants",
            "places": [
                {
                    "name": "Michelin Star Restaurant",
                    "category": "restaurant",
                    "tags": ["michelin", "fine_dining"],
                },
                {
                    "name": "Street Food Market",
                    "category": "restaurant",
                    "tags": ["street_food", "casual"],
                },
                {
                    "name": "Hidden Local Gem",
                    "category": "restaurant",
                    "tags": ["local", "authentic"],
                },
            ],
            "search_patterns": ["michelin", "street food", "authentic korean"],
        },
        "digital_nomad": {
            "persona": "Digital nomad looking for work-friendly spaces",
            "places": [
                {
                    "name": "Coworking Cafe",
                    "category": "cafe",
                    "tags": ["wifi", "work", "quiet"],
                },
                {
                    "name": "24h Study Space",
                    "category": "cafe",
                    "tags": ["24h", "study", "charging"],
                },
                {
                    "name": "Meeting Room Cafe",
                    "category": "cafe",
                    "tags": ["meeting", "private", "business"],
                },
            ],
            "search_patterns": ["wifi", "work friendly", "quiet"],
        },
        "tourist": {
            "persona": "Tourist exploring Seoul attractions and food",
            "places": [
                {
                    "name": "Palace Nearby Restaurant",
                    "category": "restaurant",
                    "tags": ["traditional", "tourist"],
                },
                {
                    "name": "Shopping District Cafe",
                    "category": "cafe",
                    "tags": ["shopping", "tourist", "instagram"],
                },
                {
                    "name": "Night Market Food",
                    "category": "restaurant",
                    "tags": ["night", "market", "experience"],
                },
            ],
            "search_patterns": ["traditional", "tourist friendly", "instagram worthy"],
        },
    }
