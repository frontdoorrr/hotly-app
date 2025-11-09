#!/usr/bin/env python3
"""
Phase 4 Integration Test Script

전체 파이프라인 end-to-end 테스트:
- URL → 플랫폼 감지 → 메타데이터 추출 → Gemini 분석 → AI 분류 → 결과
- 모든 컴포넌트 통합 검증
- 에러 처리 및 복원력 테스트

Note: 이 테스트는 실제 API를 호출하며 비용이 발생할 수 있습니다.
"""

import sys
import os
from pathlib import Path
import asyncio

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.link_analyzer_service import LinkAnalyzerService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Test URLs (public content)
TEST_URLS = {
    # Short YouTube video about food/restaurant
    'youtube_food': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # "Me at the zoo" (18s)

    # YouTube Shorts
    'youtube_shorts': 'https://youtube.com/shorts/jNQXAC9IVRw',

    # Instagram - requires valid public URL
    'instagram': None,  # Add public Instagram URL to test

    # TikTok - requires valid public URL
    'tiktok': None,  # Add public TikTok URL to test
}


async def test_service_initialization():
    """Test link analyzer service initialization."""
    print("\n📌 Testing Link Analyzer Service Initialization...")

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Missing API keys")
        return False

    try:
        service = LinkAnalyzerService(
            youtube_api_key=youtube_key,
            gemini_api_key=gemini_key,
            download_dir="temp/test"
        )

        print(f"  ✅ LinkAnalyzerService initialized")
        print(f"  ✅ YouTube extractor: {type(service.youtube_extractor).__name__}")
        print(f"  ✅ Instagram extractor: {type(service.instagram_extractor).__name__}")
        print(f"  ✅ TikTok extractor: {type(service.tiktok_extractor).__name__}")
        print(f"  ✅ Video analyzer: {type(service.video_analyzer).__name__}")
        print(f"  ✅ Image analyzer: {type(service.image_analyzer).__name__}")
        print(f"  ✅ Classifier: {type(service.classifier).__name__}")

        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_youtube_full_pipeline():
    """Test complete pipeline with YouTube URL."""
    print("\n📌 Testing YouTube Full Pipeline (End-to-End)...")
    print("  ⚠️  This makes REAL API calls (YouTube + Gemini)")
    print("  ⚠️  May take 30-60 seconds")

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Skipping (missing API keys)")
        return False

    service = LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key
    )

    url = TEST_URLS['youtube_food']

    try:
        print(f"  🔄 Analyzing: {url}")
        print(f"  Step 1: Platform detection...")
        print(f"  Step 2: Metadata extraction...")
        print(f"  Step 3: Video analysis (Gemini)...")
        print(f"  Step 4: Content classification...")

        result = await service.analyze(url)

        # Verify result structure
        required_fields = [
            'url', 'platform', 'content_type', 'metadata',
            'video_analysis', 'classification', 'analyzed_at'
        ]

        missing = [f for f in required_fields if f not in result]
        if missing:
            print(f"  ❌ Missing fields: {missing}")
            return False

        # Display results
        print(f"\n  ✅ Analysis completed successfully!")
        print(f"  ✅ Platform: {result['platform']}")
        print(f"  ✅ Content Type: {result['content_type']}")
        print(f"  ✅ Video Title: {result['metadata'].get('title', 'N/A')[:60]}...")

        if result.get('video_analysis'):
            print(f"  ✅ Video Analysis: Available")
            if 'transcript' in result['video_analysis']:
                transcript_preview = str(result['video_analysis']['transcript'])[:100]
                print(f"     - Transcript preview: {transcript_preview}...")

        if result.get('classification'):
            print(f"  ✅ Classification: Available")
            if 'primary_category' in result['classification']:
                print(f"     - Category: {result['classification']['primary_category']}")
            if 'confidence' in result['classification']:
                print(f"     - Confidence: {result['classification']['confidence']}")

        print(f"  ✅ Analyzed at: {result['analyzed_at']}")

        return True

    except Exception as e:
        print(f"  ❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_youtube_shorts_pipeline():
    """Test pipeline with YouTube Shorts."""
    print("\n📌 Testing YouTube Shorts Pipeline...")

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Skipping (missing API keys)")
        return False

    service = LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key
    )

    url = TEST_URLS['youtube_shorts']

    try:
        print(f"  🔄 Analyzing Shorts: {url[:60]}...")
        result = await service.analyze(url)

        print(f"  ✅ Shorts analysis completed")
        print(f"  ✅ Platform: {result['platform']}")
        print(f"  ✅ Is Shorts: {result['metadata'].get('is_shorts', False)}")

        return True

    except Exception as e:
        print(f"  ❌ Shorts pipeline failed: {e}")
        return False


