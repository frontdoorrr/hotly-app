#!/usr/bin/env python3
"""
Phase 1 Integration Test Script

테스트할 기능:
1. 플랫폼 자동 감지
2. YouTube 비디오 ID 추출
3. 모듈 import 검증
4. 기본 데이터 구조 검증

실제 API 호출 없이 기본 기능만 테스트합니다.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.platform.base import PlatformExtractor, Platform, ContentType
from app.services.platform.youtube import YouTubeExtractor
from app.services.platform.instagram import InstagramExtractor
from app.services.platform.tiktok import TikTokExtractor
from app.services.analysis.gemini_video import GeminiVideoAnalyzer
from app.services.analysis.gemini_image import GeminiImageAnalyzer
from app.services.analysis.content_classifier import ContentClassifier
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    Platform as SchemaPlatform,
    ContentType as SchemaContentType,
)


def test_imports():
    """Test all modules can be imported."""
    print("✅ All modules imported successfully")
    return True


def test_platform_detection():
    """Test platform auto-detection."""
    print("\n📌 Testing Platform Detection...")

    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", Platform.YOUTUBE),
        ("https://youtu.be/abc123", Platform.YOUTUBE),
        ("https://www.youtube.com/shorts/xyz789", Platform.YOUTUBE),
        ("https://www.instagram.com/p/abc123/", Platform.INSTAGRAM),
        ("https://www.tiktok.com/@user/video/123", Platform.TIKTOK),
        ("https://twitter.com/status/123", None),
    ]

    for url, expected in test_cases:
        result = PlatformExtractor.detect_platform(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {url[:50]}... → {result}")
        if result != expected:
            print(f"     Expected: {expected}, Got: {result}")
            return False

    return True


def test_youtube_video_id_extraction():
    """Test YouTube video ID extraction."""
    print("\n📌 Testing YouTube Video ID Extraction...")

    extractor = YouTubeExtractor(api_key="test_key")

    test_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/abc123", "abc123"),
        ("https://www.youtube.com/shorts/xyz789", "xyz789"),
    ]

    for url, expected_id in test_cases:
        try:
            video_id = extractor._extract_video_id(url)
            status = "✅" if video_id == expected_id else "❌"
            print(f"  {status} {url} → {video_id}")
            if video_id != expected_id:
                print(f"     Expected: {expected_id}, Got: {video_id}")
                return False
        except Exception as e:
            print(f"  ❌ {url} → Error: {e}")
            return False

    return True


def test_youtube_shorts_detection():
    """Test YouTube Shorts detection."""
    print("\n📌 Testing YouTube Shorts Detection...")

    test_cases = [
        ("https://www.youtube.com/shorts/abc123", True),
        ("https://www.youtube.com/watch?v=abc123", False),
        ("https://youtu.be/abc123", False),
    ]

    for url, expected in test_cases:
        result = YouTubeExtractor.is_shorts(url)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {url} → Shorts: {result}")
        if result != expected:
            return False

    return True


def test_schema_validation():
    """Test Pydantic schemas."""
    print("\n📌 Testing Pydantic Schemas...")

    try:
        # Test AnalysisRequest
        request = AnalysisRequest(
            url="https://www.youtube.com/watch?v=test123"
        )
        print(f"  ✅ AnalysisRequest: {request.url}")

        # Test enum compatibility
        assert SchemaPlatform.YOUTUBE == "youtube"
        assert SchemaContentType.VIDEO == "video"
        print("  ✅ Enum values match")

        return True

    except Exception as e:
        print(f"  ❌ Schema validation failed: {e}")
        return False


def test_service_initialization():
    """Test service classes can be initialized."""
    print("\n📌 Testing Service Initialization...")

    try:
        # Platform extractors
        youtube = YouTubeExtractor(api_key="test")
        print("  ✅ YouTubeExtractor initialized")

        instagram = InstagramExtractor(download_dir="temp")
        print("  ✅ InstagramExtractor initialized")

        tiktok = TikTokExtractor(download_dir="temp")
        print("  ✅ TikTokExtractor initialized")

        # Gemini analyzers
        video_analyzer = GeminiVideoAnalyzer(api_key="test")
        print("  ✅ GeminiVideoAnalyzer initialized")

        image_analyzer = GeminiImageAnalyzer(api_key="test")
        print("  ✅ GeminiImageAnalyzer initialized")

        classifier = ContentClassifier(api_key="test")
        print("  ✅ ContentClassifier initialized")

        return True

    except Exception as e:
        print(f"  ❌ Service initialization failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Phase 1 Integration Test")
    print("=" * 60)

    tests = [
        ("Module Imports", test_imports),
        ("Platform Detection", test_platform_detection),
        ("YouTube Video ID Extraction", test_youtube_video_id_extraction),
        ("YouTube Shorts Detection", test_youtube_shorts_detection),
        ("Pydantic Schema Validation", test_schema_validation),
        ("Service Initialization", test_service_initialization),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 1 tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
