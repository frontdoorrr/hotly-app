"""AI 기반 코스 추천 스키마 정의."""
from datetime import time
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TransportMethod(str, Enum):
    """이동 수단."""

    WALKING = "walking"
    TRANSIT = "transit"
    DRIVING = "driving"
    MIXED = "mixed"


class DifficultyLevel(str, Enum):
    """코스 난이도."""

    EASY = "easy"  # 이동거리 짧고 체력 소모 적음
    MODERATE = "moderate"  # 보통
    HARD = "hard"  # 이동거리 길고 체력 소모 큼


class CourseType(str, Enum):
    """코스 타입."""

    ROMANTIC = "romantic"  # 로맨틱
    FOODIE = "foodie"  # 맛집 투어
    ACTIVITY = "activity"  # 액티비티
    CULTURE = "culture"  # 문화/예술
    NATURE = "nature"  # 자연/힐링
    SHOPPING = "shopping"  # 쇼핑


class CoursePreferences(BaseModel):
    """코스 생성 선호도 설정."""

    category_order: Optional[List[str]] = Field(
        None, description="선호하는 카테고리 순서 (예: ['cafe', 'restaurant', 'attraction'])"
    )
    max_total_duration: int = Field(
        default=600, ge=240, le=720, description="최대 총 소요 시간 (분)"
    )
    avoid_rush_hours: bool = Field(default=True, description="혼잡 시간대 회피")
    preferred_stay_duration: Dict[str, int] = Field(
        default_factory=dict, description="카테고리별 선호 체류 시간 (분)"
    )
    budget_level: Optional[str] = Field(None, description="예산 수준 (low/medium/high)")


class CourseGenerateRequest(BaseModel):
    """코스 생성 요청."""

    place_ids: List[str] = Field(..., description="장소 ID 목록 (3-6개)")
    transport_method: TransportMethod = Field(
        default=TransportMethod.WALKING, description="이동 수단"
    )
    start_time: time = Field(default=time(10, 0), description="시작 시간")

    preferences: Optional[CoursePreferences] = Field(None, description="선호도 설정")
    user_id: Optional[str] = Field(None, description="사용자 ID (개인화용)")

    @field_validator("place_ids")
    @classmethod
    def validate_place_count(cls, v: List[str]) -> List[str]:
        """장소 개수 검증."""
        if len(v) < 3:
            raise ValueError("최소 3개 이상의 장소를 선택해야 합니다")
        if len(v) > 6:
            raise ValueError("최대 6개까지 장소를 선택할 수 있습니다")
        return v


class CoursePlaceDetail(BaseModel):
    """코스 내 장소 상세 정보."""

    place_id: str = Field(..., description="장소 ID")
    order: int = Field(..., description="방문 순서 (1부터 시작)")
    arrival_time: str = Field(..., description="도착 예상 시간 (HH:MM)")
    stay_duration: int = Field(..., description="체류 시간 (분)")
    departure_time: str = Field(..., description="출발 예상 시간 (HH:MM)")
    travel_to_next: Optional["TravelInfo"] = Field(None, description="다음 장소로 이동 정보")


class TravelInfo(BaseModel):
    """장소 간 이동 정보."""

    distance: int = Field(..., description="이동 거리 (미터)")
    duration: int = Field(..., description="이동 시간 (분)")
    transport_method: TransportMethod = Field(..., description="이동 수단")
    route_description: Optional[str] = Field(None, description="경로 설명")


class CostBreakdown(BaseModel):
    """예상 비용 분석."""

    transportation: int = Field(default=0, description="교통비 (원)")
    food: int = Field(default=0, description="식비 (원)")
    activity: int = Field(default=0, description="액티비티 비용 (원)")
    total: int = Field(..., description="총 예상 비용 (원)")


class CourseDetail(BaseModel):
    """코스 상세 정보."""

    name: str = Field(..., description="코스 이름")
    places: List[CoursePlaceDetail] = Field(..., description="장소 목록")
    total_duration: int = Field(..., description="총 소요 시간 (분)")
    total_distance: int = Field(..., description="총 이동 거리 (미터)")
    estimated_cost: Optional[CostBreakdown] = Field(None, description="예상 비용")
    difficulty_level: DifficultyLevel = Field(..., description="난이도")
    course_type: Optional[CourseType] = Field(None, description="코스 타입")
    tags: List[str] = Field(default_factory=list, description="코스 태그")


class CourseAlternative(BaseModel):
    """대안 코스."""

    course: CourseDetail = Field(..., description="대안 코스 상세")
    score: float = Field(..., ge=0, le=100, description="최적화 점수")
    reason: str = Field(..., description="추천 이유")


class CourseGenerateResponse(BaseModel):
    """코스 생성 응답."""

    course_id: str = Field(..., description="생성된 코스 ID")
    course: CourseDetail = Field(..., description="코스 상세 정보")
    optimization_score: float = Field(..., ge=0, le=100, description="최적화 점수 (0-100)")
    generation_time_ms: int = Field(..., description="생성 소요 시간 (밀리초)")
    alternatives: Optional[List[CourseAlternative]] = Field(
        None, description="대안 코스 목록"
    )
    warnings: List[str] = Field(default_factory=list, description="경고 메시지 (영업시간 충돌 등)")


class OptimizationMetrics(BaseModel):
    """최적화 메트릭."""

    distance_score: float = Field(..., ge=0, le=100, description="거리 최적화 점수")
    time_score: float = Field(..., ge=0, le=100, description="시간 효율성 점수")
    variety_score: float = Field(..., ge=0, le=100, description="카테고리 다양성 점수")
    preference_score: float = Field(..., ge=0, le=100, description="선호도 일치 점수")
    overall_score: float = Field(..., ge=0, le=100, description="종합 점수")


class CourseRecommendationFeedback(BaseModel):
    """코스 추천 피드백."""

    course_id: str = Field(..., description="코스 ID")
    user_id: str = Field(..., description="사용자 ID")
    rating: int = Field(..., ge=1, le=5, description="평점 (1-5)")
    was_helpful: bool = Field(..., description="유용했는지 여부")
    actual_duration: Optional[int] = Field(None, description="실제 소요 시간 (분)")
    completed: bool = Field(default=False, description="코스 완주 여부")
    comments: Optional[str] = Field(None, description="추가 코멘트")
