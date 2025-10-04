"""
검색 캐시 서비스 (Task 2-3-5)

검색 성능 최적화를 위한 종합적인 캐싱 시스템
- 검색 결과 캐싱 및 무효화
- 캐시 워밍 전략
- 성능 모니터링 및 헬스 체크
- 동시성 제어 및 크기 관리
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class SearchCacheService:
    """검색 캐시 서비스"""

    def __init__(
        self,
        redis_client: redis.Redis,
        search_service: Any,
        cache_ttl_seconds: int = 300,  # 5분
        freshness_threshold_minutes: int = 30,
        max_cache_size_mb: int = 500,
        compression_enabled: bool = True,
        async_cache_update: bool = True,
        enable_monitoring: bool = True,
    ):
        self.redis = redis_client
        self.search_service = search_service
        self.cache_ttl = cache_ttl_seconds
        self.freshness_threshold = timedelta(minutes=freshness_threshold_minutes)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # MB to bytes
        self.compression_enabled = compression_enabled
        self.async_update = async_cache_update
        self.monitoring_enabled = enable_monitoring

        # 캐시 통계 (모니터링 활성화 시)
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 동시성 제어용 락 prefix
        self.lock_prefix = "search_cache_lock:"
        self.lock_ttl = 30  # 30초

    async def cached_search(
        self,
        user_id: UUID,
        search_params: Dict[str, Any],
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        캐시를 활용한 검색 수행

        Args:
            user_id: 사용자 ID
            search_params: 검색 매개변수
            force_refresh: 강제 새로고침 여부

        Returns:
            검색 결과 (cache_hit 정보 포함)
        """
        start_time = time.time()

        try:
            # 통계 업데이트
            if self.monitoring_enabled:
                self.stats["total_requests"] += 1

            # 캐시 키 생성
            cache_key = self._generate_cache_key(user_id, search_params)

            # 강제 새로고침이 아닌 경우 캐시 확인
            if not force_refresh:
                cached_result = await self._get_cached_result(cache_key)
                if cached_result:
                    # 신선도 검사
                    if self._is_result_fresh(cached_result):
                        if self.monitoring_enabled:
                            self.stats["cache_hits"] += 1

                        cached_result["cache_hit"] = True
                        cached_result["response_time_ms"] = int(
                            (time.time() - start_time) * 1000
                        )
                        return cached_result

            # 캐시 미스 또는 만료 - 실제 검색 수행
            if self.monitoring_enabled:
                self.stats["cache_misses"] += 1

            search_result = await self._perform_search_with_lock(
                cache_key, user_id, search_params
            )

            # 결과 후처리
            search_result["cache_hit"] = False
            search_result["response_time_ms"] = int((time.time() - start_time) * 1000)

            return search_result

        except Exception as e:
            logger.error(f"Cached search failed: {str(e)}")
            # Fallback: 캐시 없이 직접 검색
            return await self.search_service.search(user_id, search_params)

    async def _perform_search_with_lock(
        self, cache_key: str, user_id: UUID, search_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """동시성 제어를 포함한 검색 및 캐싱"""
        lock_key = f"{self.lock_prefix}{cache_key}"

        try:
            # 분산 락 획득 시도
            lock_acquired = await self.redis.set(
                lock_key, "locked", nx=True, ex=self.lock_ttl
            )

            if lock_acquired:
                try:
                    # 검색 수행
                    search_result = await self.search_service.search(
                        user_id, search_params
                    )

                    # 결과 캐싱
                    await self._cache_search_result(cache_key, search_result)

                    return search_result

                finally:
                    # 락 해제
                    await self.redis.delete(lock_key)
            else:
                # 락 획득 실패 - 다른 프로세스가 처리 중
                # 잠시 대기 후 캐시 확인
                await asyncio.sleep(0.1)
                cached_result = await self._get_cached_result(cache_key)

                if cached_result:
                    return cached_result
                else:
                    # 캐시가 여전히 없으면 직접 검색
                    return await self.search_service.search(user_id, search_params)

        except Exception as e:
            logger.error(f"Search with lock failed: {str(e)}")
            return await self.search_service.search(user_id, search_params)

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 결과 조회"""
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache get failed: {str(e)}")
        return None

    async def _cache_search_result(
        self, cache_key: str, search_result: Dict[str, Any]
    ) -> None:
        """검색 결과 캐싱"""
        try:
            # 캐시 크기 관리
            await self._manage_cache_size()

            # 캐시 데이터 준비
            cache_data = {
                **search_result,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "v1.0",
            }

            # 압축 옵션 (대용량 결과)
            cache_payload = json.dumps(cache_data, default=str)
            if self.compression_enabled and len(cache_payload) > 10000:  # 10KB 이상
                # 실제 구현에서는 gzip 압축 적용
                pass

            # Redis에 저장
            await self.redis.setex(cache_key, self.cache_ttl, cache_payload)

            logger.debug(f"Cached search result: {cache_key}")

        except Exception as e:
            logger.error(f"Cache set failed: {str(e)}")

    def _generate_cache_key(self, user_id: UUID, search_params: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        # 사용자별, 검색 조건별 고유 키 생성
        key_data = {
            "user_id": str(user_id),
            "params": search_params,
            "version": "v1.0",
        }

        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(
            key_string.encode(), usedforsecurity=False
        ).hexdigest()[:16]

        return f"search_cache:{user_id}:{key_hash}"

    def _is_result_fresh(self, cached_result: Dict[str, Any]) -> bool:
        """결과 신선도 확인"""
        try:
            cached_at_str = cached_result.get("cached_at")
            if not cached_at_str:
                return False

            cached_at = datetime.fromisoformat(cached_at_str)
            age = datetime.utcnow() - cached_at

            return age <= self.freshness_threshold

        except Exception as e:
            logger.warning(f"Freshness check failed: {str(e)}")
            return False

    async def invalidate_place_cache(self, place_id: str) -> int:
        """특정 장소 관련 캐시 무효화"""
        try:
            # 패턴 매칭으로 관련 캐시 키 찾기
            pattern = "search_cache:*"
            invalidated_count = 0
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=100
                )

                if keys:
                    # 각 키의 데이터를 확인하여 해당 장소 포함 여부 체크
                    pipeline = self.redis.pipeline()
                    for key in keys:
                        pipeline.get(key)

                    cached_values = await pipeline.execute()

                    keys_to_delete = []
                    for key, value in zip(keys, cached_values):
                        if value and self._contains_place_id(value, place_id):
                            keys_to_delete.append(key)

                    if keys_to_delete:
                        await self.redis.delete(*keys_to_delete)
                        invalidated_count += len(keys_to_delete)

                if cursor == 0:
                    break

            logger.info(
                f"Invalidated {invalidated_count} cache entries for place {place_id}"
            )
            return invalidated_count

        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")
            return 0

    def _contains_place_id(self, cached_data: str, place_id: str) -> bool:
        """캐시 데이터에 특정 장소 ID 포함 여부 확인"""
        try:
            data = json.loads(cached_data)
            results = data.get("results", [])

            for result in results:
                if result.get("id") == place_id:
                    return True

            return False
        except Exception:
            return False

    async def warm_popular_searches(
        self, popular_searches: List[Dict[str, Any]], max_items: int = 10
    ) -> int:
        """인기 검색어 캐시 워밍"""
        warmed_count = 0

        try:
            # 빈도순으로 정렬하여 상위 검색어 선택
            sorted_searches = sorted(
                popular_searches, key=lambda x: x.get("frequency", 0), reverse=True
            )[:max_items]

            for search_info in sorted_searches:
                try:
                    # 검색 매개변수 구성
                    search_params = {
                        "query": search_info.get("query", ""),
                        "popular_warming": True,
                    }

                    # 대표 사용자 ID로 워밍 (실제로는 시스템 계정 사용)
                    system_user_id = UUID("00000000-0000-0000-0000-000000000000")

                    # 검색 수행 및 캐싱
                    await self.cached_search(system_user_id, search_params)
                    warmed_count += 1

                    logger.debug(f"Warmed cache for: {search_info['query']}")

                except Exception as e:
                    logger.error(f"Cache warming failed for {search_info}: {str(e)}")

        except Exception as e:
            logger.error(f"Cache warming process failed: {str(e)}")

        logger.info(f"Cache warming completed: {warmed_count} items warmed")
        return warmed_count

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        try:
            stats = self.stats.copy()

            # 히트율 계산
            if stats["total_requests"] > 0:
                stats["hit_rate"] = stats["cache_hits"] / stats["total_requests"]
            else:
                stats["hit_rate"] = 0.0

            # Redis 정보
            redis_info = await self.redis.info("memory")
            stats["redis_memory_usage"] = redis_info.get("used_memory", 0)

            # 캐시 키 개수
            cache_keys = await self._count_cache_keys()
            stats["cached_items"] = cache_keys

            return stats

        except Exception as e:
            logger.error(f"Statistics collection failed: {str(e)}")
            return {"error": str(e)}

    async def _count_cache_keys(self) -> int:
        """캐시 키 개수 조회"""
        try:
            cursor = 0
            count = 0
            pattern = "search_cache:*"

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=1000
                )
                count += len(keys)

                if cursor == 0:
                    break

            return count
        except Exception:
            return 0

    async def _manage_cache_size(self) -> None:
        """캐시 크기 관리"""
        try:
            # Redis 메모리 사용량 확인
            memory_usage = await self.redis.memory_usage("search_cache:*") or 0

            if memory_usage > self.max_cache_size:
                # LRU 정책으로 오래된 항목 정리 (Redis 설정 의존)
                # 또는 수동 정리 로직 구현
                logger.warning(f"Cache size limit exceeded: {memory_usage} bytes")

                # 필요시 오래된 캐시 항목 삭제
                await self._cleanup_old_cache_entries()

        except Exception as e:
            logger.error(f"Cache size management failed: {str(e)}")

    async def _cleanup_old_cache_entries(self) -> None:
        """오래된 캐시 항목 정리"""
        try:
            # TTL이 가장 짧은 키들부터 정리
            pattern = "search_cache:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=100
                )

                if keys:
                    # TTL 확인하여 만료 임박 항목 삭제
                    pipeline = self.redis.pipeline()
                    for key in keys:
                        pipeline.ttl(key)

                    ttls = await pipeline.execute()

                    # TTL이 60초 미만인 항목들 삭제
                    keys_to_delete = [
                        key
                        for key, ttl in zip(keys, ttls)
                        if ttl is not None and 0 < ttl < 60
                    ]

                    if keys_to_delete:
                        await self.redis.delete(*keys_to_delete)
                        deleted_count += len(keys_to_delete)

                if cursor == 0:
                    break

            logger.info(f"Cleaned up {deleted_count} cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")

    async def get_health_status(self) -> Dict[str, Any]:
        """캐시 서비스 헬스 체크"""
        try:
            # Redis 연결 상태
            redis_info = await self.redis.info()

            # 기본 상태 정보
            health_status = {
                "status": "healthy",
                "cache_enabled": True,
                "redis_connected": True,
                "memory_usage_mb": redis_info.get("used_memory", 0) // (1024 * 1024),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands": redis_info.get("total_commands_processed", 0),
                "uptime_seconds": redis_info.get("uptime_in_seconds", 0),
            }

            # 캐시 통계 추가
            if self.monitoring_enabled:
                cache_stats = await self.get_cache_statistics()
                health_status.update(
                    {
                        "cache_hit_rate": cache_stats.get("hit_rate", 0),
                        "cached_items": cache_stats.get("cached_items", 0),
                    }
                )

            # 성능 기준 체크
            if health_status["cache_hit_rate"] < 0.3:  # 30% 미만
                health_status["status"] = "degraded"
                health_status["warnings"] = ["Low cache hit rate"]

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "cache_enabled": False,
                "redis_connected": False,
                "error": str(e),
            }

    async def flush_all_cache(self) -> bool:
        """모든 검색 캐시 삭제 (관리자 전용)"""
        try:
            pattern = "search_cache:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor=cursor, match=pattern, count=1000
                )

                if keys:
                    await self.redis.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(f"Flushed {deleted_count} cache entries")
            return True

        except Exception as e:
            logger.error(f"Cache flush failed: {str(e)}")
            return False


# 의존성 주입용 팩토리 함수
def get_search_cache_service(
    redis_client: redis.Redis, search_service: Any
) -> SearchCacheService:
    """검색 캐시 서비스 의존성"""
    return SearchCacheService(redis_client, search_service)
