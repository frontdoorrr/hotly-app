"""Place-related Pydantic schemas for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class PlaceStatus(str, Enum):
    """Place status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class PlaceCategory(str, Enum):
    """Place category enumeration."""

    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    TOURIST_ATTRACTION = "tourist_attraction"
    SHOPPING = "shopping"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class PlaceBase(BaseModel):
    """Base place schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Place name")
    description: Optional[str] = Field(
        None, max_length=2000, description="Place description"
    )
    address: Optional[str] = Field(None, max_length=500, description="Place address")
    phone: Optional[str] = Field(
        None, max_length=50, description="Contact phone number"
    )
    website: Optional[str] = Field(None, max_length=500, description="Website URL")
    opening_hours: Optional[str] = Field(None, description="Opening hours information")
    price_range: Optional[str] = Field(None, max_length=50, description="Price range")
    category: PlaceCategory = Field(
        default=PlaceCategory.OTHER, description="Place category"
    )
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    keywords: List[str] = Field(
        default_factory=list, description="Characteristic keywords"
    )

    @validator("tags")
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate and normalize tags."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]

    @validator("keywords")
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Validate and normalize keywords."""
        if len(v) > 15:
            raise ValueError("Maximum 15 keywords allowed")
        return [keyword.strip() for keyword in v if keyword.strip()]

    @validator("website")
    def validate_website_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate website URL format."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Website URL must start with http:// or https://")
        return v


class PlaceCreate(PlaceBase):
    """Schema for creating a new place."""

    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Latitude coordinate"
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="Longitude coordinate"
    )
    source_url: Optional[str] = Field(
        None, max_length=1000, description="Original SNS URL"
    )
    source_platform: Optional[str] = Field(
        None, max_length=50, description="Source platform"
    )
    ai_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="AI analysis confidence"
    )
    ai_model_version: Optional[str] = Field(
        None, max_length=100, description="AI model version"
    )
    recommendation_score: Optional[int] = Field(
        None, ge=1, le=10, description="Recommendation score"
    )


class PlaceUpdate(BaseModel):
    """Schema for updating an existing place."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    opening_hours: Optional[str] = None
    price_range: Optional[str] = Field(None, max_length=50)
    category: Optional[PlaceCategory] = None
    tags: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    status: Optional[PlaceStatus] = None
    is_verified: Optional[bool] = None

    @validator("tags")
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize tags."""
        if v is None:
            return None
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.lower().strip() for tag in v if tag.strip()]

    @validator("keywords")
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate and normalize keywords."""
        if v is None:
            return None
        if len(v) > 15:
            raise ValueError("Maximum 15 keywords allowed")
        return [keyword.strip() for keyword in v if keyword.strip()]


class PlaceInDB(PlaceBase):
    """Place schema as stored in database."""

    id: UUID = Field(..., description="Place unique identifier")
    user_id: UUID = Field(..., description="Owner user ID")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    ai_confidence: Optional[float] = Field(None, description="AI analysis confidence")
    ai_model_version: Optional[str] = Field(None, description="AI model version")
    recommendation_score: Optional[int] = Field(
        None, description="Recommendation score"
    )
    source_url: Optional[str] = Field(None, description="Original SNS URL")
    source_platform: Optional[str] = Field(None, description="Source platform")
    source_content_hash: Optional[str] = Field(
        None, description="Content hash for deduplication"
    )
    status: PlaceStatus = Field(default=PlaceStatus.ACTIVE, description="Place status")
    is_verified: bool = Field(default=False, description="Whether place is verified")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True


class PlaceResponse(PlaceInDB):
    """Public place response schema."""

    # Hide internal fields from public API
    source_content_hash: Optional[str] = Field(None, exclude=True)
    ai_model_version: Optional[str] = Field(None, exclude=True)

    class Config:
        @staticmethod
        def alias_generator(field_name: str) -> str:
            """Convert snake_case to camelCase for external API."""
            return "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(field_name.split("_"))
            )

        allow_population_by_field_name = True


class PlaceListRequest(BaseModel):
    """Request schema for place list with filtering and pagination."""

    category: Optional[PlaceCategory] = Field(None, description="Filter by category")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    status: Optional[PlaceStatus] = Field(
        default=PlaceStatus.ACTIVE, description="Filter by status"
    )
    latitude: Optional[float] = Field(
        None, ge=-90, le=90, description="Center latitude for radius search"
    )
    longitude: Optional[float] = Field(
        None, ge=-180, le=180, description="Center longitude for radius search"
    )
    radius_km: Optional[float] = Field(
        None, ge=0.1, le=100, description="Search radius in kilometers"
    )
    search_query: Optional[str] = Field(
        None, max_length=200, description="Full-text search query"
    )
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field(
        "desc", regex="^(asc|desc)$", description="Sort order"
    )

    @validator("radius_km")
    def validate_radius_with_coordinates(
        cls, v: Optional[float], values: dict
    ) -> Optional[float]:
        """Validate radius only when coordinates are provided."""
        if v is not None:
            if values.get("latitude") is None or values.get("longitude") is None:
                raise ValueError("Latitude and longitude required for radius search")
        return v


class PlaceListResponse(BaseModel):
    """Response schema for place list with pagination."""

    places: List[PlaceResponse] = Field(..., description="List of places")
    total: int = Field(..., ge=0, description="Total number of places")
    page: int = Field(..., ge=1, description="Current page")
    page_size: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether next page exists")
    has_previous: bool = Field(..., description="Whether previous page exists")

    class Config:
        @staticmethod
        def alias_generator(field_name: str) -> str:
            """Convert snake_case to camelCase for external API."""
            return "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(field_name.split("_"))
            )

        allow_population_by_field_name = True


class PlaceStatsResponse(BaseModel):
    """Place statistics response schema."""

    total_places: int = Field(..., ge=0, description="Total number of places")
    places_by_category: dict = Field(..., description="Place counts by category")
    places_by_status: dict = Field(..., description="Place counts by status")
    average_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Average AI confidence"
    )
    verified_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of verified places"
    )

    class Config:
        @staticmethod
        def alias_generator(field_name: str) -> str:
            """Convert snake_case to camelCase for external API."""
            return "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(field_name.split("_"))
            )

        allow_population_by_field_name = True
