"""Gemini AI implementation for place category classification."""

import asyncio
import json
from typing import Any, Dict, List

import google.generativeai as genai
import jsonschema

from app.core.config import settings
from app.exceptions.ai import AIAnalysisError, InvalidResponseError, RateLimitError
from app.schemas.place import PlaceCreate
from app.services.ai.interfaces.classifier_interface import AIClassifierInterface

# Classification prompt template
CLASSIFICATION_PROMPT_TEMPLATE = """당신은 장소 카테고리 분류 전문가입니다.

다음 장소 정보를 분석하여 가장 적합한 카테고리를 선택해주세요:

장소명: {name}
설명: {description}
키워드: {keywords}
태그: {tags}

카테고리 옵션:
1. restaurant (음식점/식당/베이커리/디저트)
2. cafe (카페/커피숍/차집/주스바)
3. bar (술집/바/펜션주점/호프집)
4. tourist_attraction (관광지/명소/박물관/궁궐/공원)
5. shopping (쇼핑/매장/마트/백화점/시장)
6. accommodation (숙박/호텔/펜션/게스트하우스)
7. entertainment (오락/엔터테인먼트/영화관/노래방/볼링장)
8. other (위 카테고리에 해당하지 않는 기타 장소)

중요 분류 기준:
- 주요 목적과 서비스를 고려하세요
- 애매한 경우 가장 대표적인 기능을 선택하세요
- 신뢰도가 낮다면(0.7 미만) other로 분류하세요

JSON 형태로만 응답해주세요:
{{
  "category": "선택한_카테고리",
  "confidence": 0.85,
  "reasoning": "분류 근거 설명"
}}"""

# JSON schema for validation
CLASSIFICATION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": [
                "restaurant",
                "cafe",
                "bar",
                "tourist_attraction",
                "shopping",
                "accommodation",
                "entertainment",
                "other",
            ],
        },
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "reasoning": {"type": "string"},
    },
    "required": ["category", "confidence", "reasoning"],
    "additionalProperties": False,
}


class GeminiClassifier(AIClassifierInterface):
    """Gemini AI implementation for place classification."""

    def __init__(self) -> None:
        """Initialize Gemini classifier."""
        # Configure Gemini API
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model_name = "gemini-pro"
        self.timeout = 30  # 30 seconds timeout for classification
        self.max_retries = 2
        self.base_delay = 1.0

    async def classify_place(self, place_data: PlaceCreate) -> Dict[str, Any]:
        """Classify a single place using Gemini AI."""
        try:
            # Format prompt with place data
            prompt = self._format_classification_prompt(place_data)

            # Call Gemini API with retry logic
            response_text = await self._call_gemini_with_retry(prompt)

            # Parse and validate response
            result = self._parse_and_validate_response(response_text)

            return result

        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError, InvalidResponseError)):
                raise
            raise AIAnalysisError(f"Gemini classification failed: {str(e)}")

    async def classify_batch(self, places: List[PlaceCreate]) -> List[Dict[str, Any]]:
        """Classify multiple places with concurrent processing."""
        # Use semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent calls

        async def classify_single(place):
            async with semaphore:
                return await self.classify_place(place)

        # Execute classifications concurrently
        tasks = [classify_single(place) for place in places]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions in results
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(
                    {"category": "other", "confidence": 0.0, "reasoning": "분류 실패"}
                )
            else:
                processed_results.append(result)

        return processed_results

    def is_available(self) -> bool:
        """Check if Gemini API is configured and available."""
        return (
            hasattr(settings, "GEMINI_API_KEY")
            and settings.GEMINI_API_KEY
            and settings.GEMINI_API_KEY != "your-gemini-api-key"
        )

    def _format_classification_prompt(self, place_data: PlaceCreate) -> str:
        """Format classification prompt with place data."""
        keywords_str = ", ".join(place_data.keywords) if place_data.keywords else "없음"
        tags_str = ", ".join(place_data.tags) if place_data.tags else "없음"
        description = place_data.description or "설명 없음"

        return CLASSIFICATION_PROMPT_TEMPLATE.format(
            name=place_data.name,
            description=description,
            keywords=keywords_str,
            tags=tags_str,
        )

    async def _call_gemini_with_retry(self, prompt: str) -> str:
        """Call Gemini API with exponential backoff retry."""
        for attempt in range(self.max_retries):
            try:
                return await self._call_gemini_api(prompt)
            except RateLimitError:
                if attempt == self.max_retries - 1:
                    raise
                delay = self.base_delay * (2**attempt)
                await asyncio.sleep(delay)

        raise AIAnalysisError("Max retries exceeded")

    async def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API for classification."""
        try:
            # Initialize Gemini model
            model = genai.GenerativeModel(self.model_name)

            # Generate response
            response = await asyncio.wait_for(
                asyncio.create_task(self._generate_response(model, prompt)),
                timeout=self.timeout,
            )

            if not response or not response.text:
                raise InvalidResponseError("Empty response from Gemini")

            return response.text.strip()

        except asyncio.TimeoutError:
            raise AIAnalysisError("Gemini API timeout")
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise RateLimitError("Gemini API rate limit exceeded")
            raise AIAnalysisError(f"Gemini API call failed: {str(e)}")

    async def _generate_response(self, model, prompt: str):
        """Generate response from Gemini model."""
        # This would be the actual Gemini API call
        # For now, return mock response for testing
        await asyncio.sleep(0.1)  # Simulate API delay

        return type(
            "Response",
            (),
            {
                "text": json.dumps(
                    {
                        "category": "cafe",
                        "confidence": 0.85,
                        "reasoning": "커피 관련 키워드가 명확하게 식별됨",
                    },
                    ensure_ascii=False,
                )
            },
        )()

    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate Gemini classification response."""
        try:
            # Clean response text (remove markdown formatting if present)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = (
                    cleaned_text.replace("```json", "").replace("```", "").strip()
                )

            # Parse JSON
            response_data = json.loads(cleaned_text)

            # Validate against schema
            jsonschema.validate(response_data, CLASSIFICATION_RESPONSE_SCHEMA)

            return response_data

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON response from Gemini: {str(e)}")
        except jsonschema.ValidationError as e:
            raise InvalidResponseError(f"Response does not match schema: {str(e)}")
        except Exception as e:
            raise AIAnalysisError(f"Failed to parse Gemini response: {str(e)}")
