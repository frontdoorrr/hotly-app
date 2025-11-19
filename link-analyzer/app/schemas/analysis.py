"""Pydantic schemas for content analysis."""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    """Supported platforms."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class ContentType(str, Enum):
    """Content types."""
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"


class AnalysisRequest(BaseModel):
    """Content analysis request."""
    url: HttpUrl = Field(..., description="Social media URL to analyze")
    options: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            'include_video_analysis': True,
            'include_image_analysis': True,
            'include_classification': True,
        },
        description="Analysis options"
    )


class PlaceInfo(BaseModel):
    """Place information."""
    name: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    hours: Optional[str] = None
    address: Optional[str] = None


class MenuItem(BaseModel):
    """Menu or product item."""
    name: str
    price: Optional[str] = None
    description: Optional[str] = None


class ClassificationResult(BaseModel):
    """Content classification result."""
    primary_category: str = Field(..., description="Main category")
    sub_categories: List[str] = Field(default_factory=list)
    place_info: Optional[PlaceInfo] = None
    menu_items: List[MenuItem] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    price_range: Optional[str] = None
    recommended_for: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    sentiment_score: float = 0.0
    summary: str = ""
    keywords: List[str] = Field(default_factory=list)
    confidence: float = 0.0


class VideoAnalysis(BaseModel):
    """Video analysis result."""
    transcript: str = ""
    extracted_text: List[str] = Field(default_factory=list)
    visual_elements: List[str] = Field(default_factory=list)


class ImageAnalysis(BaseModel):
    """Image analysis result."""
    extracted_text: str = ""
    objects: List[str] = Field(default_factory=list)
    scene_description: str = ""


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    url: str
    platform: Platform
    content_type: ContentType

    # Analysis results
    video_analysis: Optional[VideoAnalysis] = None
    image_analysis: Optional[ImageAnalysis] = None
    classification: Optional[ClassificationResult] = None

    # Platform-specific metadata (includes title, description, hashtags, etc.)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisError(BaseModel):
    """Error response."""
    url: str
    error: str
    error_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
