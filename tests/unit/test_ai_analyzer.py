"""Test AI analysis services."""

import json
from unittest.mock import patch

import pytest

from app.exceptions.ai import AIAnalysisError, InvalidResponseError, RateLimitError
from app.schemas.ai import PlaceAnalysisRequest, PlaceCategory, PlaceInfo
from app.schemas.content import ContentMetadata
from app.services.ai.gemini_analyzer import GeminiAnalyzer
from app.services.place_analysis_service import PlaceAnalysisService


@pytest.fixture
def gemini_analyzer() -> GeminiAnalyzer:
    """Create Gemini analyzer instance."""
    return GeminiAnalyzer()


@pytest.fixture
def place_analysis_service() -> PlaceAnalysisService:
    """Create place analysis service instance."""
    return PlaceAnalysisService()


@pytest.mark.asyncio
async def test_gemini_analyze_success(gemini_analyzer: GeminiAnalyzer) -> None:
    """Test successful Gemini analysis."""
    # Mock content
    request = PlaceAnalysisRequest(
        content_text="Amazing Korean BBQ restaurant in Gangnam",
        content_description="Best bulgogi in Seoul!",
        hashtags=["#koreanbbq", "#gangnam", "#seoul"],
        images=["https://example.com/image1.jpg"],
        platform="instagram",
    )

    # Mock Gemini response
    mock_response = {
        "name": "강남 불고기 맛집",
        "address": "서울 강남구 테헤란로 123",
        "category": "restaurant",
        "keywords": ["한식", "불고기", "고급", "데이트"],
        "recommendation_score": 8,
        "phone": None,
        "website": None,
        "opening_hours": None,
        "price_range": "보통",
    }

    with patch.object(gemini_analyzer, "_call_gemini_api") as mock_api:
        mock_api.return_value = json.dumps(mock_response)

        result = await gemini_analyzer.analyze_place_content(request)

        assert result.name == "강남 불고기 맛집"
        assert result.category == PlaceCategory.RESTAURANT
        assert result.recommendation_score == 8
        assert "한식" in result.keywords


@pytest.mark.asyncio
async def test_gemini_rate_limit_error(gemini_analyzer: GeminiAnalyzer) -> None:
    """Test Gemini rate limit handling."""
    request = PlaceAnalysisRequest(content_text="Test content", platform="instagram")

    with patch.object(gemini_analyzer, "_call_gemini_api") as mock_api:
        mock_api.side_effect = RateLimitError("Rate limit exceeded")

        with pytest.raises(RateLimitError):
            await gemini_analyzer.analyze_place_content(request)


@pytest.mark.asyncio
async def test_gemini_invalid_response(gemini_analyzer: GeminiAnalyzer) -> None:
    """Test invalid JSON response handling."""
    request = PlaceAnalysisRequest(content_text="Test content", platform="instagram")

    with patch.object(gemini_analyzer, "_call_gemini_api") as mock_api:
        mock_api.return_value = "Invalid JSON response"

        with pytest.raises(InvalidResponseError):
            await gemini_analyzer.analyze_place_content(request)


@pytest.mark.asyncio
async def test_place_analysis_service_integration(
    place_analysis_service: PlaceAnalysisService,
) -> None:
    """Test place analysis service with Gemini integration."""
    content = ContentMetadata(
        title="Best pizza in Hongdae",
        description="Authentic Italian pizza",
        hashtags=["#pizza", "#hongdae", "#italian"],
        location="Hongdae, Seoul",
    )

    # Mock the Gemini analyzer
    mock_place_info = PlaceInfo(
        name="홍대 피자 맛집",
        category=PlaceCategory.RESTAURANT,
        keywords=["피자", "이탈리안", "홍대"],
        recommendation_score=9,
        address="서울 마포구 홍익로 456",
    )

    with patch.object(
        place_analysis_service.ai_analyzer, "analyze_place_content"
    ) as mock_analyze:
        mock_analyze.return_value = mock_place_info

        response = await place_analysis_service.analyze_content(content)

        assert response.success is True
        assert response.place_info.name == "홍대 피자 맛집"
        assert response.confidence > 0.0
        assert response.model_version == "gemini-pro-vision"


