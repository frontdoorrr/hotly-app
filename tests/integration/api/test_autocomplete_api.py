"""
자동완성 API 엔드포인트 테스트 코드 (Task 2-3-2)

자동완성 REST API의 전체 플로우와 에러 처리 검증
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app


class TestAutocompleteAPI:
    """자동완성 API 엔드포인트 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.client = TestClient(app)
        self.test_user_id = uuid4()
        self.mock_user = Mock()
        self.mock_user.id = self.test_user_id
        self.mock_user.is_superuser = False

        # Mock authentication
        app.dependency_overrides[deps.get_current_user] = lambda: self.mock_user

    def teardown_method(self):
        """테스트 정리"""
        app.dependency_overrides.clear()

    def test_get_autocomplete_suggestions_basic(self):
        """
        Given: 기본 자동완성 요청
        When: /api/v1/autocomplete/suggestions 엔드포인트 호출
        Then: 종합적인 자동완성 제안을 반환함
        """
        # Given: Mock 자동완성 결과
        mock_suggestions_data = {
            "suggestions": [
                {
                    "text": "홍대 카페",
                    "type": "trending",
                    "score": 3.2,
                    "category": "cafe",
                    "metadata": {"source": "trending"},
                },
                {
                    "text": "홍대 맛집",
                    "type": "personal_history",
                    "score": 2.8,
                    "category": "restaurant",
                    "metadata": {"source": "personal"},
                },
            ],
            "categories": {
                "trending": [
                    {
                        "text": "홍대 카페",
                        "type": "trending",
                        "score": 3.2,
                        "category": "cafe",
                        "metadata": {"source": "trending"},
                    }
                ],
                "personal": [
                    {
                        "text": "홍대 맛집",
                        "type": "personal_history",
                        "score": 2.8,
                        "category": "restaurant",
                        "metadata": {"source": "personal"},
                    }
                ],
            },
            "total": 2,
            "query": "홍대",
            "timestamp": datetime.utcnow().isoformat(),
        }

        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_comprehensive_suggestions.return_value = (
                mock_suggestions_data
            )
            mock_service_factory.return_value = mock_service

            # When: 기본 자동완성 요청
            response = self.client.get(
                "/api/v1/autocomplete/suggestions", params={"q": "홍대", "limit": 10}
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["suggestions"]) == 2
            assert data["total"] == 2
            assert data["query"] == "홍대"
            assert "categories" in data
            assert "timestamp" in data

            # 첫 번째 제안 상세 확인
            first_suggestion = data["suggestions"][0]
            assert first_suggestion["text"] == "홍대 카페"
            assert first_suggestion["type"] == "trending"
            assert first_suggestion["score"] == 3.2

    def test_get_autocomplete_suggestions_with_filters(self):
        """
        Given: 필터가 포함된 자동완성 요청
        When: 카테고리, 위치 필터와 함께 요청
        Then: 필터가 적용된 제안을 반환함
        """
        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_comprehensive_suggestions.return_value = {
                "suggestions": [],
                "categories": {},
                "total": 0,
                "query": "카페",
                "timestamp": datetime.utcnow().isoformat(),
            }
            mock_service_factory.return_value = mock_service

            # When: 필터 적용 자동완성 요청
            response = self.client.get(
                "/api/v1/autocomplete/suggestions",
                params={
                    "q": "카페",
                    "limit": 10,
                    "include_personal": True,
                    "include_trending": False,
                    "include_popular": True,
                    "categories": ["cafe", "restaurant"],
                    "lat": 37.5563,
                    "lng": 126.9225,
                },
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK

            # 서비스 호출 파라미터 확인
            mock_service.get_comprehensive_suggestions.assert_called_once()
            call_args = mock_service.get_comprehensive_suggestions.call_args

            assert call_args[1]["query"] == "카페"
            assert call_args[1]["include_personal"] is True
            assert call_args[1]["include_trending"] is False
            assert call_args[1]["include_popular"] is True
            assert call_args[1]["categories"] == ["cafe", "restaurant"]
            assert call_args[1]["location"] == {"lat": 37.5563, "lon": 126.9225}

    def test_get_autocomplete_suggestions_validation_error(self):
        """
        Given: 잘못된 파라미터
        When: 자동완성 요청을 수행함
        Then: 적절한 검증 에러를 반환함
        """
        # When: 빈 쿼리로 요청
        response = self.client.get(
            "/api/v1/autocomplete/suggestions", params={"q": ""}  # 빈 쿼리
        )

        # Then: 검증 에러
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When: 잘못된 위도 값
        response = self.client.get(
            "/api/v1/autocomplete/suggestions",
            params={"q": "홍대", "lat": 100.0},  # 잘못된 위도 (>90)
        )

        # Then: 검증 에러
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_autocomplete_suggestions_service_error(self):
        """
        Given: 자동완성 서비스 장애
        When: 자동완성 요청을 수행함
        Then: 적절한 에러 응답을 반환함
        """
        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_comprehensive_suggestions.side_effect = Exception(
                "Service failed"
            )
            mock_service_factory.return_value = mock_service

            # When: 서비스 장애 상황에서 요청
            response = self.client.get(
                "/api/v1/autocomplete/suggestions", params={"q": "홍대"}
            )

            # Then: 서비스 에러 응답
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "자동완성 서비스를 일시적으로 사용할 수 없습니다" in data["detail"]

    def test_get_trending_searches(self):
        """
        Given: 트렌딩 검색어 요청
        When: /api/v1/autocomplete/trending 엔드포인트 호출
        Then: 인기 검색어 목록을 반환함
        """
        # Given: Mock Redis 트렌딩 데이터
        trending_data = [
            ("홍대 맛집".encode(), 25.0),
            ("강남 카페".encode(), 18.0),
            ("이태원 바".encode(), 12.0),
        ]

        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.zrevrangebyscore.return_value = trending_data
            mock_redis_factory.return_value = mock_redis

            # When: 트렌딩 검색어 요청
            response = self.client.get(
                "/api/v1/autocomplete/trending", params={"limit": 10}
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "trending_searches" in data
            assert "total" in data
            assert "time_window_hours" in data

            trending_searches = data["trending_searches"]
            assert len(trending_searches) == 3
            assert trending_searches[0]["query"] == "홍대 맛집"
            assert trending_searches[0]["count"] == 25
            assert trending_searches[0]["type"] == "trending"

    def test_get_trending_searches_no_redis(self):
        """
        Given: Redis 서비스를 사용할 수 없음
        When: 트렌딩 검색어 요청
        Then: 서비스 사용 불가 에러를 반환함
        """
        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis_factory.return_value = None  # Redis 사용 불가

            # When: Redis 없는 상황에서 트렌딩 요청
            response = self.client.get("/api/v1/autocomplete/trending")

            # Then: 서비스 사용 불가 에러
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert "트렌딩 검색어 서비스를 사용할 수 없습니다" in data["detail"]

    def test_get_personal_search_history(self):
        """
        Given: 개인 검색 기록 요청
        When: /api/v1/autocomplete/personal-history 엔드포인트 호출
        Then: 사용자의 검색 기록을 반환함
        """
        # Given: Mock 개인 검색 기록
        history_data = [
            json.dumps(
                {
                    "query": "홍대 카페",
                    "frequency": 3,
                    "last_searched": datetime.utcnow().isoformat(),
                }
            ),
            json.dumps(
                {
                    "query": "강남 맛집",
                    "frequency": 2,
                    "last_searched": datetime.utcnow().isoformat(),
                }
            ),
        ]

        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.lrange.return_value = history_data
            mock_redis_factory.return_value = mock_redis

            # When: 개인 검색 기록 요청
            response = self.client.get(
                "/api/v1/autocomplete/personal-history", params={"limit": 20}
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "search_history" in data
            assert "total" in data
            assert data["user_id"] == str(self.test_user_id)

            search_history = data["search_history"]
            assert len(search_history) == 2
            assert search_history[0]["query"] == "홍대 카페"
            assert search_history[0]["frequency"] == 3
            assert search_history[0]["type"] == "personal_history"

    def test_get_search_analytics(self):
        """
        Given: 검색 분석 요청
        When: /api/v1/autocomplete/analytics 엔드포인트 호출
        Then: 종합적인 검색 분석 데이터를 반환함
        """
        # Given: Mock 분석 데이터
        mock_analytics = {
            "trending_searches": [{"query": "홍대 맛집", "count": 25, "type": "trending"}],
            "popular_categories": {"cafe": 150, "restaurant": 120},
            "user_search_patterns": {
                "recent_searches": [{"query": "홍대 카페", "frequency": 3}]
            },
            "performance_metrics": {"average_response_time_ms": 45.2},
        }

        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_search_analytics.return_value = mock_analytics
            mock_service_factory.return_value = mock_service

            # When: 검색 분석 요청
            response = self.client.get("/api/v1/autocomplete/analytics")

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "trending_searches" in data
            assert "popular_categories" in data
            assert "user_search_patterns" in data
            assert "performance_metrics" in data
            assert "timestamp" in data

            # 데이터 내용 확인
            assert len(data["trending_searches"]) == 1
            assert data["popular_categories"]["cafe"] == 150
            assert len(data["user_search_patterns"]["recent_searches"]) == 1

    def test_optimize_autocomplete_cache_admin_only(self):
        """
        Given: 관리자 권한이 필요한 캐시 최적화
        When: 일반 사용자가 요청함
        Then: 권한 부족 에러를 반환함
        """
        # Given: 일반 사용자 (관리자 아님)
        self.mock_user.is_superuser = False

        # When: 일반 사용자가 캐시 최적화 요청
        response = self.client.post("/api/v1/autocomplete/cache/optimize")

        # Then: 권한 부족 (mock dependency에서 superuser 체크 실패)
        # 실제로는 get_current_active_superuser dependency에서 거부됨
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_optimize_autocomplete_cache_success(self):
        """
        Given: 관리자 권한과 캐시 최적화 요청
        When: 캐시 최적화를 실행함
        Then: 최적화 결과를 반환함
        """
        # Given: 관리자 사용자
        app.dependency_overrides[
            deps.get_current_active_superuser
        ] = lambda: self.mock_user

        mock_optimization_result = {
            "status": "completed",
            "cleanup_stats": {
                "cleaned_users": 15,
                "cleaned_trending": 3,
                "optimized_cache": 45,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.optimize_suggestions_cache.return_value = (
                mock_optimization_result
            )
            mock_service_factory.return_value = mock_service

            with patch("app.api.deps.get_redis_client") as mock_redis_factory:
                mock_redis_factory.return_value = AsyncMock()  # Redis 사용 가능

                # When: 관리자가 캐시 최적화 요청
                response = self.client.post("/api/v1/autocomplete/cache/optimize")

                # Then: 성공 응답 확인
                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["message"] == "캐시 최적화가 완료되었습니다"
                assert "optimization_result" in data
                assert data["optimization_result"]["status"] == "completed"

    def test_clear_personal_search_history(self):
        """
        Given: 개인 검색 기록 삭제 요청
        When: /api/v1/autocomplete/history/clear 엔드포인트 호출
        Then: 사용자의 검색 기록을 삭제함
        """
        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 1  # 삭제된 키 개수
            mock_redis_factory.return_value = mock_redis

            # When: 검색 기록 삭제 요청
            response = self.client.delete("/api/v1/autocomplete/history/clear")

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["message"] == "검색 기록이 삭제되었습니다"
            assert data["deleted"] is True
            assert data["user_id"] == str(self.test_user_id)

            # Redis 호출 확인
            history_key = f"user_search_history:{self.test_user_id}"
            mock_redis.delete.assert_called_once_with(history_key)

    def test_autocomplete_health_check(self):
        """
        Given: 자동완성 서비스 상태 확인 요청
        When: /api/v1/autocomplete/health 엔드포인트 호출
        Then: 서비스 상태 정보를 반환함
        """
        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_redis_factory.return_value = mock_redis

            with patch("app.db.elasticsearch.es_manager") as mock_es_manager:
                mock_es_manager.client = Mock()
                mock_es_manager.health_check.return_value = {"status": "green"}

                # Mock database session
                with patch("app.api.deps.get_db") as mock_get_db:
                    mock_db = Mock()
                    mock_db.execute.return_value = None
                    mock_get_db.return_value = mock_db

                    # When: 헬스체크 요청
                    response = self.client.get("/api/v1/autocomplete/health")

                    # Then: 상태 정보 확인
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()

                    assert "status" in data
                    assert "services" in data
                    assert "timestamp" in data

                    services = data["services"]
                    assert "database" in services
                    assert "redis" in services
                    assert "elasticsearch" in services

    def test_autocomplete_health_check_degraded(self):
        """
        Given: 일부 서비스에 문제가 있는 상황
        When: 헬스체크를 수행함
        Then: degraded 상태를 반환함
        """
        with patch("app.api.deps.get_redis_client") as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Redis connection failed")
            mock_redis_factory.return_value = mock_redis

            with patch("app.api.deps.get_db") as mock_get_db:
                mock_db = Mock()
                mock_db.execute.return_value = None
                mock_get_db.return_value = mock_db

                # When: 헬스체크 요청 (Redis 장애)
                response = self.client.get("/api/v1/autocomplete/health")

                # Then: degraded 상태 확인
                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["status"] == "degraded"
                services = data["services"]
                assert "unhealthy" in services["redis"]
                assert services["database"] == "healthy"

    def test_parameter_validation_limits(self):
        """
        Given: 극한값의 파라미터
        When: 자동완성 요청을 수행함
        Then: 파라미터 제한이 적용됨
        """
        # When: 제한 초과 파라미터로 요청
        response = self.client.get(
            "/api/v1/autocomplete/suggestions",
            params={
                "q": "카페",
                "limit": 25,  # 최대 20 초과
            },
        )

        # Then: 검증 에러
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # When: 최소값 미만 파라미터
        response = self.client.get(
            "/api/v1/autocomplete/suggestions",
            params={
                "q": "카페",
                "limit": 0,  # 최소값 1 미만
            },
        )

        # Then: 검증 에러
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_response_format_validation(self):
        """
        Given: 자동완성 응답
        When: API 응답을 검증함
        Then: 올바른 스키마 형태로 반환됨
        """
        mock_suggestions_data = {
            "suggestions": [
                {
                    "text": "홍대 카페",
                    "type": "trending",
                    "score": 3.2,
                    "category": "cafe",
                    "address": "서울시 마포구",
                    "metadata": {"source": "trending", "trend_score": 15.2},
                }
            ],
            "categories": {"trending": []},
            "total": 1,
            "query": "홍대",
            "timestamp": datetime.utcnow().isoformat(),
        }

        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_comprehensive_suggestions.return_value = (
                mock_suggestions_data
            )
            mock_service_factory.return_value = mock_service

            # When: 자동완성 요청
            response = self.client.get(
                "/api/v1/autocomplete/suggestions", params={"q": "홍대"}
            )

            # Then: 응답 형태 검증
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # 필수 필드 확인
            assert "suggestions" in data
            assert "categories" in data
            assert "total" in data
            assert "query" in data
            assert "timestamp" in data

            # 제안 항목 데이터 형태 확인
            suggestion = data["suggestions"][0]
            assert "text" in suggestion
            assert "type" in suggestion
            assert "score" in suggestion
            assert suggestion["score"] == 3.2
            assert suggestion["category"] == "cafe"
            assert suggestion["address"] == "서울시 마포구"
            assert "metadata" in suggestion

    def test_concurrent_requests_handling(self):
        """
        Given: 동시 다발적인 자동완성 요청
        When: 여러 사용자가 동시에 요청함
        Then: 모든 요청이 정상 처리됨
        """
        with patch(
            "app.services.autocomplete_service.get_autocomplete_service"
        ) as mock_service_factory:
            mock_service = AsyncMock()
            mock_service.get_comprehensive_suggestions.return_value = {
                "suggestions": [],
                "categories": {},
                "total": 0,
                "query": "테스트",
                "timestamp": datetime.utcnow().isoformat(),
            }
            mock_service_factory.return_value = mock_service

            # When: 동시 요청 시뮬레이션
            import concurrent.futures

            def make_request():
                return self.client.get(
                    "/api/v1/autocomplete/suggestions", params={"q": "테스트"}
                )

            # 10개 동시 요청
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                responses = [
                    future.result()
                    for future in concurrent.futures.as_completed(futures)
                ]

            # Then: 모든 요청이 성공
            for response in responses:
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["query"] == "테스트"
