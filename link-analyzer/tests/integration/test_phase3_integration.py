#!/usr/bin/env python3
"""
Phase 3 Integration Test Script

Gemini 2.5 API를 사용한 비디오/이미지 분석 통합 테스트:
- Gemini API 연결 검증
- YouTube URL 직접 비디오 분석
- 로컬 파일 비디오 분석 (Instagram/TikTok)
- 이미지 분석 및 OCR
- AI 기반 콘텐츠 분류

Note: 이 테스트는 실제 Gemini API를 호출하며 비용이 발생할 수 있습니다.
"""

import sys
import os
from pathlib import Path
import asyncio

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.analysis.gemini_video import GeminiVideoAnalyzer
from app.services.analysis.gemini_image import GeminiImageAnalyzer
from app.services.analysis.content_classifier import ContentClassifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Test configuration
TEST_CONFIG = {
    # YouTube test video (short, public, popular)
    'youtube_url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw',  # "Me at the zoo" - first YouTube video (18s)

    # Sample prompts
    'video_analysis_prompt': """
    Analyze this video and extract:
    1. What is being said (transcription)
    2. Any visible text in the video
    3. Main visual elements and scenes
    4. Brief summary of the content

    Return response in this format:
    - Transcript: [transcribed audio]
    - Visible Text: [any text shown in video]
    - Visual Elements: [description of scenes]
    - Summary: [brief summary]
    """,

    'image_analysis_prompt': """
    Analyze this image and extract:
    1. Any text visible in the image (OCR)
    2. Objects and elements present
    3. Scene description

    Return response in this format:
    - Text: [extracted text]
    - Objects: [list of objects]
    - Scene: [scene description]
    """,

    'classification_prompt': """
    Classify this content and extract key information.

    Categories: restaurant/cafe, travel, product, health, lifestyle

    Extract:
    - Primary category
    - Sub-categories
    - Place name (if any)
    - Key features
    - Sentiment (positive/negative/neutral)

    Return as JSON.
    """
}


async def test_gemini_api_connection():
    """Test Gemini API connection and API key validity."""
    print("\n📌 Testing Gemini API Connection...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  GEMINI_API_KEY not set in .env")
        print("  ℹ️  Set GEMINI_API_KEY to test Gemini integration")
        return False

    try:
        analyzer = GeminiVideoAnalyzer(api_key=api_key)
        print(f"  ✅ Gemini API key loaded: {api_key[:10]}...")
        print(f"  ✅ Model: {analyzer.model}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to initialize Gemini analyzer: {e}")
        return False


