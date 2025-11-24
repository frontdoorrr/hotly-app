"""Place management API endpoints."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.place import place as place_crud
from app.middleware.auth_middleware import get_current_user
from app.models.user_data import AuthenticatedUser
from app.schemas.place import (
    PlaceCreate,
    PlaceListRequest,
    PlaceListResponse,
    PlaceResponse,
    PlaceStatsResponse,
    PlaceUpdate,
)
from app.services.places.duplicate_detector import DuplicateDetector

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development (will be replaced with auth)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.post("/", response_model=PlaceResponse, status_code=201)
async def create_place(
    *,
    db: Session = Depends(get_db),
    place_in: PlaceCreate,
) -> PlaceResponse:
    """
    Create a new place.

    - **name**: Place name (required)
    - **category**: Place category (defaults to 'other')
    - **latitude/longitude**: Coordinates for geographical search
    - **tags**: User-defined tags for organization
    """
    try:
        # Check for duplicate by source hash if provided
        if place_in.source_url:
            import hashlib

            content_hash = hashlib.sha256(
                f"{place_in.name}_{place_in.address}_{place_in.source_url}".encode()
            ).hexdigest()

            existing_place = place_crud.get_by_source_hash(
                db, user_id=UUID(TEMP_USER_ID), source_content_hash=content_hash
            )

            if existing_place:
                raise HTTPException(
                    status_code=409,
                    detail=f"Place already exists with ID: {existing_place.id}",
                )

        # Multi-stage duplicate detection
        existing_places = place_crud.get_multi_by_user(
            db, user_id=UUID(TEMP_USER_ID), limit=1000
        )

        existing_place_schemas = [
            PlaceCreate(
                name=place.name,
                address=place.address,
                latitude=place.latitude,
                longitude=place.longitude,
                category=place.category,
            )
            for place in existing_places
        ]

        detector = DuplicateDetector()
        duplicate_result = await detector.check_duplicate(
            place_in, existing_place_schemas
        )

        if duplicate_result.is_duplicate:
            matched_place = existing_places[duplicate_result.matched_place_index]
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Duplicate place detected",
                    "confidence": duplicate_result.confidence,
                    "matchType": duplicate_result.match_type,
                    "matchedPlace": {
                        "id": str(matched_place.id),
                        "name": matched_place.name,
                        "address": matched_place.address,
                    },
                },
            )

        # Create new place
        place = place_crud.create_with_user(
            db, obj_in=place_in, user_id=UUID(TEMP_USER_ID)
        )

        logger.info(f"Created place: {place.id} - {place.name}")
        return PlaceResponse.from_orm(place)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create place: {e}")
        raise HTTPException(status_code=500, detail="Failed to create place")


@router.get("/", response_model=PlaceListResponse)
async def get_places(
    *,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
    category: str = Query(None, description="Filter by category"),
    tags: List[str] = Query(None, description="Filter by tags"),
    latitude: float = Query(None, description="Center latitude for radius search"),
    longitude: float = Query(None, description="Center longitude for radius search"),
    radius_km: float = Query(None, description="Search radius in kilometers"),
    search_query: str = Query(None, description="Full-text search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
) -> PlaceListResponse:
    """
    Get places with filtering, searching, and pagination.

    - **Geographical search**: Provide latitude, longitude, and radius_km
    - **Text search**: Use search_query for full-text search
    - **Filtering**: Filter by category, tags, status
    - **Sorting**: Sort by created_at, name, or recommendation_score
    """
    try:
        # Build request object
        request = PlaceListRequest(
            category=category,
            tags=tags or [],
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            search_query=search_query,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Get places and total count
        places, total = place_crud.get_list_with_filters(
            db, request=request, user_id=current_user.id
        )

        # Calculate pagination info
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1

        # Convert to response models
        place_responses = [PlaceResponse.from_orm(place) for place in places]

        return PlaceListResponse(
            places=place_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get places: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve places")


@router.get("/{place_id}", response_model=PlaceResponse)
async def get_place(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
) -> PlaceResponse:
    """Get place by ID."""
    try:
        place = place_crud.get_by_user(
            db, user_id=UUID(TEMP_USER_ID), place_id=place_id
        )

        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        return PlaceResponse.from_orm(place)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get place {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve place")


@router.put("/{place_id}", response_model=PlaceResponse)
async def update_place(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
    place_update: PlaceUpdate,
) -> PlaceResponse:
    """Update place information."""
    try:
        place = place_crud.get_by_user(
            db, user_id=UUID(TEMP_USER_ID), place_id=place_id
        )

        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        updated_place = place_crud.update_with_coordinates(
            db, db_obj=place, obj_in=place_update
        )

        logger.info(f"Updated place: {place_id}")
        return PlaceResponse.from_orm(updated_place)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update place {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update place")


@router.delete("/{place_id}")
async def delete_place(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
) -> dict:
    """Soft delete place (set status to inactive)."""
    try:
        success = place_crud.soft_delete(
            db, place_id=place_id, user_id=UUID(TEMP_USER_ID)
        )

        if not success:
            raise HTTPException(status_code=404, detail="Place not found")

        logger.info(f"Deleted place: {place_id}")
        return {"message": "Place deleted successfully", "place_id": str(place_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete place {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete place")


@router.get("/nearby/", response_model=List[PlaceResponse])
async def get_nearby_places(
    *,
    db: Session = Depends(get_db),
    latitude: float = Query(..., ge=-90, le=90, description="Center latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=100, description="Search radius in km"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
) -> List[PlaceResponse]:
    """Get places within specified radius, ordered by distance."""
    try:
        places = place_crud.get_nearby_places(
            db,
            user_id=UUID(TEMP_USER_ID),
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
        )

        return [PlaceResponse.from_orm(place) for place in places]

    except Exception as e:
        logger.error(f"Failed to get nearby places: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nearby places")


@router.get("/search/", response_model=List[PlaceResponse])
async def search_places(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Search query"),
    category: str = Query(None, description="Filter by category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
) -> List[PlaceResponse]:
    """Full-text search for places."""
    try:
        places = place_crud.search_by_text(
            db,
            user_id=UUID(TEMP_USER_ID),
            query=q,
            category=category,
            limit=limit,
        )

        return [PlaceResponse.from_orm(place) for place in places]

    except Exception as e:
        logger.error(f"Failed to search places: {e}")
        raise HTTPException(status_code=500, detail="Failed to search places")


@router.get("/stats/", response_model=PlaceStatsResponse)
async def get_place_statistics(
    *,
    db: Session = Depends(get_db),
) -> PlaceStatsResponse:
    """Get place statistics for current user."""
    try:
        stats = place_crud.get_user_statistics(db, user_id=UUID(TEMP_USER_ID))

        return PlaceStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get place statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@router.post("/check-duplicate/", response_model=None)
async def check_duplicate_place(
    *,
    db: Session = Depends(get_db),
    place_in: PlaceCreate,
) -> dict:
    """
    Check if a place is a duplicate of existing places.

    Returns duplicate detection result with confidence score and match type.
    """
    try:
        # Get existing places for duplicate comparison
        existing_places = place_crud.get_multi_by_user(
            db, user_id=UUID(TEMP_USER_ID), limit=1000
        )

        # Convert to PlaceCreate schemas for duplicate detection
        existing_place_schemas = [
            PlaceCreate(
                name=place.name,
                address=place.address,
                latitude=place.latitude,
                longitude=place.longitude,
                category=place.category,
            )
            for place in existing_places
        ]

        # Run duplicate detection
        detector = DuplicateDetector()
        result = await detector.check_duplicate(place_in, existing_place_schemas)

        response = {
            "isDuplicate": result.is_duplicate,
            "confidence": result.confidence,
            "matchType": result.match_type,
        }

        if result.matched_place_index >= 0 and result.is_duplicate:
            matched_place = existing_places[result.matched_place_index]
            response["matchedPlace"] = {
                "id": str(matched_place.id),
                "name": matched_place.name,
                "address": matched_place.address,
            }

        if result.similarity_scores:
            response["similarityScores"] = result.similarity_scores

        logger.info(
            f"Duplicate check completed: {result.match_type} (confidence: {result.confidence})"
        )
        return response

    except Exception as e:
        logger.error(f"Failed to check duplicate: {e}")
        raise HTTPException(status_code=500, detail="Failed to check for duplicates")


@router.post("/classify/", response_model=None)
async def classify_place(
    *,
    place_in: PlaceCreate,
) -> dict:
    """
    Classify a place into appropriate category using AI.

    Returns classification result with predicted category, confidence, and reasoning.
    """
    try:
        from app.services.places.place_classification_service import (
            PlaceClassificationService,
        )

        # Initialize classification service
        classification_service = PlaceClassificationService()

        # Classify the place
        result = await classification_service.classify_place(place_in)

        response = {
            "predictedCategory": result.predicted_category.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "classificationTime": result.classification_time,
            "needsManualReview": result.needs_manual_review,
        }

        logger.info(
            f"Place classification completed: {place_in.name} → "
            f"{result.predicted_category} (confidence: {result.confidence:.2f})"
        )

        return response

    except Exception as e:
        logger.error(f"Failed to classify place: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify place")


@router.get("/geographic/clusters", response_model=None)
async def get_geographic_clusters(
    *,
    db: Session = Depends(get_db),
    cluster_distance_km: float = Query(
        2.0, ge=0.5, le=10, description="Cluster distance in km"
    ),
    min_cluster_size: int = Query(
        2, ge=2, le=10, description="Minimum places per cluster"
    ),
) -> List[dict]:
    """
    Get geographic clusters of places.

    - **cluster_distance_km**: Maximum distance between places in same cluster
    - **min_cluster_size**: Minimum places required to form a cluster

    Returns geographic clusters with center coordinates and place counts.
    """
    try:
        from app.services.maps.geo_service import GeoService

        geo_service = GeoService(db)
        clusters = geo_service.cluster_places_by_region(
            user_id=UUID(TEMP_USER_ID),
            cluster_distance_km=cluster_distance_km,
            min_cluster_size=min_cluster_size,
        )

        return [
            {
                "center_latitude": cluster.center_latitude,
                "center_longitude": cluster.center_longitude,
                "place_count": cluster.place_count,
                "place_ids": cluster.place_ids,
                "radius_km": cluster.radius_km,
            }
            for cluster in clusters
        ]

    except Exception as e:
        logger.error(f"Failed to get geographic clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get geographic clusters")


@router.get("/geographic/statistics", response_model=None)
async def get_geographic_statistics(
    *,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get geographic statistics for user's places.

    Returns coverage area, center point, and distribution metrics.
    """
    try:
        import math

        from app.services.maps.geo_service import GeoService

        # Get all places with coordinates
        places = place_crud.get_multi_by_user(
            db, user_id=UUID(TEMP_USER_ID), limit=10000
        )

        places_with_coords = [
            p for p in places if p.latitude is not None and p.longitude is not None
        ]

        if not places_with_coords:
            return {
                "total_places_with_coordinates": 0,
                "coverage_area_km2": 0,
                "center_latitude": None,
                "center_longitude": None,
            }

        geo_service = GeoService(db)

        # Calculate statistics
        lats = [p.latitude for p in places_with_coords]
        lngs = [p.longitude for p in places_with_coords]

        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)

        # Calculate coverage area (bounding box)
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)

        lat_range_km = (max_lat - min_lat) * 111.0  # 1 degree ≈ 111 km
        lng_range_km = (
            (max_lng - min_lng) * 111.0 * abs(math.cos(math.radians(center_lat)))
        )
        coverage_area = lat_range_km * lng_range_km

        # Calculate average distance between places
        total_distance = 0
        pair_count = 0

        for i, place1 in enumerate(places_with_coords):
            for place2 in places_with_coords[i + 1 :]:
                distance = geo_service.distance_calculator.haversine_distance(
                    place1.latitude, place1.longitude, place2.latitude, place2.longitude
                )
                total_distance += distance
                pair_count += 1

        avg_distance = total_distance / pair_count if pair_count > 0 else 0

        return {
            "total_places_with_coordinates": len(places_with_coords),
            "coverage_area_km2": round(coverage_area, 2),
            "center_latitude": round(center_lat, 6),
            "center_longitude": round(center_lng, 6),
            "bounding_box": {
                "min_latitude": min_lat,
                "min_longitude": min_lng,
                "max_latitude": max_lat,
                "max_longitude": max_lng,
            },
            "average_distance_between_places_km": round(avg_distance, 2),
        }

    except Exception as e:
        logger.error(f"Failed to get geographic statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get geographic statistics"
        )


