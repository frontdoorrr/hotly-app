"""
Cache-related Pydantic schemas for request/response validation.

Follows consistent API design patterns with camelCase for external APIs.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class CacheEntryData(BaseModel):
    """Cache entry data schema."""

    data: Any = Field(..., description="Cached data payload")
    ttl: int = Field(..., ge=1, description="Time to live in seconds")
    created_at: datetime = Field(..., description="Cache entry creation timestamp")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CacheStatsResponse(BaseModel):
    """Cache statistics response schema."""

    hit_count: int = Field(..., ge=0, description="Number of cache hits")
    miss_count: int = Field(..., ge=0, description="Number of cache misses")
    hit_rate: float = Field(..., ge=0.0, le=1.0, description="Cache hit rate (0.0-1.0)")
    total_requests: int = Field(..., ge=0, description="Total cache requests")

    class Config:
        @staticmethod
        def alias_generator(field_name: str) -> str:
            return "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(field_name.split("_"))
            )

        allow_population_by_field_name = True


class CacheKeyRequest(BaseModel):
    """Request to generate cache key."""

    url: str = Field(..., min_length=1, description="URL to generate cache key for")

    @validator("url")
    def validate_url_format(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class CacheSetRequest(BaseModel):
    """Request to set cache data."""

    url: str = Field(..., min_length=1, description="URL key for caching")
    data: Any = Field(..., description="Data to cache")
    ttl: Optional[int] = Field(
        3600, ge=1, le=86400, description="TTL in seconds (1s-24h)"
    )

    @validator("url")
    def validate_url_format(cls, v: str) -> str:
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class CacheGetResponse(BaseModel):
    """Response for cache get operation."""

    found: bool = Field(..., description="Whether cache entry was found")
    data: Optional[Any] = Field(None, description="Cached data if found")
    created_at: Optional[datetime] = Field(None, description="Cache creation time")
    ttl_remaining: Optional[int] = Field(
        None, ge=0, description="Remaining TTL in seconds"
    )

    class Config:
        @staticmethod
        def alias_generator(field_name: str) -> str:
            return "".join(
                word.capitalize() if i > 0 else word
                for i, word in enumerate(field_name.split("_"))
            )

        allow_population_by_field_name = True
