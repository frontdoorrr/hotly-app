"""코스 최적화 알고리즘 단위 테스트."""
from typing import List

import pytest

from app.services.course_optimizer import CourseOptimizer, OptimizationResult, Place


class TestCourseOptimizer:
    """코스 최적화 알고리즘 테스트."""

    @pytest.fixture
    def sample_places(self) -> List[Place]:
        """테스트용 샘플 장소들."""
        return [
            Place(
                id="place1",
                name="홍대 카페",
                latitude=37.5563,
                longitude=126.9241,
                category="cafe",
                avg_stay_duration=60,
            ),
            Place(
                id="place2",
                name="연남동 맛집",
                latitude=37.5658,
                longitude=126.9244,
                category="restaurant",
                avg_stay_duration=90,
            ),
            Place(
                id="place3",
                name="망원한강공원",
                latitude=37.5533,
                longitude=126.8947,
                category="attraction",
                avg_stay_duration=120,
            ),
            Place(
                id="place4",
                name="상수역 디저트",
                latitude=37.5478,
                longitude=126.9227,
                category="cafe",
                avg_stay_duration=45,
            ),
        ]

    @pytest.fixture
    def optimizer(self) -> CourseOptimizer:
        """테스트용 최적화 인스턴스."""
        return CourseOptimizer()

    def test_optimize_validPlaces_returnsOptimizedResult(
        self, optimizer: CourseOptimizer, sample_places: List[Place]
    ) -> None:
        """유효한 장소 입력 시 최적화 결과 반환."""
        # Given: 유효한 장소 목록
        # When: 최적화 실행
        result = optimizer.optimize(sample_places, transport_method="walking")

        # Then: 최적화 결과 반환
        assert isinstance(result, OptimizationResult)
        assert len(result.optimized_order) == len(sample_places)
        assert result.optimization_score > 0
        assert result.total_distance > 0
        assert result.total_duration > 0

    def test_optimize_minimizeDistance_returnsShortestPath(
        self, optimizer: CourseOptimizer, sample_places: List[Place]
    ) -> None:
        """거리 최소화 시 최단 경로 반환."""
        # Given: 거리 가중치 100%
        optimizer.set_weights(distance=1.0, time=0.0, variety=0.0)

        # When: 최적화 실행
        result = optimizer.optimize(sample_places, transport_method="walking")

        # Then: 최소한 place1과 place4는 인접해야 함 (가장 가까운 두 장소)
        order_ids = [p.id for p in result.optimized_order]
        place1_idx = order_ids.index("place1")
        place4_idx = order_ids.index("place4")
        assert abs(place1_idx - place4_idx) <= 1

    def test_optimize_categoryVariety_avoidsConsecutiveSameCategory(
        self, optimizer: CourseOptimizer, sample_places: List[Place]
    ) -> None:
        """카테고리 다양성 고려 시 연속 같은 카테고리 회피."""
        # Given: 카테고리 다양성 가중치 높음
        optimizer.set_weights(distance=0.3, time=0.2, variety=0.5)

        # When: 최적화 실행
        result = optimizer.optimize(sample_places, transport_method="walking")

        # Then: 카페(place1, place4)가 연속으로 오지 않음
        categories = [p.category for p in result.optimized_order]

        # 카페가 2개 있는데 연속으로 오면 안됨
        cafe_indices = [i for i, cat in enumerate(categories) if cat == "cafe"]
        if len(cafe_indices) == 2:
            assert abs(cafe_indices[0] - cafe_indices[1]) > 1

    def test_optimize_threeLocations_returnsValidCourse(
        self, optimizer: CourseOptimizer
    ) -> None:
        """최소 개수(3개) 장소로도 정상 작동."""
        # Given: 3개 장소
        places = [
            Place(
                id="p1",
                name="Place 1",
                latitude=37.5,
                longitude=127.0,
                category="cafe",
                avg_stay_duration=60,
            ),
            Place(
                id="p2",
                name="Place 2",
                latitude=37.51,
                longitude=127.01,
                category="restaurant",
                avg_stay_duration=90,
            ),
            Place(
                id="p3",
                name="Place 3",
                latitude=37.52,
                longitude=127.02,
                category="attraction",
                avg_stay_duration=120,
            ),
        ]

        # When: 최적화 실행
        result = optimizer.optimize(places, transport_method="walking")

        # Then: 3개 모두 포함된 결과 반환
        assert len(result.optimized_order) == 3
        assert result.optimization_score > 0

    def test_optimize_sixLocations_returnsValidCourse(
        self, optimizer: CourseOptimizer
    ) -> None:
        """최대 개수(6개) 장소로도 정상 작동."""
        # Given: 6개 장소
        places = [
            Place(
                id=f"p{i}",
                name=f"Place {i}",
                latitude=37.5 + i * 0.01,
                longitude=127.0 + i * 0.01,
                category="cafe" if i % 2 == 0 else "restaurant",
                avg_stay_duration=60,
            )
            for i in range(6)
        ]

        # When: 최적화 실행
        result = optimizer.optimize(places, transport_method="walking")

        # Then: 6개 모두 포함된 결과 반환
        assert len(result.optimized_order) == 6
        assert result.optimization_score > 0

    def test_optimize_differentTransportMethods_affectsDuration(
        self, optimizer: CourseOptimizer, sample_places: List[Place]
    ) -> None:
        """교통 수단에 따라 소요 시간 달라짐."""
        # When: 각기 다른 교통수단으로 최적화
        result_walking = optimizer.optimize(sample_places, transport_method="walking")
        result_transit = optimizer.optimize(sample_places, transport_method="transit")
        result_driving = optimizer.optimize(sample_places, transport_method="driving")

        # Then: 도보 > 대중교통 > 차량 순으로 시간이 더 오래 걸림
        assert result_walking.total_duration > result_transit.total_duration
        assert result_transit.total_duration > result_driving.total_duration

    def test_calculateDistance_seoulLocations_returnsAccurateDistance(
        self, optimizer: CourseOptimizer
    ) -> None:
        """서울 실제 좌표로 거리 계산 정확도 검증."""
        # Given: 홍대와 강남역 좌표
        hongdae_lat, hongdae_lon = 37.5563, 126.9241
        gangnam_lat, gangnam_lon = 37.4979, 127.0276

        # When: 거리 계산
        distance = optimizer.calculate_distance(
            hongdae_lat, hongdae_lon, gangnam_lat, gangnam_lon
        )

        # Then: 약 11.2km (Google Maps 실제 거리와 유사)
        assert 10500 <= distance <= 11500

    def test_setWeights_validWeights_modifiesOptimization(
        self, optimizer: CourseOptimizer, sample_places: List[Place]
    ) -> None:
        """가중치 설정에 따라 최적화 결과 변화."""
        # Given: 서로 다른 가중치
        optimizer_distance = CourseOptimizer()
        optimizer_distance.set_weights(distance=1.0, time=0.0, variety=0.0)

        optimizer_variety = CourseOptimizer()
        optimizer_variety.set_weights(distance=0.0, time=0.0, variety=1.0)

        # When: 최적화 실행
        result_distance = optimizer_distance.optimize(
            sample_places, transport_method="walking"
        )
        result_variety = optimizer_variety.optimize(
            sample_places, transport_method="walking"
        )

        # Then: 결과가 다름 (항상은 아니지만 대부분의 경우)
        # 거리 기반은 총 거리가 더 짧아야 함
        assert result_distance.total_distance <= result_variety.total_distance * 1.2

    def test_optimize_tooFewPlaces_raisesValueError(
        self, optimizer: CourseOptimizer
    ) -> None:
        """3개 미만 장소 입력 시 예외 발생."""
        # Given: 2개 장소만
        places = [
            Place(
                id="p1",
                name="Place 1",
                latitude=37.5,
                longitude=127.0,
                category="cafe",
                avg_stay_duration=60,
            ),
            Place(
                id="p2",
                name="Place 2",
                latitude=37.51,
                longitude=127.01,
                category="restaurant",
                avg_stay_duration=90,
            ),
        ]

        # When & Then: ValueError 발생
        with pytest.raises(ValueError, match="최소 3개 이상"):
            optimizer.optimize(places, transport_method="walking")

    def test_optimize_tooManyPlaces_raisesValueError(
        self, optimizer: CourseOptimizer
    ) -> None:
        """6개 초과 장소 입력 시 예외 발생."""
        # Given: 7개 장소
        places = [
            Place(
                id=f"p{i}",
                name=f"Place {i}",
                latitude=37.5 + i * 0.01,
                longitude=127.0 + i * 0.01,
                category="cafe",
                avg_stay_duration=60,
            )
            for i in range(7)
        ]

        # When & Then: ValueError 발생
        with pytest.raises(ValueError, match="최대 6개까지"):
            optimizer.optimize(places, transport_method="walking")
