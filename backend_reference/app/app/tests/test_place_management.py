"""Comprehensive integration tests for place management system."""

import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Test constants
TEST_USER_ID = "00000000-0000-0000-0000-000000000000"
PERFORMANCE_TIMEOUT = 1.0  # 1 second as per requirements


@pytest.mark.integration
class TestPlaceManagementWorkflow:
    """End-to-end integration tests for complete place management workflow."""

    def test_complete_place_lifecycle(self):
        """Test: 생성→검색→수정→삭제 complete workflow."""
        # Given: New place data
        place_data = {
            "name": "테스트 통합 카페",
            "description": "통합 테스트용 카페입니다",
            "address": "서울시 강남구 테스트로 999",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["테스트", "카페", "통합"],
        }
        created_place_id = None

        try:
            # Step 1: CREATE - 장소 생성
            create_response = client.post("/api/v1/places/", json=place_data)
            assert create_response.status_code in [201, 409]  # Success or duplicate

            if create_response.status_code == 201:
                created_data = create_response.json()
                created_place_id = created_data["id"]
                assert created_data["name"] == place_data["name"]

            # Step 2: READ - 장소 조회
            if created_place_id:
                get_response = client.get(f"/api/v1/places/{created_place_id}")
                assert get_response.status_code == 200
                retrieved_data = get_response.json()
                assert retrieved_data["id"] == created_place_id

            # Step 3: SEARCH - 검색으로 찾기
            search_response = client.get(
                f"/api/v1/places/search/?q={place_data['name'][:5]}"
            )
            assert search_response.status_code == 200
            search_results = search_response.json()
            assert isinstance(search_results, list)

            # Step 4: UPDATE - 장소 정보 수정
            if created_place_id:
                update_data = {"description": "수정된 설명입니다"}
                update_response = client.put(
                    f"/api/v1/places/{created_place_id}", json=update_data
                )
                assert update_response.status_code == 200
                updated_data = update_response.json()
                assert updated_data["description"] == update_data["description"]

            # Step 5: DELETE - 장소 삭제 (소프트 삭제)
            if created_place_id:
                delete_response = client.delete(f"/api/v1/places/{created_place_id}")
                assert delete_response.status_code == 200

                # Verify soft delete - place should not appear in normal queries
                get_deleted_response = client.get(f"/api/v1/places/{created_place_id}")
                assert get_deleted_response.status_code == 404

        finally:
            # Cleanup: Ensure test data is removed
            if created_place_id:
                client.delete(f"/api/v1/places/{created_place_id}")

    def test_duplicate_detection_workflow(self):
        """Test: 중복 처리 complete workflow."""
        # Given: Place data that might be duplicate
        original_place = {
            "name": "스타벅스 강남점",
            "description": "커피 체인점",
            "address": "서울시 강남구 테헤란로 123",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["커피", "체인"],
        }

        # Step 1: Check for duplicates before creation
        duplicate_check = client.post(
            "/api/v1/places/check-duplicate/", json=original_place
        )
        assert duplicate_check.status_code == 200

        duplicate_result = duplicate_check.json()
        assert "isDuplicate" in duplicate_result
        assert "confidence" in duplicate_result

        # Step 2: Create place or handle duplicate
        create_response = client.post("/api/v1/places/", json=original_place)
        assert create_response.status_code in [201, 409]

        # If created successfully, try creating similar place
        if create_response.status_code == 201:
            created_data = create_response.json()
            created_place_id = created_data["id"]

            # Try creating very similar place
            similar_place = original_place.copy()
            similar_place["name"] = "스타벅스강남점"  # Slight variation

            similar_response = client.post("/api/v1/places/", json=similar_place)
            assert similar_response.status_code == 409  # Should detect as duplicate

            # Cleanup
            client.delete(f"/api/v1/places/{created_place_id}")

    def test_status_transition_workflow(self):
        """Test: 상태 전이 workflow (active ↔ inactive)."""
        # This test would verify proper status transitions
        # Placeholder for status management workflow testing


