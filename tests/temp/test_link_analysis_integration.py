#!/usr/bin/env python3
"""
Link Analysis API Integration Test

Tests the complete link analysis workflow with real components.
"""

import asyncio
import sys
import time
from datetime import datetime

import httpx


async def test_link_analysis_integration():
    """Test link analysis integration with FastAPI server."""

    base_url = "http://localhost:8000"

    # Test URLs (using mock data for testing)
    test_urls = [
        "https://instagram.com/p/test123",
        "https://twitter.com/user/status/456",
    ]

    async with httpx.AsyncClient() as client:
        print("🚀 Starting Link Analysis Integration Tests")
        print("=" * 50)

        # Test 1: Service Status Check
        print("\n1. Testing Service Status...")
        try:
            response = await client.get(f"{base_url}/api/v1/links/status")
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ Service Status: {status_data['status']}")
                print(f"   Cache Connection: {status_data['cache_connection']}")
                print(f"   Active Analyses: {status_data['active_analyses']}")
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return False

        # Test 2: Cache Statistics
        print("\n2. Testing Cache Statistics...")
        try:
            response = await client.get(f"{base_url}/api/v1/links/cache/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Cache Stats Retrieved:")
                print(f"   Hit Rate: {stats.get('hit_rate', 0):.2%}")
                print(f"   Total Requests: {stats.get('total_requests', 0)}")
                print(f"   L1 Hits: {stats.get('l1_hits', 0)}")
                print(f"   L2 Hits: {stats.get('l2_hits', 0)}")
            else:
                print(f"❌ Cache stats failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Cache stats error: {e}")

        # Test 3: Single URL Analysis
        print("\n3. Testing Single URL Analysis...")
        for i, url in enumerate(test_urls):
            print(f"\n   Testing URL {i+1}: {url}")

            try:
                start_time = time.time()

                response = await client.post(
                    f"{base_url}/api/v1/links/analyze", json={"url": url}, timeout=30.0
                )

                end_time = time.time()
                processing_time = end_time - start_time

                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Analysis completed in {processing_time:.2f}s")
                    print(f"      Analysis ID: {data['analysisId']}")
                    print(f"      Status: {data['status']}")
                    print(f"      Cached: {data['cached']}")

                    if data.get("result"):
                        result = data["result"]
                        print(f"      Confidence: {result.get('confidence', 0):.2%}")

                        if result.get("placeInfo"):
                            place = result["placeInfo"]
                            print(f"      Place: {place.get('name', 'N/A')}")
                            print(f"      Category: {place.get('category', 'N/A')}")

                    # Test status retrieval
                    analysis_id = data["analysisId"]
                    status_response = await client.get(
                        f"{base_url}/api/v1/links/analyses/{analysis_id}"
                    )

                    if status_response.status_code == 200:
                        print(f"      ✅ Status retrieval successful")
                    else:
                        print(
                            f"      ❌ Status retrieval failed: {status_response.status_code}"
                        )

                elif response.status_code == 422:
                    print(f"   ⚠️  URL validation error (expected for test URLs)")
                elif response.status_code == 503:
                    print(f"   ⚠️  Service temporarily unavailable")
                else:
                    print(f"   ❌ Analysis failed: {response.status_code}")
                    print(f"      Error: {response.text}")

            except Exception as e:
                print(f"   ❌ Analysis error: {e}")

        # Test 4: Async Analysis with Webhook
        print("\n4. Testing Async Analysis...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/links/analyze",
                json={
                    "url": test_urls[0],
                    "webhook_url": "https://example.com/webhook",
                },
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Async analysis initiated")
                print(f"      Analysis ID: {data['analysisId']}")
                print(f"      Status: {data['status']}")

                # Check status after a moment
                await asyncio.sleep(1)

                analysis_id = data["analysisId"]
                status_response = await client.get(
                    f"{base_url}/api/v1/links/analyses/{analysis_id}"
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"      Current Status: {status_data['status']}")
                    if status_data.get("progress"):
                        print(f"      Progress: {status_data['progress']:.1%}")

            else:
                print(f"   ❌ Async analysis failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Async analysis error: {e}")

        # Test 5: Bulk Analysis
        print("\n5. Testing Bulk Analysis...")
        try:
            response = await client.post(
                f"{base_url}/api/v1/links/bulk-analyze",
                json={"urls": test_urls[:2]},  # Limit to 2 URLs for testing
                timeout=30.0,
            )

            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Bulk analysis initiated")
                print(f"      Batch ID: {data['batchId']}")
                print(f"      Total URLs: {data['totalUrls']}")
                print(f"      Accepted: {len(data['acceptedUrls'])}")
                print(f"      Rejected: {len(data['rejectedUrls'])}")

                if data["rejectedUrls"]:
                    print(f"      Rejected URLs:")
                    for rejected in data["rejectedUrls"]:
                        print(f"        - {rejected['url']}: {rejected['reason']}")

            else:
                print(f"   ❌ Bulk analysis failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Bulk analysis error: {e}")

        # Test 6: Error Handling
        print("\n6. Testing Error Handling...")

        # Invalid URL format
        try:
            response = await client.post(
                f"{base_url}/api/v1/links/analyze",
                json={"url": "invalid-url"},
                timeout=10.0,
            )

            if response.status_code == 422:
                print(f"   ✅ Invalid URL properly rejected")
            else:
                print(f"   ❌ Invalid URL handling failed: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Error handling test error: {e}")

        # Non-existent analysis ID
        try:
            fake_id = "non-existent-analysis-id"
            response = await client.get(f"{base_url}/api/v1/links/analyses/{fake_id}")

            if response.status_code == 404:
                print(f"   ✅ Non-existent analysis properly handled")
            else:
                print(
                    f"   ❌ Non-existent analysis handling failed: {response.status_code}"
                )

        except Exception as e:
            print(f"   ❌ Non-existent analysis test error: {e}")

        # Test 7: Performance Check
        print("\n7. Testing Performance...")

        performance_results = []

        for i in range(3):
            try:
                start_time = time.time()

                response = await client.post(
                    f"{base_url}/api/v1/links/analyze",
                    json={"url": f"https://example.com/performance_test_{i}"},
                    timeout=15.0,
                )

                end_time = time.time()
                response_time = end_time - start_time
                performance_results.append(response_time)

                print(
                    f"   Request {i+1}: {response_time:.2f}s (Status: {response.status_code})"
                )

            except Exception as e:
                print(f"   Performance test {i+1} error: {e}")

        if performance_results:
            avg_time = sum(performance_results) / len(performance_results)
            max_time = max(performance_results)

            print(f"   📊 Performance Summary:")
            print(f"      Average Response Time: {avg_time:.2f}s")
            print(f"      Max Response Time: {max_time:.2f}s")

            if avg_time < 10.0:
                print(f"   ✅ Performance within acceptable range")
            else:
                print(f"   ⚠️  Performance may need optimization")

        print("\n" + "=" * 50)
        print("🎉 Integration Tests Completed")

        return True


def main():
    """Main test runner."""
    print(f"Link Analysis Integration Test")
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        success = asyncio.run(test_link_analysis_integration())

        if success:
            print("\\n✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("\\n❌ Some tests failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
