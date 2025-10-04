"""
검색 히스토리 서비스 테스트 코드 (Task 2-3-5)

TDD Red Phase: 사용자 검색 히스토리 관리 및 개인화 시스템 테스트
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.search.search_history_service import SearchHistoryService


class TestSearchHistoryService:
    """검색 히스토리 서비스 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_redis = AsyncMock()
        self.mock_db = Mock()

        # 테스트 검색 히스토리 데이터
        self.sample_search_history = [
            {
                "query": "홍대 맛집",
                "filters": {"categories": ["restaurant"], "regions": ["마포구"]},
                "timestamp": datetime.utcnow().isoformat(),
                "result_count": 15,
                "clicked_places": ["place_1", "place_2"],
            },
            {
                "query": "강남 카페",
                "filters": {"categories": ["cafe"], "regions": ["강남구"]},
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "result_count": 8,
                "clicked_places": ["place_3"],
            },
        ]

    async def test_search_history_recording(self) -> None:
        """
        Given: 사용자의 검색 행동
        When: 검색 히스토리를 기록함
        Then: 올바른 형태로 히스토리가 저장됨
        """
        # Given: 히스토리 서비스 초기화
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        search_data = {
            "query": "이태원 바",
            "filters": {"categories": ["bar"], "price_max": 50000},
            "location": {"lat": 37.5349, "lng": 126.9941},
            "result_count": 12,
        }

        # When: 검색 히스토리 기록
        await history_service.record_search(
            user_id=self.test_user_id,
            search_data=search_data,
            session_id="session_abc123",
        )

        # Then: Redis에 히스토리 저장 확인
        self.mock_redis.lpush.assert_called_once()
        self.mock_redis.ltrim.assert_called_once()  # 히스토리 크기 제한

        # 저장된 데이터 구조 확인
        call_args = self.mock_redis.lpush.call_args
        history_key = call_args[0][0]
        stored_data = json.loads(call_args[0][1])

        assert f"search_history:{self.test_user_id}" in history_key
        assert stored_data["query"] == "이태원 바"
        assert stored_data["filters"] == search_data["filters"]
        assert "timestamp" in stored_data
        assert "search_id" in stored_data

    async def test_search_history_retrieval(self) -> None:
        """
        Given: 저장된 검색 히스토리
        When: 사용자 히스토리를 조회함
        Then: 최신순으로 정렬된 히스토리를 반환함
        """
        # Given: 히스토리 서비스와 저장된 데이터
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock Redis 데이터 (JSON 문자열 리스트)
        mock_history_data = [
            json.dumps(history) for history in self.sample_search_history
        ]
        self.mock_redis.lrange.return_value = mock_history_data

        # When: 검색 히스토리 조회
        history = await history_service.get_search_history(
            user_id=self.test_user_id, limit=10
        )

        # Then: 올바른 히스토리 데이터 반환 확인
        assert len(history) == 2
        assert history[0]["query"] == "홍대 맛집"
        assert history[1]["query"] == "강남 카페"

        # 최신순 정렬 확인
        time1 = datetime.fromisoformat(history[0]["timestamp"])
        time2 = datetime.fromisoformat(history[1]["timestamp"])
        assert time1 > time2

    async def test_popular_search_terms_analysis(self) -> None:
        """
        Given: 다수 사용자의 검색 히스토리
        When: 인기 검색어를 분석함
        Then: 빈도순으로 정렬된 인기 검색어를 반환함
        """
        # Given: 인기 검색어 분석 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db, enable_analytics=True
        )

        # Mock aggregated search data
        mock_popular_searches = {
            "홍대 맛집": 25,
            "강남 카페": 18,
            "이태원 바": 12,
            "명동 쇼핑": 8,
        }

        with patch.object(history_service, "_aggregate_search_terms") as mock_aggregate:
            mock_aggregate.return_value = mock_popular_searches

            # When: 인기 검색어 조회
            popular_terms = await history_service.get_popular_search_terms(
                time_period_days=7, limit=3
            )

            # Then: 빈도순 정렬된 결과 확인
            assert len(popular_terms) == 3
            assert popular_terms[0]["query"] == "홍대 맛집"
            assert popular_terms[0]["frequency"] == 25
            assert popular_terms[1]["query"] == "강남 카페"
            assert popular_terms[1]["frequency"] == 18
            assert popular_terms[2]["query"] == "이태원 바"
            assert popular_terms[2]["frequency"] == 12

    async def test_personalized_search_suggestions(self) -> None:
        """
        Given: 사용자의 검색 히스토리와 패턴
        When: 개인화된 검색 제안을 생성함
        Then: 사용자 취향에 맞는 검색어를 제안함
        """
        # Given: 개인화 제안 기능이 있는 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock user patterns
        self.mock_redis.lrange.return_value = [
            json.dumps(history) for history in self.sample_search_history
        ]

        # When: 개인화된 제안 생성
        suggestions = await history_service.get_personalized_suggestions(
            user_id=self.test_user_id, current_query="홍대", limit=5
        )

        # Then: 사용자 패턴 기반 제안 확인
        assert len(suggestions) <= 5

        # 제안에 사용자가 자주 검색하는 패턴 포함 확인
        suggestion_queries = [s["suggested_query"] for s in suggestions]
        assert any("맛집" in query for query in suggestion_queries)
        assert any("카페" in query for query in suggestion_queries)

    async def test_search_frequency_tracking(self) -> None:
        """
        Given: 반복되는 검색 쿼리
        When: 검색 빈도를 추적함
        Then: 각 쿼리별 사용 빈도를 정확히 기록함
        """
        # Given: 빈도 추적 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # When: 동일 쿼리 반복 검색
        search_query = "홍대 맛집"
        for i in range(3):
            await history_service.record_search(
                user_id=self.test_user_id,
                search_data={"query": search_query, "filters": {}},
                session_id=f"session_{i}",
            )

        # Then: 빈도 카운터 업데이트 확인
        frequency_calls = self.mock_redis.zincrby.call_args_list
        assert len(frequency_calls) == 3

        # 각 호출이 동일한 쿼리에 대한 증가인지 확인
        for call in frequency_calls:
            assert search_query in str(call)

    async def test_search_history_cleanup(self) -> None:
        """
        Given: 오래된 검색 히스토리
        When: 히스토리 정리를 수행함
        Then: 설정된 기간 이상의 오래된 데이터를 삭제함
        """
        # Given: 정리 기능이 있는 히스토리 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            history_retention_days=30,
        )

        # Mock old history data
        old_history = [
            {
                "query": "오래된 검색",
                "timestamp": (datetime.utcnow() - timedelta(days=35)).isoformat(),
            }
        ]
        recent_history = [
            {
                "query": "최근 검색",
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]

        all_history = old_history + recent_history
        self.mock_redis.lrange.return_value = [json.dumps(h) for h in all_history]

        # When: 히스토리 정리 수행
        cleaned_count = await history_service.cleanup_old_history(
            user_id=self.test_user_id
        )

        # Then: 오래된 데이터만 정리됨
        assert cleaned_count == 1

        # 새로운 히스토리 리스트 저장 확인 (최근 데이터만)
        self.mock_redis.delete.assert_called()  # 기존 리스트 삭제
        self.mock_redis.lpush.assert_called()  # 새 리스트 생성

    async def test_search_interaction_tracking(self) -> None:
        """
        Given: 검색 후 사용자 상호작용
        When: 클릭, 북마크 등의 행동을 추적함
        Then: 검색 결과의 품질을 측정할 수 있는 데이터를 저장함
        """
        # Given: 상호작용 추적 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        search_id = "search_12345"

        # When: 검색 후 상호작용 기록
        interactions = [
            {"place_id": "place_1", "action": "click", "position": 1},
            {"place_id": "place_2", "action": "bookmark", "position": 3},
            {"place_id": "place_1", "action": "visit", "position": 1},
        ]

        for interaction in interactions:
            await history_service.record_search_interaction(
                user_id=self.test_user_id,
                search_id=search_id,
                interaction_data=interaction,
            )

        # Then: 상호작용 데이터 저장 확인
        assert self.mock_redis.hset.call_count == 3

        # 각 상호작용이 올바른 키로 저장되었는지 확인
        for call in self.mock_redis.hset.call_args_list:
            args = call[0]
            assert f"search_interactions:{search_id}" in args[0]

    async def test_search_pattern_analysis(self) -> None:
        """
        Given: 사용자의 검색 히스토리 패턴
        When: 검색 패턴을 분석함
        Then: 사용자의 선호도와 행동 패턴을 도출함
        """
        # Given: 패턴 분석 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            enable_pattern_analysis=True,
        )

        # Mock comprehensive history
        pattern_history = [
            {"query": "홍대 맛집", "filters": {"categories": ["restaurant"]}},
            {"query": "홍대 카페", "filters": {"categories": ["cafe"]}},
            {"query": "마포구 술집", "filters": {"categories": ["bar"]}},
            {"query": "강남 맛집", "filters": {"categories": ["restaurant"]}},
        ]

        self.mock_redis.lrange.return_value = [json.dumps(h) for h in pattern_history]

        # When: 검색 패턴 분석
        patterns = await history_service.analyze_search_patterns(
            user_id=self.test_user_id, analysis_period_days=30
        )

        # Then: 패턴 분석 결과 확인
        assert "preferred_categories" in patterns
        assert "preferred_regions" in patterns
        assert "search_time_patterns" in patterns
        assert "query_complexity_trends" in patterns

        # 카테고리 선호도 확인 (restaurant가 가장 높아야 함)
        preferred_categories = patterns["preferred_categories"]
        assert preferred_categories[0]["category"] == "restaurant"
        assert preferred_categories[0]["frequency"] == 2

    async def test_recent_search_autocomplete(self) -> None:
        """
        Given: 사용자의 최근 검색 히스토리
        When: 자동완성 요청을 처리함
        Then: 최근 검색어 기반 자동완성 제안을 반환함
        """
        # Given: 자동완성 기능이 있는 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock recent searches
        self.mock_redis.lrange.return_value = [
            json.dumps({"query": "홍대 맛집", "timestamp": datetime.utcnow().isoformat()}),
            json.dumps({"query": "홍대 카페", "timestamp": datetime.utcnow().isoformat()}),
            json.dumps({"query": "강남 맛집", "timestamp": datetime.utcnow().isoformat()}),
        ]

        # When: 자동완성 요청
        suggestions = await history_service.get_autocomplete_suggestions(
            user_id=self.test_user_id, partial_query="홍대", limit=5
        )

        # Then: 매칭되는 최근 검색어 반환
        assert len(suggestions) == 2
        suggestion_texts = [s["text"] for s in suggestions]
        assert "홍대 맛집" in suggestion_texts
        assert "홍대 카페" in suggestion_texts
        assert "강남 맛집" not in suggestion_texts  # 부분 매칭 안됨

    async def test_search_session_management(self) -> None:
        """
        Given: 사용자의 검색 세션
        When: 세션 단위로 검색을 그룹핑함
        Then: 연관된 검색들을 하나의 세션으로 관리함
        """
        # Given: 세션 관리 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis,
            db_session=self.mock_db,
            session_timeout_minutes=30,
        )

        session_id = "session_xyz789"

        # When: 동일 세션에서 연속 검색
        searches_in_session = [
            {"query": "홍대", "timestamp": datetime.utcnow()},
            {"query": "홍대 맛집", "timestamp": datetime.utcnow() + timedelta(minutes=2)},
            {"query": "홍대 카페", "timestamp": datetime.utcnow() + timedelta(minutes=5)},
        ]

        for search in searches_in_session:
            await history_service.record_search(
                user_id=self.test_user_id, search_data=search, session_id=session_id
            )

        # When: 세션 검색 히스토리 조회
        session_history = await history_service.get_session_search_history(
            user_id=self.test_user_id, session_id=session_id
        )

        # Then: 세션 내 모든 검색 반환
        assert len(session_history) == 3
        assert session_history[0]["session_id"] == session_id

    async def test_search_history_export(self) -> None:
        """
        Given: 사용자의 검색 히스토리
        When: 데이터 내보내기를 요청함
        Then: 구조화된 형태로 히스토리 데이터를 제공함
        """
        # Given: 데이터 내보내기 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db
        )

        # Mock complete history data
        self.mock_redis.lrange.return_value = [
            json.dumps(history) for history in self.sample_search_history
        ]

        # When: 히스토리 데이터 내보내기
        exported_data = await history_service.export_search_history(
            user_id=self.test_user_id,
            format="json",
            date_from=datetime.utcnow() - timedelta(days=30),
            date_to=datetime.utcnow(),
        )

        # Then: 올바른 형태로 데이터 내보내기 확인
        assert "user_id" in exported_data
        assert "export_date" in exported_data
        assert "search_history" in exported_data
        assert "total_searches" in exported_data

        assert exported_data["user_id"] == str(self.test_user_id)
        assert len(exported_data["search_history"]) == 2

    async def test_search_history_privacy_controls(self) -> None:
        """
        Given: 사용자의 개인정보 관리 요구
        When: 특정 검색 히스토리 삭제 또는 익명화 요청
        Then: 개인정보 보호 정책에 따라 데이터를 처리함
        """
        # Given: 개인정보 관리 서비스
        history_service = SearchHistoryService(
            redis_client=self.mock_redis, db_session=self.mock_db, privacy_mode=True
        )

        # When: 특정 검색 삭제
        await history_service.delete_search_entry(
            user_id=self.test_user_id, search_id="search_to_delete"
        )

        # When: 모든 히스토리 삭제
        await history_service.clear_all_history(
            user_id=self.test_user_id, confirmation_token="confirm_delete_123"
        )

        # Then: 삭제 작업 수행 확인
        self.mock_redis.delete.assert_called()  # 히스토리 삭제

        # 관련 데이터도 함께 삭제되는지 확인
        delete_calls = [str(call) for call in self.mock_redis.delete.call_args_list]
        assert any(
            f"search_history:{self.test_user_id}" in call for call in delete_calls
        )
        assert any(
            f"search_frequency:{self.test_user_id}" in call for call in delete_calls
        )