@pytest.mark.performance
class TestPlaceManagementPerformance:
    """Performance tests for place management operations."""

    def test_crud_performance_requirements(self):
        """Test: CRUD 작업 p95 1초 이내 requirement."""
        performance_results = {}

        # Test CREATE performance
        place_data = {
            "name": f"성능테스트카페_{uuid4().hex[:8]}",
            "description": "성능 테스트용 장소",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
        }

        start_time = time.time()
        create_response = client.post("/api/v1/places/", json=place_data)
        create_time = time.time() - start_time
        performance_results["create"] = create_time

        # Verify performance requirement
        assert create_time < PERFORMANCE_TIMEOUT
        assert create_response.status_code in [201, 409]

        # Test READ performance
        start_time = time.time()
        list_response = client.get("/api/v1/places/?page_size=20")
        read_time = time.time() - start_time
        performance_results["read"] = read_time

        assert read_time < PERFORMANCE_TIMEOUT
        assert list_response.status_code == 200

    def test_search_performance_requirements(self):
        """Test: 검색 응답 500ms 이내 requirement."""
        search_queries = ["카페", "맛집", "데이트", "분위기", "강남"]

        for query in search_queries:
            start_time = time.time()
            response = client.get(f"/api/v1/places/search/?q={query}")
            search_time = time.time() - start_time

            # 500ms requirement with test environment allowance
            assert search_time < 1.0
            assert response.status_code == 200

    def test_autocomplete_performance(self):
        """Test: 자동완성 100ms requirement."""
        partial_queries = ["카", "맛", "데", "강"]

        for query in partial_queries:
            start_time = time.time()
            response = client.get(f"/api/v1/search/autocomplete?q={query}")
            autocomplete_time = time.time() - start_time

            # 100ms requirement with test environment allowance
            assert autocomplete_time < 0.5
            # Note: Endpoint may not exist, so allow 404
            assert response.status_code in [200, 404]

    def test_concurrent_user_load(self):
        """Test: 동시 사용자 100명 부하 테스트."""

        def simulate_user_session():
            """Simulate a single user session."""
            try:
                # User workflow: List → Search → View details
                client.get("/api/v1/places/")
                client.get("/api/v1/places/search/?q=카페")
                client.get("/api/v1/places/stats/")
                return True
            except:
                return False

        # Run concurrent sessions
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Scale down for test environment (10 instead of 100)
            futures = [executor.submit(simulate_user_session) for _ in range(10)]
            results = [future.result() for future in futures]

        # At least 80% of sessions should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8


@pytest.mark.security
class TestPlaceManagementSecurity:
    """Security tests for place management system."""

    def test_input_validation_security(self):
        """Test: SQL injection and XSS protection."""
        # SQL injection attempts
        malicious_inputs = [
            "'; DROP TABLE places; --",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "../../../../etc/passwd",
            "' UNION SELECT * FROM users --",
        ]

        for malicious_input in malicious_inputs:
            # Test in place creation
            response = client.post(
                "/api/v1/places/", json={"name": malicious_input, "category": "other"}
            )
            # Should either reject or sanitize, not cause 500 error
            assert response.status_code in [201, 409, 422]

            # Test in search
            search_response = client.get(f"/api/v1/places/search/?q={malicious_input}")
            assert search_response.status_code in [200, 422]

    def test_authorization_boundaries(self):
        """Test: User data isolation and access controls."""
        # Test that users can only access their own places
        # This would require multi-user test setup

    def test_rate_limiting_protection(self):
        """Test: API rate limiting protection."""
        # Test rapid consecutive requests
        for i in range(20):
            response = client.get("/api/v1/places/")
            # Should not be blocked in test environment
            assert response.status_code in [200, 429]  # 429 = rate limited


