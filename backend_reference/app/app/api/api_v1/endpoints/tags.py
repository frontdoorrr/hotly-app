"""Tag management API endpoints."""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.tag import (
    TagMergeResult,
    TagOperationResponse,
    TagStatistics,
    TagSuggestion,
    TrendingTag,
)
from app.services.tag_service import TagService

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development (will be replaced with auth)
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.get("/suggestions", response_model=List[TagSuggestion])
async def get_tag_suggestions(
    *,
    db: Session = Depends(get_db),
    q: str = Query(
        ..., min_length=1, max_length=20, description="Tag query for autocomplete"
    ),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
) -> List[TagSuggestion]:
    """
    Get tag auto-completion suggestions.

    - **q**: Partial tag input (minimum 1 character)
    - **limit**: Maximum number of suggestions (1-50)

    Returns suggestions with usage statistics and match type.
    """
    try:
        tag_service = TagService(db)
        suggestions = tag_service.get_tag_suggestions(
            query=q, user_id=UUID(TEMP_USER_ID), limit=limit
        )

        logger.info(f"Tag suggestions for '{q}': {len(suggestions)} results")
        return suggestions

    except Exception as e:
        logger.error(f"Failed to get tag suggestions for '{q}': {e}")
        raise HTTPException(status_code=500, detail="Failed to get tag suggestions")


@router.get("/popular", response_model=List[TagSuggestion])
async def get_popular_tags(
    *,
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Maximum popular tags"),
) -> List[TagSuggestion]:
    """
    Get most popular tags for current user.

    - **limit**: Maximum number of tags to return

    Returns tags ordered by usage frequency.
    """
    try:
        tag_service = TagService(db)
        popular_tags = tag_service.get_popular_tags(
            user_id=UUID(TEMP_USER_ID), limit=limit
        )

        logger.info(f"Popular tags retrieved: {len(popular_tags)} tags")
        return popular_tags

    except Exception as e:
        logger.error(f"Failed to get popular tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get popular tags")


@router.get("/trending", response_model=List[TrendingTag])
async def get_trending_tags(
    *,
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=30, description="Days to analyze for trends"),
    limit: int = Query(10, ge=1, le=20, description="Maximum trending tags"),
) -> List[TrendingTag]:
    """
    Get trending tags based on recent usage patterns.

    - **days**: Number of days to analyze (1-30)
    - **limit**: Maximum trending tags to return

    Returns tags with growth metrics and trend scores.
    """
    try:
        tag_service = TagService(db)
        trending_tags = tag_service.get_trending_tags(days=days, limit=limit)

        logger.info(f"Trending tags for last {days} days: {len(trending_tags)} tags")
        return trending_tags

    except Exception as e:
        logger.error(f"Failed to get trending tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending tags")


@router.get("/statistics", response_model=TagStatistics)
async def get_tag_statistics(
    *,
    db: Session = Depends(get_db),
) -> TagStatistics:
    """
    Get comprehensive tag usage statistics for current user.

    Returns statistics including total tags, usage patterns, and categorization.
    """
    try:
        tag_service = TagService(db)
        statistics = tag_service.get_tag_statistics(user_id=UUID(TEMP_USER_ID))

        logger.info("Tag statistics retrieved successfully")
        return statistics

    except Exception as e:
        logger.error(f"Failed to get tag statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tag statistics")


@router.get("/clusters", response_model=Dict[str, List[str]])
async def get_tag_clusters(
    *,
    db: Session = Depends(get_db),
) -> Dict[str, List[str]]:
    """
    Get semantic clusters of user's tags.

    Groups tags into meaningful categories like '장소타입', '분위기', etc.
    """
    try:
        tag_service = TagService(db)
        clusters = tag_service.get_tag_clusters(user_id=UUID(TEMP_USER_ID))

        logger.info(f"Tag clusters retrieved: {len(clusters)} categories")
        return clusters

    except Exception as e:
        logger.error(f"Failed to get tag clusters: {e}")
        raise HTTPException(status_code=500, detail="Failed to get tag clusters")


