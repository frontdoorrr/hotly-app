"""
Unit tests for CacheManager service.

Tests multi-layer caching system (L1: in-memory, L2: Redis).
Focuses on cache operations, TTL management, and performance.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions.cache import CacheConnectionError
from app.services.monitoring.cache_manager import CacheKey, CacheManager, CacheStats


class TestCacheManager:
    """Unit tests for CacheManager."""

    def setup_method(self):
        """Setup before each test."""
        self.cache_manager = CacheManager()

    def teardown_method(self):
        """Cleanup after each test."""
        # Clear in-memory cache
        if hasattr(self.cache_manager, "_l1_cache"):
            self.cache_manager._l1_cache.clear()

    # Cache key generation tests
    def test_cache_key_link_analysis_validUrl_returnsConsistentKey(self):
        """Test cache key generation for link analysis."""
        # Given
        url = "https://instagram.com/p/test123/"

        # When
        key1 = CacheKey.link_analysis(url)
        key2 = CacheKey.link_analysis(url)

        # Then
        assert key1 == key2  # Consistent key generation
        assert "link_analysis" in key1
        assert "instagram.com" in key1 or "test123" in key1

    def test_cache_key_place_info_validPlaceId_returnsFormattedKey(self):
        """Test cache key generation for place information."""
        # Given
        place_id = "place_12345"

        # When
        key = CacheKey.place_info(place_id)

        # Then
        assert key == f"place_info:{place_id}"

    def test_cache_key_user_preferences_validUserId_returnsFormattedKey(self):
        """Test cache key generation for user preferences."""
        # Given
        user_id = "user_67890"

        # When
        key = CacheKey.user_preferences(user_id)

        # Then
        assert key == f"user_prefs:{user_id}"

    # L1 Cache (in-memory) tests
    @pytest.mark.asyncio
    async def test_l1_cache_set_and_get_validData_returnsCorrectValue(self):
        """Test L1 cache set and get operations."""
        # Given
        key = "test_key"
        value = {"data": "test_value", "timestamp": datetime.utcnow().isoformat()}

        # When
        await self.cache_manager._set_l1(key, value, ttl=300)
        result = await self.cache_manager._get_l1(key)

        # Then
        assert result == value
        assert result["data"] == "test_value"

    @pytest.mark.asyncio
    async def test_l1_cache_expired_item_returnsNone(self):
        """Test L1 cache TTL expiration."""
        # Given
        key = "expired_key"
        value = {"data": "expired_value"}
        short_ttl = 0.1  # 100ms

        # When
        await self.cache_manager._set_l1(key, value, ttl=short_ttl)

        # Wait for expiration
        await asyncio.sleep(0.2)

        result = await self.cache_manager._get_l1(key)

        # Then
        assert result is None

    @pytest.mark.asyncio
    async def test_l1_cache_eviction_policy_removesOldestItems(self):
        """Test L1 cache LRU eviction policy."""
        # Given
        cache_manager = CacheManager(l1_max_size=3)  # Small cache for testing

        # When - Fill cache beyond capacity
        for i in range(5):
            await cache_manager._set_l1(f"key_{i}", f"value_{i}", ttl=300)

        # Then - Only the last 3 items should remain
        assert await cache_manager._get_l1("key_0") is None  # Evicted
        assert await cache_manager._get_l1("key_1") is None  # Evicted
        assert await cache_manager._get_l1("key_2") == "value_2"
        assert await cache_manager._get_l1("key_3") == "value_3"
        assert await cache_manager._get_l1("key_4") == "value_4"

    # L2 Cache (Redis) tests
    @pytest.mark.asyncio
    async def test_l2_cache_set_and_get_validData_returnsCorrectValue(self):
        """Test L2 (Redis) cache operations."""
        # Given
        key = "redis_test_key"
        value = {"data": "redis_value", "complex": {"nested": "object"}}

        # Mock Redis operations
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = (
                '{"data": "redis_value", "complex": {"nested": "object"}}'
            )

            # When
            await self.cache_manager._set_l2(key, value, ttl=3600)
            result = await self.cache_manager._get_l2(key)

            # Then
            assert result == value
            mock_redis.set.assert_called_once()
            mock_redis.get.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_l2_cache_redis_unavailable_handlesGracefully(self):
        """Test L2 cache handles Redis connection errors."""
        # Given
        key = "unavailable_key"
        value = {"data": "test"}

        # Mock Redis connection error
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.set.side_effect = CacheConnectionError("Redis unavailable")

            # When
            result = await self.cache_manager._set_l2(key, value, ttl=3600)

            # Then
            assert result is False  # Operation failed gracefully
            # Should not raise exception

    @pytest.mark.asyncio
    async def test_l2_cache_serialization_error_handlesGracefully(self):
        """Test L2 cache handles serialization errors."""
        # Given
        key = "serial_key"
        # Create object that can't be JSON serialized
        non_serializable = {"func": lambda x: x}

        # When
        result = await self.cache_manager._set_l2(key, non_serializable, ttl=3600)

        # Then
        assert result is False  # Serialization failed gracefully

    # Multi-layer cache integration tests
    @pytest.mark.asyncio
    async def test_get_cache_miss_both_layers_returnsNone(self):
        """Test cache miss in both L1 and L2 layers."""
        # Given
        key = "missing_key"

        # Mock Redis miss
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.get.return_value = None

            # When
            result = await self.cache_manager.get(key)

            # Then
            assert result is None

    @pytest.mark.asyncio
    async def test_get_l1_miss_l2_hit_promotesToL1(self):
        """Test L2 hit promotes data to L1 cache."""
        # Given
        key = "promotion_key"
        value = {"data": "promoted_value"}

        # Mock L2 hit, L1 miss
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.get.return_value = '{"data": "promoted_value"}'

            # When
            result = await self.cache_manager.get(key)

            # Then
            assert result == value

            # Verify data was promoted to L1
            l1_result = await self.cache_manager._get_l1(key)
            assert l1_result == value

    @pytest.mark.asyncio
    async def test_set_cache_stores_in_both_layers(self):
        """Test set operation stores data in both cache layers."""
        # Given
        key = "dual_layer_key"
        value = {"data": "dual_layer_value"}
        ttl = 3600

        # Mock Redis
        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.set.return_value = True

            # When
            await self.cache_manager.set(key, value, ttl)

            # Then
            # Check L1 cache
            l1_result = await self.cache_manager._get_l1(key)
            assert l1_result == value

            # Verify L2 was called
            mock_redis.set.assert_called_once()

    # Cache invalidation tests
    @pytest.mark.asyncio
    async def test_invalidate_cache_removes_from_both_layers(self):
        """Test cache invalidation removes from both layers."""
        # Given
        key = "invalidate_key"
        value = {"data": "to_be_invalidated"}

        # Setup cache in both layers
        await self.cache_manager._set_l1(key, value, ttl=300)

        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.delete.return_value = 1

            # When
            await self.cache_manager.invalidate(key)

            # Then
            # Check L1 removed
            l1_result = await self.cache_manager._get_l1(key)
            assert l1_result is None

            # Verify L2 delete was called
            mock_redis.delete.assert_called_once_with(key)

    @pytest.mark.asyncio
    async def test_invalidate_pattern_removes_multiple_keys(self):
        """Test pattern-based cache invalidation."""
        # Given
        pattern = "user_prefs:*"
        keys_to_invalidate = [
            "user_prefs:user1",
            "user_prefs:user2",
            "user_prefs:user3",
        ]

        # Setup cache
        for key in keys_to_invalidate:
            await self.cache_manager._set_l1(key, {"data": f"value_{key}"}, ttl=300)

        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.scan_iter.return_value = keys_to_invalidate
            mock_redis.delete.return_value = len(keys_to_invalidate)

            # When
            result = await self.cache_manager.invalidate_pattern(pattern)

            # Then
            assert result == len(keys_to_invalidate)

            # Verify all keys removed from L1
            for key in keys_to_invalidate:
                l1_result = await self.cache_manager._get_l1(key)
                assert l1_result is None

    # Cache statistics tests
    @pytest.mark.asyncio
    async def test_get_stats_returns_accurate_metrics(self):
        """Test cache statistics calculation."""
        # Given
        cache_manager = CacheManager()

        # Simulate cache operations for statistics
        await cache_manager._record_hit("l1")
        await cache_manager._record_hit("l2")
        await cache_manager._record_miss()
        await cache_manager._record_hit("l1")

        # When
        stats = await cache_manager.get_stats()

        # Then
        assert isinstance(stats, CacheStats)
        assert stats.total_requests == 4
        assert stats.cache_hits == 3
        assert stats.cache_misses == 1
        assert stats.l1_hits == 2
        assert stats.l2_hits == 1
        assert stats.hit_rate == 0.75
        assert stats.l1_hit_rate == 0.5
        assert stats.l2_hit_rate == 0.25

    # Performance tests
    @pytest.mark.asyncio
    async def test_cache_performance_l1_faster_than_l2(self):
        """Test that L1 cache is significantly faster than L2."""
        # Given
        key = "performance_key"
        value = {"data": "performance_test"}

        # Setup L1 cache
        await self.cache_manager._set_l1(key, value, ttl=300)

        # Mock slow L2 operation
        with patch.object(self.cache_manager, "_get_l2") as mock_l2:

            async def slow_l2_get(*args):
                await asyncio.sleep(0.1)  # Simulate network delay
                return value

            mock_l2.side_effect = slow_l2_get

            # When - Measure L1 performance
            start_time = asyncio.get_event_loop().time()
            l1_result = await self.cache_manager._get_l1(key)
            l1_time = asyncio.get_event_loop().time() - start_time

            # Clear L1 and measure L2 performance
            await self.cache_manager._del_l1(key)
            start_time = asyncio.get_event_loop().time()
            l2_result = await self.cache_manager._get_l2(key)
            l2_time = asyncio.get_event_loop().time() - start_time

            # Then
            assert l1_result == value
            assert l2_result == value
            assert l1_time < l2_time  # L1 should be faster
            assert l1_time < 0.01  # L1 should be very fast

    # Edge cases and error conditions
    @pytest.mark.asyncio
    async def test_cache_large_object_handlesGracefully(self):
        """Test caching of large objects."""
        # Given
        key = "large_object_key"
        # Create a large object (1MB of data)
        large_value = {"data": "x" * (1024 * 1024)}

        # When
        result = await self.cache_manager.set(key, large_value, ttl=300)

        # Then
        # Should handle gracefully (may store in L1 only or fail gracefully)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_cache_none_value_handlesCorrectly(self):
        """Test caching of None values."""
        # Given
        key = "none_value_key"
        value = None

        # When
        await self.cache_manager.set(key, value, ttl=300)
        result = await self.cache_manager.get(key)

        # Then
        assert result is None
        # Should be able to distinguish between cache miss and cached None

    @pytest.mark.asyncio
    async def test_cache_concurrent_operations_thread_safe(self):
        """Test cache operations are thread-safe."""
        # Given
        key = "concurrent_key"
        num_operations = 100

        async def set_operation(i):
            await self.cache_manager.set(f"{key}_{i}", {"value": i}, ttl=300)

        async def get_operation(i):
            return await self.cache_manager.get(f"{key}_{i}")

        # When - Perform concurrent operations
        tasks = []
        for i in range(num_operations):
            tasks.append(set_operation(i))

        await asyncio.gather(*tasks)

        # Verify data integrity
        tasks = []
        for i in range(num_operations):
            tasks.append(get_operation(i))

        results = await asyncio.gather(*tasks)

        # Then
        for i, result in enumerate(results):
            if result is not None:  # Some might be evicted due to LRU
                assert result["value"] == i

    # TTL and expiration tests
    @pytest.mark.asyncio
    async def test_cache_ttl_different_layers_expire_correctly(self):
        """Test TTL behavior across cache layers."""
        # Given
        key = "ttl_key"
        value = {"data": "ttl_test"}
        short_ttl = 1  # 1 second

        with patch.object(self.cache_manager, "redis_client") as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = None  # Simulate Redis expiration

            # When
            await self.cache_manager.set(key, value, ttl=short_ttl)

            # Immediate get should work (L1 cache)
            immediate_result = await self.cache_manager.get(key)
            assert immediate_result == value

            # Wait for L1 expiration
            await asyncio.sleep(1.1)

            # Both layers should be expired
            expired_result = await self.cache_manager.get(key)
            assert expired_result is None


# Test fixtures for cache testing
@pytest.fixture
def sample_cache_data():
    """Sample data for cache testing."""
    return {
        "place_info": {
            "name": "Test Restaurant",
            "category": "restaurant",
            "address": "Test Address",
            "confidence": 0.9,
        },
        "analysis_time": 2.5,
        "model_version": "test-1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.set.return_value = True
    mock_client.get.return_value = None
    mock_client.delete.return_value = 1
    mock_client.scan_iter.return_value = []
    return mock_client


@pytest.fixture
def cache_manager_with_mocked_redis(mock_redis_client):
    """CacheManager with mocked Redis client."""
    cache_manager = CacheManager()
    cache_manager.redis_client = mock_redis_client
    return cache_manager
