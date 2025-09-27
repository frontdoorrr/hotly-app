"""
Redis-based cache management system with distributed locking.

Features:
- URL hash-based cache keys with proper normalization
- Distributed locking for concurrent access prevention
- Multi-layer caching (L1: local LRU, L2: Redis)
- TTL management and cache statistics
- Graceful degradation on Redis failures
- Support for different cache key types (link analysis, metadata, AI analysis)

Follows hotly:{domain}:{key} naming convention.
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings
from app.exceptions.cache import (
    CacheConnectionError,
    CacheLockError,
)

logger = logging.getLogger(__name__)


class CacheKey:
    """Cache key generation utilities."""

    @staticmethod
    def link_analysis(url: str) -> str:
        """Generate cache key for link analysis results."""
        normalized_url = CacheKey._normalize_url(url)
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        return f"hotly:link_analysis:{url_hash}"

    @staticmethod
    def metadata_extraction(url: str) -> str:
        """Generate cache key for metadata extraction results."""
        normalized_url = CacheKey._normalize_url(url)
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        return f"hotly:metadata:{url_hash}"

    @staticmethod
    def ai_analysis(url: str) -> str:
        """Generate cache key for AI analysis results."""
        normalized_url = CacheKey._normalize_url(url)
        url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
        return f"hotly:ai_analysis:{url_hash}"

    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize URL for consistent caching.

        Removes tracking parameters and normalizes the URL structure.
        """
        parsed = urlparse(url)

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
            "igshid",
            "_ga",
            "source",
        }

        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }

        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

        # Normalize the URL (convert to lowercase, normalize path)
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.lower().rstrip("/")
                or "/",  # Convert path to lowercase and normalize
                parsed.params,
                new_query,
                "",  # Remove fragment
            )
        )

        return normalized


class LRUCache:
    """Local LRU cache with size limits."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache and mark as recently used."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set item in cache with LRU eviction."""
        if key in self.cache:
            # Update existing item
            self.cache[key] = value
            self.cache.move_to_end(key)
        else:
            # Add new item
            self.cache[key] = value
            if len(self.cache) > self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Remove item from cache."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all items from cache."""
        self.cache.clear()

    def __len__(self) -> int:
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        return key in self.cache


