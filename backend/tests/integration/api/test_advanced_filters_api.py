"""
고급 필터링 API 엔드포인트 테스트 (Task 2-3-3)

TDD 접근법으로 API 엔드포인트의 전체 플로우 테스트
- 요청/응답 검증
- 에러 처리
- 인증 및 권한 확인
- 성능 테스트
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User


class TestAdvancedFiltersAPI:
    """고급 필터링 API 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.client = TestClient(app)
        self.test_user_id = uuid4()
        self.test_user = User(
            id=self.test_user_id,
            email="test@example.com",
            username="testuser",
            is_active=True,
        )

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_advanced_filter_search_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 고급 필터 요청
        When: POST /api/v1/filters/search 호출
        Then: 필터링된 결과를 올바르게 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 서비스 응답
        mock_filter_result = {
            "places": [
                {
                    "id": str(uuid4()),
                    "name": "홍대 감성 카페",
                    "description": "조용하고 분위기 좋은 카페",
                    "address": "서울시 마포구 홍익로 123",
                    "location": {"lat": 37.5563, "lng": 126.9225},
                    "category": "cafe",
                    "tags": ["조용한", "분위기좋은"],
                    "rating": 4.5,
                    "review_count": 127,
                    "price_range": 15000,
                    "visit_status": "wishlist",
                    "created_at": "2024-01-15T10:30:45.123Z",
                    "relevance_score": 2.5,
                }
            ],
            "total": 1,
            "pagination": {
                "total": 1,
                "limit": 20,
                "offset": 0,
                "has_next": False,
                "has_previous": False,
            },
            "facets": {
                "categories": [{"name": "cafe", "count": 1, "selected": True}],
                "regions": [{"name": "마포구", "count": 1, "selected": True}],
            },
            "applied_filters": {
                "categories": ["cafe"],
                "regions": ["마포구"],
            },
            "query_info": {
                "total_hits": 1,
                "source": "elasticsearch",
            },
            "performance": {
                "total_time_ms": 125,
                "cache_hit": False,
            },
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_filter_result
        )

        # 요청 데이터
        request_data = {
            "query": "홍대 카페",
            "categories": ["cafe"],
            "regions": ["마포구"],
            "tags": ["조용한"],
            "rating_min": 4.0,
            "sort_by": "rating",
            "limit": 20,
            "include_facets": True,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json=request_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "places" in response_data
        assert "pagination" in response_data
        assert "facets" in response_data
        assert "applied_filters" in response_data
        assert "query_info" in response_data

        # 장소 정보 검증
        places = response_data["places"]
        assert len(places) == 1
        place = places[0]
        assert place["name"] == "홍대 감성 카페"
        assert place["category"] == "cafe"
        assert place["rating"] == 4.5

        # 패싯 정보 검증
        facets = response_data["facets"]
        assert "categories" in facets
        assert "regions" in facets

        # 서비스 호출 검증
        mock_service_instance.comprehensive_filter_search.assert_called_once()

    @patch("app.api.deps.get_current_active_user")
    def test_advanced_filter_search_validation_error(self, mock_get_user):
        """
        Given: 유효하지 않은 필터 요청 (잘못된 sort_by)
        When: POST /api/v1/filters/search 호출
        Then: 422 유효성 검사 오류 반환
        """
        # Given: Mock 사용자
        mock_get_user.return_value = self.test_user

        # 잘못된 요청 데이터
        invalid_request = {
            "query": "홍대 카페",
            "sort_by": "invalid_sort",  # 유효하지 않은 정렬 기준
            "limit": 20,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json=invalid_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 유효성 검사 오류 확인
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_data = response.json()
        assert "detail" in error_data

    def test_advanced_filter_search_unauthorized(self):
        """
        Given: 인증되지 않은 요청
        When: POST /api/v1/filters/search 호출
        Then: 401 인증 오류 반환
        """
        # Given: 인증 헤더 없음
        request_data = {
            "query": "홍대 카페",
            "categories": ["cafe"],
        }

        # When: API 호출 (인증 헤더 없음)
        response = self.client.post("/api/v1/filters/search", json=request_data)

        # Then: 인증 오류 확인
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_get_filter_facets_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 패싯 요청
        When: GET /api/v1/filters/facets 호출
        Then: 패싯 정보를 올바르게 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 패싯 응답
        mock_facet_result = {
            "places": [],
            "total": 0,
            "facets": {
                "categories": [
                    {"name": "cafe", "count": 25, "selected": False},
                    {"name": "restaurant", "count": 18, "selected": False},
                ],
                "regions": [
                    {"name": "마포구", "count": 15, "selected": False},
                    {"name": "강남구", "count": 12, "selected": False},
                ],
                "price_ranges": [
                    {"name": "10000-20000", "count": 20, "selected": False},
                    {"name": "20000-50000", "count": 15, "selected": False},
                ],
            },
            "query_info": {"source": "elasticsearch"},
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_facet_result
        )

        # When: API 호출
        response = self.client.get(
            "/api/v1/filters/facets",
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "facets" in response_data
        assert "applied_filters" in response_data
        assert "source" in response_data

        # 패싯 구조 검증
        facets = response_data["facets"]
        assert "categories" in facets
        assert "regions" in facets
        assert "price_ranges" in facets

        # 카테고리 패싯 검증
        categories = facets["categories"]
        assert len(categories) >= 1
        assert all("name" in cat and "count" in cat for cat in categories)

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_get_filter_suggestions_success(self, mock_get_user, mock_get_service):
        """
        Given: 현재 필터 조건
        When: GET /api/v1/filters/suggestions 호출
        Then: 필터 개선 제안을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 제안 응답
        mock_suggestion_result = {
            "places": [],
            "total": 2,  # 적은 결과 수
            "suggestions": {
                "message": "검색 조건을 완화해보세요",
                "alternative_filters": [
                    {"remove_filter": "rating_min", "description": "평점 조건을 낮춰보세요"},
                    {"expand_filter": "location", "description": "검색 반경을 넓혀보세요"},
                ],
            },
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_suggestion_result
        )

        # When: API 호출
        response = self.client.get(
            "/api/v1/filters/suggestions",
            params={"categories": ["cafe"], "rating_min": 4.5},
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "current_results" in response_data
        assert "suggestions" in response_data
        assert "applied_filters" in response_data

        # 제안 내용 검증
        suggestions = response_data["suggestions"]
        assert "message" in suggestions
        assert "alternative_filters" in suggestions

        assert response_data["current_results"] == 2

    @patch("app.api.deps.get_current_active_user")
    def test_save_filter_combination_success(self, mock_get_user):
        """
        Given: 유효한 필터 저장 요청
        When: POST /api/v1/filters/saved 호출
        Then: 필터 조합을 성공적으로 저장함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        # 필터 저장 요청 데이터
        save_request = {
            "name": "홍대 카페 즐겨찾기",
            "filter_criteria": {
                "categories": ["cafe"],
                "regions": ["마포구"],
                "rating_min": 4.0,
            },
            "is_public": False,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/saved",
            json=save_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_201_CREATED

        response_data = response.json()
        assert "id" in response_data
        assert response_data["name"] == "홍대 카페 즐겨찾기"
        assert "filter_criteria" in response_data
        assert response_data["is_public"] is False
        assert response_data["use_count"] == 0

    @patch("app.api.deps.get_current_active_user")
    def test_get_saved_filters_success(self, mock_get_user):
        """
        Given: 인증된 사용자
        When: GET /api/v1/filters/saved 호출
        Then: 저장된 필터 목록을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        # When: API 호출
        response = self.client.get(
            "/api/v1/filters/saved",
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert isinstance(response_data, list)

    @patch("app.api.deps.get_current_active_user")
    def test_get_filter_analytics_success(self, mock_get_user):
        """
        Given: 인증된 사용자
        When: GET /api/v1/filters/analytics 호출
        Then: 필터 분석 정보를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        # When: API 호출
        response = self.client.get(
            "/api/v1/filters/analytics",
            params={"days": 30},
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "popular_filters" in response_data
        assert "filter_effectiveness" in response_data
        assert "user_behavior" in response_data
        assert "performance_stats" in response_data

        # 분석 데이터 구조 검증
        assert isinstance(response_data["popular_filters"], list)
        assert isinstance(response_data["filter_effectiveness"], dict)
        assert "avg_response_time" in response_data["performance_stats"]

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_complex_filter_combination(self, mock_get_user, mock_get_service):
        """
        Given: 복합 필터 조건들
        When: 여러 필터를 조합한 검색 요청
        Then: 모든 조건이 AND로 적용된 결과를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 복합 필터 응답
        mock_complex_result = {
            "places": [
                {
                    "id": str(uuid4()),
                    "name": "홍대 프리미엄 카페",
                    "category": "cafe",
                    "tags": ["조용한", "와이파이", "분위기좋은"],
                    "rating": 4.7,
                    "price_range": 18000,
                    "visit_status": "wishlist",
                    "created_at": "2024-01-15T10:30:45.123Z",
                    "location": {"lat": 37.5563, "lng": 126.9225},
                    "distance_km": 0.5,
                }
            ],
            "total": 1,
            "pagination": {"total": 1, "limit": 20, "offset": 0},
            "applied_filters": {
                "categories": ["cafe"],
                "tags": ["조용한", "와이파이"],
                "price_ranges": ["10000-30000"],
                "rating_min": 4.5,
                "location": {"lat": 37.5563, "lng": 126.9225, "radius_km": 2.0},
                "visit_status": ["wishlist"],
            },
            "query_info": {"source": "elasticsearch"},
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_complex_result
        )

        # 복합 필터 요청
        complex_request = {
            "categories": ["cafe"],
            "tags": ["조용한", "와이파이"],
            "tag_match_mode": "all",
            "price_ranges": ["10000-30000"],
            "rating_min": 4.5,
            "visit_status": ["wishlist"],
            "location": {"lat": 37.5563, "lng": 126.9225, "radius_km": 2.0},
            "sort_by": "distance",
            "limit": 20,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json=complex_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        places = response_data["places"]
        assert len(places) == 1

        place = places[0]
        assert place["category"] == "cafe"
        assert "조용한" in place["tags"]
        assert "와이파이" in place["tags"]
        assert place["rating"] >= 4.5
        assert 10000 <= place["price_range"] <= 30000
        assert place["visit_status"] == "wishlist"
        assert "distance_km" in place

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_empty_results_handling(self, mock_get_user, mock_get_service):
        """
        Given: 결과가 없는 필터 조건
        When: 검색 요청을 보냄
        Then: 빈 결과와 함께 개선 제안을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 빈 결과 응답
        mock_empty_result = {
            "places": [],
            "total": 0,
            "pagination": {"total": 0, "limit": 20, "offset": 0},
            "suggestions": {
                "message": "검색 조건을 완화해보세요",
                "alternative_filters": [
                    {"remove_filter": "rating_min", "description": "평점 조건을 낮춰보세요"},
                ],
            },
            "applied_filters": {"rating_min": 5.0},
            "query_info": {"source": "elasticsearch"},
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_empty_result
        )

        # 제한적인 필터 요청
        restrictive_request = {
            "categories": ["nonexistent"],
            "rating_min": 5.0,
            "limit": 20,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json=restrictive_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["pagination"]["total"] == 0
        assert len(response_data["places"]) == 0
        assert "suggestions" in response_data

        suggestions = response_data["suggestions"]
        assert suggestions["message"] == "검색 조건을 완화해보세요"
        assert len(suggestions["alternative_filters"]) > 0

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_performance_monitoring(self, mock_get_user, mock_get_service):
        """
        Given: 성능 모니터링 활성화
        When: 필터 검색 요청
        Then: 성능 메트릭을 포함한 응답을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 성능 정보가 포함된 응답
        mock_perf_result = {
            "places": [],
            "total": 0,
            "pagination": {"total": 0, "limit": 20, "offset": 0},
            "performance": {
                "total_time_ms": 89,
                "cache_hit": False,
                "optimized": True,
                "elasticsearch_took": 45,
            },
            "applied_filters": {"categories": ["cafe"]},
            "query_info": {"source": "elasticsearch"},
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_perf_result
        )

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json={"categories": ["cafe"], "optimization_mode": True},
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 성능 메트릭 확인
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "performance" in response_data

        performance = response_data["performance"]
        assert "total_time_ms" in performance
        assert "cache_hit" in performance
        assert "elasticsearch_took" in performance
        assert performance["optimized"] is True

    @patch("app.api.api_v1.endpoints.advanced_filters.get_advanced_filter_service")
    @patch("app.api.deps.get_current_active_user")
    def test_pagination_functionality(self, mock_get_user, mock_get_service):
        """
        Given: 페이지네이션 요청
        When: 오프셋과 리밋을 지정한 검색
        Then: 올바른 페이지네이션 정보를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 페이지네이션 응답
        mock_page_result = {
            "places": [{"id": f"place-{i}", "name": f"Place {i}"} for i in range(10)],
            "total": 45,
            "pagination": {
                "total": 45,
                "limit": 10,
                "offset": 20,
                "has_next": True,
                "has_previous": True,
            },
            "applied_filters": {"categories": ["cafe"]},
            "query_info": {"source": "elasticsearch"},
        }

        mock_service_instance.comprehensive_filter_search.return_value = (
            mock_page_result
        )

        # 페이지네이션 요청
        page_request = {
            "categories": ["cafe"],
            "limit": 10,
            "offset": 20,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/filters/search",
            json=page_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 페이지네이션 확인
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        pagination = response_data["pagination"]

        assert pagination["total"] == 45
        assert pagination["limit"] == 10
        assert pagination["offset"] == 20
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is True

        assert len(response_data["places"]) == 10
