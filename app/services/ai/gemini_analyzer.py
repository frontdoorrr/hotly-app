"""Gemini AI analyzer for place information extraction."""
import asyncio
import json
import time
from typing import Any, Dict

import google.generativeai as genai
import jsonschema

from app.core.config import settings
from app.exceptions.ai import (
    AIAnalysisError,
    AIServiceUnavailableError,
    InvalidResponseError,
    RateLimitError,
)
from app.prompts.place_extraction import (
    PLACE_EXTRACTION_JSON_SCHEMA,
    PLACE_EXTRACTION_PROMPT_V1,
)
from app.schemas.ai import PlaceAnalysisRequest, PlaceInfo


class GeminiAnalyzer:
    """Google Gemini AI analyzer for place content analysis."""

    def __init__(self) -> None:
        """Initialize Gemini analyzer."""
        # Configure Gemini API
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model_name = "gemini-pro-vision"
        self.timeout = 60  # 60 seconds timeout
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff

    async def analyze_place_content(self, request: PlaceAnalysisRequest) -> PlaceInfo:
        """Analyze content and extract place information."""
        time.time()

        try:
            # Format prompt with content data
            formatted_prompt = self._format_prompt(request)

            # Call Gemini API with retries
            response_text = await self._call_gemini_api_with_retry(
                formatted_prompt, request.images
            )

            # Parse and validate response
            place_data = self._parse_and_validate_response(response_text)

            # Convert to PlaceInfo
            place_info = PlaceInfo(**place_data)

            return place_info

        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError, InvalidResponseError)):
                raise
            raise AIAnalysisError(f"Gemini analysis failed: {str(e)}")

    def _format_prompt(self, request: PlaceAnalysisRequest) -> str:
        """Format prompt template with request data."""
        hashtags_str = " ".join(request.hashtags) if request.hashtags else "없음"

        return PLACE_EXTRACTION_PROMPT_V1.format(
            platform=request.platform,
            title=request.content_text or "없음",
            description=request.content_description or "없음",
            hashtags=hashtags_str,
            json_schema=json.dumps(
                PLACE_EXTRACTION_JSON_SCHEMA, indent=2, ensure_ascii=False
            ),
        )

    async def _call_gemini_api_with_retry(self, prompt: str, images: list) -> str:
        """Call Gemini API with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await self._call_gemini_api(prompt, images)
            except RateLimitError:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)
            except AIServiceUnavailableError:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)

        raise AIAnalysisError("Max retries exceeded")

    async def _call_gemini_api(self, prompt: str, images: list) -> str:
        """Call Gemini API (mock implementation for testing)."""
        # This is a mock implementation for testing
        # Real implementation would call actual Gemini API

        # Simulate API call delay
        await asyncio.sleep(0.1)

        # Return mock JSON response
        mock_response = {
            "name": "테스트 레스토랑",
            "address": "서울 강남구 테스트로 123",
            "category": "restaurant",
            "keywords": ["한식", "맛집", "가족식당"],
            "recommendation_score": 8,
            "phone": None,
            "website": None,
            "opening_hours": None,
            "price_range": "보통",
        }

        return json.dumps(mock_response, ensure_ascii=False)

    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini JSON response."""
        try:
            # Parse JSON
            response_data = json.loads(response_text)

            # Validate against schema
            jsonschema.validate(response_data, PLACE_EXTRACTION_JSON_SCHEMA)

            return response_data

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON response from Gemini: {str(e)}")
        except jsonschema.ValidationError as e:
            raise InvalidResponseError(
                f"Response does not match expected schema: {str(e)}"
            )
        except Exception as e:
            raise AIAnalysisError(f"Failed to parse Gemini response: {str(e)}")
