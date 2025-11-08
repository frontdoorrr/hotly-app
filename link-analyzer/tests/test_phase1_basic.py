#!/usr/bin/env python3
"""
Phase 1 Basic Test Script (No Dependencies Required)

기본 구조와 import만 테스트합니다.
실제 외부 라이브러리 의존성 없이 실행 가능합니다.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_platform_base_module():
    """Test platform base module."""
    print("📌 Testing platform base module...")
    try:
        from app.services.platform.base import (
            PlatformExtractor,
            Platform,
            ContentType
        )

        # Test Platform enum
        assert Platform.YOUTUBE == "youtube"
        assert Platform.INSTAGRAM == "instagram"
        assert Platform.TIKTOK == "tiktok"
        print("  ✅ Platform enum works")

        # Test ContentType enum
        assert ContentType.VIDEO == "video"
        assert ContentType.IMAGE == "image"
        assert ContentType.CAROUSEL == "carousel"
        print("  ✅ ContentType enum works")

        # Test platform detection
        assert PlatformExtractor.detect_platform("https://youtube.com/watch?v=123") == Platform.YOUTUBE
        assert PlatformExtractor.detect_platform("https://instagram.com/p/123/") == Platform.INSTAGRAM
        assert PlatformExtractor.detect_platform("https://tiktok.com/@user/video/123") == Platform.TIKTOK
        assert PlatformExtractor.detect_platform("https://twitter.com/status/123") is None
        print("  ✅ Platform detection works")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas_module():
    """Test schemas module."""
    print("\n📌 Testing schemas module...")
    try:
        from app.schemas.analysis import (
            AnalysisRequest,
            AnalysisResponse,
            Platform,
            ContentType,
            PlaceInfo,
            MenuItem,
            ClassificationResult,
        )

        # Test Platform enum
        assert Platform.YOUTUBE == "youtube"
        print("  ✅ Platform enum in schemas works")

        # Test AnalysisRequest
        request = AnalysisRequest(url="https://youtube.com/watch?v=123")
        assert "youtube.com" in str(request.url)
        print("  ✅ AnalysisRequest works")

        # Test PlaceInfo
        place = PlaceInfo(name="Test Place", location="Seoul")
        assert place.name == "Test Place"
        print("  ✅ PlaceInfo works")

        # Test MenuItem
        item = MenuItem(name="Burger", price="10000원")
        assert item.name == "Burger"
        print("  ✅ MenuItem works")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_models_module():
    """Test models module."""
    print("\n📌 Testing models module...")
    try:
        # Models require SQLAlchemy - skip if not installed
        try:
            import sqlalchemy
        except ImportError:
            print("  ⚠️  SQLAlchemy not installed - skipping model tests")
            print("  ℹ️  Install requirements.txt to test models")
            return True

        from app.models.analysis import AnalysisResult

        # Check table name
        assert AnalysisResult.__tablename__ == "analysis_results"
        print("  ✅ AnalysisResult model structure correct")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Test file structure exists."""
    print("\n📌 Testing file structure...")

    base_path = Path(__file__).parent.parent / "app"

    required_files = [
        "services/platform/__init__.py",
        "services/platform/base.py",
        "services/platform/youtube.py",
        "services/platform/instagram.py",
        "services/platform/tiktok.py",
        "services/analysis/__init__.py",
        "services/analysis/gemini_video.py",
        "services/analysis/gemini_image.py",
        "services/analysis/content_classifier.py",
        "schemas/analysis.py",
        "models/__init__.py",
        "models/analysis.py",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} NOT FOUND")
            all_exist = False

    return all_exist


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Phase 1 Basic Test (No External Dependencies)")
    print("=" * 60)
    print()

    tests = [
        ("File Structure", test_file_structure),
        ("Platform Base Module", test_platform_base_module),
        ("Schemas Module", test_schemas_module),
        ("Models Module", test_models_module),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
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
        print("\n🎉 All Phase 1 basic tests passed!")
        print("\n📝 Note: External dependency tests (YouTube API, yt-dlp, Gemini)")
        print("   will be tested after installing requirements.txt")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
