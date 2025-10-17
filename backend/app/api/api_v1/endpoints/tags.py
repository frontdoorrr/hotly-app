"""Tag management API endpoints."""

import logging
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.tag import (
    TagClusterResponse,
    TagStatisticsResponse,
    TagSuggestionResponse,
)
from app.services.utils.tag_service import TagService

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development (will be replaced with auth)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000001"


@router.get("/statistics", response_model=TagStatisticsResponse)
async def get_tag_statistics(
    *,
    db: Session = Depends(get_db),
) -> TagStatisticsResponse:
    """
    Get comprehensive tag usage statistics for current user.

    Returns:
    - Total unique tags
    - Total tag usage count
    - Most used tags with counts
    - Tag categories/clusters
    - Average tags per place
    """
    try:
        tag_service = TagService(db)
        stats = tag_service.get_tag_statistics(UUID(TEMP_USER_ID))

        logger.info(f"Retrieved tag statistics for user {TEMP_USER_ID}")
        return TagStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get tag statistics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve tag statistics"
        )


@router.get("/popular", response_model=List[TagSuggestionResponse])
async def get_popular_tags(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum tags to return"),
) -> List[TagSuggestionResponse]:
    """
    Get user's most frequently used tags.

    Returns tags sorted by usage count with metadata.
    """
    try:
        tag_service = TagService(db)
        popular_tags = tag_service.get_popular_tags(UUID(TEMP_USER_ID), limit=limit)

        return [TagSuggestionResponse(**tag) for tag in popular_tags]

    except Exception as e:
        logger.error(f"Failed to get popular tags: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to retrieve popular tags"
        )


@router.get("/suggestions", response_model=List[TagSuggestionResponse])
async def get_tag_suggestions(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=1, description="Partial tag input"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum suggestions"),
) -> List[TagSuggestionResponse]:
    """
    Get tag auto-completion suggestions based on query.

    - Prefix matches have highest priority
    - Contains matches come next
    - Similar tags are suggested if not enough exact matches
    """
    try:
        tag_service = TagService(db)
        suggestions = tag_service.get_tag_suggestions(
            query=query, user_id=UUID(TEMP_USER_ID), limit=limit
        )

        return [TagSuggestionResponse(**suggestion) for suggestion in suggestions]

    except Exception as e:
        logger.error(f"Failed to get tag suggestions: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get tag suggestions"
        )


@router.get("/clusters", response_model=TagClusterResponse)
async def get_tag_clusters(
    *,
    db: Session = Depends(get_db),
) -> TagClusterResponse:
    """
    Get semantic clusters of user's tags.

    Groups related tags into categories like:
    - 음식 (food-related tags)
    - 데이트 (date-related tags)
    - 활동 (activity-related tags)
    """
    try:
        tag_service = TagService(db)
        clusters = tag_service.get_tag_clusters(UUID(TEMP_USER_ID))

        return TagClusterResponse(clusters=clusters)

    except Exception as e:
        logger.error(f"Failed to get tag clusters: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get tag clusters"
        )


@router.get("/trending", response_model=List[Dict])
async def get_trending_tags(
    *,
    db: Session = Depends(get_db),
    days: int = Query(default=7, ge=1, le=30, description="Days to look back"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum trending tags"),
) -> List[Dict]:
    """
    Get trending tags based on recent usage.

    - **days**: Number of days to analyze for trends
    - **limit**: Maximum trending tags to return

    Returns tags with growth metrics and trend scores.
    """
    try:
        tag_service = TagService(db)
        trending = tag_service.get_trending_tags(days=days, limit=limit)

        return trending

    except Exception as e:
        logger.error(f"Failed to get trending tags: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get trending tags"
        )


@router.post("/validate")
async def validate_tags(
    *,
    db: Session = Depends(get_db),
    tags: List[str],
) -> Dict:
    """
    Validate and normalize a list of tags.

    Returns:
    - Normalized tags
    - Warnings for tags that were modified
    - Rejected tags that don't meet validation criteria
    """
    try:
        tag_service = TagService(db)
        result = tag_service.validate_and_normalize_tags(tags)

        return result

    except Exception as e:
        logger.error(f"Failed to validate tags: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to validate tags"
        )


@router.post("/merge-duplicates")
async def merge_duplicate_tags(
    *,
    db: Session = Depends(get_db),
) -> Dict:
    """
    Find and merge duplicate/similar tags across user's places.

    Automatically identifies tags that are:
    - Typo variations
    - Different spellings
    - Similar meanings

    Returns summary of merge operations performed.
    """
    try:
        tag_service = TagService(db)
        result = tag_service.merge_duplicate_tags(UUID(TEMP_USER_ID))

        logger.info(
            f"Merged {result['merges_performed']} duplicate tags for user {TEMP_USER_ID}"
        )
        return result

    except Exception as e:
        logger.error(f"Failed to merge duplicate tags: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to merge duplicate tags"
        )


@router.post("/places/{place_id}/tags")
async def add_tags_to_place(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
    tags: List[str],
) -> Dict:
    """
    Add tags to a specific place.

    Tags are automatically normalized and deduplicated.
    Tag usage statistics are updated.
    """
    try:
        tag_service = TagService(db)
        added_tags = tag_service.add_tags_to_place(
            place_id=place_id, user_id=UUID(TEMP_USER_ID), tags=tags
        )

        return {
            "place_id": str(place_id),
            "added_tags": added_tags,
            "total_added": len(added_tags),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add tags to place {place_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to add tags to place"
        )


@router.delete("/places/{place_id}/tags")
async def remove_tags_from_place(
    *,
    db: Session = Depends(get_db),
    place_id: UUID,
    tags: List[str],
) -> Dict:
    """
    Remove tags from a specific place.

    Tags are normalized before removal.
    """
    try:
        tag_service = TagService(db)
        removed_tags = tag_service.remove_tags_from_place(
            place_id=place_id, user_id=UUID(TEMP_USER_ID), tags=tags
        )

        return {
            "place_id": str(place_id),
            "removed_tags": removed_tags,
            "total_removed": len(removed_tags),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove tags from place {place_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to remove tags from place"
        )


@router.get("/suggest-for-place")
async def suggest_tags_for_place(
    *,
    db: Session = Depends(get_db),
    place_name: str = Query(..., description="Name of the place"),
    place_description: str = Query(None, description="Optional description"),
    max_suggestions: int = Query(
        default=5, ge=1, le=10, description="Maximum suggestions"
    ),
) -> List[str]:
    """
    Suggest tags for a place based on its name and description.

    Uses:
    - Text extraction from place name/description
    - User's tag history for personalization
    """
    try:
        tag_service = TagService(db)
        suggestions = tag_service.suggest_tags_for_place(
            place_name=place_name,
            place_description=place_description,
            user_id=UUID(TEMP_USER_ID),
            max_suggestions=max_suggestions,
        )

        return suggestions

    except Exception as e:
        logger.error(f"Failed to suggest tags for place: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to suggest tags for place"
        )
