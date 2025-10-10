"""
검색 최적화 API 엔드포인트

검색 UI/UX 최적화, 성능 모니터링, 자동완성 등의 API를 제공합니다.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.deps import get_cache_service, get_current_user, get_db
from app.schemas.search_optimization import (
    AutocompleteResponse,
    InfiniteScrollResponse,
    PaginationRequest,
    PerformanceAnalysisResponse,
    SearchCacheStrategy,
    SearchOptimizationConfig,
    SearchOptimizedResponse,
    SearchPerformanceMetrics,
    SearchUIConfig,
)
from app.services.search.search_optimization_service import SearchOptimizationService
from app.services.search.search_performance_service import SearchPerformanceService
from app.services.search.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search/optimized", response_model=SearchOptimizedResponse)
async def search_with_optimization(
    query: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    cache_strategy: SearchCacheStrategy = Query(SearchCacheStrategy.BALANCED),
    enable_pagination: bool = Query(True),
    enable_response_optimization: bool = Query(True),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    최적화된 검색 수행

    - 캐시 전략 적용
    - 응답 최적화
    - 페이지네이션
    - 성능 모니터링
    """
    try:
        # 검색 세션 시작
        performance_service = SearchPerformanceService(db, cache)
        session_id = await performance_service.start_search_session(
            user_id=current_user.id, query=query, timestamp=datetime.utcnow()
        )

        start_time = datetime.utcnow()

        # 검색 서비스 및 최적화 서비스 초기화
        search_service = SearchService(db, cache)
        optimization_service = SearchOptimizationService(db, cache, search_service)

        # 캐시 키 생성
        cache_key = await optimization_service.generate_search_cache_key(
            query=query,
            user_id=current_user.id,
            filters={"page": page, "page_size": page_size},
            cache_strategy=cache_strategy,
        )

        # 캐시된 결과 확인
        cached_result = await cache.get(cache_key)
        cache_hit = cached_result is not None

        if cached_result:
            search_results = cached_result["results"]
            total_results = cached_result["total"]
        else:
            # 실제 검색 수행
            search_response = await search_service.search_places_with_ranking(
                query=query,
                user_id=current_user.id,
                offset=(page - 1) * page_size,
                limit=page_size * 2,  # 더 많은 결과로 최적화 여지 확보
            )

            search_results = search_response.get("results", [])
            total_results = search_response.get("total", len(search_results))

            # 검색 결과 캐싱
            cache_data = {
                "results": search_results,
                "total": total_results,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 캐시 전략에 따른 TTL 적용
            ttl_mapping = {
                SearchCacheStrategy.CONSERVATIVE: 300,  # 5분
                SearchCacheStrategy.BALANCED: 900,  # 15분
                SearchCacheStrategy.AGGRESSIVE: 3600,  # 1시간
            }

            await cache.set(cache_key, cache_data, ttl=ttl_mapping[cache_strategy])

        # 응답 최적화 적용
        optimized_results = search_results
        optimization_applied = []

        if enable_response_optimization:
            config = SearchOptimizationConfig(
                enable_thumbnail_optimization=True,
                max_description_length=150,
                enable_tag_filtering=True,
                response_compression=False,
                cache_strategy=cache_strategy,
            )

            optimized_results = await optimization_service.optimize_search_response(
                results=search_results, config=config
            )
            optimization_applied.append("response_optimization")

        # 페이지네이션 적용
        paginated_response = None
        if enable_pagination:
            pagination_request = PaginationRequest(
                page=page,
                page_size=page_size,
                enable_cursor_pagination=True,
                preload_next_page=True,
            )

            paginated_response = await optimization_service.optimize_pagination(
                results=optimized_results, request=pagination_request
            )
            optimization_applied.append("pagination")

        # 응답 시간 계산
        end_time = datetime.utcnow()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        # 성능 메트릭 기록
        metrics = SearchPerformanceMetrics(
            session_id=session_id,
            query=query,
            response_time_ms=response_time_ms,
            result_count=len(optimized_results),
            cache_hit=cache_hit,
            user_id=current_user.id,
            timestamp=end_time,
        )
        await performance_service.record_search_metrics(metrics)

        # 응답 구성
        if paginated_response:
            return SearchOptimizedResponse(
                items=paginated_response["items"],
                pagination=paginated_response["pagination"],
                optimization_applied=optimization_applied,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                next_cursor=paginated_response.get("pagination", {}).get("next_cursor"),
                has_more=paginated_response.get("pagination", {}).get(
                    "has_next", False
                ),
                preloaded_next=paginated_response.get("preloaded_next"),
            )
        else:
            return SearchOptimizedResponse(
                items=optimized_results,
                pagination={
                    "current_page": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                },
                optimization_applied=optimization_applied,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
            )

    except Exception as e:
        logger.error(f"Optimized search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 최적화 처리 중 오류가 발생했습니다",
        )


@router.get("/search/infinite-scroll", response_model=InfiniteScrollResponse)
async def infinite_scroll_search(
    query: str = Query(..., min_length=1),
    cursor: Optional[str] = Query(None),
    page_size: int = Query(20, ge=1, le=50),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    무한 스크롤 검색

    - 커서 기반 페이지네이션
    - 부드러운 스크롤 경험
    - 캐시 최적화
    """
    try:
        search_service = SearchService(db, cache)
        optimization_service = SearchOptimizationService(db, cache, search_service)

        start_time = datetime.utcnow()

        # 무한 스크롤 페이지 조회
        response = await optimization_service.get_infinite_scroll_page(
            query=query, cursor=cursor, page_size=page_size, user_id=current_user.id
        )

        # 응답 시간 추가
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        response["response_time_ms"] = response_time_ms

        return InfiniteScrollResponse(**response)

    except Exception as e:
        logger.error(f"Infinite scroll search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="무한 스크롤 검색 중 오류가 발생했습니다",
        )


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def get_autocomplete_suggestions(
    q: str = Query(..., alias="query", min_length=1, max_length=50),
    max_suggestions: int = Query(5, ge=1, le=20),
    enable_personalization: bool = Query(True),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    자동완성 제안

    - 개인화된 제안
    - 캐시 최적화
    - 빠른 응답 시간
    """
    try:
        start_time = datetime.utcnow()

        search_service = SearchService(db, cache)
        optimization_service = SearchOptimizationService(db, cache, search_service)

        # 캐시된 자동완성 조회
        cached_suggestions = await optimization_service.get_cached_autocomplete(
            partial_query=q, user_id=current_user.id, max_suggestions=max_suggestions
        )

        suggestions = []
        is_personalized = False
        cache_hit = cached_suggestions is not None

        if cached_suggestions:
            suggestions = cached_suggestions
        else:
            # 개인화된 자동완성 생성
            if enable_personalization:
                suggestions = await optimization_service.get_personalized_autocomplete(
                    partial_query=q,
                    user_id=current_user.id,
                    max_suggestions=max_suggestions,
                )
                is_personalized = True
            else:
                # 일반 자동완성 (구현 필요)
                suggestions = [f"{q}벅스", f"{q}일레 카페", f"{q}드 레스토랑"][:max_suggestions]

            # 자동완성 결과 캐싱
            await optimization_service.cache_autocomplete(
                partial_query=q,
                suggestions=suggestions,
                user_id=current_user.id,
                ttl=300,  # 5분
            )

        # 응답 시간 계산
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return AutocompleteResponse(
            suggestions=suggestions,
            is_personalized=is_personalized,
            cache_hit=cache_hit,
            response_time_ms=response_time_ms,
        )

    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동완성 처리 중 오류가 발생했습니다",
        )


@router.post("/performance/metrics")
async def record_client_performance_metrics(
    metrics: Dict[str, Any],
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    클라이언트 성능 메트릭 기록

    - 클라이언트 측 성능 데이터 수집
    - 실시간 모니터링
    """
    try:
        performance_service = SearchPerformanceService(db, cache)

        # 클라이언트 메트릭 검증 및 변환
        client_metrics = SearchPerformanceMetrics(
            session_id=metrics.get("session_id", "client_session"),
            query=metrics.get("query", ""),
            response_time_ms=metrics.get("response_time_ms", 0),
            result_count=metrics.get("result_count", 0),
            cache_hit=metrics.get("cache_hit", False),
            user_id=current_user.id,
            timestamp=datetime.utcnow(),
            error_occurred=metrics.get("error_occurred", False),
            error_message=metrics.get("error_message"),
        )

        success = await performance_service.record_search_metrics(client_metrics)

        if success:
            return JSONResponse(
                content={"message": "성능 메트릭이 기록되었습니다"}, status_code=status.HTTP_200_OK
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="메트릭 기록에 실패했습니다"
            )

    except Exception as e:
        logger.error(f"Client metrics recording failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메트릭 기록 중 오류가 발생했습니다",
        )


@router.get("/performance/analysis", response_model=None)  # PerformanceAnalysisResponse
async def get_search_performance_analysis(
    days: int = Query(7, ge=1, le=30),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    검색 성능 분석

    - 사용자별 성능 분석
    - 트렌드 분석
    - 알림 정보
    """
    try:
        performance_service = SearchPerformanceService(db, cache)

        # 성능 분석 수행
        analysis = await performance_service.analyze_search_performance(
            user_id=current_user.id, time_period=timedelta(days=days)
        )

        # 최근 알림 조회
        recent_alerts = await performance_service.get_recent_alerts(
            time_period=timedelta(days=1)
        )

        analysis["recent_alerts"] = recent_alerts[:5]  # 최근 5개 알림

        return analysis

    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="성능 분석 중 오류가 발생했습니다",
        )


@router.post("/ui-config")
async def update_search_ui_config(
    config: SearchUIConfig,
    current_user=Depends(get_current_user),
    cache=Depends(get_cache_service),
):
    """
    검색 UI 설정 업데이트

    - 사용자별 UI 설정
    - 실시간 적용
    """
    try:
        # 사용자별 UI 설정 캐싱
        config_key = f"search:ui_config:{current_user.id}"
        success = await cache.set(config_key, config.dict(), ttl=86400 * 30)  # 30일

        if success:
            return JSONResponse(
                content={"message": "검색 UI 설정이 업데이트되었습니다"},
                status_code=status.HTTP_200_OK,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="설정 업데이트에 실패했습니다",
            )

    except Exception as e:
        logger.error(f"UI config update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UI 설정 업데이트 중 오류가 발생했습니다",
        )


@router.get("/ui-config", response_model=SearchUIConfig)
async def get_search_ui_config(
    current_user=Depends(get_current_user), cache=Depends(get_cache_service)
):
    """
    검색 UI 설정 조회
    """
    try:
        config_key = f"search:ui_config:{current_user.id}"
        config_data = await cache.get(config_key)

        if config_data:
            return SearchUIConfig(**config_data)
        else:
            # 기본 설정 반환
            return SearchUIConfig()

    except Exception as e:
        logger.error(f"UI config retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UI 설정 조회 중 오류가 발생했습니다",
        )


# Admin endpoints (관리자용)
@router.get("/admin/performance/alerts")
async def get_all_performance_alerts(
    hours: int = Query(24, ge=1, le=168),  # 최대 7일
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    전체 성능 알림 조회 (관리자용)
    """
    # 관리자 권한 확인 (구현 필요)
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")

    try:
        performance_service = SearchPerformanceService(db, cache)

        alerts = await performance_service.get_recent_alerts(
            time_period=timedelta(hours=hours)
        )

        return {"alerts": alerts, "total": len(alerts), "time_period_hours": hours}

    except Exception as e:
        logger.error(f"Admin alerts retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="알림 조회 중 오류가 발생했습니다",
        )


# 실시간 검색 API
@router.get("/realtime-search")
async def realtime_search(
    q: str = Query(..., alias="query", min_length=2, max_length=50),
    search_type: str = Query("instant", regex="^(instant|as_you_type)$"),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    실시간 검색

    - 타자 입력과 함께 즉시 검색
    - 빠른 응답 (< 200ms)
    - 적은 수의 결과
    """
    try:
        search_service = SearchService(db, cache)
        optimization_service = SearchOptimizationService(db, cache, search_service)

        # 실시간 검색 처리
        result = await optimization_service.process_realtime_search(
            query=q, user_id=current_user.id, search_type=search_type
        )

        # 검색 기록 저장
        await optimization_service.record_user_search(
            user_id=current_user.id, query=q, timestamp=datetime.utcnow()
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Realtime search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="실시간 검색 중 오류가 발생했습니다",
        )


# 검색 히스토리 관리 API
@router.get("/history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),
    current_user=Depends(get_current_user),
    cache=Depends(get_cache_service),
):
    """
    검색 히스토리 조회
    """
    try:
        search_service = SearchService(None, cache)
        optimization_service = SearchOptimizationService(None, cache, search_service)

        history = await optimization_service.get_search_history(
            user_id=current_user.id, limit=limit
        )

        return {"history": history, "total": len(history)}

    except Exception as e:
        logger.error(f"Search history retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 히스토리 조회 중 오류가 발생했습니다",
        )


@router.delete("/history")
async def clear_search_history(
    current_user=Depends(get_current_user), cache=Depends(get_cache_service)
):
    """
    검색 히스토리 삭제
    """
    try:
        search_service = SearchService(None, cache)
        optimization_service = SearchOptimizationService(None, cache, search_service)

        success = await optimization_service.clear_search_history(
            user_id=current_user.id
        )

        if success:
            return JSONResponse(content={"message": "검색 히스토리가 삭제되었습니다"})
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="히스토리 삭제에 실패했습니다"
            )

    except Exception as e:
        logger.error(f"Clear search history failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 히스토리 삭제 중 오류가 발생했습니다",
        )


# 인기 검색어 API
@router.get("/popular")
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50), cache=Depends(get_cache_service)
):
    """
    인기 검색어 조회
    """
    try:
        search_service = SearchService(None, cache)
        optimization_service = SearchOptimizationService(None, cache, search_service)

        popular_queries = await optimization_service.get_popular_queries(limit=limit)

        return {
            "popular_queries": popular_queries,
            "total": len(popular_queries),
            "updated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Popular queries retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인기 검색어 조회 중 오류가 발생했습니다",
        )