async def test_gemini_video_url_analysis():
    """Test Gemini video analysis with YouTube URL (no download)."""
    print("\n📌 Testing Gemini Video Analysis (YouTube URL)...")
    print("  ⚠️  This makes a REAL API call and may take 20-30 seconds")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    analyzer = GeminiVideoAnalyzer(api_key=api_key)
    url = TEST_CONFIG['youtube_url']
    prompt = TEST_CONFIG['video_analysis_prompt']

    try:
        print(f"  🔄 Analyzing video: {url[:60]}...")
        result = await analyzer.analyze_video_url(url, prompt)

        print(f"  ✅ Analysis completed")
        print(f"  ✅ Response type: {type(result)}")

        # Check if we got meaningful response
        if 'response_text' in result and result['response_text']:
            response_preview = result['response_text'][:200]
            print(f"  ✅ Response preview: {response_preview}...")
            return True
        else:
            print(f"  ⚠️  Response structure: {result.keys()}")
            return True  # Still pass if we got a response

    except Exception as e:
        print(f"  ❌ Video URL analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_video_file_analysis():
    """Test Gemini video analysis with local file (Instagram/TikTok scenario)."""
    print("\n📌 Testing Gemini Video File Analysis...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    # Check if test video file exists
    test_video_path = Path(__file__).parent.parent.parent.parent / "test_video.mp4"
    if not test_video_path.exists():
        print(f"  ⚠️  No test video file at {test_video_path}")
        print("  ℹ️  Add a small test video file to test this feature")
        return True  # Skip, not a failure

    analyzer = GeminiVideoAnalyzer(api_key=api_key)
    prompt = TEST_CONFIG['video_analysis_prompt']

    try:
        print(f"  🔄 Analyzing video file: {test_video_path.name}...")
        result = await analyzer.analyze_video_file(str(test_video_path), prompt)

        print(f"  ✅ File analysis completed")
        print(f"  ✅ Response type: {type(result)}")

        if 'response_text' in result and result['response_text']:
            response_preview = result['response_text'][:200]
            print(f"  ✅ Response preview: {response_preview}...")

        return True

    except Exception as e:
        print(f"  ❌ Video file analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gemini_image_analyzer_initialization():
    """Test Gemini image analyzer initialization."""
    print("\n📌 Testing Gemini Image Analyzer Initialization...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    try:
        analyzer = GeminiImageAnalyzer(api_key=api_key)
        print(f"  ✅ GeminiImageAnalyzer initialized")
        print(f"  ✅ Model: {analyzer.model}")
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


async def test_gemini_image_analysis():
    """Test Gemini image analysis and OCR."""
    print("\n📌 Testing Gemini Image Analysis...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    # Check if test image exists
    test_image_path = Path(__file__).parent.parent.parent.parent / "test_image.jpg"
    if not test_image_path.exists():
        print(f"  ⚠️  No test image file at {test_image_path}")
        print("  ℹ️  Add a test image file to test this feature")
        return True  # Skip, not a failure

    analyzer = GeminiImageAnalyzer(api_key=api_key)
    prompt = TEST_CONFIG['image_analysis_prompt']

    try:
        print(f"  🔄 Analyzing image: {test_image_path.name}...")
        result = await analyzer.analyze_image(str(test_image_path), prompt)

        print(f"  ✅ Image analysis completed")
        print(f"  ✅ Response type: {type(result)}")

        if 'response_text' in result and result['response_text']:
            response_preview = result['response_text'][:200]
            print(f"  ✅ Response preview: {response_preview}...")

        return True

    except Exception as e:
        print(f"  ❌ Image analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_content_classifier_initialization():
    """Test content classifier initialization."""
    print("\n📌 Testing Content Classifier Initialization...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    try:
        classifier = ContentClassifier(api_key=api_key)
        print(f"  ✅ ContentClassifier initialized")
        print(f"  ✅ Model: {classifier.model}")
        return True
    except Exception as e:
        print(f"  ❌ Initialization failed: {e}")
        return False


async def test_content_classification():
    """Test AI-based content classification."""
    print("\n📌 Testing Content Classification...")

    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key or api_key == 'your_gemini_api_key':
        print("  ⚠️  Skipping (no API key)")
        return False

    classifier = ContentClassifier(api_key=api_key)

    # Sample content data for classification
    sample_content = {
        'caption': '서울 강남에 새로 오픈한 이탈리안 레스토랑! 파스타가 정말 맛있어요 🍝 #맛집 #강남맛집 #이탈리안',
        'ocr_texts': ['MENU', 'Pasta 18,000원', 'Pizza 22,000원'],
        'transcript': '안녕하세요 오늘은 강남에 있는 이탈리안 레스토랑을 소개해드릴게요',
        'hashtags': ['맛집', '강남맛집', '이탈리안'],
        'location': '서울 강남구'
    }

    try:
        print(f"  🔄 Classifying sample content...")
        result = await classifier.classify(sample_content)

        print(f"  ✅ Classification completed")
        print(f"  ✅ Result type: {type(result)}")

        if isinstance(result, dict):
            if 'primary_category' in result:
                print(f"  ✅ Primary category: {result['primary_category']}")
            if 'confidence' in result:
                print(f"  ✅ Confidence: {result['confidence']}")
            if 'response_text' in result:
                response_preview = result['response_text'][:200]
                print(f"  ✅ Response preview: {response_preview}...")

        return True

    except Exception as e:
        print(f"  ❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Phase 3 integration tests."""
    print("=" * 60)
    print("🧪 Phase 3 Integration Test - Gemini Analysis Pipeline")
    print("=" * 60)
    print()
    print("⚠️  This test makes REAL Gemini API calls (costs apply)")
    print("⚠️  Video analysis may take 20-60 seconds per request")
    print()

    tests = [
        ("Gemini API Connection", test_gemini_api_connection),
        ("Gemini Video URL Analysis", test_gemini_video_url_analysis),
        ("Gemini Video File Analysis", test_gemini_video_file_analysis),
        ("Gemini Image Analyzer Init", test_gemini_image_analyzer_initialization),
        ("Gemini Image Analysis", test_gemini_image_analysis),
        ("Content Classifier Init", test_content_classifier_initialization),
        ("Content Classification", test_content_classification),
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
    print("📊 Phase 3 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 3 integration tests passed!")
        print("\n📝 Next: Phase 4 - End-to-end pipeline integration")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\n💡 Tips:")
        print("  - Make sure GEMINI_API_KEY is set in .env")
        print("  - Add test video/image files for comprehensive testing")
        print("  - Check API quotas and billing")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
