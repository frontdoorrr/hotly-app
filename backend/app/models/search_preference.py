"""
검색 선호도 모델 (Task 2-3-3)

사용자별 검색 필터 설정, 정렬 프리셋, 검색 기록을 저장하는 데이터 모델
- 필터 프리셋 저장 및 관리
- 정렬 선호도 추적
- 검색 패턴 분석을 위한 히스토리
- 개인화 추천을 위한 사용자 행동 데이터
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class FilterPreset(Base):
    """필터 프리셋 모델"""
    
    __tablename__ = "filter_presets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 프리셋 이름
    description = Column(Text)  # 프리셋 설명
    
    # 필터 조건 (JSON으로 저장)
    criteria = Column(JSON, nullable=False)
    
    # 사용 통계
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # 공개 설정
    is_public = Column(Boolean, default=False)  # 다른 사용자와 공유 가능
    is_favorite = Column(Boolean, default=False)  # 즐겨찾기 프리셋
    
    # 자동 생성 여부 (시스템이 사용자 패턴을 보고 자동 생성)
    is_auto_generated = Column(Boolean, default=False)
    confidence_score = Column(Float)  # 자동 생성된 경우의 신뢰도
    
    # 메타데이터
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="filter_presets")


class SortPreset(Base):
    """정렬 프리셋 모델"""
    
    __tablename__ = "sort_presets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 프리셋 이름
    description = Column(Text)  # 프리셋 설명
    
    # 정렬 조건 (JSON으로 저장)
    criteria = Column(JSON, nullable=False)
    
    # 컨텍스트 정보
    context = Column(String(50))  # morning, lunch, evening, weekend 등
    
    # 사용 통계
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    # 개인화 설정
    is_personalized = Column(Boolean, default=False)  # 개인화 정렬 사용 여부
    diversity_factor = Column(Float, default=0.3)  # 다양성 팩터 (0.0~1.0)
    
    # 메타데이터
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계
    user = relationship("User", back_populates="sort_presets")


class SearchHistory(Base):
    """검색 히스토리 모델"""
    
    __tablename__ = "search_histories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 검색 정보
    query = Column(String(500))  # 검색어
    filter_criteria = Column(JSON)  # 적용된 필터
    sort_criteria = Column(JSON)  # 적용된 정렬
    
    # 검색 결과
    result_count = Column(Integer, default=0)
    clicked_results = Column(JSON, default=list)  # 클릭한 결과들의 ID 목록
    
    # 사용자 컨텍스트
    user_location = Column(JSON)  # 검색 시점의 사용자 위치 {"lat": float, "lng": float}
    device_type = Column(String(50))  # mobile, desktop, tablet
    
    # 시간 정보
    search_timestamp = Column(DateTime, default=func.now(), index=True)
    session_id = Column(String(100))  # 세션 추적용
    
    # 성능 메트릭
    response_time_ms = Column(Integer)  # 응답 시간 (밀리초)
    cache_hit = Column(Boolean, default=False)  # 캐시 히트 여부
    
    # 사용자 행동
    dwell_time_seconds = Column(Integer)  # 결과 페이지 머문 시간
    bounce_rate = Column(Float)  # 바운스율 (즉시 떠남 = 1.0)
    
    # 관계
    user = relationship("User", back_populates="search_histories")


class UserSearchPattern(Base):
    """사용자 검색 패턴 분석 모델"""
    
    __tablename__ = "user_search_patterns"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 분석 기간
    analysis_period_start = Column(DateTime, nullable=False)
    analysis_period_end = Column(DateTime, nullable=False)
    
    # 카테고리 선호도 패턴
    category_preferences = Column(JSON, default=dict)  # {"cafe": 0.4, "restaurant": 0.3, ...}
    category_search_frequency = Column(JSON, default=dict)  # 카테고리별 검색 빈도
    
    # 지역 선호도 패턴
    region_preferences = Column(JSON, default=dict)  # {"홍대": 0.3, "강남": 0.2, ...}
    region_search_frequency = Column(JSON, default=dict)  # 지역별 검색 빈도
    
    # 시간대별 검색 패턴
    hourly_search_pattern = Column(JSON, default=dict)  # 시간대별 검색 활동
    daily_search_pattern = Column(JSON, default=dict)  # 요일별 검색 활동
    
    # 필터 사용 패턴
    most_used_filters = Column(JSON, default=list)  # 자주 사용하는 필터 조합
    filter_combination_frequency = Column(JSON, default=dict)  # 필터 조합별 빈도
    
    # 정렬 선호도 패턴
    preferred_sort_fields = Column(JSON, default=list)  # 선호하는 정렬 기준
    sort_usage_frequency = Column(JSON, default=dict)  # 정렬별 사용 빈도
    
    # 검색 행동 패턴
    average_query_length = Column(Float)  # 평균 검색어 길이
    average_results_viewed = Column(Float)  # 평균 조회 결과 수
    average_click_position = Column(Float)  # 평균 클릭 위치
    search_refinement_rate = Column(Float)  # 검색 재실행율
    
    # 만족도 지표
    overall_satisfaction_score = Column(Float)  # 전체 만족도 (0.0~1.0)
    click_through_rate = Column(Float)  # 클릭률
    average_dwell_time = Column(Float)  # 평균 머문 시간
    
    # 개인화 효과
    personalization_effectiveness = Column(Float)  # 개인화 효과 측정
    diversity_preference = Column(Float)  # 다양성 선호도 (0.0~1.0)
    
    # 메타데이터
    total_searches = Column(Integer, default=0)  # 분석 기간 내 총 검색 수
    pattern_confidence = Column(Float)  # 패턴 분석 신뢰도
    last_updated = Column(DateTime, default=func.now())
    
    # 관계
    user = relationship("User", back_populates="search_patterns")


class FilterRecommendation(Base):
    """필터 추천 모델"""
    
    __tablename__ = "filter_recommendations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # 추천 정보
    name = Column(String(100), nullable=False)  # 추천 이름
    description = Column(Text)  # 추천 설명
    criteria = Column(JSON, nullable=False)  # 필터 조건
    
    # 추천 메타데이터
    recommendation_type = Column(String(50))  # trend, personal, seasonal, location_based
    confidence_score = Column(Float, nullable=False)  # 추천 신뢰도 (0.0~1.0)
    expected_result_count = Column(Integer)  # 예상 결과 수
    
    # 추천 근거
    reasoning = Column(Text)  # 추천 이유
    based_on_patterns = Column(JSON)  # 근거가 된 패턴들
    
    # 사용자 피드백
    was_used = Column(Boolean, default=False)  # 사용 여부
    user_rating = Column(Float)  # 사용자 평가 (1.0~5.0)
    feedback_comments = Column(Text)  # 피드백 코멘트
    
    # 성능 메트릭
    actual_result_count = Column(Integer)  # 실제 결과 수
    user_satisfaction = Column(Float)  # 사용자 만족도
    click_through_rate = Column(Float)  # 클릭률
    
    # 유효성
    is_active = Column(Boolean, default=True)  # 활성 상태
    expires_at = Column(DateTime)  # 만료일 (시즌성 추천의 경우)
    
    # 메타데이터
    created_at = Column(DateTime, default=func.now())
    last_shown_at = Column(DateTime)  # 마지막 노출 시간
    times_shown = Column(Integer, default=0)  # 노출 횟수
    
    # 관계
    user = relationship("User", back_populates="filter_recommendations")


class SearchSessionAnalytics(Base):
    """검색 세션 분석 모델"""
    
    __tablename__ = "search_session_analytics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)  # 세션 ID
    
    # 세션 정보
    session_start = Column(DateTime, nullable=False)
    session_end = Column(DateTime)
    total_duration_seconds = Column(Integer)
    
    # 검색 활동
    total_searches = Column(Integer, default=0)
    unique_queries = Column(Integer, default=0)
    queries_list = Column(JSON, default=list)  # 검색어 목록
    
    # 필터/정렬 사용
    filters_used = Column(JSON, default=list)  # 사용된 필터 목록
    sorts_used = Column(JSON, default=list)  # 사용된 정렬 목록
    filter_changes = Column(Integer, default=0)  # 필터 변경 횟수
    
    # 결과 상호작용
    total_results_viewed = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    clicked_positions = Column(JSON, default=list)  # 클릭한 위치들
    
    # 세션 성공 지표
    session_success = Column(Boolean)  # 세션 성공 여부 (목표 달성)
    bounce_session = Column(Boolean)  # 바운스 세션 여부
    conversion_action = Column(String(100))  # 전환 액션 (place_detail, save, visit)
    
    # 디바이스/컨텍스트
    device_type = Column(String(50))
    browser_info = Column(JSON)
    location_context = Column(JSON)  # 위치 컨텍스트
    
    # 성능 메트릭
    average_response_time = Column(Float)  # 평균 응답 시간
    cache_hit_rate = Column(Float)  # 캐시 히트율
    error_count = Column(Integer, default=0)  # 오류 발생 횟수
    
    # 관계
    user = relationship("User", back_populates="search_session_analytics")