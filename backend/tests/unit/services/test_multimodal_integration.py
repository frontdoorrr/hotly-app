"""Integration tests for multimodal analysis pipeline."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.schemas.content import ContentMetadata
from app.services.places.place_analysis_service import PlaceAnalysisService


class TestMultimodalIntegration:
    """Test multimodal analysis integration."""

    @pytest.fixture
    def sample_content_metadata(self):
        """Create sample content metadata."""
        return ContentMetadata(
            title="서울 성수동 감성 카페",
            description="북유럽 감성의 브런치 카페입니다. 루프탑도 있어요!",
            hashtags=["성수동", "카페", "브런치", "감성카페"],
            images=[
                "https://example.com/cafe1.jpg",
                "https://example.com/cafe2.jpg",
            ],
            location="서울 성동구 성수동",
        )

    @pytest.fixture
    def mock_image_bytes(self):
        """Create mock image bytes."""
        img = Image.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_analyzeContent_withImages(
        self, sample_content_metadata, mock_image_bytes
    ):
        """Test content analysis with images."""
        service = PlaceAnalysisService()

        # Mock ImageProcessor
        with patch(
            "app.services.places.multimodal_orchestrator.ImageProcessor"
        ) as MockImageProcessor:
            # Mock image processing
            mock_processor = MagicMock()
            mock_pil_img = Image.new("RGB", (800, 600))

            mock_processor.download_and_process_images = AsyncMock(
                return_value=([mock_pil_img], [])
            )
            mock_processor.__aenter__ = AsyncMock(return_value=mock_processor)
            mock_processor.__aexit__ = AsyncMock(return_value=None)

            MockImageProcessor.return_value = mock_processor

            # Mock AI analyzer
            with patch(
                "app.services.ai.gemini_analyzer_v2.GeminiAnalyzerV2.analyze_multimodal_content"
            ) as mock_analyze:
                from app.schemas.ai import (
                    MultimodalAnalysisMetadata,
                    PlaceCategory,
                    PlaceInfo,
                )

                # Mock AI response
                mock_place_info = PlaceInfo(
                    name="카페 오아시스",
                    address="서울 성동구 성수동 12-34",
                    category=PlaceCategory.CAFE,
                    keywords=["브런치", "감성", "루프탑"],
                    recommendation_score=8,
                )

                mock_metadata = MultimodalAnalysisMetadata(
                    num_images_provided=2,
                    num_images_analyzed=1,
                    num_video_frames=0,
                    text_length_chars=50,
                    image_download_time=0.1,
                    image_processing_time=0.2,
                    ai_inference_time=1.5,
                    total_time=1.8,
                    avg_image_quality=0.85,
                    text_quality_score=0.7,
                    confidence_factors={"overall_confidence": 0.8},
                )

                mock_analyze.return_value = (mock_place_info, mock_metadata)

                # Execute
                response = await service.analyze_content(
                    sample_content_metadata, enable_image_analysis=True, max_images=3
                )

                # Assertions
                assert response.success is True
                assert response.place_info is not None
                assert response.place_info.name == "카페 오아시스"
                assert response.place_info.category == PlaceCategory.CAFE
                assert response.confidence > 0.5
                assert response.multimodal_metadata is not None
                assert response.multimodal_metadata.num_images_analyzed == 1
                assert response.model_version == "gemini-2.0-flash-exp"

    @pytest.mark.asyncio
    async def test_analyzeContent_textOnly(self, sample_content_metadata):
        """Test content analysis without images (text-only)."""
        service = PlaceAnalysisService()

        # Remove images
        sample_content_metadata.images = []

        # Mock AI analyzer
        with patch(
            "app.services.ai.gemini_analyzer_v2.GeminiAnalyzerV2.analyze_multimodal_content"
        ) as mock_analyze:
            from app.schemas.ai import (
                MultimodalAnalysisMetadata,
                PlaceCategory,
                PlaceInfo,
            )

            mock_place_info = PlaceInfo(
                name="알 수 없는 카페",
                category=PlaceCategory.CAFE,
                keywords=["카페"],
                recommendation_score=5,
            )

            mock_metadata = MultimodalAnalysisMetadata(
                num_images_provided=0,
                num_images_analyzed=0,
                num_video_frames=0,
                text_length_chars=50,
                image_download_time=0.0,
                image_processing_time=0.0,
                ai_inference_time=0.8,
                total_time=0.8,
                avg_image_quality=0.0,
                text_quality_score=0.7,
                confidence_factors={"overall_confidence": 0.5},
            )

            mock_analyze.return_value = (mock_place_info, mock_metadata)

            # Execute
            response = await service.analyze_content(
                sample_content_metadata, enable_image_analysis=False
            )

            # Assertions
            assert response.success is True
            assert response.place_info is not None
            assert response.confidence >= 0.0
            assert response.multimodal_metadata.num_images_analyzed == 0

    @pytest.mark.asyncio
    async def test_analyzeContent_errorHandling(self, sample_content_metadata):
        """Test error handling in analysis."""
        service = PlaceAnalysisService()

        # Mock AI analyzer to raise error
        with patch(
            "app.services.ai.gemini_analyzer_v2.GeminiAnalyzerV2.analyze_multimodal_content"
        ) as mock_analyze:
            from app.exceptions.ai import AIAnalysisError

            mock_analyze.side_effect = AIAnalysisError("API quota exceeded")

            # Execute
            response = await service.analyze_content(sample_content_metadata)

            # Assertions
            assert response.success is False
            assert response.place_info is None
            assert response.confidence == 0.0
            assert "API quota exceeded" in response.error
