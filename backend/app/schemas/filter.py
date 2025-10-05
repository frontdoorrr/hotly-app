"""
필터 및 정렬 스키마 (Task 2-3-3)

필터링과 정렬에 사용되는 Pydantic 모델들
- 필터 조건 및 결과 모델
- 정렬 기준 및 방향 모델  
- 필터 프리셋 및 추천 모델
- 검색 선호도 및 통계 모델
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SortField(str, Enum):
    """정렬 필드 타입"""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    RATING = "rating"
    PRICE_RANGE = "price_range"
    VISIT_COUNT = "visit_count"
    LAST_VISITED = "last_visited"
    DISTANCE = "distance"
    POPULARITY = "popularity"
    RANDOM = "random"
    PERSONALIZED = "personalized"
    RELEVANCE = "relevance"


class SortDirection(str, Enum):
    """정렬 방향"""
    ASC = "asc"
    DESC = "desc"


class VisitStatus(str, Enum):
    """방문 상태"""
    VISITED = "visited"
    NOT_VISITED = "not_visited"
    ANY = "any"


class LocationInput(BaseModel):
    """위치 입력 모델"""
    latitude: float = Field(..., ge=-90, le=90, description="위도")
    longitude: float = Field(..., ge=-180, le=180, description="경도")


class SortFieldInput(BaseModel):
    """정렬 필드 입력"""
    field: SortField = Field(..., description="정렬 필드")
    direction: SortDirection = Field(SortDirection.DESC, description="정렬 방향")


class SortCriteria(BaseModel):
    """정렬 조건"""
    fields: List[SortFieldInput] = Field(default_factory=list, description="정렬 필드 목록")
    user_location: Optional[LocationInput] = Field(None, description="사용자 위치 (거리 정렬용)")

    @validator('fields')
    def validate_sort_fields(cls, v):
        if len(v) > 5:
            raise ValueError("최대 5개의 정렬 조건만 허용됩니다.")
        return v


class FilterCriteria(BaseModel):
    """필터 조건"""
    # 카테고리 필터
    categories: Optional[List[str]] = Field(None, description="카테고리 목록")
    
    # 지역 필터  
    regions: Optional[List[str]] = Field(None, description="지역 목록")
    
    # 상태 필터
    status_filters: Optional[List[str]] = Field(None, description="상태 목록")
    
    # 가격대 필터
    price_ranges: Optional[List[int]] = Field(None, description="가격대 목록 (1-5)")
    
    # 평점 필터
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="최소 평점")
    max_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="최대 평점")
    
    # 거리 필터
    max_distance_km: Optional[float] = Field(None, gt=0, description="최대 거리 (km)")
    user_location: Optional[LocationInput] = Field(None, description="사용자 위치")
    
    # 태그 필터
    required_tags: Optional[List[str]] = Field(None, description="필수 태그 (AND 조건)")
    excluded_tags: Optional[List[str]] = Field(None, description="제외할 태그")
    
    # 방문 상태 필터
    visit_status: Optional[VisitStatus] = Field(None, description="방문 상태")
    
    # 즐겨찾기 필터
    favorites_only: Optional[bool] = Field(None, description="즐겨찾기만")
    
    # 날짜 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    updated_after: Optional[datetime] = Field(None, description="수정일 이후")
    updated_before: Optional[datetime] = Field(None, description="수정일 이전")
    
    # 커스텀 필터 (고급 사용자용)
    custom_conditions: Optional[List[str]] = Field(None, description="커스텀 SQL 조건")
    
    # 정렬 조건
    sort_criteria: Optional[SortCriteria] = Field(None, description="정렬 조건")

    @validator('price_ranges')
    def validate_price_ranges(cls, v):
        if v:
            for price in v:
                if price < 1 or price > 5:
                    raise ValueError("가격대는 1-5 사이의 값이어야 합니다.")
        return v

    @validator('max_rating')
    def validate_rating_range(cls, v, values):
        if v and 'min_rating' in values and values['min_rating']:
            if v < values['min_rating']:
                raise ValueError("최대 평점은 최소 평점보다 커야 합니다.")
        return v

    @validator('created_before')
    def validate_created_date_range(cls, v, values):
        if v and 'created_after' in values and values['created_after']:
            if v < values['created_after']:
                raise ValueError("생성일 종료 날짜는 시작 날짜보다 나중이어야 합니다.")
        return v

    @validator('custom_conditions')
    def validate_custom_conditions(cls, v):
        if v and len(v) > 3:
            raise ValueError("커스텀 조건은 최대 3개까지 허용됩니다.")
        return v


class FilterStats(BaseModel):
    """필터 통계"""
    total_places: int = Field(..., description="전체 장소 수")
    filtered_count: int = Field(..., description="필터링된 장소 수")
    filter_efficiency: float = Field(..., ge=0, le=1, description="필터 효율성 (0-1)")
    category_distribution: Dict[str, int] = Field(default_factory=dict, description="카테고리별 분포")
    region_distribution: Dict[str, int] = Field(default_factory=dict, description="지역별 분포")


class FilterResult(BaseModel):
    """필터 결과"""
    places: List[Dict[str, Any]] = Field(..., description="필터링된 장소 목록")
    total_count: int = Field(..., description="전체 결과 수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    applied_filters: FilterCriteria = Field(..., description="적용된 필터")
    filter_stats: FilterStats = Field(..., description="필터 통계")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")
    cache_hit: bool = Field(..., description="캐시 히트 여부")


class FilterPresetBase(BaseModel):
    """필터 프리셋 기본"""
    name: str = Field(..., min_length=1, max_length=100, description="프리셋 이름")
    description: Optional[str] = Field(None, max_length=500, description="프리셋 설명")
    criteria: FilterCriteria = Field(..., description="필터 조건")


class FilterPresetCreate(FilterPresetBase):
    """필터 프리셋 생성"""
    pass


class FilterPresetUpdate(BaseModel):
    """필터 프리셋 수정"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="프리셋 이름")
    description: Optional[str] = Field(None, max_length=500, description="프리셋 설명")
    criteria: Optional[FilterCriteria] = Field(None, description="필터 조건")


