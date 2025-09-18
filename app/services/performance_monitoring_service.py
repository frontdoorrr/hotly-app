"""
성능 모니터링 및 APM 통합 서비스

API 응답 최적화, 성능 튜닝, 대시보드를 위한 종합 성능 모니터링 시스템입니다.
TDD 방식으로 개발된 프로덕션 레디 APM 서비스입니다.
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from functools import wraps
import threading
from concurrent.futures import ThreadPoolExecutor
import statistics
import random
from enum import Enum

# from app.core.config import settings
from app.services.logging_service import logging_service, LogLevel


class MetricType(str, Enum):
    """메트릭 타입"""
    RESPONSE_TIME = "response_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    REQUEST_RATE = "request_rate"


class AlertSeverity(str, Enum):
    """알림 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터"""
    timestamp: datetime
    metric_type: MetricType
    value: float
    service: str
    endpoint: Optional[str] = None
    labels: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertEvent:
    """알림 이벤트"""
    type: str
    message: str
    timestamp: str
    severity: AlertSeverity
    metric_value: Optional[float] = None
    threshold: Optional[float] = None


class PerformanceMetricsCollector:
    """성능 메트릭 수집기"""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
        self.cache_stats = {
            "hit_count": 0,
            "miss_count": 0,
            "total_time": 0,
            "operations": []
        }
        self.query_metrics: List[Dict] = []
        self._lock = threading.Lock()
    
    def measure_response_time(self, endpoint: str, method: str):
        """응답 시간 측정 데코레이터"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end_time = time.perf_counter()
                    duration_ms = (end_time - start_time) * 1000
                    
                    key = f"{method}_{endpoint}"
                    with self._lock:
                        self.response_times[key].append(duration_ms)
            
            return wrapper
        return decorator
    
    def track_cache_operation(self, operation: str, hit: bool, duration_ms: float):
        """캐시 연산 추적"""
        with self._lock:
            self.cache_stats["operations"].append({
                "operation": operation,
                "hit": hit,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            })
            
            if hit:
                self.cache_stats["hit_count"] += 1
            else:
                self.cache_stats["miss_count"] += 1
            
            self.cache_stats["total_time"] += duration_ms
    
    def monitor_query_performance(self, query: str, execution_time: float, rows_affected: int):
        """데이터베이스 쿼리 성능 모니터링"""
        with self._lock:
            self.query_metrics.append({
                "query": query[:50] + "..." if len(query) > 50 else query,
                "execution_time_ms": execution_time,
                "rows_affected": rows_affected,
                "timestamp": datetime.now().isoformat(),
                "slow_query": execution_time > 100  # 100ms 이상은 느린 쿼리
            })
    
    def get_response_times(self, endpoint_key: str) -> List[float]:
        """응답 시간 조회"""
        with self._lock:
            return self.response_times.get(endpoint_key, []).copy()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        with self._lock:
            return self.cache_stats.copy()
    
    def get_query_metrics(self) -> List[Dict]:
        """쿼리 메트릭 조회"""
        with self._lock:
            return self.query_metrics.copy()


