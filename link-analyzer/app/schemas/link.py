"""Link analysis request/response schemas."""
from typing import Optional, Dict, Any

from pydantic import BaseModel, HttpUrl, Field


class LinkAnalysisRequest(BaseModel):
    """Request schema for link analysis."""

    url: HttpUrl = Field(..., description="URL to analyze")


class LinkAnalysisResponse(BaseModel):
    """Response schema for link analysis."""

    url: str = Field(..., description="Analyzed URL")
    title: Optional[str] = Field(None, description="Page title")
    description: Optional[str] = Field(None, description="Page description")
    platform: Optional[str] = Field(None, description="Detected platform (instagram, blog, youtube, etc)")
    content_type: Optional[str] = Field(None, description="Type of content (place, restaurant, cafe, etc)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.instagram.com/p/example/",
                "title": "Example Post",
                "description": "This is an example post description",
                "platform": "instagram",
                "content_type": "restaurant",
                "metadata": {
                    "author": "user123",
                    "posted_at": "2024-01-01"
                }
            }
        }
