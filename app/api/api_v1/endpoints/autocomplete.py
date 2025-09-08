"""
자동완성 API 엔드포인트 (Task 2-3-2)

고도화된 자동완성 기능을 제공하는 REST API
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.autocomplete import (
    AutocompleteResponse,
    SearchAnalyticsResponse,
    SuggestionItem,
)
from app.services.autocomplete_service import get_autocomplete_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/suggestions", response_model=AutocompleteResponse)
async def get_autocomplete_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="검색 쿼리"),
    limit: int = Query(default=10, ge=1, le=20, description="제안 개수 제한"),
    include_personal: bool = Query(default=True, description="개인화 제안 포함"),
    include_trending: bool = Query(default=True, description="트렌딩 제안 포함"),
    include_popular: bool = Query(default=True, description="인기 제안 포함"),
    categories: Optional[List[str]] = Query(default=None, description="카테고리 필터"),
    lat: Optional[float] = Query(default=None, ge=-90, le=90, description="위도"),
    lng: Optional[float] = Query(default=None, ge=-180, le=180, description="경도"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> AutocompleteResponse:
    """
    종합적인 자동완성 제안 제공

    개인화 제안, 트렌딩 검색어, 인기 제안을 조합하여
    사용자에게 최적의 검색 제안을 반환합니다.
    """
    try:
        # 위치 정보 처리
        location = None
        if lat is not None and lng is not None:
            location = {"lat": lat, "lon": lng}

        # 자동완성 서비스 초기화
        autocomplete_service = get_autocomplete_service(db, redis_client)

        # 종합 제안 요청
        suggestions_data = await autocomplete_service.get_comprehensive_suggestions(
            user_id=current_user.id,
            query=q,
            limit=limit,
            include_personal=include_personal,
            include_trending=include_trending,
            include_popular=include_popular,
            categories=categories,
            location=location,
        )

        # 응답 형식에 맞게 변환
        suggestions = [
            SuggestionItem(
                text=item["text"],
                type=item["type"],
                score=item["score"],
                category=item.get("category"),
                address=item.get("address"),
                metadata=item.get("metadata", {}),
            )
            for item in suggestions_data["suggestions"]
        ]

        return AutocompleteResponse(
            suggestions=suggestions,
            categories=suggestions_data["categories"],
            total=suggestions_data["total"],
            query=suggestions_data["query"],
            timestamp=suggestions_data["timestamp"],
        )

    except Exception as e:
        logger.error(f"Autocomplete suggestions failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동완성 서비스를 일시적으로 사용할 수 없습니다",
        )


@router.get("/trending", response_model=Dict[str, Any])
async def get_trending_searches(
    limit: int = Query(default=10, ge=1, le=50, description="트렌딩 검색어 개수"),
    time_window: int = Query(default=24, ge=1, le=168, description="시간 윈도우 (시간)"),
    current_user: User = Depends(deps.get_current_user),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> Dict[str, Any]:
    """
    트렌딩 검색어 조회

    지정된 시간 윈도우 내에서 인기있는 검색어를 반환합니다.
    """
    try:
        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="트렌딩 검색어 서비스를 사용할 수 없습니다",
            )

        # 트렌딩 데이터 수집
        from datetime import datetime

        trending_key = f"trending_searches:{datetime.now().strftime('%Y%m%d')}"

        trending_data = await redis_client.zrevrangebyscore(
            trending_key, "+inf", "-inf", withscores=True, start=0, num=limit
        )

        trending_searches = []
        for term, count in trending_data:
            if isinstance(term, bytes):
                term = term.decode()

            trending_searches.append(
                {"query": term, "count": int(count), "type": "trending"}
            )

        return {
            "trending_searches": trending_searches,
            "total": len(trending_searches),
            "time_window_hours": time_window,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Trending searches failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="트렌딩 검색어를 가져올 수 없습니다",
        )


@router.get("/personal-history", response_model=Dict[str, Any])
async def get_personal_search_history(
    limit: int = Query(default=20, ge=1, le=100, description="검색 기록 개수"),
    current_user: User = Depends(deps.get_current_user),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> Dict[str, Any]:
    """
    개인 검색 기록 조회

    사용자의 최근 검색 기록을 빈도수와 함께 반환합니다.
    """
    try:
        if not redis_client:
            return {
                "search_history": [],
                "total": 0,
                "message": "검색 기록 서비스를 사용할 수 없습니다",
            }

        # 개인 검색 기록 조회
        history_key = f"user_search_history:{current_user.id}"
        history_data = await redis_client.lrange(history_key, 0, limit - 1)

        search_history = []
        for item in history_data:
            try:
                import json

                data = json.loads(item)
                search_history.append(
                    {
                        "query": data["query"],
                        "frequency": data.get("frequency", 1),
                        "last_searched": data.get("last_searched"),
                        "type": "personal_history",
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue

        return {
            "search_history": search_history,
            "total": len(search_history),
            "user_id": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Personal search history failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 기록을 가져올 수 없습니다",
        )


@router.get("/analytics", response_model=SearchAnalyticsResponse)
async def get_search_analytics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> SearchAnalyticsResponse:
    """
    검색 분석 데이터 제공

    개인화된 검색 분석과 전체 트렌드 분석을 제공합니다.
    """
    try:
        # 자동완성 서비스 초기화
        autocomplete_service = get_autocomplete_service(db, redis_client)

        # 분석 데이터 수집
        analytics_data = await autocomplete_service.get_search_analytics(
            current_user.id
        )

        return SearchAnalyticsResponse(
            trending_searches=analytics_data.get("trending_searches", []),
            popular_categories=analytics_data.get("popular_categories", {}),
            user_search_patterns=analytics_data.get("user_search_patterns", {}),
            performance_metrics=analytics_data.get("performance_metrics", {}),
            timestamp=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Search analytics failed for user {current_user.id}: {e}")
        # 에러가 발생해도 기본값 반환
        return SearchAnalyticsResponse(
            trending_searches=[],
            popular_categories={},
            user_search_patterns={},
            performance_metrics={"status": "error", "message": str(e)},
            timestamp=datetime.utcnow().isoformat(),
        )


@router.post("/cache/optimize", response_model=Dict[str, Any])
async def optimize_autocomplete_cache(
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> Dict[str, Any]:
    """
    자동완성 캐시 최적화 (관리자 전용)

    오래된 검색 기록과 트렌딩 데이터를 정리하여 성능을 최적화합니다.
    """
    try:
        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="캐시 서비스를 사용할 수 없습니다",
            )

        # 자동완성 서비스 초기화
        autocomplete_service = get_autocomplete_service(db, redis_client)

        # 캐시 최적화 실행
        optimization_result = await autocomplete_service.optimize_suggestions_cache()

        return {
            "message": "캐시 최적화가 완료되었습니다",
            "optimization_result": optimization_result,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Cache optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"캐시 최적화 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete("/history/clear", response_model=Dict[str, Any])
async def clear_personal_search_history(
    current_user: User = Depends(deps.get_current_user),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> Dict[str, Any]:
    """
    개인 검색 기록 삭제

    사용자의 모든 검색 기록을 삭제합니다.
    """
    try:
        if not redis_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="검색 기록 서비스를 사용할 수 없습니다",
            )

        # 개인 검색 기록 삭제
        history_key = f"user_search_history:{current_user.id}"
        deleted_count = await redis_client.delete(history_key)

        return {
            "message": "검색 기록이 삭제되었습니다",
            "deleted": deleted_count > 0,
            "user_id": str(current_user.id),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Clear search history failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 기록 삭제 중 오류가 발생했습니다",
        )


@router.get("/health", response_model=Dict[str, Any])
async def autocomplete_health_check(
    db: Session = Depends(deps.get_db),
    redis_client: Optional[redis.Redis] = Depends(deps.get_redis_client),
) -> Dict[str, Any]:
    """
    자동완성 서비스 상태 확인

    자동완성 서비스의 상태와 의존성 서비스들의 상태를 확인합니다.
    """
    try:
        health_status = {
            "status": "healthy",
            "services": {
                "database": "unknown",
                "redis": "unknown",
                "elasticsearch": "unknown",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 데이터베이스 상태 확인
        try:
            db.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        # Redis 상태 확인
        if redis_client:
            try:
                await redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception as e:
                health_status["services"]["redis"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        else:
            health_status["services"]["redis"] = "not_configured"

        # Elasticsearch 상태 확인
        try:
            from app.db.elasticsearch import es_manager

            if es_manager.client:
                es_health = await es_manager.health_check()
                health_status["services"]["elasticsearch"] = es_health.get(
                    "status", "unknown"
                )
                if es_health.get("status") != "green":
                    health_status["status"] = "degraded"
            else:
                health_status["services"]["elasticsearch"] = "not_connected"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["services"]["elasticsearch"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
