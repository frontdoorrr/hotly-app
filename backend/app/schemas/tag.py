"""Tag-related Pydantic schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class TagSuggestionRequest(BaseModel):
    """Request schema for tag suggestions."""

    query: str = Field(..., min_length=1, max_length=20, description="Tag query string")
    limit: Optional[int] = Field(10, ge=1, le=50, description="Maximum suggestions")


class TagSuggestion(BaseModel):
    """Individual tag suggestion with metadata."""

    tag: str = Field(..., description="Normalized tag name")
    usage_count: int = Field(..., ge=0, description="Number of times used")
    match_type: str = Field(
        ..., description="Type of match: prefix, contains, similar, popular"
    )


class TagAddRequest(BaseModel):
    """Request to add tags to a place."""

    tags: List[str] = Field(..., min_items=1, max_items=20, description="Tags to add")

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tag list."""
        if not v:
            raise ValueError("At least one tag must be provided")

        # Check for reasonable tag length
        for tag in v:
            if len(tag.strip()) > 50:
                raise ValueError(f"Tag too long: {tag}")

        return v


class TagRemoveRequest(BaseModel):
    """Request to remove tags from a place."""

    tags: List[str] = Field(..., min_items=1, description="Tags to remove")


class TagOperationResponse(BaseModel):
    """Response for tag add/remove operations."""

    added_tags: Optional[List[str]] = Field(None, description="Successfully added tags")
    removed_tags: Optional[List[str]] = Field(
        None, description="Successfully removed tags"
    )
    total_added: Optional[int] = Field(None, description="Number of tags added")
    total_removed: Optional[int] = Field(None, description="Number of tags removed")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    rejected_tags: List[str] = Field(
        default_factory=list, description="Rejected invalid tags"
    )


class TagStatistics(BaseModel):
    """Tag usage statistics for a user."""

    total_unique_tags: int = Field(..., description="Total number of unique tags")
    total_tag_usage: int = Field(..., description="Total tag usage count")
    most_used_tags: List[Dict[str, Any]] = Field(
        ..., description="Most frequently used tags"
    )
    tag_categories: Dict[str, List[str]] = Field(
        ..., description="Tags grouped by category"
    )
    average_tags_per_place: float = Field(..., description="Average tags per place")
    places_count: int = Field(..., description="Total number of places")


class TrendingTag(BaseModel):
    """Trending tag with growth metrics."""

    tag: str = Field(..., description="Tag name")
    recent_count: int = Field(..., description="Usage in recent period")
    total_count: int = Field(..., description="Total historical usage")
    growth_ratio: float = Field(..., description="Growth ratio")
    trend_score: float = Field(..., description="Calculated trend score")


class TagSuggestionForPlace(BaseModel):
    """Request for place-specific tag suggestions."""

    place_name: str = Field(..., min_length=1, max_length=255, description="Place name")
    place_description: Optional[str] = Field(
        None, max_length=1000, description="Place description"
    )
    max_suggestions: Optional[int] = Field(
        5, ge=1, le=10, description="Maximum suggestions"
    )


class TagMergeOperation(BaseModel):
    """Tag merge operation result."""

    canonical: str = Field(..., description="Canonical tag after merge")
    merged: List[str] = Field(..., description="Tags merged into canonical")


class TagMergeResult(BaseModel):
    """Result of tag merge operations."""

    merges_performed: int = Field(..., description="Number of merges performed")
    operations: List[TagMergeOperation] = Field(
        ..., description="List of merge operations"
    )


class TagValidationResult(BaseModel):
    """Tag validation and normalization result."""

    normalized_tags: List[str] = Field(..., description="Valid normalized tags")
    warnings: List[str] = Field(..., description="Validation warnings")
    rejected_tags: List[str] = Field(..., description="Rejected invalid tags")


class UserTagClusters(BaseModel):
    """User's tags grouped into semantic clusters."""

    clusters: Dict[str, List[str]] = Field(..., description="Tag clusters by category")
    total_categories: int = Field(..., description="Number of categories")
    uncategorized_tags: List[str] = Field(
        default_factory=list, description="Tags not in any category"
    )
