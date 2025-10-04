"""Tests for place duplicate detection algorithm."""

import pytest

from app.models.place import PlaceCategory
from app.schemas.place import PlaceCreate
from app.services.places.duplicate_detector import DuplicateDetector


class TestDuplicateDetector:
    """Test duplicate detection algorithm."""

    @pytest.fixture
    def detector(self) -> DuplicateDetector:
        """Create duplicate detector instance."""
        return DuplicateDetector()

    @pytest.fixture
    def sample_place(self) -> PlaceCreate:
        """Create sample place for testing."""
        return PlaceCreate(
            name="스타벅스 강남점",
            address="서울특별시 강남구 테헤란로 152",
            category=PlaceCategory.CAFE,
            latitude=37.5013068,
            longitude=127.0396597,
            tags=["카페", "스터디"],
        )

    @pytest.mark.asyncio
    async def test_exact_duplicate_detection(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test exact duplicate detection."""
        # Given: Exact same place data
        existing_places = [sample_place]
        new_place = sample_place

        # When: Check for duplicates
        result = await detector.check_duplicate(new_place, existing_places)

        # Then: Should detect as duplicate
        assert result.is_duplicate is True
        assert result.confidence >= 0.95
        assert result.match_type == "exact"

    @pytest.mark.asyncio
    async def test_name_similarity_detection(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test name similarity based duplicate detection."""
        # Given: Similar name, same address
        existing_places = [sample_place]
        new_place = PlaceCreate(
            name="스타벅스 강남",  # 약간 다른 이름
            address="서울특별시 강남구 테헤란로 152",
            category=PlaceCategory.CAFE,
            latitude=37.5013068,
            longitude=127.0396597,
        )

        # When: Check for duplicates
        result = await detector.check_duplicate(new_place, existing_places)

        # Then: Should detect as likely duplicate
        assert result.is_duplicate is True
        assert result.confidence >= 0.80
        assert result.match_type == "name_similarity"

    @pytest.mark.asyncio
    async def test_address_normalization_detection(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test address normalization based duplicate detection."""
        # Given: Different address format, same location
        existing_places = [sample_place]
        new_place = PlaceCreate(
            name="다른카페 강남점",  # 다른 이름으로 변경
            address="강남구 테헤란로152",  # 다른 주소 표기
            category=PlaceCategory.CAFE,
            latitude=37.5013068,
            longitude=127.0396597,
        )

        # When: Check for duplicates
        result = await detector.check_duplicate(new_place, existing_places)

        # Then: Should detect as possible duplicate
        assert result.is_duplicate is True
        assert result.confidence >= 0.70
        assert result.match_type == "address_similarity"

    @pytest.mark.asyncio
    async def test_geographical_proximity_detection(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test geographical proximity duplicate detection."""
        # Given: Same name, very close coordinates (within 50m)
        existing_places = [sample_place]
        new_place = PlaceCreate(
            name="다른카페 이름",  # 다른 이름으로 변경
            address="서울 강남구 다른주소",
            category=PlaceCategory.CAFE,
            latitude=37.5013500,  # 약 50m 차이
            longitude=127.0397000,
        )

        # When: Check for duplicates
        result = await detector.check_duplicate(new_place, existing_places)

        # Then: Should detect as geographical duplicate
        assert result.is_duplicate is True
        assert result.confidence >= 0.75
        assert result.match_type == "geographical_proximity"

    @pytest.mark.asyncio
    async def test_no_duplicate_different_places(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test no duplicate detection for different places."""
        # Given: Completely different place
        existing_places = [sample_place]
        new_place = PlaceCreate(
            name="투썸플레이스 역삼점",
            address="서울특별시 강남구 역삼동 123",
            category=PlaceCategory.CAFE,
            latitude=37.4979462,  # 다른 위치
            longitude=127.0276368,
        )

        # When: Check for duplicates
        result = await detector.check_duplicate(new_place, existing_places)

        # Then: Should not detect as duplicate
        assert result.is_duplicate is False
        assert result.confidence <= 0.30

    @pytest.mark.asyncio
    async def test_multi_stage_detection_algorithm(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test multi-stage duplicate detection algorithm."""
        # Given: Various similar places
        existing_places = [sample_place]
        test_cases = [
            {
                "place": PlaceCreate(
                    name="스타벅스",  # 짧은 이름
                    address="서울특별시 강남구 테헤란로 152",
                    category=PlaceCategory.CAFE,
                    latitude=37.5013068,
                    longitude=127.0396597,
                ),
                "expected_type": "name_similarity",
            },
            {
                "place": PlaceCreate(
                    name="스타벅스 강남점",
                    address="다른주소",  # 다른 주소
                    category=PlaceCategory.CAFE,
                    latitude=37.5013068,
                    longitude=127.0396597,
                ),
                "expected_type": "geographical_proximity",
            },
        ]

        # When/Then: Test each case
        for case in test_cases:
            result = await detector.check_duplicate(case["place"], existing_places)
            assert result.match_type == case["expected_type"]

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test performance with large number of existing places."""
        # Given: Large dataset of 1000 places
        existing_places = []
        for i in range(1000):
            place = PlaceCreate(
                name=f"장소{i}",
                address=f"서울시 강남구 {i}번지",
                category=PlaceCategory.RESTAURANT,
                latitude=37.5 + i * 0.001,
                longitude=127.0 + i * 0.001,
            )
            existing_places.append(place)

        # When: Check duplicate against large dataset
        import time

        start_time = time.time()
        result = await detector.check_duplicate(sample_place, existing_places)
        detection_time = time.time() - start_time

        # Then: Should complete within performance threshold (200ms)
        assert detection_time < 0.2
        assert result.is_duplicate is False

    @pytest.mark.asyncio
    async def test_confidence_threshold_validation(
        self, detector: DuplicateDetector, sample_place: PlaceCreate
    ):
        """Test confidence threshold for duplicate classification."""
        # Given: Places with various similarity levels
        test_cases = [
            {
                "name": "스타벅스 강남점",
                "address": "서울특별시 강남구 테헤란로 152",
                "expected_duplicate": True,  # 완전 일치
            },
            {
                "name": "스타벅스강남점",  # 공백 차이
                "address": "서울특별시 강남구 테헤란로 152",
                "expected_duplicate": True,  # 높은 유사도
            },
            {
                "name": "스타벅스",
                "address": "서울특별시 강남구 테헤란로 152",
                "expected_duplicate": True,  # 이름 포함 관계
            },
            {
                "name": "카페베네 강남점",
                "address": "서울특별시 서초구 반포대로 123",
                "expected_duplicate": False,  # 다른 장소 (다른 구)
            },
        ]

        existing_places = [sample_place]

        # When/Then: Test each threshold case
        for case in test_cases:
            new_place = PlaceCreate(
                name=case["name"],
                address=case["address"],
                category=PlaceCategory.CAFE,
                latitude=(37.4979462 if case["name"] == "카페베네 강남점" else 37.5013068),
                longitude=(127.0276368 if case["name"] == "카페베네 강남점" else 127.0396597),
            )

            result = await detector.check_duplicate(new_place, existing_places)
            assert result.is_duplicate == case["expected_duplicate"]

    def test_name_normalization_algorithm(self, detector: DuplicateDetector):
        """Test name normalization algorithm."""
        # Given: Various name formats
        test_cases = [
            ("스타벅스 강남점", "스타벅스강남점"),
            ("McDonald's", "mcdonalds"),
            ("KFC치킨", "kfc치킨"),
            ("  공백제거테스트  ", "공백제거테스트"),
        ]

        # When/Then: Test normalization consistency
        for original, expected in test_cases:
            normalized = detector._normalize_name(original)
            assert normalized == expected

    def test_address_normalization_algorithm(self, detector: DuplicateDetector):
        """Test address normalization algorithm."""
        # Given: Various address formats
        test_cases = [
            ("서울특별시 강남구 테헤란로 152", "서울강남구테헤란로152"),
            ("서울 강남구 테헤란로152번길", "서울강남구테헤란로152번길"),
            ("강남구 테헤란로 152", "강남구테헤란로152"),
        ]

        # When/Then: Test normalization consistency
        for original, expected in test_cases:
            normalized = detector._normalize_address(original)
            assert normalized == expected

    def test_distance_calculation_accuracy(self, detector: DuplicateDetector):
        """Test geographical distance calculation accuracy."""
        # Given: Known coordinates with known distance
        lat1, lng1 = 37.5013068, 127.0396597  # 강남역
        lat2, lng2 = 37.5042068, 127.0426597  # 약 417m 차이 (실제 계산값)

        # When: Calculate distance
        distance = detector._calculate_distance(lat1, lng1, lat2, lng2)

        # Then: Should be approximately 417m (±50m tolerance)
        assert 367 <= distance <= 467
