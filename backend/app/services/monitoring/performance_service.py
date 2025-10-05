"""
성능 모니터링 및 대시보드 서비스

API 응답 최적화 및 성능 튜닝 대시보드를 위한 서비스 구현
"""
import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from app.core.cache import get_cache_manager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """성능 메트릭 데이터"""

    timestamp: datetime
    response_time: float
    cache_hit_rate: float
    error_rate: float
    active_connections: int = 0
    requests_per_second: int = 0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class QueryPerformance:
    """쿼리 성능 데이터"""

    query: str
    execution_time_ms: float
    rows_affected: int
    timestamp: datetime
    slow_query: bool = False
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class EndpointStats:
    """엔드포인트 통계"""

    endpoint: str
    method: str
    total_requests: int = 0
    total_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    min_time: float = float("inf")
    max_time: float = 0.0

    @property
    def avg_response_time(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_time / self.total_requests

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests

    @property
    def performance_score(self) -> float:
        """성능 점수 계산 (높을수록 좋음)"""
        if self.total_requests == 0:
            return 0.0
        return self.success_rate * (1000 / max(self.avg_response_time, 1))


class MetricsCollector:
    """성능 메트릭 수집기"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.api_response_times: Dict[str, List[float]] = defaultdict(list)
        self.cache_metrics: List[Dict[str, Any]] = []
        self.query_metrics: List[QueryPerformance] = []
        self.endpoint_stats: Dict[str, EndpointStats] = {}
        self.metrics_history: deque = deque(maxlen=max_history)

    def measure_response_time(self, endpoint: str, method: str):
        """API 응답 시간 측정 데코레이터"""

        def decorator(func: Callable):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status_code = 200
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    logger.error(f"API error in {endpoint}: {e}")
                    raise
                finally:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000

                    # API 응답 시간 기록
                    key = f"{method}_{endpoint}"
                    self.api_response_times[key].append(duration_ms)

                    # 최근 100개만 유지
                    if len(self.api_response_times[key]) > 100:
                        self.api_response_times[key] = self.api_response_times[key][
                            -100:
                        ]

                    # 엔드포인트 통계 업데이트
                    self.track_endpoint_performance(
                        endpoint, method, duration_ms, status_code
                    )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                status_code = 200
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    status_code = 500
                    logger.error(f"API error in {endpoint}: {e}")
                    raise
                finally:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000

                    key = f"{method}_{endpoint}"
                    self.api_response_times[key].append(duration_ms)

                    if len(self.api_response_times[key]) > 100:
                        self.api_response_times[key] = self.api_response_times[key][
                            -100:
                        ]

                    self.track_endpoint_performance(
                        endpoint, method, duration_ms, status_code
                    )

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def track_cache_operation(self, operation: str, hit: bool, duration_ms: float):
        """캐시 연산 추적"""
        self.cache_metrics.append(
            {
                "operation": operation,
                "hit": hit,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # 최근 1000개만 유지
        if len(self.cache_metrics) > 1000:
            self.cache_metrics = self.cache_metrics[-1000:]

    def monitor_query_performance(
        self,
        query: str,
        execution_time: float,
        rows_affected: int,
        threshold_ms: float = 100.0,
    ):
        """데이터베이스 쿼리 성능 모니터링"""
        is_slow = execution_time > threshold_ms

        suggestions = []
        if is_slow:
            suggestions = self._generate_optimization_suggestions(query, execution_time)

        query_perf = QueryPerformance(
            query=query[:100] + "..." if len(query) > 100 else query,
            execution_time_ms=execution_time,
            rows_affected=rows_affected,
            timestamp=datetime.now(),
            slow_query=is_slow,
            optimization_suggestions=suggestions,
        )

        self.query_metrics.append(query_perf)

        # 최근 500개만 유지
        if len(self.query_metrics) > 500:
            self.query_metrics = self.query_metrics[-500:]

        if is_slow:
            logger.warning(
                f"Slow query detected: {query_perf.query} "
                f"({execution_time:.2f}ms, {rows_affected} rows)"
            )

    def _generate_optimization_suggestions(
        self, query: str, time_ms: float
    ) -> List[str]:
        """쿼리 최적화 제안 생성"""
        suggestions = []
        query_upper = query.upper()

        if "SELECT *" in query_upper:
            suggestions.append("Avoid SELECT *, specify only needed columns")

        if "LIKE" in query_upper and "%" in query:
            suggestions.append(
                "Consider full-text search or proper indexing for LIKE patterns"
            )

        if time_ms > 500:
            suggestions.append(
                "Query takes too long, consider query restructuring or caching"
            )

        if "JOIN" in query_upper and time_ms > 200:
            suggestions.append("Optimize JOIN conditions and ensure proper indexing")

        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            suggestions.append("Consider adding LIMIT to ORDER BY queries")

        return suggestions

    def track_endpoint_performance(
        self, endpoint: str, method: str, response_time_ms: float, status_code: int
    ):
        """엔드포인트 성능 추적"""
        key = f"{method} {endpoint}"

        if key not in self.endpoint_stats:
            self.endpoint_stats[key] = EndpointStats(endpoint=endpoint, method=method)

        stats = self.endpoint_stats[key]
        stats.total_requests += 1
        stats.total_time += response_time_ms

        if 200 <= status_code < 400:
            stats.success_count += 1
        else:
            stats.error_count += 1

        stats.min_time = min(stats.min_time, response_time_ms)
        stats.max_time = max(stats.max_time, response_time_ms)

    def add_metrics_snapshot(
        self,
        response_time: float,
        cache_hit_rate: float,
        error_rate: float,
        active_connections: int = 0,
        requests_per_second: int = 0,
        memory_usage_mb: float = 0.0,
        cpu_usage_percent: float = 0.0,
    ):
        """메트릭 스냅샷 추가"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            response_time=response_time,
            cache_hit_rate=cache_hit_rate,
            error_rate=error_rate,
            active_connections=active_connections,
            requests_per_second=requests_per_second,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
        )

        self.metrics_history.append(metrics)

    def get_performance_ranking(self) -> List[Dict[str, Any]]:
        """성능 순위 조회"""
        ranking = []

        for key, stats in self.endpoint_stats.items():
            ranking.append(
                {
                    "endpoint": stats.endpoint,
                    "method": stats.method,
                    "avg_response_time": stats.avg_response_time,
                    "success_rate": stats.success_rate,
                    "total_requests": stats.total_requests,
                    "min_time": stats.min_time if stats.min_time != float("inf") else 0,
                    "max_time": stats.max_time,
                    "performance_score": stats.performance_score,
                }
            )

        # 성능 점수로 정렬 (높은 순)
        return sorted(ranking, key=lambda x: x["performance_score"], reverse=True)

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """느린 쿼리 조회"""
        slow_queries = [q for q in self.query_metrics if q.slow_query]

        # 실행 시간 순 정렬 (느린 순)
        slow_queries.sort(key=lambda x: x.execution_time_ms, reverse=True)

        return [
            {
                "query": q.query,
                "execution_time_ms": q.execution_time_ms,
                "rows_affected": q.rows_affected,
                "timestamp": q.timestamp.isoformat(),
                "optimization_suggestions": q.optimization_suggestions,
            }
            for q in slow_queries[:limit]
        ]

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            cache_manager = await get_cache_manager()
            return await cache_manager.get_comprehensive_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}