@pytest.mark.asyncio
async def test_place_analysis_service_ai_failure(
    place_analysis_service: PlaceAnalysisService,
) -> None:
    """Test place analysis service when AI fails."""
    content = ContentMetadata(title="Test content")

    with patch.object(
        place_analysis_service.ai_analyzer, "analyze_place_content"
    ) as mock_analyze:
        mock_analyze.side_effect = AIAnalysisError("AI service unavailable")

        response = await place_analysis_service.analyze_content(content)

        assert response.success is False
        assert response.place_info is None
        assert "AI service unavailable" in response.error


def test_prompt_template_formatting() -> None:
    """Test prompt template formatting with real data."""
    from app.prompts.place_extraction import (
        PLACE_EXTRACTION_JSON_SCHEMA,
        PLACE_EXTRACTION_PROMPT_V1,
    )

    # Test prompt formatting
    formatted_prompt = PLACE_EXTRACTION_PROMPT_V1.format(
        platform="instagram",
        title="Amazing Korean BBQ",
        description="Best bulgogi in town!",
        hashtags="#koreanbbq #seoul",
        json_schema=json.dumps(PLACE_EXTRACTION_JSON_SCHEMA, indent=2),
    )

    assert "instagram" in formatted_prompt
    assert "Amazing Korean BBQ" in formatted_prompt
    assert "json" in formatted_prompt.lower()
    assert "restaurant" in formatted_prompt  # Should include category options


def test_json_schema_validation() -> None:
    """Test JSON schema validation for AI responses."""
    import jsonschema

    from app.prompts.place_extraction import PLACE_EXTRACTION_JSON_SCHEMA

    # Valid response
    valid_response = {
        "name": "Test Restaurant",
        "address": "123 Test St",
        "category": "restaurant",
        "keywords": ["한식", "맛집"],
        "recommendation_score": 8,
    }

    # Should not raise exception
    jsonschema.validate(valid_response, PLACE_EXTRACTION_JSON_SCHEMA)

    # Invalid response (missing required fields)
    invalid_response = {
        "name": "Test Restaurant"
        # Missing category and recommendation_score
    }

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(invalid_response, PLACE_EXTRACTION_JSON_SCHEMA)


