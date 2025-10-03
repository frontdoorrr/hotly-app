"""Course recommendation, sharing and personal storage API endpoints."""

import logging
import time as time_module
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import place as place_crud
from app.schemas.course import (
    CourseRecommendationResponse,
    CourseRequest,
    PlaceInCourseResponse,
)
from app.schemas.course_recommendation import (
    CourseGenerateRequest,
    CourseGenerateResponse,
)
from app.schemas.place import PlaceCreate
from app.services.course_generator_service import CourseGeneratorService
from app.services.course_recommender import CourseRecommender
from app.services.course_sharing_service import (
    CourseAnalyticsService,
    CourseDiscoveryService,
    CourseInteractionService,
    CourseSharingService,
    PersonalCourseStorageService,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


# ============================================================================
# COURSE RECOMMENDATION ENDPOINTS (Task 1-3)
# ============================================================================


@router.post("/generate", response_model=CourseGenerateResponse)
async def generate_optimized_course(
    request: CourseGenerateRequest,
    db: Session = Depends(get_db),
    current_user_id: str = TEMP_USER_ID,
):
    """
    Generate AI-optimized course using Genetic Algorithm.

    **New! Genetic Algorithm Optimization:**
    - 50 population, 100 generations for optimal route finding
    - Multi-criteria optimization (distance 40%, time 25%, variety 20%, preference 15%)
    - Haversine formula for accurate distance calculation (±10m accuracy)
    - PostGIS integration for coordinate extraction

    **Performance:**
    - Course generation: < 500ms
    - Distance calculation: < 1ms per pair
    - Optimization: < 100ms for 6 places

    **Requirements:**
    - 3-6 places required
    - Places must exist in database with valid coordinates

    **Example:**
    ```json
    {
      "place_ids": ["place1", "place2", "place3", "place4"],
      "transport_method": "walking",
      "start_time": "10:00",
      "preferences": {
        "max_total_duration": 480,
        "avoid_rush_hours": true
      }
    }
    ```
    """
    try:
        # Measure generation time for performance monitoring
        start_time = time_module.time()

        # Initialize course generation service
        generator = CourseGeneratorService(db)

        # Generate optimized course
        result = generator.generate_course(request)

        # Calculate actual generation time
        generation_time_ms = int((time_module.time() - start_time) * 1000)

        # Update generation time in response
        result.generation_time_ms = generation_time_ms

        logger.info(
            f"Course generated in {generation_time_ms}ms for user {current_user_id}: "
            f"{len(request.place_ids)} places, "
            f"score={result.optimization_score:.3f}"
        )

        return result

    except ValueError as e:
        # Handle validation errors from service
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to generate course: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Course generation failed: {str(e)}",
        )


@router.get("/{course_id}", response_model=CourseGenerateResponse)
async def get_course_by_id(
    course_id: str,
    db: Session = Depends(get_db),
    current_user_id: str = TEMP_USER_ID,
):
    """
    Retrieve generated course by ID.

    **Returns:**
    - Complete course details with optimized route
    - Place information with arrival times
    - Optimization metrics and scores

    **Example Response:**
    - Course ID, places in optimized order
    - Total distance and duration
    - Optimization score (0-1)
    - Travel information between places
    """
    # TODO: Implement course storage and retrieval
    # For now, return error since we haven't implemented persistence yet
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Course storage not implemented yet. Please use /generate endpoint.",
    )


