"""
Redis-based cache management system with distributed locking.

Features:
- URL hash-based cache keys
- Distributed locking for concurrent access prevention
- Multi-layer caching (L1: local, L2: Redis)
- TTL management and cache statistics
- Graceful degradation on Redis failures

Follows hotly:{domain}:{key} naming convention.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from app.exceptions.cache import CacheConnectionError

logger = logging.getLogger(__name__)


class CacheEntry(BaseModel):
    """Cache entry data model."""

    data: Any
    ttl: int
    created_at: datetime

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expiry_time = self.created_at + timedelta(seconds=self.ttl)
        return datetime.now(timezone.utc) > expiry_time

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CacheStats(BaseModel):
    """Cache statistics model."""

    hit_count: int
    miss_count: int

    @property
    def total_requests(self) -> int:
        """Total cache requests."""
        return self.hit_count + self.miss_count

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.hit_count / self.total_requests


class CacheManager:
    """
    Redis-based cache manager with distributed locking and statistics.

    Key features:
    - Consistent hash-based cache keys
    - Distributed locking to prevent race conditions
    - Graceful degradation when Redis is unavailable
    - Real-time cache statistics tracking
    """

    def __init__(self):
        """Initialize cache manager."""
        self._redis: Optional[redis.Redis] = None
        self._local_cache: Dict[str, CacheEntry] = {}  # L1 cache
        self._stats_key = "hotly:cache_stats:global"

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with lazy initialization."""
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                await self._redis.ping()
                logger.info("Redis connection established")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                raise CacheConnectionError(f"Failed to connect to Redis: {e}")

        return self._redis

    def _generate_cache_key(self, url: str) -> str:
        """
        Generate consistent cache key from URL.

        Uses SHA-256 hash for consistent key generation.
        Format: hotly:link_analysis:{hash}
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return f"hotly:link_analysis:{url_hash}"

    def _generate_lock_key(self, url: str) -> str:
        """Generate distributed lock key."""
        cache_key = self._generate_cache_key(url)
        return f"{cache_key}:lock"

    async def _acquire_lock(self, url: str, timeout: int = 30) -> bool:
        """
        Acquire distributed lock for cache key.

        Args:
            url: URL to lock
            timeout: Lock timeout in seconds

        Returns:
            bool: True if lock acquired, False otherwise
        """
        try:
            redis = await self._get_redis()
            lock_key = self._generate_lock_key(url)

            # Try to acquire lock with expiration
            result = await redis.set(
                lock_key, "locked", ex=timeout, nx=True  # Only set if key doesn't exist
            )

            return result is True

        except Exception as e:
            logger.error(f"Lock acquisition failed for {url}: {e}")
            return False

    async def _release_lock(self, url: str) -> bool:
        """Release distributed lock."""
        try:
            redis = await self._get_redis()
            lock_key = self._generate_lock_key(url)
            result = await redis.delete(lock_key)
            return result > 0
        except Exception as e:
            logger.error(f"Lock release failed for {url}: {e}")
            return False

    async def _update_stats(self, hit: bool) -> None:
        """Update cache statistics."""
        try:
            redis = await self._get_redis()
            field = "hits" if hit else "misses"
            await redis.hincrby(self._stats_key, field, 1)
        except Exception as e:
            logger.error(f"Stats update failed: {e}")
            # Don't raise exception for stats failures

    async def set(self, url: str, data: Any, ttl: int = 3600) -> bool:
        """
        Set cache data with TTL.

        Args:
            url: URL key for caching
            data: Data to cache
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)

            # Create cache entry
            entry = CacheEntry(
                data=data, ttl=ttl, created_at=datetime.now(timezone.utc)
            )

            # Store in local cache (L1)
            self._local_cache[cache_key] = entry

            # Store in Redis (L2) with TTL
            redis = await self._get_redis()
            entry_json = entry.json()

            result = await redis.setex(cache_key, ttl, entry_json)

            logger.info(f"Cache set successful for key: {cache_key}")
            return bool(result)

        except Exception as e:
            logger.error(f"Cache set failed for {url}: {e}")
            return False

    async def get(self, url: str) -> Optional[CacheEntry]:
        """
        Get cache data.

        Args:
            url: URL key to retrieve

        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        cache_key = self._generate_cache_key(url)

        # Try local cache first (L1)
        if cache_key in self._local_cache:
            entry = self._local_cache[cache_key]
            if not entry.is_expired():
                await self._update_stats(hit=True)
                logger.debug(f"Cache hit (L1) for key: {cache_key}")
                return entry
            else:
                # Remove expired entry
                del self._local_cache[cache_key]

        # Try Redis cache (L2)
        try:
            redis = await self._get_redis()
            cached_data = await redis.get(cache_key)

            if cached_data:
                entry = CacheEntry.parse_raw(cached_data)

                if not entry.is_expired():
                    # Store in local cache for faster future access
                    self._local_cache[cache_key] = entry
                    await self._update_stats(hit=True)
                    logger.debug(f"Cache hit (L2) for key: {cache_key}")
                    return entry
                else:
                    # Remove expired entry from Redis
                    await redis.delete(cache_key)

        except Exception as e:
            logger.error(f"Cache get failed for {url}: {e}")
            # Graceful degradation - continue without cache

        await self._update_stats(hit=False)
        logger.debug(f"Cache miss for key: {cache_key}")
        return None

    async def delete(self, url: str) -> bool:
        """
        Delete cache entry.

        Args:
            url: URL key to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)

            # Remove from local cache
            self._local_cache.pop(cache_key, None)

            # Remove from Redis
            redis = await self._get_redis()
            result = await redis.delete(cache_key)

            logger.info(f"Cache delete for key: {cache_key}")
            return result > 0

        except Exception as e:
            logger.error(f"Cache delete failed for {url}: {e}")
            return False

    async def exists(self, url: str) -> bool:
        """
        Check if cache key exists.

        Args:
            url: URL key to check

        Returns:
            bool: True if exists, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)

            # Check local cache first
            if cache_key in self._local_cache:
                entry = self._local_cache[cache_key]
                if not entry.is_expired():
                    return True
                else:
                    del self._local_cache[cache_key]

            # Check Redis
            redis = await self._get_redis()
            result = await redis.exists(cache_key)
            return result > 0

        except Exception as e:
            logger.error(f"Cache exists check failed for {url}: {e}")
            return False

    async def get_stats(self) -> CacheStats:
        """
        Get cache statistics.

        Returns:
            CacheStats: Cache hit/miss statistics
        """
        try:
            redis = await self._get_redis()
            stats_data = await redis.hgetall(self._stats_key)

            hit_count = int(stats_data.get("hits", 0))
            miss_count = int(stats_data.get("misses", 0))

            return CacheStats(hit_count=hit_count, miss_count=miss_count)

        except Exception as e:
            logger.error(f"Cache stats retrieval failed: {e}")
            # Return empty stats on failure
            return CacheStats(hit_count=0, miss_count=0)

    async def clear_stats(self) -> bool:
        """Clear cache statistics."""
        try:
            redis = await self._get_redis()
            result = await redis.delete(self._stats_key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache stats clear failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
