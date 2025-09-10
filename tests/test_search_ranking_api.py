"""
검색 랭킹 API 엔드포인트 테스트 (Task 2-3-4)

TDD 접근법으로 API 엔드포인트의 전체 플로우 테스트
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User


class TestSearchRankingAPI:
    """검색 랭킹 API 테스트"""

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

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_rank_search_results_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 검색 랭킹 요청
        When: POST /api/v1/ranking/rank 호출
        Then: 개인화된 랭킹 결과를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 랭킹 결과
        mock_ranking_result = [
            {
                "id": "place_1",
                "name": "홍대 감성 카페",
                "category": "cafe",
                "original_rank": 3,
                "final_rank": 1,
                "final_rank_score": 0.92,
                "personalization_score": 0.85,
                "ranking_factors": {
                    "base_relevance": {
                        "factor_type": "base_relevance",
                        "weight": 0.25,
                        "score": 0.78,
                        "contribution": 0.195,
                    }
                },
                "confidence_score": 0.88,
                "ranking_source": "ml_algorithm",
            }
        ]

        mock_service_instance.rank_search_results.return_value = mock_ranking_result

        # 요청 데이터
        request_data = {
            "query": "홍대 카페",
            "search_results": [
                {"id": "place_1", "name": "홍대 감성 카페", "category": "cafe", "_score": 7.8}
            ],
            "context": {
                "search_type": "text_search",
                "location": {"lat": 37.5563, "lng": 126.9225},
                "explain_ranking": True,
            },
            "max_results": 20,
            "personalization_strength": 0.8,
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/rank",
            json=request_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "ranked_results" in response_data
        assert "total_results" in response_data
        assert "personalization_applied" in response_data
        assert "ranking_metadata" in response_data
        assert "processing_time_ms" in response_data

        # 랭킹 결과 검증
        ranked_results = response_data["ranked_results"]
        assert len(ranked_results) == 1
        result = ranked_results[0]
        assert result["id"] == "place_1"
        assert result["final_rank"] == 1
        assert result["final_rank_score"] == 0.92

        # 메타데이터 검증
        metadata = response_data["ranking_metadata"]
        assert "algorithm_version" in metadata
        assert "personalization_strength" in metadata

        # 서비스 호출 검증
        mock_service_instance.rank_search_results.assert_called_once()

    @patch("app.api.deps.get_current_active_user")
    def test_rank_search_results_validation_error(self, mock_get_user):
        """
        Given: 유효하지 않은 랭킹 요청 (빈 검색 결과)
        When: POST /api/v1/ranking/rank 호출
        Then: 422 유효성 검사 오류 반환
        """
        # Given: Mock 사용자
        mock_get_user.return_value = self.test_user

        # 잘못된 요청 데이터 (빈 검색 결과)
        invalid_request = {
            "query": "홍대 카페",
            "search_results": [],  # 빈 결과
            "context": {"search_type": "text_search"},
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/rank",
            json=invalid_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 유효성 검사 오류 확인
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_rank_search_results_unauthorized(self):
        """
        Given: 인증되지 않은 요청
        When: POST /api/v1/ranking/rank 호출
        Then: 401 인증 오류 반환
        """
        # Given: 인증 헤더 없음
        request_data = {
            "query": "홍대 카페",
            "search_results": [{"id": "place_1", "name": "카페"}],
            "context": {"search_type": "text_search"},
        }

        # When: API 호출 (인증 헤더 없음)
        response = self.client.post("/api/v1/ranking/rank", json=request_data)

        # Then: 인증 오류 확인
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_submit_user_feedback_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 사용자 피드백 요청
        When: POST /api/v1/ranking/feedback 호출
        Then: 피드백이 성공적으로 접수됨
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # 피드백 요청 데이터
        feedback_data = {
            "place_id": "place_12345",
            "feedback_type": "click",
            "query_context": "홍대 카페",
            "session_id": "session_abc123",
            "additional_data": {"search_position": 2, "time_spent": 120},
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/feedback",
            json=feedback_data,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_202_ACCEPTED

        response_data = response.json()
        assert "message" in response_data
        assert "feedback_id" in response_data
        assert "성공적으로 접수" in response_data["message"]

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_get_user_profile_success(self, mock_get_user, mock_get_service):
        """
        Given: 인증된 사용자
        When: GET /api/v1/ranking/profile 호출
        Then: 사용자 프로필 데이터를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock 프로필 데이터
        mock_profile = {
            "preferences": {
                "categories": {"cafe": 0.8, "restaurant": 0.6},
                "regions": {"마포구": 0.9, "강남구": 0.3},
                "tags": {"조용한": 0.9, "분위기좋은": 0.8},
            },
            "behavior_patterns": {
                "distance_tolerance": 3.5,
                "avg_session_duration": 450,
            },
            "interaction_history": {
                "total_searches": 247,
                "click_through_rate": 0.68,
                "conversion_rate": 0.34,
            },
            "last_updated": "2024-01-15T10:30:00Z",
        }

        mock_service_instance._get_user_profile.return_value = mock_profile

        # When: API 호출
        response = self.client.get(
            "/api/v1/ranking/profile",
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "preferences" in response_data
        assert "behavior_patterns" in response_data
        assert "interaction_history" in response_data

        # 선호도 데이터 검증
        preferences = response_data["preferences"]
        assert "categories" in preferences
        assert preferences["categories"]["cafe"] == 0.8

        # 행동 패턴 검증
        behavior = response_data["behavior_patterns"]
        assert behavior["distance_tolerance"] == 3.5

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_update_user_profile_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 프로필 업데이트 요청
        When: PUT /api/v1/ranking/profile 호출
        Then: 프로필이 성공적으로 업데이트됨
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # 프로필 업데이트 데이터
        profile_update = {
            "preferences": {
                "categories": {"cafe": 0.9, "restaurant": 0.7},
                "regions": {"마포구": 1.0},
                "tags": {"조용한": 0.8},
            },
            "behavior_patterns": {
                "distance_tolerance": 4.0,
                "avg_session_duration": 500,
            },
            "interaction_history": {"total_searches": 250, "click_through_rate": 0.70},
        }

        # When: API 호출
        response = self.client.put(
            "/api/v1/ranking/profile",
            json=profile_update,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "message" in response_data
        assert "updated_at" in response_data
        assert "성공적으로 업데이트" in response_data["message"]

        # 캐시 무효화 호출 확인
        mock_service_instance._invalidate_user_ranking_cache.assert_called_once()

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_get_ranking_analytics_success(self, mock_get_user, mock_get_service):
        """
        Given: 유효한 분석 요청
        When: POST /api/v1/ranking/analytics 호출
        Then: 랭킹 분석 데이터를 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # 분석 요청 데이터
        analytics_request = {
            "date_from": "2024-01-01T00:00:00Z",
            "date_to": "2024-01-31T23:59:59Z",
            "metrics": ["click_through_rate", "conversion_rate", "user_satisfaction"],
            "group_by": ["category", "region"],
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/analytics",
            json=analytics_request,
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "period" in response_data
        assert "metrics" in response_data
        assert "trends" in response_data
        assert "recommendations" in response_data

        # 메트릭 검증
        metrics = response_data["metrics"]
        assert "total_searches" in metrics
        assert "avg_click_through_rate" in metrics
        assert "personalization_effectiveness" in metrics

        # 트렌드 데이터 검증
        trends = response_data["trends"]
        assert isinstance(trends, list)
        assert len(trends) > 0

        # 추천사항 검증
        recommendations = response_data["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_get_ml_model_metrics_success(self, mock_get_user, mock_get_service):
        """
        Given: 인증된 사용자
        When: GET /api/v1/ranking/model/metrics 호출
        Then: ML 모델 성능 메트릭을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # When: API 호출
        response = self.client.get(
            "/api/v1/ranking/model/metrics",
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "model_version" in response_data
        assert "accuracy" in response_data
        assert "precision" in response_data
        assert "recall" in response_data
        assert "f1_score" in response_data
        assert "training_date" in response_data
        assert "performance_metrics" in response_data

        # 성능 지표 범위 검증
        assert 0.0 <= response_data["accuracy"] <= 1.0
        assert 0.0 <= response_data["precision"] <= 1.0
        assert 0.0 <= response_data["recall"] <= 1.0
        assert 0.0 <= response_data["f1_score"] <= 1.0

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_update_ranking_config_success(self, mock_get_user, mock_get_service):
        """
        Given: 관리자 권한과 유효한 설정 요청
        When: POST /api/v1/ranking/config 호출
        Then: 랭킹 설정이 성공적으로 업데이트됨
        """
        # Given: Mock 관리자 사용자
        admin_user = User(
            id=self.test_user_id,
            email="admin@example.com",
            username="admin",
            is_active=True,
            is_superuser=True,
        )
        mock_get_user.return_value = admin_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # 설정 업데이트 데이터
        config_request = {
            "ranking_weights": {
                "base_relevance": 0.3,
                "personalization": 0.4,
                "behavior_score": 0.2,
                "contextual": 0.1,
            },
            "personalization_enabled": True,
            "diversity_settings": {"category_diversity": 0.3, "price_diversity": 0.2},
            "cache_settings": {"ranking_cache_ttl": 300, "profile_cache_ttl": 3600},
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/config",
            json=config_request,
            headers={"Authorization": "Bearer admin-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "message" in response_data
        assert "config_id" in response_data
        assert "updated_at" in response_data

    @patch("app.api.deps.get_current_active_user")
    def test_update_ranking_config_forbidden(self, mock_get_user):
        """
        Given: 일반 사용자 (관리자 아님)
        When: POST /api/v1/ranking/config 호출
        Then: 403 권한 오류 반환
        """
        # Given: 일반 사용자
        mock_get_user.return_value = self.test_user

        config_request = {
            "ranking_weights": {"base_relevance": 0.5, "personalization": 0.5},
            "personalization_enabled": True,
            "diversity_settings": {},
            "cache_settings": {},
        }

        # When: API 호출
        response = self.client.post(
            "/api/v1/ranking/config",
            json=config_request,
            headers={"Authorization": "Bearer user-token"},
        )

        # Then: 권한 오류 확인
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_explain_ranking_success(self, mock_get_user, mock_get_service):
        """
        Given: 특정 장소와 검색 컨텍스트
        When: POST /api/v1/ranking/explain/{place_id} 호출
        Then: 랭킹 근거 설명을 반환함
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        place_id = "place_12345"

        # When: API 호출
        response = self.client.post(
            f"/api/v1/ranking/explain/{place_id}",
            params={"query": "홍대 카페"},
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "place_id" in response_data
        assert "final_rank" in response_data
        assert "final_score" in response_data
        assert "factors" in response_data
        assert "summary" in response_data
        assert "confidence_level" in response_data

        # 랭킹 요소 검증
        factors = response_data["factors"]
        assert "base_relevance" in factors
        assert "personalization" in factors
        assert "behavior_score" in factors

        # 각 요소별 상세 정보 확인
        for factor_name, factor_data in factors.items():
            assert "score" in factor_data
            assert "weight" in factor_data
            assert "contribution" in factor_data
            assert "explanation" in factor_data

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_clear_ranking_cache_user_success(self, mock_get_user, mock_get_service):
        """
        Given: 인증된 사용자와 자신의 캐시 삭제 요청
        When: DELETE /api/v1/ranking/cache 호출
        Then: 사용자 캐시가 성공적으로 삭제됨
        """
        # Given: Mock 설정
        mock_get_user.return_value = self.test_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # When: API 호출 (자신의 캐시 삭제)
        response = self.client.delete(
            "/api/v1/ranking/cache",
            params={"user_id": str(self.test_user_id)},
            headers={"Authorization": "Bearer test-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "message" in response_data
        assert "deleted_at" in response_data
        assert str(self.test_user_id) in response_data["message"]

        # 캐시 무효화 호출 확인
        mock_service_instance._invalidate_user_ranking_cache.assert_called_once()

    @patch("app.api.api_v1.endpoints.search_ranking.get_search_ranking_service")
    @patch("app.api.deps.get_current_active_user")
    def test_clear_ranking_cache_admin_success(self, mock_get_user, mock_get_service):
        """
        Given: 관리자 권한과 전체 캐시 삭제 요청
        When: DELETE /api/v1/ranking/cache 호출 (user_id 없음)
        Then: 전체 랭킹 캐시가 삭제됨
        """
        # Given: Mock 관리자
        admin_user = User(
            id=self.test_user_id,
            email="admin@example.com",
            username="admin",
            is_active=True,
            is_superuser=True,
        )
        mock_get_user.return_value = admin_user

        mock_service_instance = AsyncMock()
        mock_get_service.return_value = mock_service_instance

        # Mock Redis scan 동작
        mock_service_instance.redis.scan.side_effect = [
            (10, ["ranking:user1:key1", "ranking:user1:key2"]),  # 첫 번째 스캔
            (0, ["ranking:user2:key1"]),  # 두 번째 스캔 (cursor=0으로 종료)
        ]

        # When: API 호출 (전체 캐시 삭제)
        response = self.client.delete(
            "/api/v1/ranking/cache",
            headers={"Authorization": "Bearer admin-token"},
        )

        # Then: 응답 검증
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert "message" in response_data
        assert "전체 랭킹 캐시" in response_data["message"]
        assert "deleted_at" in response_data

    @patch("app.api.deps.get_current_active_user")
    def test_clear_ranking_cache_forbidden(self, mock_get_user):
        """
        Given: 일반 사용자와 다른 사용자 캐시 삭제 요청
        When: DELETE /api/v1/ranking/cache 호출
        Then: 403 권한 오류 반환
        """
        # Given: 일반 사용자
        mock_get_user.return_value = self.test_user

        other_user_id = uuid4()

        # When: API 호출 (다른 사용자 캐시 삭제 시도)
        response = self.client.delete(
            "/api/v1/ranking/cache",
            params={"user_id": str(other_user_id)},
            headers={"Authorization": "Bearer user-token"},
        )

        # Then: 권한 오류 확인
        assert response.status_code == status.HTTP_403_FORBIDDEN
