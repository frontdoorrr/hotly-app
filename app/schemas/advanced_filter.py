"""
고급 필터링 시스템 스키마 (Task 2-3-3)

검색 필터링을 위한 Pydantic 요청/응답 모델 정의
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class LocationFilter(BaseModel):
    """위치 기반 필터"""
    
    lat: float = Field(..., ge=-90, le=90, description="위도")
    lng: float = Field(..., ge=-180, le=180, description="경도")
    radius_km: Optional[float] = Field(None, ge=0.1, le=50, description="반경 (km)")

    class Config:
        schema_extra = {
            "example": {
                "lat": 37.5563,
                "lng": 126.9225,
                "radius_km": 2.0
            }
        }


class AdvancedFilterRequest(BaseModel):
    """고급 필터링 요청"""
    
    # 기본 검색
    query: Optional[str] = Field(None, max_length=100, description="검색어")
    
    # 카테고리 필터
    categories: Optional[List[str]] = Field(None, description="카테고리 필터 (OR 조건)")
    
    # 지역 필터
    regions: Optional[List[str]] = Field(None, description="지역 필터 (OR 조건)")
    
    # 태그 필터
    tags: Optional[List[str]] = Field(None, description="태그 필터")
    tag_match_mode: str = Field("any", description="태그 매칭 모드 (any/all)")
    
    # 가격 필터
    price_ranges: Optional[List[str]] = Field(None, description="가격대 필터")
    price_min: Optional[int] = Field(None, ge=0, description="최소 가격")
    price_max: Optional[int] = Field(None, ge=0, description="최대 가격")
    
    # 평점 필터
    rating_min: Optional[float] = Field(None, ge=0.0, le=5.0, description="최소 평점")
    rating_max: Optional[float] = Field(None, ge=0.0, le=5.0, description="최대 평점")
    review_count_min: Optional[int] = Field(None, ge=0, description="최소 리뷰 수")
    
    # 방문 상태 필터
    visit_status: Optional[List[str]] = Field(None, description="방문 상태 필터")
    
    # 위치 필터
    location: Optional[LocationFilter] = Field(None, description="위치 기반 필터")
    
    # 시간 필터
    created_after: Optional[datetime] = Field(None, description="생성일 이후")
    created_before: Optional[datetime] = Field(None, description="생성일 이전")
    updated_after: Optional[datetime] = Field(None, description="수정일 이후")
    
    # 정렬 옵션
    sort_by: str = Field("relevance", description="정렬 기준")
    sort_order: str = Field("desc", description="정렬 순서 (asc/desc)")
    
    # 페이지네이션
    limit: int = Field(20, ge=1, le=100, description="결과 개수")
    offset: int = Field(0, ge=0, description="시작 위치")
    
    # 추가 옵션
    include_facets: bool = Field(False, description="패싯 정보 포함")
    highlight: bool = Field(True, description="검색어 하이라이트")
    optimization_mode: bool = Field(False, description="성능 최적화 모드")

    @validator("tag_match_mode")
    def validate_tag_match_mode(cls, v):
        if v not in ["any", "all"]:
            raise ValueError("tag_match_mode must be 'any' or 'all'")
        return v

    @validator("sort_by")
    def validate_sort_by(cls, v):
        valid_sorts = ["relevance", "rating", "recent", "price", "distance", "name", "popular"]
        if v not in valid_sorts:
            raise ValueError(f"sort_by must be one of: {valid_sorts}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v

    @validator("price_max")
    def validate_price_range(cls, v, values):
        if v is not None and "price_min" in values and values["price_min"] is not None:
            if v < values["price_min"]:
                raise ValueError("price_max must be greater than price_min")
        return v

    @validator("rating_max")
    def validate_rating_range(cls, v, values):
        if v is not None and "rating_min" in values and values["rating_min"] is not None:
            if v < values["rating_min"]:
                raise ValueError("rating_max must be greater than rating_min")
        return v

    class Config:
        schema_extra = {
            "example": {
                "query": "홍대 카페",
                "categories": ["cafe"],
                "regions": ["마포구"],
                "tags": ["조용한", "와이파이"],
                "tag_match_mode": "any",
                "price_ranges": ["10000-20000"],
                "rating_min": 4.0,
                "visit_status": ["wishlist"],
                "location": {
                    "lat": 37.5563,
                    "lng": 126.9225,
                    "radius_km": 2.0
                },
                "sort_by": "rating",
                "sort_order": "desc",
                "limit": 20,
                "include_facets": True
            }
        }


class FilteredPlace(BaseModel):
    """필터링된 장소 결과"""
    
    id: str = Field(..., description="장소 ID")
    name: str = Field(..., description="장소명")
    description: Optional[str] = Field(None, description="설명")
    address: Optional[str] = Field(None, description="주소")
    location: Optional[Dict[str, float]] = Field(None, description="위치 좌표")
    category: str = Field(..., description="카테고리")
    tags: List[str] = Field(default_factory=list, description="태그")
    
    # 평가 정보
    rating: Optional[float] = Field(None, description="평점")
    review_count: Optional[int] = Field(None, description="리뷰 수")
    
    # 가격 정보
    price_range: Optional[int] = Field(None, description="가격대")
    
    # 상태 정보
    visit_status: Optional[str] = Field(None, description="방문 상태")
    
    # 시간 정보
    created_at: datetime = Field(..., description="생성일")
    updated_at: Optional[datetime] = Field(None, description="수정일")
    
    # 검색 관련 정보
    relevance_score: Optional[float] = Field(None, description="관련도 점수")
    distance_km: Optional[float] = Field(None, description="거리 (km)")
    
    # 하이라이트 정보
    highlights: Optional[Dict[str, List[str]]] = Field(None, description="하이라이트된 텍스트")

    class Config:
        schema_extra = {
            "example": {
                "id": "place-123",
                "name": "홍대 감성 카페",
                "description": "조용하고 분위기 좋은 카페",
                "address": "서울시 마포구 홍익로 123",
                "location": {"lat": 37.5563, "lng": 126.9225},
                "category": "cafe",
                "tags": ["조용한", "분위기좋은", "와이파이"],
                "rating": 4.5,
                "review_count": 127,
                "price_range": 15000,
                "visit_status": "wishlist",
                "created_at": "2024-01-15T10:30:45.123Z",
                "relevance_score": 2.5,
                "distance_km": 0.8,
                "highlights": {
                    "name": ["<em>홍대</em> 감성 <em>카페</em>"],
                    "description": ["조용하고 분위기 좋은 <em>카페</em>"]
                }
            }
        }


class FacetOption(BaseModel):
    """패싯 옵션"""
    
    name: str = Field(..., description="옵션명")
    count: int = Field(..., description="해당 옵션의 결과 수")
    selected: bool = Field(False, description="현재 선택된 옵션 여부")

    class Config:
        schema_extra = {
            "example": {
                "name": "cafe",
                "count": 25,
                "selected": True
            }
        }


class FilterFacets(BaseModel):
    """필터 패싯 정보"""
    
    categories: List[FacetOption] = Field(default_factory=list, description="카테고리 패싯")
    regions: List[FacetOption] = Field(default_factory=list, description="지역 패싯")
    tags: List[FacetOption] = Field(default_factory=list, description="태그 패싯")
    price_ranges: List[FacetOption] = Field(default_factory=list, description="가격대 패싯")
    visit_status: List[FacetOption] = Field(default_factory=list, description="방문 상태 패싯")
    rating_ranges: List[FacetOption] = Field(default_factory=list, description="평점 구간 패싯")

    class Config:
        schema_extra = {
            "example": {
                "categories": [
                    {"name": "cafe", "count": 25, "selected": True},
                    {"name": "restaurant", "count": 18, "selected": False}
                ],
                "regions": [
                    {"name": "마포구", "count": 15, "selected": True},
                    {"name": "강남구", "count": 12, "selected": False}
                ],
                "price_ranges": [
                    {"name": "10000-20000", "count": 20, "selected": True},
                    {"name": "20000-50000", "count": 15, "selected": False}
                ]
            }
        }


class FilterSuggestions(BaseModel):
    """필터 제안 정보"""
    
    message: str = Field(..., description="제안 메시지")
    alternative_filters: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="대안 필터 조건"
    )
    popular_filters: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="인기 필터 조합"
    )

    class Config:
        schema_extra = {
            "example": {
                "message": "검색 조건을 완화해보세요",
                "alternative_filters": [
                    {"remove_filter": "price_ranges", "description": "가격대 필터 제거"},
                    {"expand_regions": ["서울시"], "description": "지역 범위 확대"}
                ],
                "popular_filters": [
                    {"categories": ["cafe"], "regions": ["홍대"]},
                    {"tags": ["분위기좋은"], "rating_min": 4.0}
                ]
            }
        }


class PaginationInfo(BaseModel):
    """페이지네이션 정보"""
    
    total: int = Field(..., description="전체 결과 수")
    limit: int = Field(..., description="페이지당 결과 수")
    offset: int = Field(..., description="현재 시작 위치")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_previous: bool = Field(..., description="이전 페이지 존재 여부")

    class Config:
        schema_extra = {
            "example": {
                "total": 127,
                "limit": 20,
                "offset": 40,
                "has_next": True,
                "has_previous": True
            }
        }


class PerformanceMetrics(BaseModel):
    """성능 메트릭 정보"""
    
    query_time_ms: int = Field(..., description="쿼리 실행 시간 (ms)")
    total_time_ms: int = Field(..., description="전체 처리 시간 (ms)")
    cache_hit: bool = Field(..., description="캐시 히트 여부")
    optimized: bool = Field(False, description="최적화 모드 적용 여부")
    elasticsearch_took: Optional[int] = Field(None, description="Elasticsearch 실행 시간 (ms)")

    class Config:
        schema_extra = {
            "example": {
                "query_time_ms": 45,
                "total_time_ms": 125,
                "cache_hit": False,
                "optimized": True,
                "elasticsearch_took": 23
            }
        }


class AdvancedFilterResponse(BaseModel):
    """고급 필터링 응답"""
    
    places: List[FilteredPlace] = Field(..., description="필터링된 장소 목록")
    pagination: PaginationInfo = Field(..., description="페이지네이션 정보")
    facets: Optional[FilterFacets] = Field(None, description="패싯 정보")
    suggestions: Optional[FilterSuggestions] = Field(None, description="필터 제안")
    performance: Optional[PerformanceMetrics] = Field(None, description="성능 정보")
    applied_filters: Dict[str, Any] = Field(..., description="적용된 필터 조건")
    query_info: Dict[str, Any] = Field(..., description="쿼리 실행 정보")

    class Config:
        schema_extra = {
            "example": {
                "places": [
                    {
                        "id": "place-123",
                        "name": "홍대 감성 카페",
                        "category": "cafe",
                        "rating": 4.5,
                        "distance_km": 0.8
                    }
                ],
                "pagination": {
                    "total": 127,
                    "limit": 20,
                    "offset": 0,
                    "has_next": True,
                    "has_previous": False
                },
                "facets": {
                    "categories": [
                        {"name": "cafe", "count": 25, "selected": True}
                    ]
                },
                "applied_filters": {
                    "categories": ["cafe"],
                    "regions": ["마포구"]
                },
                "query_info": {
                    "total_hits": 127,
                    "max_score": 3.2,
                    "source": "elasticsearch"
                }
            }
        }


class SavedFilterRequest(BaseModel):
    """저장된 필터 요청"""
    
    name: str = Field(..., max_length=50, description="필터 조합 이름")
    filter_criteria: AdvancedFilterRequest = Field(..., description="필터 조건")
    is_public: bool = Field(False, description="공개 필터 여부")

    class Config:
        schema_extra = {
            "example": {
                "name": "홍대 카페 즐겨찾기",
                "filter_criteria": {
                    "categories": ["cafe"],
                    "regions": ["마포구"],
                    "rating_min": 4.0
                },
                "is_public": False
            }
        }


class SavedFilter(BaseModel):
    """저장된 필터"""
    
    id: str = Field(..., description="저장된 필터 ID")
    name: str = Field(..., description="필터 조합 이름")
    filter_criteria: Dict[str, Any] = Field(..., description="필터 조건")
    is_public: bool = Field(..., description="공개 필터 여부")
    use_count: int = Field(..., description="사용 횟수")
    created_at: datetime = Field(..., description="생성일")
    last_used: Optional[datetime] = Field(None, description="마지막 사용일")

    class Config:
        schema_extra = {
            "example": {
                "id": "filter-123",
                "name": "홍대 카페 즐겨찾기",
                "filter_criteria": {
                    "categories": ["cafe"],
                    "regions": ["마포구"],
                    "rating_min": 4.0
                },
                "is_public": False,
                "use_count": 15,
                "created_at": "2024-01-15T10:30:45.123Z",
                "last_used": "2024-01-20T15:45:30.456Z"
            }
        }


class FilterAnalytics(BaseModel):
    """필터 사용 분석"""
    
    popular_filters: List[Dict[str, Any]] = Field(..., description="인기 필터 조합")
    filter_effectiveness: Dict[str, float] = Field(..., description="필터별 효과성")
    user_behavior: Dict[str, Any] = Field(..., description="사용자 필터 사용 패턴")
    performance_stats: Dict[str, Any] = Field(..., description="필터 성능 통계")

    class Config:
        schema_extra = {
            "example": {
                "popular_filters": [
                    {"combination": ["cafe", "홍대"], "usage_count": 156},
                    {"combination": ["restaurant", "강남"], "usage_count": 134}
                ],
                "filter_effectiveness": {
                    "category": 0.85,
                    "region": 0.92,
                    "rating": 0.78
                },
                "user_behavior": {
                    "avg_filters_per_search": 2.3,
                    "most_combined_filters": ["category", "region"]
                },
                "performance_stats": {
                    "avg_response_time": 145,
                    "cache_hit_rate": 0.67
                }
            }
        }