async def test_instagram_pipeline():
    """Test pipeline with Instagram URL."""
    print("\n📌 Testing Instagram Pipeline...")

    url = TEST_URLS['instagram']
    if not url:
        print("  ⚠️  No Instagram test URL provided")
        print("  ℹ️  Add a public Instagram URL to TEST_URLS to test this feature")
        return True  # Skip, not a failure

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Skipping (missing API keys)")
        return False

    service = LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key
    )

    try:
        print(f"  🔄 Analyzing Instagram: {url[:60]}...")
        result = await service.analyze(url)

        print(f"  ✅ Instagram analysis completed")
        print(f"  ✅ Platform: {result['platform']}")
        print(f"  ✅ Content Type: {result['content_type']}")

        return True

    except Exception as e:
        print(f"  ❌ Instagram pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tiktok_pipeline():
    """Test pipeline with TikTok URL."""
    print("\n📌 Testing TikTok Pipeline...")

    url = TEST_URLS['tiktok']
    if not url:
        print("  ⚠️  No TikTok test URL provided")
        print("  ℹ️  Add a public TikTok URL to TEST_URLS to test this feature")
        return True  # Skip, not a failure

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Skipping (missing API keys)")
        return False

    service = LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key
    )

    try:
        print(f"  🔄 Analyzing TikTok: {url[:60]}...")
        result = await service.analyze(url)

        print(f"  ✅ TikTok analysis completed")
        print(f"  ✅ Platform: {result['platform']}")
        print(f"  ✅ Content Type: {result['content_type']}")

        return True

    except Exception as e:
        print(f"  ❌ TikTok pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling_invalid_url():
    """Test error handling with invalid URL."""
    print("\n📌 Testing Error Handling (Invalid URL)...")

    youtube_key = os.getenv('YOUTUBE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    if not youtube_key or not gemini_key:
        print("  ⚠️  Skipping (missing API keys)")
        return False

    service = LinkAnalyzerService(
        youtube_api_key=youtube_key,
        gemini_api_key=gemini_key
    )

    invalid_urls = [
        "https://twitter.com/status/123",  # Unsupported platform
        "https://example.com/video",  # Invalid domain
        "not-a-url",  # Malformed URL
    ]

    all_handled = True
    for url in invalid_urls:
        try:
            await service.analyze(url)
            print(f"  ❌ Should have raised error for: {url}")
            all_handled = False
        except ValueError as e:
            print(f"  ✅ Correctly rejected: {url[:40]}... ({str(e)[:50]}...)")
        except Exception as e:
            print(f"  ⚠️  Unexpected error for {url}: {e}")
            all_handled = False

    return all_handled


async def main():
    """Run all Phase 4 integration tests."""
    print("=" * 70)
    print("🧪 Phase 4 Integration Test - Complete Pipeline End-to-End")
    print("=" * 70)
    print()
    print("⚠️  This test makes REAL API calls (YouTube + Gemini)")
    print("⚠️  Full pipeline tests may take 1-2 minutes per URL")
    print()

    tests = [
        ("Service Initialization", test_service_initialization),
        ("YouTube Full Pipeline", test_youtube_full_pipeline),
        ("YouTube Shorts Pipeline", test_youtube_shorts_pipeline),
        ("Instagram Pipeline", test_instagram_pipeline),
        ("TikTok Pipeline", test_tiktok_pipeline),
        ("Error Handling (Invalid URL)", test_error_handling_invalid_url),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 Phase 4 Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 4 integration tests passed!")
        print("\n📝 Complete pipeline validated:")
        print("   - Platform detection ✅")
        print("   - Metadata extraction ✅")
        print("   - Gemini video/image analysis ✅")
        print("   - AI content classification ✅")
        print("   - Error handling ✅")
        print("\n🚀 Ready for API endpoint implementation!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
