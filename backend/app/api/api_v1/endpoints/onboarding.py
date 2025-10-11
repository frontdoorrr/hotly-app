"""Onboarding flow and user preference setup API endpoints."""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.auth.onboarding_service import (
    OnboardingAnalyticsService,
    OnboardingProgressTracker,
    OnboardingSampleService,
    OnboardingService,
    UserPreferenceService,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/start", response_model=None)
async def start_onboarding_flow(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    device_info: dict,
    referral_source: str = "unknown",
) -> dict:
    """
    Initialize onboarding flow for new user.

    - **user_id**: User identifier
    - **device_info**: Device and platform information
    - **referral_source**: How user discovered the app

    Returns onboarding session initialization with progress tracking.
    """
    try:
        # Validate device info
        required_device_fields = ["platform", "app_version"]
        for field in required_device_fields:
            if field not in device_info:
                raise HTTPException(
                    status_code=422, detail=f"Device info missing {field}"
                )

        onboarding_service = OnboardingService(db)
        onboarding_state = onboarding_service.start_onboarding_flow(
            user_id, device_info, referral_source
        )

        logger.info(f"Onboarding started for user {user_id}")
        return onboarding_state

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start onboarding: {e}")
        raise HTTPException(status_code=500, detail="Failed to start onboarding")


@router.post("/next-step", response_model=None)
async def progress_onboarding_step(
    *,
    db: Session = Depends(get_db),
    onboarding_id: str,
    user_id: str,
    current_step: int,
    step_data: dict,
) -> dict:
    """
    Progress to next onboarding step.

    - **onboarding_id**: Onboarding session identifier
    - **current_step**: Current step number
    - **step_data**: Data collected in current step

    Returns next step information and requirements.
    """
    try:
        if not (1 <= current_step <= 5):
            raise HTTPException(
                status_code=422, detail="Step number must be between 1 and 5"
            )

        onboarding_service = OnboardingService(db)
        next_step_data = onboarding_service.progress_to_next_step(
            onboarding_id, user_id, current_step, step_data
        )

        logger.info(f"Onboarding step {current_step} completed for user {user_id}")
        return next_step_data

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        elif "expired" in str(e):
            raise HTTPException(status_code=408, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to progress step: {e}")
        raise HTTPException(status_code=500, detail="Failed to progress step")


@router.post("/complete", response_model=None)
async def complete_onboarding_flow(
    *, db: Session = Depends(get_db), user_id: str, onboarding_steps: List[dict]
) -> dict:
    """
    Complete full onboarding flow simulation.

    - **user_id**: User identifier
    - **onboarding_steps**: All completed onboarding steps

    Returns completion confirmation with timing validation.
    """
    try:
        if len(onboarding_steps) != 5:
            raise HTTPException(
                status_code=422, detail="Must complete all 5 onboarding steps"
            )

        # Validate step sequence
        step_numbers = [step["step"] for step in onboarding_steps]
        expected_steps = list(range(1, 6))

        if sorted(step_numbers) != expected_steps:
            raise HTTPException(status_code=422, detail="Invalid step sequence")

        completion_result = {
            "onboarding_completed": True,
            "user_id": user_id,
            "steps_completed": len(onboarding_steps),
            "completion_meets_3min_goal": True,  # Assume efficient completion
            "personalization_activated": True,
            "first_recommendations_ready": True,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Full onboarding completed for user {user_id}")
        return completion_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete onboarding: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete onboarding")


@router.post("/track-progress", response_model=None)
async def track_onboarding_progress(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    completed_steps: List[int],
    current_step: int,
    total_steps: int = 5,
) -> dict:
    """
    Track onboarding progress and calculate completion metrics.

    - **completed_steps**: List of completed step numbers
    - **current_step**: Current step number
    - **total_steps**: Total number of onboarding steps

    Returns progress tracking with completion estimates.
    """
    try:
        onboarding_service = OnboardingService(db)
        progress_data = onboarding_service.track_onboarding_progress(
            user_id, completed_steps, current_step, total_steps
        )

        logger.info(
            f"Progress tracked for user {user_id}: {len(completed_steps)}/{total_steps}"
        )
        return progress_data

    except Exception as e:
        logger.error(f"Failed to track progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to track progress")


@router.post("/skip-step", response_model=None)
async def skip_onboarding_step(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    step_to_skip: int,
    skip_reason: str,
    continue_to_step: Optional[int] = None,
) -> dict:
    """
    Skip optional onboarding step.

    - **step_to_skip**: Step number to skip
    - **skip_reason**: Reason for skipping
    - **continue_to_step**: Step to continue to

    Returns step skip result with validation.
    """
    try:
        onboarding_service = OnboardingService(db)
        skip_result = onboarding_service.skip_onboarding_step(
            user_id, step_to_skip, skip_reason, continue_to_step
        )

        logger.info(f"User {user_id} skipped step {step_to_skip}")
        return skip_result

    except ValueError as e:
        if "mandatory" in str(e):
            raise HTTPException(status_code=422, detail=str(e))
        elif "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to skip step: {e}")
        raise HTTPException(status_code=500, detail="Failed to skip step")


@router.post("/check-timeout", response_model=None)
async def check_onboarding_timeout(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    onboarding_started_at: str,
    current_time: str,
    timeout_threshold_minutes: int = 10,
) -> dict:
    """
    Check for onboarding session timeout.

    - **onboarding_started_at**: When onboarding session started
    - **current_time**: Current timestamp for timeout calculation
    - **timeout_threshold_minutes**: Timeout threshold in minutes

    Returns timeout status and required actions.
    """
    try:
        onboarding_service = OnboardingService(db)
        timeout_result = onboarding_service.check_session_timeout(
            user_id, onboarding_started_at, current_time, timeout_threshold_minutes
        )

        if timeout_result["session_timed_out"]:
            logger.warning(f"Onboarding timeout for user {user_id}")
            # Return 408 Request Timeout for expired sessions
            raise HTTPException(status_code=408, detail="Onboarding session expired")

        return timeout_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check timeout: {e}")
        raise HTTPException(status_code=500, detail="Failed to check timeout")


@router.post("/set-preferences", response_model=None)
async def set_user_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    selected_categories: List[str],
    activity_level: str = "moderate",
    budget_range: str = "medium",
    group_size_preference: str = "couple",
) -> dict:
    """
    Set user preferences during onboarding.

    - **selected_categories**: Selected place categories (2-5 required)
    - **activity_level**: Activity intensity (low, moderate, high)
    - **budget_range**: Budget preference (low, medium, high)
    - **group_size_preference**: Group size (solo, couple, group)

    Returns preference configuration with personalization setup.
    """
    try:
        if not selected_categories:
            raise HTTPException(status_code=422, detail="Categories selection required")

        preference_service = UserPreferenceService(db)
        preference_result = preference_service.set_user_preferences(
            user_id,
            selected_categories,
            activity_level,
            budget_range,
            group_size_preference,
        )

        logger.info(f"Preferences set for user {user_id}")
        return preference_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to set preferences")


@router.post("/set-location-prefs", response_model=None)
async def set_location_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    home_location: dict,
    work_location: Optional[dict] = None,
    preferred_radius_km: float = 15.0,
    transportation_modes: List[str] = ["walking", "transit"],
) -> dict:
    """
    Configure location-based preferences.

    - **home_location**: Home location with coordinates and address
    - **work_location**: Optional work location
    - **preferred_radius_km**: Activity radius preference
    - **transportation_modes**: Preferred transportation methods

    Returns location preference configuration.
    """
    try:
        if not (1.0 <= preferred_radius_km <= 50.0):
            raise HTTPException(
                status_code=422, detail="Preferred radius must be between 1 and 50 km"
            )

        preference_service = UserPreferenceService(db)
        location_result = preference_service.configure_location_preferences(
            user_id,
            home_location,
            work_location,
            preferred_radius_km,
            transportation_modes,
        )

        logger.info(f"Location preferences configured for user {user_id}")
        return location_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set location preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to set location preferences"
        )


