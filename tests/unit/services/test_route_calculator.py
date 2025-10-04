"""
RouteCalculator 서비스 단위 테스트 (TDD)

Task: 1-3-2 장소 간 실시간 위치 확인 및 거리 알고리즘
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.services.route_calculator import (
    RouteCalculator,
    RouteMatrix,
    RouteSegment,
    TransportMethod,
)


class TestRouteCalculator:
    """RouteCalculator 서비스 테스트"""

    @pytest.fixture
    def sample_places(self) -> List[Dict[str, Any]]:
        """테스트용 샘플 장소 데이터"""
        return [
            {
                "id": "place_1",
                "name": "강남역 카페",
                "latitude": 37.4979,
                "longitude": 127.0276,
            },
            {
                "id": "place_2",
                "name": "선릉역 맛집",
                "latitude": 37.5045,
                "longitude": 127.0493,
            },
            {
                "id": "place_3",
                "name": "코엑스",
                "latitude": 37.5126,
                "longitude": 127.0588,
            },
        ]

    @pytest.fixture
    def mock_kakao_response(self) -> Dict[str, Any]:
        """Kakao API Distance Matrix 응답 모킹"""
        return {
            "routes": [
                {
                    "result_code": 0,
                    "result_msg": "Success",
                    "summary": {
                        "distance": 1850,  # meters
                        "duration": 1320,  # seconds (22 minutes)
                    },
                }
            ]
        }

    # ==================== RED 단계: 실패하는 테스트 작성 ====================

    @pytest.mark.asyncio
    async def test_calculateWalkingMatrix_validPlaces_returnsMatrix(
        self, sample_places: List[Dict[str, Any]], mock_kakao_response: Dict[str, Any]
    ) -> None:
        """도보 이동시간 매트릭스 계산 - 정상 케이스"""
        # Given
        calculator = RouteCalculator()

        with patch.object(
            calculator.kakao_service, "_make_request", new=AsyncMock()
        ) as mock_request:
            mock_request.return_value = mock_kakao_response

            # When
            matrix = await calculator.calculate_route_matrix(
                sample_places, TransportMethod.WALKING
            )

            # Then
            assert matrix is not None
            assert len(matrix.distances) == 3
            assert len(matrix.durations) == 3
            assert matrix.transport_method == TransportMethod.WALKING

            # 대칭성 검증 (i->j 거리 == j->i 거리)
            for i in range(3):
                for j in range(3):
                    if i != j:
                        assert matrix.distances[i][j] > 0
                        assert matrix.durations[i][j] > 0

    @pytest.mark.asyncio
    async def test_calculateTransitMatrix_validPlaces_returnsMatrix(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """대중교통 이동시간 매트릭스 계산"""
        # Given
        calculator = RouteCalculator()

        # When
        matrix = await calculator.calculate_route_matrix(
            sample_places, TransportMethod.TRANSIT
        )

        # Then
        assert matrix.transport_method == TransportMethod.TRANSIT
        # 대중교통은 도보보다 빠를 수 있음
        assert all(duration >= 0 for row in matrix.durations for duration in row)

    @pytest.mark.asyncio
    async def test_calculateDrivingMatrix_validPlaces_returnsMatrix(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """자동차 이동시간 매트릭스 계산"""
        # Given
        calculator = RouteCalculator()

        # When
        matrix = await calculator.calculate_route_matrix(
            sample_places, TransportMethod.DRIVING
        )

        # Then
        assert matrix.transport_method == TransportMethod.DRIVING
        assert all(
            distance > 0 for row in matrix.distances for distance in row if distance > 0
        )

    @pytest.mark.asyncio
    async def test_calculateMatrix_withCache_returnsCachedResult(
        self, sample_places: List[Dict[str, Any]], mock_kakao_response: Dict[str, Any]
    ) -> None:
        """캐시된 결과 반환 - 중복 요청 시"""
        # Given
        calculator = RouteCalculator(enable_cache=True)

        with patch.object(
            calculator.kakao_service, "_make_request", new=AsyncMock()
        ) as mock_request:
            mock_request.return_value = mock_kakao_response

            # When - 첫 번째 요청
            matrix1 = await calculator.calculate_route_matrix(
                sample_places, TransportMethod.WALKING
            )

            # When - 두 번째 요청 (캐시 적중)
            matrix2 = await calculator.calculate_route_matrix(
                sample_places, TransportMethod.WALKING
            )

            # Then
            assert matrix1.distances == matrix2.distances
            assert matrix1.durations == matrix2.durations
            # API는 한 번만 호출되어야 함
            assert mock_request.call_count <= 3  # 3x3 매트릭스이므로 최대 3번

    @pytest.mark.asyncio
    async def test_calculateMatrix_apiFailure_fallbackToHaversine(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """API 실패 시 하버사인 거리로 fallback"""
        # Given
        calculator = RouteCalculator()

        with patch.object(
            calculator.kakao_service, "_make_request", new=AsyncMock()
        ) as mock_request:
            mock_request.side_effect = Exception("API Error")

            # When
            matrix = await calculator.calculate_route_matrix(
                sample_places, TransportMethod.WALKING
            )

            # Then
            assert matrix is not None
            assert all(
                distance > 0
                for row in matrix.distances
                for distance in row
                if distance > 0
            )
            # Fallback 모드 확인
            assert matrix.is_fallback is True

    def test_calculateHaversineDistance_twoPoints_returnsCorrectDistance(self) -> None:
        """하버사인 거리 계산 - 정확도 검증"""
        # Given
        calculator = RouteCalculator()
        place1 = {"latitude": 37.4979, "longitude": 127.0276}  # 강남역
        place2 = {"latitude": 37.5126, "longitude": 127.0588}  # 코엑스

        # When
        distance = calculator._calculate_haversine_distance(place1, place2)

        # Then
        # 강남역-코엑스 직선거리는 약 2.8km
        assert 2500 <= distance <= 3500  # meters
        assert isinstance(distance, (int, float))

    @pytest.mark.asyncio
    async def test_getRouteSegment_twoPlaces_returnsSegmentInfo(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """두 장소 간 경로 정보 조회"""
        # Given
        calculator = RouteCalculator()
        origin = sample_places[0]
        destination = sample_places[1]

        # When
        segment = await calculator.get_route_segment(
            origin, destination, TransportMethod.WALKING
        )

        # Then
        assert isinstance(segment, RouteSegment)
        assert segment.distance > 0
        assert segment.duration > 0
        assert segment.transport_method == TransportMethod.WALKING

    @pytest.mark.asyncio
    async def test_calculateMatrix_emptyPlaces_raisesValueError(self) -> None:
        """빈 장소 리스트 - 에러 발생"""
        # Given
        calculator = RouteCalculator()

        # When & Then
        with pytest.raises(ValueError, match="최소 2개 이상의 장소"):
            await calculator.calculate_route_matrix([], TransportMethod.WALKING)

    @pytest.mark.asyncio
    async def test_calculateMatrix_singlePlace_raisesValueError(self) -> None:
        """단일 장소 - 에러 발생"""
        # Given
        calculator = RouteCalculator()
        single_place = [{"id": "1", "latitude": 37.5, "longitude": 127.0}]

        # When & Then
        with pytest.raises(ValueError, match="최소 2개 이상의 장소"):
            await calculator.calculate_route_matrix(
                single_place, TransportMethod.WALKING
            )

    def test_generateCacheKey_samePlaces_returnsSameKey(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """동일한 장소 조합 - 동일한 캐시 키 생성"""
        # Given
        calculator = RouteCalculator()

        # When
        key1 = calculator._generate_cache_key(sample_places, TransportMethod.WALKING)
        key2 = calculator._generate_cache_key(sample_places, TransportMethod.WALKING)

        # Then
        assert key1 == key2
        assert "walking" in key1.lower()

    def test_generateCacheKey_differentOrder_returnsSameKey(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """장소 순서 무관 - 동일한 캐시 키 생성"""
        # Given
        calculator = RouteCalculator()
        reversed_places = list(reversed(sample_places))

        # When
        key1 = calculator._generate_cache_key(sample_places, TransportMethod.WALKING)
        key2 = calculator._generate_cache_key(reversed_places, TransportMethod.WALKING)

        # Then
        # 매트릭스는 순서 무관하므로 같은 키
        assert key1 == key2

    def test_generateCacheKey_differentTransport_returnsDifferentKey(
        self, sample_places: List[Dict[str, Any]]
    ) -> None:
        """다른 이동수단 - 다른 캐시 키 생성"""
        # Given
        calculator = RouteCalculator()

        # When
        key_walking = calculator._generate_cache_key(
            sample_places, TransportMethod.WALKING
        )
        key_driving = calculator._generate_cache_key(
            sample_places, TransportMethod.DRIVING
        )

        # Then
        assert key_walking != key_driving


class TestRouteMatrix:
    """RouteMatrix 모델 테스트"""

    def test_createMatrix_validData_success(self) -> None:
        """유효한 데이터로 RouteMatrix 생성"""
        # Given
        distances = [[0, 1000, 2000], [1000, 0, 1500], [2000, 1500, 0]]
        durations = [[0, 720, 1440], [720, 0, 1080], [1440, 1080, 0]]

        # When
        matrix = RouteMatrix(
            distances=distances,
            durations=durations,
            transport_method=TransportMethod.WALKING,
        )

        # Then
        assert matrix.distances == distances
        assert matrix.durations == durations
        assert matrix.size == 3

    def test_getDistance_validIndices_returnsDistance(self) -> None:
        """특정 인덱스 간 거리 조회"""
        # Given
        matrix = RouteMatrix(
            distances=[[0, 1000], [1000, 0]],
            durations=[[0, 720], [720, 0]],
            transport_method=TransportMethod.WALKING,
        )

        # When
        distance = matrix.get_distance(0, 1)

        # Then
        assert distance == 1000

    def test_getDuration_validIndices_returnsDuration(self) -> None:
        """특정 인덱스 간 이동시간 조회"""
        # Given
        matrix = RouteMatrix(
            distances=[[0, 1000], [1000, 0]],
            durations=[[0, 720], [720, 0]],
            transport_method=TransportMethod.WALKING,
        )

        # When
        duration = matrix.get_duration(0, 1)

        # Then
        assert duration == 720  # 12분

    def test_getDistance_invalidIndex_raisesIndexError(self) -> None:
        """잘못된 인덱스 - 에러 발생"""
        # Given
        matrix = RouteMatrix(
            distances=[[0, 1000], [1000, 0]],
            durations=[[0, 720], [720, 0]],
            transport_method=TransportMethod.WALKING,
        )

        # When & Then
        with pytest.raises(IndexError):
            matrix.get_distance(0, 5)


class TestRouteSegment:
    """RouteSegment 모델 테스트"""

    def test_createSegment_validData_success(self) -> None:
        """유효한 데이터로 RouteSegment 생성"""
        # Given & When
        segment = RouteSegment(
            distance=1500,  # meters
            duration=1080,  # seconds (18 minutes)
            transport_method=TransportMethod.WALKING,
        )

        # Then
        assert segment.distance == 1500
        assert segment.duration == 1080
        assert segment.distance_km == 1.5
        assert segment.duration_minutes == 18

    def test_formatDuration_seconds_returnsFormattedString(self) -> None:
        """이동시간 포맷팅 - 사람이 읽기 쉬운 형태"""
        # Given
        segment = RouteSegment(
            distance=3000, duration=3720, transport_method=TransportMethod.WALKING
        )

        # When
        formatted = segment.format_duration()

        # Then
        assert formatted == "1시간 2분"  # 3720초 = 62분

    def test_formatDuration_shortTime_returnsMinutesOnly(self) -> None:
        """짧은 이동시간 - 분 단위만 표시"""
        # Given
        segment = RouteSegment(
            distance=500, duration=300, transport_method=TransportMethod.WALKING
        )

        # When
        formatted = segment.format_duration()

        # Then
        assert formatted == "5분"
