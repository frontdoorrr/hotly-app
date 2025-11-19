"""Gemini 2.5 based video analysis."""

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
    before_sleep_log,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiVideoAnalyzer:
    """Gemini 2.5 Flash based unified video analysis (transcription + OCR + scene analysis)."""

    def __init__(self, api_key: str):
        """
        Initialize Gemini video analyzer.

        Args:
            api_key: Google Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"

        # Rate limiting
        self.last_request_time: datetime | None = None
        self.min_request_interval = settings.GEMINI_MIN_REQUEST_INTERVAL

    async def analyze_video_url(self, url: str, prompt: str | None) -> Dict[str, Any]:
        """
        Analyze YouTube video directly from URL (no download required).

        Args:
            url: YouTube public URL
            prompt: Analysis prompt

        Returns:
            Dictionary containing:
                - transcript: Audio transcription text
                - extracted_text: List of texts from video frames (OCR)
                - visual_elements: List of scene descriptions
                - analysis: AI analysis results

        Raises:
            ValueError: If video analysis fails
        """
        # Apply rate limiting
        await self._apply_rate_limit()

        try:
            contents = [types.Part.from_uri(file_uri=url, mime_type="video/mp4")]
            if prompt:
                contents.append(types.Part.from_text(prompt))
            response = await self._call_gemini_with_retry(contents=contents)
            return self._parse_response(response)

        except Exception as e:
            raise ValueError(f"Failed to analyze video from URL: {e}")

    async def analyze_video_file(self, file_path: str, prompt: str) -> Dict[str, Any]:
        """
        Analyze local video file (for Instagram/TikTok).

        Uses File API for files >20MB, inline upload for smaller files.

        Args:
            file_path: Path to downloaded video file
            prompt: Analysis prompt

        Returns:
            Dictionary containing:
                - transcript: Audio transcription text
                - extracted_text: List of texts from video frames (OCR)
                - visual_elements: List of scene descriptions
                - analysis: AI analysis results

        Raises:
            ValueError: If video analysis fails
        """
        try:
            # Read video file
            with open(file_path, "rb") as f:
                video_bytes = f.read()

            # Check file size (20MB = 20 * 1024 * 1024 bytes)
            file_size_mb = len(video_bytes) / (1024 * 1024)

            if file_size_mb > 20:
                # Use File API for large files
                return await self._analyze_with_file_api(file_path, prompt)
            else:
                # Use inline upload for small files
                return await self._analyze_with_inline_data(video_bytes, prompt)

        except Exception as e:
            raise ValueError(f"Failed to analyze video file: {e}")

    async def _analyze_with_inline_data(
        self, video_bytes: bytes, prompt: str
    ) -> Dict[str, Any]:
        """
        Analyze video using inline data upload (<20MB).

        Args:
            video_bytes: Video file bytes
            prompt: Analysis prompt

        Returns:
            Parsed analysis results
        """
        # Apply rate limiting
        await self._apply_rate_limit()

        response = await self._call_gemini_with_retry(
            contents=[
                types.Part(
                    inline_data=types.Blob(data=video_bytes, mime_type="video/mp4")
                ),
                types.Part(text=prompt),
            ]
        )
        return self._parse_response(response)

    async def _analyze_with_file_api(
        self, file_path: str, prompt: str
    ) -> Dict[str, Any]:
        """
        Analyze video using File API (>20MB).

        Args:
            file_path: Path to video file
            prompt: Analysis prompt

        Returns:
            Parsed analysis results
        """
        # TODO: Implement File API upload
        # file = self.client.files.upload(file=file_path)
        # Wait for processing...
        # Then analyze
        raise NotImplementedError("File API support coming soon")

    async def _apply_rate_limit(self):
        """Apply rate limiting between API requests."""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                logger.info(
                    f"Rate limiting: waiting {wait_time:.2f}s before next video analysis request"
                )
                await asyncio.sleep(wait_time)

        self.last_request_time = datetime.now()

    @retry(
        stop=stop_after_attempt(settings.GEMINI_MAX_RETRIES),
        wait=wait_exponential(
            multiplier=1,
            min=settings.GEMINI_RETRY_MIN_WAIT,
            max=settings.GEMINI_RETRY_MAX_WAIT,
        ),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
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
                self.client.models.generate_content, model=self.model, contents=contents
            )
            return response

        except Exception as e:
            logger.error(f"Gemini video analysis API call failed: {e}")
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
                "transcript": "",
                "extracted_text": [],
                "visual_elements": [],
                "parsing_note": "Could not parse as JSON",
            }