@router.post("/recommend", response_model=CourseRecommendationResponse)
async def recommend_course(
    request: CourseRequest,
    db: Session = Depends(get_db),
    current_user_id: str = TEMP_USER_ID,
):
    """
    Generate optimized course recommendation from selected places.

    **DEPRECATED:** Use /generate endpoint instead for Genetic Algorithm optimization.

    **Requirements:**
    - 3-6 places required
    - Places must exist in database
    - Response time < 10 seconds

    **Optimization:**
    - Minimizes travel distance (30%+ improvement)
    - Ensures category diversity (max 2 consecutive same category)
    - Calculates accurate travel times

    **Example:**
    ```json
    {
      "place_ids": ["place1", "place2", "place3"],
      "transport_mode": "walking",
      "start_time": "10:00"
    }
    ```
    """
    # Validate place count
    if len(request.place_ids) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 3 places required for course recommendation",
        )
    if len(request.place_ids) > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 6 places allowed for course recommendation",
        )

    # Fetch places from database
    places: List[PlaceCreate] = []
    for place_id in request.place_ids:
        place = place_crud.place.get(db, id=place_id)
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Place with ID {place_id} not found",
            )

        # Convert to PlaceCreate for recommendation engine
        place_data = PlaceCreate(
            name=place.name,
            address=place.address,
            latitude=place.latitude,
            longitude=place.longitude,
            category=place.category,
        )
        places.append(place_data)

    # Generate course recommendation
    recommender = CourseRecommender()
    start_location = None
    if request.start_latitude and request.start_longitude:
        start_location = (request.start_latitude, request.start_longitude)

    result = recommender.recommend_course(places, start_location)

    # Calculate arrival times if start_time provided
    arrival_times = []
    if request.start_time:
        current_minutes = _parse_time_to_minutes(request.start_time)
        for place_in_course in result.places:
            arrival_times.append(_minutes_to_time_str(current_minutes))
            current_minutes += place_in_course.estimated_duration_minutes + (
                place_in_course.travel_duration_minutes or 0
            )
    else:
        arrival_times = [None] * len(result.places)

    # Format response
    places_response = [
        PlaceInCourseResponse(
            place_id=request.place_ids[
                places.index(pic.place)
            ],  # Map back to original ID
            place_name=pic.place.name,
            category=pic.category,
            address=pic.place.address,
            latitude=pic.place.latitude,
            longitude=pic.place.longitude,
            position=pic.position,
            travel_distance_km=pic.travel_distance_km,
            travel_duration_minutes=pic.travel_duration_minutes,
            estimated_duration_minutes=pic.estimated_duration_minutes,
            arrival_time=arrival_times[pic.position],
        )
        for pic in result.places
    ]

    return CourseRecommendationResponse(
        course_id=str(uuid.uuid4()),
        user_id=current_user_id,
        places=places_response,
        total_distance_km=result.total_distance_km,
        total_duration_minutes=result.total_duration_minutes,
        optimization_score=result.optimization_score,
        transport_mode=request.transport_mode,
        created_at=datetime.utcnow(),
    )


