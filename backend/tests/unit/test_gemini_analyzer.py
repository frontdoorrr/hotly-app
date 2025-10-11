"""Unit tests for Gemini AI Analyzer."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions.ai import (
    AIAnalysisError,
    AIServiceUnavailableError,
    InvalidResponseError,
    RateLimitError,
)
from app.schemas.ai import PlaceAnalysisRequest, PlaceInfo
from app.services.ai.gemini_analyzer import GeminiAnalyzer


class TestGeminiAnalyzer:
    """Test suite for GeminiAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create GeminiAnalyzer instance."""
        return GeminiAnalyzer()

    @pytest.fixture
    def sample_request(self):
        """Create sample analysis request."""
        return PlaceAnalysisRequest(
            platform="instagram",
            content_text="강남 최고 맛집! 파스타가 정말 맛있어요",
            content_description="분위기 좋은 이탈리안 레스토랑",
            hashtags=["강남맛집", "이탈리안", "파스타"],
            images=[],
        )

    @pytest.fixture
    def sample_gemini_response(self):
        """Sample valid Gemini JSON response."""
        return json.dumps(
            {
                "name": "라 파스타",
                "address": "서울시 강남구 테헤란로 123",
                "category": "restaurant",
                "keywords": ["이탈리안", "파스타", "분위기좋은"],
                "recommendation_score": 9,
                "phone": None,
                "website": None,
                "opening_hours": None,
                "price_range": "2-3만원",
            },
            ensure_ascii=False,
        )

    def test_initialization(self, analyzer):
        """Test GeminiAnalyzer initialization."""
        assert analyzer.model_name == "gemini-1.5-flash"
        assert analyzer.timeout == 60
        assert analyzer.max_retries == 3
        assert analyzer.base_delay == 1.0

    def test_format_prompt(self, analyzer, sample_request):
        """Test prompt formatting."""
        prompt = analyzer._format_prompt(sample_request)

        assert "instagram" in prompt
        assert "강남 최고 맛집" in prompt
        assert "이탈리안 레스토랑" in prompt
        assert "강남맛집 이탈리안 파스타" in prompt
        assert "JSON" in prompt

    @pytest.mark.asyncio
    async def test_parse_valid_response(self, analyzer, sample_gemini_response):
        """Test parsing valid Gemini response."""
        result = analyzer._parse_and_validate_response(sample_gemini_response)

        assert result["name"] == "라 파스타"
        assert result["category"] == "restaurant"
        assert result["recommendation_score"] == 9
        assert "이탈리안" in result["keywords"]

    @pytest.mark.asyncio
    @patch("app.services.ai.gemini_analyzer.genai.GenerativeModel")
    async def test_parse_response_with_markdown(self, mock_model_class, analyzer):
        """Test parsing response with markdown code blocks."""
        response_with_markdown = '''```json
{
    "name": "Test Place",
    "address": null,
    "category": "cafe",
    "keywords": ["cozy"],
    "recommendation_score": 7
}
```'''

        # Mock the Gemini model to return markdown response
        mock_response = MagicMock()
        mock_response.text = response_with_markdown

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        with patch("app.services.ai.gemini_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            # Call the actual method which should clean up markdown
            result = await analyzer._call_gemini_api("test", [])

            # The method should clean up markdown
            assert not result.startswith("```")
            assert not result.endswith("```")
            assert "Test Place" in result

    @pytest.mark.asyncio
    async def test_invalid_json_response(self, analyzer):
        """Test handling of invalid JSON response."""
        with pytest.raises(InvalidResponseError):
            analyzer._parse_and_validate_response("This is not JSON")

    @pytest.mark.asyncio
    async def test_schema_validation_failure(self, analyzer):
        """Test handling of response that doesn't match schema."""
        invalid_response = json.dumps(
            {
                "name": "Test",
                # Missing required fields: category, recommendation_score, keywords
            }
        )

        with pytest.raises(InvalidResponseError):
            analyzer._parse_and_validate_response(invalid_response)

    @pytest.mark.asyncio
    async def test_api_key_not_configured(self):
        """Test error when API key is not set."""
        with patch("app.services.ai.gemini_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = None

            analyzer = GeminiAnalyzer()

            with pytest.raises(AIServiceUnavailableError, match="API key not configured"):
                await analyzer._call_gemini_api("test prompt", [])

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, analyzer):
        """Test retry mechanism on rate limit error."""
        with patch.object(analyzer, "_call_gemini_api") as mock_call:
            # Simulate rate limit on first 2 attempts, success on 3rd
            mock_call.side_effect = [
                RateLimitError("Rate limit"),
                RateLimitError("Rate limit"),
                "success",
            ]

            # Should succeed after retries
            result = await analyzer._call_gemini_api_with_retry("test", [])
            assert result == "success"
            assert mock_call.call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, analyzer):
        """Test failure when max retries are exceeded."""
        with patch.object(analyzer, "_call_gemini_api") as mock_call:
            # Always fail with rate limit
            mock_call.side_effect = RateLimitError("Rate limit")

            with pytest.raises(RateLimitError):
                await analyzer._call_gemini_api_with_retry("test", [])

            assert mock_call.call_count == analyzer.max_retries

    @pytest.mark.asyncio
    @patch("app.services.ai.gemini_analyzer.genai.GenerativeModel")
    async def test_successful_api_call(
        self, mock_model_class, analyzer, sample_gemini_response
    ):
        """Test successful Gemini API call."""
        # Mock the Gemini model response
        mock_response = MagicMock()
        mock_response.text = sample_gemini_response

        mock_model = MagicMock()
        mock_model.generate_content = MagicMock(return_value=mock_response)
        mock_model_class.return_value = mock_model

        # Mock settings to have API key
        with patch("app.services.ai.gemini_analyzer.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = "test-key"

            result = await analyzer._call_gemini_api("test prompt", [])

            assert "라 파스타" in result
            mock_model.generate_content.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_response_error(self, analyzer):
        """Test handling of empty response from Gemini."""
        with patch("app.services.ai.gemini_analyzer.genai.GenerativeModel") as mock_model_class:
            # Mock empty response
            mock_response = MagicMock()
            mock_response.text = ""

            mock_model = MagicMock()
            mock_model.generate_content = MagicMock(return_value=mock_response)
            mock_model_class.return_value = mock_model

            with patch("app.services.ai.gemini_analyzer.settings") as mock_settings:
                mock_settings.GEMINI_API_KEY = "test-key"

                with pytest.raises(InvalidResponseError, match="Empty response"):
                    await analyzer._call_gemini_api("test", [])

    # TODO(human): Add test for real Gemini API call
    # Uncomment and implement when you have a valid API key
    #
    # @pytest.mark.asyncio
    # @pytest.mark.skipif(
    #     not settings.GEMINI_API_KEY,
    #     reason="GEMINI_API_KEY not configured"
    # )
    # async def test_real_gemini_api_call(self, analyzer, sample_request):
    #     """Test actual Gemini API integration (requires API key)."""
    #     # This test will be skipped if GEMINI_API_KEY is not set
    #     result = await analyzer.analyze_place_content(sample_request)
    #
    #     # Verify result structure
    #     assert isinstance(result, PlaceInfo)
    #     assert result.name
    #     assert result.category
    #     assert 1 <= result.recommendation_score <= 10
    #     assert len(result.keywords) > 0
