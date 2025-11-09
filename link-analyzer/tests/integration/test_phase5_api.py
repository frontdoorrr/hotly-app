#!/usr/bin/env python3
"""
Phase 5 API Integration Test

FastAPI 엔드포인트 테스트:
- POST /api/v1/analyze - 링크 분석 API
- GET /api/v1/analyze/health - 헬스 체크
- GET /api/v1/analyze/platforms - 지원 플랫폼 목록
- 에러 처리 테스트

Note: 이 테스트는 실제 API를 호출하며 비용이 발생할 수 있습니다.
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after env vars are loaded
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    print("\n📌 Testing Health Check Endpoint...")

    response = client.get("/api/v1/analyze/health")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "status" in data, "Response missing 'status' field"
    assert data["status"] == "ok", f"Expected status 'ok', got '{data['status']}'"

    print(f"  ✅ Health check passed: {data}")
    return True


def test_platforms_endpoint():
    """Test platforms listing endpoint."""
    print("\n📌 Testing Platforms Endpoint...")

    response = client.get("/api/v1/analyze/platforms")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert "platforms" in data, "Response missing 'platforms' field"
    assert len(data["platforms"]) >= 3, "Expected at least 3 platforms"

    platforms = data["platforms"]
    platform_names = [p["name"] for p in platforms]

    print(f"  ✅ Supported platforms: {', '.join(platform_names)}")

    # Verify required platforms
    assert any(p["value"] == "youtube" for p in platforms), "YouTube not in platforms"
    assert any(p["value"] == "instagram" for p in platforms), "Instagram not in platforms"
    assert any(p["value"] == "tiktok" for p in platforms), "TikTok not in platforms"

    print(f"  ✅ All required platforms present")
    return True


def test_analyze_youtube_url():
    """Test analysis with YouTube URL."""
    print("\n📌 Testing Analyze Endpoint (YouTube URL)...")
    print("  ⚠️  This makes REAL API calls (YouTube + Gemini)")
    print("  ⚠️  May take 30-60 seconds")

    request_data = {
        "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # "Me at the zoo" (18s)
        "options": {
            "include_video_analysis": True,
            "include_classification": True
        }
    }

    response = client.post("/api/v1/analyze/", json=request_data)

    # Check response status
    if response.status_code != 200:
        print(f"  ❌ API returned {response.status_code}")
        print(f"  Response: {response.json()}")
        return False

    data = response.json()

    # Verify response structure
    required_fields = ['url', 'platform', 'content_type', 'title', 'analyzed_at']
    missing = [f for f in required_fields if f not in data]

    if missing:
        print(f"  ❌ Missing fields: {missing}")
        return False

    print(f"  ✅ Analysis completed")
    print(f"  ✅ Platform: {data['platform']}")
    print(f"  ✅ Content Type: {data['content_type']}")
    print(f"  ✅ Title: {data['title'][:60]}...")

    if data.get('video_analysis'):
        print(f"  ✅ Video analysis included")

    if data.get('classification'):
        print(f"  ✅ Classification included")
        print(f"     - Category: {data['classification'].get('primary_category', 'N/A')}")
        print(f"     - Confidence: {data['classification'].get('confidence', 0)}")

    return True


def test_analyze_invalid_url():
    """Test analysis with invalid URL."""
    print("\n📌 Testing Error Handling (Invalid URL)...")

    request_data = {
        "url": "https://twitter.com/status/123"  # Unsupported platform
    }

    response = client.post("/api/v1/analyze/", json=request_data)

    # Should return 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    data = response.json()
    assert "detail" in data, "Error response missing 'detail' field"

    print(f"  ✅ Correctly rejected invalid URL")
    print(f"  ✅ Error message: {data['detail'][:80]}...")

    return True


def test_analyze_malformed_request():
    """Test analysis with malformed request."""
    print("\n📌 Testing Error Handling (Malformed Request)...")

    # Missing required 'url' field
    request_data = {
        "options": {}
    }

    response = client.post("/api/v1/analyze/", json=request_data)

    # Should return 422 Validation Error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    print(f"  ✅ Correctly rejected malformed request")

    return True


def main():
    """Run all Phase 5 API tests."""
    print("=" * 70)
    print("🧪 Phase 5 API Integration Test - FastAPI Endpoints")
    print("=" * 70)
    print()
    print("⚠️  Some tests make REAL API calls")
    print()

    tests = [
        ("Health Check", test_health_check),
        ("Platforms Endpoint", test_platforms_endpoint),
        ("Analyze YouTube URL", test_analyze_youtube_url),
        ("Error Handling (Invalid URL)", test_analyze_invalid_url),
        ("Error Handling (Malformed Request)", test_analyze_malformed_request),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except AssertionError as e:
            print(f"  ❌ Assertion failed: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("📊 Phase 5 Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 5 API tests passed!")
        print("\n📝 API endpoints validated:")
        print("   - POST /api/v1/analyze/ ✅")
        print("   - GET /api/v1/analyze/health ✅")
        print("   - GET /api/v1/analyze/platforms ✅")
        print("   - Error handling (400, 422) ✅")
        print("\n🚀 API ready for production use!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