class PerformanceDashboard:
    """성능 대시보드"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.current_metrics: Dict[str, Any] = {}
        self.alerts: List[Dict[str, Any]] = []
        self.alert_thresholds = {
            "response_time_p95": 1000,  # 1초
            "cache_hit_rate_min": 0.6,  # 60%
            "error_rate_max": 0.05,  # 5%
            "cpu_usage_max": 80,  # 80%
            "memory_usage_max": 85,  # 85%
        }

    def update_metrics(self, metrics: Dict[str, Any]):
        """대시보드 메트릭 업데이트"""
        timestamp = datetime.now().isoformat()
        self.current_metrics = {**metrics, "timestamp": timestamp}

        # 알림 체크
        self._check_alerts(metrics, timestamp)

    def _check_alerts(self, metrics: Dict[str, Any], timestamp: str):
        """임계값 체크 및 알림 생성"""
        # P95 응답 시간 체크
        if (
            metrics.get("response_time_p95", 0)
            > self.alert_thresholds["response_time_p95"]
        ):
            self.alerts.append(
                {
                    "type": "high_response_time",
                    "message": f"P95 response time: {metrics['response_time_p95']}ms",
                    "timestamp": timestamp,
                    "severity": "warning",
                }
            )

        # 캐시 적중률 체크
        if (
            metrics.get("cache_hit_rate", 1.0)
            < self.alert_thresholds["cache_hit_rate_min"]
        ):
            self.alerts.append(
                {
                    "type": "low_cache_hit_rate",
                    "message": f"Cache hit rate: {metrics['cache_hit_rate']:.2%}",
                    "timestamp": timestamp,
                    "severity": "warning",
                }
            )

        # 에러율 체크
        if metrics.get("error_rate", 0) > self.alert_thresholds["error_rate_max"]:
            self.alerts.append(
                {
                    "type": "high_error_rate",
                    "message": f"Error rate: {metrics['error_rate']:.2%}",
                    "timestamp": timestamp,
                    "severity": "critical",
                }
            )

        # CPU 사용률 체크
        if metrics.get("cpu_usage", 0) > self.alert_thresholds["cpu_usage_max"]:
            self.alerts.append(
                {
                    "type": "high_cpu_usage",
                    "message": f"CPU usage: {metrics['cpu_usage']:.1f}%",
                    "timestamp": timestamp,
                    "severity": "critical" if metrics["cpu_usage"] > 90 else "warning",
                }
            )

        # 메모리 사용률 체크
        if metrics.get("memory_usage", 0) > self.alert_thresholds["memory_usage_max"]:
            self.alerts.append(
                {
                    "type": "high_memory_usage",
                    "message": f"Memory usage: {metrics['memory_usage']:.1f}%",
                    "timestamp": timestamp,
                    "severity": "critical"
                    if metrics["memory_usage"] > 95
                    else "warning",
                }
            )

        # 최근 100개 알림만 유지
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def analyze_performance_trend(self, hours: int = 1) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m
            for m in self.metrics_collector.metrics_history
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {"trend": "no_data"}

        # 평균 계산
        avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
        avg_cache_hit_rate = statistics.mean(m.cache_hit_rate for m in recent_metrics)
        avg_error_rate = statistics.mean(m.error_rate for m in recent_metrics)

        # 트렌드 계산 (첫 번째 vs 마지막 값 비교)
        if len(recent_metrics) >= 2:
            first = recent_metrics[0]
            last = recent_metrics[-1]

            response_time_trend = (
                "improving"
                if last.response_time < first.response_time
                else (
                    "degrading"
                    if last.response_time > first.response_time
                    else "stable"
                )
            )
            cache_trend = (
                "improving"
                if last.cache_hit_rate > first.cache_hit_rate
                else (
                    "degrading"
                    if last.cache_hit_rate < first.cache_hit_rate
                    else "stable"
                )
            )
            error_trend = (
                "improving"
                if last.error_rate < first.error_rate
                else ("degrading" if last.error_rate > first.error_rate else "stable")
            )
        else:
            response_time_trend = cache_trend = error_trend = "stable"

        return {
            "period_hours": hours,
            "data_points": len(recent_metrics),
            "averages": {
                "response_time": avg_response_time,
                "cache_hit_rate": avg_cache_hit_rate,
                "error_rate": avg_error_rate,
            },
            "trends": {
                "response_time": response_time_trend,
                "cache_hit_rate": cache_trend,
                "error_rate": error_trend,
            },
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        return {
            "current_metrics": self.current_metrics,
            "alerts": self.alerts,
            "performance_ranking": self.metrics_collector.get_performance_ranking(),
            "slow_queries": self.metrics_collector.get_slow_queries(),
            "trend_analysis": self.analyze_performance_trend(1),
        }


class ScalingRecommendationEngine:
    """스케일링 권장 엔진"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    def generate_scaling_recommendations(self) -> List[Dict[str, Any]]:
        """스케일링 권장사항 생성"""
        recommendations = []

        if not self.metrics_collector.metrics_history:
            return recommendations

        # 최근 메트릭 평균 계산
        recent_metrics = list(self.metrics_collector.metrics_history)[-10:]  # 최근 10개

        avg_cpu = statistics.mean(m.cpu_usage_percent for m in recent_metrics)
        avg_memory = statistics.mean(m.memory_usage_mb for m in recent_metrics)
        avg_response_time = statistics.mean(m.response_time for m in recent_metrics)
        avg_requests = statistics.mean(m.requests_per_second for m in recent_metrics)

        # CPU 기반 권장사항
        if avg_cpu > 80:
            recommendations.append(
                {
                    "type": "scale_up",
                    "resource": "cpu",
                    "current_usage": avg_cpu,
                    "recommended_action": "Increase CPU cores or scale out",
                    "priority": "high" if avg_cpu > 90 else "medium",
                }
            )
        elif avg_cpu < 20:
            recommendations.append(
                {
                    "type": "scale_down",
                    "resource": "cpu",
                    "current_usage": avg_cpu,
                    "recommended_action": "Consider reducing CPU allocation",
                    "priority": "low",
                }
            )

        # 메모리 기반 권장사항 (가정: 전체 메모리 대비 사용률)
        memory_usage_percent = (avg_memory / 1024) * 100  # 1GB 기준으로 계산
        if memory_usage_percent > 85:
            recommendations.append(
                {
                    "type": "scale_up",
                    "resource": "memory",
                    "current_usage": memory_usage_percent,
                    "recommended_action": "Increase memory allocation",
                    "priority": "high" if memory_usage_percent > 95 else "medium",
                }
            )

        # 응답시간 기반 권장사항
        if avg_response_time > 1000:  # 1초 초과
            recommendations.append(
                {
                    "type": "performance",
                    "resource": "response_time",
                    "current_value": avg_response_time,
                    "recommended_action": "Scale out or optimize application performance",
                    "priority": "high",
                }
            )

        # 요청률 기반 권장사항
        if avg_requests > 1000:  # 초당 1000건 초과
            recommendations.append(
                {
                    "type": "scale_out",
                    "resource": "requests",
                    "current_value": avg_requests,
                    "recommended_action": "Add more server instances to handle load",
                    "priority": "medium",
                }
            )

        return recommendations


# 전역 인스턴스
_metrics_collector: Optional[MetricsCollector] = None
_performance_dashboard: Optional[PerformanceDashboard] = None
_scaling_engine: Optional[ScalingRecommendationEngine] = None


def get_metrics_collector() -> MetricsCollector:
    """메트릭 수집기 싱글톤 인스턴스"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_performance_dashboard() -> PerformanceDashboard:
    """성능 대시보드 싱글톤 인스턴스"""
    global _performance_dashboard
    if _performance_dashboard is None:
        collector = get_metrics_collector()
        _performance_dashboard = PerformanceDashboard(collector)
    return _performance_dashboard


def get_scaling_engine() -> ScalingRecommendationEngine:
    """스케일링 엔진 싱글톤 인스턴스"""
    global _scaling_engine
    if _scaling_engine is None:
        collector = get_metrics_collector()
        _scaling_engine = ScalingRecommendationEngine(collector)
    return _scaling_engine
