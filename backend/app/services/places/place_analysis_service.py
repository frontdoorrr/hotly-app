"""Place analysis service that orchestrates content extraction and AI analysis."""

import logging
import time
from typing import List, Optional

from app.exceptions.ai import AIAnalysisError
from app.schemas.ai import PlaceAnalysisResponse
from app.schemas.content import ContentMetadata
from app.services.places.multimodal_orchestrator import MultimodalOrchestrator

logger = logging.getLogger(__name__)


class PlaceAnalysisService:
    """Service for analyzing content and extracting place information (multimodal)."""

    def __init__(self) -> None:
        """Initialize place analysis service."""
        self.orchestrator = MultimodalOrchestrator()

    async def analyze_content(
        self,
        content: ContentMetadata,
        images: Optional[List[str]] = None,
        enable_image_analysis: bool = True,
        max_images: int = 3,
    ) -> PlaceAnalysisResponse:
        """
        Analyze content metadata and extract place information (multimodal).

        Args:
            content: Content metadata from extraction
            images: Optional image URLs (overrides content.images)
            enable_image_analysis: Enable image download and analysis
            max_images: Maximum number of images to process

        Returns:
            PlaceAnalysisResponse with multimodal metadata
        """
        start_time = time.time()

        try:
            # Override images if provided
            if images is not None:
                content.images = images

            # Call multimodal orchestrator
            (
                place_info,
                confidence,
                multimodal_metadata,
            ) = await self.orchestrator.analyze_content(
                content_metadata=content,
                enable_image_analysis=enable_image_analysis,
                max_images=max_images,
            )

            analysis_time = time.time() - start_time

            return PlaceAnalysisResponse(
                success=True,
                place_info=place_info,
                confidence=confidence,
                analysis_time=analysis_time,
                model_version="gemini-2.0-flash-exp",
                multimodal_metadata=multimodal_metadata,
            )

        except AIAnalysisError as e:
            analysis_time = time.time() - start_time
            logger.error(f"AI analysis failed: {e}")

            return PlaceAnalysisResponse(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=analysis_time,
                error=str(e),
                model_version="gemini-2.0-flash-exp",
            )
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"Unexpected error in place analysis: {e}")

            return PlaceAnalysisResponse(
                success=False,
                place_info=None,
                confidence=0.0,
                analysis_time=analysis_time,
                error=f"Analysis failed: {str(e)}",
                model_version="gemini-2.0-flash-exp",
            )

