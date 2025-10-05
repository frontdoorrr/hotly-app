"""
자동완성 서비스 테스트 코드 (Task 2-3-2)

고도화된 자동완성 기능의 전체 플로우 테스트
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.search.autocomplete_service import AutocompleteService


class TestAutocompleteService:
    """자동완성 서비스 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_db = Mock()
        self.mock_redis = AsyncMock()

        # Mock 장소 데이터
        self.mock_places = [
            Mock(
                id=str(uuid4()),
                user_id=str(self.test_user_id),
                name="홍대 맛집 카페",
                category="cafe",
                address="서울시 마포구 홍익로 123",
                visit_count=5,
                created_at=datetime.utcnow(),
            ),
            Mock(
                id=str(uuid4()),
                user_id=str(self.test_user_id),
                name="강남 이탈리안 레스토랑",
                category="restaurant",
                address="서울시 강남구 테헤란로 456",
                visit_count=3,
                created_at=datetime.utcnow(),
            ),
        ]

    async def test_get_comprehensive_suggestions_basic(self) -> None:
        """
        Given: 기본 자동완성 요청
        When: 종합 제안을 요청함
        Then: 다양한 소스에서 제안을 통합하여 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # Mock 각종 제안 메서드
        with patch.object(
            service, "_get_personalized_suggestions", new_callable=AsyncMock
        ) as mock_personal:
            with patch.object(
                service, "_get_trending_suggestions", new_callable=AsyncMock
            ) as mock_trending:
                with patch.object(
                    service, "_get_popular_suggestions", new_callable=AsyncMock
                ) as mock_popular:
                    with patch.object(
                        service,
                        "_get_elasticsearch_suggestions",
                        new_callable=AsyncMock,
                    ) as mock_es:
                        # 각 메서드별 Mock 반환값
                        mock_personal.return_value = [
                            {
                                "text": "홍대 카페",
                                "type": "personal_history",
                                "score": 2.5,
                                "metadata": {"source": "personal"},
                            }
                        ]

                        mock_trending.return_value = [
                            {
                                "text": "홍대 맛집",
                                "type": "trending",
                                "score": 3.0,
                                "metadata": {"source": "trending"},
                            }
                        ]

                        mock_popular.return_value = [
                            {
                                "text": "홍대입구역",
                                "type": "popular_place",
                                "score": 2.0,
                                "metadata": {"source": "popular"},
                            }
                        ]

                        mock_es.return_value = [
                            {
                                "text": "홍대 술집",
                                "type": "elasticsearch",
                                "score": 2.8,
                                "metadata": {"source": "elasticsearch"},
                            }
                        ]

                        # When: 종합 제안 요청
                        result = await service.get_comprehensive_suggestions(
                            user_id=self.test_user_id, query="홍대", limit=10
                        )

                        # Then: 모든 소스의 제안이 통합됨
                        assert "suggestions" in result
                        assert "categories" in result
                        assert "total" in result
                        assert result["query"] == "홍대"

                        # 제안 개수 확인 (중복 제거 후)
                        assert len(result["suggestions"]) == 4
                        assert result["total"] == 4

                        # 점수순 정렬 확인 (trending: 3.0이 최고점)
                        suggestions = result["suggestions"]
                        assert suggestions[0]["text"] == "홍대 맛집"
                        assert suggestions[0]["score"] == 3.0

    async def test_get_personalized_suggestions(self) -> None:
        """
        Given: 사용자의 개인 검색 기록과 저장된 장소
        When: 개인화 제안을 요청함
        Then: 개인 검색 기록과 사용자 장소 기반 제안을 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # Redis 검색 기록 Mock
        search_history = [
            json.dumps(
                {
                    "query": "홍대 카페",
                    "frequency": 3,
                    "last_searched": datetime.utcnow().isoformat(),
                }
            ),
            json.dumps(
                {
                    "query": "홍대 맛집",
                    "frequency": 2,
                    "last_searched": datetime.utcnow().isoformat(),
                }
            ),
        ]
        self.mock_redis.lrange.return_value = search_history

        # 데이터베이스 쿼리 Mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_places[0]]  # 홍대 카페만 매칭

        self.mock_db.query.return_value = mock_query

        # When: 개인화 제안 요청
        suggestions = await service._get_personalized_suggestions(
            self.test_user_id, "홍대", 5
        )

        # Then: 개인 기록과 사용자 장소 기반 제안 반환
        assert len(suggestions) == 3  # Redis 2개 + DB 1개

        # 개인 검색 기록 제안 확인
        personal_history_suggestions = [
            s for s in suggestions if s["type"] == "personal_history"
        ]
        assert len(personal_history_suggestions) == 2
        assert personal_history_suggestions[0]["text"] == "홍대 카페"
        assert personal_history_suggestions[0]["score"] == 2.0 * 3  # frequency * weight

        # 사용자 장소 제안 확인
        user_place_suggestions = [s for s in suggestions if s["type"] == "user_place"]
        assert len(user_place_suggestions) == 1
        assert user_place_suggestions[0]["text"] == "홍대 맛집 카페"
        assert user_place_suggestions[0]["category"] == "cafe"

    async def test_get_trending_suggestions(self) -> None:
        """
        Given: Redis의 트렌딩 검색어 데이터
        When: 트렌딩 제안을 요청함
        Then: 인기 검색어 기반 제안을 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # Redis 트렌딩 데이터 Mock
        trending_data = [
            ("홍대 맛집".encode(), 25.0),
            ("홍대 카페".encode(), 18.0),
            ("홍대 술집".encode(), 12.0),
        ]
        self.mock_redis.zrevrangebyscore.return_value = trending_data

        # When: 트렌딩 제안 요청
        suggestions = await service._get_trending_suggestions("홍대", 10)

        # Then: 트렌딩 검색어 기반 제안 반환
        assert len(suggestions) == 3
        assert suggestions[0]["text"] == "홍대 맛집"
        assert suggestions[0]["type"] == "trending"
        assert suggestions[0]["score"] == 25.0 * 1.5  # trend_score * weight
        assert suggestions[0]["metadata"]["source"] == "trending"

    async def test_get_popular_suggestions_with_category_filter(self) -> None:
        """
        Given: 카테고리 필터가 있는 인기 제안 요청
        When: 특정 카테고리로 인기 제안을 요청함
        Then: 해당 카테고리의 인기 장소만 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 데이터베이스 쿼리 Mock (카페만 필터링)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            (self.mock_places[0], 15)
        ]  # (place, search_count)

        self.mock_db.query.return_value = mock_query

        # When: 카테고리 필터링 인기 제안 요청
        suggestions = await service._get_popular_suggestions(
            "홍대", 10, categories=["cafe"]
        )

        # Then: 카페 카테고리 인기 장소만 반환
        assert len(suggestions) == 1
        assert suggestions[0]["text"] == "홍대 맛집 카페"
        assert suggestions[0]["type"] == "popular_place"
        assert suggestions[0]["category"] == "cafe"
        assert (
            suggestions[0]["score"] == 1.8 + 15 * 0.1
        )  # base_score + search_count * multiplier

    async def test_get_elasticsearch_suggestions(self) -> None:
        """
        Given: Elasticsearch completion suggester
        When: Elasticsearch 기반 제안을 요청함
        Then: ES completion 결과를 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # Mock ES manager
        with patch("app.services.autocomplete_service.es_manager") as mock_es_manager:
            mock_es_manager.client = Mock()
            mock_es_manager.get_index_name.return_value = "hotly_places"

            # ES completion 결과 Mock
            mock_es_result = {
                "suggest": {
                    "place_suggest": [
                        {
                            "options": [
                                {"text": "홍대입구역 맛집", "_score": 3.5},
                                {"text": "홍대 데이트 카페", "_score": 2.8},
                            ]
                        }
                    ]
                }
            }
            mock_es_manager.client.search.return_value = mock_es_result

            # When: ES 제안 요청
            suggestions = await service._get_elasticsearch_suggestions(
                self.test_user_id, "홍대", 5
            )

            # Then: ES completion 결과 반환
            assert len(suggestions) == 2
            assert suggestions[0]["text"] == "홍대입구역 맛집"
            assert suggestions[0]["type"] == "elasticsearch"
            assert suggestions[0]["score"] == 3.5 * 1.2  # es_score * weight
            assert suggestions[1]["text"] == "홍대 데이트 카페"

    async def test_ranking_and_deduplication(self) -> None:
        """
        Given: 중복된 제안과 다양한 점수의 제안들
        When: 순위 매기기 및 중복 제거를 수행함
        Then: 중복 제거되고 점수순으로 정렬된 결과를 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 중복 포함된 제안 목록
        suggestions = [
            {"text": "홍대 카페", "type": "personal", "score": 2.0},
            {"text": "홍대 맛집", "type": "trending", "score": 3.5},
            {"text": "홍대 카페", "type": "popular", "score": 2.5},  # 중복
            {"text": "홍대 술집", "type": "elasticsearch", "score": 2.8},
            {"text": "홍익대학교", "type": "popular", "score": 1.5},
        ]

        # When: 순위 매기기 및 중복 제거
        result = service._rank_and_deduplicate_suggestions(suggestions, "홍대", 10)

        # Then: 중복 제거 및 점수순 정렬
        assert len(result) == 4  # 중복 1개 제거

        # 점수순 정렬 확인
        assert result[0]["text"] == "홍대 맛집"  # 최고 점수
        assert result[0]["score"] == 3.5

        # 중복 제거 확인 (더 높은 점수가 보존됨)
        cafe_suggestions = [s for s in result if "카페" in s["text"]]
        assert len(cafe_suggestions) == 1
        assert cafe_suggestions[0]["score"] >= 2.5  # 더 높은 점수 보존

    async def test_categorize_suggestions(self) -> None:
        """
        Given: 다양한 타입의 제안들
        When: 카테고리별 분류를 수행함
        Then: 타입별로 올바르게 분류된 결과를 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        suggestions = [
            {"text": "홍대 카페", "type": "personal_history", "score": 2.0},
            {"text": "홍대 맛집", "type": "trending", "score": 3.0},
            {"text": "홍대 술집", "type": "popular_place", "category": "bar", "score": 2.5},
            {"text": "홍익대학교", "type": "user_place", "score": 2.2},
        ]

        # When: 카테고리별 분류
        result = service._categorize_suggestions(suggestions)

        # Then: 올바른 카테고리 분류
        assert "personal" in result
        assert "trending" in result
        assert "popular" in result
        assert "places" in result

        assert len(result["personal"]) == 2  # personal_history + user_place
        assert len(result["trending"]) == 1
        assert len(result["popular"]) == 1
        assert len(result["places"]) == 1  # category가 있는 항목

    async def test_search_query_logging(self) -> None:
        """
        Given: 검색 쿼리
        When: 검색 로그를 기록함
        Then: Redis에 개인 기록과 트렌딩 데이터가 업데이트됨
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 기존 검색 기록이 없는 경우
        self.mock_redis.lrange.return_value = []

        # When: 검색 로그 기록
        await service._log_search_query(self.test_user_id, "홍대 카페")

        # Then: Redis 업데이트 호출 확인
        history_key = f"user_search_history:{self.test_user_id}"
        trending_key = f"trending_searches:{datetime.now().strftime('%Y%m%d')}"

        # 개인 검색 기록 추가 확인
        self.mock_redis.lpush.assert_called_once()
        call_args = self.mock_redis.lpush.call_args
        assert call_args[0][0] == history_key

        # 검색 데이터 구조 확인
        search_data = json.loads(call_args[0][1])
        assert search_data["query"] == "홍대 카페"
        assert search_data["frequency"] == 1

        # 트렌딩 검색어 업데이트 확인
        self.mock_redis.zincrby.assert_called_once_with(trending_key, 1, "홍대 카페")

    async def test_search_analytics(self) -> None:
        """
        Given: 검색 분석 요청
        When: 분석 데이터를 수집함
        Then: 트렌딩, 카테고리, 사용자 패턴 데이터를 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # Redis 트렌딩 데이터 Mock
        trending_data = [("홍대 맛집".encode(), 25.0), ("강남 카페".encode(), 18.0)]
        self.mock_redis.zrevrangebyscore.return_value = trending_data

        # 개인 검색 기록 Mock
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
        self.mock_redis.lrange.return_value = history_data

        # 데이터베이스 카테고리 통계 Mock
        category_stats = [("cafe", 150), ("restaurant", 120), ("bar", 80)]
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = category_stats

        self.mock_db.query.return_value = mock_query

        # When: 분석 데이터 수집
        analytics = await service.get_search_analytics(self.test_user_id)

        # Then: 종합 분석 데이터 반환
        assert "trending_searches" in analytics
        assert "popular_categories" in analytics
        assert "user_search_patterns" in analytics

        # 트렌딩 검색어 확인
        trending_searches = analytics["trending_searches"]
        assert len(trending_searches) == 2
        assert trending_searches[0]["query"] == "홍대 맛집"
        assert trending_searches[0]["count"] == 25

        # 인기 카테고리 확인
        popular_categories = analytics["popular_categories"]
        assert popular_categories["cafe"] == 150
        assert popular_categories["restaurant"] == 120

        # 사용자 검색 패턴 확인
        user_patterns = analytics["user_search_patterns"]
        assert "recent_searches" in user_patterns
        recent_searches = user_patterns["recent_searches"]
        assert len(recent_searches) == 2
        assert recent_searches[0]["query"] == "홍대 카페"

    async def test_cache_optimization(self) -> None:
        """
        Given: 오래된 캐시 데이터
        When: 캐시 최적화를 수행함
        Then: 오래된 데이터가 정리되고 최적화 통계를 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 사용자 검색 기록 키 Mock
        user_keys = [
            f"user_search_history:{uuid4()}".encode(),
            f"user_search_history:{uuid4()}".encode(),
        ]

        # 트렌딩 검색어 키 Mock
        old_date = (datetime.utcnow() - timedelta(days=10)).strftime("%Y%m%d")
        trending_keys = [
            f"trending_searches:{old_date}".encode(),
            f"trending_searches:{datetime.now().strftime('%Y%m%d')}".encode(),
        ]

        # Mock Redis scan_iter 호출별 반환값 설정
        async def mock_scan_iter(match):
            if "user_search_history" in match:
                for key in user_keys:
                    yield key
            elif "trending_searches" in match:
                for key in trending_keys:
                    yield key

        self.mock_redis.scan_iter = mock_scan_iter

        # 오래된 검색 기록 Mock (30일 이상 된 데이터)
        old_search_data = [
            json.dumps(
                {
                    "query": "오래된 검색",
                    "last_searched": (
                        datetime.utcnow() - timedelta(days=35)
                    ).isoformat(),
                }
            )
        ]
        recent_search_data = [
            json.dumps(
                {"query": "최근 검색", "last_searched": datetime.utcnow().isoformat()}
            )
        ]

        self.mock_redis.lrange.return_value = old_search_data + recent_search_data
        self.mock_redis.delete.return_value = 1

        # When: 캐시 최적화 실행
        result = await service.optimize_suggestions_cache()

        # Then: 최적화 결과 확인
        assert result["status"] == "completed"
        assert "cleanup_stats" in result

        cleanup_stats = result["cleanup_stats"]
        assert cleanup_stats["cleaned_users"] >= 0
        assert cleanup_stats["cleaned_trending"] >= 0

    async def test_fallback_to_basic_suggestions(self) -> None:
        """
        Given: 모든 고급 제안 방법이 실패
        When: 기본 제안으로 fallback함
        Then: 간단한 데이터베이스 쿼리 기반 제안을 반환함
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 데이터베이스 쿼리 Mock
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_places[0]]

        self.mock_db.query.return_value = mock_query

        # When: 기본 제안 요청
        result = await service._get_basic_suggestions(self.test_user_id, "홍대", 5)

        # Then: 기본 제안 반환
        assert "suggestions" in result
        assert "categories" in result
        assert result["total"] == 1

        suggestions = result["suggestions"]
        assert len(suggestions) == 1
        assert suggestions[0]["text"] == "홍대 맛집 카페"
        assert suggestions[0]["type"] == "basic"
        assert suggestions[0]["score"] == 1.0

    async def test_korean_analyzer_integration(self) -> None:
        """
        Given: 한국어 검색어
        When: 한국어 분석기를 사용한 제안 순위 조정
        Then: 한국어 키워드 분석이 점수에 반영됨
        """
        # Given: 자동완성 서비스 초기화
        service = AutocompleteService(self.mock_db, self.mock_redis)

        # 한국어 분석기 Mock
        with patch.object(service.korean_analyzer, "analyze_text") as mock_analyze:
            mock_analyze.side_effect = [
                {"keywords": ["홍대", "카페"]},  # 쿼리 분석
                {"keywords": ["홍대", "맛집", "카페"]},  # 첫 번째 제안 분석
                {"keywords": ["강남", "레스토랑"]},  # 두 번째 제안 분석
            ]

            suggestions = [
                {"text": "홍대 맛집 카페", "type": "trending", "score": 2.0},
                {"text": "강남 레스토랑", "type": "popular", "score": 2.5},
            ]

            # When: 순위 매기기 (한국어 분석 포함)
            result = service._rank_and_deduplicate_suggestions(suggestions, "홍대 카페", 10)

            # Then: 키워드 겹침에 따른 점수 조정 확인
            # "홍대 맛집 카페"는 쿼리와 2개 키워드 겹침 (홍대, 카페)
            # "강남 레스토랑"는 쿼리와 겹치는 키워드 없음

            hongdae_suggestion = next(s for s in result if "홍대" in s["text"])
            gangnam_suggestion = next(s for s in result if "강남" in s["text"])

            # 키워드 겹침 보너스로 홍대 제안이 더 높은 점수를 받아야 함
            assert hongdae_suggestion["score"] > 2.0  # 원래 점수보다 증가
            assert gangnam_suggestion["score"] == 2.5  # 키워드 겹침 없어서 원래 점수 유지

    async def test_error_handling(self) -> None:
        """
        Given: 다양한 에러 상황
        When: 자동완성 서비스 메서드 호출
        Then: 적절한 에러 처리와 fallback 동작 확인
        """
        # Given: 자동완성 서비스 초기화 (Redis 없음)
        service = AutocompleteService(self.mock_db, redis_client=None)

        # When & Then: Redis 의존성 메서드들이 안전하게 처리됨

        # 트렌딩 제안 (Redis 없음)
        trending_suggestions = await service._get_trending_suggestions("홍대", 10)
        assert trending_suggestions == []

        # 개인화 제안 (Redis 없지만 DB는 동작)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        personal_suggestions = await service._get_personalized_suggestions(
            self.test_user_id, "홍대", 5
        )
        assert isinstance(personal_suggestions, list)

        # 검색 로그 (Redis 없음)
        await service._log_search_query(self.test_user_id, "홍대")  # 예외 없이 실행되어야 함

        # 전체 제안 요청시 fallback 동작 확인
        with patch.object(
            service, "_get_basic_suggestions", new_callable=AsyncMock
        ) as mock_basic:
            mock_basic.return_value = {
                "suggestions": [],
                "categories": {},
                "total": 0,
                "query": "홍대",
            }

            # 모든 고급 제안 메서드가 실패하는 상황 시뮬레이션
            with patch.object(
                service,
                "_get_personalized_suggestions",
                side_effect=Exception("DB failed"),
            ):
                result = await service.get_comprehensive_suggestions(
                    self.test_user_id, "홍대"
                )

                # fallback이 호출되었는지 확인
                mock_basic.assert_called_once()
                assert result["query"] == "홍대"