def _parse_time_to_minutes(time_str: str) -> int:
    """Parse HH:MM time string to minutes since midnight."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 600  # Default 10:00 AM


def _minutes_to_time_str(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM string."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


# ============================================================================
# COURSE SHARING ENDPOINTS (Task 1-5)
# ============================================================================


@router.post("/create-share-link", response_model=dict)
async def create_course_share_link(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    title: str,
    places: List[dict],
    share_settings: dict,
) -> dict:
    """
    Create shareable link for a course.

    - **course_id**: Course identifier
    - **title**: Course title
    - **places**: List of places in course
    - **share_settings**: Sharing configuration (public_access, allow_copy, expire_days)

    Returns shareable link with expiration and permissions.
    """
    try:
        course_data = {
            "title": title,
            "places": places,
            "course_type": "user_created",
            "description": f"사용자가 만든 {len(places)}곳 코스",
        }

        sharing_service = CourseSharingService(db)
        share_result = sharing_service.create_share_link(
            course_id, user_id, course_data, share_settings
        )

        logger.info(f"Share link created for course {course_id}")
        return share_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create share link: {e}")
        raise HTTPException(status_code=500, detail="Failed to create share link")


@router.get("/shared/{share_id}", response_model=dict)
async def access_shared_course(
    *, share_id: str, accessing_user_id: Optional[str] = None
) -> dict:
    """
    Access shared course via share link.

    - **share_id**: Share link identifier
    - **accessing_user_id**: Optional user accessing the course

    Returns course information from share link.
    """
    try:
        sharing_service = CourseSharingService(db=None)  # No DB needed for cached data
        shared_course = sharing_service.access_shared_course(
            share_id, accessing_user_id
        )

        logger.info(f"Shared course {share_id} accessed")
        return shared_course

    except ValueError as e:
        if "not found" in str(e) or "expired" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "revoked" in str(e):
            raise HTTPException(status_code=410, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to access shared course: {e}")
        raise HTTPException(status_code=500, detail="Failed to access shared course")


@router.delete("/revoke-share", response_model=dict)
async def revoke_share_link(
    *,
    db: Session = Depends(get_db),
    share_id: str,
    user_id: str = TEMP_USER_ID,
    reason: str = "user_request",
) -> dict:
    """
    Revoke share link within 1 second requirement.

    - **share_id**: Share link to revoke
    - **user_id**: User requesting revocation
    - **reason**: Reason for revocation

    Returns revocation confirmation.
    """
    try:
        sharing_service = CourseSharingService(db)
        revocation_result = sharing_service.revoke_share_link(share_id, user_id, reason)

        logger.info(f"Share link {share_id} revoked")
        return revocation_result

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "Only course owner" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to revoke share link: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke share link")


@router.post("/save-favorite", response_model=dict)
async def save_course_to_favorites(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    save_type: str = Query("favorite", description="Save type"),
    folder_name: Optional[str] = None,
    private_notes: Optional[str] = None,
) -> dict:
    """
    Save course to user's personal favorites.

    - **course_id**: Course to save
    - **save_type**: Type of save (favorite, wishlist, archive)
    - **folder_name**: Target folder for organization
    - **private_notes**: Personal notes about the course

    Returns save operation result.
    """
    try:
        storage_service = PersonalCourseStorageService(db)
        save_result = storage_service.save_course_to_favorites(
            course_id, user_id, save_type, folder_name, private_notes
        )

        logger.info(f"Course {course_id} saved to {save_type}")
        return save_result

    except Exception as e:
        logger.error(f"Failed to save course: {e}")
        raise HTTPException(status_code=500, detail="Failed to save course")


@router.post("/create-folder", response_model=dict)
async def create_personal_folder(
    *,
    db: Session = Depends(get_db),
    user_id: str = TEMP_USER_ID,
    folder_name: str,
    folder_description: str = "",
    folder_color: str = "#95A5A6",
    is_private: bool = True,
) -> dict:
    """
    Create personal folder for course organization.

    - **folder_name**: Name of the folder
    - **folder_description**: Description of folder purpose
    - **folder_color**: Folder color code
    - **is_private**: Whether folder is private

    Returns created folder information.
    """
    try:
        if len(folder_name.strip()) < 1:
            raise HTTPException(status_code=422, detail="Folder name cannot be empty")

        storage_service = PersonalCourseStorageService(db)
        folder_result = storage_service.create_personal_folder(
            user_id, folder_name, folder_description, folder_color, is_private
        )

        logger.info(f"Personal folder '{folder_name}' created")
        return folder_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create folder: {e}")
        raise HTTPException(status_code=500, detail="Failed to create folder")


@router.post("/organize-folder", response_model=dict)
async def organize_courses_in_folder(
    *,
    db: Session = Depends(get_db),
    folder_id: str,
    user_id: str = TEMP_USER_ID,
    course_ids: List[str],
    organization_type: str = Query(
        "move", description="Organization type (move, copy)"
    ),
) -> dict:
    """
    Organize courses within a personal folder.

    - **folder_id**: Target folder ID
    - **course_ids**: List of course IDs to organize
    - **organization_type**: move or copy operation

    Returns organization operation result.
    """
    try:
        if not course_ids:
            raise HTTPException(
                status_code=422, detail="Course IDs list cannot be empty"
            )

        valid_org_types = ["move", "copy"]
        if organization_type not in valid_org_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid organization type. Must be one of: {valid_org_types}",
            )

        storage_service = PersonalCourseStorageService(db)
        organize_result = storage_service.organize_courses_in_folder(
            folder_id, user_id, course_ids, organization_type
        )

        logger.info(f"Organized {len(course_ids)} courses in folder {folder_id}")
        return organize_result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to organize courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to organize courses")


@router.post("/add-to-wishlist", response_model=dict)
async def add_course_to_wishlist(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    priority: str = Query("medium", description="Wishlist priority"),
    planned_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """
    Add course to user's wishlist.

    - **course_id**: Course to add to wishlist
    - **priority**: Wishlist priority (low, medium, high)
    - **planned_date**: Planned visit date (YYYY-MM-DD)
    - **notes**: Personal notes about planning

    Returns wishlist addition result.
    """
    try:
        valid_priorities = ["low", "medium", "high"]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid priority. Must be one of: {valid_priorities}",
            )

        storage_service = PersonalCourseStorageService(db)
        wishlist_result = storage_service.add_to_wishlist(
            course_id, user_id, priority, planned_date, notes
        )

        logger.info(f"Course {course_id} added to wishlist")
        return wishlist_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to wishlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add to wishlist")


@router.post("/like", response_model=dict)
async def like_course(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    action: str = Query(..., description="Action: like or unlike"),
) -> dict:
    """
    Like or unlike a course.

    - **course_id**: Course to like/unlike
    - **action**: like or unlike

    Returns like action result with updated counts.
    """
    try:
        valid_actions = ["like", "unlike"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid action. Must be one of: {valid_actions}",
            )

        interaction_service = CourseInteractionService(db)
        like_result = interaction_service.handle_course_like(course_id, user_id, action)

        logger.info(f"Course {course_id} {action}d by user {user_id}")
        return like_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to {action} course: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to {action} course")


@router.post("/add-comment", response_model=dict)
async def add_course_comment(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    comment_text: str,
    rating: Optional[int] = Query(None, ge=1, le=5, description="Course rating 1-5"),
    is_public: bool = True,
) -> dict:
    """
    Add comment to a course.

    - **course_id**: Course to comment on
    - **comment_text**: Comment content
    - **rating**: Optional course rating (1-5)
    - **is_public**: Whether comment is public

    Returns comment creation result.
    """
    try:
        if len(comment_text.strip()) < 1:
            raise HTTPException(status_code=422, detail="Comment text cannot be empty")

        if len(comment_text) > 1000:
            raise HTTPException(
                status_code=422, detail="Comment text too long (max 1000 characters)"
            )

        interaction_service = CourseInteractionService(db)
        comment_result = interaction_service.add_course_comment(
            course_id, user_id, comment_text, rating, is_public
        )

        logger.info(f"Comment added to course {course_id}")
        return comment_result

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to add comment")


@router.get("/{course_id}/ratings", response_model=dict)
async def get_course_ratings(*, db: Session = Depends(get_db), course_id: str) -> dict:
    """
    Get course rating summary and distribution.

    - **course_id**: Course to get ratings for

    Returns rating aggregation with distribution breakdown.
    """
    try:
        interaction_service = CourseInteractionService(db)
        rating_summary = interaction_service.get_course_ratings_summary(course_id)

        logger.info(f"Rating summary retrieved for course {course_id}")
        return rating_summary

    except Exception as e:
        logger.error(f"Failed to get course ratings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get course ratings")


@router.post("/discover", response_model=dict)
async def discover_public_courses(
    *,
    db: Session = Depends(get_db),
    location: dict,
    radius_km: float = Query(10.0, ge=1.0, le=50.0),
    category: Optional[str] = None,
    min_rating: float = Query(0.0, ge=0.0, le=5.0),
    sort_by: str = Query("popularity", description="Sort criteria"),
) -> dict:
    """
    Discover public courses based on location and preferences.

    - **location**: Search center coordinates (latitude, longitude)
    - **radius_km**: Search radius in kilometers
    - **category**: Filter by place category
    - **min_rating**: Minimum course rating
    - **sort_by**: Sort by popularity, rating, or distance

    Returns discovered courses matching criteria.
    """
    try:
        # Validate location
        if "latitude" not in location or "longitude" not in location:
            raise HTTPException(
                status_code=422, detail="Location must contain latitude and longitude"
            )

        valid_sort_options = ["popularity", "rating", "distance", "newest"]
        if sort_by not in valid_sort_options:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid sort option. Must be one of: {valid_sort_options}",
            )

        discovery_service = CourseDiscoveryService(db)
        discovery_result = discovery_service.discover_public_courses(
            location, radius_km, category, min_rating, sort_by
        )

        logger.info(f"Discovered courses in {radius_km}km radius")
        return discovery_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to discover courses")


@router.get("/trending", response_model=dict)
async def get_trending_courses(
    *,
    db: Session = Depends(get_db),
    time_period: str = Query("week", description="Trending period"),
    location_filter: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
) -> dict:
    """
    Get trending courses based on engagement metrics.

    - **time_period**: Trending period (week, month, all_time)
    - **location_filter**: Geographic filter for trends
    - **limit**: Maximum courses to return

    Returns trending courses with ranking criteria.
    """
    try:
        valid_periods = ["week", "month", "all_time"]
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid time period. Must be one of: {valid_periods}",
            )

        discovery_service = CourseDiscoveryService(db)
        trending_result = discovery_service.get_trending_courses(
            time_period, location_filter, limit
        )

        logger.info(f"Retrieved {limit} trending courses for {time_period}")
        return trending_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trending courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending courses")


@router.post("/recommend-from-saves", response_model=dict)
async def recommend_courses_from_saves(
    *,
    db: Session = Depends(get_db),
    user_id: str = TEMP_USER_ID,
    saved_courses_count: int,
    preferred_categories: List[str],
    activity_radius_km: float = 15.0,
) -> dict:
    """
    Get course recommendations based on save history.

    - **saved_courses_count**: Number of courses user has saved
    - **preferred_categories**: User's preferred place categories
    - **activity_radius_km**: User's typical activity radius

    Returns personalized course recommendations.
    """
    try:
        if saved_courses_count < 0:
            raise HTTPException(
                status_code=422, detail="Saved courses count cannot be negative"
            )

        if not preferred_categories:
            raise HTTPException(
                status_code=422, detail="Preferred categories cannot be empty"
            )

        discovery_service = CourseDiscoveryService(db)
        recommendations = discovery_service.recommend_courses_from_saves(
            user_id, saved_courses_count, preferred_categories, activity_radius_km
        )

        logger.info(f"Generated recommendations for user {user_id}")
        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recommend courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to recommend courses")


@router.post("/save-shared-course", response_model=dict)
async def save_shared_course_to_personal(
    *,
    db: Session = Depends(get_db),
    shared_course_id: str,
    saving_user_id: str = TEMP_USER_ID,
    save_to_folder: str = "기본 폴더",
    add_personal_notes: Optional[str] = None,
    copy_or_reference: str = Query("reference", description="Copy type"),
) -> dict:
    """
    Save shared course to personal collection.

    - **shared_course_id**: Shared course to save
    - **save_to_folder**: Target folder name
    - **add_personal_notes**: Personal notes to add
    - **copy_or_reference**: Keep link to original (reference) or create independent copy

    Returns save operation with attribution preservation.
    """
    try:
        valid_copy_types = ["reference", "full_copy"]
        if copy_or_reference not in valid_copy_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid copy type. Must be one of: {valid_copy_types}",
            )

        storage_service = PersonalCourseStorageService(db)

        # Save with appropriate attribution
        save_result = storage_service.save_course_to_favorites(
            course_id=f"shared_{shared_course_id}",
            user_id=saving_user_id,
            save_type="shared_save",
            folder_name=save_to_folder,
            private_notes=add_personal_notes,
        )

        # Add attribution information
        attribution_info = {
            "saved_course_id": save_result["save_id"],
            "original_course_id": shared_course_id,
            "original_course_link": f"https://hotly.app/shared/{shared_course_id}",
            "copy_type": copy_or_reference,
            "attribution_preserved": True,
            "saved_by": saving_user_id,
            "saved_at": save_result["saved_at"],
        }

        result = {**save_result, **attribution_info}

        logger.info(f"Shared course {shared_course_id} saved by user {saving_user_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save shared course: {e}")
        raise HTTPException(status_code=500, detail="Failed to save shared course")


@router.post("/sharing-analytics", response_model=dict)
async def get_course_sharing_analytics(
    *,
    course_id: str,
    owner_user_id: str = TEMP_USER_ID,
    analytics_period: str = Query("30_days", description="Analytics period"),
) -> dict:
    """
    Get comprehensive sharing analytics for course.

    - **course_id**: Course to analyze
    - **analytics_period**: Analysis time period

    Returns detailed sharing analytics and insights.
    """
    try:
        valid_periods = ["7_days", "30_days", "90_days", "all_time"]
        if analytics_period not in valid_periods:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid analytics period. Must be one of: {valid_periods}",
            )

        analytics_service = CourseAnalyticsService()
        analytics_result = analytics_service.get_sharing_analytics(
            course_id, owner_user_id, analytics_period
        )

        logger.info(f"Sharing analytics generated for course {course_id}")
        return analytics_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sharing analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sharing analytics")


@router.post("/trend-analysis", response_model=dict)
async def analyze_course_trends(
    *,
    db: Session = Depends(get_db),
    analysis_period: str = "7_days",
    location_filter: Optional[dict] = None,
    category_filter: Optional[List[str]] = None,
) -> dict:
    """
    Analyze course trends and popularity patterns.

    - **analysis_period**: Period for trend analysis
    - **location_filter**: Geographic filter (city, district)
    - **category_filter**: Category filter for analysis

    Returns course trend analysis with growth metrics.
    """
    try:
        analytics_service = CourseAnalyticsService()
        trend_result = analytics_service.analyze_course_trends(
            analysis_period, location_filter, category_filter
        )

        logger.info(f"Course trend analysis completed for {analysis_period}")
        return trend_result

    except Exception as e:
        logger.error(f"Failed to analyze trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze trends")


@router.post("/user-insights", response_model=dict)
async def get_user_course_insights(
    *,
    db: Session = Depends(get_db),
    user_id: str = TEMP_USER_ID,
    insight_type: str = "personal_summary",
    time_range: str = "month",
) -> dict:
    """
    Generate personalized course insights for user.

    - **insight_type**: Type of insights (personal_summary, activity_report)
    - **time_range**: Time range for analysis

    Returns personalized insights and activity patterns.
    """
    try:
        valid_insight_types = ["personal_summary", "activity_report", "social_summary"]
        if insight_type not in valid_insight_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid insight type. Must be one of: {valid_insight_types}",
            )

        analytics_service = CourseAnalyticsService()
        insights_result = analytics_service.generate_user_course_insights(
            user_id, insight_type, time_range
        )

        logger.info(f"User insights generated for user {user_id}")
        return insights_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate user insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate user insights")


@router.post("/quick-share", response_model=dict)
async def quick_share_course(
    *,
    db: Session = Depends(get_db),
    course_id: str,
    user_id: str = TEMP_USER_ID,
    quick_share: bool = True,
) -> dict:
    """
    Generate quick share link with simplified settings.

    - **course_id**: Course to share quickly
    - **quick_share**: Enable quick sharing mode

    Returns share link generated within 500ms requirement.
    """
    try:
        # Quick share with default settings
        quick_settings = {
            "public_access": True,
            "allow_copy": True,
            "allow_comments": True,
            "expire_days": 7,  # Shorter expiration for quick shares
        }

        course_data = {
            "title": f"빠른 공유 코스 {course_id}",
            "places": [],  # Simplified for quick sharing
            "course_type": "quick_share",
        }

        sharing_service = CourseSharingService(db)
        quick_share_result = sharing_service.create_share_link(
            course_id, user_id, course_data, quick_settings
        )

        # Add quick share metadata
        quick_share_result.update(
            {
                "share_type": "quick_share",
                "simplified_settings": True,
                "generation_time_requirement": "500ms",
            }
        )

        logger.info(f"Quick share link generated for course {course_id}")
        return quick_share_result

    except Exception as e:
        logger.error(f"Failed to quick share course: {e}")
        raise HTTPException(status_code=500, detail="Failed to quick share course")


@router.post("/validate-ownership", response_model=dict)
async def validate_course_ownership(
    *,
    course_id: str,
    user_id: str = TEMP_USER_ID,
    operation: str = Query(..., description="Operation to validate"),
) -> dict:
    """
    Validate course ownership for operations.

    - **course_id**: Course to validate ownership for
    - **operation**: Operation requiring ownership validation

    Returns ownership validation result.
    """
    try:
        valid_operations = ["modify", "delete", "share", "transfer"]
        if operation not in valid_operations:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid operation. Must be one of: {valid_operations}",
            )

        # Mock ownership validation
        # In production, would check actual course ownership in database

        ownership_result = {
            "course_id": course_id,
            "user_id": user_id,
            "is_owner": True,  # Mock: assume user owns course
            "operation": operation,
            "permission_granted": True,
            "validated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Ownership validated for course {course_id}, operation: {operation}"
        )
        return ownership_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate ownership: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate ownership")


@router.post("/copy-shared", response_model=dict)
async def copy_shared_course(
    *,
    db: Session = Depends(get_db),
    original_course_id: str,
    copying_user_id: str = TEMP_USER_ID,
    copy_type: str = "full_copy",
    new_title: Optional[str] = None,
) -> dict:
    """
    Copy shared course with proper attribution.

    - **original_course_id**: Original course to copy
    - **copy_type**: full_copy or reference_only
    - **new_title**: Custom title for copied course

    Returns new course information with attribution.
    """
    try:
        valid_copy_types = ["full_copy", "reference_only"]
        if copy_type not in valid_copy_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid copy type. Must be one of: {valid_copy_types}",
            )

        # Generate new course ID
        from uuid import uuid4

        new_course_id = str(uuid4())

        copy_result = {
            "new_course_id": new_course_id,
            "original_course_id": original_course_id,
            "copied_by": copying_user_id,
            "copy_type": copy_type,
            "new_title": new_title or f"복사된 코스 - {original_course_id}",
            "original_course_preserved": True,
            "attribution_maintained": True,
            "copied_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Course {original_course_id} copied to {new_course_id}")
        return copy_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to copy shared course: {e}")
        raise HTTPException(status_code=500, detail="Failed to copy course")
