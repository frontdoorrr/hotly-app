"""Tests for ImageProcessor."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from app.exceptions.media import (
    ImageDownloadError,
    ImageProcessingError,
    InvalidImageError,
)
from app.services.media.image_processor import ImageProcessor


class TestImageProcessor:
    """Test ImageProcessor."""

    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image."""
        img = Image.new("RGB", (800, 600), color="red")
        return img

    @pytest.fixture
    def mock_image_bytes(self, mock_image):
        """Convert mock image to bytes."""
        buffer = io.BytesIO()
        mock_image.save(buffer, format="JPEG")
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_downloadAndProcessImages_success(
        self, mock_image_bytes, mock_image
    ):
        """Test successful image download and processing."""
        image_urls = ["https://example.com/image1.jpg"]

        async with ImageProcessor() as processor:
            # Mock HTTP client
            mock_response = MagicMock()
            mock_response.content = mock_image_bytes
            mock_response.headers = {"content-length": str(len(mock_image_bytes))}
            mock_response.raise_for_status = MagicMock()

            processor.http_client.get = AsyncMock(return_value=mock_response)

            # Execute
            pil_images, processed_images = await processor.download_and_process_images(
                image_urls, max_images=3
            )

            # Assert
            assert len(pil_images) == 1
            assert len(processed_images) == 1
            assert isinstance(pil_images[0], Image.Image)
            assert processed_images[0].original_url == image_urls[0]
            assert processed_images[0].metadata.width <= 1024
            assert processed_images[0].metadata.height <= 1024

    @pytest.mark.asyncio
    async def test_downloadAndProcessImages_maxImagesLimit(self, mock_image_bytes):
        """Test max images limit."""
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.jpg",
            "https://example.com/image3.jpg",
            "https://example.com/image4.jpg",
        ]

        async with ImageProcessor() as processor:
            mock_response = MagicMock()
            mock_response.content = mock_image_bytes
            mock_response.headers = {"content-length": str(len(mock_image_bytes))}
            mock_response.raise_for_status = MagicMock()

            processor.http_client.get = AsyncMock(return_value=mock_response)

            # Execute with max_images=2
            pil_images, _ = await processor.download_and_process_images(
                image_urls, max_images=2
            )

            # Assert: Only 2 images processed
            assert len(pil_images) == 2

    @pytest.mark.asyncio
    async def test_downloadAndProcessImages_emptyList(self):
        """Test with empty image list."""
        async with ImageProcessor() as processor:
            pil_images, processed_images = await processor.download_and_process_images(
                [], max_images=3
            )

            assert len(pil_images) == 0
            assert len(processed_images) == 0

    @pytest.mark.asyncio
    async def test_downloadImage_tooLarge(self):
        """Test image too large error."""
        async with ImageProcessor() as processor:
            # Mock response with large content-length
            mock_response = MagicMock()
            mock_response.headers = {
                "content-length": str(ImageProcessor.MAX_IMAGE_SIZE_BYTES + 1)
            }
            mock_response.raise_for_status = MagicMock()

            processor.http_client.get = AsyncMock(return_value=mock_response)

            # Execute and expect error
            with pytest.raises(ImageDownloadError, match="Image too large"):
                await processor._download_image("https://example.com/large.jpg")

    @pytest.mark.asyncio
    async def test_validateImage_tooSmall(self):
        """Test image too small validation."""
        processor = ImageProcessor()

        # Create small image (50x50)
        small_img = Image.new("RGB", (50, 50))

        with pytest.raises(InvalidImageError, match="Image too small"):
            await processor._validate_image(small_img)

    @pytest.mark.asyncio
    async def test_validateImage_unsupportedFormat(self):
        """Test unsupported format validation."""
        processor = ImageProcessor()

        # Create image with unsupported format
        img = Image.new("RGB", (500, 500))
        img.format = "TIFF"  # Not in SUPPORTED_FORMATS

        with pytest.raises(InvalidImageError, match="Unsupported format"):
            await processor._validate_image(img)

    @pytest.mark.asyncio
    async def test_resizeIfNeeded_largeImage(self):
        """Test resizing of large images."""
        processor = ImageProcessor()

        # Create large image (2000x1500)
        large_img = Image.new("RGB", (2000, 1500))

        # Resize
        resized = await processor._resize_if_needed(large_img)

        # Assert: max dimension should be <= 1024
        assert max(resized.size) <= 1024
        # Assert: aspect ratio preserved
        original_ratio = 2000 / 1500
        resized_ratio = resized.width / resized.height
        assert abs(original_ratio - resized_ratio) < 0.01

    @pytest.mark.asyncio
    async def test_normalizeFormat_rgba(self):
        """Test RGBA to RGB conversion."""
        processor = ImageProcessor()

        # Create RGBA image
        rgba_img = Image.new("RGBA", (500, 500), (255, 0, 0, 128))

        # Normalize
        normalized = await processor._normalize_format(rgba_img)

        # Assert: converted to RGB
        assert normalized.mode == "RGB"

    @pytest.mark.asyncio
    async def test_calculateQualityScore(self):
        """Test quality score calculation."""
        processor = ImageProcessor()

        # HD image (1920x1080)
        hd_img = Image.new("RGB", (1920, 1080))
        file_size = 1920 * 1080 * 2  # 2 bytes per pixel (good compression)

        score = processor._calculate_quality_score(hd_img, file_size)

        # Assert: should be high quality score
        assert 0.5 <= score <= 1.0


class TestImageProcessorIntegration:
    """Integration tests for ImageProcessor."""

    @pytest.mark.asyncio
    async def test_fullPipeline_withRealImage(self):
        """Test full pipeline with real image data."""
        # Create a real test image
        test_img = Image.new("RGB", (1200, 900), color="blue")
        buffer = io.BytesIO()
        test_img.save(buffer, format="JPEG", quality=85)
        test_bytes = buffer.getvalue()

        image_urls = ["https://example.com/test.jpg"]

        async with ImageProcessor() as processor:
            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.content = test_bytes
            mock_response.headers = {"content-length": str(len(test_bytes))}
            mock_response.raise_for_status = MagicMock()

            processor.http_client.get = AsyncMock(return_value=mock_response)

            # Execute full pipeline
            pil_images, processed_images = await processor.download_and_process_images(
                image_urls, max_images=1
            )

            # Assertions
            assert len(pil_images) == 1
            assert len(processed_images) == 1

            # Check processed image
            pil_img = pil_images[0]
            assert pil_img.mode == "RGB"
            assert max(pil_img.size) <= 1024

            # Check metadata
            metadata = processed_images[0].metadata
            assert metadata.width <= 1024
            assert metadata.height <= 1024
            assert metadata.format == "JPEG"
            assert 0 <= metadata.quality_score <= 1.0
            assert processed_images[0].processing_time > 0