class FilterPreset(FilterPresetBase):
    """필터 프리셋"""
    id: UUID = Field(..., description="프리셋 ID")
    user_id: UUID = Field(..., description="사용자 ID")
    usage_count: int = Field(0, description="사용 횟수")
    last_used_at: Optional[datetime] = Field(None, description="마지막 사용 시간")
    is_public: bool = Field(False, description="공개 프리셋 여부")
    is_favorite: bool = Field(False, description="즐겨찾기 여부")
    is_auto_generated: bool = Field(False, description="자동 생성 여부")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="신뢰도 점수")
    created_at: datetime = Field(..., description="생성 시간")
    updated_at: datetime = Field(..., description="수정 시간")

    class Config:
        from_attributes = True


class FilterRecommendation(BaseModel):
    """필터 추천"""
    name: str = Field(..., description="추천 이름")
    description: str = Field(..., description="추천 설명")
    criteria: FilterCriteria = Field(..., description="필터 조건")
    confidence_score: float = Field(..., ge=0, le=1, description="추천 신뢰도")
    usage_frequency: int = Field(0, description="사용 빈도")
    recommendation_type: str = Field("personal", description="추천 타입")
    expected_result_count: Optional[int] = Field(None, description="예상 결과 수")


class PersonalizedSortCriteria(BaseModel):
    """개인화 정렬 조건"""
    category_weight: float = Field(0.3, ge=0, le=1, description="카테고리 가중치")
    region_weight: float = Field(0.2, ge=0, le=1, description="지역 가중치")
    price_weight: float = Field(0.15, ge=0, le=1, description="가격 가중치")
    rating_weight: float = Field(0.25, ge=0, le=1, description="평점 가중치")
    distance_weight: float = Field(0.1, ge=0, le=1, description="거리 가중치")
    recency_weight: float = Field(0.0, ge=0, le=1, description="최신성 가중치")
    diversity_factor: float = Field(0.3, ge=0, le=1, description="다양성 팩터")
    direction: SortDirection = Field(SortDirection.DESC, description="정렬 방향")

    @validator('category_weight', 'region_weight', 'price_weight', 'rating_weight', 'distance_weight', 'recency_weight')
    def validate_weights_sum(cls, v, values):
        # 모든 가중치의 합이 1.0에 근사해야 함
        total_weight = sum([
            v,
            values.get('category_weight', 0),
            values.get('region_weight', 0), 
            values.get('price_weight', 0),
            values.get('rating_weight', 0),
            values.get('distance_weight', 0),
            values.get('recency_weight', 0)
        ])
        if total_weight > 1.1:  # 약간의 오차 허용
            raise ValueError("모든 가중치의 합은 1.0 이하여야 합니다.")
        return v