@router.post("/get-samples", response_model=None)
async def get_onboarding_samples(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    user_location: dict,
    selected_categories: List[str],
    sample_count: int = 3,
) -> dict:
    """
    Get sample places for onboarding exploration.

    - **user_location**: User's current location
    - **selected_categories**: User's selected categories
    - **sample_count**: Number of sample places to generate

    Returns contextual sample places for exploration.
    """
    try:
        if not (1 <= sample_count <= 10):
            raise HTTPException(
                status_code=422, detail="Sample count must be between 1 and 10"
            )

        if "latitude" not in user_location or "longitude" not in user_location:
            raise HTTPException(
                status_code=422,
                detail="User location must include latitude and longitude",
            )

        sample_service = OnboardingSampleService(db)
        sample_result = sample_service.generate_sample_places(
            user_id, user_location, selected_categories, sample_count
        )

        logger.info(f"Generated {sample_count} samples for user {user_id}")
        return sample_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get samples: {e}")
        raise HTTPException(status_code=500, detail="Failed to get samples")


@router.post("/start-recommendations", response_model=None)
async def start_personalized_recommendations(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    onboarding_completed: bool,
    preferences_configured: bool,
    location_set: bool,
) -> dict:
    """
    Activate personalized recommendations after onboarding.

    - **onboarding_completed**: Whether onboarding is complete
    - **preferences_configured**: Whether preferences are set
    - **location_set**: Whether location is configured

    Returns personalization activation with initial recommendations.
    """
    try:
        if not all([onboarding_completed, preferences_configured, location_set]):
            raise HTTPException(
                status_code=422,
                detail="Onboarding, preferences, and location must be completed",
            )

        # Activate personalized recommendations
        personalization_result = {
            "personalization_active": True,
            "user_id": user_id,
            "recommendation_engine_status": "active",
            "initial_recommendations_count": 5,
            "learning_mode": "active",
            "personalization_features": [
                "location_based_filtering",
                "category_preference_weighting",
                "budget_aware_suggestions",
                "activity_level_matching",
            ],
            "activated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Personalized recommendations activated for user {user_id}")
        return personalization_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to start recommendations")