class PerformanceDashboard:
    """성능 대시보드"""
    
    def __init__(self):
        self.current_metrics: Dict[str, Any] = {}
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[AlertEvent] = []
        self.performance_trends: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        # 임계값 설정
        self.thresholds = {
            "response_time_p95": 1000,  # 1초
            "cache_hit_rate_min": 0.7,   # 70%
            "cpu_usage_max": 80,         # 80%
            "memory_usage_max": 85,      # 85%
            "error_rate_max": 0.05       # 5%
        }
    
    def update_dashboard_metrics(self, metrics: Dict[str, Any]):
        """대시보드 메트릭 업데이트"""
        timestamp = datetime.now().isoformat()
        
        with self._lock:
            self.current_metrics = {
                **metrics,
                "timestamp": timestamp
            }
            
            # 히스토리에 추가 (최근 100개만 유지)
            self.metrics_history.append({
                **metrics,
                "timestamp": timestamp
            })
            
            if len(self.metrics_history) > 100:
                self.metrics_history = self.metrics_history[-100:]
            
            # 임계값 체크 및 알림 생성
            self._check_thresholds(metrics, timestamp)
    
    def _check_thresholds(self, metrics: Dict[str, Any], timestamp: str):
        """임계값 체크 및 알림 생성"""
        # P95 응답 시간 체크
        if metrics.get("response_time_p95", 0) > self.thresholds["response_time_p95"]:
            self.alerts.append(AlertEvent(
                type="high_response_time",
                message=f"P95 response time: {metrics['response_time_p95']}ms",
                timestamp=timestamp,
                severity=AlertSeverity.WARNING,
                metric_value=metrics["response_time_p95"],
                threshold=self.thresholds["response_time_p95"]
            ))
        
        # 캐시 적중률 체크
        if metrics.get("cache_hit_rate", 1.0) < self.thresholds["cache_hit_rate_min"]:
            self.alerts.append(AlertEvent(
                type="low_cache_hit_rate",
                message=f"Cache hit rate: {metrics['cache_hit_rate']:.1%}",
                timestamp=timestamp,
                severity=AlertSeverity.WARNING,
                metric_value=metrics["cache_hit_rate"],
                threshold=self.thresholds["cache_hit_rate_min"]
            ))
        
        # CPU 사용률 체크
        if metrics.get("cpu_usage", 0) > self.thresholds["cpu_usage_max"]:
            self.alerts.append(AlertEvent(
                type="high_cpu_usage",
                message=f"CPU usage: {metrics['cpu_usage']}%",
                timestamp=timestamp,
                severity=AlertSeverity.ERROR if metrics["cpu_usage"] > 90 else AlertSeverity.WARNING,
                metric_value=metrics["cpu_usage"],
                threshold=self.thresholds["cpu_usage_max"]
            ))
    
    def analyze_performance_trends(self, hours: int = 1) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 문자열 타임스탬프를 datetime으로 변환하여 필터링
            recent_metrics = []
            for m in self.metrics_history:
                try:
                    metric_time = datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00'))
                    if metric_time >= cutoff_time:
                        recent_metrics.append(m)
                except:
                    # 타임스탬프 파싱 실패 시 무시
                    continue
            
            if not recent_metrics:
                return {"trend": "no_data"}
            
            # 평균 계산
            if len(recent_metrics) == 0:
                return {"trend": "insufficient_data"}
            
            avg_response_time = sum(m.get("response_time_avg", 0) for m in recent_metrics) / len(recent_metrics)
            avg_cache_hit_rate = sum(m.get("cache_hit_rate", 0) for m in recent_metrics) / len(recent_metrics)
            avg_error_rate = sum(m.get("error_rate", 0) for m in recent_metrics) / len(recent_metrics)
            
            # 트렌드 계산 (첫 번째 vs 마지막 값 비교)
            if len(recent_metrics) >= 2:
                first = recent_metrics[0]
                last = recent_metrics[-1]
                
                response_time_trend = ("improving" if last.get("response_time_avg", 0) < first.get("response_time_avg", 0) 
                                     else ("degrading" if last.get("response_time_avg", 0) > first.get("response_time_avg", 0) 
                                           else "stable"))
                cache_trend = ("improving" if last.get("cache_hit_rate", 0) > first.get("cache_hit_rate", 0)
                              else ("degrading" if last.get("cache_hit_rate", 0) < first.get("cache_hit_rate", 0)
                                    else "stable"))
                error_trend = ("improving" if last.get("error_rate", 0) < first.get("error_rate", 0)
                              else ("degrading" if last.get("error_rate", 0) > first.get("error_rate", 0)
                                    else "stable"))
            else:
                response_time_trend = cache_trend = error_trend = "stable"
            
            trend_analysis = {
                "period_hours": hours,
                "data_points": len(recent_metrics),
                "averages": {
                    "response_time": avg_response_time,
                    "cache_hit_rate": avg_cache_hit_rate,
                    "error_rate": avg_error_rate
                },
                "trends": {
                    "response_time": response_time_trend,
                    "cache_hit_rate": cache_trend,
                    "error_rate": error_trend
                }
            }
            
            self.performance_trends = trend_analysis
            return trend_analysis
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """현재 메트릭 조회"""
        with self._lock:
            return self.current_metrics.copy()
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """알림 목록 조회"""
        with self._lock:
            return [
                {
                    "type": alert.type,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "severity": alert.severity.value,
                    "metric_value": alert.metric_value,
                    "threshold": alert.threshold
                }
                for alert in self.alerts
            ]


