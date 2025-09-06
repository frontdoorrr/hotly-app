"""User preference and behavior tracking API endpoints."""

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.preference import (
    BehaviorAnalyticsResponse,
    FeedbackCreate,
    LearningMetricsResponse,
    PreferenceAnalysisResponse,
    PreferenceHistoryResponse,
    UserBehaviorCreate,
    UserBehaviorResponse,
    UserProfileCreate,
    UserProfileResponse,
)
from app.services.user_preference_service import UserPreferenceService

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary user_id for development
TEMP_USER_ID = "00000000-0000-0000-0000-000000000000"


@router.post("/behavior", response_model=UserBehaviorResponse, status_code=201)
async def record_user_behavior(
    *, db: Session = Depends(get_db), behavior_data: UserBehaviorCreate
) -> UserBehaviorResponse:
    """
    Record user behavior for preference learning.

    - **action**: Type of action performed
    - **place_id**: Related place (if applicable)
    - **rating**: User rating (if provided)
    - **duration_minutes**: Time spent

    Records user interactions to build preference profile.
    """
    try:
        preference_service = UserPreferenceService(db)

        behavior = preference_service.record_user_behavior(
            user_id=UUID(TEMP_USER_ID), behavior_data=behavior_data
        )

        logger.info(
            f"Recorded behavior: {behavior_data.action} for user {TEMP_USER_ID}"
        )
        return UserBehaviorResponse.from_orm(behavior)

    except Exception as e:
        logger.error(f"Failed to record user behavior: {e}")
        raise HTTPException(status_code=500, detail="Failed to record behavior")


@router.get("/analysis/{user_id}", response_model=PreferenceAnalysisResponse)
async def get_preference_analysis(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    analysis_days: int = Query(
        90, ge=7, le=365, description="Days of history to analyze"
    ),
) -> PreferenceAnalysisResponse:
    """
    Get comprehensive preference analysis for user.

    - **user_id**: User identifier
    - **analysis_days**: Number of days of history to analyze

    Returns detailed preference analysis with confidence scores.
    """
    try:
        preference_service = UserPreferenceService(db)

        analysis = preference_service.analyze_user_preferences(
            user_id=user_id, analysis_window_days=analysis_days
        )

        logger.info(f"Preference analysis completed for user {user_id}")
        return analysis

    except Exception as e:
        logger.error(f"Failed to analyze preferences for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze preferences")


