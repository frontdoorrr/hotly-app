"""
Simple tests for cache manager.

Basic functionality tests to improve coverage.
"""


class TestCacheManager:
    """Test cache manager basic operations."""

    def test_set_and_get_returnsValue(self):
        """Test setting and getting a cached value."""
        from app.services.monitoring.cache_manager import CacheManager

        cache = CacheManager()
        key = "test_key"
        value = {"data": "test_value"}

        # Set value
        cache.set(key, value, ttl=60)

        # Get value
        result = cache.get(key)

        assert result == value

    def test_get_nonexistentKey_returnsNone(self):
        """Test getting a non-existent key returns None."""
        from app.services.monitoring.cache_manager import CacheManager

        cache = CacheManager()
        result = cache.get("nonexistent_key")

        assert result is None

    def test_delete_existingKey_removesValue(self):
        """Test deleting a key removes it from cache."""
        from app.services.monitoring.cache_manager import CacheManager

        cache = CacheManager()
        key = "test_key"
        value = "test_value"

        cache.set(key, value)
        cache.delete(key)

        result = cache.get(key)
        assert result is None