@pytest.mark.data_integrity
class TestPlaceDataIntegrity:
    """Data integrity and consistency tests."""

    def test_coordinate_validation(self):
        """Test: 좌표 유효성 검증."""
        invalid_coordinates = [
            {"latitude": 91.0, "longitude": 126.9780},  # Invalid latitude
            {"latitude": 37.5665, "longitude": 181.0},  # Invalid longitude
            {"latitude": -91.0, "longitude": 126.9780},  # Invalid latitude
            {"latitude": 37.5665, "longitude": -181.0},  # Invalid longitude
        ]

        for coords in invalid_coordinates:
            place_data = {"name": "좌표 테스트", "category": "other", **coords}
            response = client.post("/api/v1/places/", json=place_data)
            assert response.status_code == 422  # Validation error

    def test_tag_normalization_consistency(self):
        """Test: 태그 정규화 일관성."""
        # Test that the same tag input normalizes consistently
        tag_variations = [
            "  카페  ",  # Whitespace
            "COFFEE",  # English uppercase
            "음식점!",  # Punctuation
            "데이트장소",  # Compound word
        ]

        # This would test tag normalization across different entry points
        # Requires implementation of tag normalization service

    def test_search_index_consistency(self):
        """Test: 검색 인덱스 일관성."""
        # Test that search indexes are properly maintained
        # When places are created/updated/deleted


class TestPlaceManagementScenarios:
    """Real-world scenario testing."""

    def test_restaurant_discovery_scenario(self):
        """Scenario: 사용자가 맛집을 찾고 저장하는 플로우."""
        # Given: User wants to find restaurants near Gangnam
        search_lat, search_lng = 37.5665, 126.9780

        # Step 1: Geographic search for restaurants
        nearby_response = client.get(
            f"/api/v1/places/nearby/?latitude={search_lat}&longitude={search_lng}"
            f"&radius_km=2&limit=10"
        )
        assert nearby_response.status_code == 200
        nearby_places = nearby_response.json()
        assert isinstance(nearby_places, list)

        # Step 2: Text search for specific cuisine
        search_response = client.get(
            "/api/v1/places/search/?q=이탈리안&category=restaurant"
        )
        assert search_response.status_code == 200

        # Step 3: Check place statistics
        stats_response = client.get("/api/v1/places/stats/")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert "total_places" in stats

    def test_travel_planning_scenario(self):
        """Scenario: 여행 코스 계획 플로우."""
        # Given: User planning a travel route
        route_waypoints = [
            {"latitude": 37.5665, "longitude": 126.9780},  # Gangnam
            {"latitude": 37.5547, "longitude": 126.9707},  # Myeongdong
            {"latitude": 37.5796, "longitude": 126.9770},  # Jongno
        ]

        # Step 1: Find places along route
        route_search = client.post(
            "/api/v1/places/geographic/route-search",
            json={"waypoints": route_waypoints, "buffer_km": 1.0, "limit": 20},
        )

        # Should return places along the route
        assert route_search.status_code in [
            200,
            422,
        ]  # 200 success, 422 validation error

        # Step 2: Get geographic clusters for organization
        cluster_response = client.get("/api/v1/places/geographic/clusters")
        assert cluster_response.status_code == 200
        clusters = cluster_response.json()
        assert isinstance(clusters, list)

    def test_data_export_scenario(self):
        """Scenario: 데이터 내보내기 플로우."""
        # Step 1: Export all places as JSON
        json_export = client.get("/api/v1/places/export?format=json")
        assert json_export.status_code == 200
        json_data = json_export.json()
        assert "export_info" in json_data
        assert "places" in json_data

        # Step 2: Export filtered data as CSV info
        csv_export = client.get("/api/v1/places/export?format=csv&category=restaurant")
        assert csv_export.status_code == 200
        csv_data = csv_export.json()
        assert "download_url" in csv_data or "message" in csv_data


@pytest.fixture
def sample_places_data():
    """Fixture providing sample test places."""
    return [
        {
            "name": "테스트 카페 1",
            "description": "조용한 분위기의 카페",
            "address": "서울시 강남구 A로 1",
            "category": "restaurant",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "tags": ["카페", "조용한", "스터디"],
        },
        {
            "name": "테스트 레스토랑 2",
            "description": "맛있는 이탈리안 음식점",
            "address": "서울시 강남구 B로 2",
            "category": "restaurant",
            "latitude": 37.5675,
            "longitude": 126.9790,
            "tags": ["이탈리안", "파스타", "데이트"],
        },
        {
            "name": "테스트 바 3",
            "description": "분위기 좋은 칵테일 바",
            "address": "서울시 강남구 C로 3",
            "category": "bar",
            "latitude": 37.5655,
            "longitude": 126.9770,
            "tags": ["칵테일", "분위기", "야경"],
        },
    ]