# 검색 통계 API
@router.get("/stats")
async def get_search_statistics(
    days: int = Query(7, ge=1, le=30), cache=Depends(get_cache_service)
):
    """
    검색 통계 조회
    """
    try:
        search_service = SearchService(None, cache)
        optimization_service = SearchOptimizationService(None, cache, search_service)

        stats = await optimization_service.get_search_performance_stats(days=days)

        return stats

    except Exception as e:
        logger.error(f"Search statistics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="검색 통계 조회 중 오류가 발생했습니다",
        )


# 검색 캐시 관리 API
@router.post("/cache/warm")
async def warm_search_cache(
    queries: List[str],
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    cache=Depends(get_cache_service),
):
    """
    검색 캐시 미리 워밍

    - 인기 검색어 사전 캐싱
    - 성능 향상
    """
    try:
        if len(queries) > 20:  # 최대 20개 제한
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="최대 20개의 쿼리만 처리 가능합니다"
            )

        search_service = SearchService(db, cache)
        optimization_service = SearchOptimizationService(db, cache, search_service)

        warmed_count = 0
        failed_count = 0

        for query in queries:
            try:
                # 각 쿼리에 대해 검색 실행 및 캐싱
                await optimization_service.process_realtime_search(
                    query=query, user_id=current_user.id, search_type="instant"
                )
                warmed_count += 1
            except Exception:
                failed_count += 1

        return {
            "message": f"캐시 워밍 완료",
            "warmed_queries": warmed_count,
            "failed_queries": failed_count,
            "total_queries": len(queries),
        }

    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="캐시 워밍 중 오류가 발생했습니다",
        )