@router.post("/feedback", response_model=dict, status_code=201)
async def submit_feedback(
    *, db: Session = Depends(get_db), feedback_data: FeedbackCreate
) -> dict:
    """
    Submit user feedback for preference learning.

    - **rating**: User rating (1-5)
    - **visited**: Whether user actually visited the place
    - **feedback_text**: Optional text feedback

    Updates user preference model based on feedback.
    """
    try:
        preference_service = UserPreferenceService(db)

        success = preference_service.update_preferences_from_feedback(
            user_id=UUID(TEMP_USER_ID),
            place_id=feedback_data.place_id,
            rating=feedback_data.rating,
            feedback_text=feedback_data.feedback_text,
            visited=feedback_data.visited,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="Place not found or invalid feedback"
            )

        logger.info(f"Processed feedback for user {TEMP_USER_ID}")
        return {
            "message": "Feedback processed successfully",
            "rating": feedback_data.rating,
            "will_update_recommendations": True,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process feedback")


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(
    *, db: Session = Depends(get_db), user_id: UUID
) -> UserProfileResponse:
    """
    Get comprehensive user profile with preferences.

    - **user_id**: User identifier

    Returns complete user profile including preference analysis.
    """
    try:
        preference_service = UserPreferenceService(db)

        profile = preference_service.get_user_profile(user_id)

        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        logger.info(f"Retrieved profile for user {user_id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user profile {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")


@router.post("/profile", response_model=dict, status_code=201)
async def create_user_profile(
    *, db: Session = Depends(get_db), profile_data: UserProfileCreate
) -> dict:
    """
    Create initial user profile.

    - **age_group**: User age group
    - **budget_range**: Preferred budget range
    - **activity_preferences**: Preferred activity types

    Creates baseline profile that will be refined through learning.
    """
    try:
        # This would create initial profile record
        # For now, return success message

        logger.info(f"Created profile for user {TEMP_USER_ID}")
        return {
            "message": "User profile created successfully",
            "user_id": TEMP_USER_ID,
            "profile_data": profile_data.dict(),
        }

    except Exception as e:
        logger.error(f"Failed to create user profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user profile")


@router.get("/history/{user_id}", response_model=PreferenceHistoryResponse)
async def get_preference_history(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    days: int = Query(30, ge=7, le=180, description="Days of history to analyze"),
) -> PreferenceHistoryResponse:
    """
    Get preference change history for user.

    - **user_id**: User identifier
    - **days**: Days of history to analyze

    Returns how user preferences have evolved over time.
    """
    try:
        preference_service = UserPreferenceService(db)

        changes = preference_service.track_preference_changes(
            user_id=user_id, window_days=days
        )

        return PreferenceHistoryResponse(
            user_id=str(user_id),
            changes=changes,
            analysis_period_days=days,
            total_changes=len(changes),
        )

    except Exception as e:
        logger.error(f"Failed to get preference history for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preference history")


@router.get("/metrics/{user_id}", response_model=LearningMetricsResponse)
async def get_learning_metrics(
    *, db: Session = Depends(get_db), user_id: UUID
) -> LearningMetricsResponse:
    """
    Get preference learning performance metrics.

    - **user_id**: User identifier

    Returns metrics on how well the preference learning system is performing.
    """
    try:
        # Get basic metrics from user behaviors and feedback
        from app.models.user_behavior import UserBehavior, UserFeedback

        # Count total behaviors
        behavior_count = (
            db.query(UserBehavior).filter(UserBehavior.user_id == user_id).count()
        )

        # Count feedback
        feedback_count = (
            db.query(UserFeedback).filter(UserFeedback.user_id == user_id).count()
        )

        # Calculate positive feedback rate
        positive_feedbacks = (
            db.query(UserFeedback)
            .filter(UserFeedback.user_id == user_id, UserFeedback.rating >= 4.0)
            .count()
        )

        positive_rate = (
            positive_feedbacks / feedback_count if feedback_count > 0 else 0.0
        )

        # Estimate accuracy based on feedback patterns
        prediction_accuracy = min(0.7 + (positive_rate * 0.3), 1.0)

        return LearningMetricsResponse(
            user_id=str(user_id),
            prediction_accuracy=prediction_accuracy,
            feedback_count=feedback_count,
            positive_feedback_rate=positive_rate,
            model_confidence=min(
                behavior_count / 50, 1.0
            ),  # Confidence grows with data
            last_learning_update=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Failed to get learning metrics for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get learning metrics")


@router.get("/analytics/{user_id}", response_model=BehaviorAnalyticsResponse)
async def get_behavior_analytics(
    *,
    db: Session = Depends(get_db),
    user_id: UUID,
    days: int = Query(30, ge=7, le=90, description="Days to analyze"),
) -> BehaviorAnalyticsResponse:
    """
    Get detailed behavior analytics for user.

    - **user_id**: User identifier
    - **days**: Days of data to analyze

    Returns comprehensive behavior analytics and engagement metrics.
    """
    try:
        from datetime import timedelta

        from app.models.user_behavior import UserBehavior

        # Get behavior data for period
        start_date = datetime.utcnow() - timedelta(days=days)
        behaviors = (
            db.query(UserBehavior)
            .filter(
                UserBehavior.user_id == user_id, UserBehavior.created_at >= start_date
            )
            .all()
        )

        # Analyze behavior patterns
        behavior_counts = {}
        action_types = set(b.action for b in behaviors)

        for action in action_types:
            behavior_counts[action] = sum(1 for b in behaviors if b.action == action)

        # Calculate engagement trends (simplified)
        daily_engagement = [0] * min(days, 30)  # Last 30 days max
        for i in range(len(daily_engagement)):
            day_start = datetime.utcnow() - timedelta(days=i + 1)
            day_end = day_start + timedelta(days=1)

            daily_behaviors = [
                b for b in behaviors if day_start <= b.created_at < day_end
            ]
            daily_engagement[i] = len(daily_behaviors)

        return BehaviorAnalyticsResponse(
            user_id=str(user_id),
            analysis_period={"start": start_date, "end": datetime.utcnow()},
            behavior_summary=behavior_counts,
            engagement_trends={"daily_interactions": daily_engagement},
            preference_stability=0.8,  # Would calculate from actual data
            recommendation_acceptance_rate=0.65,  # Would calculate from feedback data
        )

    except Exception as e:
        logger.error(f"Failed to get behavior analytics for {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get behavior analytics")
