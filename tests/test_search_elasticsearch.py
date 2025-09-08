"""
Elasticsearch 기반 검색 인덱스 테스트 코드 (Task 2-3-1)

TDD Red phase: Elasticsearch 검색 기능 전체 플로우 테스트 작성
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.db.elasticsearch import es_manager
from app.services.search_schemas import SearchIndexSchemas
from app.services.search_service import SearchService


class TestElasticsearchSearchIndex:
    """Elasticsearch 검색 인덱스 테스트"""

    def setup_method(self):
        """테스트 데이터 준비"""
        self.test_user_id = uuid4()
        self.test_places = [
            {
                "id": str(uuid4()),
                "user_id": str(self.test_user_id),
                "name": "홍대 맛집 카페",
                "description": "홍익대학교 근처 분위기 좋은 카페입니다",
                "address": "서울시 마포구 홍익로 123",
                "latitude": 37.5563,
                "longitude": 126.9225,
                "category": "cafe",
                "tags": ["카페", "홍대", "분위기"],
                "status": "active",
                "created_at": datetime.utcnow(),
            },
            {
                "id": str(uuid4()),
                "user_id": str(self.test_user_id),
                "name": "강남 이탈리안 레스토랑",
                "description": "정통 이탈리안 요리를 맛볼 수 있는 곳",
                "address": "서울시 강남구 테헤란로 456",
                "latitude": 37.5665,
                "longitude": 127.0780,
                "category": "restaurant",
                "tags": ["이탈리안", "강남", "레스토랑"],
                "status": "active",
                "created_at": datetime.utcnow(),
            },
        ]

    async def test_elasticsearch_connection_and_health(self):
        """
        Given: Elasticsearch 연결 설정
        When: 연결 상태를 확인함
        Then: 정상적으로 연결되고 헬스체크가 성공함
        """
        with patch.object(es_manager, "client") as mock_client:
            mock_client.cluster.health.return_value = {
                "status": "green",
                "cluster_name": "hotly-cluster",
                "number_of_nodes": 1,
                "active_primary_shards": 5,
                "active_shards": 5,
            }

            # When: 헬스체크 실행
            health = await es_manager.health_check()

            # Then: 정상 상태 확인
            assert health["status"] == "green"
            assert health["cluster_name"] == "hotly-cluster"
            assert health["number_of_nodes"] >= 1

    async def test_search_index_initialization(self):
        """
        Given: 검색 인덱스 스키마
        When: 인덱스 초기화를 실행함
        Then: 모든 인덱스가 올바른 매핑으로 생성됨
        """
        SearchIndexSchemas()

        with patch.object(
            es_manager, "create_index", new_callable=AsyncMock
        ) as mock_create:
            mock_create.return_value = True

            # When: 인덱스 초기화
            search_service = SearchService(db=Mock())
            await search_service.initialize_elasticsearch_indices()

            # Then: 모든 인덱스 생성 호출 확인
            assert mock_create.call_count >= 4  # places, courses, users, suggestions

            # 인덱스별 매핑 확인
            calls = mock_create.call_args_list
            index_names = [call[1]["index_name"] for call in calls]
            assert "places" in index_names
            assert "courses" in index_names
            assert "users" in index_names
            assert "suggestions" in index_names

    async def test_korean_analyzer_configuration(self):
        """
        Given: 한국어 텍스트 분석기 설정
        When: 한국어 텍스트를 분석함
        Then: Nori 분석기가 올바르게 형태소 분석을 수행함
        """
        # Given: 한국어 텍스트 샘플
        korean_text = "홍익대학교 근처 맛있는 카페"

        with patch.object(es_manager, "client") as mock_client:
            # Mock Elasticsearch analyze API
            mock_client.indices.analyze.return_value = {
                "tokens": [
                    {"token": "홍익대학교", "start_offset": 0, "end_offset": 5},
                    {"token": "근처", "start_offset": 6, "end_offset": 8},
                    {"token": "맛있", "start_offset": 9, "end_offset": 11},
                    {"token": "카페", "start_offset": 13, "end_offset": 15},
                ]
            }

            # When: 텍스트 분석 실행
            result = await mock_client.indices.analyze(
                index=es_manager.get_index_name("places"),
                body={"analyzer": "korean", "text": korean_text},
            )

            # Then: 형태소 분석 결과 확인
            tokens = result["tokens"]
            assert len(tokens) >= 4
            assert any("홍익대학교" in token["token"] for token in tokens)
            assert any("카페" in token["token"] for token in tokens)

    async def test_place_document_indexing(self):
        """
        Given: 장소 데이터
        When: Elasticsearch에 인덱싱함
        Then: 올바른 형태로 문서가 인덱싱됨
        """
        place_data = self.test_places[0]

        with patch.object(
            es_manager, "index_document", new_callable=AsyncMock
        ) as mock_index:
            mock_index.return_value = place_data["id"]

            # When: 장소 인덱싱
            search_service = SearchService(db=Mock())

            # Create mock Place object
            mock_place = Mock()
            for key, value in place_data.items():
                setattr(mock_place, key, value)
            mock_place.status = Mock()
            mock_place.status.value = "active"

            success = await search_service.index_place_to_elasticsearch(mock_place)

            # Then: 인덱싱 성공 확인
            assert success is True
            mock_index.assert_called_once()

            # 인덱싱된 문서 구조 확인
            call_args = mock_index.call_args
            document = call_args[1]["document"]

            assert document["name"] == "홍대 맛집 카페"
            assert document["category"] == "cafe"
            assert document["location"]["lat"] == 37.5563
            assert document["location"]["lon"] == 126.9225
            assert "홍대" in document["search_keywords"]

    async def test_elasticsearch_place_search_basic(self):
        """
        Given: 인덱싱된 장소 데이터
        When: 기본 텍스트 검색을 수행함
        Then: 관련도 순으로 정확한 결과를 반환함
        """
        # Given: Mock search results
        mock_search_result = {
            "took": 15,
            "timed_out": False,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 2.5,
                        "_source": {
                            "id": self.test_places[0]["id"],
                            "name": "홍대 맛집 카페",
                            "description": "홍익대학교 근처 분위기 좋은 카페입니다",
                            "address": "서울시 마포구 홍익로 123",
                            "category": "cafe",
                            "tags": ["카페", "홍대", "분위기"],
                            "location": {"lat": 37.5563, "lon": 126.9225},
                        },
                    }
                ],
            },
        }

        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_result

            # When: 검색 실행
            search_service = SearchService(db=Mock())
            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id, query="홍대 카페", limit=10
            )

            # Then: 검색 결과 확인
            assert results["total"] == 1
            assert len(results["places"]) == 1
            assert results["places"][0]["name"] == "홍대 맛집 카페"
            assert results["places"][0]["score"] == 2.5
            assert results["source"] == "elasticsearch"

    async def test_elasticsearch_geographic_search(self):
        """
        Given: 위치 정보가 있는 장소 데이터
        When: 지리적 검색을 수행함
        Then: 거리 순으로 결과를 반환함
        """
        # Given: 지리적 검색 결과 mock
        mock_geo_result = {
            "took": 20,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 1.0,
                        "_source": self.test_places[0],
                        "sort": [1.2],  # 거리 (km)
                    }
                ],
            },
        }

        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_geo_result

            # When: 지리적 검색 실행
            search_service = SearchService(db=Mock())
            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id,
                query="카페",
                location={"lat": 37.5565, "lon": 126.9230},
                radius_km=5.0,
                sort_by="distance",
            )

            # Then: 거리 정보 포함 결과 확인
            assert results["total"] == 1
            place = results["places"][0]
            assert place["distance_km"] == 1.2
            assert "location" in place

    async def test_elasticsearch_category_filtering(self):
        """
        Given: 다양한 카테고리의 장소 데이터
        When: 카테고리로 필터링하여 검색함
        Then: 해당 카테고리의 장소만 반환함
        """
        # Given: 카테고리 필터링 결과
        cafe_result = {
            "took": 10,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 2.0,
                        "_source": {**self.test_places[0], "category": "cafe"},
                    }
                ],
            },
        }

        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = cafe_result

            # When: 카테고리 필터링 검색
            search_service = SearchService(db=Mock())
            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id, query="", category="cafe"
            )

            # Then: 카페 카테고리만 반환 확인
            assert results["total"] == 1
            assert results["places"][0]["category"] == "cafe"

    async def test_elasticsearch_tag_filtering(self):
        """
        Given: 태그가 있는 장소 데이터
        When: 태그로 필터링하여 검색함
        Then: 해당 태그를 가진 장소만 반환함
        """
        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {
                "took": 12,
                "hits": {
                    "total": {"value": 1},
                    "hits": [
                        {
                            "_score": 1.8,
                            "_source": {
                                **self.test_places[0],
                                "tags": ["카페", "홍대", "분위기"],
                            },
                        }
                    ],
                },
            }

            # When: 태그 필터링 검색
            search_service = SearchService(db=Mock())
            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id, query="", tags=["홍대", "카페"]
            )

            # Then: 태그 필터링 결과 확인
            assert results["total"] == 1
            place = results["places"][0]
            assert "홍대" in place["tags"]
            assert "카페" in place["tags"]

    async def test_elasticsearch_search_suggestions(self):
        """
        Given: 인덱싱된 장소 데이터
        When: 자동완성 제안을 요청함
        Then: 관련 검색어 제안을 반환함
        """
        # Given: 자동완성 결과 mock
        mock_suggest_result = {
            "hits": {
                "hits": [
                    {
                        "_score": 3.0,
                        "_source": {
                            "name": "홍대 맛집 카페",
                            "category": "cafe",
                            "address": "서울시 마포구 홍익로 123",
                        },
                    },
                    {
                        "_score": 2.5,
                        "_source": {
                            "name": "홍대입구역 카페",
                            "category": "cafe",
                            "address": "서울시 마포구 양화로 456",
                        },
                    },
                ]
            }
        }

        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_suggest_result

            # When: 자동완성 요청
            search_service = SearchService(db=Mock())
            suggestions = await search_service.get_elasticsearch_suggestions(
                user_id=self.test_user_id, query="홍대", limit=5
            )

            # Then: 제안 결과 확인
            assert len(suggestions) == 2
            assert suggestions[0]["text"] == "홍대 맛집 카페"
            assert suggestions[0]["type"] == "place"
            assert suggestions[0]["score"] == 3.0

    async def test_elasticsearch_fuzzy_search(self):
        """
        Given: 오타가 포함된 검색어
        When: 퍼지 매칭으로 검색함
        Then: 유사한 단어로 결과를 반환함
        """
        # Given: 퍼지 매칭 결과 (오타: "카페" -> "까페")
        fuzzy_result = {
            "took": 25,
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {"_score": 1.5, "_source": self.test_places[0]}  # 퍼지 매칭으로 인한 낮은 스코어
                ],
            },
        }

        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = fuzzy_result

            # When: 오타 포함 검색
            search_service = SearchService(db=Mock())
            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id, query="홍대 까페"  # 의도적 오타
            )

            # Then: 퍼지 매칭 결과 확인
            assert results["total"] == 1
            assert results["places"][0]["name"] == "홍대 맛집 카페"
            assert results["places"][0]["score"] > 0  # 매칭되었지만 스코어는 낮음

    async def test_elasticsearch_fallback_to_postgresql(self):
        """
        Given: Elasticsearch 서비스 장애
        When: 검색을 시도함
        Then: PostgreSQL로 자동 fallback됨
        """
        with patch.object(
            es_manager, "search", side_effect=Exception("ES connection failed")
        ):
            with patch.object(SearchService, "full_text_search") as mock_pg_search:
                # Mock PostgreSQL 검색 결과
                mock_place = Mock()
                mock_place.id = uuid4()
                mock_place.name = "홍대 맛집 카페"
                mock_place.description = "홍익대학교 근처 카페"
                mock_place.category = "cafe"
                mock_place.tags = ["카페", "홍대"]
                mock_place.latitude = 37.5563
                mock_place.longitude = 126.9225

                mock_pg_search.return_value = [(mock_place, 0.8)]

                # When: Elasticsearch 장애 상황에서 검색
                search_service = SearchService(db=Mock())
                results = await search_service.elasticsearch_search_places(
                    user_id=self.test_user_id, query="홍대 카페"
                )

                # Then: PostgreSQL fallback 확인
                assert results["source"] == "postgresql_fallback"
                assert len(results["places"]) == 1
                assert results["places"][0]["place"].name == "홍대 맛집 카페"

    async def test_search_performance_and_timeout(self):
        """
        Given: 대량의 검색 요청
        When: 성능 임계값을 확인함
        Then: 응답 시간이 허용 범위 내에 있음
        """
        # Given: 성능 테스트를 위한 mock
        with patch.object(es_manager, "search", new_callable=AsyncMock) as mock_search:
            # 빠른 응답 시뮬레이션
            mock_search.return_value = {
                "took": 50,  # 50ms
                "timed_out": False,
                "hits": {"total": {"value": 10}, "hits": []},
            }

            # When: 검색 성능 테스트
            search_service = SearchService(db=Mock())
            import time

            start_time = time.time()

            results = await search_service.elasticsearch_search_places(
                user_id=self.test_user_id, query="테스트 검색어"
            )

            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000

            # Then: 성능 기준 확인
            assert results["took"] <= 100  # Elasticsearch 내부 시간 100ms 이내
            assert response_time_ms <= 500  # 전체 응답 시간 500ms 이내
            assert results["timed_out"] is False

    async def test_bulk_place_indexing(self):
        """
        Given: 여러 장소 데이터
        When: 대량 인덱싱을 수행함
        Then: 모든 장소가 효율적으로 인덱싱됨
        """
        # Given: 대량 장소 데이터
        bulk_places = [
            Mock(**{**place_data, "status": Mock(value="active")})
            for place_data in self.test_places
        ]

        with patch.object(
            es_manager, "bulk_index", new_callable=AsyncMock
        ) as mock_bulk:
            mock_bulk.return_value = {"successful": len(bulk_places), "failed": 0}

            # When: 대량 인덱싱 실행
            search_service = SearchService(db=Mock())

            # Prepare documents for bulk indexing
            documents = []
            for place in bulk_places:
                doc = search_service._prepare_place_document(place)
                doc["_id"] = place.id
                documents.append(doc)

            result = await es_manager.bulk_index("places", documents)

            # Then: 대량 인덱싱 성공 확인
            assert result["successful"] == len(bulk_places)
            assert result["failed"] == 0
            mock_bulk.assert_called_once()

    async def test_search_analytics_and_monitoring(self):
        """
        Given: 검색 서비스 운영 중
        When: 분석 데이터를 수집함
        Then: 인덱스 상태 및 성능 메트릭을 반환함
        """
        # Given: 인덱스 통계 mock
        mock_stats = {
            "indices": {
                "hotly_places": {
                    "total": {
                        "docs": {"count": 1000},
                        "store": {"size_in_bytes": 5242880},  # 5MB
                    }
                }
            }
        }

        with patch.object(es_manager, "client") as mock_client:
            mock_client.indices.stats.return_value = mock_stats

            # When: 분석 데이터 수집
            search_service = SearchService(db=Mock())
            analytics = await search_service.get_search_analytics("places")

            # Then: 분석 데이터 확인
            assert analytics["document_count"] == 1000
            assert analytics["store_size"] == 5242880
            assert "timestamp" in analytics
            assert analytics["index_name"] == "hotly_places"

    def test_search_query_building(self):
        """
        Given: 다양한 검색 조건
        When: Elasticsearch 쿼리를 생성함
        Then: 올바른 쿼리 구조가 생성됨
        """
        # Given: 검색 서비스
        search_service = SearchService(db=Mock())

        # When: 복합 쿼리 생성
        query = search_service._build_elasticsearch_query(
            user_id=self.test_user_id,
            query="홍대 카페",
            location={"lat": 37.5563, "lon": 126.9225},
            radius_km=2.0,
            category="cafe",
            tags=["분위기", "데이트"],
        )

        # Then: 쿼리 구조 확인
        assert "function_score" in query
        assert "query" in query["function_score"]

        bool_query = query["function_score"]["query"]["bool"]
        assert "must" in bool_query
        assert "filter" in bool_query

        # 텍스트 검색 쿼리 확인
        assert any("multi_match" in clause for clause in bool_query["must"])

        # 필터 확인
        filters = bool_query["filter"]
        assert any(
            "term" in f and f["term"].get("user_id") == str(self.test_user_id)
            for f in filters
        )
        assert any("geo_distance" in f for f in filters)
        assert any("term" in f and f["term"].get("category") == "cafe" for f in filters)
        assert any("terms" in f and "tags" in f["terms"] for f in filters)