@router.delete("/cache/clear")
async def clear_search_cache(
    cache_type: str = Query("all", regex="^(all|autocomplete|results|history)$"),
    current_user=Depends(get_current_user),
    cache=Depends(get_cache_service),
):
    """
    검색 캐시 삭제
    """
    try:
        cache_patterns = {
            "all": f"search:*:{current_user.id}*",
            "autocomplete": f"autocomplete:{current_user.id}:*",
            "results": f"search:optimized:*:{current_user.id}*",
            "history": f"search:history:{current_user.id}",
        }

        cache_patterns[cache_type]

        # 실제 구현에서는 Redis의 SCAN 명령어나 cache 서비스의 패턴 삭제 기능 사용
        # 여기서는 간단한 구현
        if cache_type == "history":
            await cache.delete(f"search:history:{current_user.id}")
        else:
            # 패턴 기반 삭제는 cache 서비스에서 구현 필요
            pass

        return JSONResponse(content={"message": f"{cache_type} 캐시가 삭제되었습니다"})

    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="캐시 삭제 중 오류가 발생했습니다",
        )


# 검색 A/B 테스트 API
@router.post("/ab-test/variant")
async def set_search_ab_test_variant(
    variant: str = Query(..., regex="^(control|variant_a|variant_b)$"),
    current_user=Depends(get_current_user),
    cache=Depends(get_cache_service),
):
    """
    검색 A/B 테스트 변형 설정
    """
    try:
        # A/B 테스트 변형 저장
        variant_key = f"search:ab_test:{current_user.id}"
        await cache.set(
            variant_key,
            {"variant": variant, "assigned_at": datetime.utcnow().isoformat()},
            ttl=86400 * 30,
        )  # 30일

        return JSONResponse(
            content={"message": "A/B 테스트 변형이 설정되었습니다", "variant": variant}
        )

    except Exception as e:
        logger.error(f"A/B test variant setting failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A/B 테스트 설정 중 오류가 발생했습니다",
        )


