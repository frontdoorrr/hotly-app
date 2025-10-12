"""Gemini AI analyzer V2 with enhanced multimodal support."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai
from PIL import Image

from app.core.config import settings
from app.exceptions.ai import (
    AIAnalysisError,
    AIServiceUnavailableError,
    InvalidResponseError,
    RateLimitError,
)
from app.schemas.ai import (
    MultimodalAnalysisMetadata,
    PlaceAnalysisRequest,
    PlaceInfo,
)
from app.services.ai.prompts.multimodal_prompt import (
    get_image_analysis_instruction,
    get_multimodal_prompt,
)


class GeminiAnalyzerV2:
    """
    Gemini 2.0 Flash based multimodal analyzer (enhanced version).

    Improvements:
    - Direct PIL.Image object processing
    - Optimized multimodal prompts
    - Image analysis results reflected in confidence
    - Detailed metadata collection
    """

    def __init__(self) -> None:
        """Initialize Gemini analyzer."""
        if hasattr(settings, "GEMINI_API_KEY") and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

        self.model_name = "gemini-2.0-flash-exp"
        self.timeout = 60
        self.max_retries = 3
        self.base_delay = 1.0

    async def analyze_multimodal_content(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]] = None,
    ) -> Tuple[PlaceInfo, MultimodalAnalysisMetadata]:
        """
        Analyze multimodal content (text + images).

        Args:
            request: Analysis request (includes text info)
            pil_images: List of PIL.Image objects

        Returns:
            (PlaceInfo, MultimodalAnalysisMetadata)
        """
        start_time = time.time()

        try:
            # Initialize metadata
            metadata = MultimodalAnalysisMetadata(
                num_images_provided=len(request.images),
                num_images_analyzed=len(pil_images) if pil_images else 0,
                num_video_frames=0,  # TODO: Update when video frame support is added
                text_length_chars=len(request.content_text or ""),
                image_download_time=0.0,
                image_processing_time=0.0,
                ai_inference_time=0.0,
                total_time=0.0,
                avg_image_quality=0.0,
                text_quality_score=self._calculate_text_quality(request),
                confidence_factors={},
            )

            # Generate prompt
            prompt = self._format_multimodal_prompt(request, pil_images)

            # Call Gemini API
            ai_start_time = time.time()
            response_text = await self._call_gemini_api_with_retry(prompt, pil_images)
            metadata.ai_inference_time = time.time() - ai_start_time

            # Parse response
            place_data = self._parse_and_validate_response(response_text)

            # Create PlaceInfo
            place_info = PlaceInfo(**place_data)

            # Calculate confidence factors
            metadata.confidence_factors = self._calculate_confidence_factors(
                request, pil_images, place_info
            )

            # Total processing time
            metadata.total_time = time.time() - start_time

            return place_info, metadata

        except Exception as e:
            if isinstance(e, (AIAnalysisError, RateLimitError, InvalidResponseError)):
                raise
            raise AIAnalysisError(f"Multimodal analysis failed: {str(e)}")

    def _format_multimodal_prompt(
        self, request: PlaceAnalysisRequest, pil_images: Optional[List[Image.Image]]
    ) -> str:
        """Generate multimodal prompt."""
        hashtags_str = " ".join(request.hashtags) if request.hashtags else "없음"

        # Adjust prompt based on number of images
        image_instruction = ""
        if pil_images and len(pil_images) > 0:
            image_instruction = get_image_analysis_instruction(len(pil_images))

        prompt = get_multimodal_prompt(
            platform=request.platform,
            title=request.content_text or "없음",
            description=request.content_description or "없음",
            hashtags=hashtags_str,
            image_instruction=image_instruction,
        )

        return prompt

    async def _call_gemini_api_with_retry(
        self, prompt: str, images: Optional[List[Image.Image]]
    ) -> str:
        """Call Gemini API (with retry)."""
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

    async def _call_gemini_api(
        self, prompt: str, images: Optional[List[Image.Image]]
    ) -> str:
        """Call Gemini API (multimodal)."""
        try:
            if not hasattr(settings, "GEMINI_API_KEY") or not settings.GEMINI_API_KEY:
                raise AIServiceUnavailableError("Gemini API key not configured")

            model = genai.GenerativeModel(self.model_name)

            # Construct content
            if images and len(images) > 0:
                # Multimodal: [prompt, image1, image2, ...]
                content = [prompt] + images
            else:
                # Text only
                content = prompt

            # API call
            response = await asyncio.to_thread(
                model.generate_content,
                content,
                generation_config=genai.GenerationConfig(
                    temperature=0.1,  # Low temperature for consistency
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=2048,
                ),
            )

            if not response or not response.text:
                raise InvalidResponseError("Empty response from Gemini")

            response_text = response.text.strip()

            # Remove markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()

            return response_text

        except Exception as e:
            error_msg = str(e).lower()

            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Gemini rate limit: {str(e)}")
            if (
                "unavailable" in error_msg
                or "503" in error_msg
                or "500" in error_msg
            ):
                raise AIServiceUnavailableError(f"Gemini unavailable: {str(e)}")
            if "api key" in error_msg or "401" in error_msg:
                raise AIServiceUnavailableError(f"Gemini auth failed: {str(e)}")

            if isinstance(
                e, (RateLimitError, AIServiceUnavailableError, InvalidResponseError)
            ):
                raise

            raise AIAnalysisError(f"Gemini API call failed: {str(e)}")

    def _parse_and_validate_response(self, response_text: str) -> Dict[str, Any]:
        """Parse and validate JSON response."""
        try:
            response_data = json.loads(response_text)

            # Basic field validation
            if "name" not in response_data:
                raise InvalidResponseError("Missing 'name' field in response")

            return response_data

        except json.JSONDecodeError as e:
            raise InvalidResponseError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise AIAnalysisError(f"Failed to parse response: {str(e)}")

    def _calculate_text_quality(self, request: PlaceAnalysisRequest) -> float:
        """Calculate text quality score."""
        score = 0.0

        # Title length
        if request.content_text and len(request.content_text) > 10:
            score += 0.3

        # Description exists
        if request.content_description and len(request.content_description) > 20:
            score += 0.3

        # Number of hashtags
        if request.hashtags:
            score += min(len(request.hashtags) * 0.1, 0.4)

        return min(score, 1.0)

    def _calculate_confidence_factors(
        self,
        request: PlaceAnalysisRequest,
        pil_images: Optional[List[Image.Image]],
        place_info: PlaceInfo,
    ) -> Dict[str, float]:
        """Calculate confidence factors by category."""
        factors = {}

        # Text richness
        factors["text_richness"] = self._calculate_text_quality(request)

        # Image provision
        if pil_images and len(pil_images) > 0:
            factors["image_provided"] = 1.0
            factors["image_count_boost"] = min(len(pil_images) * 0.2, 0.6)
        else:
            factors["image_provided"] = 0.0
            factors["image_count_boost"] = 0.0

        # Extracted information completeness
        factors["name_extracted"] = 1.0 if place_info.name else 0.0
        factors["address_extracted"] = 0.8 if place_info.address else 0.0
        factors["category_extracted"] = 0.6 if place_info.category else 0.0

        # Overall confidence
        factors["overall_confidence"] = sum(factors.values()) / len(factors)

        return factors
