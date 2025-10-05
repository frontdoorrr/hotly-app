"""AI analysis schemas for place information extraction."""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class PlaceCategory(str, Enum):
    """Place categories."""

    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    TOURIST_ATTRACTION = "tourist_attraction"
    SHOPPING = "shopping"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class PlaceInfo(BaseModel):
    """Extracted place information from AI analysis."""

    name: str = Field(..., description="Place name (exact business name)")
    address: Optional[str] = Field(
        None, description="Place address (street address preferred)"
    )
    category: PlaceCategory = Field(..., description="Place category")
    keywords: List[str] = Field(
        default_factory=list, description="Characteristic keywords"
    )
    recommendation_score: int = Field(
        ..., ge=1, le=10, description="Recommendation score (1-10)"
    )
    phone: Optional[str] = Field(None, description="Phone number if mentioned")
    website: Optional[str] = Field(None, description="Website URL if mentioned")
    opening_hours: Optional[str] = Field(None, description="Opening hours if mentioned")
    price_range: Optional[str] = Field(None, description="Price range (저렴/보통/비쌈)")

    @validator("keywords")
    def validate_keywords(cls, v):
        """Limit keywords to reasonable number."""
        return v[:10] if len(v) > 10 else v


class PlaceAnalysisRequest(BaseModel):
    """Request for AI place analysis."""

    content_text: str = Field(..., description="Extracted text content")
    content_description: Optional[str] = Field(None, description="Content description")
    hashtags: List[str] = Field(
        default_factory=list, description="Hashtags from content"
    )
    images: List[str] = Field(
        default_factory=list, description="Image URLs for vision analysis"
    )
    platform: str = Field(..., description="Source platform")


class AnalysisConfidence(str, Enum):
    """Analysis confidence levels."""
    
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"


class PlaceAnalysisResult(BaseModel):
    """Single place analysis result."""
    
    name: str = Field(..., description="Place name")
    address: Optional[str] = Field(None, description="Place address")
    category: str = Field(..., description="Place category")
    confidence: AnalysisConfidence = Field(..., description="Confidence level")
    description: Optional[str] = Field(None, description="Place description")
    coordinates: Optional[tuple] = Field(None, description="GPS coordinates if available")


class GeminiRequest(BaseModel):
    """Request to Gemini API."""
    
    content: str = Field(..., description="Text content to analyze")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    platform: str = Field(..., description="Source platform")
    model_version: str = Field("gemini-pro-vision", description="Model version")


class GeminiResponse(BaseModel):
    """Response from Gemini API."""
    
    places: List[PlaceAnalysisResult] = Field(default_factory=list, description="Detected places")
    overall_confidence: AnalysisConfidence = Field(..., description="Overall analysis confidence")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")


class PlaceAnalysisResponse(BaseModel):
    """Response from AI place analysis."""

    success: bool = Field(..., description="Whether analysis was successful")
    place_info: Optional[PlaceInfo] = Field(
        None, description="Extracted place information"
    )
    confidence: float = Field(
        0.0, ge=0.0, le=1.0, description="Analysis confidence score"
    )
    analysis_time: float = Field(0.0, description="Time taken for analysis (seconds)")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    model_version: str = Field("gemini-pro-vision", description="AI model version used")
