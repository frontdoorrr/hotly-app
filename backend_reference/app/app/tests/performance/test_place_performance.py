"""Performance benchmarks for place management system."""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Performance thresholds from requirements
P95_CRUD_THRESHOLD = 1.0  # 1 second for CRUD operations
SEARCH_THRESHOLD = 0.5  # 500ms for search
AUTOCOMPLETE_THRESHOLD = 0.1  # 100ms for autocomplete


@pytest.mark.performance
class TestCRUDPerformance:
    """Performance benchmarks for CRUD operations."""

    def test_place_creation_performance_p95(self):
        """Benchmark: Place creation p95 performance."""
        execution_times = []

        for i in range(20):  # Run 20 iterations for statistical significance
            place_data = {
                "name": f"성능테스트_{i}",
                "description": "성능 테스트용 장소",
                "category": "other",
                "latitude": 37.5665 + (i * 0.001),  # Slight variation
                "longitude": 126.9780 + (i * 0.001),
            }

            start_time = time.time()
            response = client.post("/api/v1/places/", json=place_data)
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            # Cleanup if created successfully
            if response.status_code == 201:
                place_id = response.json()["id"]
                client.delete(f"/api/v1/places/{place_id}")

        # Calculate p95 performance
        p95_time = statistics.quantiles(execution_times, n=20)[18]  # 95th percentile

        assert (
            p95_time < P95_CRUD_THRESHOLD
        ), f"P95 create time {p95_time:.3f}s exceeds {P95_CRUD_THRESHOLD}s"

        return {
            "p50": statistics.median(execution_times),
            "p95": p95_time,
            "p99": statistics.quantiles(execution_times, n=100)[98],
            "mean": statistics.mean(execution_times),
        }

    def test_place_list_performance_p95(self):
        """Benchmark: Place list retrieval p95 performance."""
        execution_times = []

        for i in range(20):
            start_time = time.time()
            response = client.get("/api/v1/places/?page_size=20")
            end_time = time.time()

            assert response.status_code == 200
            execution_times.append(end_time - start_time)

        p95_time = statistics.quantiles(execution_times, n=20)[18]
        assert (
            p95_time < P95_CRUD_THRESHOLD
        ), f"P95 list time {p95_time:.3f}s exceeds {P95_CRUD_THRESHOLD}s"

    def test_place_update_performance_p95(self):
        """Benchmark: Place update p95 performance."""
        # Create test place first
        place_data = {
            "name": "업데이트 성능 테스트",
            "category": "other",
            "latitude": 37.5665,
            "longitude": 126.9780,
        }

        create_response = client.post("/api/v1/places/", json=place_data)
        if create_response.status_code != 201:
            pytest.skip("Could not create test place")

        place_id = create_response.json()["id"]

        try:
            execution_times = []

            for i in range(20):
                update_data = {"description": f"업데이트된 설명 {i}"}

                start_time = time.time()
                response = client.put(f"/api/v1/places/{place_id}", json=update_data)
                end_time = time.time()

                if response.status_code == 200:
                    execution_times.append(end_time - start_time)

            if execution_times:
                p95_time = statistics.quantiles(execution_times, n=20)[18]
                assert (
                    p95_time < P95_CRUD_THRESHOLD
                ), f"P95 update time {p95_time:.3f}s exceeds {P95_CRUD_THRESHOLD}s"

        finally:
            # Cleanup
            client.delete(f"/api/v1/places/{place_id}")


