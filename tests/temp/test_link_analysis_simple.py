#!/usr/bin/env python3
"""
Simple Link Analysis Test

Tests the link analysis functionality without loading the full app.
"""

import asyncio
import sys
from datetime import datetime


# Test link analysis components directly
async def test_link_analysis_components():
    """Test individual link analysis components."""

    print("🚀 Simple Link Analysis Component Tests")
    print("=" * 50)

    # Test 1: Content Extractor
    print("\n1. Testing Content Extractor...")
    try:
        from app.services.content_extractor import ContentExtractor

        extractor = ContentExtractor()
        print("✅ ContentExtractor imported successfully")

        # Test URL platform detection
        valid_urls = [
            "https://instagram.com/p/test123",
            "https://www.instagram.com/p/test456",
            "https://blog.naver.com/test/123",
        ]

        for url in valid_urls:
            try:
                platform = extractor._detect_platform(url)
                print(f"   URL: {url} - Platform: {platform.value}")
            except Exception as e:
                print(f"   URL: {url} - Error: {type(e).__name__}")

    except Exception as e:
        print(f"❌ ContentExtractor test failed: {e}")
        return False

    # Test 2: Cache Manager
    print("\n2. Testing Cache Manager...")
    try:
        from app.services.cache_manager import CacheKey, CacheManager

        CacheManager()
        print("✅ CacheManager imported successfully")

        # Test cache key generation
        test_url = "https://instagram.com/p/test123"
        cache_key = CacheKey.link_analysis(test_url)
        print(f"   Cache key for {test_url}: {cache_key}")

    except Exception as e:
        print(f"❌ CacheManager test failed: {e}")
        return False

    # Test 3: Place Analysis Service
    print("\n3. Testing Place Analysis Service...")
    try:
        from app.services.place_analysis_service import PlaceAnalysisService

        PlaceAnalysisService()
        print("✅ PlaceAnalysisService imported successfully")

    except Exception as e:
        print(f"❌ PlaceAnalysisService test failed: {e}")
        return False

    # Test 4: Link Analysis Schemas
    print("\n4. Testing Link Analysis Schemas...")
    try:
        from app.schemas.link_analysis import AnalysisStatus, LinkAnalyzeRequest

        print("✅ Link analysis schemas imported successfully")

        # Test schema validation
        test_request = LinkAnalyzeRequest(
            url="https://instagram.com/p/test123", force_refresh=False
        )
        print(f"   Test request created: {test_request.url}")

        # Test status enum
        print(f"   Available statuses: {[status.value for status in AnalysisStatus]}")

    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

    # Test 5: AI Analyzer
    print("\n5. Testing AI Analyzer...")
    try:
        from app.services.ai.gemini_analyzer import GeminiAnalyzer

        print("✅ GeminiAnalyzer imported successfully")

        # Test analyzer configuration
        analyzer = GeminiAnalyzer()
        if hasattr(analyzer, "model_name"):
            print(f"   Model: {analyzer.model_name}")

    except Exception as e:
        print(f"❌ AI Analyzer test failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 Component Tests Completed Successfully!")
    return True


async def test_content_extraction_mock():
    """Test content extraction with mock data."""

    print("\n" + "=" * 50)
    print("🧪 Mock Content Extraction Test")
    print("=" * 50)

    try:
        from app.services.content_extractor import ContentExtractor

        extractor = ContentExtractor()

        # Test with a simple URL (this should fail gracefully)
        test_url = "https://example.com/test"

        print(f"\nTesting URL: {test_url}")
        print("Expected: UnsupportedPlatformError (this is correct behavior)")

        try:
            result = await extractor.extract_content(test_url)
            print(f"❌ Expected error but got result: {result}")
            return False
        except Exception as e:
            print(f"✅ Correctly caught exception: {type(e).__name__}")
            return True

    except Exception as e:
        print(f"❌ Mock extraction test failed: {e}")
        return False


def main():
    """Main test runner."""
    print(f"Simple Link Analysis Test")
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        # Run component tests
        success1 = asyncio.run(test_link_analysis_components())

        # Run mock extraction test
        success2 = asyncio.run(test_content_extraction_mock())

        if success1 and success2:
            print("\n✅ All simple tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
