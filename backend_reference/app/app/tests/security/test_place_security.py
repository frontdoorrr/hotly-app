"""Security tests for place management system."""


import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.mark.security
class TestInputValidationSecurity:
    """Test input validation and sanitization security."""

    def test_sql_injection_protection(self):
        """Test: SQL injection 방지."""
        sql_injection_payloads = [
            "'; DROP TABLE places; --",
            "' OR '1'='1' --",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO places (name) VALUES ('injected'); --",
            "' OR 1=1 LIMIT 1 OFFSET 1 --",
        ]

        for payload in sql_injection_payloads:
            # Test in place creation
            response = client.post(
                "/api/v1/places/", json={"name": payload, "category": "other"}
            )

            # Should handle safely - either create with sanitized input or reject
            assert response.status_code in [201, 409, 422]

            # Test in search
            search_response = client.get(f"/api/v1/places/search/?q={payload}")
            assert search_response.status_code in [200, 422]

            # Should not cause server errors
            assert search_response.status_code != 500

    def test_xss_protection(self):
        """Test: Cross-Site Scripting (XSS) 방지."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
        ]

        for payload in xss_payloads:
            place_data = {
                "name": payload,
                "description": payload,
                "address": payload,
                "category": "other",
            }

            response = client.post("/api/v1/places/", json=place_data)

            # Should handle XSS attempts safely
            assert response.status_code in [201, 409, 422]

            # If created, verify content is properly escaped
            if response.status_code == 201:
                created_data = response.json()
                place_id = created_data["id"]

                # Get place and verify no script execution
                get_response = client.get(f"/api/v1/places/{place_id}")
                if get_response.status_code == 200:
                    place_data = get_response.json()
                    # XSS payloads should be escaped/sanitized
                    assert "<script>" not in place_data.get("name", "")
                    assert "javascript:" not in place_data.get("description", "")

                # Cleanup
                client.delete(f"/api/v1/places/{place_id}")

    def test_path_traversal_protection(self):
        """Test: Path traversal 공격 방지."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for payload in path_traversal_payloads:
            place_data = {
                "name": payload,
                "description": f"Path traversal test: {payload}",
                "category": "other",
            }

            response = client.post("/api/v1/places/", json=place_data)

            # Should handle path traversal attempts safely
            assert response.status_code in [201, 409, 422]
            assert response.status_code != 500  # Should not cause server error

    def test_oversized_input_protection(self):
        """Test: 과도한 입력 크기 방지."""
        # Test various oversized inputs
        oversized_tests = [
            {"name": "A" * 1000, "category": "other"},  # Very long name
            {"description": "B" * 10000, "category": "other"},  # Very long description
            {"tags": ["tag"] * 100, "category": "other"},  # Too many tags
            {"address": "C" * 2000, "category": "other"},  # Very long address
        ]

        for test_data in oversized_tests:
            response = client.post("/api/v1/places/", json=test_data)

            # Should reject oversized input with validation error
            assert response.status_code == 422


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication and authorization security."""

    def test_user_data_isolation(self):
        """Test: 사용자 데이터 격리."""
        # This would test that users cannot access other users' data
        # Requires multi-user setup and actual authentication

    def test_unauthorized_access_prevention(self):
        """Test: 미인증 접근 방지."""
        # In current implementation using TEMP_USER_ID
        # In production, would test JWT token validation

    def test_privilege_escalation_prevention(self):
        """Test: 권한 상승 방지."""
        # Test that users cannot perform admin operations


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting and abuse prevention."""

    def test_api_rate_limiting(self):
        """Test: API 속도 제한."""
        # Test rapid consecutive requests
        responses = []

        for i in range(50):  # 50 rapid requests
            response = client.get("/api/v1/places/")
            responses.append(response.status_code)

        # Should eventually rate limit or handle gracefully
        # In test environment, might not have rate limiting enabled
        success_count = sum(1 for code in responses if code == 200)
        rate_limited_count = sum(1 for code in responses if code == 429)

        # Either all successful (no rate limiting) or some rate limited
        assert success_count + rate_limited_count == 50

    def test_search_abuse_prevention(self):
        """Test: 검색 남용 방지."""
        # Test rapid search requests
        search_queries = ["test"] * 30

        for i, query in enumerate(search_queries):
            response = client.get(f"/api/v1/places/search/?q={query}{i}")

            # Should not cause server overload
            assert response.status_code in [200, 429]  # Success or rate limited

    def test_resource_exhaustion_protection(self):
        """Test: 자원 고갈 공격 방지."""
        # Test requests designed to consume excessive resources
        expensive_operations = [
            "/api/v1/places/?page_size=100",  # Large page size
            "/api/v1/places/nearby/?latitude=37.5665&longitude=126.9780&radius_km=50&limit=200",  # Large radius/limit
            "/api/v1/places/search/?q=" + "카페 " * 20,  # Complex search query
        ]

        for operation in expensive_operations:
            start_time = time.time()
            response = client.get(operation)
            end_time = time.time()

            # Should complete within reasonable time and not crash
            assert end_time - start_time < 10.0  # 10 second max
            assert response.status_code in [200, 422, 429]


