#!/usr/bin/env python3
"""
Phase 2 Integration Test Script

실제 API를 사용하여 플랫폼별 메타데이터 추출을 테스트합니다.
- YouTube Data API v3 연동 테스트
- yt-dlp Instagram 추출 테스트
- yt-dlp TikTok 추출 테스트
- 에러 처리 및 재시도 로직 검증

Note: 이 테스트는 실제 API를 호출하므로 인터넷 연결과 API 키가 필요합니다.
"""

import sys
import os
from pathlib import Path
import asyncio

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.platform.youtube import YouTubeExtractor
from app.services.platform.instagram import InstagramExtractor
from app.services.platform.tiktok import TikTokExtractor
from app.services.platform.base import Platform
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Test URLs (using public, popular content)
TEST_URLS = {
    'youtube_standard': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',  # Rick Astley - Never Gonna Give You Up
    'youtube_short': 'https://youtube.com/shorts/jNQXAC9IVRw',  # Sample short
    'youtube_youtu_be': 'https://youtu.be/dQw4w9WgXcQ',  # Short URL format
    # Note: Instagram/TikTok URLs should be replaced with actual public URLs
    # These are placeholders - real tests need valid public URLs
    'instagram_video': None,  # Replace with actual Instagram video URL
    'instagram_image': None,  # Replace with actual Instagram image URL
    'tiktok_video': None,     # Replace with actual TikTok video URL
}


async def test_youtube_api_connection():
    """Test YouTube Data API v3 connection and API key validity."""
    print("\n📌 Testing YouTube Data API Connection...")

    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_youtube_data_api_key_here':
        print("  ⚠️  YOUTUBE_API_KEY not set in .env")
        print("  ℹ️  Set YOUTUBE_API_KEY to test YouTube integration")
        return False

    try:
        extractor = YouTubeExtractor(api_key=api_key)
        print(f"  ✅ YouTube API key loaded: {api_key[:10]}...")
        return True
    except Exception as e:
        print(f"  ❌ Failed to initialize YouTube extractor: {e}")
        return False


async def test_youtube_video_id_extraction():
    """Test YouTube video ID extraction from various URL formats."""
    print("\n📌 Testing YouTube Video ID Extraction...")

    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_youtube_data_api_key_here':
        print("  ⚠️  Skipping (no API key)")
        return False

    extractor = YouTubeExtractor(api_key=api_key)

    test_cases = [
        (TEST_URLS['youtube_standard'], 'dQw4w9WgXcQ'),
        (TEST_URLS['youtube_youtu_be'], 'dQw4w9WgXcQ'),
        (TEST_URLS['youtube_short'], 'jNQXAC9IVRw'),
    ]

    all_passed = True
    for url, expected_id in test_cases:
        try:
            video_id = extractor._extract_video_id(url)
            if video_id == expected_id:
                print(f"  ✅ {url[:50]}... → {video_id}")
            else:
                print(f"  ❌ {url[:50]}... → {video_id} (expected: {expected_id})")
                all_passed = False
        except Exception as e:
            print(f"  ❌ {url[:50]}... → Error: {e}")
            all_passed = False

    return all_passed


