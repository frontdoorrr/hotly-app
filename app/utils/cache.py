"""
캐시 유틸리티

Redis 클라이언트 및 캐시 관련 유틸리티 함수를 제공합니다.
"""
import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """비동기 캐시 서비스"""

    def __init__(self):
        self.redis_client: Optional[Redis] = None

    async def connect(self):
        """Redis 연결"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # 연결 테스트
            await self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self.redis_client = None

    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"캐시 조회 실패 ({key}): {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        if not self.redis_client:
            return False

        try:
            json_value = json.dumps(value, default=str)
            if ttl:
                await self.redis_client.setex(key, ttl, json_value)
            else:
                await self.redis_client.set(key, json_value)
            return True
        except Exception as e:
            logger.error(f"캐시 저장 실패 ({key}): {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"캐시 삭제 실패 ({key}): {e}")
            return False

    async def exists(self, key: str) -> bool:
        """캐시 키 존재 확인"""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"캐시 키 존재 확인 실패 ({key}): {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """캐시 만료 시간 설정"""
        if not self.redis_client:
            return False

        try:
            result = await self.redis_client.expire(key, ttl)
            return result
        except Exception as e:
            logger.error(f"캐시 만료 시간 설정 실패 ({key}): {e}")
            return False


# 전역 캐시 서비스 인스턴스
cache_service = CacheService()


async def get_redis_client() -> Optional[Redis]:
    """Redis 클라이언트 조회"""
    if not cache_service.redis_client:
        await cache_service.connect()
    return cache_service.redis_client


async def get_cache_service() -> CacheService:
    """캐시 서비스 조회"""
    if not cache_service.redis_client:
        await cache_service.connect()
    return cache_service


def cache_key(prefix: str, *args) -> str:
    """캐시 키 생성 헬퍼"""
    key_parts = [prefix]
    for arg in args:
        if isinstance(arg, (str, int, float)):
            key_parts.append(str(arg))
        else:
            key_parts.append(str(hash(str(arg))))
    return ":".join(key_parts)
