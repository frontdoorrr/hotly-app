"""Place analysis service that orchestrates content extraction and AI analysis."""
import time
from typing import List

from app.exceptions.ai import AIAnalysisError
from app.schemas.ai import PlaceAnalysisRequest, PlaceAnalysisResponse, PlaceInfo
from app.schemas.content import ContentMetadata
from app.services.ai.gemini_analyzer import GeminiAnalyzer


class PlaceAnalysisService:
    """Service for analyzing content and extracting place information."""

    def __init__(self) -> None:
        """Initialize place analysis service."""
        self.ai_analyzer = GeminiAnalyzer()  # Phase 1: Direct injection

    async def analyze_content(
        self, content: ContentMetadata, images: List[str] = None
    ) -> PlaceAnalysisResponse:
        """Analyze content metadata and extract place information."""
        start_time = time.time()

        try:
            # Prepare AI analysis request
            ai_request = PlaceAnalysisRequest(
                content_text=content.title or "",
                content_description=content.description,
                hashtags=content.hashtags or [],
                images=images or content.images or [],
                platform="extracted_content",  # Generic platform for processed content
            )

            # Analyze with AI
            place_info = await self.ai_analyzer.analyze_place_content(ai_request)

            # Calculate confidence based on available data
            confidence = self._calculate_confidence(content, place_info)

            analysis_time = time.time() - start_time

            return PlaceAnalysisResponse(
                success=True,
                place_info=place_info,
                confidence=confidence,
                analysis_time=analysis_time,
                model_version="gemini-pro-vision",
            )

        except AIAnalysisError as e:
            analysis_time = time.time() - start_time

            return PlaceAnalysisResponse(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=analysis_time,
                error=str(e),
                model_version="gemini-pro-vision",
            )

    def _calculate_confidence(
        self, content: ContentMetadata, place_info: PlaceInfo
    ) -> float:
        """Calculate confidence score based on available data quality."""
        confidence = 0.5  # Base confidence

        # Boost confidence based on data availability
        if content.title and len(content.title) > 10:
            confidence += 0.1
        if content.description and len(content.description) > 20:
            confidence += 0.1
        if content.location:
            confidence += 0.1
        if content.hashtags and len(content.hashtags) > 2:
            confidence += 0.1
        if content.images and len(content.images) > 0:
            confidence += 0.1

        # Boost confidence based on extracted place info quality
        if place_info.address:
            confidence += 0.1
        if place_info.phone:
            confidence += 0.05
        if len(place_info.keywords) > 3:
            confidence += 0.05

        # Cap confidence at 1.0
        return min(confidence, 1.0)
