"""
성능 모니터링 API 엔드포인트

성능 대시보드 및 모니터링을 위한 API 엔드포인트
"""
import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.monitoring.performance_service import (
    get_metrics_collector,
    get_performance_dashboard,
    get_scaling_engine,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class MetricsRequest(BaseModel):
    """메트릭 업데이트 요청"""

    response_time: float = Field(..., ge=0, description="평균 응답 시간 (ms)")
    cache_hit_rate: float = Field(..., ge=0, le=1, description="캐시 적중률 (0-1)")
    error_rate: float = Field(..., ge=0, le=1, description="에러율 (0-1)")
    active_connections: int = Field(0, ge=0, description="활성 연결 수")
    requests_per_second: int = Field(0, ge=0, description="초당 요청 수")
    memory_usage_mb: float = Field(0, ge=0, description="메모리 사용량 (MB)")
    cpu_usage_percent: float = Field(0, ge=0, le=100, description="CPU 사용률 (%)")


class QueryPerformanceRequest(BaseModel):
    """쿼리 성능 기록 요청"""

    query: str = Field(..., description="실행된 쿼리")
    execution_time_ms: float = Field(..., ge=0, description="실행 시간 (ms)")
    rows_affected: int = Field(0, ge=0, description="영향받은 행 수")


class EndpointPerformanceRequest(BaseModel):
    """엔드포인트 성능 기록 요청"""

    endpoint: str = Field(..., description="API 엔드포인트 경로")
    method: str = Field(..., description="HTTP 메소드")
    response_time_ms: float = Field(..., ge=0, description="응답 시간 (ms)")
    status_code: int = Field(..., ge=100, le=599, description="HTTP 상태 코드")


class PerformanceResponse(BaseModel):
    """성능 데이터 응답"""

    current_metrics: Dict[str, Any] = Field(..., description="현재 메트릭")
    alerts: List[Dict[str, Any]] = Field(..., description="알림 목록")
    performance_ranking: List[Dict[str, Any]] = Field(..., description="엔드포인트 성능 순위")
    slow_queries: List[Dict[str, Any]] = Field(..., description="느린 쿼리 목록")
    trend_analysis: Dict[str, Any] = Field(..., description="성능 트렌드 분석")


class CacheStatsResponse(BaseModel):
    """캐시 통계 응답"""

    overall: Dict[str, Any] = Field(..., description="전체 캐시 통계")
    l1_memory: Dict[str, Any] = Field(..., description="L1 메모리 캐시 통계")
    l2_disk: Dict[str, Any] = Field(..., description="L2 디스크 캐시 통계")
    l3_redis: Dict[str, Any] = Field(..., description="L3 Redis 캐시 통계")


class ScalingRecommendationsResponse(BaseModel):
    """스케일링 권장사항 응답"""

    recommendations: List[Dict[str, Any]] = Field(..., description="권장사항 목록")
    generated_at: str = Field(..., description="생성 시간")


@router.get(
    "/dashboard",
    response_model=PerformanceResponse,
    summary="성능 대시보드 데이터 조회",
    description="실시간 성능 메트릭, 알림, 순위, 트렌드 분석 데이터를 조회합니다.",
)
async def get_performance_dashboard():
    """
    성능 대시보드 데이터 조회

    실시간 성능 메트릭과 분석 데이터를 제공합니다:
    - 현재 성능 메트릭
    - 성능 알림 목록
    - API 엔드포인트 성능 순위
    - 느린 쿼리 목록
    - 성능 트렌드 분석
    """
    try:
        dashboard = get_performance_dashboard()
        dashboard_data = dashboard.get_dashboard_data()

        return PerformanceResponse(**dashboard_data)

    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance dashboard data",
        )


