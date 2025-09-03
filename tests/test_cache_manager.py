"""
Tests for Redis-based cache management system.

Following TDD approach:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize and improve code quality
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.cache_manager import CacheEntry, CacheManager, CacheStats


@pytest.fixture
def cache_manager():
    """Cache manager fixture with mocked Redis."""
    return CacheManager()


@pytest.fixture
def sample_url():
    """Sample URL for testing."""
    return "https://instagram.com/p/ABC123"


@pytest.fixture
def sample_cache_data():
    """Sample cache data for testing."""
    return {
        "place_info": {
            "name": "Test Restaurant",
            "address": "123 Test St",
            "category": "restaurant",
        },
        "confidence": 0.95,
        "analysis_time": 1.5,
    }


class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.mark.asyncio
    async def test_generate_cache_key_creates_consistent_hash(
        self, cache_manager, sample_url
    ):
        """Test cache key generation creates consistent hash."""
        # Given: A URL and cache manager

        # When: Generating cache key multiple times
        key1 = cache_manager._generate_cache_key(sample_url)
        key2 = cache_manager._generate_cache_key(sample_url)

        # Then: Keys should be consistent and follow naming convention
        assert key1 == key2
        assert key1.startswith("hotly:link_analysis:")
        assert len(key1.split(":")[-1]) == 64  # SHA-256 hash length

    @pytest.mark.asyncio
    async def test_generate_cache_key_different_for_different_urls(self, cache_manager):
        """Test cache key generation creates different keys for different URLs."""
        # Given: Two different URLs
        url1 = "https://instagram.com/p/ABC123"
        url2 = "https://instagram.com/p/DEF456"

        # When: Generating cache keys
        key1 = cache_manager._generate_cache_key(url1)
        key2 = cache_manager._generate_cache_key(url2)

        # Then: Keys should be different
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_set_stores_data_with_ttl(
        self, cache_manager, sample_url, sample_cache_data
    ):
        """Test cache set operation stores data with TTL."""
        # Given: Mock Redis connection
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.setex = AsyncMock(return_value=True)

            # When: Setting cache data
            result = await cache_manager.set(sample_url, sample_cache_data, ttl=3600)

            # Then: Redis setex should be called with correct parameters
            assert result is True
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            assert call_args[0][0].startswith("hotly:link_analysis:")  # cache key
            assert call_args[0][1] == 3600  # TTL

    @pytest.mark.asyncio
    async def test_cache_get_retrieves_existing_data(
        self, cache_manager, sample_url, sample_cache_data
    ):
        """Test cache get operation retrieves existing data."""
        # Given: Mock Redis with cached data
        cache_entry = CacheEntry(
            data=sample_cache_data, ttl=3600, created_at=datetime.now(timezone.utc)
        )

        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.get = AsyncMock(return_value=cache_entry.json())

            # When: Getting cache data
            result = await cache_manager.get(sample_url)

            # Then: Should return cached data
            assert result is not None
            assert result.data == sample_cache_data
            assert result.ttl == 3600

    @pytest.mark.asyncio
    async def test_cache_get_returns_none_for_missing_data(
        self, cache_manager, sample_url
    ):
        """Test cache get returns None for missing data."""
        # Given: Mock Redis with no cached data
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)

            # When: Getting non-existent cache data
            result = await cache_manager.get(sample_url)

            # Then: Should return None
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete_removes_data(self, cache_manager, sample_url):
        """Test cache delete operation removes data."""
        # Given: Mock Redis connection
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)  # 1 key deleted

            # When: Deleting cache data
            result = await cache_manager.delete(sample_url)

            # Then: Should return True and call Redis delete
            assert result is True
            mock_redis.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_exists_checks_key_existence(self, cache_manager, sample_url):
        """Test cache exists operation checks key existence."""
        # Given: Mock Redis connection
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.exists = AsyncMock(return_value=1)  # Key exists

            # When: Checking if cache exists
            result = await cache_manager.exists(sample_url)

            # Then: Should return True
            assert result is True
            mock_redis.exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_stats_returns_hit_miss_counts(self, cache_manager):
        """Test cache stats returns hit/miss statistics."""
        # Given: Mock Redis with stats data
        stats_data = {"hits": 100, "misses": 25, "total_requests": 125}

        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.hgetall = AsyncMock(return_value=stats_data)

            # When: Getting cache stats
            stats = await cache_manager.get_stats()

            # Then: Should return CacheStats object
            assert isinstance(stats, CacheStats)
            assert stats.hit_rate == 0.8  # 100/125
            assert stats.miss_count == 25
            assert stats.hit_count == 100

    @pytest.mark.asyncio
    async def test_distributed_lock_prevents_concurrent_access(
        self, cache_manager, sample_url
    ):
        """Test distributed lock prevents concurrent cache access."""
        # Given: Mock Redis connection
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.set = AsyncMock(
                side_effect=[True, False]
            )  # First succeeds, second fails
            mock_redis.delete = AsyncMock(return_value=1)

            # When: Two concurrent lock attempts
            async def acquire_lock():
                return await cache_manager._acquire_lock(sample_url, timeout=1)

            lock1 = await acquire_lock()
            lock2 = await acquire_lock()

            # Then: Only first lock should succeed
            assert lock1 is True
            assert lock2 is False

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_redis_failure(
        self, cache_manager, sample_url
    ):
        """Test graceful degradation when Redis is unavailable."""
        # Given: Mock Redis that raises connection error
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))

            # When: Attempting to get cache data
            # Then: Should not raise exception, return None for graceful degradation
            result = await cache_manager.get(sample_url)
            assert result is None

    @pytest.mark.asyncio
    async def test_cache_connection_error_handling(
        self, cache_manager, sample_url, sample_cache_data
    ):
        """Test proper error handling for cache connection issues."""
        # Given: Mock Redis that raises connection error on set
        with patch.object(cache_manager, "_redis") as mock_redis:
            mock_redis.setex = AsyncMock(side_effect=Exception("Connection timeout"))

            # When: Attempting to set cache data
            # Then: Should handle gracefully and return False
            result = await cache_manager.set(sample_url, sample_cache_data)
            assert result is False


class TestCacheEntry:
    """Test suite for CacheEntry data model."""

    def test_cache_entry_creation_with_valid_data(self, sample_cache_data):
        """Test CacheEntry creation with valid data."""
        # Given: Valid cache data
        ttl = 3600
        created_at = datetime.now(timezone.utc)

        # When: Creating cache entry
        entry = CacheEntry(data=sample_cache_data, ttl=ttl, created_at=created_at)

        # Then: Entry should be created with correct attributes
        assert entry.data == sample_cache_data
        assert entry.ttl == ttl
        assert entry.created_at == created_at

    def test_cache_entry_is_expired_checks_ttl(self, sample_cache_data):
        """Test CacheEntry expiration check."""
        # Given: Cache entry created 2 hours ago with 1 hour TTL
        created_at = datetime.now(timezone.utc) - timedelta(hours=2)
        entry = CacheEntry(
            data=sample_cache_data, ttl=3600, created_at=created_at  # 1 hour
        )

        # When: Checking if expired
        is_expired = entry.is_expired()

        # Then: Should be expired
        assert is_expired is True

    def test_cache_entry_is_not_expired_within_ttl(self, sample_cache_data):
        """Test CacheEntry is not expired within TTL."""
        # Given: Recently created cache entry
        created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
        entry = CacheEntry(
            data=sample_cache_data, ttl=3600, created_at=created_at  # 1 hour
        )

        # When: Checking if expired
        is_expired = entry.is_expired()

        # Then: Should not be expired
        assert is_expired is False


class TestCacheStats:
    """Test suite for CacheStats data model."""

    def test_cache_stats_calculates_hit_rate_correctly(self):
        """Test CacheStats calculates hit rate correctly."""
        # Given: Hit and miss counts
        hit_count = 80
        miss_count = 20

        # When: Creating cache stats
        stats = CacheStats(hit_count=hit_count, miss_count=miss_count)

        # Then: Hit rate should be calculated correctly
        assert stats.hit_rate == 0.8  # 80/100
        assert stats.total_requests == 100

    def test_cache_stats_handles_zero_requests(self):
        """Test CacheStats handles zero requests gracefully."""
        # Given: Zero hit and miss counts
        hit_count = 0
        miss_count = 0

        # When: Creating cache stats
        stats = CacheStats(hit_count=hit_count, miss_count=miss_count)

        # Then: Hit rate should be 0 and not cause division by zero
        assert stats.hit_rate == 0.0
        assert stats.total_requests == 0
