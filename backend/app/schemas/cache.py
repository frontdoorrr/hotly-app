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


class CacheKey:
    """Cache key generation utilities."""

    @staticmethod
    def link_analysis(url: str) -> str:
        """Generate cache key for link analysis results."""
        import hashlib
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(url)

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
            "igshid",
            "_ga",
            "source",
        }

        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }

        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

        # Normalize the URL (convert to lowercase, normalize path)
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.lower().rstrip("/")
                or "/",  # Convert path to lowercase and normalize
                parsed.params,
                new_query,
                "",  # Remove fragment
            )
        )

        url_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return f"hotly:link_analysis:{url_hash}"

    @staticmethod
    def metadata_extraction(url: str) -> str:
        """Generate cache key for metadata extraction results."""
        # Reuse the same normalization logic
        link_key = CacheKey.link_analysis(url)
        return link_key.replace("link_analysis", "metadata")

    @staticmethod
    def ai_analysis(url: str) -> str:
        """Generate cache key for AI analysis results."""
        # Reuse the same normalization logic
        link_key = CacheKey.link_analysis(url)
        return link_key.replace("link_analysis", "ai_analysis")


class CacheEntry(BaseModel):
    """Cache entry with TTL and expiration checking."""

    data: Any = Field(..., description="Cached data")
    ttl: int = Field(..., ge=1, description="Time to live in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        from datetime import timedelta, timezone

        expiry_time = self.created_at + timedelta(seconds=self.ttl)
        return datetime.now(timezone.utc) > expiry_time

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CacheStats(BaseModel):
    """Enhanced cache statistics."""

    cache_hits: int = Field(0, ge=0, description="Total cache hits")
    cache_misses: int = Field(0, ge=0, description="Total cache misses")
    l1_hits: int = Field(0, ge=0, description="Local cache hits")
    l2_hits: int = Field(0, ge=0, description="Redis cache hits")
    total_requests: int = Field(0, ge=0, description="Total requests")

    @property
    def hit_rate(self) -> float:
        """Overall cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def l1_hit_rate(self) -> float:
        """L1 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l1_hits / self.total_requests

    @property
    def l2_hit_rate(self) -> float:
        """L2 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l2_hits / self.total_requests


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


class CacheKey:
    """Cache key generation utilities."""

    @staticmethod
    def link_analysis(url: str) -> str:
        """Generate cache key for link analysis results."""
        import hashlib
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        parsed = urlparse(url)

        # Remove common tracking parameters
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "fbclid",
            "gclid",
            "ref",
            "igshid",
            "_ga",
            "source",
        }

        query_params = parse_qs(parsed.query)
        filtered_params = {
            k: v for k, v in query_params.items() if k.lower() not in tracking_params
        }

        # Rebuild query string
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ""

        # Normalize the URL (convert to lowercase, normalize path)
        normalized = urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.lower().rstrip("/")
                or "/",  # Convert path to lowercase and normalize
                parsed.params,
                new_query,
                "",  # Remove fragment
            )
        )

        url_hash = hashlib.sha256(normalized.encode()).hexdigest()
        return f"hotly:link_analysis:{url_hash}"

    @staticmethod
    def metadata_extraction(url: str) -> str:
        """Generate cache key for metadata extraction results."""
        # Reuse the same normalization logic
        link_key = CacheKey.link_analysis(url)
        return link_key.replace("link_analysis", "metadata")

    @staticmethod
    def ai_analysis(url: str) -> str:
        """Generate cache key for AI analysis results."""
        # Reuse the same normalization logic
        link_key = CacheKey.link_analysis(url)
        return link_key.replace("link_analysis", "ai_analysis")


class CacheEntry(BaseModel):
    """Cache entry with TTL and expiration checking."""

    data: Any = Field(..., description="Cached data")
    ttl: int = Field(..., ge=1, description="Time to live in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        from datetime import timedelta, timezone

        expiry_time = self.created_at + timedelta(seconds=self.ttl)
        return datetime.now(timezone.utc) > expiry_time

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CacheStats(BaseModel):
    """Enhanced cache statistics."""

    cache_hits: int = Field(0, ge=0, description="Total cache hits")
    cache_misses: int = Field(0, ge=0, description="Total cache misses")
    l1_hits: int = Field(0, ge=0, description="Local cache hits")
    l2_hits: int = Field(0, ge=0, description="Redis cache hits")
    total_requests: int = Field(0, ge=0, description="Total requests")

    @property
    def hit_rate(self) -> float:
        """Overall cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests

    @property
    def l1_hit_rate(self) -> float:
        """L1 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l1_hits / self.total_requests

    @property
    def l2_hit_rate(self) -> float:
        """L2 cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.l2_hits / self.total_requests
