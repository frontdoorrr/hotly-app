#!/usr/bin/env python3
"""Simple test script for content extractor."""

import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.places.content_extractor import ContentExtractor


async def test_content_extractor():
    """Test content extractor functionality."""
    print("Testing ContentExtractor...")

    extractor = ContentExtractor()

    # Test platform detection
    print("\n1. Testing platform detection:")
    try:
        instagram_platform = extractor._detect_platform(
            "https://www.instagram.com/p/ABC123/"
        )
        print(f"✅ Instagram detected: {instagram_platform}")

        naver_platform = extractor._detect_platform("https://blog.naver.com/user/post")
        print(f"✅ Naver Blog detected: {naver_platform}")

        youtube_platform = extractor._detect_platform(
            "https://www.youtube.com/watch?v=ABC123"
        )
        print(f"✅ YouTube detected: {youtube_platform}")

        try:
            extractor._detect_platform("https://unsupported.com/post")
            print("❌ Should have raised UnsupportedPlatformError")
        except Exception as e:
            print(f"✅ Unsupported platform correctly rejected: {type(e).__name__}")

    except Exception as e:
        print(f"❌ Platform detection failed: {e}")

    # Test content extraction
    print("\n2. Testing content extraction:")
    try:
        test_urls = [
            "https://www.instagram.com/p/ABC123/",
            "https://blog.naver.com/user/post",
            "https://www.youtube.com/watch?v=ABC123",
        ]

        for url in test_urls:
            result = await extractor.extract_content(url)
            print(f"✅ Extracted from {result.platform.value}:")
            print(f"   Title: {result.metadata.title}")
            print(f"   Description: {result.metadata.description[:50]}...")
            print(f"   Images: {len(result.metadata.images)} found")
            print(f"   Hashtags: {len(result.metadata.hashtags)} found")
            print(f"   Extraction time: {result.extraction_time:.3f}s")

    except Exception as e:
        print(f"❌ Content extraction failed: {e}")

    # Test concurrent extraction
    print("\n3. Testing concurrent extraction:")
    try:
        urls = [
            "https://www.instagram.com/p/TEST1/",
            "https://blog.naver.com/user1/post1",
            "https://www.youtube.com/watch?v=TEST2",
        ]

        import time

        start_time = time.time()

        tasks = [extractor.extract_content(url) for url in urls]
        results = await asyncio.gather(*tasks)

        duration = time.time() - start_time
        print(f"✅ Processed {len(results)} URLs in {duration:.3f}s")

        for result in results:
            print(f"   {result.platform.value}: {result.extraction_time:.3f}s")

    except Exception as e:
        print(f"❌ Concurrent extraction failed: {e}")

    print("\n🎉 All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_content_extractor())
