#!/usr/bin/env python3
"""
Tag Autocomplete Performance Tests

Tests for validating 100ms response time requirement for tag autocomplete system.
Follows TDD approach for Task 1-2-4: 태그 관리 및 자동완성 시스템 (100ms)
"""

import time
from unittest.mock import Mock
from uuid import uuid4

from app.services.utils.tag_service import TagService
from app.utils.tag_normalizer import TagNormalizer


class TestTagAutocompletePerformance:
    """
    Performance tests for tag autocomplete system.

    Validates that autocomplete responses meet 100ms requirement
    under various load conditions.
    """

    def setup_method(self):
        """Setup test data and mock database."""
        self.mock_db = Mock()
        self.tag_service = TagService(self.mock_db)

        # Performance threshold
        self.autocomplete_threshold_ms = 100  # 100ms requirement

        # Setup mock data for performance testing
        self._setup_mock_data()

    def _setup_mock_data(self):
        """Setup mock database responses for consistent performance testing."""
        # Mock common Korean tags for autocomplete testing
        self.common_korean_tags = [
            ("카페", 25),
            ("맛집", 22),
            ("한식", 18),
            ("치킨", 15),
            ("커피", 14),
            ("브런치", 12),
            ("디저트", 11),
            ("분식", 10),
            ("노래방", 9),
            ("술집", 8),
            ("백화점", 7),
            ("쇼핑", 6),
            ("관광", 5),
            ("문화", 4),
            ("전통", 3),
            ("역사", 2),
        ]

        # Setup mock query results
        def mock_query_side_effect(*args, **kwargs):
            mock_query = Mock()

            # Mock the chained query methods
            mock_query.filter.return_value = mock_query
            mock_query.group_by.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_query.limit.return_value = mock_query

            # Mock results based on tag data
            mock_results = []
            for tag, count in self.common_korean_tags:
                mock_result = Mock()
                mock_result.tag = tag
                mock_result.count = count
                mock_results.append(mock_result)

            mock_query.all.return_value = mock_results
            return mock_query

        self.mock_db.query.side_effect = mock_query_side_effect

    async def measure_autocomplete_time(self, query: str, user_id: str = None) -> tuple:
        """Measure tag autocomplete response time."""
        if user_id is None:
            user_id = uuid4()

        start_time = time.perf_counter()

        suggestions = self.tag_service.get_tag_suggestions(
            query=query, user_id=user_id, limit=10
        )

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        return execution_time_ms, suggestions

    def test_autocomplete_performance_commonQueries_under100ms(self):
        """
        Test: Common autocomplete queries complete under 100ms

        RED: This test validates current performance meets requirements
        """
        # Given: Common Korean search queries
        test_queries = [
            "카",  # Single character
            "카페",  # Common complete word
            "맛",  # Partial word
            "한식당",  # Complex query
            "커피숍",  # Another common term
            "치킨집",  # Korean-specific business
            "노래",  # Entertainment prefix
            "쇼핑몰",  # Shopping related
        ]

        performance_results = []

        # When: Execute autocomplete for each query
        for query in test_queries:
            execution_time_ms, suggestions = self.measure_autocomplete_time(query)

            performance_results.append(
                {
                    "query": query,
                    "time_ms": execution_time_ms,
                    "suggestion_count": len(suggestions),
                    "under_threshold": execution_time_ms
                    < self.autocomplete_threshold_ms,
                }
            )

            # Then: Should complete under 100ms
            assert (
                execution_time_ms < self.autocomplete_threshold_ms
            ), f"Autocomplete for '{query}' took {execution_time_ms:.1f}ms, expected < {self.autocomplete_threshold_ms}ms"

        # Print performance summary
        print("\n⚡ Tag Autocomplete Performance Results:")
        print(f"   Threshold: {self.autocomplete_threshold_ms}ms")

        total_time = sum(result["time_ms"] for result in performance_results)
        avg_time = total_time / len(performance_results)

        print(f"   Average response time: {avg_time:.1f}ms")
        print(f"   Total queries tested: {len(performance_results)}")

        for result in performance_results:
            status = "✅" if result["under_threshold"] else "❌"
            print(
                f"   {status} '{result['query']}': {result['time_ms']:.1f}ms "
                f"({result['suggestion_count']} suggestions)"
            )

        # All queries should meet threshold
        failed_queries = [r for r in performance_results if not r["under_threshold"]]
        assert (
            len(failed_queries) == 0
        ), f"{len(failed_queries)} queries exceeded threshold"

    def test_autocomplete_scalability_increasingDataSize_maintainPerformance(self):
        """
        Test: Autocomplete maintains performance as data size increases

        Simulates performance under different user tag collection sizes
        """
        # Given: Different user data sizes
        data_sizes = [10, 50, 100, 500, 1000]  # Number of user tags
        query = "카페"

        performance_by_size = []

        for size in data_sizes:
            # Mock larger dataset for this user
            large_dataset = self.common_korean_tags * (
                size // len(self.common_korean_tags) + 1
            )
            large_dataset = large_dataset[:size]

            # Update mock to return larger dataset
            def mock_large_query(*args, **kwargs):
                mock_query = Mock()
                mock_query.filter.return_value = mock_query
                mock_query.group_by.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_query.limit.return_value = mock_query

                mock_results = []
                for tag, count in large_dataset:
                    mock_result = Mock()
                    mock_result.tag = tag
                    mock_result.count = count
                    mock_results.append(mock_result)

                mock_query.all.return_value = mock_results
                return mock_query

            self.mock_db.query.side_effect = mock_large_query

            # When: Measure performance
            execution_time_ms, suggestions = self.measure_autocomplete_time(query)

            performance_by_size.append(
                {
                    "data_size": size,
                    "time_ms": execution_time_ms,
                    "suggestions": len(suggestions),
                }
            )

            # Then: Should still meet performance threshold
            assert (
                execution_time_ms < self.autocomplete_threshold_ms
            ), f"Performance degraded with {size} tags: {execution_time_ms:.1f}ms"

        print("\n📈 Scalability Test Results:")
        for result in performance_by_size:
            print(f"   {result['data_size']} tags: {result['time_ms']:.1f}ms")

        # Performance should not degrade significantly
        min_time = min(r["time_ms"] for r in performance_by_size)
        max_time = max(r["time_ms"] for r in performance_by_size)
        performance_ratio = max_time / min_time

        assert (
            performance_ratio < 3.0
        ), f"Performance degraded too much: {performance_ratio:.1f}x slower"

    def test_korean_text_normalization_performance_complexInputs_efficientProcessing(
        self,
    ):
        """
        Test: Korean text normalization performs efficiently

        Critical for Korean autocomplete performance
        """
        # Given: Complex Korean normalization cases
        korean_test_cases = [
            "한국 전통 음식점",  # Spaces and traditional terms
            "스타벅스@홍대입구역",  # Mixed Korean/English with symbols
            "치킨&맥주 전문점!!!",  # Special characters
            "파리바게뜨 (베이커리)",  # Parentheses and brand names
            "24시 편의점/마트",  # Numbers and slashes
        ]

        normalizer = TagNormalizer()

        for test_input in korean_test_cases:
            # When: Normalize Korean text
            start_time = time.perf_counter()

            normalized = normalizer.normalize_tag(test_input)

            end_time = time.perf_counter()
            normalization_time_ms = (end_time - start_time) * 1000

            # Then: Should normalize quickly (well under 100ms)
            assert (
                normalization_time_ms < 10
            ), f"Korean normalization too slow for '{test_input}': {normalization_time_ms:.2f}ms"

            print(
                f"   ✅ '{test_input}' → '{normalized}' ({normalization_time_ms:.2f}ms)"
            )

    def test_concurrent_autocomplete_requests_multipleUsers_noPerformanceDegradation(
        self,
    ):
        """
        Test: Concurrent autocomplete requests maintain performance

        Simulates multiple users using autocomplete simultaneously
        """
        import concurrent.futures

        # Given: Multiple concurrent requests
        num_concurrent_requests = 10
        test_query = "맛집"

        def single_autocomplete_request():
            user_id = uuid4()
            execution_time_ms, suggestions = self.measure_autocomplete_time(
                test_query, user_id
            )
            return execution_time_ms

        # When: Execute concurrent requests
        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_concurrent_requests
        ) as executor:
            futures = [
                executor.submit(single_autocomplete_request)
                for _ in range(num_concurrent_requests)
            ]

            execution_times = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        total_time = time.perf_counter() - start_time

        # Then: All requests should meet performance threshold
        max_time = max(execution_times)
        avg_time = sum(execution_times) / len(execution_times)

        print("\n🔄 Concurrent Request Results:")
        print(f"   Concurrent requests: {num_concurrent_requests}")
        print(f"   Total time: {total_time * 1000:.1f}ms")
        print(f"   Average per request: {avg_time:.1f}ms")
        print(f"   Slowest request: {max_time:.1f}ms")

        assert (
            max_time < self.autocomplete_threshold_ms
        ), f"Slowest concurrent request took {max_time:.1f}ms, expected < {self.autocomplete_threshold_ms}ms"

        # Total time should be reasonable (not just sequential)
        expected_sequential_time = num_concurrent_requests * avg_time
        concurrency_improvement = expected_sequential_time / (total_time * 1000)

        assert (
            concurrency_improvement > 2.0
        ), f"Poor concurrency: only {concurrency_improvement:.1f}x improvement"

    def test_edge_case_performance_emptyAndSpecialInputs_robustHandling(self):
        """
        Test: Edge cases are handled efficiently without performance impact

        Tests autocomplete with problematic inputs
        """
        # Given: Edge case inputs
        edge_cases = [
            "",  # Empty string
            " ",  # Whitespace only
            "a",  # Single character
            "ㄱㄴㄷ",  # Korean consonants only
            "123",  # Numbers only
            "!@#$%",  # Special characters only
            "a" * 100,  # Very long input
        ]

        for edge_input in edge_cases:
            # When: Process edge case
            execution_time_ms, suggestions = self.measure_autocomplete_time(edge_input)

            # Then: Should handle gracefully and quickly
            assert (
                execution_time_ms < 50
            ), f"Edge case '{edge_input}' took too long: {execution_time_ms:.1f}ms"

            # Should return appropriate response (empty or fallback)
            assert isinstance(
                suggestions, list
            ), f"Invalid response type for '{edge_input}'"

            print(f"   ✅ Edge case '{edge_input}' handled in {execution_time_ms:.1f}ms")

    def test_caching_effectiveness_repeatedQueries_improvedPerformance(self):
        """
        Test: Repeated queries benefit from caching (if implemented)

        Measures performance improvement on repeated autocomplete requests
        """
        # Given: Same query repeated multiple times
        query = "한식"
        num_repeats = 5

        execution_times = []

        # When: Execute same query multiple times
        for i in range(num_repeats):
            execution_time_ms, suggestions = self.measure_autocomplete_time(query)
            execution_times.append(execution_time_ms)

        # Then: Later queries should be as fast or faster
        first_time = execution_times[0]
        avg_later_time = sum(execution_times[1:]) / len(execution_times[1:])

        print("\n🔄 Caching Test Results:")
        print(f"   First query: {first_time:.1f}ms")
        print(f"   Average later queries: {avg_later_time:.1f}ms")

        # All queries should still meet threshold regardless
        max_time = max(execution_times)
        assert (
            max_time < self.autocomplete_threshold_ms
        ), f"Repeated query exceeded threshold: {max_time:.1f}ms"