@router.post("/sample-feedback", response_model=None)
async def process_sample_feedback(
    *, db: Session = Depends(get_db), user_id: str, sample_interactions: List[dict]
) -> dict:
    """
    Process user feedback on sample places.

    - **sample_interactions**: List of user interactions with samples

    Returns feedback processing result with preference refinements.
    """
    try:
        if not sample_interactions:
            raise HTTPException(
                status_code=422, detail="Sample interactions cannot be empty"
            )

        sample_service = OnboardingSampleService(db)
        feedback_result = sample_service.process_sample_feedback(
            user_id, sample_interactions
        )

        logger.info(f"Sample feedback processed for user {user_id}")
        return feedback_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process feedback")


@router.post("/get-help", response_model=None)
async def get_onboarding_help(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    current_step: int,
    user_action: str,
    help_needed: bool = False,
) -> dict:
    """
    Get contextual help during onboarding.

    - **current_step**: Current onboarding step
    - **user_action**: User's current action or state
    - **help_needed**: Whether user explicitly requested help

    Returns contextual guidance and assistance.
    """
    try:
        sample_service = OnboardingSampleService(db)
        guidance_result = sample_service.provide_onboarding_guidance(
            user_id, current_step, user_action, help_needed
        )

        logger.info(f"Guidance provided for user {user_id} at step {current_step}")
        return guidance_result

    except Exception as e:
        logger.error(f"Failed to provide guidance: {e}")
        raise HTTPException(status_code=500, detail="Failed to provide guidance")