class PerformanceOptimizer:
    """성능 최적화 시스템"""
    
    def __init__(self):
        self.slow_queries: List[Dict] = []
        self.query_threshold_ms = 100
        self.endpoint_stats: Dict[str, Dict] = {}
        self.resource_metrics: Dict[str, List[float]] = {
            "cpu_usage": [],
            "memory_usage": [],
            "request_rate": [],
            "response_time": []
        }
        self._lock = threading.Lock()
    
    def detect_slow_query(self, query: str, execution_time_ms: float, params: Dict = None):
        """느린 쿼리 감지"""
        if execution_time_ms > self.query_threshold_ms:
            with self._lock:
                self.slow_queries.append({
                    "query": query,
                    "execution_time_ms": execution_time_ms,
                    "params": params or {},
                    "detected_at": datetime.now().isoformat(),
                    "optimization_suggestions": self._generate_optimization_suggestions(query, execution_time_ms)
                })
    
    def _generate_optimization_suggestions(self, query: str, time_ms: float) -> List[str]:
        """최적화 제안 생성"""
        suggestions = []
        query_upper = query.upper()
        
        if "SELECT *" in query_upper:
            suggestions.append("Avoid SELECT *, specify only needed columns")
        
        if "LIKE" in query_upper and "%" in query:
            suggestions.append("Consider full-text search or proper indexing for LIKE patterns")
        
        if time_ms > 500:
            suggestions.append("Query takes too long, consider query restructuring or caching")
        
        if "JOIN" in query_upper and time_ms > 200:
            suggestions.append("Optimize JOIN conditions and ensure proper indexing")
        
        return suggestions
    
    def track_endpoint_performance(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
        """엔드포인트 성능 추적"""
        key = f"{method} {endpoint}"
        
        with self._lock:
            if key not in self.endpoint_stats:
                self.endpoint_stats[key] = {
                    "total_requests": 0,
                    "total_time": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "min_time": float('inf'),
                    "max_time": 0
                }
            
            stats = self.endpoint_stats[key]
            stats["total_requests"] += 1
            stats["total_time"] += response_time_ms
            
            if 200 <= status_code < 400:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1
            
            stats["min_time"] = min(stats["min_time"], response_time_ms)
            stats["max_time"] = max(stats["max_time"], response_time_ms)
    
    def get_performance_ranking(self) -> List[Dict[str, Any]]:
        """성능 순위 조회"""
        with self._lock:
            ranking = []
            
            for endpoint, stats in self.endpoint_stats.items():
                if stats["total_requests"] == 0:
                    continue
                
                avg_time = stats["total_time"] / stats["total_requests"]
                success_rate = stats["success_count"] / stats["total_requests"]
                
                ranking.append({
                    "endpoint": endpoint,
                    "avg_response_time": avg_time,
                    "success_rate": success_rate,
                    "total_requests": stats["total_requests"],
                    "min_time": stats["min_time"],
                    "max_time": stats["max_time"],
                    "performance_score": success_rate * (1000 / max(avg_time, 1))  # 높을수록 좋음
                })
            
            # 성능 점수로 정렬 (높은 순)
            return sorted(ranking, key=lambda x: x["performance_score"], reverse=True)
    
    def collect_resource_metrics(self, cpu: float, memory: float, request_rate: int, response_time: float):
        """리소스 메트릭 수집"""
        with self._lock:
            self.resource_metrics["cpu_usage"].append(cpu)
            self.resource_metrics["memory_usage"].append(memory)
            self.resource_metrics["request_rate"].append(request_rate)
            self.resource_metrics["response_time"].append(response_time)
    
    def generate_scaling_recommendations(self) -> List[Dict[str, Any]]:
        """스케일링 권장사항 생성"""
        with self._lock:
            recommendations = []
            
            if not self.resource_metrics["cpu_usage"]:
                return recommendations
            
            avg_cpu = sum(self.resource_metrics["cpu_usage"]) / len(self.resource_metrics["cpu_usage"])
            avg_memory = sum(self.resource_metrics["memory_usage"]) / len(self.resource_metrics["memory_usage"])
            avg_request_rate = sum(self.resource_metrics["request_rate"]) / len(self.resource_metrics["request_rate"])
            avg_response_time = sum(self.resource_metrics["response_time"]) / len(self.resource_metrics["response_time"])
            
            # CPU 기반 권장사항
            if avg_cpu > 80:
                recommendations.append({
                    "type": "scale_up",
                    "resource": "cpu",
                    "current_usage": avg_cpu,
                    "recommended_action": "Increase CPU cores or scale out",
                    "priority": "high" if avg_cpu > 90 else "medium"
                })
            elif avg_cpu < 20:
                recommendations.append({
                    "type": "scale_down",
                    "resource": "cpu",
                    "current_usage": avg_cpu,
                    "recommended_action": "Consider reducing CPU allocation",
                    "priority": "low"
                })
            
            # 메모리 기반 권장사항
            if avg_memory > 85:
                recommendations.append({
                    "type": "scale_up",
                    "resource": "memory",
                    "current_usage": avg_memory,
                    "recommended_action": "Increase memory allocation",
                    "priority": "high" if avg_memory > 95 else "medium"
                })
            
            # 응답시간 기반 권장사항
            if avg_response_time > 1000:  # 1초 초과
                recommendations.append({
                    "type": "performance",
                    "resource": "response_time",
                    "current_value": avg_response_time,
                    "recommended_action": "Scale out or optimize application performance",
                    "priority": "high"
                })
            
            return recommendations
    
    def get_slow_queries(self) -> List[Dict]:
        """느린 쿼리 목록 조회"""
        with self._lock:
            return self.slow_queries.copy()


class APMIntegrationService:
    """APM 통합 서비스"""
    
    def __init__(self):
        self.metrics_collector = PerformanceMetricsCollector()
        self.dashboard = PerformanceDashboard()
        self.optimizer = PerformanceOptimizer()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._monitoring_active = False
        self._monitoring_task = None
    
    async def start_monitoring(self):
        """모니터링 시작"""
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logging_service.log(LogLevel.INFO, "APM monitoring started")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
        logging_service.log(LogLevel.INFO, "APM monitoring stopped")
    
    async def _monitoring_loop(self):
        """모니터링 루프"""
        while self._monitoring_active:
            try:
                # 시스템 메트릭 수집 (실제 구현에서는 시스템 API 사용)
                metrics = self._collect_system_metrics()
                
                # 대시보드 업데이트
                self.dashboard.update_dashboard_metrics(metrics)
                
                # 트렌드 분석
                self.dashboard.analyze_performance_trends()
                
                await asyncio.sleep(10)  # 10초마다 수집
            except Exception as e:
                logging_service.log(LogLevel.ERROR, f"Monitoring loop error: {e}")
                await asyncio.sleep(5)
    
    def _collect_system_metrics(self) -> Dict[str, Any]:
        """시스템 메트릭 수집 (시뮬레이션)"""
        # 실제 구현에서는 시스템 API를 사용
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": random.uniform(20, 90),
            "memory_usage": random.uniform(30, 85),
            "response_time_avg": random.uniform(50, 500),
            "response_time_p95": random.uniform(100, 1000),
            "cache_hit_rate": random.uniform(0.6, 0.95),
            "error_rate": random.uniform(0, 0.1),
            "requests_per_second": random.randint(50, 300),
            "active_connections": random.randint(10, 100)
        }
    
    def measure_response_time(self, endpoint: str, method: str = "GET"):
        """응답 시간 측정 데코레이터"""
        return self.metrics_collector.measure_response_time(endpoint, method)
    
    def track_cache_operation(self, operation: str, hit: bool, duration_ms: float):
        """캐시 연산 추적"""
        self.metrics_collector.track_cache_operation(operation, hit, duration_ms)
    
    def monitor_query_performance(self, query: str, execution_time: float, rows_affected: int):
        """쿼리 성능 모니터링"""
        self.metrics_collector.monitor_query_performance(query, execution_time, rows_affected)
        self.optimizer.detect_slow_query(query, execution_time)
    
    def track_endpoint_performance(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
        """엔드포인트 성능 추적"""
        self.optimizer.track_endpoint_performance(endpoint, method, response_time_ms, status_code)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        return {
            "current_metrics": self.dashboard.get_current_metrics(),
            "alerts": self.dashboard.get_alerts(),
            "performance_ranking": self.optimizer.get_performance_ranking(),
            "slow_queries": self.optimizer.get_slow_queries(),
            "scaling_recommendations": self.optimizer.generate_scaling_recommendations()
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        return self.metrics_collector.get_cache_stats()
    
    def analyze_trends(self, hours: int = 1) -> Dict[str, Any]:
        """성능 트렌드 분석"""
        return self.dashboard.analyze_performance_trends(hours)


# 글로벌 APM 서비스 인스턴스
apm_service = APMIntegrationService()


def get_apm_service() -> APMIntegrationService:
    """APM 서비스 인스턴스 조회"""
    return apm_service


# 편의 함수들
def monitor_performance(endpoint: str, method: str = "GET"):
    """성능 모니터링 데코레이터"""
    return apm_service.measure_response_time(endpoint, method)


def track_cache_hit(operation: str, duration_ms: float):
    """캐시 히트 추적"""
    apm_service.track_cache_operation(operation, True, duration_ms)


def track_cache_miss(operation: str, duration_ms: float):
    """캐시 미스 추적"""
    apm_service.track_cache_operation(operation, False, duration_ms)


def monitor_slow_query(query: str, execution_time: float, rows_affected: int = 0):
    """느린 쿼리 모니터링"""
    apm_service.monitor_query_performance(query, execution_time, rows_affected)