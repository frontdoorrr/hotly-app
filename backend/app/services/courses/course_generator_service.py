"""코스 생성 서비스."""
import time
import uuid
from datetime import datetime
from datetime import time as time_obj
from datetime import timedelta
from typing import Any, List

from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from app.models.place import Place as PlaceModel
from app.schemas.course_recommendation import (
    CourseDetail,
    CourseGenerateRequest,
    CourseGenerateResponse,
    CoursePlaceDetail,
    DifficultyLevel,
    TravelInfo,
)
from app.services.courses.course_optimizer import CourseOptimizer, Place


class CourseGeneratorService:
    """코스 생성 서비스."""

    def __init__(self, db: Session):
        """
        초기화.

        Args:
            db: 데이터베이스 세션
        """
        self.db = db
        self.optimizer = CourseOptimizer()

    async def generate_course(
        self, request: CourseGenerateRequest
    ) -> CourseGenerateResponse:
        """
        코스 생성.

        Args:
            request: 코스 생성 요청

        Returns:
            생성된 코스

        Raises:
            ValueError: 장소를 찾을 수 없는 경우
        """
        start_time = time.time()

        # 데이터베이스에서 장소 정보 조회
        place_models = (
            self.db.query(PlaceModel).filter(PlaceModel.id.in_(request.place_ids)).all()
        )

        if len(place_models) != len(request.place_ids):
            raise ValueError(
                f"요청한 {len(request.place_ids)}개 장소 중 {len(place_models)}개만 찾았습니다. "
                f"존재하지 않는 장소 ID가 포함되어 있을 수 있습니다."
            )

        # PlaceModel을 CourseOptimizer의 Place 객체로 변환
        places = [
            Place(
                id=str(p.id),
                name=p.name,
                latitude=self._extract_latitude(p.coordinates),
                longitude=self._extract_longitude(p.coordinates),
                category=p.category,
                avg_stay_duration=60,  # 기본값, 추후 카테고리별 차별화 가능
            )
            for p in place_models
        ]

        # 최적화 실행
        optimization_result = self.optimizer.optimize(
            places, transport_method=request.transport_method.value
        )

        # CourseDetail 객체 생성
        course_id = str(uuid.uuid4())
        course_name = (
            f"{optimization_result.optimized_order[0].name} → "
            f"{optimization_result.optimized_order[-1].name} 코스"
        )

        course_detail = CourseDetail(
            name=course_name,
            places=self._create_course_places(
                optimization_result.optimized_order, request.start_time
            ),
            total_duration=optimization_result.total_duration,
            total_distance=optimization_result.total_distance,
            difficulty_level=self._calculate_difficulty(
                optimization_result.total_distance, optimization_result.total_duration
            ),
            tags=[],
        )

        # 생성 시간 계산
        generation_time_ms = int((time.time() - start_time) * 1000)

        return CourseGenerateResponse(
            course_id=course_id,
            course=course_detail,
            optimization_score=optimization_result.optimization_score,
            generation_time_ms=generation_time_ms,
            warnings=[],
        )

    def _extract_latitude(self, coordinates: Any) -> float:
        """PostGIS Geography에서 위도 추출."""
        if coordinates is None:
            return 0.0
        point = to_shape(coordinates)
        return float(point.y)

    def _extract_longitude(self, coordinates: Any) -> float:
        """PostGIS Geography에서 경도 추출."""
        if coordinates is None:
            return 0.0
        point = to_shape(coordinates)
        return float(point.x)

    def _create_course_places(
        self, optimized_order: List[Place], start_time: time_obj
    ) -> List[CoursePlaceDetail]:
        """최적화된 순서로 코스 장소 상세 정보 생성."""
        course_places = []
        current_time = start_time

        for idx, place in enumerate(optimized_order):
            # 도착 시간
            arrival_time = self._format_time(current_time)

            # 체류 시간
            stay_duration = place.avg_stay_duration

            # 출발 시간 계산
            departure_minutes = (
                current_time.hour * 60 + current_time.minute + stay_duration
            )
            departure_time = self._format_minutes_to_time(departure_minutes)

            # 다음 장소로 이동 정보
            travel_info = None
            if idx < len(optimized_order) - 1:
                next_place = optimized_order[idx + 1]
                distance = int(
                    self.optimizer.calculate_distance(
                        place.latitude,
                        place.longitude,
                        next_place.latitude,
                        next_place.longitude,
                    )
                )
                travel_duration = self.optimizer._estimate_travel_time(
                    distance, "walking"
                )

                travel_info = TravelInfo(
                    distance=distance,
                    duration=travel_duration,
                    transport_method="walking",
                    route_description=f"{place.name}에서 {next_place.name}까지",
                )

                # 다음 도착 시간 계산
                current_time = self._add_minutes(
                    current_time, stay_duration + travel_duration
                )
            else:
                current_time = self._add_minutes(current_time, stay_duration)

            course_place = CoursePlaceDetail(
                place_id=place.id,
                order=idx + 1,
                arrival_time=arrival_time,
                stay_duration=stay_duration,
                departure_time=departure_time,
                travel_to_next=travel_info,
            )

            course_places.append(course_place)

        return course_places

    def _calculate_difficulty(
        self, total_distance: int, total_duration: int
    ) -> DifficultyLevel:
        """난이도 계산."""
        # 간단한 휴리스틱: 거리와 시간 기반
        if total_distance < 5000 and total_duration < 240:  # 5km 미만, 4시간 미만
            return DifficultyLevel.EASY
        elif total_distance < 10000 and total_duration < 420:  # 10km 미만, 7시간 미만
            return DifficultyLevel.MODERATE
        else:
            return DifficultyLevel.HARD

    def _format_time(self, time_value: time_obj) -> str:
        """시간 객체를 HH:MM 형식 문자열로 변환."""
        return f"{time_value.hour:02d}:{time_value.minute:02d}"

    def _format_minutes_to_time(self, minutes: int) -> str:
        """분을 HH:MM 형식으로 변환."""
        hours = (minutes // 60) % 24
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def _add_minutes(self, time_value: time_obj, minutes: int) -> time_obj:
        """시간 객체에 분을 더함."""
        # time을 datetime으로 변환
        dt = datetime.combine(datetime.today(), time_value)
        # 분 추가
        dt = dt + timedelta(minutes=minutes)
        # 다시 time으로 변환
        return dt.time()
