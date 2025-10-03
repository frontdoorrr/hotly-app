#!/usr/bin/env python3
"""Enhanced test script for cache manager with all new features."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.schemas.cache import CacheEntry
from app.services.cache_manager import CacheKey, CacheManager, LRUCache


async def test_enhanced_cache_manager():
    """Test enhanced cache manager functionality."""
    print("Testing Enhanced CacheManager...")

    # Test 1: URL normalization
    print("\n1. Testing URL normalization:")
    try:
        url1 = "https://www.instagram.com/p/ABC123/"
        url2 = "https://www.instagram.com/p/ABC123/?utm_source=web&fbclid=123"
        url3 = "https://WWW.INSTAGRAM.COM/P/ABC123"  # Different case

        key1 = CacheKey.link_analysis(url1)
        key2 = CacheKey.link_analysis(url2)
        key3 = CacheKey.link_analysis(url3)

        print(f"✅ URL normalization:")
        print(f"   Original URL: {url1}")
        print(f"   URL with tracking: {url2}")
        print(f"   Different case: {url3}")
        print(f"   Key 1: {key1}")
        print(f"   Key 2: {key2}")
        print(f"   Key 3: {key3}")
        print(f"   All keys equal: {key1 == key2 == key3}")

    except Exception as e:
        print(f"❌ URL normalization test failed: {e}")

    # Test 2: Different cache key types
    print("\n2. Testing different cache key types:")
    try:
        url = "https://www.instagram.com/p/ABC123/"

        link_key = CacheKey.link_analysis(url)
        metadata_key = CacheKey.metadata_extraction(url)
        ai_key = CacheKey.ai_analysis(url)

        print(f"✅ Cache key types:")
        print(f"   Link analysis: {link_key}")
        print(f"   Metadata: {metadata_key}")
        print(f"   AI analysis: {ai_key}")
        print(f"   All different: {len({link_key, metadata_key, ai_key}) == 3}")

    except Exception as e:
        print(f"❌ Cache key types test failed: {e}")

    # Test 3: LRU Cache functionality
    print("\n3. Testing LRU Cache:")
    try:
        lru = LRUCache(max_size=3)

        # Add items
        lru.set("key1", "value1")
        lru.set("key2", "value2")
        lru.set("key3", "value3")

        print(f"✅ LRU Cache:")
        print(f"   Cache size: {len(lru)}")
        print(f"   Contains key1: {'key1' in lru}")

        # Access key1 to make it recently used
        val1 = lru.get("key1")
        print(f"   Retrieved key1: {val1}")

        # Add key4 which should evict key2 (least recently used)
        lru.set("key4", "value4")
        print(f"   After adding key4, size: {len(lru)}")
        print(f"   Contains key2 (should be evicted): {'key2' in lru}")
        print(f"   Contains key1 (recently used): {'key1' in lru}")

    except Exception as e:
        print(f"❌ LRU Cache test failed: {e}")

    # Test 4: Cache Entry expiration
    print("\n4. Testing cache entry expiration:")
    try:
        from datetime import datetime, timezone

        # Non-expired entry
        entry1 = CacheEntry(
            data={"test": "data"}, ttl=3600, created_at=datetime.now(timezone.utc)
        )

        # Expired entry
        import time

        entry2 = CacheEntry(
            data={"test": "data"}, ttl=1, created_at=datetime.now(timezone.utc)
        )
        time.sleep(2)  # Wait for expiration

        print(f"✅ Cache entry expiration:")
        print(f"   Entry 1 expired: {entry1.is_expired()}")
        print(f"   Entry 2 expired: {entry2.is_expired()}")

    except Exception as e:
        print(f"❌ Cache entry expiration test failed: {e}")

    # Test 5: Enhanced cache manager (without Redis)
    print("\n5. Testing enhanced cache manager (local only):")
    try:
        cache_manager = CacheManager(local_cache_max_size=5)

        # Test set/get operations
        key = CacheKey.link_analysis("https://test.com")
        data = {"places": [{"name": "Test Place"}]}

        # This will fail Redis connection but should work with local cache
        await cache_manager.set(key, data, 3600)
        result = await cache_manager.get(key)

        print(f"✅ Enhanced cache manager:")
        print(f"   Set data: {data}")
        print(f"   Retrieved data: {result}")
        print(f"   Data matches: {data == result}")

        # Test cache stats
        stats = await cache_manager.get_stats()
        print(f"   Cache hits: {stats.cache_hits}")
        print(f"   Total requests: {stats.total_requests}")
        print(f"   Hit rate: {stats.hit_rate:.2f}")

    except Exception as e:
        print(f"❌ Enhanced cache manager test failed: {e}")

    # Test 6: Multiple cache operations for hit rate testing
    print("\n6. Testing cache hit rate:")
    try:
        cache_manager = CacheManager(local_cache_max_size=10)

        # Populate cache with some data
        urls = [f"https://example{i}.com" for i in range(5)]
        data = {"test": "data"}

        # Set cache entries
        for url in urls:
            key = CacheKey.link_analysis(url)
            await cache_manager.set(key, data, 3600)

        # Mix of hits and misses
        hit_urls = urls[:3]  # First 3 should be hits
        miss_urls = [
            f"https://missing{i}.com" for i in range(2)
        ]  # These should be misses

        # Perform gets
        for url in hit_urls:
            key = CacheKey.link_analysis(url)
            result = await cache_manager.get(key)
            assert result is not None

        for url in miss_urls:
            key = CacheKey.link_analysis(url)
            result = await cache_manager.get(key)
            assert result is None

        stats = await cache_manager.get_stats()
        print(f"✅ Cache hit rate test:")
        print(f"   Total requests: {stats.total_requests}")
        print(f"   Cache hits: {stats.cache_hits}")
        print(f"   Cache misses: {stats.cache_misses}")
        print(f"   Hit rate: {stats.hit_rate:.2f}")
        print(f"   Meets 40% requirement: {stats.hit_rate >= 0.4}")

    except Exception as e:
        print(f"❌ Cache hit rate test failed: {e}")

    # Test 7: Performance test
    print("\n7. Testing cache performance:")
    try:
        cache_manager = CacheManager(local_cache_max_size=100)

        # Performance test with 50 operations
        urls = [f"https://perf{i}.com" for i in range(50)]
        data = {"performance": "test", "large_data": ["item"] * 100}

        # Set operations
        start_time = time.time()
        for url in urls:
            key = CacheKey.link_analysis(url)
            await cache_manager.set(key, data, 3600)
        set_time = time.time() - start_time

        # Get operations (should be fast from local cache)
        start_time = time.time()
        for url in urls:
            key = CacheKey.link_analysis(url)
            result = await cache_manager.get(key)
            assert result is not None
        get_time = time.time() - start_time

        print(f"✅ Cache performance:")
        print(
            f"   50 set operations: {set_time:.3f}s ({set_time/50*1000:.1f}ms per op)"
        )
        print(
            f"   50 get operations: {get_time:.3f}s ({get_time/50*1000:.1f}ms per op)"
        )
        print(f"   Set performance OK: {set_time < 1.0}")  # Should be under 1 second
        print(f"   Get performance OK: {get_time < 0.5}")  # Should be under 0.5 seconds

    except Exception as e:
        print(f"❌ Cache performance test failed: {e}")

    print("\n🎉 All enhanced cache manager tests completed!")


if __name__ == "__main__":
    asyncio.run(test_enhanced_cache_manager())
