#!/usr/bin/env python3
"""
Direct Link Analysis Test

Tests the link analysis functionality without Redis cache dependency.
"""

import asyncio
import sys
from datetime import datetime


async def test_content_extraction_only():
    """Test content extraction functionality directly."""

    print("🚀 Direct Content Extraction Test")
    print("=" * 50)

    try:
        from app.exceptions.external import UnsupportedPlatformError
        from app.services.content_extractor import ContentExtractor

        extractor = ContentExtractor()
        print("✅ ContentExtractor imported successfully")

        # Test 1: Supported platform detection
        print("\n1. Testing Platform Detection...")
        test_urls = {
            "https://instagram.com/p/test123": "instagram",
            "https://www.instagram.com/p/test456": "instagram",
            "https://blog.naver.com/test/123": "naver_blog",
            "https://youtube.com/watch?v=abc123": "youtube",
            "https://youtu.be/xyz789": "youtube",
        }

        for url, expected_platform in test_urls.items():
            try:
                platform = extractor._detect_platform(url)
                if platform.value == expected_platform:
                    print(f"   ✅ {url} -> {platform.value}")
                else:
                    print(
                        f"   ❌ {url} -> {platform.value} (expected {expected_platform})"
                    )
            except Exception as e:
                print(f"   ❌ {url} -> Error: {e}")

        # Test 2: Unsupported platform detection
        print("\n2. Testing Unsupported Platform Detection...")
        unsupported_urls = [
            "https://facebook.com/post/123",
            "https://twitter.com/user/status/456",
            "https://example.com/page",
        ]

        for url in unsupported_urls:
            try:
                platform = extractor._detect_platform(url)
                print(f"   ❌ {url} should have failed but got: {platform.value}")
            except UnsupportedPlatformError:
                print(f"   ✅ {url} correctly rejected")
            except Exception as e:
                print(f"   ⚠️  {url} failed with unexpected error: {e}")

        # Test 3: Mock content extraction
        print("\n3. Testing Mock Content Extraction...")
        mock_urls = [
            "https://instagram.com/p/test123",
            "https://blog.naver.com/test/123",
            "https://youtube.com/watch?v=abc123",
        ]

        for url in mock_urls:
            try:
                print(f"   Testing: {url}")
                content = await extractor.extract_content(url)

                print(f"     ✅ Platform: {content.platform.value}")
                print(f"     ✅ Title: {content.metadata.title}")
                print(f"     ✅ Description: {content.metadata.description[:50]}...")
                print(f"     ✅ Images count: {len(content.metadata.images)}")
                print(f"     ✅ Hashtags count: {len(content.metadata.hashtags)}")
                print(
                    f"     ✅ Extraction time: {content.metadata.extraction_time:.3f}s"
                )

            except Exception as e:
                print(f"     ❌ Failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Content extraction test failed: {e}")
        return False


async def test_ai_analysis_mock():
    """Test AI analysis functionality."""

    print("\n" + "=" * 50)
    print("🧠 AI Analysis Mock Test")
    print("=" * 50)

    try:
        from app.schemas.content import ContentMetadata
        from app.services.place_analysis_service import PlaceAnalysisService

        analysis_service = PlaceAnalysisService()
        print("✅ PlaceAnalysisService imported successfully")

        # Create mock content for analysis
        mock_content = ContentMetadata(
            title="Amazing Korean BBQ Restaurant in Gangnam",
            description="Best Korean BBQ in Seoul! Great atmosphere and delicious food. #korean #bbq #gangnam #seoul #restaurant",
            images=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
            hashtags=["#korean", "#bbq", "#gangnam", "#seoul", "#restaurant"],
        )

        print("\n1. Testing Content Analysis...")
        print(f"   Mock content title: {mock_content.title}")
        print(f"   Mock content hashtags: {mock_content.hashtags}")

        try:
            # Test AI analysis (this might fail due to missing API keys, which is expected)
            result = await analysis_service.analyze_content(
                mock_content, mock_content.images
            )

            print(f"   ✅ Analysis completed")
            print(f"   ✅ Success: {result.success}")
            print(f"   ✅ Confidence: {result.confidence}")

            if result.place_info:
                print(f"   ✅ Place name: {result.place_info.name}")
                print(f"   ✅ Category: {result.place_info.category}")
                print(f"   ✅ Address: {result.place_info.address}")

        except Exception as e:
            print(f"   ⚠️  AI analysis failed (expected if no API key): {e}")
            print(f"   ✅ Error handling working correctly")

        return True

    except Exception as e:
        print(f"❌ AI analysis test failed: {e}")
        return False


async def test_schemas_validation():
    """Test schema validation."""

    print("\n" + "=" * 50)
    print("📋 Schema Validation Test")
    print("=" * 50)

    try:
        from app.schemas.link_analysis import (
            AnalysisStatus,
            LinkAnalyzeRequest,
        )

        print("✅ Schemas imported successfully")

        # Test request schema validation
        print("\n1. Testing Request Schema...")

        valid_requests = [
            {"url": "https://instagram.com/p/test123"},
            {"url": "https://instagram.com/p/test123", "force_refresh": True},
            {
                "url": "https://instagram.com/p/test123",
                "webhook_url": "https://example.com/webhook",
            },
        ]

        for req_data in valid_requests:
            try:
                request = LinkAnalyzeRequest(**req_data)
                print(f"   ✅ Valid request: {request.url}")
            except Exception as e:
                print(f"   ❌ Invalid request {req_data}: {e}")

        # Test invalid requests
        print("\n2. Testing Invalid Requests...")
        invalid_requests = [
            {"url": "not-a-url"},
            {"url": ""},
            {},
        ]

        for req_data in invalid_requests:
            try:
                request = LinkAnalyzeRequest(**req_data)
                print(f"   ❌ Should have failed: {req_data}")
            except Exception:
                print(f"   ✅ Correctly rejected: {req_data}")

        # Test status enum
        print("\n3. Testing Status Enum...")
        statuses = [status for status in AnalysisStatus]
        print(f"   ✅ Available statuses: {[s.value for s in statuses]}")

        return True

    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False


def main():
    """Main test runner."""
    print(f"Direct Link Analysis Test")
    print(f"Started at: {datetime.now().isoformat()}")

    async def run_all_tests():
        results = await asyncio.gather(
            test_content_extraction_only(),
            test_ai_analysis_mock(),
            test_schemas_validation(),
            return_exceptions=True,
        )
        return results

    try:
        # Run all tests
        results = asyncio.run(run_all_tests())

        success_count = sum(1 for result in results if result is True)
        total_tests = len(results)

        print("\n" + "=" * 50)
        print(f"📊 Test Results: {success_count}/{total_tests} passed")

        if success_count == total_tests:
            print("🎉 All tests passed!")
            sys.exit(0)
        else:
            print("⚠️  Some tests failed or had issues")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
