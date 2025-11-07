"""Gemini Vision API based image analysis."""

from typing import Dict, Any
from google import genai
from google.genai import types


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
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_bytes = f.read()

            response = self.client.models.generate_content(
                model=self.model,
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
