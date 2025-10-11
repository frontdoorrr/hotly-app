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

        # Use Gemini 1.5 Flash (fast, cost-effective, supports vision)
        # Alternative: "gemini-1.5-pro" for higher accuracy but slower
        self.model_name = "gemini-1.5-flash"
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
        """Call Gemini API with actual Google Generative AI."""
        try:
            # Check if API key is configured
            if not hasattr(settings, "GEMINI_API_KEY") or not settings.GEMINI_API_KEY:
                raise AIServiceUnavailableError(
                    "Gemini API key not configured. Set GEMINI_API_KEY in environment."
                )

            # Initialize the model
            model = genai.GenerativeModel(self.model_name)

            # Prepare content for API call
            if images and len(images) > 0:
                # Multimodal: Text + Images
                # Images should be PIL.Image objects or file paths
                content = [prompt] + images
            else:
                # Text-only
                content = prompt

            # Call Gemini API with asyncio.to_thread for sync API
            response = await asyncio.to_thread(
                model.generate_content,
                content,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistent structured output
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            # Check if response has text
            if not response or not response.text:
                raise InvalidResponseError("Empty response from Gemini API")

            # Extract response text
            response_text = response.text.strip()

            # Clean up markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
                if response_text.endswith("```"):
                    response_text = response_text[:-3]  # Remove ```
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            return response_text

        except Exception as e:
            # Handle specific error types
            error_message = str(e).lower()

            # Rate limit errors
            if "quota" in error_message or "rate limit" in error_message or "429" in error_message:
                raise RateLimitError(f"Gemini API rate limit exceeded: {str(e)}")

            # Service unavailable
            if "unavailable" in error_message or "503" in error_message or "500" in error_message:
                raise AIServiceUnavailableError(f"Gemini service unavailable: {str(e)}")

            # API key errors
            if "api key" in error_message or "authentication" in error_message or "401" in error_message:
                raise AIServiceUnavailableError(f"Gemini API authentication failed: {str(e)}")

            # Re-raise known exceptions
            if isinstance(e, (RateLimitError, AIServiceUnavailableError, InvalidResponseError)):
                raise

            # Generic error
            raise AIAnalysisError(f"Gemini API call failed: {str(e)}")

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
