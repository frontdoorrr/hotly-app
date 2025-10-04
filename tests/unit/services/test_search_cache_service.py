"""
검색 캐시 서비스 테스트 코드 (Task 2-3-5)

TDD Red Phase: 검색 성능 최적화를 위한 캐싱 시스템 테스트
"""

import json
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.search.search_cache_service import SearchCacheService


class TestSearchCacheService:
    """검색 캐시 서비스 테스트"""

    def setup_method(self) -> None:
        """테스트 설정"""
        self.test_user_id = uuid4()
        self.mock_redis = AsyncMock()
        self.mock_search_service = AsyncMock()

        # 테스트 검색 결과
        self.sample_search_results = [
            {
                "id": "place_1",
                "name": "홍대 감성 카페",
                "category": "cafe",
                "rating": 4.5,
                "distance_km": 0.8,
                "relevance_score": 0.92,
            },
            {
                "id": "place_2",
                "name": "강남 이탈리안 레스토랑",
                "category": "restaurant",
                "rating": 4.8,
                "distance_km": 2.3,
                "relevance_score": 0.87,
            },
        ]

    async def test_basic_search_result_caching(self) -> None:
        """
        Given: 검색 쿼리와 결과
        When: 검색 결과를 캐시에 저장함
        Then: 동일한 쿼리에 대해 캐시된 결과를 빠르게 반환함
        """
        # Given: 캐시 서비스 초기화
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        search_query = {
            "query": "홍대 카페",
            "filters": {"categories": ["cafe"]},
            "location": {"lat": 37.5563, "lng": 126.9225},
        }

        # 첫 번째 요청 - 캐시 미스
        self.mock_redis.get.return_value = None
        self.mock_search_service.search.return_value = {
            "results": self.sample_search_results,
            "total": 2,
            "took_ms": 150,
        }

        # When: 첫 번째 검색 수행 (캐시 저장)
        result1 = await cache_service.cached_search(
            user_id=self.test_user_id, search_params=search_query
        )

        # Then: 검색 서비스 호출 및 캐시 저장 확인
        self.mock_search_service.search.assert_called_once()
        self.mock_redis.setex.assert_called_once()
        assert result1["cache_hit"] is False
        assert result1["total"] == 2
        assert len(result1["results"]) == 2

        # 두 번째 요청 - 캐시 히트
        cached_data = {
            "results": self.sample_search_results,
            "total": 2,
            "took_ms": 150,
            "cached_at": datetime.utcnow().isoformat(),
            "cache_hit": True,
        }
        self.mock_redis.get.return_value = json.dumps(cached_data)

        # When: 두 번째 검색 수행 (캐시 사용)
        result2 = await cache_service.cached_search(
            user_id=self.test_user_id, search_params=search_query
        )

        # Then: 캐시된 결과 반환 확인
        assert result2["cache_hit"] is True
        assert result2["total"] == 2
        assert result2["results"] == self.sample_search_results

    async def test_personalized_cache_keys(self) -> None:
        """
        Given: 동일한 검색 쿼리, 다른 사용자
        When: 사용자별로 검색 캐시를 저장함
        Then: 각 사용자마다 독립적인 캐시 키를 사용함
        """
        # Given: 캐시 서비스와 두 사용자
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        user1_id = uuid4()
        user2_id = uuid4()

        search_query = {
            "query": "맛집",
            "filters": {"categories": ["restaurant"]},
        }

        # When: 각 사용자별로 검색 수행
        await cache_service.cached_search(user1_id, search_query)
        await cache_service.cached_search(user2_id, search_query)

        # Then: 서로 다른 캐시 키로 저장 확인
        cache_calls = self.mock_redis.setex.call_args_list
        assert len(cache_calls) == 2

        key1 = cache_calls[0][0][0]  # 첫 번째 호출의 키
        key2 = cache_calls[1][0][0]  # 두 번째 호출의 키

        assert key1 != key2
        assert str(user1_id) in key1
        assert str(user2_id) in key2

    async def test_cache_expiration_management(self) -> None:
        """
        Given: 다양한 TTL 설정의 캐시 항목들
        When: 시간 경과에 따른 캐시 만료 처리
        Then: TTL에 따라 적절하게 캐시를 관리함
        """
        # Given: TTL 설정이 다른 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis,
            search_service=self.mock_search_service,
            cache_ttl_seconds=300,  # 5분
        )

        search_params = {
            "query": "카페",
            "filters": {"rating_min": 4.0},
        }

        # When: 캐시 저장
        self.mock_redis.get.return_value = None
        self.mock_search_service.search.return_value = {
            "results": self.sample_search_results,
            "total": 2,
        }

        await cache_service.cached_search(self.test_user_id, search_params)

        # Then: 올바른 TTL로 캐시 저장 확인
        self.mock_redis.setex.assert_called_once()
        call_args = self.mock_redis.setex.call_args
        cache_key, ttl, _ = call_args[0]

        assert ttl == 300
        assert "search_cache" in cache_key

    async def test_cache_invalidation_on_data_change(self) -> None:
        """
        Given: 장소 데이터 변경 또는 사용자 선호도 업데이트
        When: 관련 캐시 무효화를 수행함
        Then: 영향받는 캐시 항목들을 적절히 삭제함
        """
        # Given: 캐시 무효화 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        place_id = "place_12345"

        # Mock Redis SCAN for pattern matching
        self.mock_redis.scan.return_value = (
            0,
            [
                f"search_cache:{self.test_user_id}:category_cafe:abc123",
                f"search_cache:{self.test_user_id}:location_hongdae:def456",
                f"search_cache:{uuid4()}:category_restaurant:ghi789",
            ],
        )

        # When: 특정 장소 관련 캐시 무효화
        await cache_service.invalidate_place_cache(place_id)

        # Then: 패턴 매칭으로 관련 캐시 삭제 확인
        self.mock_redis.scan.assert_called()
        self.mock_redis.delete.assert_called()

    async def test_cache_warming_strategy(self) -> None:
        """
        Given: 인기 검색 쿼리들과 사용자 패턴
        When: 캐시 워밍 전략을 실행함
        Then: 자주 사용되는 검색 결과를 미리 캐시에 저장함
        """
        # Given: 캐시 워밍 전략이 있는 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        popular_searches = [
            {"query": "홍대 맛집", "frequency": 150, "avg_response_time": 200},
            {"query": "강남 카페", "frequency": 120, "avg_response_time": 180},
            {"query": "이태원 바", "frequency": 90, "avg_response_time": 220},
        ]

        # Mock search service responses
        self.mock_search_service.search.return_value = {
            "results": self.sample_search_results,
            "total": 2,
        }

        # When: 인기 검색어들을 미리 캐시에 워밍
        warmed_count = await cache_service.warm_popular_searches(
            popular_searches, max_items=2
        )

        # Then: 상위 2개 검색어가 캐시에 저장됨
        assert warmed_count == 2
        assert self.mock_search_service.search.call_count == 2
        assert self.mock_redis.setex.call_count == 2

    async def test_cache_hit_rate_monitoring(self) -> None:
        """
        Given: 캐시 서비스 사용 중
        When: 캐시 히트/미스 이벤트들 발생
        Then: 히트율을 정확히 측정하고 모니터링함
        """
        # Given: 모니터링 기능이 있는 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis,
            search_service=self.mock_search_service,
            enable_monitoring=True,
        )

        search_params = {"query": "테스트"}

        # 첫 3번 요청 - 캐시 미스
        self.mock_redis.get.return_value = None
        self.mock_search_service.search.return_value = {"results": [], "total": 0}

        for _ in range(3):
            await cache_service.cached_search(self.test_user_id, search_params)

        # 다음 7번 요청 - 캐시 히트
        self.mock_redis.get.return_value = json.dumps(
            {"results": [], "total": 0, "cache_hit": True}
        )

        for _ in range(7):
            await cache_service.cached_search(self.test_user_id, search_params)

        # When: 캐시 통계 조회
        stats = await cache_service.get_cache_statistics()

        # Then: 정확한 히트율 측정 확인 (70% = 7/10)
        assert stats["total_requests"] == 10
        assert stats["cache_hits"] == 7
        assert stats["cache_misses"] == 3
        assert stats["hit_rate"] == 0.7
        assert stats["hit_rate"] >= 0.6  # 목표 60% 이상 달성

    async def test_search_result_freshness_check(self) -> None:
        """
        Given: 캐시된 검색 결과의 생성 시간
        When: 결과의 신선도를 확인함
        Then: 오래된 결과는 재검색하여 업데이트함
        """
        # Given: 신선도 검사 기능이 있는 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis,
            search_service=self.mock_search_service,
            freshness_threshold_minutes=30,
        )

        # 오래된 캐시 데이터 (1시간 전)
        old_cached_data = {
            "results": self.sample_search_results,
            "total": 2,
            "cached_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "cache_hit": True,
        }

        self.mock_redis.get.return_value = json.dumps(old_cached_data)
        self.mock_search_service.search.return_value = {
            "results": self.sample_search_results,
            "total": 2,
        }

        # When: 검색 수행
        result = await cache_service.cached_search(
            self.test_user_id, {"query": "오래된 검색"}
        )

        # Then: 신선도 만료로 재검색 수행 확인
        self.mock_search_service.search.assert_called_once()
        assert result["cache_hit"] is False  # 신선도 만료로 재검색됨

    async def test_cache_size_limit_management(self) -> None:
        """
        Given: 캐시 크기 제한 설정
        When: 캐시가 한계에 도달함
        Then: LRU 정책으로 오래된 항목을 제거함
        """
        # Given: 크기 제한이 있는 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis,
            search_service=self.mock_search_service,
            max_cache_size_mb=100,
        )

        # Mock Redis memory usage
        self.mock_redis.memory_usage.return_value = 95 * 1024 * 1024  # 95MB

        # When: 새로운 캐시 항목 추가
        await cache_service.cached_search(self.test_user_id, {"query": "새 검색"})

        # Then: 메모리 사용량 체크 및 정리 작업 수행
        self.mock_redis.memory_usage.assert_called()

    async def test_concurrent_cache_access(self) -> None:
        """
        Given: 동시 다발적인 동일 검색 요청
        When: 여러 요청이 같은 캐시 키에 접근함
        Then: 레이스 컨디션 없이 안전하게 처리함
        """
        # Given: 동시성 제어가 있는 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        search_params = {"query": "동시 검색"}

        # Mock lock acquisition
        self.mock_redis.set.return_value = True  # Lock acquired
        self.mock_redis.get.return_value = None  # Cache miss
        self.mock_search_service.search.return_value = {
            "results": self.sample_search_results,
            "total": 2,
        }

        # When: 동일한 검색을 동시에 수행 (시뮬레이션)
        import asyncio

        tasks = [
            cache_service.cached_search(self.test_user_id, search_params)
            for _ in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # Then: 모든 요청이 성공적으로 처리됨
        assert len(results) == 5
        for result in results:
            assert "results" in result
            assert "total" in result

    async def test_cache_performance_optimization(self) -> None:
        """
        Given: 대용량 검색 결과와 복잡한 쿼리
        When: 성능 최적화된 캐싱을 수행함
        Then: 목표 성능 기준을 만족함 (1초 이내)
        """
        # Given: 성능 최적화된 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis,
            search_service=self.mock_search_service,
            compression_enabled=True,
            async_cache_update=True,
        )

        # 대용량 검색 결과 Mock (1000개 항목)
        large_results = [
            {"id": f"place_{i}", "name": f"장소 {i}", "rating": 4.5} for i in range(1000)
        ]

        self.mock_search_service.search.return_value = {
            "results": large_results,
            "total": 1000,
        }

        # When: 대용량 검색 및 캐싱 수행
        start_time = time.time()

        result = await cache_service.cached_search(
            self.test_user_id, {"query": "대용량 검색"}
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Then: 성능 기준 만족 확인 (1초 이내)
        assert response_time < 1.0  # 1초 이내
        assert result["total"] == 1000
        assert len(result["results"]) == 1000

    async def test_cache_health_monitoring(self) -> None:
        """
        Given: 캐시 서비스 운영 중
        When: 헬스 체크를 수행함
        Then: 캐시 상태와 성능 지표를 반환함
        """
        # Given: 헬스 모니터링이 있는 캐시 서비스
        cache_service = SearchCacheService(
            redis_client=self.mock_redis, search_service=self.mock_search_service
        )

        # Mock Redis info
        self.mock_redis.info.return_value = {
            "used_memory": 50000000,  # 50MB
            "connected_clients": 10,
            "total_commands_processed": 1000,
        }

        # When: 헬스 체크 수행
        health_status = await cache_service.get_health_status()

        # Then: 상태 정보 반환 확인
        assert health_status["status"] == "healthy"
        assert "memory_usage_mb" in health_status
        assert "connected_clients" in health_status
        assert "total_commands" in health_status
        assert health_status["cache_enabled"] is True