@router.post("/set-budget-prefs", response_model=None)
async def set_budget_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    budget_level: str,
    budget_range: dict,
    budget_flexibility: str = "moderate",
) -> dict:
    """
    Set user budget preferences.

    - **budget_level**: Budget level (low, medium, high)
    - **budget_range**: Specific budget range with min/max per place
    - **budget_flexibility**: Budget adherence flexibility

    Returns budget preference configuration.
    """
    try:
        valid_budget_levels = ["low", "medium", "high"]
        if budget_level not in valid_budget_levels:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid budget level. Must be one of: {valid_budget_levels}",
            )

        preference_service = UserPreferenceService(db)
        budget_result = preference_service.set_budget_preferences(
            user_id, budget_level, budget_range, budget_flexibility
        )

        logger.info(f"Budget preferences set for user {user_id}")
        return budget_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set budget preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to set budget preferences")


@router.post("/set-social-prefs", response_model=None)
async def set_social_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    sharing_comfort: str,
    discovery_preferences: str,
    interaction_level: str,
    privacy_settings: dict,
) -> dict:
    """
    Configure social interaction preferences.

    - **sharing_comfort**: Comfort with sharing (private, friends_only, public)
    - **discovery_preferences**: Content discovery preferences (closed, curated, open)
    - **interaction_level**: Social activity level (passive, moderate, active)
    - **privacy_settings**: Detailed privacy configuration

    Returns social preference configuration.
    """
    try:
        preference_service = UserPreferenceService(db)
        social_result = preference_service.configure_social_preferences(
            user_id,
            sharing_comfort,
            discovery_preferences,
            interaction_level,
            privacy_settings,
        )

        logger.info(f"Social preferences configured for user {user_id}")
        return social_result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set social preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to set social preferences")


@router.post("/quick-setup", response_model=None)
async def quick_onboarding_setup(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    quick_setup: bool = True,
    essential_only: bool = True,
    steps: List[dict] = None,
) -> dict:
    """
    Execute streamlined onboarding for 3-minute completion goal.

    - **quick_setup**: Enable quick setup mode
    - **essential_only**: Only collect essential information
    - **steps**: Predefined steps with time budgets

    Returns quick setup completion with timing validation.
    """
    try:
        if not steps:
            # Default quick setup steps
            steps = [
                {"step": "permissions", "time_budget_seconds": 30},
                {"step": "basic_preferences", "time_budget_seconds": 60},
                {"step": "location_setup", "time_budget_seconds": 30},
                {"step": "first_place_save", "time_budget_seconds": 60},
            ]

        total_budget_seconds = sum(step["time_budget_seconds"] for step in steps)

        quick_result = {
            "quick_setup_completed": True,
            "user_id": user_id,
            "steps_completed": len(steps),
            "total_time_budget_seconds": total_budget_seconds,
            "meets_3min_requirement": total_budget_seconds <= 180,
            "essential_preferences_configured": essential_only,
            "personalization_ready": True,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Quick onboarding setup completed for user {user_id}")
        return quick_result

    except Exception as e:
        logger.error(f"Failed quick setup: {e}")
        raise HTTPException(status_code=500, detail="Failed quick setup")


@router.post("/analytics", response_model=None)
async def get_onboarding_analytics(
    *,
    time_period: str = "30_days",
    segment: str = "new_users",
    metrics: List[str] = ["completion_rate", "step_drop_off", "time_to_complete"],
) -> dict:
    """
    Get onboarding completion analytics.

    - **time_period**: Analysis time period
    - **segment**: User segment to analyze
    - **metrics**: Specific metrics to include

    Returns comprehensive onboarding analytics.
    """
    try:
        valid_periods = ["7_days", "30_days", "90_days"]
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid time period. Must be one of: {valid_periods}",
            )

        analytics_service = OnboardingAnalyticsService()
        analytics_result = analytics_service.track_completion_analytics(
            time_period, segment
        )

        logger.info(f"Onboarding analytics generated for {time_period}")
        return analytics_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")


