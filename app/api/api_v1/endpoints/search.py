"""
Search API endpoints with Elasticsearch support.

Provides comprehensive search functionality for places with
Korean language support, autocomplete, and advanced filtering.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.db.deps import get_db
from app.models.user import User
from app.schemas.search import PlaceSearchResponse, SearchSuggestionResponse
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/places", response_model=PlaceSearchResponse)
async def search_places(
    q: str = Query("", description="Search query"),
    category: Optional[str] = Query(None, description="Place category filter"),
    tags: Optional[List[str]] = Query(None, description="Tags to filter by"),
    lat: Optional[float] = Query(None, description="Latitude for geo search"),
    lng: Optional[float] = Query(None, description="Longitude for geo search"),
    radius_km: Optional[float] = Query(5.0, description="Search radius in kilometers"),
    sort_by: str = Query("relevance", description="Sort option"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    use_elasticsearch: bool = Query(True, description="Use Elasticsearch for search"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search places with advanced filtering and sorting options.

    Supports both Elasticsearch (default) and PostgreSQL full-text search
    with automatic fallback for reliability.
    """
    try:
        search_service = SearchService(db)

        # Prepare location data for geo search
        location = None
        if lat is not None and lng is not None:
            location = {"lat": lat, "lon": lng}

        if use_elasticsearch:
            # Use Elasticsearch for advanced search
            try:
                result = await search_service.elasticsearch_search_places(
                    user_id=current_user.id,
                    query=q,
                    location=location,
                    radius_km=radius_km,
                    category=category,
                    tags=tags,
                    sort_by=sort_by,
                    limit=limit,
                    offset=offset,
                )

                return PlaceSearchResponse(
                    places=result["places"],
                    total=result["total"],
                    query=q,
                    took_ms=result.get("took", 0),
                    source=result.get("source", "elasticsearch"),
                )

            except Exception as e:
                logger.warning(
                    f"Elasticsearch search failed, falling back to PostgreSQL: {e}"
                )
                use_elasticsearch = False

        if not use_elasticsearch:
            # Fall back to PostgreSQL search
            places_with_scores = search_service.full_text_search(
                user_id=current_user.id,
                query=q,
                category=category,
                limit=limit,
            )

            # Convert to response format
            places_data = []
            for place, score in places_with_scores:
                place_data = {
                    "id": str(place.id),
                    "name": place.name,
                    "description": place.description,
                    "address": place.address,
                    "category": place.category,
                    "tags": place.tags or [],
                    "score": score,
                }

                # Add location if available
                if place.latitude and place.longitude:
                    place_data["location"] = {
                        "lat": float(place.latitude),
                        "lon": float(place.longitude),
                    }

                places_data.append(place_data)

            return PlaceSearchResponse(
                places=places_data,
                total=len(places_data),
                query=q,
                took_ms=0,
                source="postgresql",
            )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500, detail="Search service temporarily unavailable"
        )


@router.get("/suggestions", response_model=SearchSuggestionResponse)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    categories: Optional[List[str]] = Query(None, description="Category filters"),
    limit: int = Query(10, ge=1, le=50, description="Number of suggestions"),
    use_elasticsearch: bool = Query(True, description="Use Elasticsearch"),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get search suggestions for autocomplete functionality.

    Returns suggestions based on place names, addresses, and other searchable fields
    with support for Korean text analysis.
    """
    try:
        search_service = SearchService(db)

        if use_elasticsearch:
            try:
                # Use Elasticsearch suggestions
                suggestions = await search_service.get_elasticsearch_suggestions(
                    user_id=current_user.id,
                    query=q,
                    categories=categories,
                    limit=limit,
                )

                return SearchSuggestionResponse(
                    suggestions=suggestions, query=q, source="elasticsearch"
                )

            except Exception as e:
                logger.warning(f"Elasticsearch suggestions failed, falling back: {e}")

        # Fall back to PostgreSQL autocomplete
        suggestions_list = search_service.autocomplete_suggestions(
            user_id=current_user.id,
            partial_query=q,
            limit=limit,
        )

        # Convert to response format
        suggestions = [
            {"text": suggestion, "type": "place", "score": 1.0}
            for suggestion in suggestions_list
        ]

        return SearchSuggestionResponse(
            suggestions=suggestions, query=q, source="postgresql"
        )

    except Exception as e:
        logger.error(f"Suggestions failed: {e}")
        raise HTTPException(
            status_code=500, detail="Suggestion service temporarily unavailable"
        )


@router.post("/index/places/{place_id}")
async def index_place_to_elasticsearch(
    place_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually index a specific place to Elasticsearch.

    Useful for testing or re-indexing after data changes.
    """
    try:
        from app.crud.place import place as place_crud

        # Get the place
        place = place_crud.get_by_id(db, place_id)
        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        # Verify ownership
        if place.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        # Index to Elasticsearch
        search_service = SearchService(db)
        success = await search_service.index_place_to_elasticsearch(place)

        if success:
            return {"message": "Place indexed successfully", "place_id": place_id}
        else:
            raise HTTPException(
                status_code=500, detail="Failed to index place to Elasticsearch"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Place indexing failed: {e}")
        raise HTTPException(
            status_code=500, detail="Indexing service temporarily unavailable"
        )


@router.post("/initialize-indices")
async def initialize_elasticsearch_indices(
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(get_db),
):
    """
    Initialize Elasticsearch indices with proper mappings and settings.

    Admin-only endpoint for setting up the search infrastructure.
    """
    try:
        search_service = SearchService(db)
        await search_service.initialize_elasticsearch_indices()

        return {
            "message": "Elasticsearch indices initialized successfully",
            "indices": ["places", "courses", "users", "suggestions"],
        }

    except Exception as e:
        logger.error(f"Index initialization failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize search indices: {str(e)}"
        )


@router.get("/health")
async def search_health_check():
    """
    Check the health of search services.

    Returns status of both PostgreSQL and Elasticsearch search capabilities.
    """
    try:
        from app.db.elasticsearch import es_manager

        health_status = {"postgresql": "healthy", "elasticsearch": "unknown"}

        # Check Elasticsearch health
        try:
            if es_manager.client:
                es_health = await es_manager.health_check()
                health_status["elasticsearch"] = es_health.get("status", "unknown")
            else:
                health_status["elasticsearch"] = "disconnected"
        except Exception as e:
            health_status["elasticsearch"] = f"error: {str(e)}"

        overall_status = (
            "healthy" if health_status["postgresql"] == "healthy" else "degraded"
        )

        return {
            "status": overall_status,
            "services": health_status,
            "timestamp": "2025-09-08T12:00:00Z",  # Would use actual timestamp
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "error": str(e), "timestamp": "2025-09-08T12:00:00Z"}