class DistributedLock:
    """Redis-based distributed lock context manager."""

    def __init__(self, redis_client: redis.Redis, resource_key: str, timeout: int = 30):
        self.redis = redis_client
        self.resource_key = resource_key
        self.timeout = timeout
        self.lock_key = f"lock:{resource_key}"
        self.lock_value = str(time.time())

    async def __aenter__(self):
        """Acquire the distributed lock."""
        acquired = await self.redis.set(
            self.lock_key,
            self.lock_value,
            ex=self.timeout,
            nx=True,  # Only set if not exists
        )

        if not acquired:
            raise CacheLockError(f"Failed to acquire lock for {self.resource_key}")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release the distributed lock."""
        try:
            # Use Lua script to ensure we only delete our own lock
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            await self.redis.eval(lua_script, 1, self.lock_key, self.lock_value)
        except Exception as e:
            logger.warning(f"Failed to release lock {self.resource_key}: {e}")


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

    cache_hits: int = 0
    cache_misses: int = 0
    l1_hits: int = 0  # Local cache hits
    l2_hits: int = 0  # Redis cache hits
    total_requests: int = 0

    @property
    def hit_count(self) -> int:
        """Total cache hits (for backward compatibility)."""
        return self.cache_hits

    @property
    def miss_count(self) -> int:
        """Total cache misses (for backward compatibility)."""
        return self.cache_misses

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l1_hits / self.total_requests

    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l2_hits / self.total_requests


class CacheManager:
    """
    Enhanced Redis-based cache manager with distributed locking and multi-layer caching.

    Key features:
    - Multi-layer caching (L1: LRU local cache, L2: Redis)
    - URL normalization for consistent cache keys
    - Distributed locking to prevent race conditions
    - Comprehensive cache statistics
    - Graceful degradation when Redis is unavailable
    - Support for different cache key types
    """

    def __init__(self, local_cache_max_size: int = 1000):
        """Initialize cache manager."""
        self._redis: Optional[redis.Redis] = None
        self._local_cache = LRUCache(max_size=local_cache_max_size)  # L1 cache
        self._local_cache_max_size = local_cache_max_size
        self._stats_key = "hotly:cache_stats:global"
        self._stats_lock = asyncio.Lock()

        # Local statistics for atomic updates
        self._local_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "total_requests": 0,
        }

    async def initialize(self) -> None:
        """Initialize Redis connection and test connectivity."""
        try:
            self._redis = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "localhost"),
                port=getattr(settings, "REDIS_PORT", 6379),
                db=getattr(settings, "REDIS_DB", 0),
                password=getattr(settings, "REDIS_PASSWORD", None),
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

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection."""
        if self._redis is None:
            await self.initialize()
        return self._redis

    def _generate_url_hash(self, url: str) -> str:
        """Generate MD5 hash from URL (for backward compatibility)."""
        normalized_url = CacheKey._normalize_url(url)
        return hashlib.md5(normalized_url.encode()).hexdigest()

    async def _update_stats(
        self, cache_hit: bool, l1_hit: bool = False, l2_hit: bool = False
    ) -> None:
        """Update cache statistics with detailed tracking."""
        async with self._stats_lock:
            self._local_stats["total_requests"] += 1

            if cache_hit:
                self._local_stats["cache_hits"] += 1
                if l1_hit:
                    self._local_stats["l1_hits"] += 1
                elif l2_hit:
                    self._local_stats["l2_hits"] += 1
            else:
                self._local_stats["cache_misses"] += 1

        # Periodically sync to Redis (every 10 requests)
        if self._local_stats["total_requests"] % 10 == 0:
            await self._sync_stats_to_redis()

    async def _sync_stats_to_redis(self) -> None:
        """Sync local statistics to Redis."""
        try:
            redis_client = await self._get_redis()
            async with redis_client.pipeline() as pipe:
                pipe.hincrby(
                    self._stats_key, "cache_hits", self._local_stats["cache_hits"]
                )
                pipe.hincrby(
                    self._stats_key, "cache_misses", self._local_stats["cache_misses"]
                )
                pipe.hincrby(self._stats_key, "l1_hits", self._local_stats["l1_hits"])
                pipe.hincrby(self._stats_key, "l2_hits", self._local_stats["l2_hits"])
                pipe.hincrby(
                    self._stats_key,
                    "total_requests",
                    self._local_stats["total_requests"],
                )
                await pipe.execute()

            # Reset local counters after sync
            self._local_stats = {k: 0 for k in self._local_stats.keys()}

        except Exception as e:
            logger.error(f"Stats sync to Redis failed: {e}")
            # Don't raise exception for stats failures

    async def set(self, cache_key: str, data: Any, ttl: int = 3600) -> bool:
        """
        Set cache data with TTL in both L1 and L2 cache.

        Args:
            cache_key: Cache key (should be generated using CacheKey methods)
            data: Data to cache
            ttl: Time to live in seconds

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create cache entry
            entry = CacheEntry(
                data=data, ttl=ttl, created_at=datetime.now(timezone.utc)
            )

            # Store in local cache (L1)
            self._local_cache.set(cache_key, entry)

            # Store in Redis (L2) with TTL
            try:
                redis_client = await self._get_redis()
                entry_json = entry.json()
                result = await redis_client.setex(cache_key, ttl, entry_json)
                redis_success = bool(result)
            except Exception as e:
                logger.warning(f"Redis cache set failed for {cache_key}: {e}")
                redis_success = False

            logger.debug(
                f"Cache set for key: {cache_key} (L1: ✓, L2: {'✓' if redis_success else '✗'})"
            )
            return True  # Return True if at least L1 cache succeeded

        except Exception as e:
            logger.error(f"Cache set failed for {cache_key}: {e}")
            return False

    async def get(self, cache_key: str) -> Optional[Any]:
        """
        Get cache data from L1 (local) then L2 (Redis) cache.

        Args:
            cache_key: Cache key to retrieve

        Returns:
            Cached data if found and not expired, None otherwise
        """
        # Try local cache first (L1)
        entry = self._local_cache.get(cache_key)
        if entry and not entry.is_expired():
            await self._update_stats(cache_hit=True, l1_hit=True)
            logger.debug(f"Cache hit (L1) for key: {cache_key}")
            return entry.data

        # Remove expired entry from L1 cache
        if entry and entry.is_expired():
            self._local_cache.delete(cache_key)

        # Try Redis cache (L2)
        try:
            redis_client = await self._get_redis()
            cached_data = await redis_client.get(cache_key)

            if cached_data:
                try:
                    entry = CacheEntry.parse_raw(cached_data)
                except Exception as e:
                    logger.error(f"Cache deserialization failed for {cache_key}: {e}")
                    # Clean up corrupted cache entry
                    await redis_client.delete(cache_key)
                    await self._update_stats(cache_hit=False)
                    return None

                if not entry.is_expired():
                    # Store in local cache for faster future access
                    self._local_cache.set(cache_key, entry)
                    await self._update_stats(cache_hit=True, l2_hit=True)
                    logger.debug(f"Cache hit (L2) for key: {cache_key}")
                    return entry.data
                else:
                    # Remove expired entry from Redis
                    await redis_client.delete(cache_key)

        except Exception as e:
            logger.warning(f"Redis cache get failed for {cache_key}: {e}")
            # Graceful degradation - continue without Redis

        await self._update_stats(cache_hit=False)
        logger.debug(f"Cache miss for key: {cache_key}")
        return None

    async def invalidate(self, cache_key: str) -> bool:
        """
        Delete cache entry from both L1 and L2.

        Args:
            cache_key: Cache key to delete

        Returns:
            bool: True if deleted from any cache, False otherwise
        """
        success = False

        # Remove from local cache (L1)
        if self._local_cache.delete(cache_key):
            success = True

        # Remove from Redis (L2)
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(cache_key)
            if result > 0:
                success = True
        except Exception as e:
            logger.warning(f"Redis cache delete failed for {cache_key}: {e}")

        logger.debug(f"Cache invalidate for key: {cache_key}")
        return success

    async def exists(self, cache_key: str) -> bool:
        """
        Check if cache key exists in L1 or L2.

        Args:
            cache_key: Cache key to check

        Returns:
            bool: True if exists and not expired, False otherwise
        """
        # Check local cache first
        entry = self._local_cache.get(cache_key)
        if entry and not entry.is_expired():
            return True

        # Remove expired entry from L1
        if entry and entry.is_expired():
            self._local_cache.delete(cache_key)

        # Check Redis
        try:
            redis_client = await self._get_redis()
            result = await redis_client.exists(cache_key)
            return result > 0
        except Exception as e:
            logger.warning(f"Redis exists check failed for {cache_key}: {e}")
            return False

    async def clear_all(self) -> bool:
        """Clear all cache entries from both L1 and L2."""
        # Clear local cache
        self._local_cache.clear()

        # Clear Redis cache
        try:
            redis_client = await self._get_redis()
            await redis_client.flushdb()
            logger.info("All cache entries cleared")
            return True
        except Exception as e:
            logger.warning(f"Redis cache clear failed: {e}")
            return False

    async def get_stats(self) -> CacheStats:
        """
        Get comprehensive cache statistics.

        Returns:
            CacheStats: Detailed cache statistics
        """
        try:
            # Sync local stats first
            await self._sync_stats_to_redis()

            redis_client = await self._get_redis()
            stats_data = await redis_client.hgetall(self._stats_key)

            cache_hits = int(stats_data.get("cache_hits", 0))
            cache_misses = int(stats_data.get("cache_misses", 0))
            l1_hits = int(stats_data.get("l1_hits", 0))
            l2_hits = int(stats_data.get("l2_hits", 0))
            total_requests = int(stats_data.get("total_requests", 0))

            return CacheStats(
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                l1_hits=l1_hits,
                l2_hits=l2_hits,
                total_requests=total_requests,
            )

        except Exception as e:
            logger.error(f"Cache stats retrieval failed: {e}")
            # Return local stats as fallback
            return CacheStats(
                cache_hits=self._local_stats["cache_hits"],
                cache_misses=self._local_stats["cache_misses"],
                l1_hits=self._local_stats["l1_hits"],
                l2_hits=self._local_stats["l2_hits"],
                total_requests=self._local_stats["total_requests"],
            )

    async def clear_stats(self) -> bool:
        """Clear cache statistics."""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(self._stats_key)

            # Also clear local stats
            self._local_stats = {k: 0 for k in self._local_stats.keys()}

            return result > 0
        except Exception as e:
            logger.error(f"Cache stats clear failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection and sync final stats."""
        try:
            # Final stats sync
            await self._sync_stats_to_redis()
        except Exception as e:
            logger.warning(f"Final stats sync failed: {e}")

        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")