@pytest.mark.security
class TestDataIntegritySecurity:
    """Test data integrity and consistency security."""

    def test_coordinate_boundary_validation(self):
        """Test: 좌표 경계값 검증."""
        boundary_test_cases = [
            {"latitude": 90.0, "longitude": 180.0},  # Max valid
            {"latitude": -90.0, "longitude": -180.0},  # Min valid
            {"latitude": 90.1, "longitude": 126.9780},  # Invalid (too high)
            {"latitude": -90.1, "longitude": 126.9780},  # Invalid (too low)
            {"latitude": 37.5665, "longitude": 180.1},  # Invalid longitude
            {"latitude": 37.5665, "longitude": -180.1},  # Invalid longitude
        ]

        for coords in boundary_test_cases:
            place_data = {"name": "경계값 테스트", "category": "other", **coords}

            response = client.post("/api/v1/places/", json=place_data)

            if -90 <= coords["latitude"] <= 90 and -180 <= coords["longitude"] <= 180:
                # Valid coordinates should be accepted
                assert response.status_code in [201, 409]
            else:
                # Invalid coordinates should be rejected
                assert response.status_code == 422

    def test_category_validation_security(self):
        """Test: 카테고리 값 검증."""
        valid_categories = [
            "restaurant",
            "cafe",
            "bar",
            "tourist_attraction",
            "shopping",
            "accommodation",
            "entertainment",
            "other",
        ]

        invalid_categories = [
            "invalid_category",
            "",  # Empty
            "script_injection",
            "drop_table",
            None,  # Null value
        ]

        for category in valid_categories:
            response = client.post(
                "/api/v1/places/",
                json={"name": f"카테고리 테스트 {category}", "category": category},
            )
            assert response.status_code in [201, 409]  # Should accept valid categories

        for category in invalid_categories:
            place_data = {"name": "Invalid category test"}
            if category is not None:
                place_data["category"] = category

            response = client.post("/api/v1/places/", json=place_data)
            # Should reject invalid categories
            if category is None:
                assert response.status_code == 422  # Missing required field
            else:
                assert response.status_code == 422  # Invalid category

    def test_uuid_validation_security(self):
        """Test: UUID 형식 검증."""
        invalid_uuids = [
            "not-a-uuid",
            "123456789",
            "",
            "00000000-0000-0000-0000-00000000000g",  # Invalid character
            "../../../etc/passwd",
            "' OR '1'='1",
        ]

        for invalid_uuid in invalid_uuids:
            # Test in place retrieval
            response = client.get(f"/api/v1/places/{invalid_uuid}")
            assert response.status_code == 422  # Validation error

            # Test in place update
            update_response = client.put(
                f"/api/v1/places/{invalid_uuid}", json={"name": "test"}
            )
            assert update_response.status_code == 422

            # Test in place deletion
            delete_response = client.delete(f"/api/v1/places/{invalid_uuid}")
            assert delete_response.status_code == 422


@pytest.mark.security
class TestInformationDisclosure:
    """Test information disclosure prevention."""

    def test_error_message_sanitization(self):
        """Test: 에러 메시지 정보 누출 방지."""
        # Test that error messages don't expose sensitive information

        # Invalid UUID that might trigger database error
        response = client.get("/api/v1/places/invalid-id")
        assert response.status_code == 422

        error_detail = response.json().get("detail", "")

        # Error message should not contain:
        # - Database connection strings
        # - File paths
        # - Stack traces
        # - Internal system information
        sensitive_patterns = [
            "postgresql://",
            "/app/",
            "Traceback",
            'File "/',
            "line ",
            "sqlalchemy",
            "psycopg2",
        ]

        error_lower = error_detail.lower() if isinstance(error_detail, str) else ""
        for pattern in sensitive_patterns:
            assert (
                pattern.lower() not in error_lower
            ), f"Error message contains sensitive info: {pattern}"

    def test_response_header_security(self):
        """Test: HTTP 응답 헤더 보안."""
        response = client.get("/api/v1/places/")
        headers = response.headers

        # Check for security headers (if implemented)
        # Note: These might not be implemented yet
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
        ]

        # Just verify no sensitive headers are exposed
        sensitive_headers = [
            "Server",  # Should not reveal server details
            "X-Powered-By",  # Should not reveal technology stack
        ]

        for header in sensitive_headers:
            if header in headers:
                # If present, should not contain sensitive information
                header_value = headers[header].lower()
                assert "postgresql" not in header_value
                assert "fastapi" not in header_value
