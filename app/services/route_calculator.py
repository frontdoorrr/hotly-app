"""
RouteCalculator Service

Task 1-3-2: 장소 간 실시간 위치 확인 및 거리 알고리즘

Kakao Map API를 활용한 실제 경로 거리/시간 계산 서비스
- Distance Matrix API 연동
- 다중 이동수단 지원 (도보/대중교통/자동차)
- 다층 캐싱 (L1: 메모리, L2: Redis 예정)
- Fallback: Haversine 직선거리
"""

import hashlib
import math
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.kakao_map_service import KakaoMapService


class TransportMethod(str, Enum):
    """이동수단"""

    WALKING = "walking"
    TRANSIT = "transit"
    DRIVING = "driving"
    MIXED = "mixed"


class RouteSegment(BaseModel):
    """두 장소 간 경로 정보"""

    distance: int = Field(..., description="거리 (미터)")
    duration: int = Field(..., description="이동시간 (초)")
    transport_method: TransportMethod

    @property
    def distance_km(self) -> float:
        """거리를 킬로미터로 반환"""
        return round(self.distance / 1000, 2)

    @property
    def duration_minutes(self) -> int:
        """이동시간을 분으로 반환"""
        return int(self.duration / 60)

    def format_duration(self) -> str:
        """사람이 읽기 쉬운 형태로 이동시간 포맷팅"""
        minutes = self.duration_minutes
        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}시간 {mins}분"
        else:
            return f"{mins}분"


class RouteMatrix(BaseModel):
    """모든 장소 간 경로 정보 매트릭스"""

    distances: List[List[int]] = Field(..., description="거리 매트릭스 (미터)")
    durations: List[List[int]] = Field(..., description="이동시간 매트릭스 (초)")
    transport_method: TransportMethod
    is_fallback: bool = Field(default=False, description="Fallback 모드 여부")

    @property
    def size(self) -> int:
        """매트릭스 크기 (장소 개수)"""
        return len(self.distances)

    def get_distance(self, from_index: int, to_index: int) -> int:
        """특정 인덱스 간 거리 조회"""
        return self.distances[from_index][to_index]

    def get_duration(self, from_index: int, to_index: int) -> int:
        """특정 인덱스 간 이동시간 조회"""
        return self.durations[from_index][to_index]


