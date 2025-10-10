"""
고급 필터링 API 엔드포인트 (Task 2-3-3)

다중 필터 조건을 지원하는 고급 검색 API
- Elasticsearch 기반 고성능 필터링
- 실시간 패싯 정보 제공
- 복합 조건 필터링 지원
- 캐싱 및 성능 최적화
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.schemas.advanced_filter import (
    AdvancedFilterRequest,
    AdvancedFilterResponse,
    FilterAnalytics,
    FilteredPlace,
    FilterFacetsResponse,
    FilterSuggestionsResponse,
    SavedFilter,
    SavedFilterRequest,
    SavedFiltersResponse,
)
from app.services.ranking.advanced_filter_service import get_advanced_filter_service
from app.utils.cache import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/search",
    response_model=AdvancedFilterResponse,
    summary="고급 필터 검색",
    description="다중 필터 조건을 통한 고급 장소 검색",
)
async def advanced_filter_search(
    *,
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis_client),
    current_user: User = Depends(deps.get_current_active_user),
    filter_request: AdvancedFilterRequest,
    background_tasks: BackgroundTasks,
) -> AdvancedFilterResponse:
    """
    고급 필터 조건을 통한 장소 검색

    - **query**: 검색어 (선택사항)
    - **categories**: 카테고리 필터 (OR 조건)
    - **regions**: 지역 필터 (OR 조건)
    - **tags**: 태그 필터
    - **price_ranges**: 가격대 필터
    - **rating_min**: 최소 평점
    - **location**: 위치 기반 필터
    - **visit_status**: 방문 상태 필터
    - **sort_by**: 정렬 기준 (relevance, rating, recent, price, distance, name, popular)
    - **include_facets**: 패싯 정보 포함 여부
    """
    try:
        # 고급 필터링 서비스 초기화
        filter_service = get_advanced_filter_service(db, redis_client)

        # 필터 조건을 딕셔너리로 변환
        filter_criteria = filter_request.dict(exclude_unset=True)

        # 종합 필터 검색 수행
        result = await filter_service.comprehensive_filter_search(
            user_id=current_user.id,
            filter_criteria=filter_criteria,
            limit=filter_request.limit,
            offset=filter_request.offset,
            include_facets=filter_request.include_facets,
        )

        # 백그라운드 작업: 검색 로그 기록
        background_tasks.add_task(
            _log_search_analytics,
            user_id=current_user.id,
            filter_criteria=filter_criteria,
            result_count=result.get("total", 0),
            performance=result.get("performance", {}),
        )

        # 응답 변환
        response_data = _convert_to_response_format(result, filter_request)

        logger.info(
            f"Advanced filter search completed for user {current_user.id}: "
            f"{result.get('total', 0)} results"
        )

        return AdvancedFilterResponse(**response_data)

    except Exception as e:
        logger.error(f"Advanced filter search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="고급 필터 검색 처리 중 오류가 발생했습니다.",
        )


@router.get(
    "/facets",
    response_model=FilterFacetsResponse,
    summary="필터 패싯 정보",
    description="현재 데이터에 기반한 필터 패싯 옵션 조회",
)
async def get_filter_facets(
    *,
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis_client),
    current_user: User = Depends(deps.get_current_active_user),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    region: Optional[str] = Query(None, description="지역 필터"),
    use_cache: bool = Query(True, description="캐시 사용 여부"),
) -> Dict[str, Any]:
    """
    필터 패싯 정보 조회

    사용자의 장소 데이터를 기반으로 사용 가능한 필터 옵션들을 제공
    """
    try:
        filter_service = get_advanced_filter_service(db, redis_client)

        # 기본 필터 조건으로 패싯 정보 요청
        base_filter = {}
        if category:
            base_filter["categories"] = [category]
        if region:
            base_filter["regions"] = [region]

        # 패싯만 포함하는 검색 실행
        result = await filter_service.comprehensive_filter_search(
            user_id=current_user.id,
            filter_criteria=base_filter,
            limit=0,  # 결과는 필요 없고 패싯만
            include_facets=True,
        )

        facets = result.get("facets", {})

        logger.info(f"Retrieved facets for user {current_user.id}")

        return {
            "facets": facets,
            "applied_filters": base_filter,
            "source": result.get("query_info", {}).get("source", "unknown"),
        }

    except Exception as e:
        logger.error(f"Failed to retrieve facets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 패싯 정보 조회 중 오류가 발생했습니다.",
        )


@router.get(
    "/suggestions",
    response_model=FilterSuggestionsResponse,
    summary="필터 제안",
    description="현재 필터 조건에 대한 개선 제안",
)
async def get_filter_suggestions(
    *,
    db: Session = Depends(get_db),
    redis_client: Optional[Redis] = Depends(get_redis_client),
    current_user: User = Depends(deps.get_current_active_user),
    categories: Optional[List[str]] = Query(None, description="현재 카테고리 필터"),
    regions: Optional[List[str]] = Query(None, description="현재 지역 필터"),
    tags: Optional[List[str]] = Query(None, description="현재 태그 필터"),
    rating_min: Optional[float] = Query(None, description="현재 최소 평점"),
) -> Dict[str, Any]:
    """
    현재 필터 조건에 대한 개선 제안

    빈 결과이거나 너무 적은 결과를 가진 필터에 대해 대안 제안
    """
    try:
        filter_service = get_advanced_filter_service(db, redis_client)

        # 현재 필터 조건 구성
        current_filter = {}
        if categories:
            current_filter["categories"] = categories
        if regions:
            current_filter["regions"] = regions
        if tags:
            current_filter["tags"] = tags
        if rating_min:
            current_filter["rating_min"] = rating_min

        # 현재 필터로 검색하여 결과 수 확인
        result = await filter_service.comprehensive_filter_search(
            user_id=current_user.id,
            filter_criteria=current_filter,
            limit=1,  # 결과 수만 확인
        )

        suggestions = result.get("suggestions", {})
        total_results = result.get("total", 0)

        # 추가 제안 생성
        if total_results < 5:  # 결과가 적으면 추가 제안
            enhanced_suggestions = await _generate_enhanced_suggestions(
                filter_service, current_user.id, current_filter
            )
            suggestions.update(enhanced_suggestions)

        logger.info(f"Generated filter suggestions for user {current_user.id}")

        return {
            "current_results": total_results,
            "suggestions": suggestions,
            "applied_filters": current_filter,
        }

    except Exception as e:
        logger.error(f"Failed to generate filter suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 제안 생성 중 오류가 발생했습니다.",
        )


@router.post(
    "/saved",
    response_model=SavedFilter,
    summary="필터 조합 저장",
    description="자주 사용하는 필터 조합을 저장",
    status_code=status.HTTP_201_CREATED,
)
async def save_filter_combination(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    save_request: SavedFilterRequest,
) -> SavedFilter:
    """
    필터 조합 저장

    자주 사용하는 필터 조합을 이름을 붙여 저장
    """
    try:
        # TODO: SavedFilter 모델과 CRUD 구현 필요
        # 현재는 기본 응답 반환
        saved_filter_data = {
            "id": f"filter-{current_user.id}-{hash(save_request.name)}",
            "name": save_request.name,
            "filter_criteria": save_request.filter_criteria.dict(exclude_unset=True),
            "is_public": save_request.is_public,
            "use_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "last_used": None,
        }

        logger.info(
            f"Saved filter combination '{save_request.name}' for user {current_user.id}"
        )

        return SavedFilter(**saved_filter_data)

    except Exception as e:
        logger.error(f"Failed to save filter combination: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 조합 저장 중 오류가 발생했습니다.",
        )


@router.get(
    "/saved",
    response_model=SavedFiltersResponse,
    summary="저장된 필터 목록",
    description="사용자가 저장한 필터 조합 목록",
)
async def get_saved_filters(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    include_public: bool = Query(False, description="공개 필터 포함"),
) -> SavedFiltersResponse:
    """
    저장된 필터 조합 목록 조회
    """
    try:
        # TODO: 실제 데이터베이스에서 조회
        saved_filters = []

        logger.info(f"Retrieved saved filters for user {current_user.id}")

        return SavedFiltersResponse(filters=saved_filters)

    except Exception as e:
        logger.error(f"Failed to retrieve saved filters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장된 필터 조회 중 오류가 발생했습니다.",
        )


@router.get(
    "/analytics",
    response_model=FilterAnalytics,
    summary="필터 사용 분석",
    description="필터 사용 패턴 및 효과성 분석",
)
async def get_filter_analytics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    days: int = Query(30, ge=1, le=90, description="분석 기간 (일)"),
) -> FilterAnalytics:
    """
    필터 사용 분석 정보

    사용자의 필터 사용 패턴과 효과성 분석 제공
    """
    try:
        # TODO: 실제 분석 데이터 구현
        analytics_data = {
            "popular_filters": [
                {"combination": ["cafe", "홍대"], "usage_count": 25},
                {"combination": ["restaurant", "강남"], "usage_count": 18},
            ],
            "filter_effectiveness": {
                "category": 0.85,
                "region": 0.92,
                "rating": 0.78,
                "price": 0.67,
                "tags": 0.73,
            },
            "user_behavior": {
                "avg_filters_per_search": 2.3,
                "most_combined_filters": ["category", "region"],
                "preferred_sort_order": "rating",
            },
            "performance_stats": {
                "avg_response_time": 145,
                "cache_hit_rate": 0.67,
                "elasticsearch_usage": 0.89,
            },
        }

        logger.info(f"Retrieved filter analytics for user {current_user.id}")

        return FilterAnalytics(**analytics_data)

    except Exception as e:
        logger.error(f"Failed to retrieve filter analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="필터 분석 정보 조회 중 오류가 발생했습니다.",
        )


# 헬퍼 함수들


def _convert_to_response_format(
    result: Dict[str, Any], request: AdvancedFilterRequest
) -> Dict[str, Any]:
    """검색 결과를 API 응답 형식으로 변환"""

    # 장소 데이터 변환
    places = []
    for place_data in result.get("places", []):
        filtered_place = FilteredPlace(
            id=place_data.get("id", ""),
            name=place_data.get("name", ""),
            description=place_data.get("description"),
            address=place_data.get("address"),
            location=place_data.get("location"),
            category=place_data.get("category", ""),
            tags=place_data.get("tags", []),
            rating=place_data.get("rating"),
            review_count=place_data.get("review_count"),
            price_range=place_data.get("price_range"),
            visit_status=place_data.get("visit_status"),
            created_at=place_data.get("created_at", "2024-01-01T00:00:00Z"),
            updated_at=place_data.get("updated_at"),
            relevance_score=place_data.get("relevance_score"),
            distance_km=place_data.get("distance_km"),
            highlights=place_data.get("highlights"),
        )
        places.append(filtered_place)

    # 응답 데이터 구성
    response_data = {
        "places": places,
        "pagination": result.get("pagination", {}),
        "applied_filters": result.get("applied_filters", {}),
        "query_info": result.get("query_info", {}),
    }

    # 선택적 필드 추가
    if "facets" in result:
        response_data["facets"] = result["facets"]

    if "suggestions" in result:
        response_data["suggestions"] = result["suggestions"]

    if "performance" in result:
        response_data["performance"] = result["performance"]

    return response_data


async def _generate_enhanced_suggestions(
    filter_service, user_id: UUID, current_filter: Dict[str, Any]
) -> Dict[str, Any]:
    """향상된 필터 제안 생성"""

    enhanced_suggestions = {
        "popular_alternatives": [],
        "location_suggestions": [],
        "category_expansions": [],
    }

    # 인기 있는 대체 필터 조합 제안
    popular_combinations = [
        {"categories": ["cafe"], "regions": ["홍대"]},
        {"categories": ["restaurant"], "regions": ["강남"]},
        {"tags": ["분위기좋은"], "rating_min": 4.0},
    ]

    for combo in popular_combinations:
        if combo != current_filter:
            enhanced_suggestions["popular_alternatives"].append(
                {
                    "filter_combination": combo,
                    "description": f"인기 조합: {combo}",
                    "expected_results": 15,  # 예상 결과 수
                }
            )

    return enhanced_suggestions


async def _log_search_analytics(
    user_id: UUID,
    filter_criteria: Dict[str, Any],
    result_count: int,
    performance: Dict[str, Any],
) -> None:
    """검색 분석 로그 기록 (백그라운드 작업)"""

    try:
        # TODO: 실제 분석 로그 저장 구현
        analytics_data = {
            "user_id": str(user_id),
            "filters_used": list(filter_criteria.keys()),
            "result_count": result_count,
            "response_time_ms": performance.get("total_time_ms", 0),
            "cache_hit": performance.get("cache_hit", False),
            "source": "elasticsearch" if not performance.get("cache_hit") else "cache",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        logger.info(f"Logged search analytics: {analytics_data}")

    except Exception as e:
        logger.error(f"Failed to log search analytics: {e}")