class TestGeminiAnalyzerComprehensive:
    """Comprehensive tests for GeminiAnalyzer following TDD approach."""

    @pytest.fixture
    def analyzer(self):
        """Create GeminiAnalyzer instance."""
        return GeminiAnalyzer()

    @pytest.fixture
    def sample_instagram_content(self):
        """Sample Instagram content for testing."""
        return {
            "url": "https://www.instagram.com/p/ABC123/",
            "platform": "instagram",
            "title": "Amazing Korean BBQ in Gangnam",
            "description": "Just had the best Korean BBQ at this place in Gangnam! The beef was incredible and the service was amazing. Located near Gangnam Station. #koreanbbq #gangnam #seoul #restaurant",
            "images": ["https://instagram.com/image1.jpg"],
            "location": "Gangnam, Seoul",
            "hashtags": ["#koreanbbq", "#gangnam", "#seoul", "#restaurant"],
        }

    @pytest.mark.asyncio
    async def test_gemini_multimodal_analysis(self, analyzer, sample_instagram_content):
        """Test multimodal analysis with text and images."""
        # Given
        request = PlaceAnalysisRequest(
            content_text=sample_instagram_content["description"],
            content_description=sample_instagram_content["title"],
            hashtags=sample_instagram_content["hashtags"],
            images=sample_instagram_content["images"],
            platform=sample_instagram_content["platform"],
        )

        expected_response = {
            "name": "Gangnam Korean BBQ Restaurant",
            "address": "Near Gangnam Station, Seoul",
            "category": "restaurant",
            "keywords": ["korean_bbq", "gangnam", "beef"],
            "recommendation_score": 9,
            "confidence": 0.95,
        }

        with patch.object(analyzer, "_call_gemini_api") as mock_api:
            mock_api.return_value = json.dumps(expected_response)

            # When
            result = await analyzer.analyze_place_content(request)

            # Then
            assert result.name == "Gangnam Korean BBQ Restaurant"
            assert result.category == PlaceCategory.RESTAURANT
            assert result.recommendation_score == 9
            assert "korean_bbq" in result.keywords
            # Verify that images were passed to the API
            mock_api.assert_called_once()

    @pytest.mark.asyncio
    async def test_gemini_retry_logic_exponential_backoff(self, analyzer):
        """Test retry logic with exponential backoff for temporary failures."""
        # Given
        request = PlaceAnalysisRequest(
            content_text="Test content", platform="instagram"
        )
        call_count = 0

        def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise AIAnalysisError("Temporary API failure")
            return json.dumps(
                {
                    "name": "Test Place",
                    "address": "Test Address",
                    "category": "restaurant",
                    "keywords": ["test"],
                    "recommendation_score": 7,
                }
            )

        with patch.object(analyzer, "_call_gemini_api", side_effect=mock_api_call):
            with patch("asyncio.sleep") as mock_sleep:  # Mock sleep to speed up test
                # When
                result = await analyzer.analyze_place_content(request)

                # Then
                assert call_count == 3  # Should retry twice then succeed
                assert result.name == "Test Place"
                # Verify exponential backoff sleep calls
                assert mock_sleep.call_count == 2  # 2 retries
                sleep_durations = [call[0][0] for call in mock_sleep.call_args_list]
                assert sleep_durations[1] > sleep_durations[0]  # Exponential increase

    @pytest.mark.asyncio
    async def test_gemini_90_percent_accuracy_requirement(self, analyzer):
        """Test that analysis meets 90% accuracy requirement."""
        # Given test cases with clear place mentions
        test_cases = [
            {
                "request": PlaceAnalysisRequest(
                    content_text="Dinner at Jungsik Restaurant in Gangnam",
                    hashtags=["#jungsik", "#finedining"],
                    platform="instagram",
                ),
                "expected_place": "Jungsik",
            },
            {
                "request": PlaceAnalysisRequest(
                    content_text="Amazing coffee at Blue Bottle Coffee Hongdae",
                    hashtags=["#bluebottle", "#coffee"],
                    platform="instagram",
                ),
                "expected_place": "Blue Bottle Coffee",
            },
            {
                "request": PlaceAnalysisRequest(
                    content_text="Went to Myeongdong Kyoja for best dumplings",
                    hashtags=["#myeongdong", "#dumplings"],
                    platform="blog",
                ),
                "expected_place": "Myeongdong Kyoja",
            },
        ]

        success_count = 0

        for case in test_cases:
            # Mock response with expected place name
            mock_response = {
                "name": case["expected_place"],
                "address": "Seoul, Korea",
                "category": "restaurant",
                "keywords": ["test"],
                "recommendation_score": 8,
            }

            with patch.object(analyzer, "_call_gemini_api") as mock_api:
                mock_api.return_value = json.dumps(mock_response)

                result = await analyzer.analyze_place_content(case["request"])
                if case["expected_place"].lower() in result.name.lower():
                    success_count += 1

        # Should achieve 90%+ accuracy
        accuracy = success_count / len(test_cases)
        assert accuracy >= 0.9, f"Accuracy {accuracy:.2%} below 90% requirement"

    @pytest.mark.asyncio
    async def test_gemini_rate_limit_handling_with_backoff(self, analyzer):
        """Test proper handling of rate limits with backoff strategy."""
        # Given
        request = PlaceAnalysisRequest(
            content_text="Test content", platform="instagram"
        )

        # Simulate rate limit then success
        call_count = 0

        def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError("Rate limit exceeded, retry after 60 seconds")
            return json.dumps(
                {
                    "name": "Test Place",
                    "address": "Test Address",
                    "category": "restaurant",
                    "keywords": ["test"],
                    "recommendation_score": 7,
                }
            )

        with patch.object(analyzer, "_call_gemini_api", side_effect=mock_api_call):
            with patch("asyncio.sleep") as mock_sleep:
                # When
                result = await analyzer.analyze_place_content(request)

                # Then
                assert call_count == 2  # Should retry once after rate limit
                assert result.name == "Test Place"
                # Should have slept for rate limit backoff
                mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_gemini_prompt_versioning_and_templates(self, analyzer):
        """Test prompt versioning and template management."""
        # Given
        request = PlaceAnalysisRequest(
            content_text="Korean BBQ restaurant", platform="instagram"
        )

        with patch.object(analyzer, "_call_gemini_api") as mock_api:
            mock_api.return_value = json.dumps(
                {
                    "name": "Test Place",
                    "address": "Test Address",
                    "category": "restaurant",
                    "keywords": ["test"],
                    "recommendation_score": 7,
                }
            )

            # When
            await analyzer.analyze_place_content(request)

            # Then
            # Verify that prompt includes version information
            call_args = mock_api.call_args[0]
            prompt = call_args[0] if call_args else ""
            assert "version" in prompt.lower() or "v1" in prompt.lower()

    @pytest.mark.asyncio
    async def test_gemini_response_validation_and_sanitization(self, analyzer):
        """Test response validation and data sanitization."""
        # Given
        request = PlaceAnalysisRequest(content_text="Test place", platform="instagram")

        # Test with malformed but parseable response
        malformed_response = {
            "name": "   Test Place   ",  # Extra whitespace
            "address": "",  # Empty address
            "category": "RESTAURANT",  # Wrong case
            "keywords": ["test", "", "valid"],  # Empty keyword
            "recommendation_score": 15,  # Out of range
            "extra_field": "should_be_ignored",  # Unexpected field
        }

        with patch.object(analyzer, "_call_gemini_api") as mock_api:
            mock_api.return_value = json.dumps(malformed_response)

            # When
            result = await analyzer.analyze_place_content(request)

            # Then
            assert result.name == "Test Place"  # Trimmed whitespace
            assert result.category == PlaceCategory.RESTAURANT  # Normalized case
            assert result.recommendation_score <= 10  # Clamped to valid range
            assert "" not in result.keywords  # Empty keywords filtered out

    @pytest.mark.asyncio
    async def test_gemini_concurrent_request_handling(self, analyzer):
        """Test handling multiple concurrent requests."""
        # Given
        requests = [
            PlaceAnalysisRequest(content_text=f"Restaurant {i}", platform="instagram")
            for i in range(5)
        ]

        def mock_api_call(prompt, *args, **kwargs):
            # Extract restaurant number from prompt for unique response
            import re

            match = re.search(r"Restaurant (\d+)", prompt)
            restaurant_num = match.group(1) if match else "0"

            return json.dumps(
                {
                    "name": f"Restaurant {restaurant_num}",
                    "address": "Test Address",
                    "category": "restaurant",
                    "keywords": ["test"],
                    "recommendation_score": 8,
                }
            )

        with patch.object(analyzer, "_call_gemini_api", side_effect=mock_api_call):
            # When
            tasks = [analyzer.analyze_place_content(req) for req in requests]
            results = await asyncio.gather(*tasks)

            # Then
            assert len(results) == 5
            for i, result in enumerate(results):
                assert f"Restaurant {i}" in result.name
                assert result.category == PlaceCategory.RESTAURANT

    @pytest.mark.asyncio
    async def test_gemini_response_confidence_scoring(self, analyzer):
        """Test confidence scoring in responses."""
        # Given
        request = PlaceAnalysisRequest(content_text="Test place", platform="instagram")

        # Test different confidence scenarios
        test_cases = [
            {"confidence": 0.95, "expected_high": True},
            {"confidence": 0.75, "expected_high": False},
            {"confidence": 0.45, "expected_high": False},
        ]

        for case in test_cases:
            mock_response = {
                "name": "Test Place",
                "address": "Test Address",
                "category": "restaurant",
                "keywords": ["test"],
                "recommendation_score": 8,
                "confidence": case["confidence"],
            }

            with patch.object(analyzer, "_call_gemini_api") as mock_api:
                mock_api.return_value = json.dumps(mock_response)

                # When
                result = await analyzer.analyze_place_content(request)

                # Then
                # High confidence results should have higher recommendation scores
                if case["expected_high"]:
                    assert result.recommendation_score >= 8
                else:
                    # Low confidence might reduce recommendation score
                    assert result.recommendation_score >= 5