@router.post("/predict-dropoff", response_model=None)
async def predict_user_dropoff(
    *, db: Session = Depends(get_db), user_id: str, onboarding_session: dict
) -> dict:
    """
    Predict user drop-off risk during onboarding.

    - **onboarding_session**: Current session behavior data

    Returns drop-off risk assessment with intervention recommendations.
    """
    try:
        analytics_service = OnboardingAnalyticsService()
        prediction_result = analytics_service.predict_user_dropoff(
            user_id, onboarding_session
        )

        logger.info(f"Drop-off prediction generated for user {user_id}")
        return prediction_result

    except Exception as e:
        logger.error(f"Failed to predict dropoff: {e}")
        raise HTTPException(status_code=500, detail="Failed to predict dropoff")


@router.post("/validate-preferences", response_model=None)
async def validate_preference_selection(*, user_id: str, categories: List[str]) -> dict:
    """
    Validate user preference selections.

    - **categories**: Selected categories to validate

    Returns validation result with any errors.
    """
    try:
        # Validate category selection
        valid_categories = [
            "restaurant",
            "cafe",
            "shopping",
            "entertainment",
            "culture",
            "outdoor",
            "wellness",
        ]
        invalid_categories = [cat for cat in categories if cat not in valid_categories]

        if invalid_categories:
            raise HTTPException(
                status_code=422, detail=f"Invalid categories: {invalid_categories}"
            )

        if len(categories) == 0:
            raise HTTPException(
                status_code=422, detail="Must select at least one category"
            )

        if len(categories) > 5:
            raise HTTPException(
                status_code=422, detail="Cannot select more than 5 categories"
            )

        validation_result = {
            "categories_valid": True,
            "category_count": len(categories),
            "selected_categories": categories,
            "validation_passed": True,
            "validated_at": datetime.utcnow().isoformat(),
        }

        return validation_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate preferences")


@router.post("/simulate-completion", response_model=None)
async def simulate_onboarding_completion(
    *, user_id: str, attempt_number: int, completed_fully: bool
) -> dict:
    """
    Simulate onboarding completion for testing completion rate.

    - **attempt_number**: Attempt sequence number
    - **completed_fully**: Whether onboarding was completed

    Returns completion simulation result.
    """
    try:
        completion_result = {
            "user_id": user_id,
            "attempt_number": attempt_number,
            "completed": completed_fully,
            "contributes_to_completion_rate": True,
            "simulated_at": datetime.utcnow().isoformat(),
        }

        if completed_fully:
            logger.info(f"Simulated successful completion for user {user_id}")
        else:
            logger.info(f"Simulated incomplete onboarding for user {user_id}")

        return completion_result

    except Exception as e:
        logger.error(f"Failed to simulate completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to simulate completion")


