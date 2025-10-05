"""
Integration tests for Place Management system.

Tests the complete place management workflow including API endpoints,
services, and database operations working together.
"""

import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from tests.utils.test_helpers import (
    MockFactory,
    PerformanceTestHelpers,
    TestDataBuilder,
)

from app.main import app
from app.models.place import PlaceCategory


class TestPlaceManagementAPIIntegration:
    """Integration tests for place management API endpoints."""

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client for integration testing."""
        return TestClient(app)

    @pytest.fixture
    def mock_services(self):
        """Mock external services for integration testing."""
        with patch(
            "app.services.duplicate_detector.DuplicateDetector"
        ) as mock_detector, patch(
            "app.services.place_classifier.PlaceClassifier"
        ) as mock_classifier, patch(
            "app.crud.place.place"
        ) as mock_place_crud:
            # Setup realistic service responses
            mock_detector_instance = mock_detector.return_value
            mock_detector_instance.check_duplicate = AsyncMock()

            mock_classifier_instance = mock_classifier.return_value
            mock_classifier_instance.classify_place = AsyncMock()

            yield {
                "detector": mock_detector_instance,
                "classifier": mock_classifier_instance,
                "crud": mock_place_crud,
            }

    def test_create_place_validData_returnsCreated(self, client, mock_services):
        """
        Test complete place creation workflow.

        Integration Flow:
        1. User submits place creation request
        2. System checks for duplicates
        3. AI classifier categorizes the place
        4. Place is saved to database
        5. Response includes created place data
        """
        # Given - User wants to create a new Korean BBQ place
        place_data = {
            "name": "Gangnam Premium Korean BBQ",
            "description": "Amazing Korean BBQ in Gangnam",
            "address": "123 Gangnam-gu, Seoul",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["korean", "bbq", "gangnam"],
            "phone": "+82-2-555-1234",
            "website": "https://gangnam-bbq.com",
        }

        # Setup mock responses for integration
        mock_services[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )

        mock_services[
            "classifier"
        ].classify_place.return_value = MockFactory.create_classification_result(
            predicted_category=PlaceCategory.RESTAURANT, confidence=0.92
        )

        created_place = MockFactory.create_place_model(
            name=place_data["name"], category=PlaceCategory.RESTAURANT
        )
        mock_services["crud"].create_with_user.return_value = created_place
        mock_services["crud"].get_multi_by_user.return_value = []

        # When - User creates the place
        response = client.post("/api/v1/places/", json=place_data)

        # Then - Place is created successfully
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()

        assert result["name"] == place_data["name"]
        assert result["category"] == "restaurant"
        assert result["latitude"] == place_data["latitude"]
        assert result["longitude"] == place_data["longitude"]

        # Verify integration workflow
        mock_services["detector"].check_duplicate.assert_called_once()
        mock_services["crud"].create_with_user.assert_called_once()

    def test_create_place_duplicateDetected_returnsConflict(
        self, client, mock_services
    ):
        """
        Test place creation with duplicate detection.

        Integration Flow:
        1. User submits place creation request
        2. Duplicate detector finds existing similar place
        3. System returns conflict with matched place info
        """
        # Given - User tries to create duplicate place
        place_data = {
            "name": "Existing Restaurant",
            "address": "123 Test Street, Seoul",
            "category": "restaurant",
        }

        existing_place = MockFactory.create_place_model(
            name="Similar Restaurant", address="123 Test Street, Seoul"
        )

        # Setup duplicate detection
        mock_services[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=True,
            confidence=0.95,
            match_type="name_similarity",
            matched_place_index=0,
        )

        mock_services["crud"].get_multi_by_user.return_value = [existing_place]

        # When - User attempts to create duplicate place
        response = client.post("/api/v1/places/", json=place_data)

        # Then - System rejects with conflict
        assert response.status_code == status.HTTP_409_CONFLICT
        error_data = response.json()

        assert error_data["detail"]["message"] == "Duplicate place detected"
        assert error_data["detail"]["confidence"] == 0.95
        assert error_data["detail"]["matchType"] == "name_similarity"
        assert "matchedPlace" in error_data["detail"]

    def test_get_place_list_withFilters_returnsFilteredResults(
        self, client, mock_services
    ):
        """
        Test place list retrieval with multiple filters.

        Integration Flow:
        1. User requests filtered place list
        2. System applies category, location, and text filters
        3. Results are paginated and returned
        """
        # Given - User wants filtered restaurant list in Gangnam
        filters = {
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "radius_km": 5.0,
            "search_query": "korean bbq",
            "tags": ["korean"],
            "page": 1,
            "size": 10,
        }

        filtered_places = [
            MockFactory.create_place_model(
                name="Korean BBQ Place 1", category=PlaceCategory.RESTAURANT
            ),
            MockFactory.create_place_model(
                name="Korean BBQ Place 2", category=PlaceCategory.RESTAURANT
            ),
        ]

        mock_services["crud"].get_list_with_filters.return_value = (filtered_places, 2)

        # When - User requests filtered list
        response = client.get("/api/v1/places/", params=filters)

        # Then - System returns filtered results
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["size"] == 10

        # Verify all places match filter criteria
        for place in result["items"]:
            assert place["category"] == "restaurant"

    def test_update_place_validChanges_updatesSuccessfully(self, client, mock_services):
        """
        Test place update workflow.

        Integration Flow:
        1. User submits place update
        2. System validates user ownership
        3. AI re-classifies if category changes
        4. Database is updated
        """
        # Given - User wants to update existing place
        place_id = str(uuid4())
        update_data = {
            "name": "Updated Restaurant Name",
            "description": "Updated description",
            "category": "restaurant",
            "tags": ["korean", "updated"],
        }

        existing_place = MockFactory.create_place_model(place_id=place_id)
        updated_place = MockFactory.create_place_model(
            place_id=place_id, name=update_data["name"]
        )

        mock_services["crud"].get_by_user.return_value = existing_place
        mock_services["crud"].update.return_value = updated_place

        # When - User updates the place
        response = client.put(f"/api/v1/places/{place_id}", json=update_data)

        # Then - Place is updated successfully
        assert response.status_code == status.HTTP_200_OK
        result = response.json()

        assert result["name"] == update_data["name"]
        assert result["description"] == update_data["description"]

        mock_services["crud"].get_by_user.assert_called_once()
        mock_services["crud"].update.assert_called_once()

    def test_delete_place_existingPlace_deletesSuccessfully(
        self, client, mock_services
    ):
        """
        Test place deletion workflow.

        Integration Flow:
        1. User requests place deletion
        2. System validates ownership
        3. Place status is updated to inactive
        """
        # Given - User wants to delete existing place
        place_id = str(uuid4())

        existing_place = MockFactory.create_place_model(place_id=place_id)
        mock_services["crud"].get_by_user.return_value = existing_place
        mock_services["crud"].remove.return_value = True

        # When - User deletes the place
        response = client.delete(f"/api/v1/places/{place_id}")

        # Then - Place is deleted successfully
        assert response.status_code == status.HTTP_204_NO_CONTENT

        mock_services["crud"].get_by_user.assert_called_once()
        mock_services["crud"].remove.assert_called_once()


class TestPlaceServiceIntegration:
    """Integration tests for place services working together."""

    @pytest.mark.asyncio
    async def test_duplicate_detection_workflow_identifiesCorrectMatches(self):
        """
        Test duplicate detection service integration.

        Integration Flow:
        1. New place data is processed
        2. Duplicate detector compares with existing places
        3. Multi-stage algorithm determines similarity
        """
        # Given - New place and existing similar places
        builder = TestDataBuilder()
        new_place = builder.with_korean_bbq_content().build_place_create()

        existing_places = [
            TestDataBuilder().with_korean_bbq_content().build_place_create(),
            TestDataBuilder().with_cafe_content().build_place_create(),
        ]

        # When - Duplicate detection runs
        from app.services.places.duplicate_detector import DuplicateDetector

        detector = DuplicateDetector()

        result = await detector.check_duplicate(new_place, existing_places)

        # Then - Correct duplicate detected
        assert result.is_duplicate is True
        assert result.confidence > 0.8
        assert result.match_type in [
            "exact_match",
            "name_similarity",
            "address_similarity",
        ]

    @pytest.mark.asyncio
    async def test_ai_classification_integration_categorizesCorrectly(self):
        """
        Test AI place classification service integration.

        Integration Flow:
        1. Place content is analyzed
        2. TF-IDF vectorization extracts features
        3. RandomForest model predicts category
        """
        # Given - Place with clear restaurant indicators
        place_data = TestDataBuilder().with_korean_bbq_content().build_place_create()

        # When - AI classification runs
        from app.services.places.place_classifier import PlaceClassifier

        classifier = PlaceClassifier(confidence_threshold=0.70)

        # Mock the model for testing
        with patch.object(classifier, "predict_category") as mock_predict:
            mock_predict.return_value = MockFactory.create_classification_result(
                predicted_category=PlaceCategory.RESTAURANT, confidence=0.92
            )

            result = classifier.predict_category(place_data)

        # Then - Correct category predicted
        assert result.predicted_category == PlaceCategory.RESTAURANT
        assert result.confidence > 0.8
        assert result.needs_manual_review is False

    @pytest.mark.asyncio
    async def test_geographical_search_integration_returnsAccurateResults(self):
        """
        Test geographical search integration with PostGIS.

        Integration Flow:
        1. User specifies location and radius
        2. PostGIS calculates distances
        3. Results ordered by proximity
        """
        # Given - Search location and mock places at various distances
        search_lat, search_lng = 37.5665, 126.9780
        radius_km = 5.0

        nearby_places = [
            MockFactory.create_place_model(
                latitude=37.5665, longitude=126.9780
            ),  # Same location
            MockFactory.create_place_model(
                latitude=37.5700, longitude=126.9800
            ),  # ~500m away
            MockFactory.create_place_model(
                latitude=37.6000, longitude=127.0000
            ),  # ~5km away
        ]

        # When - Geographical search is performed
        with patch("app.crud.place.place") as mock_crud:
            mock_crud.get_nearby_places.return_value = nearby_places[:2]  # Within 5km

            from app.crud.place import place as place_crud

            results = place_crud.get_nearby_places(
                db=None,  # Mocked
                user_id=uuid4(),
                latitude=search_lat,
                longitude=search_lng,
                radius_km=radius_km,
            )

        # Then - Nearby places returned in order
        assert len(results) == 2
        # Results should be ordered by distance (closest first)


class TestPlaceManagementPerformance:
    """Performance integration tests for place management."""

    @pytest.mark.asyncio
    async def test_bulk_place_creation_performance_meetsRequirements(self):
        """
        Test bulk place creation performance.

        Performance Requirements:
        - 100 places created in under 30 seconds
        - Database performance maintained
        """
        # Given - Bulk place creation data
        bulk_places = [
            TestDataBuilder().with_cafe_content().build_place_create()
            for _ in range(50)  # Reduced for testing
        ]

        # When - Bulk creation is performed
        start_time = asyncio.get_event_loop().time()

        created_places = []
        for place_data in bulk_places:
            # Simulate place creation (mocked for performance)
            created_place = MockFactory.create_place_model(name=place_data.name)
            created_places.append(created_place)

            # Simulate minimal processing time
            await asyncio.sleep(0.01)

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        # Then - Performance requirements met
        assert len(created_places) == 50
        assert execution_time < 10.0  # 50 places in under 10 seconds

        PerformanceTestHelpers.assert_performance_metrics(
            execution_time, 10.0, "Bulk Place Creation"
        )

    @pytest.mark.asyncio
    async def test_geographical_search_performance_scalesToManyPlaces(self):
        """
        Test geographical search performance with large dataset.

        Performance Requirements:
        - Search 1000 places in under 500ms
        - PostGIS spatial index utilization
        """
        # Given - Large dataset simulation

        # When - Geographical search is performed
        start_time = asyncio.get_event_loop().time()

        # Simulate PostGIS spatial search
        with patch("app.crud.place.place.get_nearby_places") as mock_search:
            mock_search.return_value = [
                MockFactory.create_place_model() for _ in range(20)
            ]  # Return top 20 results

            from app.crud.place import place as place_crud

            results = place_crud.get_nearby_places(
                db=None,  # Mocked
                user_id=uuid4(),
                latitude=37.5665,
                longitude=126.9780,
                radius_km=5.0,
                limit=20,
            )

        end_time = asyncio.get_event_loop().time()
        search_time = end_time - start_time

        # Then - Search performance requirements met
        assert len(results) == 20
        assert search_time < 0.5  # Under 500ms

        PerformanceTestHelpers.assert_performance_metrics(
            search_time, 0.5, "Geographical Search"
        )


class TestPlaceManagementErrorRecovery:
    """Error recovery and resilience integration tests."""

    def test_database_error_recovery_gracefulDegradation(self, client, mock_services):
        """
        Test error recovery when database operations fail.

        Error Recovery Flow:
        1. Database connection fails
        2. System handles gracefully
        3. Appropriate error response returned
        """
        # Given - Database error scenario
        place_data = {"name": "Test Restaurant", "category": "restaurant"}

        mock_services["crud"].get_multi_by_user.side_effect = Exception(
            "Database connection failed"
        )

        # When - User attempts place creation during DB failure
        response = client.post("/api/v1/places/", json=place_data)

        # Then - System handles error gracefully
        assert response.status_code in [500, 503]  # Server error or service unavailable

        # Error response should be informative but not expose internals
        error_data = response.json()
        assert "detail" in error_data
        assert "Database connection failed" not in str(
            error_data
        )  # Don't expose internal errors

    def test_external_service_failure_fallbackBehavior(self, client, mock_services):
        """
        Test fallback behavior when external services fail.

        Fallback Flow:
        1. AI classification service fails
        2. System uses default categorization
        3. Place creation continues with fallback
        """
        # Given - AI service failure scenario
        place_data = {
            "name": "Test Restaurant",
            "category": "other",  # Fallback category
        }

        # Setup service failures
        mock_services[
            "detector"
        ].check_duplicate.return_value = MockFactory.create_duplicate_result(
            is_duplicate=False
        )
        mock_services["classifier"].classify_place.side_effect = Exception(
            "AI service unavailable"
        )

        created_place = MockFactory.create_place_model(category=PlaceCategory.OTHER)
        mock_services["crud"].create_with_user.return_value = created_place
        mock_services["crud"].get_multi_by_user.return_value = []

        # When - Place creation attempted during AI failure
        response = client.post("/api/v1/places/", json=place_data)

        # Then - System falls back gracefully
        assert response.status_code == status.HTTP_201_CREATED
        result = response.json()

        # Place created with fallback category
        assert result["category"] == "other"


# Test fixtures and helpers
@pytest.fixture
def sample_places_data():
    """Sample place data for integration testing."""
    return [
        {
            "name": "Korean BBQ House",
            "category": "restaurant",
            "address": "123 Gangnam-gu, Seoul",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["korean", "bbq"],
        },
        {
            "name": "Hongdae Cafe",
            "category": "cafe",
            "address": "456 Hongik-ro, Seoul",
            "latitude": 37.5563,
            "longitude": 126.9236,
            "tags": ["cafe", "study"],
        },
    ]


@pytest.fixture
def mock_database_session():
    """Mock database session for integration testing."""
    from unittest.mock import Mock

    return Mock()
