"""
Unit tests for course recommendation engine.

TDD approach: Write tests first, then implement the recommendation logic.
"""

from typing import List

import pytest

from app.schemas.place import PlaceCreate
from app.services.course_recommender import CourseRecommender


class TestCourseRecommender:
    """Test course recommendation engine."""

    @pytest.fixture
    def recommender(self):
        """Create course recommender instance."""
        return CourseRecommender()

    @pytest.fixture
    def sample_places(self) -> List[PlaceCreate]:
        """Sample places for testing."""
        return [
            PlaceCreate(
                name="강남 카페",
                address="서울 강남구 강남대로 123",
                latitude=37.4979,
                longitude=127.0276,
                category="cafe",
            ),
            PlaceCreate(
                name="강남 레스토랑",
                address="서울 강남구 테헤란로 456",
                latitude=37.5001,
                longitude=127.0369,
                category="restaurant",
            ),
            PlaceCreate(
                name="코엑스",
                address="서울 강남구 영동대로 513",
                latitude=37.5126,
                longitude=127.0589,
                category="shopping",
            ),
            PlaceCreate(
                name="봉은사",
                address="서울 강남구 봉은사로 531",
                latitude=37.5156,
                longitude=127.0734,
                category="tourist_attraction",
            ),
            PlaceCreate(
                name="잠실 카페",
                address="서울 송파구 올림픽로 240",
                latitude=37.5133,
                longitude=127.1028,
                category="cafe",
            ),
        ]

    def test_courseRecommendation_minimumPlaces_requiresAtLeast3Places(
        self, recommender, sample_places
    ):
        """
        Test: Course recommendation requires minimum 3 places

        Given: Less than 3 places
        When: Requesting course recommendation
        Then: Raises ValueError
        """
        # Given: Only 2 places
        places = sample_places[:2]

        # When & Then: Should raise ValueError
        with pytest.raises(ValueError, match="At least 3 places required"):
            recommender.recommend_course(places)

    def test_courseRecommendation_maximumPlaces_limitsTo6Places(
        self, recommender, sample_places
    ):
        """
        Test: Course recommendation limits to maximum 6 places

        Given: More than 6 places
        When: Requesting course recommendation
        Then: Raises ValueError
        """
        # Given: 7 places (adding duplicates)
        places = sample_places + sample_places[:2]

        # When & Then: Should raise ValueError
        with pytest.raises(ValueError, match="Maximum 6 places allowed"):
            recommender.recommend_course(places)

    def test_courseOptimization_distanceBasedOrder_minimizesTotalDistance(
        self, recommender, sample_places
    ):
        """
        Test: Course optimization minimizes total travel distance

        Given: 5 geographically distributed places in worst order
        When: Course is optimized
        Then: Total distance is at least 30% less than worst order

        RED: This test should initially fail until optimization is implemented
        """
        # Given: 5 places in deliberately worst order (far-to-near zig-zag)
        # Start from far east, then far west, back and forth
        worst_order = [
            sample_places[4],  # 잠실 카페 (가장 동쪽)
            sample_places[0],  # 강남 카페 (가장 서쪽)
            sample_places[3],  # 봉은사 (동쪽)
            sample_places[1],  # 강남 레스토랑 (서쪽)
            sample_places[2],  # 코엑스 (중간)
        ]

        # When: Generate optimized course
        result = recommender.recommend_course(worst_order)

        # Then: Verify optimization
        # Calculate distance of optimized order
        optimized_distance = sum(
            place.travel_distance_km
            for place in result.places
            if place.travel_distance_km
        )

        # Calculate distance of worst order
        worst_distance = self._calculate_total_distance(worst_order)

        # Should be at least 30% improvement over worst order
        improvement = (worst_distance - optimized_distance) / worst_distance
        assert improvement >= 0.30, (
            f"Distance optimization insufficient: {improvement:.1%} improvement "
            f"(expected >= 30%), worst: {worst_distance:.2f}km, optimized: {optimized_distance:.2f}km"
        )

        # Verify result structure
        assert len(result.places) == 5
        assert result.total_distance_km == pytest.approx(optimized_distance, rel=0.01)
        assert result.total_duration_minutes > 0

    def test_categoryDiversity_consecutivePlaces_limitsTo2SameCategory(
        self, recommender, sample_places
    ):
        """
        Test: Category diversity limits consecutive same-category places to 2

        Given: Multiple places with same categories
        When: Course is recommended
        Then: No more than 2 consecutive places of same category

        RED: This test should fail until diversity algorithm is implemented
        """
        # Given: Places with duplicate categories (2 cafes)
        places = sample_places

        # When: Generate course
        result = recommender.recommend_course(places)

        # Then: Check category diversity
        consecutive_same_category = 0
        max_consecutive = 0
        prev_category = None

        for place in result.places:
            if place.category == prev_category:
                consecutive_same_category += 1
                max_consecutive = max(max_consecutive, consecutive_same_category + 1)
            else:
                consecutive_same_category = 0
                prev_category = place.category

        assert max_consecutive <= 2, (
            f"Category diversity violated: {max_consecutive} consecutive places "
            f"of same category (max allowed: 2)"
        )

    def test_courseRecommendation_responseTime_completesWithin10Seconds(
        self, recommender, sample_places
    ):
        """
        Test: Course recommendation completes within 10 seconds

        Given: Standard 5-place course request
        When: Course is recommended
        Then: Response time < 10 seconds
        """
        import time

        # Given: 5 places
        places = sample_places

        # When: Measure recommendation time
        start_time = time.perf_counter()
        result = recommender.recommend_course(places)
        elapsed_time = time.perf_counter() - start_time

        # Then: Should complete within 10 seconds
        assert (
            elapsed_time < 10.0
        ), f"Course recommendation too slow: {elapsed_time:.2f}s (max: 10s)"
        assert result is not None

    def test_travelTimeEstimation_consecutivePlaces_calculatesAccurately(
        self, recommender, sample_places
    ):
        """
        Test: Travel time estimation between consecutive places

        Given: Places with known distances
        When: Course is generated
        Then: Travel times are calculated for each segment
        """
        # Given: 3 places
        places = sample_places[:3]

        # When: Generate course
        result = recommender.recommend_course(places)

        # Then: Each place (except first) should have travel info
        assert result.places[0].travel_distance_km is None  # First place
        assert result.places[0].travel_duration_minutes is None

        for place in result.places[1:]:
            assert place.travel_distance_km is not None
            assert place.travel_distance_km > 0
            assert place.travel_duration_minutes is not None
            assert place.travel_duration_minutes > 0

    def _calculate_total_distance(self, places: List[PlaceCreate]) -> float:
        """Calculate total distance for a given order of places."""
        from geopy.distance import geodesic

        total = 0.0
        for i in range(len(places) - 1):
            coord1 = (places[i].latitude, places[i].longitude)
            coord2 = (places[i + 1].latitude, places[i + 1].longitude)
            total += geodesic(coord1, coord2).kilometers

        return total
