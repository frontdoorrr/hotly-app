"""Content extraction schemas."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class PlatformType(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    NAVER_BLOG = "naver_blog"
    YOUTUBE = "youtube"


class ContentMetadata(BaseModel):
    """Extracted content metadata."""
    title: Optional[str] = Field(None, description="Content title")
    description: Optional[str] = Field(None, description="Content description")
    images: List[str] = Field(default_factory=list, description="Image URLs")
    location: Optional[str] = Field(None, description="Location mentioned in content")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags found")
    author: Optional[str] = Field(None, description="Content author")
    published_at: Optional[str] = Field(None, description="Publication date")


class ExtractedContent(BaseModel):
    """Complete extracted content result."""
    url: str = Field(..., description="Original URL")
    platform: PlatformType = Field(..., description="Detected platform")
    metadata: ContentMetadata = Field(..., description="Extracted metadata")
    extraction_time: Optional[float] = Field(None, description="Time taken to extract (seconds)")
    
    
class ContentExtractionRequest(BaseModel):
    """Request schema for content extraction."""
    url: HttpUrl = Field(..., description="URL to extract content from")
    force_refresh: bool = Field(False, description="Skip cache and force fresh extraction")


class ContentExtractionResponse(BaseModel):
    """Response schema for content extraction."""
    success: bool = Field(..., description="Whether extraction was successful")
    content: Optional[ExtractedContent] = Field(None, description="Extracted content")
    error: Optional[str] = Field(None, description="Error message if extraction failed")
    cached: bool = Field(False, description="Whether result was served from cache")