"""Place management API endpoints."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.place import place as place_crud
from app.schemas.place import (
    PlaceCreate,
    PlaceListRequest,
    PlaceListResponse,
    PlaceResponse,
    PlaceStatsResponse,
    PlaceUpdate,
)
from app.services.duplicate_detector import DuplicateDetector

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development (will be replaced with auth)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


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
            db, request=request, user_id=UUID(TEMP_USER_ID)
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


@router.post("/check-duplicate/", response_model=dict)
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


@router.post("/classify/", response_model=dict)
async def classify_place(
    *,
    place_in: PlaceCreate,
) -> dict:
    """
    Classify a place into appropriate category using AI.

    Returns classification result with predicted category, confidence, and reasoning.
    """
    try:
        from app.services.place_classification_service import PlaceClassificationService

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


@router.put("/{place_id}/status", response_model=PlaceResponse)
async def update_place_status(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
    status: str,
) -> PlaceResponse:
    """
    Update place status (active/inactive).

    - **place_id**: Place UUID
    - **status**: New status ('active' or 'inactive')

    Allows soft activation/deactivation of places without deletion.
    """
    try:
        from app.models.place import PlaceStatus

        # Validate status
        try:
            new_status = PlaceStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid status: {status}. Must be one of: {[s.value for s in PlaceStatus]}",
            )

        # Get and verify place ownership
        place = place_crud.get_by_user(
            db, user_id=UUID(TEMP_USER_ID), place_id=place_id
        )

        if not place:
            raise HTTPException(status_code=404, detail="Place not found")

        # Update status
        place.status = new_status
        db.commit()
        db.refresh(place)

        logger.info(f"Updated place {place_id} status to {new_status}")
        return PlaceResponse.from_orm(place)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update place status {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update place status")


@router.get("/{place_id}/related", response_model=List[PlaceResponse])
async def get_related_places(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
    limit: int = Query(10, ge=1, le=20, description="Maximum related places"),
) -> List[PlaceResponse]:
    """
    Get places related to the given place based on tags, category, and location.

    - **place_id**: Reference place UUID
    - **limit**: Maximum number of related places

    Returns places with similar characteristics ordered by relevance.
    """
    try:
        # Get the reference place
        reference_place = place_crud.get_by_user(
            db, user_id=UUID(TEMP_USER_ID), place_id=place_id
        )

        if not reference_place:
            raise HTTPException(status_code=404, detail="Place not found")

        # Find related places based on multiple criteria
        related_places = place_crud.get_related_places(
            db, user_id=UUID(TEMP_USER_ID), reference_place=reference_place, limit=limit
        )

        return [PlaceResponse.from_orm(place) for place in related_places]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get related places for {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get related places")


@router.get("/export", response_model=dict)
async def export_places(
    *,
    db: Session = Depends(get_db),
    format: str = Query("json", description="Export format: json, csv"),
    category: str = Query(None, description="Filter by category"),
    tags: List[str] = Query(None, description="Filter by tags"),
) -> dict:
    """
    Export user's places in specified format.

    - **format**: Export format (json, csv)
    - **category**: Optional category filter
    - **tags**: Optional tag filters

    Returns export data or download link for large datasets.
    """
    try:
        from datetime import datetime, timedelta

        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=422, detail="Invalid format. Must be 'json' or 'csv'"
            )

        # Get user's places with filters
        request = PlaceListRequest(
            category=category,
            tags=tags or [],
            page=1,
            page_size=10000,  # Large limit for export
            sort_by="created_at",
            sort_order="desc",
        )

        places, total = place_crud.get_list_with_filters(
            db, request=request, user_id=UUID(TEMP_USER_ID)
        )

        if format == "json":
            # Return JSON format
            export_data = {
                "export_info": {
                    "total_places": total,
                    "export_format": "json",
                    "exported_at": datetime.utcnow().isoformat(),
                    "filters": {"category": category, "tags": tags},
                },
                "places": [
                    {
                        "id": str(place.id),
                        "name": place.name,
                        "description": place.description,
                        "address": place.address,
                        "category": place.category,
                        "tags": place.tags,
                        "latitude": place.latitude,
                        "longitude": place.longitude,
                        "created_at": place.created_at.isoformat()
                        if place.created_at
                        else None,
                    }
                    for place in places
                ],
            }

            return export_data

        elif format == "csv":
            # For CSV, return download instructions
            return {
                "message": "CSV export prepared",
                "download_url": f"/api/v1/places/download-csv?category={category}&tags={','.join(tags or [])}",
                "total_places": total,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export places: {e}")
        raise HTTPException(status_code=500, detail="Failed to export places")