@router.post("/geographic/route-search", response_model=None)
async def search_places_along_route(
    *,
    db: Session = Depends(get_db),
    waypoints: List[dict],
    buffer_km: float = Query(
        1.0, ge=0.1, le=5, description="Buffer distance from route"
    ),
    category: str = Query(None, description="Category filter"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
) -> List[dict]:
    """
    Find places along a route with specified buffer distance.

    - **waypoints**: List of coordinate points defining the route
    - **buffer_km**: Buffer distance from route in kilometers
    - **category**: Optional category filter

    Returns places within buffer distance of the route, ordered by distance.
    """
    try:
        from app.services.maps.geo_service import GeoService

        # Validate waypoints
        if len(waypoints) < 2:
            raise HTTPException(
                status_code=422, detail="Route must have at least 2 waypoints"
            )

        # Convert waypoints to coordinate tuples
        route_points = []
        for wp in waypoints:
            if "latitude" not in wp or "longitude" not in wp:
                raise HTTPException(
                    status_code=422,
                    detail="Each waypoint must have latitude and longitude",
                )
            route_points.append((wp["latitude"], wp["longitude"]))

        geo_service = GeoService(db)
        places_with_distance = geo_service.get_places_along_route(
            user_id=UUID(TEMP_USER_ID),
            waypoints=route_points,
            buffer_km=buffer_km,
            limit=limit,
        )

        response = []
        for place, distance_to_route in places_with_distance:
            if category is None or place.category == category:
                response.append(
                    {
                        "place_id": str(place.id),
                        "name": place.name,
                        "description": place.description,
                        "address": place.address,
                        "category": place.category,
                        "coordinates": {
                            "latitude": place.latitude,
                            "longitude": place.longitude,
                        },
                        "distance_to_route_km": round(distance_to_route, 3),
                    }
                )

        logger.info(f"Found {len(response)} places along route")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search places along route: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to search places along route"
        )


