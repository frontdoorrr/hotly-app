"""
성능 대시보드 TDD 테스트

API 응답 최적화 및 성능 튜닝 대시보드를 위한 TDD 테스트를 정의합니다.
"""
# from fastapi.testclient import TestClient
# from fastapi import status
import time

# import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List


class TestPerformanceMetricsCollector:
    """성능 메트릭 수집기 테스트"""

    def test_api_response_time_measurement(self):
        """API 응답 시간 측정 테스트"""
        # Given: 성능 메트릭 수집기
        metrics_collector = {}

        def measure_response_time(endpoint: str, method: str):
            """응답 시간 측정 데코레이터"""

            def decorator(func):
                def wrapper(*args, **kwargs):
                    start_time = time.perf_counter()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        end_time = time.perf_counter()
                        duration_ms = (end_time - start_time) * 1000

                        key = f"{method}_{endpoint}"
                        if key not in metrics_collector:
                            metrics_collector[key] = []
                        metrics_collector[key].append(duration_ms)

                return wrapper

            return decorator

        # When: API 엔드포인트 호출 시뮬레이션
        @measure_response_time("/api/v1/places", "GET")
        def get_places():
            time.sleep(0.01)  # 10ms 시뮬레이션
            return {"places": []}

        # 여러 번 호출
        for _ in range(5):
            get_places()

        # Then: 응답 시간이 수집됨
        assert "GET_/api/v1/places" in metrics_collector
        response_times = metrics_collector["GET_/api/v1/places"]
        assert len(response_times) == 5
        assert all(rt >= 10.0 for rt in response_times)  # 최소 10ms
        assert all(rt < 50.0 for rt in response_times)  # 최대 50ms

        print("✅ API 응답 시간 측정 테스트 통과")

    def test_cache_performance_tracking(self):
        """캐시 성능 추적 테스트"""
        # Given: 캐시 성능 추적기
        cache_metrics = {
            "hit_count": 0,
            "miss_count": 0,
            "total_time": 0,
            "operations": [],
        }

        def track_cache_operation(operation: str, hit: bool, duration_ms: float):
            """캐시 연산 추적"""
            cache_metrics["operations"].append(
                {
                    "operation": operation,
                    "hit": hit,
                    "duration_ms": duration_ms,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            if hit:
                cache_metrics["hit_count"] += 1
            else:
                cache_metrics["miss_count"] += 1

            cache_metrics["total_time"] += duration_ms

        # When: 캐시 연산 시뮬레이션
        track_cache_operation("GET", True, 0.5)  # 캐시 히트 - 빠름
        track_cache_operation("GET", False, 25.0)  # 캐시 미스 - 느림
        track_cache_operation("GET", True, 0.3)  # 캐시 히트 - 빠름
        track_cache_operation("SET", True, 1.2)  # 캐시 설정

        # Then: 캐시 성능 메트릭 수집
        assert cache_metrics["hit_count"] == 3
        assert cache_metrics["miss_count"] == 1
        assert len(cache_metrics["operations"]) == 4

        hit_rate = cache_metrics["hit_count"] / (
            cache_metrics["hit_count"] + cache_metrics["miss_count"]
        )
        assert hit_rate == 0.75  # 75% 적중률

        avg_time = cache_metrics["total_time"] / len(cache_metrics["operations"])
        assert avg_time == (0.5 + 25.0 + 0.3 + 1.2) / 4

        print("✅ 캐시 성능 추적 테스트 통과")

    def test_database_query_performance(self):
        """데이터베이스 쿼리 성능 측정 테스트"""
        # Given: DB 성능 모니터링
        query_metrics = []

        def monitor_query_performance(
            query: str, execution_time: float, rows_affected: int
        ):
            """쿼리 성능 모니터링"""
            query_metrics.append(
                {
                    "query": query[:50] + "..." if len(query) > 50 else query,
                    "execution_time_ms": execution_time,
                    "rows_affected": rows_affected,
                    "timestamp": datetime.now().isoformat(),
                    "slow_query": execution_time > 100,  # 100ms 이상은 느린 쿼리
                }
            )

        # When: 다양한 쿼리 시뮬레이션
        monitor_query_performance("SELECT * FROM places WHERE id = ?", 2.5, 1)
        monitor_query_performance(
            "SELECT * FROM places WHERE category LIKE '%restaurant%'", 150.0, 500
        )
        monitor_query_performance("INSERT INTO user_activities (...)", 5.0, 1)
        monitor_query_performance(
            "UPDATE places SET updated_at = NOW() WHERE ...", 45.0, 20
        )

        # Then: 쿼리 성능 분석
        assert len(query_metrics) == 4

        slow_queries = [q for q in query_metrics if q["slow_query"]]
        assert len(slow_queries) == 1
        assert "SELECT * FROM places WHERE category LIKE" in slow_queries[0]["query"]

        fast_queries = [q for q in query_metrics if not q["slow_query"]]
        assert len(fast_queries) == 3

        avg_time = sum(q["execution_time_ms"] for q in query_metrics) / len(
            query_metrics
        )
        assert avg_time == (2.5 + 150.0 + 5.0 + 45.0) / 4

        print("✅ 데이터베이스 쿼리 성능 측정 테스트 통과")


class TestPerformanceDashboard:
    """성능 대시보드 테스트"""

    def test_real_time_metrics_display(self):
        """실시간 메트릭 표시 테스트"""
        # Given: 실시간 메트릭 대시보드
        dashboard_data = {"current_metrics": {}, "history": [], "alerts": []}

        def update_dashboard_metrics(metrics: Dict[str, Any]):
            """대시보드 메트릭 업데이트"""
            timestamp = datetime.now().isoformat()
            dashboard_data["current_metrics"] = {**metrics, "timestamp": timestamp}

            # 히스토리에 추가 (최근 100개만 유지)
            dashboard_data["history"].append({**metrics, "timestamp": timestamp})

            if len(dashboard_data["history"]) > 100:
                dashboard_data["history"] = dashboard_data["history"][-100:]

            # 임계값 체크 및 알림
            if metrics.get("response_time_p95", 0) > 1000:  # 1초 초과
                dashboard_data["alerts"].append(
                    {
                        "type": "high_response_time",
                        "message": f"P95 response time: {metrics['response_time_p95']}ms",
                        "timestamp": timestamp,
                        "severity": "warning",
                    }
                )

        # When: 메트릭 업데이트
        test_metrics = {
            "active_connections": 45,
            "requests_per_second": 120,
            "response_time_avg": 250,
            "response_time_p95": 800,
            "cache_hit_rate": 0.85,
            "error_rate": 0.02,
        }

        update_dashboard_metrics(test_metrics)

        # Then: 대시보드 데이터 확인
        assert dashboard_data["current_metrics"]["active_connections"] == 45
        assert dashboard_data["current_metrics"]["requests_per_second"] == 120
        assert dashboard_data["current_metrics"]["cache_hit_rate"] == 0.85
        assert "timestamp" in dashboard_data["current_metrics"]

        assert len(dashboard_data["history"]) == 1
        assert len(dashboard_data["alerts"]) == 0  # 임계값 미초과로 알림 없음

        # When: 임계값 초과 메트릭
        alert_metrics = {**test_metrics, "response_time_p95": 1500}  # 임계값 초과

        update_dashboard_metrics(alert_metrics)

        # Then: 알림 생성 확인
        assert len(dashboard_data["alerts"]) == 1
        assert dashboard_data["alerts"][0]["type"] == "high_response_time"
        assert dashboard_data["alerts"][0]["severity"] == "warning"

        print("✅ 실시간 메트릭 표시 테스트 통과")

    def test_performance_trend_analysis(self):
        """성능 트렌드 분석 테스트"""
        # Given: 성능 트렌드 분석기
        metrics_history = []

        def add_metrics_snapshot(
            response_time: float, cache_hit_rate: float, error_rate: float
        ):
            """메트릭 스냅샷 추가"""
            metrics_history.append(
                {
                    "timestamp": datetime.now(),
                    "response_time": response_time,
                    "cache_hit_rate": cache_hit_rate,
                    "error_rate": error_rate,
                }
            )

        def analyze_performance_trend(hours: int = 1) -> Dict[str, Any]:
            """성능 트렌드 분석"""
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = [
                m for m in metrics_history if m["timestamp"] >= cutoff_time
            ]

            if not recent_metrics:
                return {"trend": "no_data"}

            # 평균 계산
            avg_response_time = sum(m["response_time"] for m in recent_metrics) / len(
                recent_metrics
            )
            avg_cache_hit_rate = sum(m["cache_hit_rate"] for m in recent_metrics) / len(
                recent_metrics
            )
            avg_error_rate = sum(m["error_rate"] for m in recent_metrics) / len(
                recent_metrics
            )

            # 트렌드 계산 (첫 번째 vs 마지막 값 비교)
            if len(recent_metrics) >= 2:
                first = recent_metrics[0]
                last = recent_metrics[-1]

                response_time_trend = (
                    "improving"
                    if last["response_time"] < first["response_time"]
                    else (
                        "degrading"
                        if last["response_time"] > first["response_time"]
                        else "stable"
                    )
                )
                cache_trend = (
                    "improving"
                    if last["cache_hit_rate"] > first["cache_hit_rate"]
                    else (
                        "degrading"
                        if last["cache_hit_rate"] < first["cache_hit_rate"]
                        else "stable"
                    )
                )
                error_trend = (
                    "improving"
                    if last["error_rate"] < first["error_rate"]
                    else (
                        "degrading"
                        if last["error_rate"] > first["error_rate"]
                        else "stable"
                    )
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

        # When: 시간 흐름에 따른 메트릭 추가
        # 성능이 점진적으로 개선되는 시나리오
        add_metrics_snapshot(300.0, 0.70, 0.05)  # 초기 - 성능 나쁨
        add_metrics_snapshot(250.0, 0.75, 0.04)  # 개선 중
        add_metrics_snapshot(200.0, 0.80, 0.03)  # 더 개선
        add_metrics_snapshot(180.0, 0.85, 0.02)  # 최종 - 성능 좋음

        analysis = analyze_performance_trend(1)

        # Then: 트렌드 분석 결과 확인
        assert analysis["data_points"] == 4
        # 트렌드 분석은 첫 번째와 마지막 값을 비교
        # 300->180 (improving), 0.70->0.85 (improving), 0.05->0.02 (improving)
        assert analysis["trends"]["response_time"] == "improving"
        assert analysis["trends"]["cache_hit_rate"] == "improving"
        assert analysis["trends"]["error_rate"] == "improving"

        import math

        assert analysis["averages"]["response_time"] == (300 + 250 + 200 + 180) / 4
        assert analysis["averages"]["cache_hit_rate"] == (0.70 + 0.75 + 0.80 + 0.85) / 4
        assert math.isclose(
            analysis["averages"]["error_rate"], (0.05 + 0.04 + 0.03 + 0.02) / 4
        )

        print("✅ 성능 트렌드 분석 테스트 통과")


class TestPerformanceOptimization:
    """성능 최적화 테스트"""

    def test_slow_query_detection(self):
        """느린 쿼리 감지 테스트"""
        # Given: 느린 쿼리 감지 시스템
        slow_queries = []
        query_threshold_ms = 100

        def detect_slow_query(
            query: str, execution_time_ms: float, params: Dict = None
        ):
            """느린 쿼리 감지"""
            if execution_time_ms > query_threshold_ms:
                slow_queries.append(
                    {
                        "query": query,
                        "execution_time_ms": execution_time_ms,
                        "params": params or {},
                        "detected_at": datetime.now().isoformat(),
                        "optimization_suggestions": generate_optimization_suggestions(
                            query, execution_time_ms
                        ),
                    }
                )

        def generate_optimization_suggestions(query: str, time_ms: float) -> List[str]:
            """최적화 제안 생성"""
            suggestions = []

            if "SELECT *" in query.upper():
                suggestions.append("Avoid SELECT *, specify only needed columns")

            if "LIKE" in query.upper() and "%" in query:
                suggestions.append(
                    "Consider full-text search or proper indexing for LIKE patterns"
                )

            if time_ms > 500:
                suggestions.append(
                    "Query takes too long, consider query restructuring or caching"
                )

            if "JOIN" in query.upper() and time_ms > 200:
                suggestions.append(
                    "Optimize JOIN conditions and ensure proper indexing"
                )

            return suggestions

        # When: 다양한 쿼리 시뮬레이션
        detect_slow_query(
            "SELECT id, name FROM places WHERE category = ?",
            50,
            {"category": "restaurant"},
        )
        detect_slow_query(
            "SELECT * FROM places WHERE name LIKE '%pizza%'", 250, {"pattern": "pizza"}
        )
        detect_slow_query(
            "SELECT p.*, r.* FROM places p JOIN reviews r ON p.id = r.place_id", 350
        )
        detect_slow_query(
            "SELECT COUNT(*) FROM user_activities WHERE created_at > ?", 80
        )

        # Then: 느린 쿼리 감지 및 최적화 제안
        assert len(slow_queries) == 2  # 250ms, 350ms 쿼리

        like_query = next(q for q in slow_queries if "LIKE" in q["query"])
        suggestions = like_query["optimization_suggestions"]
        assert any("Avoid SELECT *" in suggestion for suggestion in suggestions)
        assert any("full-text search" in suggestion for suggestion in suggestions)

        join_query = next(q for q in slow_queries if "JOIN" in q["query"])
        assert any(
            "Optimize JOIN conditions" in suggestion
            for suggestion in join_query["optimization_suggestions"]
        )

        print("✅ 느린 쿼리 감지 테스트 통과")

    def test_api_endpoint_performance_ranking(self):
        """API 엔드포인트 성능 순위 테스트"""
        # Given: 엔드포인트 성능 추적
        endpoint_stats = {}

        def track_endpoint_performance(
            endpoint: str, method: str, response_time_ms: float, status_code: int
        ):
            """엔드포인트 성능 추적"""
            key = f"{method} {endpoint}"

            if key not in endpoint_stats:
                endpoint_stats[key] = {
                    "total_requests": 0,
                    "total_time": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "min_time": float("inf"),
                    "max_time": 0,
                }

            stats = endpoint_stats[key]
            stats["total_requests"] += 1
            stats["total_time"] += response_time_ms

            if 200 <= status_code < 400:
                stats["success_count"] += 1
            else:
                stats["error_count"] += 1

            stats["min_time"] = min(stats["min_time"], response_time_ms)
            stats["max_time"] = max(stats["max_time"], response_time_ms)

        def get_performance_ranking() -> List[Dict[str, Any]]:
            """성능 순위 조회"""
            ranking = []

            for endpoint, stats in endpoint_stats.items():
                avg_time = stats["total_time"] / stats["total_requests"]
                success_rate = stats["success_count"] / stats["total_requests"]

                ranking.append(
                    {
                        "endpoint": endpoint,
                        "avg_response_time": avg_time,
                        "success_rate": success_rate,
                        "total_requests": stats["total_requests"],
                        "min_time": stats["min_time"],
                        "max_time": stats["max_time"],
                        "performance_score": success_rate
                        * (1000 / max(avg_time, 1)),  # 높을수록 좋음
                    }
                )

            # 성능 점수로 정렬 (높은 순)
            return sorted(ranking, key=lambda x: x["performance_score"], reverse=True)

        # When: 다양한 엔드포인트 성능 데이터
        # 빠르고 안정적인 엔드포인트
        for _ in range(10):
            track_endpoint_performance("/api/v1/health", "GET", 5.0, 200)

        # 보통 성능 엔드포인트
        for _ in range(20):
            track_endpoint_performance("/api/v1/places", "GET", 150.0, 200)

        # 느리지만 안정적인 엔드포인트
        for _ in range(5):
            track_endpoint_performance("/api/v1/search", "POST", 800.0, 200)

        # 빠르지만 에러가 있는 엔드포인트
        for _ in range(8):
            track_endpoint_performance("/api/v1/users", "GET", 50.0, 200)
        for _ in range(2):
            track_endpoint_performance("/api/v1/users", "GET", 60.0, 500)

        ranking = get_performance_ranking()

        # Then: 성능 순위 확인
        assert len(ranking) == 4

        # 최고 성능은 health 엔드포인트 (빠르고 100% 성공)
        best_performer = ranking[0]
        assert best_performer["endpoint"] == "GET /api/v1/health"
        assert best_performer["success_rate"] == 1.0
        assert best_performer["avg_response_time"] == 5.0

        # 성능 점수 순서대로 정렬 확인
        scores = [ep["performance_score"] for ep in ranking]
        assert scores == sorted(scores, reverse=True)

        # 에러가 있는 엔드포인트의 성공률 확인
        users_endpoint = next(ep for ep in ranking if "/users" in ep["endpoint"])
        assert users_endpoint["success_rate"] == 0.8  # 8/10

        print("✅ API 엔드포인트 성능 순위 테스트 통과")

    def test_automatic_scaling_recommendations(self):
        """자동 스케일링 권장사항 테스트"""
        # Given: 스케일링 권장 시스템
        resource_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "request_rate": [],
            "response_time": [],
        }

        def collect_resource_metrics(
            cpu: float, memory: float, request_rate: int, response_time: float
        ):
            """리소스 메트릭 수집"""
            resource_metrics["cpu_usage"].append(cpu)
            resource_metrics["memory_usage"].append(memory)
            resource_metrics["request_rate"].append(request_rate)
            resource_metrics["response_time"].append(response_time)

        def generate_scaling_recommendations() -> List[Dict[str, Any]]:
            """스케일링 권장사항 생성"""
            recommendations = []

            if not resource_metrics["cpu_usage"]:
                return recommendations

            avg_cpu = sum(resource_metrics["cpu_usage"]) / len(
                resource_metrics["cpu_usage"]
            )
            avg_memory = sum(resource_metrics["memory_usage"]) / len(
                resource_metrics["memory_usage"]
            )
            avg_request_rate = sum(resource_metrics["request_rate"]) / len(
                resource_metrics["request_rate"]
            )
            avg_response_time = sum(resource_metrics["response_time"]) / len(
                resource_metrics["response_time"]
            )

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

            # 메모리 기반 권장사항
            if avg_memory > 85:
                recommendations.append(
                    {
                        "type": "scale_up",
                        "resource": "memory",
                        "current_usage": avg_memory,
                        "recommended_action": "Increase memory allocation",
                        "priority": "high" if avg_memory > 95 else "medium",
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

            return recommendations

        # When: 다양한 리소스 상황 시뮬레이션

        # 시나리오 1: 정상 상태
        for _ in range(5):
            collect_resource_metrics(45.0, 60.0, 100, 200.0)

        recommendations = generate_scaling_recommendations()
        assert len(recommendations) == 0  # 정상 상태라 권장사항 없음

        # 시나리오 2: 높은 CPU 사용률
        resource_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "request_rate": [],
            "response_time": [],
        }
        for _ in range(5):
            collect_resource_metrics(95.0, 70.0, 200, 300.0)

        recommendations = generate_scaling_recommendations()
        cpu_rec = next((r for r in recommendations if r["resource"] == "cpu"), None)
        assert cpu_rec is not None
        assert cpu_rec["type"] == "scale_up"
        assert cpu_rec["priority"] == "high"

        # 시나리오 3: 높은 메모리 + 느린 응답시간
        resource_metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "request_rate": [],
            "response_time": [],
        }
        for _ in range(5):
            collect_resource_metrics(60.0, 98.0, 150, 1500.0)

        recommendations = generate_scaling_recommendations()
        assert len(recommendations) == 2

        memory_rec = next(
            (r for r in recommendations if r["resource"] == "memory"), None
        )
        response_rec = next(
            (r for r in recommendations if r["resource"] == "response_time"), None
        )

        assert memory_rec["priority"] == "high"
        assert response_rec["priority"] == "high"
        assert "Scale out" in response_rec["recommended_action"]

        print("✅ 자동 스케일링 권장사항 테스트 통과")


def main():
    """성능 대시보드 테스트 실행"""
    print("🎯 성능 대시보드 TDD 테스트 시작")
    print("=" * 60)

    test_classes = [
        TestPerformanceMetricsCollector(),
        TestPerformanceDashboard(),
        TestPerformanceOptimization(),
    ]

    total_passed = 0
    total_failed = 0

    for test_instance in test_classes:
        class_name = test_instance.__class__.__name__
        print(f"\n📊 {class_name} 테스트 실행")
        print("-" * 40)

        test_methods = [
            method for method in dir(test_instance) if method.startswith("test_")
        ]

        for method_name in test_methods:
            try:
                if hasattr(test_instance, "setup_method"):
                    test_instance.setup_method()

                test_method = getattr(test_instance, method_name)
                test_method()
                total_passed += 1
            except Exception as e:
                print(f"❌ {method_name} 실패: {e}")
                total_failed += 1

    print(f"\n📈 성능 대시보드 테스트 결과:")
    print(f"   ✅ 통과: {total_passed}")
    print(f"   ❌ 실패: {total_failed}")
    print(f"   📊 전체: {total_passed + total_failed}")

    if total_failed == 0:
        print("🏆 모든 성능 대시보드 테스트 통과!")
        return True
    else:
        print(f"⚠️ {total_failed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
