"""
검색 랭킹 및 개인화 스키마 (Task 2-3-4)

Pydantic 모델로 요청/응답 스키마 정의
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class RankingFactorType(str, Enum):
    """랭킹 요소 타입"""

    BASE_RELEVANCE = "base_relevance"
    PERSONALIZATION = "personalization"
    BEHAVIOR_SCORE = "behavior_score"
    CONTEXTUAL = "contextual"
    ML_SCORE = "ml_score"
    REAL_TIME = "real_time"


class FeedbackType(str, Enum):
    """사용자 피드백 타입"""

    CLICK = "click"
    VIEW = "view"
    BOOKMARK = "bookmark"
    VISIT = "visit"
    SHARE = "share"
    SKIP = "skip"
    NEGATIVE = "negative"


class SearchContextType(str, Enum):
    """검색 컨텍스트 타입"""

    TEXT_SEARCH = "text_search"
    LOCATION_BASED = "location_based"
    CATEGORY_BROWSE = "category_browse"
    RECOMMENDATION = "recommendation"
    VOICE_SEARCH = "voice_search"


class RankingContext(BaseModel):
    """랭킹 컨텍스트"""

    search_type: SearchContextType = SearchContextType.TEXT_SEARCH
    location: Optional[Dict[str, float]] = Field(None, description="사용자 위치 {lat, lng}")
    time_of_search: Optional[datetime] = Field(None, description="검색 시점")
    day_of_week: Optional[str] = Field(None, description="요일")
    weather: Optional[str] = Field(None, description="날씨 정보")
    device_type: Optional[str] = Field(None, description="디바이스 타입")
    session_context: Optional[Dict[str, Any]] = Field(None, description="세션 컨텍스트")
    ab_test_variant: Optional[str] = Field(None, description="A/B 테스트 변형")
    optimization_mode: bool = Field(False, description="성능 최적화 모드")
    explain_ranking: bool = Field(False, description="랭킹 설명 포함")
    diversity_enabled: bool = Field(True, description="다양성 주입 활성화")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "search_type": "text_search",
                "location": {"lat": 37.5563, "lng": 126.9225},
                "time_of_search": "2024-01-15T14:30:00Z",
                "day_of_week": "monday",
                "weather": "sunny",
                "device_type": "mobile",
                "optimization_mode": False,
                "explain_ranking": True,
                "diversity_enabled": True,
            }
        }


class RankingFactor(BaseModel):
    """랭킹 요소"""

    factor_type: RankingFactorType
    weight: float = Field(..., ge=0.0, le=1.0, description="가중치")
    score: float = Field(..., ge=0.0, le=1.0, description="점수")
    contribution: float = Field(..., description="최종 점수 기여도")
    explanation: Optional[str] = Field(None, description="요소 설명")

    class Config:
        schema_extra = {
            "example": {
                "factor_type": "personalization",
                "weight": 0.3,
                "score": 0.85,
                "contribution": 0.255,
                "explanation": "카페 카테고리에 대한 높은 선호도",
            }
        }


class RankedSearchResult(BaseModel):
    """랭킹된 검색 결과"""

    id: str
    name: str
    description: Optional[str] = None
    address: str
    location: Dict[str, float]
    category: str
    tags: List[str] = []
    rating: Optional[float] = None
    review_count: Optional[int] = None
    price_range: Optional[int] = None
    distance_km: Optional[float] = None

    # 랭킹 관련 정보
    original_rank: int = Field(..., description="원본 순위")
    final_rank: int = Field(..., description="최종 랭킹")
    final_rank_score: float = Field(..., ge=0.0, le=1.0, description="최종 랭킹 점수")
    personalization_score: float = Field(..., ge=0.0, le=1.0, description="개인화 점수")

    # 상세 랭킹 정보
    ranking_factors: Dict[str, RankingFactor] = Field(..., description="랭킹 요소들")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="랭킹 신뢰도")
    ranking_source: str = Field("ml_algorithm", description="랭킹 알고리즘 출처")

    # 메타데이터
    created_at: datetime
    last_visited: Optional[datetime] = None
    user_interaction_score: float = Field(
        0.0, ge=0.0, le=1.0, description="사용자 상호작용 점수"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "id": "place_12345",
                "name": "홍대 감성 카페",
                "description": "조용하고 분위기 좋은 카페",
                "address": "서울시 마포구 홍익로 123",
                "location": {"lat": 37.5563, "lng": 126.9225},
                "category": "cafe",
                "tags": ["조용한", "분위기좋은", "와이파이"],
                "rating": 4.5,
                "review_count": 127,
                "price_range": 15000,
                "distance_km": 0.8,
                "original_rank": 3,
                "final_rank": 1,
                "final_rank_score": 0.92,
                "personalization_score": 0.85,
                "ranking_factors": {
                    "base_relevance": {
                        "factor_type": "base_relevance",
                        "weight": 0.4,
                        "score": 0.78,
                        "contribution": 0.312,
                    }
                },
                "confidence_score": 0.88,
                "ranking_source": "ml_algorithm",
            }
        }


class SearchRankingRequest(BaseModel):
    """검색 랭킹 요청"""

    query: Optional[str] = Field(None, max_length=200, description="검색 쿼리")
    search_results: List[Dict[str, Any]] = Field(..., description="원본 검색 결과")
    context: RankingContext = Field(..., description="랭킹 컨텍스트")
    max_results: Optional[int] = Field(50, ge=1, le=1000, description="최대 결과 수")
    personalization_strength: float = Field(0.7, ge=0.0, le=1.0, description="개인화 강도")
    diversity_threshold: float = Field(0.3, ge=0.0, le=1.0, description="다양성 임계값")

    @validator("search_results")
    def validate_search_results(cls, v):
        if not v:
            raise ValueError("검색 결과가 비어있습니다")
        if len(v) > 1000:
            raise ValueError("검색 결과가 너무 많습니다 (최대 1000개)")
        return v

    class Config:
        schema_extra = {
            "example": {
                "query": "홍대 카페",
                "search_results": [
                    {"id": "place_1", "name": "카페 A", "category": "cafe", "rating": 4.5}
                ],
                "context": {
                    "search_type": "text_search",
                    "location": {"lat": 37.5563, "lng": 126.9225},
                    "explain_ranking": True,
                },
                "max_results": 20,
                "personalization_strength": 0.8,
            }
        }


class SearchRankingResponse(BaseModel):
    """검색 랭킹 응답"""

    ranked_results: List[RankedSearchResult]
    total_results: int
    personalization_applied: bool
    ranking_metadata: Dict[str, Any] = Field(..., description="랭킹 메타데이터")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")
    cache_hit: bool = Field(False, description="캐시 히트 여부")

    class Config:
        schema_extra = {
            "example": {
                "ranked_results": [
                    {
                        "id": "place_1",
                        "name": "홍대 감성 카페",
                        "final_rank": 1,
                        "final_rank_score": 0.92,
                        "personalization_score": 0.85,
                    }
                ],
                "total_results": 15,
                "personalization_applied": True,
                "ranking_metadata": {
                    "algorithm_version": "v2.1",
                    "personalization_factors": [
                        "category_preference",
                        "location_preference",
                    ],
                    "diversity_applied": True,
                },
                "processing_time_ms": 145,
                "cache_hit": False,
            }
        }


class UserFeedbackRequest(BaseModel):
    """사용자 피드백 요청"""

    place_id: str = Field(..., description="장소 ID")
    feedback_type: FeedbackType = Field(..., description="피드백 타입")
    query_context: Optional[str] = Field(None, description="검색 쿼리 컨텍스트")
    session_id: Optional[str] = Field(None, description="세션 ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    additional_data: Optional[Dict[str, Any]] = Field(None, description="추가 데이터")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "place_id": "place_12345",
                "feedback_type": "click",
                "query_context": "홍대 카페",
                "session_id": "session_abc123",
                "additional_data": {"search_position": 2, "time_spent": 120},
            }
        }


class UserProfileData(BaseModel):
    """사용자 프로필 데이터"""

    preferences: Dict[str, Dict[str, float]] = Field(..., description="카테고리별 선호도")
    behavior_patterns: Dict[str, Union[float, int, str]] = Field(
        ..., description="행동 패턴"
    )
    interaction_history: Dict[str, Union[int, float]] = Field(
        ..., description="상호작용 히스토리"
    )
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "preferences": {
                    "categories": {"cafe": 0.8, "restaurant": 0.6},
                    "price_ranges": {"10000-30000": 0.9},
                    "regions": {"마포구": 0.9},
                },
                "behavior_patterns": {
                    "avg_session_duration": 450,
                    "distance_tolerance": 3.5,
                    "visit_time_preference": "afternoon",
                },
                "interaction_history": {
                    "total_searches": 247,
                    "click_through_rate": 0.68,
                    "conversion_rate": 0.34,
                },
            }
        }


class RankingAnalyticsRequest(BaseModel):
    """랭킹 분석 요청"""

    date_from: datetime = Field(..., description="시작 날짜")
    date_to: datetime = Field(..., description="종료 날짜")
    metrics: List[str] = Field(..., description="분석할 메트릭")
    group_by: Optional[List[str]] = Field(None, description="그룹핑 기준")

    @validator("date_to")
    def validate_date_range(cls, v, values):
        if "date_from" in values and v <= values["date_from"]:
            raise ValueError("종료 날짜는 시작 날짜보다 나중이어야 합니다")
        return v

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class RankingAnalyticsResponse(BaseModel):
    """랭킹 분석 응답"""

    period: Dict[str, datetime]
    metrics: Dict[str, Union[float, int, Dict]]
    trends: List[Dict[str, Any]]
    recommendations: List[str]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MLModelMetrics(BaseModel):
    """ML 모델 메트릭"""

    model_version: str
    accuracy: float = Field(..., ge=0.0, le=1.0)
    precision: float = Field(..., ge=0.0, le=1.0)
    recall: float = Field(..., ge=0.0, le=1.0)
    f1_score: float = Field(..., ge=0.0, le=1.0)
    training_date: datetime
    performance_metrics: Dict[str, float]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        schema_extra = {
            "example": {
                "model_version": "ranking_v2.1.0",
                "accuracy": 0.85,
                "precision": 0.82,
                "recall": 0.78,
                "f1_score": 0.80,
                "training_date": "2024-01-10T09:00:00Z",
                "performance_metrics": {
                    "avg_ndcg": 0.78,
                    "click_through_rate": 0.34,
                    "user_satisfaction": 0.82,
                },
            }
        }


class ABTestVariant(BaseModel):
    """A/B 테스트 변형"""

    variant_name: str
    traffic_percentage: int = Field(..., ge=0, le=100)
    ranking_config: Dict[str, float]
    description: str
    is_active: bool = Field(True)

    class Config:
        schema_extra = {
            "example": {
                "variant_name": "ml_boost_v2",
                "traffic_percentage": 50,
                "ranking_config": {
                    "ml_weight": 0.5,
                    "behavior_weight": 0.2,
                    "context_weight": 0.3,
                },
                "description": "ML 점수 가중치를 높인 변형",
                "is_active": True,
            }
        }


class RankingConfigRequest(BaseModel):
    """랭킹 설정 요청"""

    user_id: Optional[UUID] = Field(None, description="특정 사용자 설정 (전역 설정 시 None)")
    ranking_weights: Dict[str, float] = Field(..., description="랭킹 가중치")
    personalization_enabled: bool = Field(True)
    diversity_settings: Dict[str, float] = Field(..., description="다양성 설정")
    cache_settings: Dict[str, int] = Field(..., description="캐시 설정")

    @validator("ranking_weights")
    def validate_weights_sum(cls, v):
        total = sum(v.values())
        if not (0.8 <= total <= 1.2):  # 어느 정도 유연성 허용
            raise ValueError(f"가중치 합이 1.0에 가까워야 합니다 (현재: {total})")
        return v

    class Config:
        schema_extra = {
            "example": {
                "ranking_weights": {
                    "base_relevance": 0.4,
                    "personalization": 0.3,
                    "behavior_score": 0.2,
                    "contextual": 0.1,
                },
                "personalization_enabled": True,
                "diversity_settings": {
                    "category_diversity": 0.3,
                    "price_diversity": 0.2,
                    "location_diversity": 0.1,
                },
                "cache_settings": {"ranking_cache_ttl": 300, "profile_cache_ttl": 3600},
            }
        }