@router.post(
    "/metrics",
    status_code=status.HTTP_201_CREATED,
    summary="성능 메트릭 업데이트",
    description="새로운 성능 메트릭 데이터를 대시보드에 업데이트합니다.",
)
async def update_metrics(metrics: MetricsRequest):
    """
    성능 메트릭 업데이트

    시스템 모니터링 도구나 애플리케이션에서 수집한
    성능 메트릭을 대시보드에 반영합니다.
    """
    try:
        dashboard = get_performance_dashboard()
        collector = get_metrics_collector()

        # 메트릭 스냅샷 추가
        collector.add_metrics_snapshot(
            response_time=metrics.response_time,
            cache_hit_rate=metrics.cache_hit_rate,
            error_rate=metrics.error_rate,
            active_connections=metrics.active_connections,
            requests_per_second=metrics.requests_per_second,
            memory_usage_mb=metrics.memory_usage_mb,
            cpu_usage_percent=metrics.cpu_usage_percent,
        )

        # 대시보드 메트릭 업데이트
        dashboard.update_metrics(metrics.dict())

        return {"message": "Metrics updated successfully"}

    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update performance metrics",
        )


@router.post(
    "/query-performance",
    status_code=status.HTTP_201_CREATED,
    summary="쿼리 성능 기록",
    description="데이터베이스 쿼리 성능을 모니터링하고 최적화 제안을 받습니다.",
)
async def record_query_performance(query_perf: QueryPerformanceRequest):
    """
    쿼리 성능 기록

    데이터베이스 쿼리의 실행 시간과 영향받은 행 수를 기록하고,
    느린 쿼리에 대한 최적화 제안을 제공합니다.
    """
    try:
        collector = get_metrics_collector()

        collector.monitor_query_performance(
            query=query_perf.query,
            execution_time=query_perf.execution_time_ms,
            rows_affected=query_perf.rows_affected,
        )

        return {"message": "Query performance recorded successfully"}

    except Exception as e:
        logger.error(f"Failed to record query performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record query performance",
        )


@router.post(
    "/endpoint-performance",
    status_code=status.HTTP_201_CREATED,
    summary="엔드포인트 성능 기록",
    description="API 엔드포인트의 응답 시간과 상태 코드를 기록합니다.",
)
async def record_endpoint_performance(endpoint_perf: EndpointPerformanceRequest):
    """
    엔드포인트 성능 기록

    API 엔드포인트의 성능 데이터를 수집하여
    성능 순위와 최적화가 필요한 엔드포인트를 식별합니다.
    """
    try:
        collector = get_metrics_collector()

        collector.track_endpoint_performance(
            endpoint=endpoint_perf.endpoint,
            method=endpoint_perf.method,
            response_time_ms=endpoint_perf.response_time_ms,
            status_code=endpoint_perf.status_code,
        )

        return {"message": "Endpoint performance recorded successfully"}

    except Exception as e:
        logger.error(f"Failed to record endpoint performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record endpoint performance",
        )


@router.get(
    "/cache-stats",
    response_model=CacheStatsResponse,
    summary="캐시 통계 조회",
    description="다계층 캐시 시스템의 상세 통계를 조회합니다.",
)
async def get_cache_statistics():
    """
    캐시 통계 조회

    L1(메모리), L2(디스크), L3(Redis) 캐시의 상세한
    사용량과 성능 통계를 제공합니다.
    """
    try:
        collector = get_metrics_collector()
        cache_stats = await collector.get_cache_stats()

        if not cache_stats:
            # 기본 응답 구조
            cache_stats = {
                "overall": {},
                "l1_memory": {},
                "l2_disk": {},
                "l3_redis": {},
            }

        return CacheStatsResponse(**cache_stats)

    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics",
        )


@router.get(
    "/performance-ranking", summary="API 성능 순위", description="API 엔드포인트의 성능 순위를 조회합니다."
)
async def get_performance_ranking(
    limit: int = Query(10, ge=1, le=100, description="조회할 엔드포인트 수")
):
    """
    API 성능 순위 조회

    성능 점수를 기준으로 API 엔드포인트의 순위를 제공합니다.
    성능 점수는 응답 시간과 성공률을 고려하여 계산됩니다.
    """
    try:
        collector = get_metrics_collector()
        ranking = collector.get_performance_ranking()

        return {
            "ranking": ranking[:limit],
            "total_endpoints": len(ranking),
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance ranking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance ranking",
        )