async def test_youtube_metadata_extraction():
    """Test actual YouTube metadata extraction using YouTube Data API v3."""
    print("\n📌 Testing YouTube Metadata Extraction (Real API Call)...")

    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_youtube_data_api_key_here':
        print("  ⚠️  Skipping (no API key)")
        return False

    extractor = YouTubeExtractor(api_key=api_key)
    url = TEST_URLS['youtube_standard']

    try:
        metadata = await extractor.extract_metadata(url)

        # Verify required fields
        required_fields = ['platform', 'content_type', 'video_id', 'title', 'description']
        missing_fields = [field for field in required_fields if field not in metadata]

        if missing_fields:
            print(f"  ❌ Missing fields: {missing_fields}")
            return False

        print(f"  ✅ Platform: {metadata['platform']}")
        print(f"  ✅ Content Type: {metadata['content_type']}")
        print(f"  ✅ Video ID: {metadata['video_id']}")
        print(f"  ✅ Title: {metadata['title'][:50]}...")
        print(f"  ✅ Channel: {metadata.get('channel_title', 'N/A')}")
        print(f"  ✅ Duration: {metadata.get('duration', 'N/A')}")
        print(f"  ✅ View Count: {metadata.get('view_count', 'N/A')}")

        # Verify platform and content_type
        if metadata['platform'] != Platform.YOUTUBE:
            print(f"  ❌ Wrong platform: {metadata['platform']}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Metadata extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_youtube_shorts_detection():
    """Test YouTube Shorts URL detection and metadata extraction."""
    print("\n📌 Testing YouTube Shorts Detection...")

    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key or api_key == 'your_youtube_data_api_key_here':
        print("  ⚠️  Skipping (no API key)")
        return False

    extractor = YouTubeExtractor(api_key=api_key)
    shorts_url = TEST_URLS['youtube_short']

    try:
        # Test is_shorts detection
        is_short = YouTubeExtractor.is_shorts(shorts_url)
        if not is_short:
            print(f"  ❌ Failed to detect Shorts URL")
            return False

        print(f"  ✅ Shorts URL detected correctly")

        # Test metadata extraction for Shorts
        metadata = await extractor.extract_metadata(shorts_url)
        print(f"  ✅ Shorts metadata extracted: {metadata['title'][:40]}...")

        return True

    except Exception as e:
        print(f"  ❌ Shorts test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_instagram_extractor_initialization():
    """Test Instagram extractor initialization (yt-dlp)."""
    print("\n📌 Testing Instagram Extractor Initialization...")

    try:
        extractor = InstagramExtractor(download_dir="temp/test")
        print(f"  ✅ InstagramExtractor initialized")
        print(f"  ✅ Download directory: {extractor.download_dir}")

        # Check if yt-dlp is available
        import yt_dlp
        print(f"  ✅ yt-dlp version: {yt_dlp.version.__version__}")

        return True

    except ImportError as e:
        print(f"  ❌ yt-dlp not installed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


async def test_tiktok_extractor_initialization():
    """Test TikTok extractor initialization (yt-dlp)."""
    print("\n📌 Testing TikTok Extractor Initialization...")

    try:
        extractor = TikTokExtractor(download_dir="temp/test")
        print(f"  ✅ TikTokExtractor initialized")
        print(f"  ✅ Download directory: {extractor.download_dir}")

        return True

    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


async def test_instagram_metadata_extraction():
    """Test Instagram metadata extraction (requires valid Instagram URL)."""
    print("\n📌 Testing Instagram Metadata Extraction...")

    url = TEST_URLS['instagram_video']
    if not url:
        print("  ⚠️  No Instagram test URL provided")
        print("  ℹ️  Add a public Instagram URL to TEST_URLS to test this feature")
        return True  # Skip, not a failure

    try:
        extractor = InstagramExtractor(download_dir="temp/test")
        metadata = await extractor.extract_metadata(url)

        print(f"  ✅ Platform: {metadata['platform']}")
        print(f"  ✅ Content Type: {metadata['content_type']}")
        print(f"  ✅ Caption: {metadata.get('caption', 'N/A')[:50]}...")
        print(f"  ✅ Hashtags: {len(metadata.get('hashtags', []))} found")

        return True

    except Exception as e:
        print(f"  ❌ Instagram extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tiktok_metadata_extraction():
    """Test TikTok metadata extraction (requires valid TikTok URL)."""
    print("\n📌 Testing TikTok Metadata Extraction...")

    url = TEST_URLS['tiktok_video']
    if not url:
        print("  ⚠️  No TikTok test URL provided")
        print("  ℹ️  Add a public TikTok URL to TEST_URLS to test this feature")
        return True  # Skip, not a failure

    try:
        extractor = TikTokExtractor(download_dir="temp/test")
        metadata = await extractor.extract_metadata(url)

        print(f"  ✅ Platform: {metadata['platform']}")
        print(f"  ✅ Content Type: {metadata['content_type']}")
        print(f"  ✅ Description: {metadata.get('description', 'N/A')[:50]}...")
        print(f"  ✅ Hashtags: {len(metadata.get('hashtags', []))} found")

        return True

    except Exception as e:
        print(f"  ❌ TikTok extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 2 integration tests."""
    print("=" * 60)
    print("🧪 Phase 2 Integration Test - Platform Metadata Extraction")
    print("=" * 60)
    print()
    print("⚠️  This test makes REAL API calls and downloads media files")
    print()

    tests = [
        ("YouTube API Connection", test_youtube_api_connection),
        ("YouTube Video ID Extraction", test_youtube_video_id_extraction),
        ("YouTube Metadata Extraction", test_youtube_metadata_extraction),
        ("YouTube Shorts Detection", test_youtube_shorts_detection),
        ("Instagram Extractor Init", test_instagram_extractor_initialization),
        ("TikTok Extractor Init", test_tiktok_extractor_initialization),
        ("Instagram Metadata Extraction", test_instagram_metadata_extraction),
        ("TikTok Metadata Extraction", test_tiktok_metadata_extraction),
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
    print("\n" + "=" * 60)
    print("📊 Phase 2 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 2 integration tests passed!")
        print("\n📝 Next: Phase 3 - Gemini analysis pipeline")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\n💡 Tips:")
        print("  - Make sure YOUTUBE_API_KEY is set in .env")
        print("  - Add public Instagram/TikTok URLs to TEST_URLS for full testing")
        print("  - Check internet connection for API calls")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
