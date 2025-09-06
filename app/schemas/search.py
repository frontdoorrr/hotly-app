"""Search-related Pydantic schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    """Advanced search request with multiple criteria."""

    query: str = Field(..., min_length=1, max_length=100, description="Search query")
    category: Optional[str] = Field(None, description="Category filter")
    tags: List[str] = Field(default_factory=list, description="Tag filters")
    enable_fuzzy: bool = Field(True, description="Enable fuzzy matching for typos")
    boost_factors: Optional[Dict[str, float]] = Field(
        None, description="Field boost weights"
    )
    limit: int = Field(20, ge=1, le=100, description="Maximum results")


class SearchResponse(BaseModel):
    """Search result with relevance information."""

    place_id: str = Field(..., description="Place identifier")
    name: str = Field(..., description="Place name")
    description: Optional[str] = Field(None, description="Place description")
    address: Optional[str] = Field(None, description="Place address")
    category: str = Field(..., description="Place category")
    tags: List[str] = Field(default_factory=list, description="Place tags")
    relevance_score: float = Field(..., description="Search relevance score")
    highlighted_name: Optional[str] = Field(
        None, description="Name with search terms highlighted"
    )
    highlighted_description: Optional[str] = Field(
        None, description="Description with search terms highlighted"
    )
    match_type: str = Field(..., description="Type of match: exact, fuzzy, partial")


class AutocompleteRequest(BaseModel):
    """Autocomplete suggestion request."""

    query: str = Field(
        ..., min_length=1, max_length=50, description="Partial search query"
    )
    limit: int = Field(10, ge=1, le=20, description="Maximum suggestions")
    include_context: bool = Field(False, description="Include context information")


class AutocompleteResponse(BaseModel):
    """Autocomplete suggestion with metadata."""

    suggestion: str = Field(..., description="Suggested completion")
    type: str = Field(..., description="Suggestion type: place_name, keyword, category")
    frequency: int = Field(..., description="Usage frequency")
    context: Optional[str] = Field(None, description="Additional context")


class FuzzySearchRequest(BaseModel):
    """Fuzzy search request for typo tolerance."""

    query: str = Field(..., min_length=2, max_length=100, description="Search query")
    similarity_threshold: float = Field(
        0.3, ge=0.1, le=1.0, description="Minimum similarity score"
    )
    category: Optional[str] = Field(None, description="Category filter")
    limit: int = Field(20, ge=1, le=50, description="Maximum results")


class SearchAnalytics(BaseModel):
    """Search analytics and performance metrics."""

    total_searches: int = Field(..., description="Total search queries")
    average_response_time_ms: float = Field(
        ..., description="Average response time in milliseconds"
    )
    top_queries: List[Dict[str, Any]] = Field(
        ..., description="Most popular search queries"
    )
    no_results_queries: List[str] = Field(
        ..., description="Queries that returned no results"
    )
    fuzzy_match_rate: float = Field(
        ..., description="Percentage of searches using fuzzy matching"
    )


class SearchRankingConfig(BaseModel):
    """Configuration for search result ranking."""

    field_weights: Dict[str, float] = Field(
        default={"name": 3.0, "tags": 2.0, "description": 1.0, "address": 0.5},
        description="Weight factors for different fields",
    )
    recency_boost: float = Field(
        0.1, description="Boost factor for recently created places"
    )
    popularity_boost: float = Field(0.2, description="Boost factor for popular places")
    user_preference_boost: float = Field(
        0.15, description="Boost factor based on user history"
    )


class HighlightedText(BaseModel):
    """Text with highlighted search terms."""

    original: str = Field(..., description="Original text")
    highlighted: str = Field(..., description="Text with highlighted search terms")
    match_positions: List[Dict[str, int]] = Field(
        default_factory=list, description="Positions of matched terms"
    )


class SearchSuggestion(BaseModel):
    """Search suggestion with metadata."""

    query: str = Field(..., description="Suggested query")
    type: str = Field(..., description="Suggestion type")
    score: float = Field(..., description="Relevance score")
    description: Optional[str] = Field(None, description="Suggestion description")


class KoreanTextAnalysis(BaseModel):
    """Korean text analysis result."""

    original_text: str = Field(..., description="Original input text")
    normalized_text: str = Field(..., description="Normalized text")
    keywords: List[str] = Field(..., description="Extracted keywords")
    entities: List[Dict[str, Any]] = Field(
        default_factory=list, description="Named entities"
    )
    complexity_score: float = Field(..., description="Text complexity score")
    language_confidence: float = Field(
        ..., description="Korean language detection confidence"
    )


class SearchPerformanceMetrics(BaseModel):
    """Search performance monitoring metrics."""

    query: str = Field(..., description="Search query")
    execution_time_ms: float = Field(..., description="Query execution time")
    result_count: int = Field(..., description="Number of results returned")
    cache_hit: bool = Field(..., description="Whether result was served from cache")
    index_usage: List[str] = Field(
        default_factory=list, description="Database indexes used"
    )

    @validator("execution_time_ms")
    def validate_execution_time(cls, v):
        if v > 1000:  # 1 second
            logger.warning(f"Slow search query detected: {v}ms")
        return v
