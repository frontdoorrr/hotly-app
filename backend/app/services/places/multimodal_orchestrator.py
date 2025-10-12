"""Multimodal analysis orchestrator."""

import logging
import time
from typing import List, Optional, Tuple

from PIL import Image

from app.schemas.ai import MultimodalAnalysisMetadata, PlaceAnalysisRequest, PlaceInfo
from app.schemas.content import ContentMetadata
from app.schemas.media import ProcessedImage
from app.services.ai.gemini_analyzer_v2 import GeminiAnalyzerV2
from app.services.media.image_processor import ImageProcessor
from app.services.media.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class MultimodalOrchestrator:
    """
    Multimodal analysis orchestrator.

    Responsibilities:
    1. Coordinate media processing (images, videos, text)
    2. Call AI analysis
    3. Integrate results and calculate confidence
    4. Execute fallback strategies
    """

    def __init__(self):
        """Initialize orchestrator."""
        self.ai_analyzer = GeminiAnalyzerV2()
        self.text_processor = TextProcessor()

    async def analyze_content(
        self,
        content_metadata: ContentMetadata,
        enable_image_analysis: bool = True,
        max_images: int = 3,
    ) -> Tuple[PlaceInfo, float, MultimodalAnalysisMetadata]:
        """
        Comprehensive content analysis (text + images + videos).

        Args:
            content_metadata: Extracted content metadata
            enable_image_analysis: Enable image analysis
            max_images: Maximum number of images to analyze

        Returns:
            (PlaceInfo, confidence, MultimodalAnalysisMetadata)
        """
        start_time = time.time()

        # 1. Text processing
        cleaned_text = await self.text_processor.clean_text(
            content_metadata.title or ""
        )
        hashtags = await self.text_processor.extract_hashtags(
            content_metadata.description or ""
        )

        # 2. Image processing (optional)
        pil_images: List[Image.Image] = []
        processed_images: List[ProcessedImage] = []
        image_processing_time = 0.0

        if enable_image_analysis and content_metadata.images:
            try:
                img_start = time.time()
                async with ImageProcessor() as img_processor:
                    (
                        pil_images,
                        processed_images,
                    ) = await img_processor.download_and_process_images(
                        content_metadata.images, max_images=max_images
                    )
                image_processing_time = time.time() - img_start

                if pil_images:
                    logger.info(
                        f"Successfully processed {len(pil_images)} images in {image_processing_time:.2f}s"
                    )
            except Exception as e:
                logger.warning(
                    f"Image processing failed, falling back to text-only: {e}"
                )
                # Fallback: Continue with text-only analysis

        # 3. Video processing (optional, YouTube only)
        # TODO: Video processing implementation
        video_frames: List[Image.Image] = []
        video_transcript: Optional[str] = None

        # 4. Prepare AI analysis request
        ai_request = PlaceAnalysisRequest(
            content_text=cleaned_text,
            content_description=content_metadata.description,
            hashtags=hashtags or [],
            images=[],  # URLs already downloaded
            platform=getattr(content_metadata, "platform", "unknown"),
        )

        # 5. AI multimodal analysis
        all_images = pil_images + video_frames
        place_info, ai_metadata = await self.ai_analyzer.analyze_multimodal_content(
            ai_request, pil_images=all_images if all_images else None
        )

        # 6. Enhance metadata
        ai_metadata.image_download_time = 0.0  # Already included in processing_time
        ai_metadata.image_processing_time = image_processing_time
        ai_metadata.num_video_frames = len(video_frames)

        # Calculate average image quality
        if processed_images:
            avg_quality = sum(
                img.metadata.quality_score for img in processed_images
            ) / len(processed_images)
            ai_metadata.avg_image_quality = avg_quality
        else:
            ai_metadata.avg_image_quality = 0.0

        # 7. Calculate overall confidence
        final_confidence = self._calculate_final_confidence(
            ai_metadata.confidence_factors,
            len(pil_images),
            len(video_frames),
            ai_metadata.text_quality_score,
        )

        # 8. Total processing time
        ai_metadata.total_time = time.time() - start_time

        return place_info, final_confidence, ai_metadata

    def _calculate_final_confidence(
        self,
        confidence_factors: dict,
        num_images: int,
        num_video_frames: int,
        text_quality: float,
    ) -> float:
        """
        Calculate overall confidence.

        Considered factors:
        - AI's own confidence
        - Number and quality of images
        - Text quality
        - Information completeness
        """
        # Base confidence (average of AI confidence factors)
        base_confidence = confidence_factors.get("overall_confidence", 0.5)

        # Multimodal bonus
        multimodal_bonus = 0.0

        if num_images > 0:
            # Image count bonus (max +0.2)
            multimodal_bonus += min(num_images * 0.1, 0.2)

        if num_video_frames > 0:
            # Video frame bonus (max +0.1)
            multimodal_bonus += min(num_video_frames * 0.05, 0.1)

        # Text quality bonus (max +0.1)
        text_bonus = text_quality * 0.1

        # Overall confidence (max 1.0)
        final = min(base_confidence + multimodal_bonus + text_bonus, 1.0)

        return final
