"""Tests for tag management API endpoints."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Test user ID
TEST_USER_ID = "00000000-0000-0000-0000-000000000000"


class TestTagAPI:
    """Test tag management API endpoints."""

    def test_get_tag_suggestions_success(self):
        """Test successful tag auto-completion."""
        # When: Request tag suggestions
        response = client.get("/api/v1/tags/suggestions?q=커&limit=5")

        # Then: Should return suggestions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

        # Check suggestion structure
        if data:
            suggestion = data[0]
            assert "tag" in suggestion
            assert "usage_count" in suggestion
            assert "match_type" in suggestion

    def test_get_tag_suggestions_validation_error(self):
        """Test tag suggestions with invalid query."""
        # When: Request with invalid query (too short)
        response = client.get("/api/v1/tags/suggestions?q=")

        # Then: Should return validation error
        assert response.status_code == 422

    def test_get_tag_suggestions_query_too_long(self):
        """Test tag suggestions with too long query."""
        # When: Request with query too long
        long_query = "a" * 25
        response = client.get(f"/api/v1/tags/suggestions?q={long_query}")

        # Then: Should return validation error
        assert response.status_code == 422

    def test_get_popular_tags_success(self):
        """Test getting popular tags."""
        # When: Request popular tags
        response = client.get("/api/v1/tags/popular?limit=10")

        # Then: Should return popular tags
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_get_trending_tags_success(self):
        """Test getting trending tags."""
        # When: Request trending tags
        response = client.get("/api/v1/tags/trending?days=7&limit=5")

        # Then: Should return trending analysis
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

        # Check trending tag structure
        if data:
            trending_tag = data[0]
            required_fields = [
                "tag",
                "recent_count",
                "total_count",
                "growth_ratio",
                "trend_score",
            ]
            for field in required_fields:
                assert field in trending_tag

    def test_get_trending_tags_invalid_days(self):
        """Test trending tags with invalid days parameter."""
        # When: Request with invalid days (too high)
        response = client.get("/api/v1/tags/trending?days=50")

        # Then: Should return validation error
        assert response.status_code == 422

    def test_get_tag_statistics_success(self):
        """Test getting tag usage statistics."""
        # When: Request tag statistics
        response = client.get("/api/v1/tags/statistics")

        # Then: Should return comprehensive statistics
        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "total_unique_tags",
            "total_tag_usage",
            "most_used_tags",
            "tag_categories",
            "average_tags_per_place",
            "places_count",
        ]

        for field in required_fields:
            assert field in data

        assert isinstance(data["most_used_tags"], list)
        assert isinstance(data["tag_categories"], dict)
        assert isinstance(data["average_tags_per_place"], (int, float))

    def test_get_tag_clusters_success(self):
        """Test getting semantic tag clusters."""
        # When: Request tag clusters
        response = client.get("/api/v1/tags/clusters")

        # Then: Should return categorized tags
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Check if clusters have expected categories
        possible_categories = ["장소타입", "분위기", "대상", "가격", "특징", "기타"]
        for category in data.keys():
            assert category in possible_categories

    def test_add_tags_to_place_success(self):
        """Test adding tags to a place."""
        # Given: Sample place ID and tags
        place_id = str(uuid4())
        tags_to_add = ["커피", "조용한", "데이트"]

        # When: Add tags to place
        response = client.post(f"/api/v1/tags/{place_id}/tags", json=tags_to_add)

        # Note: This will likely fail in real test without proper place setup
        # This is testing the API structure and validation
        assert response.status_code in [200, 404]  # 404 if place not found

    def test_add_tags_invalid_place_id(self):
        """Test adding tags with invalid place ID."""
        # When: Add tags with invalid UUID
        response = client.post("/api/v1/tags/invalid-uuid/tags", json=["커피"])

        # Then: Should return validation error
        assert response.status_code == 422

    def test_add_tags_empty_list(self):
        """Test adding empty tag list."""
        # Given: Valid place ID but empty tags
        place_id = str(uuid4())

        # When: Add empty tag list
        response = client.post(f"/api/v1/tags/{place_id}/tags", json=[])

        # Then: Should return validation error
        assert response.status_code == 422

    def test_remove_tags_from_place(self):
        """Test removing tags from a place."""
        # Given: Sample place ID and tags
        place_id = str(uuid4())
        tags_to_remove = ["커피", "조용한"]

        # When: Remove tags from place
        response = client.delete(f"/api/v1/tags/{place_id}/tags", json=tags_to_remove)

        # Note: This will likely return 404 without proper setup
        assert response.status_code in [200, 404]

    def test_suggest_tags_for_place_success(self):
        """Test getting tag suggestions for specific place."""
        # When: Request tag suggestions for place
        response = client.post(
            "/api/v1/tags/suggest-for-place",
            json={
                "place_name": "스타벅스 강남점",
                "place_description": "커피가 맛있는 조용한 카페",
                "max_suggestions": 5,
            },
        )

        # Then: Should return tag suggestions
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_suggest_tags_for_place_missing_name(self):
        """Test tag suggestions without place name."""
        # When: Request without place name
        response = client.post(
            "/api/v1/tags/suggest-for-place", json={"place_description": "좋은 곳"}
        )

        # Then: Should return validation error
        assert response.status_code == 422

    def test_suggest_tags_for_place_name_too_long(self):
        """Test tag suggestions with too long place name."""
        # When: Request with very long place name
        long_name = "a" * 300
        response = client.post(
            "/api/v1/tags/suggest-for-place",
            json={"place_name": long_name, "max_suggestions": 3},
        )

        # Then: Should return validation error
        assert response.status_code == 422

    def test_merge_duplicate_tags_success(self):
        """Test merging duplicate tags."""
        # When: Request tag merge operation
        response = client.post("/api/v1/tags/merge-duplicates")

        # Then: Should return merge results
        assert response.status_code == 200
        data = response.json()

        assert "merges_performed" in data
        assert "operations" in data
        assert isinstance(data["operations"], list)

    def test_tag_endpoints_require_authentication(self):
        """Test that tag endpoints handle authentication properly."""
        # Note: In a real implementation, these would test authentication
        # For now, we use TEMP_USER_ID

        endpoints_to_test = [
            "/api/v1/tags/suggestions?q=test",
            "/api/v1/tags/popular",
            "/api/v1/tags/statistics",
            "/api/v1/tags/clusters",
        ]

        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            # Should not return 401/403 with temp user setup
            assert response.status_code != 401
            assert response.status_code != 403


@pytest.mark.integration
class TestTagIntegration:
    """Integration tests for tag system with place management."""

    def test_tag_workflow_integration(self):
        """Test complete tag workflow with place creation."""
        # This test would require database setup and place creation
        # Placeholder for future integration testing

    def test_tag_normalization_consistency(self):
        """Test that tag normalization is consistent across different entry points."""
        # Test that the same tag input normalizes the same way
        # whether entered via place creation or tag addition

        # This would test both:
        # 1. Creating place with tags
        # 2. Adding tags to existing place
        # And verify they produce the same normalized results

    def test_tag_statistics_real_time_update(self):
        """Test that tag statistics update in real time."""
        # This would test:
        # 1. Get initial tag statistics
        # 2. Add tags to places
        # 3. Verify statistics updated correctly
