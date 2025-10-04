"""
Performance tests for Link Analysis API.

Tests concurrent load, response times, and resource usage.
"""

import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.services.places.place_analysis_service import PlaceAnalysisResult


class TestLinkAnalysisPerformance:
    """Performance test suite for link analysis."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_fast_content(self):
        """Fast mock content extraction."""
        return ContentExtractResult(
            url="https://instagram.com/p/perf_test/",
            title="Performance Test Post",
            description="Testing performance",
            images=["https://example.com/img.jpg"],
            platform="instagram",
            extraction_time=0.1,  # Fast extraction
            success=True,
        )

    @pytest.fixture
    def mock_fast_analysis(self):
        """Fast mock AI analysis."""
        return PlaceAnalysisResult(
            success=True,
            place_info=PlaceInfo(
                name="Fast Restaurant",
                category="restaurant",
                address="Performance Street 123",
                confidence=0.9,
            ),
            confidence=0.9,
            analysis_time=0.2,  # Fast analysis
            model_version="gemini-fast",
            error=None,
        )

    def test_single_request_response_time(
        self, client, mock_fast_content, mock_fast_analysis
    ):
        """Test single request response time meets requirements."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup fast mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = mock_fast_content

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = mock_fast_analysis

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Measure response time
            start_time = time.time()

            response = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/perf_single/"},
            )

            end_time = time.time()
            response_time = end_time - start_time

            # Assertions
            assert response.status_code == 200
            assert response_time < 5.0  # Should complete within 5 seconds

            data = response.json()
            assert data["success"] is True
            assert data["processingTime"] > 0

            print(f"Single request response time: {response_time:.3f}s")

    def test_cache_hit_performance(self, client):
        """Test cache hit response time."""

        cached_data = {
            "place_info": {
                "name": "Cached Place",
                "category": "restaurant",
                "confidence": 0.9,
            },
            "confidence": 0.9,
            "analysis_time": 0.1,
            "content_metadata": {"title": "Cache Test", "extraction_time": 0.05},
        }

        with patch("app.services.cache_manager.CacheManager") as mock_cache:
            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = cached_data
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Measure cache hit response time
            response_times = []

            for i in range(10):  # Test multiple cache hits
                start_time = time.time()

                response = client.post(
                    "/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/cache_perf_{i}/"},
                )

                end_time = time.time()
                response_time = end_time - start_time
                response_times.append(response_time)

                assert response.status_code == 200
                assert response.json()["cached"] is True

            # Performance requirements for cache hits
            avg_cache_time = statistics.mean(response_times)
            max_cache_time = max(response_times)

            assert avg_cache_time < 0.5  # Average cache hit should be < 500ms
            assert max_cache_time < 1.0  # Max cache hit should be < 1s

            print(f"Cache hit performance:")
            print(f"  Average: {avg_cache_time:.3f}s")
            print(f"  Max: {max_cache_time:.3f}s")
            print(f"  Min: {min(response_times):.3f}s")

    def test_concurrent_request_performance(
        self, client, mock_fast_content, mock_fast_analysis
    ):
        """Test performance under concurrent load."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = mock_fast_content

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = mock_fast_analysis

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            def make_request(request_id):
                """Make a single request."""
                start_time = time.time()
                response = client.post(
                    "/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/concurrent_{request_id}/"},
                )
                end_time = time.time()
                return {
                    "id": request_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200
                    and response.json().get("success", False),
                }

            # Test with different concurrency levels
            concurrency_levels = [5, 10, 20]

            for concurrency in concurrency_levels:
                print(f"\\nTesting concurrency level: {concurrency}")

                start_time = time.time()

                # Use ThreadPoolExecutor for concurrent requests
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [
                        executor.submit(make_request, i) for i in range(concurrency)
                    ]
                    results = [future.result() for future in futures]

                end_time = time.time()
                total_time = end_time - start_time

                # Analyze results
                successful_requests = sum(1 for r in results if r["success"])
                response_times = [r["response_time"] for r in results if r["success"]]

                if response_times:
                    avg_response_time = statistics.mean(response_times)
                    max_response_time = max(response_times)
                    throughput = successful_requests / total_time

                    print(f"  Successful requests: {successful_requests}/{concurrency}")
                    print(f"  Total time: {total_time:.2f}s")
                    print(f"  Average response time: {avg_response_time:.3f}s")
                    print(f"  Max response time: {max_response_time:.3f}s")
                    print(f"  Throughput: {throughput:.2f} req/s")

                    # Performance assertions
                    assert successful_requests >= concurrency * 0.9  # 90% success rate
                    assert avg_response_time < 10.0  # Average under 10s
                    assert max_response_time < 30.0  # Max under 30s
                    assert throughput > 0.5  # At least 0.5 requests per second

    def test_bulk_analysis_performance(self, client):
        """Test bulk analysis performance."""

        # Test different batch sizes
        batch_sizes = [2, 5, 10]

        for batch_size in batch_sizes:
            print(f"\\nTesting batch size: {batch_size}")

            urls = [
                f"https://instagram.com/p/bulk_perf_{i}/" for i in range(batch_size)
            ]

            start_time = time.time()

            response = client.post("/api/v1/links/bulk-analyze", json={"urls": urls})

            end_time = time.time()
            response_time = end_time - start_time

            assert response.status_code == 200
            data = response.json()

            assert data["totalUrls"] == batch_size
            assert len(data["acceptedUrls"]) == batch_size

            # Performance metrics
            time_per_url = response_time / batch_size

            print(f"  Total time: {response_time:.2f}s")
            print(f"  Time per URL: {time_per_url:.3f}s")

            # Bulk requests should be efficient
            assert response_time < 5.0  # Batch creation should be fast
            assert time_per_url < 1.0  # Overhead per URL should be minimal

    @pytest.mark.asyncio
    async def test_async_performance(self):
        """Test async request performance with httpx."""

        async def make_async_request(session, url_id):
            """Make async request."""
            start_time = time.time()
            try:
                response = await session.post(
                    "http://testserver/api/v1/links/analyze",
                    json={"url": f"https://instagram.com/p/async_perf_{url_id}/"},
                    timeout=10.0,
                )
                end_time = time.time()

                return {
                    "id": url_id,
                    "status_code": response.status_code,
                    "response_time": end_time - start_time,
                    "success": response.status_code == 200,
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "id": url_id,
                    "status_code": 0,
                    "response_time": end_time - start_time,
                    "success": False,
                    "error": str(e),
                }

        with patch("app.services.content_extractor.ContentExtractor"), patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ), patch("app.services.cache_manager.CacheManager"):
            async with httpx.AsyncClient(
                app=app, base_url="http://testserver"
            ) as client:
                # Test async concurrency
                num_requests = 15

                start_time = time.time()

                tasks = [make_async_request(client, i) for i in range(num_requests)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                end_time = time.time()
                total_time = end_time - start_time

                # Filter out exceptions
                valid_results = [r for r in results if isinstance(r, dict)]
                successful_results = [r for r in valid_results if r["success"]]

                if successful_results:
                    response_times = [r["response_time"] for r in successful_results]
                    avg_response_time = statistics.mean(response_times)
                    throughput = len(successful_results) / total_time

                    print(f"\\nAsync performance test:")
                    print(f"  Total requests: {num_requests}")
                    print(f"  Successful: {len(successful_results)}")
                    print(f"  Total time: {total_time:.2f}s")
                    print(f"  Average response time: {avg_response_time:.3f}s")
                    print(f"  Throughput: {throughput:.2f} req/s")

                    # Async should be more efficient
                    assert len(successful_results) >= num_requests * 0.8
                    assert throughput > 1.0  # Should handle more than 1 req/s

    def test_memory_usage_stability(
        self, client, mock_fast_content, mock_fast_analysis
    ):
        """Test that memory usage remains stable under load."""

        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup mocks
            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = mock_fast_content

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = mock_fast_analysis

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # Import psutil if available for memory monitoring
            try:
                import os

                import psutil

                process = psutil.Process(os.getpid())
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB

                print(f"Initial memory usage: {initial_memory:.2f} MB")

                # Make many requests to test memory stability
                num_requests = 50
                memory_samples = []

                for i in range(num_requests):
                    response = client.post(
                        "/api/v1/links/analyze",
                        json={"url": f"https://instagram.com/p/memory_test_{i}/"},
                    )

                    assert response.status_code == 200

                    # Sample memory every 10 requests
                    if i % 10 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)

                final_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = final_memory - initial_memory

                print(f"Final memory usage: {final_memory:.2f} MB")
                print(f"Memory growth: {memory_growth:.2f} MB")
                print(f"Memory samples: {[f'{m:.1f}' for m in memory_samples]}")

                # Memory growth should be reasonable (less than 100MB for 50 requests)
                assert memory_growth < 100.0

                # Memory usage should be relatively stable (no exponential growth)
                if len(memory_samples) > 2:
                    growth_rate = (memory_samples[-1] - memory_samples[0]) / len(
                        memory_samples
                    )
                    assert growth_rate < 5.0  # Less than 5MB growth per 10 requests

            except ImportError:
                print("psutil not available, skipping detailed memory analysis")

                # Just test that we can handle many requests without crashing
                for i in range(20):
                    response = client.post(
                        "/api/v1/links/analyze",
                        json={"url": f"https://instagram.com/p/stability_test_{i}/"},
                    )
                    assert response.status_code == 200

    def test_cache_performance_improvement(self, client):
        """Test that cache provides significant performance improvement."""

        # Test without cache (first request)
        with patch(
            "app.services.content_extractor.ContentExtractor"
        ) as mock_extractor, patch(
            "app.services.place_analysis_service.PlaceAnalysisService"
        ) as mock_analysis, patch(
            "app.services.cache_manager.CacheManager"
        ) as mock_cache:
            # Setup slower processing for uncached request
            mock_content = ContentExtractResult(
                url="https://instagram.com/p/cache_perf_test/",
                title="Cache Performance Test",
                description="Testing cache performance",
                images=["img.jpg"],
                platform="instagram",
                extraction_time=0.5,  # Slower extraction
                success=True,
            )

            mock_result = PlaceAnalysisResult(
                success=True,
                place_info=PlaceInfo(
                    name="Cache Test Restaurant",
                    category="restaurant",
                    address="Cache Street 123",
                    confidence=0.9,
                ),
                confidence=0.9,
                analysis_time=1.0,  # Slower analysis
                model_version="gemini",
                error=None,
            )

            mock_extractor_instance = mock_extractor.return_value
            mock_extractor_instance.extract_content.return_value = mock_content

            mock_analysis_instance = mock_analysis.return_value
            mock_analysis_instance.analyze_content.return_value = mock_result

            mock_cache_instance = mock_cache.return_value
            mock_cache_instance.get.return_value = None  # No cache
            mock_cache_instance.initialize.return_value = None
            mock_cache_instance.close.return_value = None

            # First request (no cache)
            start_time = time.time()
            response1 = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cache_perf_test/"},
            )
            uncached_time = time.time() - start_time

            assert response1.status_code == 200
            assert response1.json()["cached"] is False

            # Setup cache hit for second request
            cached_data = {
                "place_info": mock_result.place_info.dict(),
                "confidence": mock_result.confidence,
                "analysis_time": mock_result.analysis_time,
                "content_metadata": {
                    "title": mock_content.title,
                    "description": mock_content.description,
                    "images": mock_content.images,
                    "extraction_time": mock_content.extraction_time,
                },
            }

            mock_cache_instance.get.return_value = cached_data

            # Second request (with cache)
            start_time = time.time()
            response2 = client.post(
                "/api/v1/links/analyze",
                json={"url": "https://instagram.com/p/cache_perf_test/"},
            )
            cached_time = time.time() - start_time

            assert response2.status_code == 200
            assert response2.json()["cached"] is True

            # Performance improvement calculation
            improvement_factor = uncached_time / cached_time
            improvement_percent = ((uncached_time - cached_time) / uncached_time) * 100

            print(f"\\nCache performance improvement:")
            print(f"  Uncached request time: {uncached_time:.3f}s")
            print(f"  Cached request time: {cached_time:.3f}s")
            print(f"  Improvement factor: {improvement_factor:.1f}x")
            print(f"  Improvement percentage: {improvement_percent:.1f}%")

            # Cache should provide significant improvement
            assert improvement_factor > 2.0  # At least 2x faster
            assert cached_time < 1.0  # Cached requests should be under 1s
