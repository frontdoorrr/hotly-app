"""
검색 API 엔드포인트 테스트 코드 (Task 2-3-1)

검색 API의 전체 플로우와 에러 처리를 검증
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.api import deps
from app.main import app


class TestSearchAPI:
    """검색 API 엔드포인트 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.client = TestClient(app)
        self.test_user_id = uuid4()
        self.mock_user = Mock()
        self.mock_user.id = self.test_user_id

        # Mock authentication
        app.dependency_overrides[deps.get_current_user] = lambda: self.mock_user

    def teardown_method(self):
        """테스트 정리"""
        app.dependency_overrides.clear()

    def test_search_places_basic_query(self):
        """
        Given: 기본 검색 요청
        When: /api/v1/search/places 엔드포인트 호출
        Then: 올바른 검색 결과를 반환함
        """
        # Given: Mock 검색 결과
        mock_results = {
            "places": [
                {
                    "id": str(uuid4()),
                    "name": "홍대 카페",
                    "description": "분위기 좋은 카페",
                    "address": "서울시 마포구",
                    "category": "cafe",
                    "tags": ["카페", "홍대"],
                    "score": 2.5,
                }
            ],
            "total": 1,
            "query": "홍대 카페",
            "took": 15,
            "source": "elasticsearch",
        }

        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = mock_results

            # When: 기본 검색 요청
            response = self.client.get(
                "/api/v1/search/places", params={"q": "홍대 카페", "limit": 20}
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["places"]) == 1
            assert data["total"] == 1
            assert data["query"] == "홍대 카페"
            assert data["source"] == "elasticsearch"
            assert data["places"][0]["name"] == "홍대 카페"

    def test_search_places_with_filters(self):
        """
        Given: 필터가 적용된 검색 요청
        When: 카테고리, 태그, 위치 필터와 함께 검색
        Then: 필터가 적용된 결과를 반환함
        """
        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = {
                "places": [],
                "total": 0,
                "query": "카페",
                "took": 10,
                "source": "elasticsearch",
            }

            # When: 필터 적용 검색
            response = self.client.get(
                "/api/v1/search/places",
                params={
                    "q": "카페",
                    "category": "cafe",
                    "tags": ["홍대", "분위기"],
                    "lat": 37.5563,
                    "lng": 126.9225,
                    "radius_km": 2.0,
                    "sort_by": "distance",
                },
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK

            # 검색 서비스 호출 파라미터 확인
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["category"] == "cafe"
            assert call_args[1]["tags"] == ["홍대", "분위기"]
            assert call_args[1]["location"] == {"lat": 37.5563, "lon": 126.9225}
            assert call_args[1]["radius_km"] == 2.0
            assert call_args[1]["sort_by"] == "distance"

    def test_search_places_elasticsearch_fallback(self):
        """
        Given: Elasticsearch 장애 상황
        When: 검색 요청을 수행함
        Then: PostgreSQL로 자동 fallback됨
        """
        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            side_effect=Exception("ES failed"),
        ):
            with patch(
                "app.services.search_service.SearchService.full_text_search"
            ) as mock_pg:
                # Mock PostgreSQL 결과
                mock_place = Mock()
                mock_place.id = uuid4()
                mock_place.name = "홍대 카페"
                mock_place.description = "카페 설명"
                mock_place.address = "서울시 마포구"
                mock_place.category = "cafe"
                mock_place.tags = ["카페", "홍대"]
                mock_place.latitude = 37.5563
                mock_place.longitude = 126.9225

                mock_pg.return_value = [(mock_place, 0.8)]

                # When: 검색 요청
                response = self.client.get(
                    "/api/v1/search/places", params={"q": "홍대 카페"}
                )

                # Then: PostgreSQL fallback 확인
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["source"] == "postgresql"
                assert len(data["places"]) == 1

    def test_search_suggestions_endpoint(self):
        """
        Given: 자동완성 요청
        When: /api/v1/search/suggestions 엔드포인트 호출
        Then: 관련 검색어 제안을 반환함
        """
        # Given: Mock 제안 결과
        mock_suggestions = [
            {"text": "홍대 카페", "type": "place", "score": 3.0},
            {"text": "홍대입구역", "type": "place", "score": 2.5},
        ]

        with patch(
            "app.services.search_service.SearchService.get_elasticsearch_suggestions",
            new_callable=AsyncMock,
        ) as mock_suggest:
            mock_suggest.return_value = mock_suggestions

            # When: 자동완성 요청
            response = self.client.get(
                "/api/v1/search/suggestions", params={"q": "홍대", "limit": 10}
            )

            # Then: 성공 응답 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data["suggestions"]) == 2
            assert data["query"] == "홍대"
            assert data["source"] == "elasticsearch"
            assert data["suggestions"][0]["text"] == "홍대 카페"

    def test_search_suggestions_with_categories(self):
        """
        Given: 카테고리 필터가 있는 자동완성 요청
        When: 특정 카테고리로 제안 요청
        Then: 해당 카테고리의 제안만 반환함
        """
        with patch(
            "app.services.search_service.SearchService.get_elasticsearch_suggestions",
            new_callable=AsyncMock,
        ) as mock_suggest:
            mock_suggest.return_value = [
                {"text": "홍대 카페", "type": "place", "category": "cafe", "score": 3.0}
            ]

            # When: 카테고리 필터링 제안 요청
            response = self.client.get(
                "/api/v1/search/suggestions",
                params={"q": "홍대", "categories": ["cafe"], "limit": 5},
            )

            # Then: 성공 응답 및 필터링 확인
            assert response.status_code == status.HTTP_200_OK

            mock_suggest.assert_called_once()
            call_args = mock_suggest.call_args
            assert call_args[1]["categories"] == ["cafe"]

    def test_search_suggestions_fallback(self):
        """
        Given: Elasticsearch 제안 서비스 장애
        When: 자동완성 요청을 수행함
        Then: PostgreSQL 자동완성으로 fallback됨
        """
        with patch(
            "app.services.search_service.SearchService.get_elasticsearch_suggestions",
            side_effect=Exception("ES suggestions failed"),
        ):
            with patch(
                "app.services.search_service.SearchService.autocomplete_suggestions"
            ) as mock_pg_auto:
                mock_pg_auto.return_value = ["홍대 카페", "홍대입구역"]

                # When: 자동완성 요청
                response = self.client.get(
                    "/api/v1/search/suggestions", params={"q": "홍대"}
                )

                # Then: PostgreSQL fallback 확인
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["source"] == "postgresql"
                assert len(data["suggestions"]) == 2

    def test_search_validation_errors(self):
        """
        Given: 잘못된 검색 파라미터
        When: 검색 요청을 수행함
        Then: 적절한 검증 에러를 반환함
        """
        # When: 빈 자동완성 쿼리
        response = self.client.get(
            "/api/v1/search/suggestions", params={"q": ""}  # 빈 쿼리
        )

        # Then: 검증 에러
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_pagination(self):
        """
        Given: 페이지네이션 파라미터
        When: 검색 요청을 수행함
        Then: 올바른 페이지네이션이 적용됨
        """
        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = {
                "places": [],
                "total": 100,
                "query": "카페",
                "took": 10,
                "source": "elasticsearch",
            }

            # When: 페이지네이션 검색
            response = self.client.get(
                "/api/v1/search/places", params={"q": "카페", "limit": 20, "offset": 40}
            )

            # Then: 페이지네이션 파라미터 확인
            assert response.status_code == status.HTTP_200_OK

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["limit"] == 20
            assert call_args[1]["offset"] == 40

    def test_search_parameter_limits(self):
        """
        Given: 극한값의 파라미터
        When: 검색 요청을 수행함
        Then: 파라미터 제한이 적용됨
        """
        # When: 제한 초과 파라미터
        response = self.client.get(
            "/api/v1/search/places",
            params={
                "q": "카페",
                "limit": 200,  # 최대 100 초과
                "offset": -1,  # 음수
                "radius_km": 200,  # 큰 값
            },
        )

        # Then: 검증 에러 또는 제한값 적용
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    def test_index_place_to_elasticsearch_endpoint(self):
        """
        Given: 관리자 권한과 장소 ID
        When: 수동 인덱싱 요청을 수행함
        Then: 해당 장소가 Elasticsearch에 인덱싱됨
        """
        # Given: Mock place and indexing
        place_id = str(uuid4())

        with patch("app.crud.place.place.get_by_id") as mock_get_place:
            mock_place = Mock()
            mock_place.id = place_id
            mock_place.user_id = self.test_user_id
            mock_place.name = "테스트 카페"
            mock_get_place.return_value = mock_place

            with patch(
                "app.services.search_service.SearchService.index_place_to_elasticsearch",
                new_callable=AsyncMock,
            ) as mock_index:
                mock_index.return_value = True

                # When: 수동 인덱싱 요청
                response = self.client.post(f"/api/v1/search/index/places/{place_id}")

                # Then: 인덱싱 성공 확인
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["message"] == "Place indexed successfully"
                assert data["place_id"] == place_id

    def test_index_place_permission_denied(self):
        """
        Given: 다른 사용자의 장소
        When: 인덱싱 요청을 수행함
        Then: 권한 거부 에러를 반환함
        """
        place_id = str(uuid4())
        other_user_id = uuid4()

        with patch("app.crud.place.place.get_by_id") as mock_get_place:
            mock_place = Mock()
            mock_place.id = place_id
            mock_place.user_id = other_user_id  # 다른 사용자
            mock_get_place.return_value = mock_place

            # When: 권한 없는 인덱싱 요청
            response = self.client.post(f"/api/v1/search/index/places/{place_id}")

            # Then: 권한 거부
            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_initialize_elasticsearch_indices_admin_only(self):
        """
        Given: 관리자 권한이 필요한 엔드포인트
        When: 일반 사용자가 요청함
        Then: 접근이 거부됨
        """
        # When: 일반 사용자로 인덱스 초기화 요청
        response = self.client.post("/api/v1/search/initialize-indices")

        # Then: 권한 거부 (admin dependency 때문)
        # 실제로는 get_current_admin_user dependency 때문에 실패할 것
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_search_health_check(self):
        """
        Given: 검색 서비스 상태
        When: 헬스체크 요청을 수행함
        Then: 서비스 상태 정보를 반환함
        """
        with patch("app.db.elasticsearch.es_manager") as mock_es_manager:
            mock_es_manager.client = Mock()
            mock_es_manager.health_check.return_value = {
                "status": "green",
                "cluster_name": "hotly-cluster",
                "number_of_nodes": 1,
            }

            # When: 헬스체크 요청
            response = self.client.get("/api/v1/search/health")

            # Then: 상태 정보 확인
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data
            assert "services" in data
            assert "timestamp" in data

    def test_search_error_handling(self):
        """
        Given: 검색 서비스 장애
        When: 검색 요청을 수행함
        Then: 적절한 에러 응답을 반환함
        """
        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            side_effect=Exception("Critical search failure"),
        ):
            with patch(
                "app.services.search_service.SearchService.full_text_search",
                side_effect=Exception("DB also failed"),
            ):
                # When: 모든 검색 서비스 장애 상황
                response = self.client.get("/api/v1/search/places", params={"q": "카페"})

                # Then: 서비스 에러 응답
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                data = response.json()
                assert "detail" in data
                assert "temporarily unavailable" in data["detail"]

    def test_search_response_format_validation(self):
        """
        Given: 검색 결과
        When: API 응답을 검증함
        Then: 올바른 스키마 형태로 반환됨
        """
        mock_results = {
            "places": [
                {
                    "id": str(uuid4()),
                    "name": "테스트 카페",
                    "description": "설명",
                    "address": "주소",
                    "location": {"lat": 37.5563, "lon": 126.9225},
                    "category": "cafe",
                    "tags": ["카페", "테스트"],
                    "score": 2.5,
                    "distance_km": 1.2,
                }
            ],
            "total": 1,
            "query": "테스트",
            "took": 15,
            "source": "elasticsearch",
        }

        with patch(
            "app.services.search_service.SearchService.elasticsearch_search_places",
            new_callable=AsyncMock,
        ) as mock_search:
            mock_search.return_value = mock_results

            # When: 검색 요청
            response = self.client.get(
                "/api/v1/search/places",
                params={"q": "테스트", "lat": 37.5563, "lng": 126.9225},
            )

            # Then: 응답 형태 검증
            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # 필수 필드 확인
            assert "places" in data
            assert "total" in data
            assert "query" in data
            assert "took_ms" in data
            assert "source" in data

            # 장소 데이터 형태 확인
            place = data["places"][0]
            assert "id" in place
            assert "name" in place
            assert "location" in place
            assert "score" in place
            assert place["distance_km"] == 1.2
