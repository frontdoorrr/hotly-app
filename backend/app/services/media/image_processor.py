"""Image download and processing module."""

import asyncio
import io
from typing import List, Optional, Tuple

import httpx
from PIL import Image

from app.exceptions.media import (
    ImageDownloadError,
    ImageProcessingError,
    InvalidImageError,
)
from app.schemas.media import ImageMetadata, ProcessedImage


class ImageProcessor:
    """Image download and preprocessing processor."""

    # Configuration constants
    MAX_IMAGE_SIZE_MB = 10
    MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
    TARGET_MAX_DIMENSION = 1024  # Gemini API recommended size
    DOWNLOAD_TIMEOUT = 10  # seconds
    SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}

    def __init__(self):
        """Initialize image processor."""
        self.http_client = None
        self._download_semaphore = asyncio.Semaphore(3)  # Limit 3 concurrent downloads

    async def __aenter__(self):
        """Async context manager entry."""
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.DOWNLOAD_TIMEOUT),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.http_client:
            await self.http_client.aclose()

    async def download_and_process_images(
        self, image_urls: List[str], max_images: int = 3
    ) -> Tuple[List[Image.Image], List[ProcessedImage]]:
        """
        Download and process multiple images.

        Args:
            image_urls: List of image URLs
            max_images: Maximum number of images to process

        Returns:
            (List of PIL.Image objects, List of ProcessedImage metadata)
        """
        if not image_urls:
            return [], []

        # Limit to max images
        urls_to_process = image_urls[:max_images]

        # Parallel download and processing
        tasks = [
            self._download_and_process_single(url) for url in urls_to_process
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        pil_images = []
        processed_images = []

        for result in results:
            if isinstance(result, Exception):
                # Individual image failure: log and continue
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Image processing failed: {result}")
                continue

            if result:
                pil_image, processed_image = result
                pil_images.append(pil_image)
                processed_images.append(processed_image)

        return pil_images, processed_images

    async def _download_and_process_single(
        self, image_url: str
    ) -> Optional[Tuple[Image.Image, ProcessedImage]]:
        """
        Download and process a single image.

        Returns:
            (PIL.Image, ProcessedImage) or None (on failure)
        """
        start_time = asyncio.get_event_loop().time()

        async with self._download_semaphore:  # Limit concurrent downloads
            try:
                # 1. Download image
                image_bytes = await self._download_image(image_url)

                # 2. Convert to PIL.Image
                try:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    # Force load to detect corrupted images
                    pil_image.load()
                except Exception as e:
                    raise InvalidImageError(
                        f"Cannot decode image from {image_url}. "
                        f"The file may not be a valid image or may be corrupted. Error: {str(e)}"
                    )

                # 3. Validate image
                await self._validate_image(pil_image)

                # 4. Extract metadata
                metadata = await self._extract_metadata(
                    image_url, pil_image, image_bytes
                )

                # 5. Resize if needed
                pil_image = await self._resize_if_needed(pil_image)

                # 6. Normalize format (WebP → JPEG, etc.)
                pil_image = await self._normalize_format(pil_image)

                processing_time = asyncio.get_event_loop().time() - start_time

                processed_image = ProcessedImage(
                    original_url=image_url,
                    metadata=metadata,
                    processing_time=processing_time,
                )

                return pil_image, processed_image

            except Exception as e:
                raise ImageProcessingError(
                    f"Failed to process image {image_url}: {str(e)}"
                )

    async def _download_image(self, url: str) -> bytes:
        """Download image."""
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()

            # Content-Type validation
            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                raise ImageDownloadError(
                    f"Invalid content type: {content_type}. Expected image/* but got HTML or other content. "
                    f"URL may not be a direct image link."
                )

            # Size validation
            content_length = int(response.headers.get("content-length", 0))
            if content_length > self.MAX_IMAGE_SIZE_BYTES:
                raise ImageDownloadError(
                    f"Image too large: {content_length} bytes (max: {self.MAX_IMAGE_SIZE_BYTES})"
                )

            image_bytes = response.content

            # Actual size validation
            if len(image_bytes) > self.MAX_IMAGE_SIZE_BYTES:
                raise ImageDownloadError(
                    f"Downloaded image too large: {len(image_bytes)} bytes"
                )

            # Empty content validation
            if len(image_bytes) == 0:
                raise ImageDownloadError(f"Downloaded empty image from: {url}")

            return image_bytes

        except httpx.HTTPStatusError as e:
            raise ImageDownloadError(f"HTTP error {e.response.status_code}: {url}")
        except httpx.TimeoutException:
            raise ImageDownloadError(f"Download timeout: {url}")
        except ImageDownloadError:
            raise  # Re-raise our custom errors
        except Exception as e:
            raise ImageDownloadError(f"Download failed: {str(e)}")

    async def _validate_image(self, image: Image.Image) -> None:
        """Validate image."""
        # Format validation
        if image.format not in self.SUPPORTED_FORMATS:
            raise InvalidImageError(
                f"Unsupported format: {image.format}. Supported: {self.SUPPORTED_FORMATS}"
            )

        # Size validation
        width, height = image.size
        if width < 100 or height < 100:
            raise InvalidImageError(
                f"Image too small: {width}x{height} (min: 100x100)"
            )

        if width > 10000 or height > 10000:
            raise InvalidImageError(
                f"Image too large: {width}x{height} (max: 10000x10000)"
            )

        # Mode validation (detect corrupted images)
        if image.mode not in ("RGB", "RGBA", "L", "P"):
            raise InvalidImageError(f"Invalid image mode: {image.mode}")

    async def _extract_metadata(
        self, url: str, image: Image.Image, image_bytes: bytes
    ) -> ImageMetadata:
        """Extract image metadata."""
        width, height = image.size
        file_size = len(image_bytes)

        # EXIF data extraction
        exif_gps = None
        exif_datetime = None

        try:
            exif_data = image._getexif()
            if exif_data:
                # GPS info extraction
                gps_info = exif_data.get(34853)  # GPSInfo tag
                if gps_info:
                    exif_gps = self._parse_gps_info(gps_info)

                # Capture time extraction
                datetime_original = exif_data.get(36867)  # DateTimeOriginal
                if datetime_original:
                    try:
                        from datetime import datetime

                        exif_datetime = datetime.strptime(
                            datetime_original, "%Y:%m:%d %H:%M:%S"
                        )
                    except:
                        pass
        except:
            pass  # EXIF extraction failure is ignored

        # Image quality score calculation
        quality_score = self._calculate_quality_score(image, file_size)

        return ImageMetadata(
            url=url,
            width=width,
            height=height,
            file_size_bytes=file_size,
            format=image.format or "UNKNOWN",
            exif_gps=exif_gps,
            exif_datetime=exif_datetime,
            quality_score=quality_score,
        )

    def _parse_gps_info(self, gps_info: dict) -> Optional[dict]:
        """Parse GPS information."""
        try:
            # GPS coordinate extraction logic (simplified)
            # Actual implementation requires accurate GPSInfo tag parsing
            if not gps_info:
                return None

            # TODO: Implement actual GPS parsing
            return None
        except:
            return None

    def _calculate_quality_score(self, image: Image.Image, file_size: int) -> float:
        """Calculate image quality score."""
        width, height = image.size
        pixels = width * height

        # Resolution score (0.0 ~ 0.4)
        resolution_score = min(pixels / (1920 * 1080), 1.0) * 0.4

        # File size vs resolution (compression rate judgment) (0.0 ~ 0.3)
        bytes_per_pixel = file_size / pixels if pixels > 0 else 0
        # Appropriate compression: 0.5~3.0 bytes/pixel
        compression_score = 0.3 if 0.5 <= bytes_per_pixel <= 3.0 else 0.15

        # Aspect ratio normality (0.0 ~ 0.3)
        aspect_ratio = width / height if height > 0 else 0
        # Normal range: 0.5 ~ 2.0
        aspect_score = 0.3 if 0.5 <= aspect_ratio <= 2.0 else 0.1

        return min(resolution_score + compression_score + aspect_score, 1.0)

    async def _resize_if_needed(self, image: Image.Image) -> Image.Image:
        """Resize image if necessary."""
        width, height = image.size
        max_dim = max(width, height)

        if max_dim <= self.TARGET_MAX_DIMENSION:
            return image  # No resizing needed

        # Resize while maintaining aspect ratio
        scale = self.TARGET_MAX_DIMENSION / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return resized

    async def _normalize_format(self, image: Image.Image) -> Image.Image:
        """Normalize image format."""
        # Convert RGBA to RGB (Gemini prefers RGB)
        if image.mode == "RGBA":
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel
            return rgb_image

        # Convert palette mode to RGB
        if image.mode == "P":
            return image.convert("RGB")

        # Convert grayscale to RGB (optional)
        if image.mode == "L":
            return image.convert("RGB")

        return image
