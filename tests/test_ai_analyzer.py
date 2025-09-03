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
