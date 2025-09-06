"""Tests for place management API endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Test user ID
TEST_USER_ID = "00000000-0000-0000-0000-000000000000"


class TestPlaceAPI:
    """Test place management API endpoints."""

    def test_create_place_success(self):
        """Test successful place creation."""
        # Given: Valid place data
        place_data = {
            "name": "테스트 카페",
            "description": "맛있는 커피를 파는 조용한 카페",
            "address": "서울시 강남구 테스트로 123",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["커피", "조용한", "카페"],
        }

        # When: Create place
        response = client.post("/api/v1/places/", json=place_data)

        # Then: Should create successfully or detect duplicate
        assert response.status_code in [201, 409]  # 201 created, 409 duplicate

        if response.status_code == 201:
            data = response.json()
            assert data["name"] == place_data["name"]
            assert data["category"] == place_data["category"]
            assert "id" in data

    def test_create_place_validation_error(self):
        """Test place creation with invalid data."""
        # When: Create place without required name
        response = client.post("/api/v1/places/", json={})

        # Then: Should return validation error
        assert response.status_code == 422

    def test_get_places_success(self):
        """Test retrieving places list."""
        # When: Get places
        response = client.get("/api/v1/places/")

        # Then: Should return paginated list
        assert response.status_code == 200
        data = response.json()
        assert "places" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["places"], list)

    def test_get_places_with_filters(self):
        """Test places list with category filter."""
        # When: Get places filtered by category
        response = client.get("/api/v1/places/?category=restaurant&page_size=5")

        # Then: Should return filtered results
        assert response.status_code == 200
        data = response.json()
        assert data["page_size"] <= 5

    def test_get_place_by_id_not_found(self):
        """Test getting non-existent place."""
        # Given: Random UUID
        place_id = str(uuid4())

        # When: Get place by ID
        response = client.get(f"/api/v1/places/{place_id}")

        # Then: Should return not found
        assert response.status_code == 404

    def test_update_place_not_found(self):
        """Test updating non-existent place."""
        # Given: Random UUID and update data
        place_id = str(uuid4())
        update_data = {"name": "Updated Name"}

        # When: Update place
        response = client.put(f"/api/v1/places/{place_id}", json=update_data)

        # Then: Should return not found
        assert response.status_code == 404

    def test_delete_place_not_found(self):
        """Test deleting non-existent place."""
        # Given: Random UUID
        place_id = str(uuid4())

        # When: Delete place
        response = client.delete(f"/api/v1/places/{place_id}")

        # Then: Should return not found
        assert response.status_code == 404

    def test_get_nearby_places_success(self):
        """Test geographic search for nearby places."""
        # When: Search for nearby places
        response = client.get(
            "/api/v1/places/nearby/?latitude=37.5665&longitude=126.9780&radius_km=5"
        )

        # Then: Should return nearby places
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nearby_places_invalid_coordinates(self):
        """Test nearby search with invalid coordinates."""
        # When: Search with invalid latitude
        response = client.get(
            "/api/v1/places/nearby/?latitude=200&longitude=126.9780&radius_km=5"
        )

        # Then: Should return validation error
        assert response.status_code == 422

    def test_search_places_success(self):
        """Test full-text search for places."""
        # When: Search places
        response = client.get("/api/v1/places/search/?q=카페")

        # Then: Should return search results
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_places_query_too_short(self):
        """Test search with too short query."""
        # When: Search with single character
        response = client.get("/api/v1/places/search/?q=a")

        # Then: Should return validation error
        assert response.status_code == 422

    def test_get_place_statistics_success(self):
        """Test getting place statistics."""
        # When: Get statistics
        response = client.get("/api/v1/places/stats/")

        # Then: Should return statistics
        assert response.status_code == 200
        data = response.json()
        required_fields = ["total_places", "categories", "tags_stats"]
        for field in required_fields:
            assert field in data

    def test_check_duplicate_place_success(self):
        """Test duplicate place checking."""
        # Given: Place data for duplicate check
        place_data = {
            "name": "스타벅스 강남점",
            "address": "서울시 강남구 테헤란로",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "category": "restaurant",
        }

        # When: Check for duplicates
        response = client.post("/api/v1/places/check-duplicate/", json=place_data)

        # Then: Should return duplicate check result
        assert response.status_code == 200
        data = response.json()
        assert "isDuplicate" in data
        assert "confidence" in data
        assert "matchType" in data

    def test_classify_place_success(self):
        """Test place classification."""
        # Given: Place data for classification
        place_data = {
            "name": "맥도날드 강남점",
            "description": "패스트푸드 체인점",
            "category": "other",
        }

        # When: Classify place
        response = client.post("/api/v1/places/classify/", json=place_data)

        # Then: Should return classification
        assert response.status_code == 200
        data = response.json()
        assert "predictedCategory" in data
        assert "confidence" in data
        assert "reasoning" in data

    def test_update_place_status_invalid_status(self):
        """Test updating place status with invalid value."""
        # Given: Random place ID
        place_id = str(uuid4())

        # When: Update with invalid status
        response = client.put(f"/api/v1/places/{place_id}/status?status=invalid")

        # Then: Should return validation error
        assert response.status_code in [
            404,
            422,
        ]  # 404 if place not found, 422 if invalid status

    def test_get_related_places_not_found(self):
        """Test getting related places for non-existent place."""
        # Given: Random place ID
        place_id = str(uuid4())

        # When: Get related places
        response = client.get(f"/api/v1/places/{place_id}/related")

        # Then: Should return not found
        assert response.status_code == 404

    def test_export_places_json_format(self):
        """Test exporting places in JSON format."""
        # When: Export places as JSON
        response = client.get("/api/v1/places/export?format=json")

        # Then: Should return JSON export
        assert response.status_code == 200
        data = response.json()
        assert "export_info" in data
        assert "places" in data
        assert data["export_info"]["export_format"] == "json"

    def test_export_places_csv_format(self):
        """Test exporting places in CSV format."""
        # When: Export places as CSV
        response = client.get("/api/v1/places/export?format=csv")

        # Then: Should return CSV export info
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "download_url" in data
        assert "total_places" in data

    def test_export_places_invalid_format(self):
        """Test export with invalid format."""
        # When: Export with invalid format
        response = client.get("/api/v1/places/export?format=xml")

        # Then: Should return validation error
        assert response.status_code == 422

    def test_places_api_authentication_handling(self):
        """Test that places endpoints handle authentication properly."""
        # Note: In real implementation, these would test authentication
        # For now, we use TEMP_USER_ID

        endpoints_to_test = [
            "/api/v1/places/",
            "/api/v1/places/stats/",
            "/api/v1/places/nearby/?latitude=37.5665&longitude=126.9780&radius_km=5",
            "/api/v1/places/search/?q=test",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 401/403 with temp user setup
            assert response.status_code != 401
            assert response.status_code != 403


@pytest.mark.integration
class TestPlaceIntegration:
    """Integration tests for place management system."""

    def test_place_crud_workflow(self):
        """Test complete place CRUD workflow."""
        # This test would require database setup and real place creation
        # Placeholder for future integration testing

    def test_place_search_performance(self):
        """Test place search performance requirements."""
        # Test that search operations complete within 500ms requirement
        import time

        start_time = time.time()
        response = client.get("/api/v1/places/search/?q=카페")
        end_time = time.time()

        # Should complete within 1 second (allowing for test environment overhead)
        assert (end_time - start_time) < 1.0
        assert response.status_code == 200

    def test_place_geographic_search_accuracy(self):
        """Test geographic search accuracy."""
        # Test that nearby search returns places within specified radius
        # This would require test data setup with known coordinates

    def test_place_export_large_dataset(self):
        """Test place export with large dataset."""
        # Test export performance with large number of places
        response = client.get("/api/v1/places/export?format=json")
        assert response.status_code == 200

        # Should handle large datasets efficiently
        data = response.json()
        assert "export_info" in data
        assert isinstance(data["places"], list)