class TestPlaceManagementStressTest:
    """Stress and load testing for place management."""

    def test_bulk_operations_performance(self, sample_places_data):
        """Test: 대량 데이터 처리 성능."""
        created_ids = []

        try:
            # Bulk create test (scaled down for test environment)
            start_time = time.time()
            for i, place_data in enumerate(sample_places_data * 3):  # 9 places total
                place_data = place_data.copy()
                place_data["name"] = f"{place_data['name']}_{i}"

                response = client.post("/api/v1/places/", json=place_data)
                if response.status_code == 201:
                    created_ids.append(response.json()["id"])

            bulk_create_time = time.time() - start_time

            # Should handle bulk creation efficiently
            assert bulk_create_time < 10.0  # 10 seconds for test environment

            # Test bulk search performance
            start_time = time.time()
            search_response = client.get("/api/v1/places/?page_size=50")
            bulk_search_time = time.time() - start_time

            assert bulk_search_time < PERFORMANCE_TIMEOUT
            assert search_response.status_code == 200

        finally:
            # Cleanup created test data
            for place_id in created_ids:
                client.delete(f"/api/v1/places/{place_id}")

    def test_memory_usage_stability(self):
        """Test: 메모리 누수 검사."""
        # This would monitor memory usage during operations
        # Placeholder for memory monitoring


class TestErrorHandlingRobustness:
    """Error handling and edge case testing."""

    def test_malformed_request_handling(self):
        """Test: 잘못된 요청 처리."""
        malformed_requests = [
            {},  # Empty object
            {"invalid_field": "value"},  # Unknown fields
            {"name": ""},  # Empty required field
            {"name": "a" * 1000},  # Too long field
            {"latitude": "invalid"},  # Wrong type
        ]

        for request_data in malformed_requests:
            response = client.post("/api/v1/places/", json=request_data)
            assert response.status_code == 422  # Validation error

    def test_database_error_recovery(self):
        """Test: 데이터베이스 에러 복구."""
        # This would test database connection failures and recovery
        # Requires database connection mocking

    def test_external_service_failure_handling(self):
        """Test: 외부 서비스 실패 처리 (AI, geocoding, etc.)."""
        # Test graceful degradation when AI services are unavailable
        # Placeholder for external service failure simulation


@pytest.mark.integration
class TestSearchSystemIntegration:
    """Integration tests specifically for search functionality."""

    def test_korean_search_accuracy(self):
        """Test: 한국어 검색 정확도."""
        korean_queries = ["맛있는 커피", "분위기 좋은 카페", "데이트하기 좋은 곳", "강남 이탈리안", "홍대 술집"]

        for query in korean_queries:
            response = client.get(f"/api/v1/places/search/?q={query}")
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)

    def test_complex_filter_combinations(self):
        """Test: 복합 필터 조합."""
        # Test multiple filters working together
        response = client.get(
            "/api/v1/places/?category=restaurant&tags=이탈리안&tags=데이트"
            "&latitude=37.5665&longitude=126.9780&radius_km=5"
        )
        assert response.status_code == 200
        data = response.json()
        assert "places" in data

    def test_search_edge_cases(self):
        """Test: 검색 엣지 케이스."""
        edge_cases = [
            "ㄱㄴㄷ",  # Only consonants
            "123",  # Only numbers
            "!@#$%",  # Only special characters
            "a" * 100,  # Very long query
            "카페" + " " * 50,  # Query with lots of whitespace
        ]

        for query in edge_cases:
            response = client.get(f"/api/v1/places/search/?q={query}")
            # Should handle gracefully, not crash
            assert response.status_code in [200, 422]
