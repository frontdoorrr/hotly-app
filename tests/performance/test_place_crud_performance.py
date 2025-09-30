#!/usr/bin/env python3
"""
Place CRUD API Performance Tests

Tests for validating p95 1-second response time requirement for Place CRUD operations.
Follows TDD approach for Task 1-2-5: 장소 CRUD API 구현 (p95 1초)
"""

import time
from typing import List
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.places import router as places_router
from app.schemas.place import PlaceCreate


class TestPlaceCRUDPerformance:
    """
    Performance tests for Place CRUD API operations.

    Validates that all CRUD operations meet p95 1-second requirement
    under realistic load conditions.
    """

    def setup_method(self) -> None:
        """Setup test client and performance thresholds."""
        # Create test FastAPI app
        app = FastAPI()
        app.include_router(places_router, prefix="/api/v1")

        self.client = TestClient(app)

        # Performance requirements
        self.p95_threshold_ms = 1000  # 1 second for p95
        self.p50_threshold_ms = 500  # 500ms for median (good performance)

        # Test data
        self.test_user_id = str(uuid4())
        self.sample_places = self._create_sample_places()

    def _create_sample_places(self) -> List[PlaceCreate]:
        """Create sample place data for performance testing."""
        return [
            PlaceCreate(
                name="스타벅스 홍대입구역점",
                address="서울특별시 마포구 홍익로 69",
                latitude=37.5572,
                longitude=126.9238,
                category="cafe",
                tags=["커피", "카페", "스터디"],
            ),
            PlaceCreate(
                name="교촌치킨 강남점",
                address="서울특별시 강남구 강남대로 390",
                latitude=37.4979,
                longitude=127.0276,
                category="restaurant",
                tags=["치킨", "배달", "테이크아웃"],
            ),
            PlaceCreate(
                name="롯데백화점 본점",
                address="서울특별시 중구 소공로 81",
                latitude=37.5651,
                longitude=126.9820,
                category="shopping",
                tags=["쇼핑", "백화점", "브랜드"],
            ),
        ]

    def measure_api_response_time(self, method: str, endpoint: str, **kwargs) -> tuple[float, object]:
        """Measure API response time for HTTP operations."""
        start_time = time.perf_counter()

        if method.upper() == "GET":
            response = self.client.get(endpoint, **kwargs)
        elif method.upper() == "POST":
            response = self.client.post(endpoint, **kwargs)
        elif method.upper() == "PUT":
            response = self.client.put(endpoint, **kwargs)
        elif method.upper() == "PATCH":
            response = self.client.patch(endpoint, **kwargs)
        elif method.upper() == "DELETE":
            response = self.client.delete(endpoint, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        return response_time_ms, response

    def test_create_place_performance_singleRequest_underP95Threshold(self) -> None:
        """
        Test: Single place creation completes under p95 threshold

        RED: This test validates create operation performance
        """
        # Given: New place data
        new_place = self.sample_places[0]

        # When: Create place via API
        response_time_ms, response = self.measure_api_response_time(
            "POST", "/api/v1/places/", json=new_place.dict()
        )

        # Then: Should complete under p95 threshold
        assert (
            response_time_ms < self.p95_threshold_ms
        ), f"Place creation took {response_time_ms:.1f}ms, expected < {self.p95_threshold_ms}ms"

        # Should also be successful
        assert response.status_code in [
            200,
            201,
        ], f"Create failed with status {response.status_code}: {response.text}"

        print(f"✅ Create place: {response_time_ms:.1f}ms")

    def test_bulk_place_operations_multipleRequests_meetP95Performance(self) -> None:
        """
        Test: Bulk CRUD operations meet p95 performance requirements

        Tests realistic load with multiple operations
        """
        # Given: Multiple operations to perform
        num_operations = 20
        operation_times = []

        # When: Perform bulk create operations
        for i in range(num_operations):
            place_data = self.sample_places[i % len(self.sample_places)]
            place_data_dict = place_data.dict()
            place_data_dict["name"] = f"{place_data.name} #{i + 1}"  # Make unique

            response_time_ms, response = self.measure_api_response_time(
                "POST", "/api/v1/places/", json=place_data_dict
            )

            operation_times.append(response_time_ms)

            # Each individual operation should meet threshold
            assert (
                response_time_ms < self.p95_threshold_ms
            ), f"Operation {i + 1} took {response_time_ms:.1f}ms"

        # Then: Calculate performance percentiles
        operation_times.sort()
        p50_time = operation_times[len(operation_times) // 2]
        p95_index = int(len(operation_times) * 0.95)
        p95_time = operation_times[p95_index]
        avg_time = sum(operation_times) / len(operation_times)

        print("\n📊 Bulk Operations Performance:")
        print(f"   Operations: {num_operations}")
        print(f"   Average: {avg_time:.1f}ms")
        print(f"   P50 (median): {p50_time:.1f}ms")
        print(f"   P95: {p95_time:.1f}ms")
        print(f"   Target P95: {self.p95_threshold_ms}ms")

        # Validate performance requirements
        assert (
            p95_time < self.p95_threshold_ms
        ), f"P95 response time {p95_time:.1f}ms exceeds {self.p95_threshold_ms}ms threshold"

        assert (
            p50_time < self.p50_threshold_ms
        ), f"P50 response time {p50_time:.1f}ms exceeds {self.p50_threshold_ms}ms target"

    def test_read_operations_performance_variousQueries_efficientRetrieval(self) -> None:
        """
        Test: Read operations (GET) perform efficiently under load

        Tests list, search, and detail retrieval performance
        """
        # Given: Different read operation types
        read_operations = [
            ("GET", "/api/v1/places/", {}, "List all places"),
            ("GET", "/api/v1/places/", {"params": {"limit": 10}}, "Paginated list"),
            (
                "GET",
                "/api/v1/places/search",
                {"params": {"q": "카페"}},
                "Search places",
            ),
            (
                "GET",
                "/api/v1/places/nearby",
                {"params": {"lat": 37.5665, "lng": 126.9780, "radius": 1000}},
                "Nearby search",
            ),
        ]

        performance_results = []

        # When: Execute each read operation multiple times
        for method, endpoint, kwargs, description in read_operations:
            times = []

            for _ in range(5):  # 5 iterations per operation
                response_time_ms, response = self.measure_api_response_time(
                    method, endpoint, **kwargs
                )
                times.append(response_time_ms)

            avg_time = sum(times) / len(times)
            max_time = max(times)

            performance_results.append(
                {
                    "operation": description,
                    "avg_time": avg_time,
                    "max_time": max_time,
                    "under_threshold": max_time < self.p95_threshold_ms,
                }
            )

            # Then: All operations should meet performance requirements
            assert (
                max_time < self.p95_threshold_ms
            ), f"{description} max time {max_time:.1f}ms exceeds threshold"

        print("\n📖 Read Operations Performance:")
        for result in performance_results:
            status = "✅" if result["under_threshold"] else "❌"
            print(
                f"   {status} {result['operation']}: avg {result['avg_time']:.1f}ms, max {result['max_time']:.1f}ms"
            )

    def test_update_operations_performance_patchAndPut_efficientModification(self) -> None:
        """
        Test: Update operations perform efficiently

        Tests both PATCH (partial) and PUT (full) updates
        """
        # Given: Place to update (mock existing place)
        place_id = str(uuid4())

        update_operations = [
            ("PATCH", {"name": "Updated Place Name"}, "Partial update"),
            ("PUT", self.sample_places[0].dict(), "Full update"),
            ("PATCH", {"tags": ["new", "tags", "list"]}, "Tag update"),
        ]

        # When: Perform various update operations
        for method, update_data, description in update_operations:
            response_time_ms, response = self.measure_api_response_time(
                method, f"/api/v1/places/{place_id}", json=update_data
            )

            # Then: Should complete efficiently
            # Note: This may fail due to missing place, but we're testing performance
            print(f"   {description}: {response_time_ms:.1f}ms")

            # Performance should still be reasonable even for failed requests
            assert (
                response_time_ms < self.p95_threshold_ms
            ), f"{description} took {response_time_ms:.1f}ms, too slow even for error response"

    def test_delete_operation_performance_singleAndBulk_efficientRemoval(self) -> None:
        """
        Test: Delete operations complete efficiently

        Tests single delete performance
        """
        # Given: Place ID to delete
        place_id = str(uuid4())

        # When: Perform delete operation
        response_time_ms, response = self.measure_api_response_time(
            "DELETE", f"/api/v1/places/{place_id}"
        )

        # Then: Should complete quickly
        assert (
            response_time_ms < self.p95_threshold_ms
        ), f"Delete operation took {response_time_ms:.1f}ms, exceeds threshold"

        print(f"✅ Delete place: {response_time_ms:.1f}ms")

    def test_concurrent_api_requests_multipleUsers_maintainPerformance(self) -> None:
        """
        Test: Concurrent API requests maintain performance standards

        Simulates multiple users making simultaneous requests
        """
        import concurrent.futures
        import threading

        # Given: Concurrent request parameters
        num_concurrent_users = 5

        def simulate_user_session() -> list[float]:
            """Simulate a user making multiple API requests."""
            user_times = []

            # Create a place
            place_data = self.sample_places[0].dict()
            place_data["name"] = f"Concurrent Test {threading.current_thread().ident}"

            response_time_ms, response = self.measure_api_response_time(
                "POST", "/api/v1/places/", json=place_data
            )
            user_times.append(response_time_ms)

            # List places
            response_time_ms, response = self.measure_api_response_time(
                "GET", "/api/v1/places/"
            )
            user_times.append(response_time_ms)

            # Search places
            response_time_ms, response = self.measure_api_response_time(
                "GET", "/api/v1/places/search", params={"q": "카페"}
            )
            user_times.append(response_time_ms)

            # Get nearby places
            response_time_ms, response = self.measure_api_response_time(
                "GET",
                "/api/v1/places/nearby",
                params={"lat": 37.5665, "lng": 126.9780, "radius": 1000},
            )
            user_times.append(response_time_ms)

            return user_times

        # When: Execute concurrent user sessions
        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_concurrent_users
        ) as executor:
            futures = [
                executor.submit(simulate_user_session)
                for _ in range(num_concurrent_users)
            ]

            all_user_times = []
            for future in concurrent.futures.as_completed(futures):
                user_times = future.result()
                all_user_times.extend(user_times)

        total_time = time.perf_counter() - start_time

        # Then: Calculate concurrent performance metrics
        all_user_times.sort()
        p95_index = int(len(all_user_times) * 0.95)
        concurrent_p95 = all_user_times[p95_index]
        avg_time = sum(all_user_times) / len(all_user_times)

        print("\n🔄 Concurrent API Performance:")
        print(f"   Concurrent users: {num_concurrent_users}")
        print(f"   Total requests: {len(all_user_times)}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average response: {avg_time:.1f}ms")
        print(f"   P95 response: {concurrent_p95:.1f}ms")

        # Concurrent P95 should still meet requirements
        assert (
            concurrent_p95 < self.p95_threshold_ms
        ), f"Concurrent P95 {concurrent_p95:.1f}ms exceeds {self.p95_threshold_ms}ms threshold"

    def test_complex_query_performance_advancedFiltering_efficientExecution(self) -> None:
        """
        Test: Complex queries with multiple filters perform efficiently

        Tests advanced search and filtering performance
        """
        # Given: Complex query parameters
        complex_queries = [
            {
                "params": {
                    "category": "restaurant",
                    "tags": "한식,맛집",
                    "lat": 37.5665,
                    "lng": 126.9780,
                    "radius": 2000,
                    "limit": 20,
                },
                "description": "Category + tags + geo + pagination",
            },
            {
                "params": {
                    "q": "스타벅스",
                    "category": "cafe",
                    "min_rating": 4.0,
                    "sort": "distance",
                },
                "description": "Text search + category + rating + sorting",
            },
            {
                "params": {
                    "bbox": "126.9,37.5,127.0,37.6",  # Bounding box search
                    "tags": "카페,디저트",
                    "created_after": "2024-01-01",
                },
                "description": "Bounding box + tags + date filter",
            },
        ]

        # When: Execute complex queries
        for query_config in complex_queries:
            response_time_ms, response = self.measure_api_response_time(
                "GET", "/api/v1/places/search", params=query_config["params"]
            )

            # Then: Should complete within performance threshold
            assert (
                response_time_ms < self.p95_threshold_ms
            ), f"Complex query '{query_config['description']}' took {response_time_ms:.1f}ms"

            print(f"   ✅ {query_config['description']}: {response_time_ms:.1f}ms")

    @pytest.mark.slow
    def test_stress_testing_highLoad_maintainStability(self) -> None:
        """
        Test: API maintains performance under high load

        Stress test with sustained high request volume
        """
        # Given: High load parameters
        num_requests = 100
        request_times = []

        # When: Generate sustained load
        for i in range(num_requests):
            # Alternate between different operations
            if i % 4 == 0:
                # Create operation
                place_data = self.sample_places[i % len(self.sample_places)].dict()
                place_data["name"] = f"Stress Test Place {i}"
                response_time_ms, response = self.measure_api_response_time(
                    "POST", "/api/v1/places/", json=place_data
                )
            elif i % 4 == 1:
                # List operation
                response_time_ms, response = self.measure_api_response_time(
                    "GET", "/api/v1/places/", params={"limit": 10}
                )
            elif i % 4 == 2:
                # Search operation
                response_time_ms, response = self.measure_api_response_time(
                    "GET", "/api/v1/places/search", params={"q": "카페"}
                )
            else:
                # Nearby operation
                response_time_ms, response = self.measure_api_response_time(
                    "GET",
                    "/api/v1/places/nearby",
                    params={"lat": 37.5665, "lng": 126.9780, "radius": 1000},
                )

            request_times.append(response_time_ms)

        # Then: Analyze performance under load
        request_times.sort()
        p95_index = int(len(request_times) * 0.95)
        stress_p95 = request_times[p95_index]
        avg_time = sum(request_times) / len(request_times)

        print("\n🔥 Stress Test Results:")
        print(f"   Total requests: {num_requests}")
        print(f"   Average response: {avg_time:.1f}ms")
        print(f"   P95 response: {stress_p95:.1f}ms")
        print(f"   Max response: {max(request_times):.1f}ms")

        # Performance should remain stable under load
        assert (
            stress_p95 < self.p95_threshold_ms * 1.5
        ), f"Stress test P95 {stress_p95:.1f}ms too high (allowed: {self.p95_threshold_ms * 1.5}ms)"
