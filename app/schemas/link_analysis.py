"""
Link analysis request/response schemas.

Combines content extraction and AI analysis for complete workflow.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.schemas.ai import PlaceInfo


class AnalysisStatus(str, Enum):
    """Analysis status enumeration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LinkAnalyzeRequest(BaseModel):
    """Request to analyze SNS link."""

    url: str = Field(..., min_length=1, description="SNS URL to analyze")
    force_refresh: bool = Field(False, description="Force refresh ignoring cache")
    webhook_url: Optional[str] = Field(
        None, description="Webhook URL for async notification"
    )

    @validator("url")
    def validate_url_format(cls, v):
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        """Validate webhook URL if provided."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        return v


class ContentSummary(BaseModel):
    """Summary of extracted content."""

    title: Optional[str] = Field(None, description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    image_count: int = Field(0, ge=0, description="Number of images extracted")
    extraction_time: float = Field(
        ..., ge=0, description="Content extraction time in seconds"
    )


class AnalysisResult(BaseModel):
    """Complete analysis result."""

    place_info: Optional[PlaceInfo] = Field(
        None, description="Extracted place information"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Analysis confidence score"
    )
    analysis_time: float = Field(..., ge=0.0, description="AI analysis time in seconds")
    content_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Original content metadata"
    )

    class Config:
        alias_generator = lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        )
        allow_population_by_field_name = True


class LinkAnalyzeResponse(BaseModel):
    """Response for link analysis request."""

    success: bool = Field(..., description="Whether analysis was successful")
    analysis_id: str = Field(..., description="Unique analysis identifier")
    status: AnalysisStatus = Field(..., description="Current analysis status")
    result: Optional[AnalysisResult] = Field(
        None, description="Analysis result if completed"
    )
    error: Optional[str] = Field(None, description="Error message if failed")
    cached: bool = Field(False, description="Whether result was served from cache")
    processing_time: float = Field(
        ..., ge=0.0, description="Total processing time in seconds"
    )

    class Config:
        alias_generator = lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        )
        allow_population_by_field_name = True


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status check."""

    analysis_id: str = Field(..., description="Analysis identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    progress: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Progress percentage"
    )
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated completion time"
    )
    result: Optional[AnalysisResult] = Field(None, description="Result if completed")

    class Config:
        alias_generator = lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        )
        allow_population_by_field_name = True


class BulkAnalyzeRequest(BaseModel):
    """Request for bulk analysis of multiple URLs."""

    urls: List[str] = Field(
        ..., min_items=1, max_items=10, description="URLs to analyze"
    )
    force_refresh: bool = Field(False, description="Force refresh ignoring cache")
    webhook_url: Optional[str] = Field(
        None, description="Webhook URL for completion notification"
    )

    @validator("urls")
    def validate_urls_format(cls, v):
        """Validate all URLs format."""
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"URL {url} must start with http:// or https://")
        return v


class BulkAnalyzeResponse(BaseModel):
    """Response for bulk analysis request."""

    batch_id: str = Field(..., description="Unique batch identifier")
    total_urls: int = Field(..., ge=1, description="Total number of URLs to analyze")
    accepted_urls: List[str] = Field(..., description="URLs accepted for analysis")
    rejected_urls: List[Dict[str, str]] = Field(
        default_factory=list, description="URLs rejected with reasons"
    )
    estimated_completion: Optional[datetime] = Field(
        None, description="Estimated batch completion time"
    )

    class Config:
        alias_generator = lambda field_name: "".join(
            word.capitalize() if i > 0 else word
            for i, word in enumerate(field_name.split("_"))
        )
        allow_population_by_field_name = True