class SearchPreferenceAnalysis(BaseModel):
    """검색 선호도 분석 결과"""
    user_id: UUID = Field(..., description="사용자 ID")
    analysis_period_days: int = Field(..., description="분석 기간 (일)")
    
    # 카테고리 선호도
    category_preferences: Dict[str, float] = Field(default_factory=dict, description="카테고리별 선호도")
    most_preferred_categories: List[str] = Field(default_factory=list, description="선호 카테고리 순위")
    
    # 지역 선호도
    region_preferences: Dict[str, float] = Field(default_factory=dict, description="지역별 선호도")
    most_preferred_regions: List[str] = Field(default_factory=list, description="선호 지역 순위")
    
    # 시간 패턴
    peak_search_hours: List[int] = Field(default_factory=list, description="주요 검색 시간대")
    peak_search_days: List[int] = Field(default_factory=list, description="주요 검색 요일")
    
    # 필터 사용 패턴
    most_used_filters: List[str] = Field(default_factory=list, description="자주 사용하는 필터")
    average_filter_count: float = Field(0, description="평균 필터 사용 개수")
    
    # 성능 지표
    average_response_time_ms: float = Field(0, description="평균 응답 시간")
    cache_hit_rate: float = Field(0, ge=0, le=1, description="캐시 히트율")
    
    # 만족도 지표
    click_through_rate: float = Field(0, ge=0, le=1, description="클릭률")
    average_session_duration: float = Field(0, description="평균 세션 지속 시간")
    search_success_rate: float = Field(0, ge=0, le=1, description="검색 성공률")


class FilterOptimization(BaseModel):
    """필터 최적화 제안"""
    optimization_type: str = Field(..., description="최적화 타입")
    title: str = Field(..., description="제안 제목")
    description: str = Field(..., description="제안 설명")
    current_performance: float = Field(..., description="현재 성능 지표")
    expected_improvement: float = Field(..., description="예상 개선도")
    confidence: float = Field(..., ge=0, le=1, description="신뢰도")
    action_required: str = Field(..., description="필요한 액션")
    estimated_benefit: str = Field(..., description="예상 효과")


class FilterPerformanceMetrics(BaseModel):
    """필터 성능 지표"""
    total_filter_requests: int = Field(0, description="총 필터 요청 수")
    average_processing_time_ms: float = Field(0, description="평균 처리 시간")
    p95_processing_time_ms: float = Field(0, description="95% 처리 시간")
    cache_hit_rate: float = Field(0, ge=0, le=1, description="캐시 히트율")
    error_rate: float = Field(0, ge=0, le=1, description="에러율")
    
    # 필터 효율성
    average_result_reduction_ratio: float = Field(0, ge=0, le=1, description="평균 결과 축소 비율")
    filter_effectiveness_score: float = Field(0, ge=0, le=1, description="필터 효과 점수")
    
    # 사용자 만족도
    user_satisfaction_score: float = Field(0, ge=0, le=1, description="사용자 만족도")
    filter_abandonment_rate: float = Field(0, ge=0, le=1, description="필터 포기율")
    
    # 시간별 분석
    peak_usage_hours: List[int] = Field(default_factory=list, description="피크 사용 시간대")
    performance_by_hour: Dict[str, float] = Field(default_factory=dict, description="시간대별 성능")
    
    # 필터별 성능
    filter_type_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="필터 타입별 성능")
    most_expensive_filters: List[str] = Field(default_factory=list, description="가장 무거운 필터들")
    
    last_updated: datetime = Field(..., description="마지막 업데이트 시간")