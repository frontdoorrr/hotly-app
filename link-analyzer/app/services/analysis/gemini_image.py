"""Gemini Vision API based image analysis."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any
from google import genai
from google.genai import types
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiImageAnalyzer:
    """Gemini Vision API based unified image analysis (OCR + object detection + scene understanding)."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini image analyzer.

        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = 'gemini-2.5-flash'

        # Rate limiting
        self.last_request_time: datetime | None = None
        self.min_request_interval = settings.GEMINI_MIN_REQUEST_INTERVAL

    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze image with unified analysis (OCR + object detection + scene description).

        Args:
            image_path: Path to image file
            prompt: Analysis prompt

        Returns:
            Dictionary containing:
                - extracted_text: OCR text from image
                - objects: List of detected objects
                - scene_description: Scene understanding
                - analysis: AI analysis results

        Raises:
            ValueError: If image analysis fails
        """
        # Apply rate limiting
        await self._apply_rate_limit()

        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            response = await self._call_gemini_with_retry(
                contents=[
                    types.Part(
                        inline_data=types.Blob(
                            data=image_bytes,
                            mime_type='image/jpeg'  # TODO: Auto-detect mime type
                        )
                    ),
                    types.Part(text=prompt)
                ]
            )

            return self._parse_response(response)

        except Exception as e:
            raise ValueError(f"Failed to analyze image: {e}")

    async def analyze_multiple_images(
        self,
        image_paths: list[str],
        prompt: str
    ) -> list[Dict[str, Any]]:
        """
        Analyze multiple images (for carousel posts).

        Args:
            image_paths: List of image file paths
            prompt: Analysis prompt

        Returns:
            List of analysis results for each image

        Raises:
            ValueError: If any image analysis fails
        """
        results = []
        for image_path in image_paths:
            result = await self.analyze_image(image_path, prompt)
            results.append(result)
        return results

    async def _apply_rate_limit(self):
        """Apply rate limiting between API requests."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.info(f"Rate limiting: waiting {wait_time:.2f}s before next image analysis request")
                await asyncio.sleep(wait_time)

        self.last_request_time = datetime.now()

    @retry(
        stop=stop_after_attempt(settings.GEMINI_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=settings.GEMINI_RETRY_MIN_WAIT,
            max=settings.GEMINI_RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _call_gemini_with_retry(self, contents):
        """
        Call Gemini API with retry logic.

        Args:
            contents: Gemini API contents parameter

        Returns:
            Gemini API response

        Raises:
            Exception: If all retries fail
        """
        try:
            # Note: google-genai SDK doesn't have async support yet
            # We wrap the sync call to maintain async interface
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model,
                contents=contents
            )
            return response

        except Exception as e:
            logger.error(f"Gemini image analysis API call failed: {e}")
            raise

    def _parse_response(self, response) -> Dict[str, Any]:
        """
        Parse Gemini API response.

        Args:
            response: Gemini API response object

        Returns:
            Structured analysis results
        """
        result_text = response.text

        # Try to parse JSON if response is structured
        try:
            import json
            # Remove code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]

            parsed = json.loads(result_text.strip())
            return parsed

        except json.JSONDecodeError:
            # Return raw text if not JSON
            return {
                "raw_response": result_text,
                "extracted_text": "",
                "objects": [],
                "scene_description": "",
                "parsing_note": "Could not parse as JSON"
            }