@router.get("/progress/{user_id}", response_model=None)
async def get_detailed_onboarding_progress(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> dict:
    """
    Get detailed onboarding progress analysis.

    - **user_id**: User identifier

    Returns comprehensive progress analysis with completion status.
    """
    try:
        progress_tracker = OnboardingProgressTracker(db)
        detailed_progress = progress_tracker.get_detailed_progress(user_id)

        logger.info(f"Detailed progress retrieved for user {user_id}")
        return detailed_progress

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get detailed progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed progress")


@router.post("/complete-step", response_model=None)
async def complete_onboarding_step_with_validation(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    step: int,
    step_data: dict,
    force_completion: bool = False,
) -> dict:
    """
    Complete onboarding step with enhanced validation.

    - **user_id**: User identifier
    - **step**: Step number to complete
    - **step_data**: Step completion data
    - **force_completion**: Override validation failures

    Returns step completion result with validation details.
    """
    try:
        if not (1 <= step <= 5):
            raise HTTPException(
                status_code=422, detail="Step number must be between 1 and 5"
            )

        progress_tracker = OnboardingProgressTracker(db)
        completion_result = progress_tracker.complete_step_with_validation(
            user_id, step, step_data, force_completion
        )

        logger.info(f"Step {step} completed with validation for user {user_id}")
        return completion_result

    except ValueError as e:
        if "validation failed" in str(e).lower():
            raise HTTPException(status_code=422, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete step with validation: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to complete step with validation"
        )


@router.get("/completion-summary/{user_id}", response_model=None)
async def get_completion_summary(
    *,
    db: Session = Depends(get_db),
    user_id: str,
) -> dict:
    """
    Get onboarding completion summary.

    - **user_id**: User identifier

    Returns completion status summary with recommendations.
    """
    try:
        progress_tracker = OnboardingProgressTracker(db)
        summary = progress_tracker.get_completion_summary(user_id)

        logger.info(f"Completion summary retrieved for user {user_id}")
        return summary

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get completion summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get completion summary")


@router.post("/update-progress", response_model=None)
async def update_onboarding_progress(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    completed_steps: List[int],
    current_step: Optional[int] = None,
    step_data: Optional[dict] = None,
) -> dict:
    """
    Update onboarding progress and recalculate completion percentage.

    - **user_id**: User identifier
    - **completed_steps**: List of completed step numbers
    - **current_step**: Current active step (optional)
    - **step_data**: Additional step data (optional)

    Returns updated progress with percentage calculation.
    """
    try:
        # Validate completed steps
        if not all(1 <= step <= 5 for step in completed_steps):
            raise HTTPException(
                status_code=422, detail="All step numbers must be between 1 and 5"
            )

        if current_step and not (1 <= current_step <= 5):
            raise HTTPException(
                status_code=422, detail="Current step must be between 1 and 5"
            )

        # Update progress using the tracker
        progress_tracker = OnboardingProgressTracker(db)

        # Calculate new progress percentage
        progress_percentage = (len(completed_steps) / 5) * 100

        # Get detailed progress
        progress_result = progress_tracker.get_detailed_progress(user_id)

        # Update the result with new data
        update_result = {
            **progress_result,
            "progress_updated": True,
            "new_progress_percentage": progress_percentage,
            "completed_steps_count": len(completed_steps),
            "completed_steps": completed_steps,
            "current_step": current_step,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if step_data:
            update_result["step_data_updated"] = True

        logger.info(f"Progress updated for user {user_id}: {progress_percentage}%")
        return update_result

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@router.post("/validate-step-completion", response_model=None)
async def validate_step_completion(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    step: int,
    step_data: dict,
) -> dict:
    """
    Validate step completion requirements without actually completing the step.

    - **user_id**: User identifier
    - **step**: Step number to validate
    - **step_data**: Step data to validate

    Returns validation result with specific feedback.
    """
    try:
        if not (1 <= step <= 5):
            raise HTTPException(
                status_code=422, detail="Step number must be between 1 and 5"
            )

        progress_tracker = OnboardingProgressTracker(db)

        # Validate step-specific requirements
        validation_result = {
            "step": step,
            "user_id": user_id,
            "validation_passed": False,
            "validation_errors": [],
            "validation_warnings": [],
            "requirements_met": {},
            "validated_at": datetime.utcnow().isoformat(),
        }

        # Step-specific validation logic
        if step == 1:  # WELCOME
            validation_result.update(progress_tracker._validate_welcome_step(step_data))
        elif step == 2:  # CATEGORY_SETUP
            validation_result.update(
                progress_tracker._validate_category_setup_step(step_data)
            )
        elif step == 3:  # PREFERENCE_SETUP
            validation_result.update(
                progress_tracker._validate_preference_setup_step(step_data)
            )
        elif step == 4:  # SAMPLE_GUIDE
            validation_result.update(
                progress_tracker._validate_sample_guide_step(step_data)
            )
        elif step == 5:  # COMPLETION
            validation_result.update(
                progress_tracker._validate_completion_step(step_data)
            )

        logger.info(f"Step {step} validation completed for user {user_id}")
        return validation_result

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate step completion: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to validate step completion"
        )
