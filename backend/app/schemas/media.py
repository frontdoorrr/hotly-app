"""Media processing schemas for multimodal analysis."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class ImageMetadata(BaseModel):
    """Image metadata extracted from processing."""

    url: HttpUrl
    width: int
    height: int
    file_size_bytes: int
    format: str  # JPEG, PNG, WebP
    exif_gps: Optional[Dict[str, float]] = None  # {lat: 37.xx, lng: 127.xx}
    exif_datetime: Optional[datetime] = None
    quality_score: float = Field(ge=0.0, le=1.0)  # 0.0~1.0


class ProcessedImage(BaseModel):
    """Processed image information."""

    original_url: HttpUrl
    metadata: ImageMetadata
    processing_time: float


class VideoFrameMetadata(BaseModel):
    """Video frame metadata."""

    video_url: HttpUrl
    frame_index: int  # 0, 1, 2, ...
    timestamp_seconds: float  # Frame extraction position (seconds)
    width: int
    height: int
    quality_score: float


class ProcessedMedia(BaseModel):
    """Complete media processing result."""

    # Text information
    cleaned_text: str
    hashtags: List[str]
    keywords: List[str]

    # Image information
    images: List[ProcessedImage]
    total_images: int

    # Video information
    video_frames: List[VideoFrameMetadata]
    video_transcript: Optional[str] = None  # YouTube captions

    # Statistics
    processing_time: float
    total_media_size_mb: float

    # Quality metrics
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    confidence_boost: float = Field(
        ge=0.0, le=1.0
    )  # Confidence increase from multimodal
