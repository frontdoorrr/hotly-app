"""
자동완성 API 스키마 (Task 2-3-2)

자동완성 요청/응답 모델 정의
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class SuggestionItem(BaseModel):
    """검색 제안 항목"""

    text: str = Field(..., description="제안 텍스트")
    type: str = Field(
        ..., description="제안 유형 (personal_history, trending, popular_place, etc.)"
    )
    score: float = Field(..., ge=0.0, description="관련도 점수")
    category: Optional[str] = Field(None, description="카테고리")
    address: Optional[str] = Field(None, description="주소")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")

    class Config:
        schema_extra = {
            "example": {
                "text": "홍대 카페",
                "type": "trending",
                "score": 2.5,
                "category": "cafe",
                "address": "서울시 마포구",
                "metadata": {"source": "trending", "trend_score": 15.2},
            }
        }


class AutocompleteRequest(BaseModel):
    """자동완성 요청"""

    query: str = Field(..., min_length=1, max_length=100, description="검색 쿼리")
    limit: int = Field(default=10, ge=1, le=20, description="제안 개수 제한")
    include_personal: bool = Field(default=True, description="개인화 제안 포함")
    include_trending: bool = Field(default=True, description="트렌딩 제안 포함")
    include_popular: bool = Field(default=True, description="인기 제안 포함")
    categories: Optional[List[str]] = Field(None, description="카테고리 필터")
    location: Optional[Dict[str, float]] = Field(None, description="위치 정보 {lat, lng}")

    @validator("location")
    def validate_location(cls, v):
        if v is not None:
            if not isinstance(v, dict):
                raise ValueError("location must be a dictionary")
            if "lat" not in v or "lng" not in v:
                raise ValueError("location must contain 'lat' and 'lng' keys")
            if not (-90 <= v["lat"] <= 90):
                raise ValueError("latitude must be between -90 and 90")
            if not (-180 <= v["lng"] <= 180):
                raise ValueError("longitude must be between -180 and 180")
        return v

    class Config:
        schema_extra = {
            "example": {
                "query": "홍대",
                "limit": 10,
                "include_personal": True,
                "include_trending": True,
                "include_popular": True,
                "categories": ["cafe", "restaurant"],
                "location": {"lat": 37.5563, "lng": 126.9225},
            }
        }


class AutocompleteResponse(BaseModel):
    """자동완성 응답"""

    suggestions: List[SuggestionItem] = Field(..., description="제안 목록")
    categories: Dict[str, List[SuggestionItem]] = Field(
        default_factory=dict, description="카테고리별 제안 분류"
    )
    total: int = Field(..., ge=0, description="전체 제안 개수")
    query: str = Field(..., description="원본 검색 쿼리")
    timestamp: str = Field(..., description="응답 생성 시간")

    class Config:
        schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "text": "홍대 카페",
                        "type": "trending",
                        "score": 3.2,
                        "category": "cafe",
                        "metadata": {"source": "trending"},
                    }
                ],
                "categories": {
                    "trending": [
                        {
                            "text": "홍대 카페",
                            "type": "trending",
                            "score": 3.2,
                            "category": "cafe",
                            "metadata": {"source": "trending"},
                        }
                    ]
                },
                "total": 1,
                "query": "홍대",
                "timestamp": "2024-01-15T10:30:45.123Z",
            }
        }


class TrendingSearchItem(BaseModel):
    """트렌딩 검색어 항목"""

    query: str = Field(..., description="검색어")
    count: int = Field(..., ge=0, description="검색 횟수")
    type: str = Field(default="trending", description="항목 유형")

    class Config:
        schema_extra = {"example": {"query": "홍대 맛집", "count": 152, "type": "trending"}}


class PersonalSearchHistoryItem(BaseModel):
    """개인 검색 기록 항목"""

    query: str = Field(..., description="검색어")
    frequency: int = Field(..., ge=1, description="검색 빈도")
    last_searched: Optional[str] = Field(None, description="마지막 검색 시간")
    type: str = Field(default="personal_history", description="항목 유형")

    class Config:
        schema_extra = {
            "example": {
                "query": "강남 이탈리안",
                "frequency": 3,
                "last_searched": "2024-01-15T09:45:30.123Z",
                "type": "personal_history",
            }
        }


class SearchAnalyticsResponse(BaseModel):
    """검색 분석 응답"""

    trending_searches: List[TrendingSearchItem] = Field(
        default_factory=list, description="트렌딩 검색어"
    )
    popular_categories: Dict[str, int] = Field(
        default_factory=dict, description="인기 카테고리별 검색 횟수"
    )
    user_search_patterns: Dict[str, Any] = Field(
        default_factory=dict, description="사용자 검색 패턴"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="성능 메트릭"
    )
    timestamp: str = Field(..., description="분석 생성 시간")

    class Config:
        schema_extra = {
            "example": {
                "trending_searches": [
                    {"query": "홍대 맛집", "count": 152, "type": "trending"}
                ],
                "popular_categories": {"cafe": 245, "restaurant": 187, "bar": 98},
                "user_search_patterns": {
                    "recent_searches": [
                        {
                            "query": "강남 카페",
                            "frequency": 2,
                            "last_searched": "2024-01-15T09:30:00.123Z",
                        }
                    ]
                },
                "performance_metrics": {
                    "average_response_time_ms": 45.2,
                    "cache_hit_rate": 0.85,
                },
                "timestamp": "2024-01-15T10:30:45.123Z",
            }
        }


class CacheOptimizationResult(BaseModel):
    """캐시 최적화 결과"""

    status: str = Field(..., description="최적화 상태")
    cleanup_stats: Dict[str, int] = Field(default_factory=dict, description="정리 통계")
    timestamp: str = Field(..., description="최적화 실행 시간")

    class Config:
        schema_extra = {
            "example": {
                "status": "completed",
                "cleanup_stats": {
                    "cleaned_users": 15,
                    "cleaned_trending": 3,
                    "optimized_cache": 45,
                },
                "timestamp": "2024-01-15T10:30:45.123Z",
            }
        }


class AutocompleteHealthResponse(BaseModel):
    """자동완성 서비스 헬스체크 응답"""

    status: str = Field(..., description="전체 서비스 상태")
    services: Dict[str, str] = Field(..., description="각 서비스별 상태")
    timestamp: str = Field(..., description="헬스체크 실행 시간")
    error: Optional[str] = Field(None, description="에러 메시지")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "elasticsearch": "green",
                },
                "timestamp": "2024-01-15T10:30:45.123Z",
            }
        }