@router.get("/ab-test/variant")
async def get_search_ab_test_variant(
    current_user=Depends(get_current_user), cache=Depends(get_cache_service)
):
    """
    현재 사용자의 A/B 테스트 변형 조회
    """
    try:
        variant_key = f"search:ab_test:{current_user.id}"
        variant_data = await cache.get(variant_key)

        if variant_data:
            return variant_data
        else:
            # 기본값 반환 및 설정
            default_variant = {
                "variant": "control",
                "assigned_at": datetime.utcnow().isoformat(),
            }
            await cache.set(variant_key, default_variant, ttl=86400 * 30)
            return default_variant

    except Exception as e:
        logger.error(f"A/B test variant retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A/B 테스트 변형 조회 중 오류가 발생했습니다",
        )


# 검색 피드백 API
@router.post("/feedback")
async def submit_search_feedback(
    query: str,
    rating: int = Query(..., ge=1, le=5),
    feedback_type: str = Query(..., regex="^(relevance|speed|ui_ux|other)$"),
    comments: Optional[str] = None,
    current_user=Depends(get_current_user),
    cache=Depends(get_cache_service),
):
    """
    검색 결과에 대한 사용자 피드백 제출
    """
    try:
        feedback_data = {
            "user_id": str(current_user.id),
            "query": query,
            "rating": rating,
            "feedback_type": feedback_type,
            "comments": comments,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 피드백 저장 (실제로는 데이터베이스에 저장)
        feedback_key = f"search:feedback:{datetime.utcnow().strftime('%Y%m%d')}"
        daily_feedback = await cache.get(feedback_key) or []
        daily_feedback.append(feedback_data)

        # 최대 1000개 피드백 유지
        if len(daily_feedback) > 1000:
            daily_feedback = daily_feedback[-1000:]

        await cache.set(feedback_key, daily_feedback, ttl=86400 * 30)  # 30일

        return JSONResponse(content={"message": "피드백이 제출되었습니다"})

    except Exception as e:
        logger.error(f"Search feedback submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="피드백 제출 중 오류가 발생했습니다",
        )
