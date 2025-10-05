"""
검색 최적화 및 성능 관련 Pydantic 스키마

이 모듈은 검색 UI/UX 최적화 및 성능 모니터링을 위한 데이터 모델을 정의합니다.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SearchCacheStrategy(str, Enum):
    """검색 캐시 전략"""
    CONSERVATIVE = "conservative"  # 보수적 캐싱 (짧은 TTL)
    BALANCED = "balanced"         # 균형 캐싱 (중간 TTL)
    AGGRESSIVE = "aggressive"     # 적극적 캐싱 (긴 TTL)


class SearchOptimizationConfig(BaseModel):
    """검색 최적화 설정"""
    enable_thumbnail_optimization: bool = Field(default=True, description="썸네일 최적화 활성화")
    max_description_length: int = Field(default=100, description="설명 최대 길이")
    enable_tag_filtering: bool = Field(default=True, description="태그 필터링 활성화")
    response_compression: bool = Field(default=False, description="응답 압축 활성화")
    cache_strategy: SearchCacheStrategy = Field(default=SearchCacheStrategy.BALANCED)
    
    @validator('max_description_length')
    def validate_description_length(cls, v):
        if v < 10 or v > 500:
            raise ValueError('설명 길이는 10-500자 사이여야 합니다')
        return v


class PaginationRequest(BaseModel):
    """페이지네이션 요청"""
    page: int = Field(default=1, ge=1, description="페이지 번호")
    page_size: int = Field(default=20, ge=1, le=100, description="페이지 크기")
    enable_cursor_pagination: bool = Field(default=False, description="커서 페이지네이션 사용")
    cursor: Optional[str] = Field(default=None, description="페이지네이션 커서")
    preload_next_page: bool = Field(default=False, description="다음 페이지 미리로드")


class PaginationResponse(BaseModel):
    """페이지네이션 응답"""
    current_page: int = Field(description="현재 페이지")
    page_size: int = Field(description="페이지 크기")
    total_pages: int = Field(description="전체 페이지 수")
    total_items: int = Field(description="전체 아이템 수")
    has_next: bool = Field(description="다음 페이지 존재 여부")
    has_previous: bool = Field(description="이전 페이지 존재 여부")
    next_cursor: Optional[str] = Field(default=None, description="다음 페이지 커서")
    previous_cursor: Optional[str] = Field(default=None, description="이전 페이지 커서")


class SearchPerformanceMetrics(BaseModel):
    """검색 성능 메트릭"""
    session_id: str = Field(description="검색 세션 ID")
    query: str = Field(description="검색 쿼리")
    response_time_ms: float = Field(description="응답 시간 (밀리초)")
    result_count: int = Field(description="검색 결과 수")
    cache_hit: bool = Field(description="캐시 히트 여부")
    user_id: UUID = Field(description="사용자 ID")
    timestamp: datetime = Field(description="측정 시간")
    error_occurred: bool = Field(default=False, description="오류 발생 여부")
    error_message: Optional[str] = Field(default=None, description="오류 메시지")
    
    # 추가 성능 지표
    database_query_time_ms: Optional[float] = Field(default=None, description="DB 쿼리 시간")
    elasticsearch_query_time_ms: Optional[float] = Field(default=None, description="ES 쿼리 시간")
    cache_operation_time_ms: Optional[float] = Field(default=None, description="캐시 작업 시간")
    
    @validator('response_time_ms')
    def validate_response_time(cls, v):
        if v < 0:
            raise ValueError('응답 시간은 0 이상이어야 합니다')
        return v


class SearchOptimizedResponse(BaseModel):
    """최적화된 검색 응답"""
    items: List[Dict[str, Any]] = Field(description="검색 결과 아이템")
    pagination: PaginationResponse = Field(description="페이지네이션 정보")
    optimization_applied: List[str] = Field(description="적용된 최적화 목록")
    response_time_ms: float = Field(description="응답 시간")
    cache_hit: bool = Field(description="캐시 히트 여부")
    
    # 무한 스크롤 지원
    next_cursor: Optional[str] = Field(default=None, description="다음 페이지 커서")
    has_more: bool = Field(default=False, description="더 많은 결과 존재 여부")
    preloaded_next: Optional[List[Dict[str, Any]]] = Field(default=None, description="미리로드된 다음 페이지")


class AutocompleteRequest(BaseModel):
    """자동완성 요청"""
    partial_query: str = Field(min_length=1, max_length=100, description="부분 쿼리")
    max_suggestions: int = Field(default=5, ge=1, le=20, description="최대 제안 수")
    user_id: Optional[UUID] = Field(default=None, description="사용자 ID")
    enable_personalization: bool = Field(default=True, description="개인화 활성화")
    include_popular: bool = Field(default=True, description="인기 검색어 포함")
    
    @validator('partial_query')
    def validate_partial_query(cls, v):
        if not v.strip():
            raise ValueError('검색어는 공백일 수 없습니다')
        return v.strip()


class AutocompleteResponse(BaseModel):
    """자동완성 응답"""
    suggestions: List[str] = Field(description="자동완성 제안")
    is_personalized: bool = Field(description="개인화 적용 여부")
    cache_hit: bool = Field(description="캐시 히트 여부")
    response_time_ms: float = Field(description="응답 시간")


class SearchAnalytics(BaseModel):
    """검색 분석 결과"""
    avg_response_time: float = Field(description="평균 응답 시간")
    cache_hit_rate: float = Field(description="캐시 히트율")
    total_searches: int = Field(description="총 검색 수")
    performance_trend: str = Field(description="성능 트렌드 (improving/stable/declining)")
    
    # 시간대별 분석
    hourly_stats: Optional[Dict[str, float]] = Field(default=None, description="시간대별 통계")
    daily_stats: Optional[Dict[str, float]] = Field(default=None, description="일별 통계")
    
    # 쿼리 분석
    popular_queries: List[Dict[str, Union[str, int]]] = Field(description="인기 검색어")
    slow_queries: List[Dict[str, Union[str, float]]] = Field(description="느린 검색어")
    
    @validator('cache_hit_rate')
    def validate_cache_hit_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('캐시 히트율은 0과 1 사이여야 합니다')
        return v


class PerformanceAlert(BaseModel):
    """성능 알림"""
    alert_id: str = Field(description="알림 ID")
    metric: str = Field(description="알림 메트릭 (response_time/cache_hit_rate/error_rate)")
    threshold_value: float = Field(description="임계값")
    actual_value: float = Field(description="실제 값")
    severity: str = Field(description="심각도 (low/medium/high/critical)")
    message: str = Field(description="알림 메시지")
    timestamp: datetime = Field(description="알림 시간")
    resolved: bool = Field(default=False, description="해결 여부")


class SearchSessionInfo(BaseModel):
    """검색 세션 정보"""
    session_id: str = Field(description="세션 ID")
    user_id: UUID = Field(description="사용자 ID")
    start_time: datetime = Field(description="시작 시간")
    query_count: int = Field(default=0, description="쿼리 수")
    total_response_time: float = Field(default=0.0, description="총 응답 시간")
    cache_hits: int = Field(default=0, description="캐시 히트 수")
    last_activity: datetime = Field(description="마지막 활동 시간")


class InfiniteScrollRequest(BaseModel):
    """무한 스크롤 요청"""
    query: str = Field(description="검색 쿼리")
    cursor: Optional[str] = Field(default=None, description="스크롤 커서")
    page_size: int = Field(default=20, ge=1, le=50, description="페이지 크기")
    user_id: Optional[UUID] = Field(default=None, description="사용자 ID")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="검색 필터")


class InfiniteScrollResponse(BaseModel):
    """무한 스크롤 응답"""
    items: List[Dict[str, Any]] = Field(description="검색 결과")
    next_cursor: Optional[str] = Field(default=None, description="다음 커서")
    has_more: bool = Field(description="더 많은 결과 존재 여부")
    total_loaded: int = Field(description="현재까지 로드된 총 아이템 수")
    response_time_ms: float = Field(description="응답 시간")


class SearchUIConfig(BaseModel):
    """검색 UI 설정"""
    enable_autocomplete: bool = Field(default=True, description="자동완성 활성화")
    autocomplete_delay_ms: int = Field(default=300, description="자동완성 지연 시간")
    min_query_length: int = Field(default=2, description="최소 쿼리 길이")
    enable_search_history: bool = Field(default=True, description="검색 기록 활성화")
    enable_infinite_scroll: bool = Field(default=False, description="무한 스크롤 활성화")
    results_per_page: int = Field(default=20, description="페이지당 결과 수")
    enable_performance_monitoring: bool = Field(default=True, description="성능 모니터링 활성화")
    
    @validator('autocomplete_delay_ms')
    def validate_autocomplete_delay(cls, v):
        if v < 100 or v > 1000:
            raise ValueError('자동완성 지연 시간은 100-1000ms 사이여야 합니다')
        return v


class SearchHistoryItem(BaseModel):
    """검색 히스토리 아이템"""
    query: str = Field(description="검색 쿼리")
    timestamp: datetime = Field(description="검색 시간")
    result_count: int = Field(description="결과 수")
    count: int = Field(default=1, description="검색 횟수")


class SearchHistoryResponse(BaseModel):
    """검색 히스토리 응답"""
    history: List[SearchHistoryItem] = Field(description="검색 히스토리")
    total: int = Field(description="총 히스토리 수")
    user_id: UUID = Field(description="사용자 ID")


class PopularQuery(BaseModel):
    """인기 검색어"""
    query: str = Field(description="검색 쿼리")
    count: int = Field(description="검색 횟수")
    rank: int = Field(description="순위")
    trend: Optional[str] = Field(default=None, description="트렌드 (rising/falling/stable)")


class PopularQueriesResponse(BaseModel):
    """인기 검색어 응답"""
    popular_queries: List[PopularQuery] = Field(description="인기 검색어 목록")
    total: int = Field(description="총 개수")
    updated_at: datetime = Field(description="업데이트 시간")


class RealtimeSearchResponse(BaseModel):
    """실시간 검색 응답"""
    results: List[Dict[str, Any]] = Field(description="검색 결과")
    suggestions: List[str] = Field(description="자동완성 제안")
    query_time: float = Field(description="쿼리 시간 (ms)")
    cache_hit: bool = Field(description="캐시 히트 여부")
    total_found: int = Field(description="총 결과 수")
    search_type: str = Field(description="검색 타입")


class SearchFeedback(BaseModel):
    """검색 피드백"""
    query: str = Field(description="검색 쿼리")
    rating: int = Field(ge=1, le=5, description="평점 (1-5)")
    feedback_type: str = Field(description="피드백 유형")
    comments: Optional[str] = Field(default=None, description="추가 의견")
    user_id: UUID = Field(description="사용자 ID")
    timestamp: datetime = Field(description="피드백 시간")


class SearchABTestVariant(BaseModel):
    """검색 A/B 테스트 변형"""
    variant: str = Field(description="변형 ID (control/variant_a/variant_b)")
    assigned_at: datetime = Field(description="할당 시간")
    user_id: UUID = Field(description="사용자 ID")


class SearchCacheInfo(BaseModel):
    """검색 캐시 정보"""
    cache_key: str = Field(description="캐시 키")
    ttl: int = Field(description="TTL (초)")
    size_bytes: Optional[int] = Field(default=None, description="캐시 크기 (바이트)")
    hit_count: int = Field(default=0, description="히트 횟수")
    created_at: datetime = Field(description="생성 시간")
    last_accessed: Optional[datetime] = Field(default=None, description="마지막 접근 시간")


class SearchPerformanceStats(BaseModel):
    """검색 성능 통계"""
    average_response_time: float = Field(description="평균 응답 시간 (ms)")
    p50_response_time: float = Field(description="50% 응답 시간 (ms)")
    p90_response_time: float = Field(description="90% 응답 시간 (ms)")
    p95_response_time: float = Field(description="95% 응답 시간 (ms)")
    cache_hit_rate: float = Field(description="캐시 히트율 (%)")
    total_searches: int = Field(description="총 검색 수")
    error_rate: float = Field(description="오류율 (%)")
    daily_stats: List[Dict[str, Any]] = Field(description="일별 통계")


class SearchUIOptimizationReport(BaseModel):
    """검색 UI 최적화 리포트"""
    user_id: UUID = Field(description="사용자 ID")
    report_period: str = Field(description="리포트 기간")
    total_searches: int = Field(description="총 검색 수")
    average_session_duration: float = Field(description="평균 세션 시간 (초)")
    bounce_rate: float = Field(description="이탈률 (%)")
    conversion_rate: float = Field(description="전환율 (%)")
    
    # UI 상호작용 메트릭
    autocomplete_usage_rate: float = Field(description="자동완성 사용률 (%)")
    infinite_scroll_usage_rate: float = Field(description="무한스크롤 사용률 (%)")
    filter_usage_rate: float = Field(description="필터 사용률 (%)")
    
    # 성능 메트릭
    performance_stats: SearchPerformanceStats = Field(description="성능 통계")
    
    # 추천 사항
    recommendations: List[str] = Field(description="UI 최적화 추천 사항")


class SearchExperimentConfig(BaseModel):
    """검색 실험 설정"""
    experiment_id: str = Field(description="실험 ID")
    name: str = Field(description="실험 이름")
    description: str = Field(description="실험 설명")
    start_date: datetime = Field(description="시작 날짜")
    end_date: datetime = Field(description="종료 날짜")
    
    # 실험 변형
    control_config: Dict[str, Any] = Field(description="컨트롤 그룹 설정")
    variant_configs: List[Dict[str, Any]] = Field(description="변형 그룹 설정들")
    
    # 실험 메트릭
    primary_metric: str = Field(description="주요 메트릭")
    secondary_metrics: List[str] = Field(description="보조 메트릭들")
    
    # 트래픽 분배
    traffic_allocation: Dict[str, float] = Field(description="트래픽 분배 비율")
    
    is_active: bool = Field(default=True, description="실험 활성화 상태")


class SearchHeatmapData(BaseModel):
    """검색 히트맵 데이터"""
    query: str = Field(description="검색 쿼리")
    hour: int = Field(ge=0, le=23, description="시간 (0-23)")
    day_of_week: int = Field(ge=0, le=6, description="요일 (0=월요일)")
    search_count: int = Field(description="검색 횟수")
    average_response_time: float = Field(description="평균 응답 시간")
    success_rate: float = Field(description="성공률")


class SearchTrendAnalysis(BaseModel):
    """검색 트렌드 분석"""
    period: str = Field(description="분석 기간")
    trending_queries: List[PopularQuery] = Field(description="트렌딩 검색어")
    declining_queries: List[PopularQuery] = Field(description="하락 검색어")
    seasonal_patterns: Dict[str, List[float]] = Field(description="계절성 패턴")
    user_behavior_insights: List[str] = Field(description="사용자 행동 인사이트")


class SearchErrorAnalysis(BaseModel):
    """검색 오류 분석"""
    error_type: str = Field(description="오류 유형")
    error_count: int = Field(description="오류 횟수")
    error_rate: float = Field(description="오류율 (%)")
    affected_queries: List[str] = Field(description="영향받은 쿼리들")
    error_patterns: List[Dict[str, Any]] = Field(description="오류 패턴")
    suggested_fixes: List[str] = Field(description="해결 방안")


class SearchPersonalizationProfile(BaseModel):
    """검색 개인화 프로필"""
    user_id: UUID = Field(description="사용자 ID")
    search_preferences: Dict[str, Any] = Field(description="검색 선호도")
    frequent_categories: List[str] = Field(description="자주 검색하는 카테고리")
    preferred_locations: List[Dict[str, Any]] = Field(description="선호 위치")
    search_patterns: Dict[str, Any] = Field(description="검색 패턴")
    last_updated: datetime = Field(description="마지막 업데이트")


class SearchQualityScore(BaseModel):
    """검색 품질 점수"""
    query: str = Field(description="검색 쿼리")
    relevance_score: float = Field(ge=0, le=1, description="관련성 점수")
    diversity_score: float = Field(ge=0, le=1, description="다양성 점수")
    freshness_score: float = Field(ge=0, le=1, description="신선도 점수")
    overall_score: float = Field(ge=0, le=1, description="전체 점수")
    factors: Dict[str, float] = Field(description="점수 구성 요소")


class SearchMonitoringAlert(BaseModel):
    """검색 모니터링 알림"""
    alert_id: str = Field(description="알림 ID")
    alert_type: str = Field(description="알림 유형")
    severity: str = Field(description="심각도")
    title: str = Field(description="알림 제목")
    message: str = Field(description="알림 메시지")
    metric_name: str = Field(description="메트릭 이름")
    current_value: float = Field(description="현재 값")
    threshold_value: float = Field(description="임계값")
    created_at: datetime = Field(description="생성 시간")
    resolved_at: Optional[datetime] = Field(default=None, description="해결 시간")
    actions_taken: List[str] = Field(default_factory=list, description="취한 조치들")