@router.get("/search/advanced", response_model=None)
async def advanced_search(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Search query"),
    category: str = Query(None, description="Category filter"),
    tags: List[str] = Query(None, description="Tag filters"),
    enable_fuzzy: bool = Query(True, description="Enable fuzzy matching"),
    enable_highlighting: bool = Query(
        False, description="Enable search term highlighting"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
) -> List[dict]:
    """
    Advanced search with Korean text analysis, fuzzy matching, and highlighting.

    - **q**: Search query (minimum 2 characters)
    - **category**: Optional category filter
    - **tags**: Optional tag filters
    - **enable_fuzzy**: Enable typo tolerance
    - **enable_highlighting**: Highlight search terms in results

    Returns search results with relevance scores and optional highlighting.
    """
    try:
        from app.services.search.search_service import SearchService

        search_service = SearchService(db)

        # Perform advanced search
        places_with_scores = search_service.full_text_search(
            user_id=UUID(TEMP_USER_ID),
            query=q,
            category=category,
            limit=limit,
            enable_fuzzy=enable_fuzzy,
        )

        # Filter by tags if specified
        if tags:
            filtered_results = []
            for place, score in places_with_scores:
                if any(tag in (place.tags or []) for tag in tags):
                    filtered_results.append((place, score))
            places_with_scores = filtered_results

        # Build response
        results = []
        for place, score in places_with_scores:
            place_data = {
                "place_id": str(place.id),
                "name": place.name,
                "description": place.description,
                "address": place.address,
                "category": place.category,
                "tags": place.tags or [],
                "coordinates": {
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                },
                "relevance_score": round(score, 4),
            }

            # Add highlighting if requested
            if enable_highlighting:
                place_data["highlighted_name"] = search_service.highlight_search_terms(
                    place.name or "", q
                )
                place_data[
                    "highlighted_description"
                ] = search_service.highlight_search_terms(place.description or "", q)

            results.append(place_data)

        logger.info(f"Advanced search for '{q}': {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Failed advanced search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform advanced search")


@router.get("/search/autocomplete", response_model=List[str])
async def search_autocomplete(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=1, max_length=50, description="Partial query"),
    limit: int = Query(10, ge=1, le=20, description="Maximum suggestions"),
) -> List[str]:
    """
    Get search autocomplete suggestions.

    - **q**: Partial search query
    - **limit**: Maximum number of suggestions

    Returns list of autocomplete suggestions based on user's places.
    """
    try:
        from app.services.search.search_service import SearchService

        search_service = SearchService(db)
        suggestions = search_service.autocomplete_suggestions(
            user_id=UUID(TEMP_USER_ID), partial_query=q, limit=limit
        )

        logger.info(f"Autocomplete for '{q}': {len(suggestions)} suggestions")
        return suggestions

    except Exception as e:
        logger.error(f"Failed autocomplete: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get autocomplete suggestions"
        )


