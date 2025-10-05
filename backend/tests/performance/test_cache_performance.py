"""
캐시 성능 테스트

캐시 성능 모니터링, 최적화, 메트릭 수집을 위한 TDD 테스트를 정의합니다.
"""
import statistics

# import pytest
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class CacheMetrics:
    """캐시 성능 메트릭"""

    hit_count: int = 0
    miss_count: int = 0
    total_requests: int = 0
    response_times: List[float] = None
    memory_usage: Dict[str, int] = None
    cache_sizes: Dict[str, int] = None

    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
        if self.memory_usage is None:
            self.memory_usage = {"l1": 0, "l2": 0, "l3": 0}
        if self.cache_sizes is None:
            self.cache_sizes = {"l1": 0, "l2": 0, "l3": 0}

    @property
    def hit_rate(self) -> float:
        """캐시 적중률"""
        if self.total_requests == 0:
            return 0.0
        return self.hit_count / self.total_requests

    @property
    def miss_rate(self) -> float:
        """캐시 미스율"""
        return 1.0 - self.hit_rate

    @property
    def avg_response_time(self) -> float:
        """평균 응답 시간"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        """95퍼센타일 응답 시간"""
        if not self.response_times or len(self.response_times) < 2:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[min(index, len(sorted_times) - 1)]


class TestCachePerformanceMetrics:
    """캐시 성능 메트릭 테스트"""

    def setup_method(self):
        """테스트 설정"""
        self.metrics = CacheMetrics()

    def test_cache_hit_rate_calculation(self):
        """캐시 적중률 계산 테스트"""
        # Given: 캐시 요청 통계
        self.metrics.hit_count = 70
        self.metrics.miss_count = 30
        self.metrics.total_requests = 100

        # When: 적중률 계산
        hit_rate = self.metrics.hit_rate
        miss_rate = self.metrics.miss_rate

        # Then: 올바른 적중률 계산
        assert hit_rate == 0.7
        assert abs(miss_rate - 0.3) < 0.001  # 부동소수점 오차 허용
        assert abs(hit_rate + miss_rate - 1.0) < 0.001  # 부동소수점 오차 허용

        print("✅ 캐시 적중률 계산 테스트 통과")

    def test_response_time_statistics(self):
        """응답 시간 통계 테스트"""
        # Given: 응답 시간 데이터
        response_times = [0.1, 0.2, 0.15, 0.3, 0.25, 0.4, 0.2, 0.1, 0.35, 0.5]
        self.metrics.response_times = response_times

        # When: 통계 계산
        avg_time = self.metrics.avg_response_time

        # Then: 올바른 통계 계산
        expected_avg = sum(response_times) / len(response_times)
        assert abs(avg_time - expected_avg) < 0.01
        assert avg_time > 0

        print("✅ 응답 시간 통계 테스트 통과")

    def test_memory_usage_tracking(self):
        """메모리 사용량 추적 테스트"""
        # Given: 계층별 메모리 사용량
        self.metrics.memory_usage = {
            "l1": 50 * 1024 * 1024,  # 50MB
            "l2": 200 * 1024 * 1024,  # 200MB
            "l3": 500 * 1024 * 1024,  # 500MB
        }

        # When: 총 메모리 사용량 계산
        total_memory = sum(self.metrics.memory_usage.values())
        memory_mb = {k: v / (1024 * 1024) for k, v in self.metrics.memory_usage.items()}

        # Then: 메모리 사용량 추적
        assert memory_mb["l1"] == 50
        assert memory_mb["l2"] == 200
        assert memory_mb["l3"] == 500
        assert total_memory == 750 * 1024 * 1024  # 750MB

        print("✅ 메모리 사용량 추적 테스트 통과")


class TestPerformanceMonitoring:
    """성능 모니터링 시스템 테스트"""

    def test_performance_monitoring_collection(self):
        """성능 메트릭 수집 테스트"""
        # Given: 성능 모니터링 시스템
        performance_data = []

        def collect_performance_metrics() -> Dict[str, Any]:
            """성능 메트릭 수집"""
            timestamp = datetime.now().isoformat()
            metrics = {
                "timestamp": timestamp,
                "cache_hit_rate": 0.75,
                "avg_response_time": 0.23,
                "memory_usage_mb": 156,
                "active_connections": 42,
                "cpu_usage_percent": 15.5,
                "requests_per_second": 120,
            }
            performance_data.append(metrics)
            return metrics

        def get_performance_trends(minutes: int = 5) -> Dict[str, List[float]]:
            """성능 트렌드 분석"""
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_data = [
                data
                for data in performance_data
                if datetime.fromisoformat(data["timestamp"]) >= cutoff_time
            ]

            if not recent_data:
                return {}

            return {
                "hit_rates": [d["cache_hit_rate"] for d in recent_data],
                "response_times": [d["avg_response_time"] for d in recent_data],
                "memory_usage": [d["memory_usage_mb"] for d in recent_data],
            }

        # When: 여러 시점의 성능 데이터 수집
        for i in range(5):
            collect_performance_metrics()
            time.sleep(0.01)  # 시간 간격

        trends = get_performance_trends(10)

        # Then: 성능 데이터 수집 및 트렌드 분석
        assert len(performance_data) == 5
        assert all("timestamp" in data for data in performance_data)
        assert all("cache_hit_rate" in data for data in performance_data)

        assert "hit_rates" in trends
        assert "response_times" in trends
        assert len(trends["hit_rates"]) == 5

        print("✅ 성능 메트릭 수집 테스트 통과")

    def test_performance_alerting_system(self):
        """성능 알림 시스템 테스트"""
        # Given: 성능 알림 시스템
        alerts = []
        thresholds = {
            "max_response_time": 1.0,  # 1초
            "min_hit_rate": 0.6,  # 60%
            "max_memory_usage": 200,  # 200MB
            "max_cpu_usage": 80,  # 80%
        }

        def check_performance_alerts(metrics: Dict[str, Any]):
            """성능 임계값 체크 및 알림"""
            current_alerts = []

            if metrics["avg_response_time"] > thresholds["max_response_time"]:
                current_alerts.append(
                    {
                        "type": "high_response_time",
                        "value": metrics["avg_response_time"],
                        "threshold": thresholds["max_response_time"],
                        "severity": "warning",
                    }
                )

            if metrics["cache_hit_rate"] < thresholds["min_hit_rate"]:
                current_alerts.append(
                    {
                        "type": "low_hit_rate",
                        "value": metrics["cache_hit_rate"],
                        "threshold": thresholds["min_hit_rate"],
                        "severity": "warning",
                    }
                )

            if metrics["memory_usage_mb"] > thresholds["max_memory_usage"]:
                current_alerts.append(
                    {
                        "type": "high_memory_usage",
                        "value": metrics["memory_usage_mb"],
                        "threshold": thresholds["max_memory_usage"],
                        "severity": "critical",
                    }
                )

            alerts.extend(current_alerts)
            return current_alerts

        # When: 임계값을 초과하는 메트릭
        problematic_metrics = {
            "cache_hit_rate": 0.45,  # 임계값 미달
            "avg_response_time": 1.5,  # 임계값 초과
            "memory_usage_mb": 250,  # 임계값 초과
            "cpu_usage_percent": 45,
        }

        normal_metrics = {
            "cache_hit_rate": 0.75,
            "avg_response_time": 0.3,
            "memory_usage_mb": 150,
            "cpu_usage_percent": 25,
        }

        problem_alerts = check_performance_alerts(problematic_metrics)
        normal_alerts = check_performance_alerts(normal_metrics)

        # Then: 적절한 알림 생성
        assert len(problem_alerts) == 3  # 3개 임계값 초과
        assert len(normal_alerts) == 0  # 정상 상태

        alert_types = [alert["type"] for alert in problem_alerts]
        assert "low_hit_rate" in alert_types
        assert "high_response_time" in alert_types
        assert "high_memory_usage" in alert_types

        # 심각도 체크
        memory_alert = next(
            a for a in problem_alerts if a["type"] == "high_memory_usage"
        )
        assert memory_alert["severity"] == "critical"

        print("✅ 성능 알림 시스템 테스트 통과")


class TestCacheOptimization:
    """캐시 최적화 테스트"""

    def test_cache_warming_strategy(self):
        """캐시 워밍 전략 테스트"""
        # Given: 캐시 워밍 시스템
        cache = {}
        popular_keys = ["place:123", "place:456", "place:789"]

        def warm_cache_with_popular_data():
            """인기 데이터로 캐시 워밍"""
            warmed_count = 0

            for key in popular_keys:
                # 인기 데이터를 미리 캐시에 로드
                cache_data = {
                    "key": key,
                    "data": f"popular_data_for_{key}",
                    "warmed_at": datetime.now().isoformat(),
                    "is_warmed": True,
                }
                cache[key] = cache_data
                warmed_count += 1

            return warmed_count

        def get_cache_warming_status() -> Dict[str, Any]:
            """캐시 워밍 상태 조회"""
            warmed_keys = [k for k, v in cache.items() if v.get("is_warmed", False)]
            return {
                "total_warmed": len(warmed_keys),
                "warmed_keys": warmed_keys,
                "warming_rate": len(warmed_keys) / len(popular_keys)
                if popular_keys
                else 0,
            }

        # When: 캐시 워밍 실행
        warmed_count = warm_cache_with_popular_data()
        warming_status = get_cache_warming_status()

        # Then: 캐시 워밍 성공
        assert warmed_count == 3
        assert warming_status["total_warmed"] == 3
        assert warming_status["warming_rate"] == 1.0

        # 워밍된 데이터 검증
        for key in popular_keys:
            assert key in cache
            assert cache[key]["is_warmed"] is True

        print("✅ 캐시 워밍 전략 테스트 통과")

    def test_cache_preloading_optimization(self):
        """캐시 프리로딩 최적화 테스트"""
        # Given: 사용자 행동 기반 프리로딩 시스템
        user_access_patterns = {
            "user_123": ["place:1", "place:2", "place:3"],
            "user_456": ["place:2", "place:4", "place:5"],
        }
        cache = {}
        preload_queue = []

        def predict_next_access(user_id: str, current_key: str) -> List[str]:
            """사용자 패턴 기반 다음 접근 예측"""
            if user_id not in user_access_patterns:
                return []

            user_pattern = user_access_patterns[user_id]
            try:
                current_index = user_pattern.index(current_key)
                # 다음 2개 항목 예측
                next_items = user_pattern[current_index + 1 : current_index + 3]
                return next_items
            except ValueError:
                return user_pattern[:2]  # 패턴 시작부분 반환

        def preload_cache(user_id: str, predicted_keys: List[str]):
            """예측된 키들을 캐시에 프리로딩"""
            for key in predicted_keys:
                if key not in cache:
                    cache[key] = {
                        "data": f"preloaded_data_for_{key}",
                        "preloaded_for_user": user_id,
                        "preloaded_at": datetime.now().isoformat(),
                        "is_preloaded": True,
                    }
                    preload_queue.append(key)

            return len(predicted_keys)

        # When: 사용자 접근 패턴 기반 프리로딩
        user_id = "user_123"
        current_access = "place:1"

        predicted_keys = predict_next_access(user_id, current_access)
        preloaded_count = preload_cache(user_id, predicted_keys)

        # Then: 예측 기반 프리로딩 성공
        assert predicted_keys == ["place:2", "place:3"]
        assert preloaded_count == 2
        assert len(preload_queue) == 2

        # 프리로딩된 데이터 검증
        for key in predicted_keys:
            assert key in cache
            assert cache[key]["is_preloaded"] is True
            assert cache[key]["preloaded_for_user"] == user_id

        print("✅ 캐시 프리로딩 최적화 테스트 통과")

    def test_cache_compression_optimization(self):
        """캐시 압축 최적화 테스트"""
        # Given: 캐시 압축 시스템
        import base64
        import gzip
        import json

        cache_storage = {}
        compression_stats = {"original_size": 0, "compressed_size": 0}

        def compress_cache_data(data: Any) -> str:
            """캐시 데이터 압축"""
            json_str = json.dumps(data)
            json_bytes = json_str.encode("utf-8")

            compression_stats["original_size"] += len(json_bytes)

            # gzip 압축
            compressed = gzip.compress(json_bytes)
            compression_stats["compressed_size"] += len(compressed)

            # base64 인코딩하여 문자열로 저장
            return base64.b64encode(compressed).decode("utf-8")

        def decompress_cache_data(compressed_data: str) -> Any:
            """캐시 데이터 압축 해제"""
            compressed_bytes = base64.b64decode(compressed_data.encode("utf-8"))
            decompressed_bytes = gzip.decompress(compressed_bytes)
            json_str = decompressed_bytes.decode("utf-8")
            return json.loads(json_str)

        def store_compressed_cache(key: str, data: Any):
            """압축된 형태로 캐시 저장"""
            compressed = compress_cache_data(data)
            cache_storage[key] = {
                "compressed_data": compressed,
                "is_compressed": True,
                "stored_at": datetime.now().isoformat(),
            }

        def get_compressed_cache(key: str) -> Optional[Any]:
            """압축된 캐시에서 데이터 조회"""
            if key not in cache_storage:
                return None

            cache_entry = cache_storage[key]
            if cache_entry["is_compressed"]:
                return decompress_cache_data(cache_entry["compressed_data"])
            return cache_entry["data"]

        # When: 큰 데이터를 압축하여 캐시 저장
        large_data = {
            "places": [
                {"id": i, "name": f"Place {i}", "description": "A" * 100}
                for i in range(50)  # 큰 데이터셋
            ],
            "metadata": {"total": 50, "generated_at": datetime.now().isoformat()},
        }

        store_compressed_cache("large_dataset", large_data)
        retrieved_data = get_compressed_cache("large_dataset")

        # Then: 압축/해제 성공 및 압축률 확인
        assert retrieved_data == large_data
        assert compression_stats["compressed_size"] < compression_stats["original_size"]

        compression_ratio = (
            compression_stats["compressed_size"] / compression_stats["original_size"]
        )
        assert compression_ratio < 0.8  # 최소 20% 압축

        print(f"✅ 캐시 압축 최적화 테스트 통과 (압축률: {compression_ratio:.2%})")


class TestCachePerformanceBenchmark:
    """캐시 성능 벤치마크 테스트"""

    def test_cache_throughput_benchmark(self):
        """캐시 처리량 벤치마크 테스트"""
        # Given: 캐시 처리량 벤치마크 시스템
        cache = {}
        benchmark_results = []

        def benchmark_cache_operations(operation_count: int = 1000):
            """캐시 연산 벤치마크"""
            # SET 연산 벤치마크
            start_time = time.time()
            for i in range(operation_count):
                cache[f"bench_key_{i}"] = f"bench_value_{i}"
            set_duration = time.time() - start_time

            # GET 연산 벤치마크
            start_time = time.time()
            for i in range(operation_count):
                _ = cache.get(f"bench_key_{i}")
            get_duration = time.time() - start_time

            return {
                "operation_count": operation_count,
                "set_duration": set_duration,
                "get_duration": get_duration,
                "set_ops_per_sec": operation_count / set_duration,
                "get_ops_per_sec": operation_count / get_duration,
            }

        # When: 벤치마크 실행
        results = benchmark_cache_operations(1000)
        benchmark_results.append(results)

        # Then: 성능 기준 충족
        assert results["set_ops_per_sec"] > 10000  # 초당 10,000회 이상
        assert results["get_ops_per_sec"] > 50000  # 초당 50,000회 이상
        assert results["set_duration"] < 0.5  # 0.5초 이내
        assert results["get_duration"] < 0.1  # 0.1초 이내

        print(f"✅ 캐시 처리량 벤치마크 통과")
        print(f"   SET: {results['set_ops_per_sec']:.0f} ops/sec")
        print(f"   GET: {results['get_ops_per_sec']:.0f} ops/sec")

    def test_cache_latency_benchmark(self):
        """캐시 지연시간 벤치마크 테스트"""
        # Given: 지연시간 측정 시스템
        cache = {"test_key": "test_value"}

        def measure_cache_latency(iterations: int = 100):
            """캐시 접근 지연시간 측정"""
            latencies = []

            for _ in range(iterations):
                start_time = time.perf_counter()
                _ = cache.get("test_key")
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000  # 밀리초 변환
                latencies.append(latency_ms)

            return {
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "avg_latency": statistics.mean(latencies),
                "p95_latency": sorted(latencies)[int(0.95 * len(latencies))]
                if len(latencies) > 1
                else latencies[0]
                if latencies
                else 0,
                "measurements": len(latencies),
            }

        # When: 지연시간 측정
        latency_stats = measure_cache_latency(100)

        # Then: 지연시간 기준 충족
        assert latency_stats["avg_latency"] < 1.0  # 평균 1ms 미만
        assert latency_stats["p95_latency"] < 2.0  # P95 2ms 미만
        assert latency_stats["max_latency"] < 10.0  # 최대 10ms 미만

        print(f"✅ 캐시 지연시간 벤치마크 통과")
        print(f"   평균: {latency_stats['avg_latency']:.3f}ms")
        print(f"   P95: {latency_stats['p95_latency']:.3f}ms")
        print(f"   최대: {latency_stats['max_latency']:.3f}ms")


def main():
    """캐시 성능 테스트 실행"""
    print("🚀 캐시 성능 및 최적화 TDD 테스트 시작")
    print("=" * 60)

    test_classes = [
        TestCachePerformanceMetrics(),
        TestPerformanceMonitoring(),
        TestCacheOptimization(),
        TestCachePerformanceBenchmark(),
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

    print(f"\n📈 캐시 성능 테스트 결과:")
    print(f"   ✅ 통과: {total_passed}")
    print(f"   ❌ 실패: {total_failed}")
    print(f"   📊 전체: {total_passed + total_failed}")

    if total_failed == 0:
        print("🏆 모든 캐시 성능 테스트 통과!")
        return True
    else:
        print(f"⚠️ {total_failed}개 테스트 실패")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
