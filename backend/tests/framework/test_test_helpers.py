"""
Tests for the testing framework utilities.

Meta-tests that verify the test infrastructure itself works correctly.
These tests ensure our testing utilities and helpers are reliable.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from tests.utils.test_helpers import (
    SAMPLE_PLACES,
    TEST_URLS,
    AsyncTestHelpers,
    MockFactory,
    MockServiceFactory,
    PerformanceTestHelpers,
    TestDataBuilder,
    ValidationHelpers,
)

from app.schemas.ai import PlaceInfo
from app.schemas.content import ContentExtractResult
from app.services.places.place_analysis_service import PlaceAnalysisResult


class TestMockFactory:
    """Test the MockFactory utility class."""

    def test_create_content_extract_result_defaultValues_returnsValidObject(self):
        """Test MockFactory creates valid ContentExtractResult with defaults."""
        # When
        result = MockFactory.create_content_extract_result()

        # Then
        assert isinstance(result, ContentExtractResult)
        assert result.url == "https://instagram.com/p/test123/"
        assert result.title == "Test Restaurant Post"
        assert result.platform == "instagram"
        assert result.success is True
        assert result.extraction_time > 0
        assert isinstance(result.images, list)
        assert isinstance(result.hashtags, list)

    def test_create_content_extract_result_customValues_usesCustomValues(self):
        """Test MockFactory respects custom values."""
        # Given
        custom_url = "https://instagram.com/p/custom/"
        custom_title = "Custom Restaurant"

        # When
        result = MockFactory.create_content_extract_result(
            url=custom_url, title=custom_title, extraction_time=1.5
        )

        # Then
        assert result.url == custom_url
        assert result.title == custom_title
        assert result.extraction_time == 1.5

    def test_create_place_info_defaultValues_returnsValidObject(self):
        """Test MockFactory creates valid PlaceInfo with defaults."""
        # When
        place_info = MockFactory.create_place_info()

        # Then
        assert isinstance(place_info, PlaceInfo)
        assert place_info.name == "Test Restaurant"
        assert place_info.category == "restaurant"
        assert place_info.confidence == 0.85
        assert place_info.address is not None
        assert isinstance(place_info.keywords, list)

    def test_create_place_analysis_result_successScenario_returnsValidResult(self):
        """Test MockFactory creates valid successful analysis result."""
        # When
        result = MockFactory.create_place_analysis_result(success=True)

        # Then
        assert isinstance(result, PlaceAnalysisResult)
        assert result.success is True
        assert result.place_info is not None
        assert result.confidence > 0
        assert result.analysis_time > 0
        assert result.error is None

    def test_create_place_analysis_result_failureScenario_returnsValidError(self):
        """Test MockFactory creates valid failure result."""
        # When
        result = MockFactory.create_place_analysis_result(
            success=False, error="Test error message"
        )

        # Then
        assert result.success is False
        assert result.place_info is None
        assert result.confidence == 0.0
        assert result.error == "Test error message"


class TestTestDataBuilder:
    """Test the TestDataBuilder utility class."""

    def test_builder_reset_clearsState(self):
        """Test builder reset functionality."""
        # Given
        builder = TestDataBuilder()
        builder.with_high_quality_content()

        # When
        builder.reset()
        new_result = builder.build_content_result()

        # Then
        assert (
            new_result.title
            != "Michelin-starred Korean Restaurant - Exceptional Dining Experience"
        )

    def test_builder_high_quality_content_setsQualityData(self):
        """Test builder creates high-quality content scenario."""
        # Given
        builder = TestDataBuilder()

        # When
        result = builder.with_high_quality_content().build_content_result()

        # Then
        assert "Michelin" in result.title
        assert len(result.description) > 100
        assert len(result.images) >= 3

    def test_builder_low_quality_content_setsLowQualityData(self):
        """Test builder creates low-quality content scenario."""
        # Given
        builder = TestDataBuilder()

        # When
        result = builder.with_low_quality_content().build_content_result()

        # Then
        assert result.title == "Food"
        assert result.description == "Ate something #food"
        assert len(result.images) == 0

    def test_builder_korean_bbq_content_setsSpecificData(self):
        """Test builder creates Korean BBQ specific content."""
        # Given
        builder = TestDataBuilder()

        # When
        result = builder.with_korean_bbq_content().build_content_result()

        # Then
        assert "Korean BBQ" in result.title
        assert "gangnam" in result.description.lower()
        assert "korean" in [tag.lower() for tag in result.hashtags]

    def test_builder_error_scenario_setsErrorData(self):
        """Test builder creates error scenarios."""
        # Given
        builder = TestDataBuilder()

        # When
        result = builder.with_error_scenario("ai_analysis").build_analysis_result()

        # Then
        assert result.success is False
        assert "AI service temporarily unavailable" in result.error
        assert result.confidence == 0.0

    def test_builder_chaining_allowsMultipleConfigurations(self):
        """Test builder method chaining works correctly."""
        # Given
        builder = TestDataBuilder()

        # When
        result = builder.with_cafe_content().build_place_info()

        # Then
        assert result.category == "cafe"
        assert "cafe" in [kw.lower() for kw in result.keywords]


class TestAsyncTestHelpers:
    """Test the AsyncTestHelpers utility class."""

    @pytest.mark.asyncio
    async def test_run_with_timeout_successfulOperation_returnsResult(self):
        """Test timeout helper with successful operation."""

        # Given
        async def quick_operation():
            await asyncio.sleep(0.1)
            return "success"

        # When
        result = await AsyncTestHelpers.run_with_timeout(quick_operation(), timeout=1.0)

        # Then
        assert result == "success"

    @pytest.mark.asyncio
    async def test_run_with_timeout_slowOperation_raisesTimeoutError(self):
        """Test timeout helper with slow operation."""

        # Given
        async def slow_operation():
            await asyncio.sleep(2.0)
            return "too slow"

        # When/Then
        with pytest.raises(AssertionError) as exc_info:
            await AsyncTestHelpers.run_with_timeout(slow_operation(), timeout=0.5)

        assert "timed out after 0.5 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_simulate_slow_operation_addsDelay(self):
        """Test slow operation simulation."""
        # Given
        start_time = asyncio.get_event_loop().time()

        # When
        result = await AsyncTestHelpers.simulate_slow_operation("test", delay=0.1)
        end_time = asyncio.get_event_loop().time()

        # Then
        assert result == "test"
        assert (end_time - start_time) >= 0.1

    def test_create_async_mock_withReturnValue_createsValidMock(self):
        """Test async mock creation with return value."""
        # When
        mock = AsyncTestHelpers.create_async_mock(return_value="test_value")

        # Then
        assert isinstance(mock, AsyncMock)
        # Note: Actual async call would need to be tested in async context

    def test_create_async_mock_withSideEffect_createsValidMock(self):
        """Test async mock creation with side effect."""
        # When
        mock = AsyncTestHelpers.create_async_mock(side_effect=Exception("test error"))

        # Then
        assert isinstance(mock, AsyncMock)


class TestMockServiceFactory:
    """Test the MockServiceFactory utility class."""

    def test_create_content_extractor_mock_successScenario_returnsValidMock(self):
        """Test content extractor mock creation for success scenario."""
        # When
        mock = MockServiceFactory.create_content_extractor_mock(success=True)

        # Then
        assert hasattr(mock, "extract_content")
        assert isinstance(mock.extract_content, AsyncMock)

    def test_create_content_extractor_mock_failureScenario_returnsErrorMock(self):
        """Test content extractor mock creation for failure scenario."""
        # When
        mock = MockServiceFactory.create_content_extractor_mock(success=False)

        # Then
        assert hasattr(mock, "extract_content")
        assert isinstance(mock.extract_content, AsyncMock)

    def test_create_analysis_service_mock_successScenario_returnsValidMock(self):
        """Test analysis service mock creation for success scenario."""
        # When
        mock = MockServiceFactory.create_analysis_service_mock(
            success=True, confidence=0.9
        )

        # Then
        assert hasattr(mock, "analyze_content")
        assert isinstance(mock.analyze_content, AsyncMock)

    def test_create_cache_manager_mock_cacheHit_returnsHitMock(self):
        """Test cache manager mock creation for cache hit scenario."""
        # Given
        test_data = {"key": "value"}

        # When
        mock = MockServiceFactory.create_cache_manager_mock(
            cache_hit=True, cached_data=test_data
        )

        # Then
        assert hasattr(mock, "get")
        assert hasattr(mock, "set")
        assert hasattr(mock, "initialize")
        assert hasattr(mock, "close")

    def test_create_cache_manager_mock_cacheMiss_returnsMissMock(self):
        """Test cache manager mock creation for cache miss scenario."""
        # When
        mock = MockServiceFactory.create_cache_manager_mock(cache_hit=False)

        # Then
        assert hasattr(mock, "get")
        assert hasattr(mock, "set")


class TestPerformanceTestHelpers:
    """Test the PerformanceTestHelpers utility class."""

    @pytest.mark.asyncio
    async def test_measure_execution_time_returnsTimeAndResult(self):
        """Test execution time measurement."""

        # Given
        async def test_operation():
            await asyncio.sleep(0.1)
            return "completed"

        # When
        result, execution_time = await PerformanceTestHelpers.measure_execution_time(
            test_operation()
        )

        # Then
        assert result == "completed"
        assert execution_time >= 0.1
        assert execution_time < 0.2  # Should not be too slow

    def test_assert_performance_metrics_withinLimits_passes(self):
        """Test performance assertion with acceptable timing."""
        # When/Then - Should not raise exception
        PerformanceTestHelpers.assert_performance_metrics(
            execution_time=0.5, max_time=1.0, operation_name="Test Operation"
        )

    def test_assert_performance_metrics_exceedsLimits_raisesAssertion(self):
        """Test performance assertion with unacceptable timing."""
        # When/Then
        with pytest.raises(AssertionError) as exc_info:
            PerformanceTestHelpers.assert_performance_metrics(
                execution_time=2.0, max_time=1.0, operation_name="Slow Operation"
            )

        assert "Slow Operation took 2.000s, expected <= 1.0s" in str(exc_info.value)

    def test_create_load_test_data_createsValidData(self):
        """Test load test data creation."""
        # When
        test_data = PerformanceTestHelpers.create_load_test_data(count=10)

        # Then
        assert len(test_data) == 10
        assert all("url" in item for item in test_data)
        assert all("title" in item for item in test_data)
        assert all("expected_confidence" in item for item in test_data)

        # Verify confidence varies
        confidences = [item["expected_confidence"] for item in test_data]
        assert len(set(confidences)) > 1  # Should have different confidence values


class TestValidationHelpers:
    """Test the ValidationHelpers utility class."""

    def test_assert_valid_place_info_validData_passes(self):
        """Test place info validation with valid data."""
        # Given
        place_info = MockFactory.create_place_info(confidence=0.9)

        # When/Then - Should not raise exception
        ValidationHelpers.assert_valid_place_info(place_info, min_confidence=0.8)

    def test_assert_valid_place_info_lowConfidence_raisesAssertion(self):
        """Test place info validation with low confidence."""
        # Given
        place_info = MockFactory.create_place_info(confidence=0.5)

        # When/Then
        with pytest.raises(AssertionError):
            ValidationHelpers.assert_valid_place_info(place_info, min_confidence=0.8)

    def test_assert_valid_content_result_validData_passes(self):
        """Test content result validation with valid data."""
        # Given
        content = MockFactory.create_content_extract_result()

        # When/Then - Should not raise exception
        ValidationHelpers.assert_valid_content_result(content)

    def test_assert_valid_analysis_result_successResult_passes(self):
        """Test analysis result validation with successful result."""
        # Given
        result = MockFactory.create_place_analysis_result(success=True)

        # When/Then - Should not raise exception
        ValidationHelpers.assert_valid_analysis_result(result)

    def test_assert_valid_analysis_result_failureResult_passes(self):
        """Test analysis result validation with failure result."""
        # Given
        result = MockFactory.create_place_analysis_result(
            success=False, error="Test error"
        )

        # When/Then - Should not raise exception
        ValidationHelpers.assert_valid_analysis_result(result)

    def test_assert_api_response_structure_validResponse_passes(self):
        """Test API response structure validation."""
        # Given
        response_data = {
            "success": True,
            "status": "completed",
            "result": {"data": "test"},
        }
        expected_fields = ["success", "status", "result"]

        # When/Then - Should not raise exception
        ValidationHelpers.assert_api_response_structure(response_data, expected_fields)

    def test_assert_api_response_structure_missingField_raisesAssertion(self):
        """Test API response structure validation with missing field."""
        # Given
        response_data = {"success": True}
        expected_fields = ["success", "status", "result"]

        # When/Then
        with pytest.raises(AssertionError) as exc_info:
            ValidationHelpers.assert_api_response_structure(
                response_data, expected_fields
            )

        assert "Missing required field: status" in str(exc_info.value)

    def test_assert_datetime_format_validFormat_passes(self):
        """Test datetime format validation with valid format."""
        # Given
        valid_datetime = "2024-01-15T14:30:00Z"

        # When/Then - Should not raise exception
        ValidationHelpers.assert_datetime_format(valid_datetime)

    def test_assert_datetime_format_invalidFormat_raisesAssertion(self):
        """Test datetime format validation with invalid format."""
        # Given
        invalid_datetime = "not-a-datetime"

        # When/Then
        with pytest.raises(AssertionError) as exc_info:
            ValidationHelpers.assert_datetime_format(invalid_datetime)

        assert "Invalid datetime format" in str(exc_info.value)


class TestTestConstants:
    """Test the test data constants."""

    def test_test_urls_structure_isValid(self):
        """Test TEST_URLS constant has valid structure."""
        # Then
        assert isinstance(TEST_URLS, dict)
        assert "instagram" in TEST_URLS
        assert "naver_blog" in TEST_URLS
        assert "youtube" in TEST_URLS
        assert "unsupported" in TEST_URLS

        # Verify each category has URLs
        for category, urls in TEST_URLS.items():
            assert isinstance(urls, list)
            assert len(urls) > 0
            assert all(isinstance(url, str) for url in urls)

    def test_sample_places_structure_isValid(self):
        """Test SAMPLE_PLACES constant has valid structure."""
        # Then
        assert isinstance(SAMPLE_PLACES, dict)
        assert "korean_restaurant" in SAMPLE_PLACES
        assert "cafe" in SAMPLE_PLACES
        assert "fine_dining" in SAMPLE_PLACES

        # Verify each place has required fields
        required_fields = ["name", "category", "address", "keywords", "confidence"]
        for place_name, place_data in SAMPLE_PLACES.items():
            assert isinstance(place_data, dict)
            for field in required_fields:
                assert field in place_data


class TestFrameworkIntegration:
    """Test framework components work together correctly."""

    def test_mock_factory_with_builder_integration_worksCorrectly(self):
        """Test MockFactory and TestDataBuilder work together."""
        # Given
        builder = TestDataBuilder()

        # When
        content_result = builder.with_high_quality_content().build_content_result()
        place_info = MockFactory.create_place_info(confidence=0.95)

        # Then
        ValidationHelpers.assert_valid_content_result(content_result)
        ValidationHelpers.assert_valid_place_info(place_info, min_confidence=0.9)

    @pytest.mark.asyncio
    async def test_async_helpers_with_mock_services_integration_worksCorrectly(self):
        """Test AsyncTestHelpers work with mock services."""
        # Given
        mock_service = MockServiceFactory.create_analysis_service_mock(
            success=True, confidence=0.9
        )

        # When
        async def test_async_operation():
            # Simulate calling the mock service
            return "async operation completed"

        result = await AsyncTestHelpers.run_with_timeout(
            test_async_operation(), timeout=1.0
        )

        # Then
        assert result == "async operation completed"
        assert hasattr(mock_service, "analyze_content")

    def test_validation_helpers_with_test_data_integration_worksCorrectly(self):
        """Test ValidationHelpers work with test data constants."""
        # Given
        test_place = SAMPLE_PLACES["korean_restaurant"]
        place_info = MockFactory.create_place_info(**test_place)

        # When/Then - Should validate successfully
        ValidationHelpers.assert_valid_place_info(place_info, min_confidence=0.8)

    def test_framework_error_handling_gracefulFailure(self):
        """Test framework components handle errors gracefully."""
        # Given
        builder = TestDataBuilder()

        # When
        error_result = builder.with_error_scenario("network").build_analysis_result()

        # Then
        assert error_result.success is False
        assert error_result.error is not None
        ValidationHelpers.assert_valid_analysis_result(error_result)


class TestFrameworkPerformance:
    """Test performance characteristics of testing framework."""

    def test_mock_creation_performance_isAcceptable(self):
        """Test mock creation is fast enough for testing."""
        import time

        # When
        start_time = time.time()

        for _ in range(100):
            MockFactory.create_content_extract_result()
            MockFactory.create_place_info()
            MockFactory.create_place_analysis_result()

        end_time = time.time()
        execution_time = end_time - start_time

        # Then
        assert execution_time < 1.0  # Should create 300 mocks in under 1 second

    def test_builder_performance_isAcceptable(self):
        """Test builder pattern performance is acceptable."""
        import time

        # When
        start_time = time.time()

        builder = TestDataBuilder()
        for _ in range(50):
            (builder.reset().with_high_quality_content().build_content_result())

        end_time = time.time()
        execution_time = end_time - start_time

        # Then
        assert execution_time < 0.5  # Should build 50 objects in under 0.5 seconds


class TestFrameworkDocumentation:
    """Test framework components are properly documented."""

    def test_mock_factory_has_docstrings(self):
        """Test MockFactory methods have docstrings."""
        # Then
        assert MockFactory.create_content_extract_result.__doc__ is not None
        assert MockFactory.create_place_info.__doc__ is not None
        assert MockFactory.create_place_analysis_result.__doc__ is not None

    def test_test_data_builder_has_docstrings(self):
        """Test TestDataBuilder methods have docstrings."""
        # Then
        assert TestDataBuilder.with_high_quality_content.__doc__ is not None
        assert TestDataBuilder.with_korean_bbq_content.__doc__ is not None

    def test_helpers_have_docstrings(self):
        """Test helper classes have proper documentation."""
        # Then
        assert AsyncTestHelpers.run_with_timeout.__doc__ is not None
        assert PerformanceTestHelpers.measure_execution_time.__doc__ is not None
        assert ValidationHelpers.assert_valid_place_info.__doc__ is not None
