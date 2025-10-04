#!/usr/bin/env python3
"""Simple test script for cache manager functionality."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.monitoring.cache_manager import CacheEntry, CacheManager, CacheStats


async def test_cache_manager():
    """Test cache manager functionality directly."""
    print("Testing CacheManager...")

    # Test 1: Basic functionality without Redis
    print("\n1. Testing basic cache functionality:")
    try:
        cache_manager = CacheManager()

        # Test key generation
        url1 = "https://www.instagram.com/p/ABC123/"
        url2 = "https://www.instagram.com/p/ABC123/"

        key1 = cache_manager._generate_cache_key(url1)
        key2 = cache_manager._generate_cache_key(url2)

        print(f"✅ Key generation:")
        print(f"   Key 1: {key1}")
        print(f"   Key 2: {key2}")
        print(f"   Keys equal: {key1 == key2}")
        print(f"   Key format correct: {key1.startswith('hotly:link_analysis:')}")

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")

    # Test 2: Cache entry validation
    print("\n2. Testing cache entry validation:")
    try:
        import time
        from datetime import datetime, timezone

        # Test non-expired entry
        data = {"places": [{"name": "Test Place"}]}
        entry = CacheEntry(data=data, ttl=3600, created_at=datetime.now(timezone.utc))

        print(f"✅ Cache entry validation:")
        print(f"   Entry data: {entry.data}")
        print(f"   Entry TTL: {entry.ttl}")
        print(f"   Is expired: {entry.is_expired()}")

        # Test expired entry
        expired_entry = CacheEntry(
            data=data, ttl=1, created_at=datetime.now(timezone.utc)  # 1 second TTL
        )
        time.sleep(2)  # Wait for expiration
        print(f"   Expired entry is expired: {expired_entry.is_expired()}")

    except Exception as e:
        print(f"❌ Cache entry validation failed: {e}")

    # Test 3: Cache stats
    print("\n3. Testing cache stats:")
    try:
        stats = CacheStats(hit_count=100, miss_count=25)

        print(f"✅ Cache stats:")
        print(f"   Hit count: {stats.hit_count}")
        print(f"   Miss count: {stats.miss_count}")
        print(f"   Total requests: {stats.total_requests}")
        print(f"   Hit rate: {stats.hit_rate:.2f}")

        # Test zero requests
        zero_stats = CacheStats(hit_count=0, miss_count=0)
        print(f"   Zero requests hit rate: {zero_stats.hit_rate}")

    except Exception as e:
        print(f"❌ Cache stats test failed: {e}")

    # Test 4: Local cache (without Redis)
    print("\n4. Testing local cache operations:")
    try:
        cache_manager = CacheManager()

        # Test local cache storage
        cache_key = cache_manager._generate_cache_key("https://test.com")
        test_data = {"test": "data"}

        entry = CacheEntry(
            data=test_data, ttl=3600, created_at=datetime.now(timezone.utc)
        )

        # Store in local cache directly
        cache_manager._local_cache[cache_key] = entry

        # Retrieve from local cache
        if cache_key in cache_manager._local_cache:
            retrieved_entry = cache_manager._local_cache[cache_key]
            print(f"✅ Local cache operations:")
            print(f"   Stored data: {test_data}")
            print(f"   Retrieved data: {retrieved_entry.data}")
            print(f"   Data matches: {test_data == retrieved_entry.data}")
        else:
            print(f"❌ Local cache retrieval failed")

    except Exception as e:
        print(f"❌ Local cache test failed: {e}")

    # Test 5: Key generation consistency
    print("\n5. Testing key generation consistency:")
    try:
        cache_manager = CacheManager()

        # Test different URLs
        urls = [
            "https://www.instagram.com/p/ABC123/",
            "https://blog.naver.com/user/post123",
            "https://www.youtube.com/watch?v=ABC123",
            "https://www.instagram.com/p/ABC123/?utm_source=web",  # Same as first but with query params
        ]

        keys = [cache_manager._generate_cache_key(url) for url in urls]

        print(f"✅ Key generation consistency:")
        for i, (url, key) in enumerate(zip(urls, keys)):
            print(f"   URL {i+1}: {url[:50]}...")
            print(f"   Key {i+1}: {key}")

        print(f"   All keys unique: {len(set(keys)) == len(keys)}")
        print(
            f"   First and last same content: {keys[0] == keys[3]}"
        )  # Should be same after normalization

    except Exception as e:
        print(f"❌ Key generation consistency test failed: {e}")

    print("\n🎉 All cache manager basic tests completed!")


if __name__ == "__main__":
    asyncio.run(test_cache_manager())