@router.get(
    "/slow-queries", summary="느린 쿼리 조회", description="성능 임계값을 초과한 느린 쿼리와 최적화 제안을 조회합니다."
)
async def get_slow_queries(
    limit: int = Query(10, ge=1, le=50, description="조회할 쿼리 수"),
    threshold_ms: float = Query(100.0, ge=10.0, description="느린 쿼리 임계값 (ms)"),
):
    """
    느린 쿼리 조회

    지정된 임계값을 초과한 느린 쿼리들과
    각 쿼리에 대한 최적화 제안을 제공합니다.
    """
    try:
        collector = get_metrics_collector()
        slow_queries = collector.get_slow_queries(limit)

        # 임계값 필터링
        filtered_queries = [
            q for q in slow_queries if q["execution_time_ms"] >= threshold_ms
        ]

        return {
            "slow_queries": filtered_queries,
            "threshold_ms": threshold_ms,
            "total_found": len(filtered_queries),
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve slow queries",
        )


@router.get(
    "/scaling-recommendations",
    response_model=ScalingRecommendationsResponse,
    summary="스케일링 권장사항",
    description="현재 성능 메트릭을 기반으로 한 스케일링 권장사항을 제공합니다.",
)
async def get_scaling_recommendations():
    """
    스케일링 권장사항 조회

    CPU, 메모리, 응답시간, 요청률 등의 메트릭을 분석하여
    자동으로 생성된 스케일링 권장사항을 제공합니다.
    """
    try:
        scaling_engine = get_scaling_engine()
        recommendations = scaling_engine.generate_scaling_recommendations()

        return ScalingRecommendationsResponse(
            recommendations=recommendations, generated_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to get scaling recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate scaling recommendations",
        )


@router.get(
    "/trend-analysis", summary="성능 트렌드 분석", description="지정된 기간 동안의 성능 트렌드를 분석합니다."
)
async def get_trend_analysis(
    hours: int = Query(1, ge=1, le=168, description="분석 기간 (시간)")
):
    """
    성능 트렌드 분석

    지정된 기간 동안의 성능 메트릭 변화를 분석하여
    개선/악화 트렌드를 제공합니다.
    """
    try:
        dashboard = get_performance_dashboard()
        trend_analysis = dashboard.analyze_performance_trend(hours)

        return {**trend_analysis, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Failed to get trend analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze performance trends",
        )


@router.delete(
    "/metrics/clear", summary="메트릭 데이터 초기화", description="수집된 모든 성능 메트릭 데이터를 초기화합니다."
)
async def clear_metrics():
    """
    메트릭 데이터 초기화

    테스트나 유지보수 목적으로 수집된 모든 성능 메트릭을 삭제합니다.
    주의: 이 작업은 되돌릴 수 없습니다.
    """
    try:
        collector = get_metrics_collector()

        # 모든 메트릭 데이터 초기화
        collector.api_response_times.clear()
        collector.cache_metrics.clear()
        collector.query_metrics.clear()
        collector.endpoint_stats.clear()
        collector.metrics_history.clear()

        # 대시보드 데이터도 초기화
        dashboard = get_performance_dashboard()
        dashboard.current_metrics.clear()
        dashboard.alerts.clear()

        return {"message": "All performance metrics cleared successfully"}

    except Exception as e:
        logger.error(f"Failed to clear metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear performance metrics",
        )


@router.get("/health", summary="성능 모니터링 시스템 상태", description="성능 모니터링 시스템의 상태를 확인합니다.")
async def get_monitoring_health():
    """
    성능 모니터링 시스템 상태 확인

    메트릭 수집기와 대시보드의 작동 상태를 확인합니다.
    """
    try:
        collector = get_metrics_collector()
        dashboard = get_performance_dashboard()

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics_collector": {
                "api_metrics_count": sum(
                    len(times) for times in collector.api_response_times.values()
                ),
                "cache_metrics_count": len(collector.cache_metrics),
                "query_metrics_count": len(collector.query_metrics),
                "endpoint_stats_count": len(collector.endpoint_stats),
                "metrics_history_count": len(collector.metrics_history),
            },
            "dashboard": {
                "current_metrics_available": bool(dashboard.current_metrics),
                "alerts_count": len(dashboard.alerts),
                "last_update": dashboard.current_metrics.get("timestamp", "never"),
            },
        }

        return health_status

    except Exception as e:
        logger.error(f"Failed to get monitoring health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check monitoring system health",
        )