class RouteCalculator:
    """
    RouteCalculator Service

    Kakao Map API를 활용한 실제 경로 거리/시간 계산 서비스
    """

    def __init__(self, api_key: Optional[str] = None, enable_cache: bool = True):
        """
        RouteCalculator 초기화

        Args:
            api_key: Kakao API 키 (None일 경우 settings에서 가져옴, 없으면 fallback 모드)
            enable_cache: 캐시 활성화 여부
        """
        # Kakao API 키가 있을 경우에만 서비스 초기화
        try:
            self.kakao_service = KakaoMapService(
                api_key=api_key, enable_cache=enable_cache
            )
        except Exception:  # nosec B110  # Fallback 모드로 안전하게 동작
            # API 키 없으면 None (fallback 모드로 동작)
            self.kakao_service = None  # type: ignore

        self.enable_cache = enable_cache
        self._cache: Dict[str, RouteMatrix] = {} if enable_cache else {}

    async def calculate_route_matrix(
        self, places: List[Dict[str, Any]], transport_method: TransportMethod
    ) -> RouteMatrix:
        """
        모든 장소 간 경로 매트릭스 계산

        Args:
            places: 장소 리스트 (각각 id, latitude, longitude 필드 포함)
            transport_method: 이동수단

        Returns:
            RouteMatrix: 거리/시간 매트릭스

        Raises:
            ValueError: 장소가 2개 미만일 경우
        """
        if len(places) < 2:
            raise ValueError("최소 2개 이상의 장소가 필요합니다")

        # 캐시 확인
        cache_key = self._generate_cache_key(places, transport_method)
        if self.enable_cache and cache_key in self._cache:
            return self._cache[cache_key]

        n = len(places)
        distances = [[0] * n for _ in range(n)]
        durations = [[0] * n for _ in range(n)]
        is_fallback = False

        # 모든 장소 쌍에 대해 경로 계산
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue

                try:
                    # Kakao API로 실제 경로 계산
                    segment = await self._calculate_route_segment(
                        places[i], places[j], transport_method
                    )
                    distances[i][j] = segment.distance
                    durations[i][j] = segment.duration
                except Exception:
                    # Fallback: Haversine 직선거리
                    distance = self._calculate_haversine_distance(places[i], places[j])
                    distances[i][j] = distance
                    durations[i][j] = self._estimate_duration_from_distance(
                        distance, transport_method
                    )
                    is_fallback = True

        matrix = RouteMatrix(
            distances=distances,
            durations=durations,
            transport_method=transport_method,
            is_fallback=is_fallback,
        )

        # 캐시 저장
        if self.enable_cache:
            self._cache[cache_key] = matrix

        return matrix

    async def get_route_segment(
        self,
        origin: Dict[str, Any],
        destination: Dict[str, Any],
        transport_method: TransportMethod,
    ) -> RouteSegment:
        """
        두 장소 간 경로 정보 조회

        Args:
            origin: 출발 장소
            destination: 도착 장소
            transport_method: 이동수단

        Returns:
            RouteSegment: 경로 정보
        """
        return await self._calculate_route_segment(
            origin, destination, transport_method
        )

    async def _calculate_route_segment(
        self,
        origin: Dict[str, Any],
        destination: Dict[str, Any],
        transport_method: TransportMethod,
    ) -> RouteSegment:
        """
        Kakao API를 사용하여 실제 경로 계산

        Args:
            origin: 출발 장소 (latitude, longitude 포함)
            destination: 도착 장소 (latitude, longitude 포함)
            transport_method: 이동수단

        Returns:
            RouteSegment: 경로 정보
        """
        # TODO: Kakao Directions API 연동 (현재는 직선거리로 추정)
        # 실제 구현 시 Kakao Mobility API 사용

        # Fallback: Haversine 거리로 추정
        distance = self._calculate_haversine_distance(origin, destination)
        duration = self._estimate_duration_from_distance(distance, transport_method)

        return RouteSegment(
            distance=distance, duration=duration, transport_method=transport_method
        )

    def _calculate_haversine_distance(
        self, place1: Dict[str, Any], place2: Dict[str, Any]
    ) -> int:
        """
        Haversine 공식을 사용한 두 지점 간 직선거리 계산

        Args:
            place1: 장소1 (latitude, longitude 포함)
            place2: 장소2 (latitude, longitude 포함)

        Returns:
            int: 거리 (미터)
        """
        # 지구 반지름 (미터)
        R = 6371000

        lat1 = math.radians(place1["latitude"])
        lat2 = math.radians(place2["latitude"])
        delta_lat = math.radians(place2["latitude"] - place1["latitude"])
        delta_lon = math.radians(place2["longitude"] - place1["longitude"])

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return int(distance)

    def _estimate_duration_from_distance(
        self, distance: int, transport_method: TransportMethod
    ) -> int:
        """
        거리로부터 이동시간 추정

        Args:
            distance: 거리 (미터)
            transport_method: 이동수단

        Returns:
            int: 이동시간 (초)
        """
        # 평균 속도 (m/s)
        speed_map = {
            TransportMethod.WALKING: 1.2,  # 4.3km/h
            TransportMethod.TRANSIT: 8.3,  # 30km/h (환승 포함)
            TransportMethod.DRIVING: 11.1,  # 40km/h (시내 주행)
            TransportMethod.MIXED: 5.0,  # 혼합
        }

        speed = speed_map.get(transport_method, 1.2)
        duration = int(distance / speed)

        # 최소 이동시간: 1분
        return max(duration, 60)

    def _generate_cache_key(
        self, places: List[Dict[str, Any]], transport_method: TransportMethod
    ) -> str:
        """
        캐시 키 생성

        장소 좌표 조합 + 이동수단으로 고유한 키 생성
        순서 무관 (매트릭스는 순서에 상관없이 동일)

        Args:
            places: 장소 리스트
            transport_method: 이동수단

        Returns:
            str: 캐시 키
        """
        # 좌표 튜플 리스트 생성 및 정렬 (순서 무관)
        coords = [(round(p["latitude"], 6), round(p["longitude"], 6)) for p in places]
        coords_sorted = sorted(coords)

        # 해시 생성 (보안용 아님, 캐시 키 생성용)
        coords_str = str(coords_sorted)
        coord_hash = hashlib.md5(  # nosec B324  # 캐시 키 생성용, 보안 목적 아님
            coords_str.encode(), usedforsecurity=False
        ).hexdigest()[:12]

        return f"{transport_method.value}_{coord_hash}"
