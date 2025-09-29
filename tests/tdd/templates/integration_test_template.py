"""
Integration Test Template

Integration tests verify that multiple components work together correctly.
They test the interactions between services, databases, and external APIs.

Use this template for testing:
- Service-to-service communication
- Database interactions
- External API integrations
- Message queue operations
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app


class TestServiceIntegration:
    """
    Template for testing service integration.

    Integration tests should:
    1. Test component interactions
    2. Use real database connections (with test data)
    3. Mock only external dependencies (APIs, third-party services)
    4. Verify data flow between services
    """

    @pytest.fixture(scope="class")
    def db_session(self):
        """Create a real database session for integration testing."""
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()

    @pytest.fixture(scope="class")
    def test_client(self):
        """Create FastAPI test client."""
        with TestClient(app) as client:
            yield client

    def setup_method(self):
        """Setup test data before each test."""
        # Create test data in database

    def teardown_method(self):
        """Clean up test data after each test."""
        # Remove test data from database

    def test_create_and_retrieve_place_fullWorkflow_persistsCorrectly(
        self, db_session: Session
    ):
        """
        Test complete workflow: create place → save to DB → retrieve from DB

        This tests the integration between:
        - PlaceService
        - PlaceRepository
        - Database
        """
        # Given
        place_data = {
            "name": "Integration Test Restaurant",
            "address": "123 Test Street, Seoul",
            "category": "restaurant",
            "coordinates": {"lat": 37.5665, "lng": 126.9780},
        }

        # When - Create place through service layer
        place_service = PlaceService(db_session)
        created_place = place_service.create_place(place_data)

        # Then - Verify it was saved and can be retrieved
        assert created_place.id is not None

        # Retrieve from database
        retrieved_place = place_service.get_place_by_id(created_place.id)
        assert retrieved_place is not None
        assert retrieved_place.name == place_data["name"]
        assert retrieved_place.address == place_data["address"]

    @pytest.mark.asyncio
    async def test_link_analysis_to_place_extraction_pipeline_fullIntegration(
        self, db_session: Session
    ):
        """
        Test integration between link analysis and place extraction services.

        Workflow: URL → Content Extraction → AI Analysis → Place Creation
        """
        # Given
        instagram_url = "https://instagram.com/p/test123/"

        # Mock external dependencies only (Instagram API, Google AI)
        with patch(
            "app.services.content_extractor.InstagramExtractor"
        ) as mock_instagram, patch(
            "app.services.ai.gemini_analyzer.GeminiAnalyzer"
        ) as mock_ai:
            # Setup mocks for external services
            mock_instagram.return_value.extract.return_value = {
                "title": "Amazing Korean BBQ",
                "description": "Best BBQ in Gangnam #korean #bbq #restaurant",
                "images": ["https://instagram.com/image1.jpg"],
                "hashtags": ["korean", "bbq", "restaurant"],
            }

            mock_ai.return_value.analyze.return_value = {
                "place_name": "Gangnam Korean BBQ",
                "category": "restaurant",
                "address": "Gangnam-gu, Seoul",
                "confidence": 0.9,
            }

            # When - Execute the full pipeline
            link_analysis_service = LinkAnalysisService(db_session)
            analysis_result = await link_analysis_service.analyze_link(instagram_url)

            # Then - Verify complete integration
            assert analysis_result.success is True
            assert analysis_result.place_info is not None
            assert analysis_result.place_info.name == "Gangnam Korean BBQ"

            # Verify place was created in database
            place_id = analysis_result.place_info.id
            place_service = PlaceService(db_session)
            saved_place = place_service.get_place_by_id(place_id)
            assert saved_place is not None
            assert saved_place.name == "Gangnam Korean BBQ"

    def test_cache_and_database_consistency_cacheHit_returnsSameDataAsDatabase(
        self, db_session: Session
    ):
        """
        Test integration between cache and database layers.

        Verifies that cached data matches database data.
        """
        # Given
        place_data = {
            "name": "Cache Test Restaurant",
            "address": "Cache Test Address",
            "category": "restaurant",
        }

        # When - Create place and cache it
        place_service = PlaceService(db_session)
        cache_service = CacheService()

        created_place = place_service.create_place(place_data)
        cache_service.cache_place(created_place)

        # Then - Verify cache and database have same data
        cached_place = cache_service.get_cached_place(created_place.id)
        db_place = place_service.get_place_by_id(created_place.id)

        assert cached_place.id == db_place.id
        assert cached_place.name == db_place.name
        assert cached_place.address == db_place.address

    @pytest.mark.asyncio
    async def test_notification_and_user_preference_integration_sendsCorrectNotifications(
        self, db_session: Session
    ):
        """
        Test integration between notification service and user preferences.

        Verifies that notifications respect user preferences.
        """
        # Given
        user_id = "test_user_123"

        # Create user with notification preferences
        user_service = UserService(db_session)
        user = user_service.create_user(
            {
                "id": user_id,
                "email": "test@example.com",
                "notification_preferences": {
                    "push_notifications": True,
                    "email_notifications": False,
                    "place_recommendations": True,
                },
            }
        )

        # When - Send notification through service
        notification_service = NotificationService(db_session)

        # Mock external notification delivery
        with patch("app.services.fcm_service.FCMService") as mock_fcm:
            mock_fcm.return_value.send_notification.return_value = {"success": True}

            result = await notification_service.send_place_recommendation(
                user_id=user_id,
                place_data={"name": "New Restaurant", "category": "restaurant"},
            )

        # Then - Verify notification was sent according to preferences
        assert result.success is True
        assert result.channels_used == ["push"]  # Only push, not email

        # Verify notification was logged in database
        notifications = notification_service.get_user_notifications(user_id)
        assert len(notifications) == 1
        assert notifications[0].type == "place_recommendation"


class TestAPIIntegration:
    """Template for testing API endpoint integration."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Authentication headers for protected endpoints."""
        # Create test user and get auth token
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword"},
        )
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_create_place_via_api_validData_returnsCreatedPlace(
        self, client, auth_headers
    ):
        """
        Test complete API workflow for place creation.

        Tests integration of:
        - API endpoint
        - Authentication middleware
        - Request validation
        - Service layer
        - Database persistence
        """
        # Given
        place_data = {
            "name": "API Test Restaurant",
            "address": "API Test Address",
            "category": "restaurant",
            "coordinates": {"lat": 37.5665, "lng": 126.9780},
        }

        # When
        response = client.post("/api/v1/places/", json=place_data, headers=auth_headers)

        # Then
        assert response.status_code == 201
        created_place = response.json()

        assert created_place["name"] == place_data["name"]
        assert created_place["id"] is not None

        # Verify place can be retrieved
        place_id = created_place["id"]
        get_response = client.get(f"/api/v1/places/{place_id}")
        assert get_response.status_code == 200
        retrieved_place = get_response.json()
        assert retrieved_place["name"] == place_data["name"]

    def test_link_analysis_api_fullWorkflow_returnsAnalysisResult(self, client):
        """
        Test complete link analysis API workflow.

        Integration test covering:
        - API request/response
        - Background task processing
        - Service integrations
        - Response formatting
        """
        # Given
        request_data = {
            "url": "https://instagram.com/p/test123/",
            "force_refresh": False,
        }

        # Mock external dependencies
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis:
            # Setup realistic mock responses
            mock_extractor.return_value.extract_content.return_value = Mock(
                url=request_data["url"],
                title="Restaurant Post",
                description="Great food #restaurant",
                platform="instagram",
                success=True,
            )

            mock_analysis.return_value.analyze_content.return_value = Mock(
                success=True,
                place_info=Mock(
                    name="Test Restaurant", category="restaurant", confidence=0.9
                ),
                confidence=0.9,
            )

            # When
            response = client.post("/api/v1/links/analyze", json=request_data)

            # Then
            assert response.status_code == 200
            result = response.json()

            assert result["success"] is True
            assert result["result"]["placeInfo"]["name"] == "Test Restaurant"
            assert result["result"]["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_concurrent_api_requests_handlesLoadCorrectly(self, client):
        """
        Test API integration under concurrent load.

        Verifies that the system handles multiple simultaneous requests correctly.
        """
        from concurrent.futures import ThreadPoolExecutor

        # Given
        request_data = {"url": "https://instagram.com/p/concurrent_test/"}

        def make_request():
            return client.post("/api/v1/links/analyze", json=request_data)

        # When - Make 10 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]

        # Then - All requests should succeed
        assert len(responses) == 10
        for response in responses:
            assert response.status_code in [200, 202]  # 200 for sync, 202 for async


class TestDatabaseIntegration:
    """Template for testing database integration."""

    @pytest.fixture
    def db_session(self):
        """Database session with transaction rollback."""
        session = SessionLocal()

        # Start transaction
        transaction = session.begin()

        try:
            yield session
        finally:
            # Rollback transaction to clean up test data
            transaction.rollback()
            session.close()

    def test_place_crud_operations_fullCycle_maintainsDataIntegrity(self, db_session):
        """
        Test complete CRUD operations for place entity.

        Verifies database integration for:
        - Create
        - Read
        - Update
        - Delete
        """
        # Given
        place_repository = PlaceRepository(db_session)

        place_data = {
            "name": "CRUD Test Restaurant",
            "address": "CRUD Test Address",
            "category": "restaurant",
        }

        # When/Then - Create
        created_place = place_repository.create(place_data)
        assert created_place.id is not None

        # When/Then - Read
        retrieved_place = place_repository.get_by_id(created_place.id)
        assert retrieved_place.name == place_data["name"]

        # When/Then - Update
        updated_data = {"name": "Updated Restaurant Name"}
        updated_place = place_repository.update(created_place.id, updated_data)
        assert updated_place.name == "Updated Restaurant Name"

        # When/Then - Delete
        deleted = place_repository.delete(created_place.id)
        assert deleted is True

        # Verify deletion
        deleted_place = place_repository.get_by_id(created_place.id)
        assert deleted_place is None

    def test_complex_query_integration_returnsCorrectResults(self, db_session):
        """
        Test complex database queries with joins and filters.

        Verifies integration between:
        - Repository layer
        - ORM queries
        - Database indexes
        - Query optimization
        """
        # Given - Create test data
        place_repository = PlaceRepository(db_session)
        UserRepository(db_session)

        # Create test places and users
        places = [
            place_repository.create(
                {
                    "name": f"Restaurant {i}",
                    "category": "restaurant",
                    "rating": 4.0 + (i * 0.1),
                }
            )
            for i in range(5)
        ]

        # When - Execute complex query
        high_rated_restaurants = place_repository.find_places_by_criteria(
            category="restaurant", min_rating=4.3, limit=10
        )

        # Then - Verify results
        assert len(high_rated_restaurants) == 2  # Restaurants 3 and 4
        assert all(place.rating >= 4.3 for place in high_rated_restaurants)
        assert all(place.category == "restaurant" for place in high_rated_restaurants)


# Example service classes (these would be in your actual code)
class PlaceService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.repository = PlaceRepository(db_session)

    def create_place(self, place_data):
        return self.repository.create(place_data)

    def get_place_by_id(self, place_id):
        return self.repository.get_by_id(place_id)


class PlaceRepository:
    def __init__(self, db_session):
        self.db_session = db_session

    def create(self, place_data):
        # Implementation would create database record
        pass

    def get_by_id(self, place_id):
        # Implementation would query database
        pass