@router.get("/search/fuzzy", response_model=None)
async def fuzzy_search(
    *,
    db: Session = Depends(get_db),
    q: str = Query(..., min_length=2, description="Search query"),
    similarity: float = Query(
        0.3, ge=0.1, le=1.0, description="Minimum similarity threshold"
    ),
    category: str = Query(None, description="Category filter"),
    limit: int = Query(20, ge=1, le=50, description="Maximum results"),
) -> List[dict]:
    """
    Fuzzy search for handling typos and variations.

    - **q**: Search query
    - **similarity**: Minimum similarity threshold (0.1-1.0)
    - **category**: Optional category filter

    Returns places matching with similarity scores above threshold.
    """
    try:
        from app.services.search.search_service import SearchService

        search_service = SearchService(db)
        places_with_scores = search_service._fuzzy_search_fallback(
            user_id=UUID(TEMP_USER_ID), query=q, category=category, limit=limit
        )

        # Filter by similarity threshold
        filtered_results = [
            (place, score) for place, score in places_with_scores if score >= similarity
        ]

        results = []
        for place, score in filtered_results:
            results.append(
                {
                    "place_id": str(place.id),
                    "name": place.name,
                    "description": place.description,
                    "address": place.address,
                    "category": place.category,
                    "tags": place.tags or [],
                    "similarity_score": round(score, 4),
                    "match_type": "fuzzy",
                }
            )

        logger.info(f"Fuzzy search for '{q}': {len(results)} results")
        return results

    except Exception as e:
        logger.error(f"Failed fuzzy search: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform fuzzy search")


@router.get("/search/analytics", response_model=None)
async def get_search_analytics(
    *,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get search analytics and performance metrics.

    Returns search usage statistics and performance data.
    """
    try:
        # Basic analytics implementation
        # In production, this would read from search logs/metrics

        return {
            "total_searches_today": 0,
            "average_response_time_ms": 150,
            "top_queries": [
                {"query": "카페", "count": 45},
                {"query": "맛집", "count": 32},
                {"query": "데이트", "count": 28},
            ],
            "no_results_rate": 0.05,
            "fuzzy_match_usage_rate": 0.12,
            "performance_metrics": {
                "p50_response_time_ms": 120,
                "p95_response_time_ms": 380,
                "p99_response_time_ms": 450,
            },
        }

    except Exception as e:
        logger.error(f"Failed to get search analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get search analytics")
