#!/usr/bin/env python3
"""Test URL normalization fix."""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.cache_manager import CacheKey


def test_url_normalization():
    """Test that URL normalization works correctly."""
    print("Testing URL normalization fix...")

    # Test case 1: Same URL with different cases
    url1 = "https://www.instagram.com/p/ABC123/"
    url2 = "https://WWW.INSTAGRAM.COM/P/ABC123/"
    url3 = (
        "HTTPS://www.instagram.com/p/ABC123"  # Different scheme case, no trailing slash
    )

    key1 = CacheKey.link_analysis(url1)
    key2 = CacheKey.link_analysis(url2)
    key3 = CacheKey.link_analysis(url3)

    print(f"✅ Case normalization:")
    print(f"   URL 1: {url1}")
    print(f"   URL 2: {url2}")
    print(f"   URL 3: {url3}")
    print(f"   Key 1: {key1}")
    print(f"   Key 2: {key2}")
    print(f"   Key 3: {key3}")
    print(f"   All keys equal: {key1 == key2 == key3}")

    # Test case 2: URLs with tracking parameters
    url4 = "https://www.instagram.com/p/ABC123/"
    url5 = "https://www.instagram.com/p/ABC123/?utm_source=web&fbclid=123&ref=share"
    url6 = "https://www.instagram.com/p/ABC123?igshid=abc123"

    key4 = CacheKey.link_analysis(url4)
    key5 = CacheKey.link_analysis(url5)
    key6 = CacheKey.link_analysis(url6)

    print(f"\n✅ Tracking parameter removal:")
    print(f"   URL 4: {url4}")
    print(f"   URL 5: {url5}")
    print(f"   URL 6: {url6}")
    print(f"   Key 4: {key4}")
    print(f"   Key 5: {key5}")
    print(f"   Key 6: {key6}")
    print(f"   All keys equal: {key4 == key5 == key6}")

    # Test case 3: Different key types
    metadata_key = CacheKey.metadata_extraction(url1)
    ai_key = CacheKey.ai_analysis(url1)

    print(f"\n✅ Different key types:")
    print(f"   Link key: {key1}")
    print(f"   Metadata key: {metadata_key}")
    print(f"   AI key: {ai_key}")
    print(f"   All different: {len({key1, metadata_key, ai_key}) == 3}")
    print(
        f"   Share same hash suffix: {key1.split(':')[-1] == metadata_key.split(':')[-1] == ai_key.split(':')[-1]}"
    )


if __name__ == "__main__":
    test_url_normalization()