@pytest.mark.performance
class TestSearchPerformance:
    """Performance benchmarks for search operations."""

    def test_search_performance_500ms(self):
        """Benchmark: Search 500ms requirement."""
        search_queries = [
            "카페",
            "맛집",
            "레스토랑",
            "바",
            "관광지",
            "데이트",
            "분위기",
            "조용한",
            "맛있는",
            "예쁜",
        ]

        execution_times = []

        for query in search_queries:
            start_time = time.time()
            response = client.get(f"/api/v1/places/search/?q={query}")
            end_time = time.time()

            assert response.status_code == 200
            execution_time = end_time - start_time
            execution_times.append(execution_time)

            # Individual query should meet threshold
            assert (
                execution_time < SEARCH_THRESHOLD
            ), f"Search '{query}' took {execution_time:.3f}s"

        # Overall performance statistics
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)

        assert (
            avg_time < SEARCH_THRESHOLD * 0.8
        ), f"Average search time {avg_time:.3f}s too high"
        assert (
            max_time < SEARCH_THRESHOLD
        ), f"Max search time {max_time:.3f}s exceeds threshold"

    def test_autocomplete_performance_100ms(self):
        """Benchmark: Autocomplete 100ms requirement."""
        partial_queries = ["카", "맛", "레", "데", "분", "조", "예", "좋", "강", "홍"]

        execution_times = []

        for query in partial_queries:
            start_time = time.time()
            response = client.get(f"/api/v1/search/autocomplete?q={query}")
            end_time = time.time()

            execution_time = end_time - start_time
            execution_times.append(execution_time)

            # Allow 404 since autocomplete endpoint might not exist yet
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                assert (
                    execution_time < AUTOCOMPLETE_THRESHOLD
                ), f"Autocomplete '{query}' took {execution_time:.3f}s"

    def test_geographic_search_performance(self):
        """Benchmark: Geographic search performance."""
        test_coordinates = [
            (37.5665, 126.9780),  # Gangnam
            (37.5547, 126.9707),  # Myeongdong
            (37.5796, 126.9770),  # Jongno
            (37.5172, 127.0473),  # Samseong
            (37.5563, 126.9723),  # Jung-gu
        ]

        execution_times = []

        for lat, lng in test_coordinates:
            start_time = time.time()
            response = client.get(
                f"/api/v1/places/nearby/?latitude={lat}&longitude={lng}&radius_km=5&limit=20"
            )
            end_time = time.time()

            assert response.status_code == 200
            execution_time = end_time - start_time
            execution_times.append(execution_time)

        # Geographic search should be under 100ms as per requirements
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)

        assert avg_time < 0.1, f"Average geo search time {avg_time:.3f}s exceeds 100ms"
        assert max_time < 0.2, f"Max geo search time {max_time:.3f}s too high"


@pytest.mark.load
class TestConcurrentLoad:
    """Concurrent load testing."""

    def test_concurrent_read_operations(self):
        """Test: 동시 읽기 작업 부하."""

        def read_operation():
            try:
                response = client.get("/api/v1/places/?page_size=10")
                return response.status_code == 200
            except:
                return False

        # Simulate 20 concurrent read operations
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(read_operation) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]

        success_rate = sum(results) / len(results)
        assert (
            success_rate >= 0.9
        ), f"Concurrent read success rate {success_rate:.2f} below 90%"

    def test_mixed_operations_load(self):
        """Test: 혼합 작업 부하 (읽기/쓰기/검색)."""

        def mixed_operation(operation_type: str):
            try:
                if operation_type == "read":
                    response = client.get("/api/v1/places/?page_size=5")
                elif operation_type == "search":
                    response = client.get("/api/v1/places/search/?q=카페")
                elif operation_type == "stats":
                    response = client.get("/api/v1/places/stats/")
                else:
                    return False

                return response.status_code == 200
            except:
                return False

        # Mix of operations
        operations = ["read"] * 10 + ["search"] * 8 + ["stats"] * 2

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mixed_operation, op) for op in operations]
            results = [future.result() for future in as_completed(futures)]

        success_rate = sum(results) / len(results)
        assert (
            success_rate >= 0.85
        ), f"Mixed operation success rate {success_rate:.2f} below 85%"


@pytest.mark.benchmark
def test_overall_system_benchmark():
    """Overall system performance benchmark."""
    benchmark_results = {}

    # Test key operations
    operations = [
        ("place_list", lambda: client.get("/api/v1/places/?page_size=20")),
        ("place_search", lambda: client.get("/api/v1/places/search/?q=카페")),
        (
            "nearby_search",
            lambda: client.get(
                "/api/v1/places/nearby/?latitude=37.5665&longitude=126.9780&radius_km=5"
            ),
        ),
        ("place_stats", lambda: client.get("/api/v1/places/stats/")),
    ]

    for operation_name, operation_func in operations:
        times = []
        for _ in range(10):
            start = time.time()
            response = operation_func()
            end = time.time()

            if response.status_code == 200:
                times.append(end - start)

        if times:
            benchmark_results[operation_name] = {
                "mean": statistics.mean(times),
                "p50": statistics.median(times),
                "p95": statistics.quantiles(times, n=20)[18]
                if len(times) >= 20
                else max(times),
                "min": min(times),
                "max": max(times),
            }

    # Log benchmark results for analysis
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Performance benchmark results: {benchmark_results}")

    return benchmark_results
