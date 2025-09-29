"""
Unit Test Template

Copy this template when creating new unit tests.
Follow the Red-Green-Refactor TDD cycle.

Naming Convention: test_methodName_condition_expectedResult
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest


class TestExampleService:
    """
    Template for unit testing a service class.

    Unit tests should:
    1. Test single methods/functions in isolation
    2. Mock all external dependencies
    3. Focus on business logic
    4. Be fast and reliable
    """

    # Setup and teardown
    def setup_method(self):
        """Setup before each test method."""
        self.mock_dependency = Mock()
        self.service = ExampleService(self.mock_dependency)

    def teardown_method(self):
        """Cleanup after each test method."""

    # Success path tests
    def test_process_data_validInput_returnsProcessedData(self):
        """
        Test the happy path with valid input.

        Template structure:
        1. Given (Arrange) - Set up test data and mocks
        2. When (Act) - Call the method under test
        3. Then (Assert) - Verify the results
        """
        # Given (Arrange)
        input_data = {"key": "value", "count": 5}
        expected_result = {"processed": True, "count": 5}

        # Setup mock dependencies
        self.mock_dependency.process.return_value = expected_result

        # When (Act)
        result = self.service.process_data(input_data)

        # Then (Assert)
        assert result == expected_result
        assert result["processed"] is True
        assert result["count"] == 5

        # Verify interactions with dependencies
        self.mock_dependency.process.assert_called_once_with(input_data)

    @pytest.mark.asyncio
    async def test_async_process_validInput_returnsResult(self):
        """Template for testing async methods."""
        # Given
        input_data = {"async_key": "async_value"}
        expected_result = {"async_processed": True}

        # Setup async mock
        self.mock_dependency.async_process = AsyncMock(return_value=expected_result)

        # When
        result = await self.service.async_process(input_data)

        # Then
        assert result == expected_result
        self.mock_dependency.async_process.assert_called_once_with(input_data)

    # Error handling tests
    def test_process_data_invalidInput_raisesValidationError(self):
        """Test error handling with invalid input."""
        # Given
        invalid_input = None

        # When/Then
        with pytest.raises(ValidationError) as exc_info:
            self.service.process_data(invalid_input)

        # Verify error details
        assert "Input data cannot be None" in str(exc_info.value)

    def test_process_data_dependencyFails_raisesServiceError(self):
        """Test error handling when dependency fails."""
        # Given
        input_data = {"key": "value"}
        self.mock_dependency.process.side_effect = ConnectionError(
            "Database unavailable"
        )

        # When/Then
        with pytest.raises(ServiceError) as exc_info:
            self.service.process_data(input_data)

        # Verify error propagation
        assert "Service temporarily unavailable" in str(exc_info.value)

    # Edge cases
    def test_process_data_emptyInput_returnsEmptyResult(self):
        """Test edge case with empty input."""
        # Given
        empty_input = {}
        expected_result = {"processed": True, "empty": True}
        self.mock_dependency.process.return_value = expected_result

        # When
        result = self.service.process_data(empty_input)

        # Then
        assert result["empty"] is True
        assert result["processed"] is True

    def test_process_data_largeInput_handlesCorrectly(self):
        """Test edge case with large input."""
        # Given
        large_input = {"items": list(range(10000))}
        expected_result = {"processed": True, "count": 10000}
        self.mock_dependency.process.return_value = expected_result

        # When
        result = self.service.process_data(large_input)

        # Then
        assert result["count"] == 10000

    # Parameterized tests
    @pytest.mark.parametrize(
        "input_value,expected",
        [
            ("valid_string", True),
            ("", False),
            (None, False),
            (123, False),
        ],
    )
    def test_validate_string_variousInputs_returnsExpectedResult(
        self, input_value, expected
    ):
        """Template for parameterized tests."""
        # When
        result = self.service.validate_string(input_value)

        # Then
        assert result == expected

    # Mock behavior verification
    def test_process_data_validInput_callsDependenciesInOrder(self):
        """Test that dependencies are called in the correct order."""
        # Given
        input_data = {"key": "value"}

        # Setup multiple mock dependencies
        self.service.validator = Mock()
        self.service.processor = Mock()
        self.service.notifier = Mock()

        # When
        self.service.process_data(input_data)

        # Then - verify call order
        calls = [
            self.service.validator.validate.call_args_list,
            self.service.processor.process.call_args_list,
            self.service.notifier.notify.call_args_list,
        ]

        # Verify each dependency was called once
        assert len(calls[0]) == 1  # validator called
        assert len(calls[1]) == 1  # processor called
        assert len(calls[2]) == 1  # notifier called

    # Context manager tests
    def test_with_context_validUsage_managesResourcesProperly(self):
        """Template for testing context managers."""
        # Given
        self.service.resource = Mock()

        # When
        with self.service.get_context() as context:
            context.do_something()

        # Then
        self.service.resource.acquire.assert_called_once()
        self.service.resource.release.assert_called_once()

    # Property tests
    def test_status_property_afterInitialization_returnsDefault(self):
        """Template for testing properties."""
        # When
        status = self.service.status

        # Then
        assert status == "initialized"

    def test_status_property_afterProcessing_returnsProcessing(self):
        """Test property state changes."""
        # Given
        self.service.process_data({"key": "value"})

        # When
        status = self.service.status

        # Then
        assert status == "processed"


class TestExampleFunction:
    """
    Template for unit testing standalone functions.
    """

    def test_calculate_discount_validInputs_returnsCorrectDiscount(self):
        """Test a pure function with valid inputs."""
        # Given
        price = 100.0
        discount_percentage = 10.0

        # When
        result = calculate_discount(price, discount_percentage)

        # Then
        assert result == 90.0

    def test_calculate_discount_zeroPrice_returnsZero(self):
        """Test edge case with zero price."""
        # Given
        price = 0.0
        discount_percentage = 10.0

        # When
        result = calculate_discount(price, discount_percentage)

        # Then
        assert result == 0.0

    def test_calculate_discount_negativeDiscount_raisesValueError(self):
        """Test error handling with invalid discount."""
        # Given
        price = 100.0
        discount_percentage = -5.0

        # When/Then
        with pytest.raises(ValueError) as exc_info:
            calculate_discount(price, discount_percentage)

        assert "Discount percentage cannot be negative" in str(exc_info.value)


# Test Fixtures for this module
@pytest.fixture
def sample_service_data():
    """Provide sample data for service tests."""
    return {
        "user_id": "test_user_123",
        "preferences": {"categories": ["restaurant", "cafe"], "budget": "medium"},
        "location": {"lat": 37.5665, "lng": 126.9780},
    }


@pytest.fixture
def mock_external_api():
    """Mock external API responses."""
    with patch("app.services.external_api.ExternalAPI") as mock:
        mock.return_value.get_data.return_value = {
            "status": "success",
            "data": {"key": "value"},
        }
        yield mock


# Example classes to test (these would be in your actual code)
class ExampleService:
    """Example service class for testing."""

    def __init__(self, dependency):
        self.dependency = dependency
        self.status = "initialized"

    def process_data(self, data):
        if data is None:
            raise ValidationError("Input data cannot be None")

        try:
            result = self.dependency.process(data)
            self.status = "processed"
            return result
        except ConnectionError as e:
            raise ServiceError("Service temporarily unavailable") from e

    async def async_process(self, data):
        return await self.dependency.async_process(data)

    def validate_string(self, value):
        return isinstance(value, str) and len(value) > 0


def calculate_discount(price, discount_percentage):
    """Example function for testing."""
    if discount_percentage < 0:
        raise ValueError("Discount percentage cannot be negative")

    return price * (1 - discount_percentage / 100)


class ValidationError(Exception):
    """Example validation exception."""


class ServiceError(Exception):
    """Example service exception."""