@router.post("/{place_id}/tags", response_model=TagOperationResponse)
async def add_tags_to_place(
    *, db: Session = Depends(get_db), place_id: UUID, tags: List[str]
) -> TagOperationResponse:
    """
    Add tags to a specific place.

    - **place_id**: Place UUID
    - **tags**: List of tags to add

    Returns validation results and successfully added tags.
    """
    try:
        tag_service = TagService(db)

        # Validate and normalize tags first
        validation_result = tag_service.validate_and_normalize_tags(tags)

        if not validation_result["normalized_tags"]:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "No valid tags provided",
                    "warnings": validation_result["warnings"],
                    "rejected_tags": validation_result["rejected_tags"],
                },
            )

        # Add normalized tags to place
        added_tags = tag_service.add_tags_to_place(
            place_id=place_id,
            user_id=UUID(TEMP_USER_ID),
            tags=validation_result["normalized_tags"],
        )

        response = {
            "added_tags": added_tags,
            "total_added": len(added_tags),
            "warnings": validation_result["warnings"],
            "rejected_tags": validation_result["rejected_tags"],
        }

        logger.info(f"Added {len(added_tags)} tags to place {place_id}")
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add tags to place {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to add tags to place")


@router.delete("/{place_id}/tags", response_model=TagOperationResponse)
async def remove_tags_from_place(
    *, db: Session = Depends(get_db), place_id: UUID, tags: List[str]
) -> TagOperationResponse:
    """
    Remove tags from a specific place.

    - **place_id**: Place UUID
    - **tags**: List of tags to remove

    Returns list of successfully removed tags.
    """
    try:
        tag_service = TagService(db)

        removed_tags = tag_service.remove_tags_from_place(
            place_id=place_id, user_id=UUID(TEMP_USER_ID), tags=tags
        )

        response = {"removed_tags": removed_tags, "total_removed": len(removed_tags)}

        logger.info(f"Removed {len(removed_tags)} tags from place {place_id}")
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to remove tags from place {place_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove tags from place")


@router.post("/suggest-for-place", response_model=List[str])
async def suggest_tags_for_place(
    *,
    db: Session = Depends(get_db),
    place_name: str,
    place_description: Optional[str] = None,
    max_suggestions: int = Query(5, ge=1, le=10, description="Maximum suggestions"),
) -> List[str]:
    """
    Suggest tags for a place based on name and description.

    - **place_name**: Name of the place
    - **place_description**: Optional description
    - **max_suggestions**: Maximum number of suggestions

    Returns list of suggested tags based on content analysis and user history.
    """
    try:
        tag_service = TagService(db)

        suggestions = tag_service.suggest_tags_for_place(
            place_name=place_name,
            place_description=place_description,
            user_id=UUID(TEMP_USER_ID),
            max_suggestions=max_suggestions,
        )

        logger.info(f"Tag suggestions for '{place_name}': {len(suggestions)} tags")
        return suggestions

    except Exception as e:
        logger.error(f"Failed to suggest tags for place '{place_name}': {e}")
        raise HTTPException(status_code=500, detail="Failed to suggest tags for place")


@router.post("/merge-duplicates", response_model=TagMergeResult)
async def merge_duplicate_tags(
    *,
    db: Session = Depends(get_db),
) -> TagMergeResult:
    """
    Find and merge duplicate/similar tags across user's places.

    Automatically merges similar tags to maintain consistency.
    Returns summary of merge operations performed.
    """
    try:
        tag_service = TagService(db)

        merge_result = tag_service.merge_duplicate_tags(user_id=UUID(TEMP_USER_ID))

        logger.info(f"Tag merge completed: {merge_result['merges_performed']} merges")
        return merge_result

    except Exception as e:
        logger.error(f"Failed to merge duplicate tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to merge duplicate tags")
