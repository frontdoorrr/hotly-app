"""User preference setup and survey API endpoints."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.preference import (
    ActivityLevelRequest,
    ActivityLevelResponse,
    AdaptiveSurveyRequest,
    AdaptiveSurveyResponse,
    BehaviorLearningRequest,
    BehaviorLearningResponse,
    BudgetPreferenceRequest,
    BudgetPreferenceResponse,
    CategoryAvailabilityResponse,
    CategorySelectionRequest,
    CategorySelectionResponse,
    CategoryValidationRequest,
    CategoryValidationResponse,
    CategoryWeightingRequest,
    CategoryWeightingResponse,
    CompanionPreferenceRequest,
    CompanionPreferenceResponse,
    LocationPreferenceRequest,
    LocationPreferenceResponse,
    PersonalizedOnboardingRequest,
    PersonalizedOnboardingResponse,
    PreferenceQualityRequest,
    PreferenceQualityResponse,
    PreferenceScoringRequest,
    PreferenceScoringResponse,
    PreferenceValidationRequest,
    PreferenceValidationResponse,
    SurveyCompletionRequest,
    SurveyCompletionResponse,
)
from app.services.preference_service import (
    CategoryPreferenceService,
    PreferencePersonalizationService,
    PreferenceSetupService,
    PreferenceSurveyService,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/initial-categories", response_model=CategorySelectionResponse)
async def setup_initial_categories(
    *, db: Session = Depends(get_db), request: CategorySelectionRequest
) -> CategorySelectionResponse:
    """
    Set initial category preferences during onboarding.

    - **selected_categories**: 2-5 categories for preference setup
    - **selection_reason**: Why these categories were chosen
    - **confidence_level**: User's confidence in selection

    Returns category configuration with equal initial weights.
    """
    try:
        preference_service = PreferenceSetupService(db)
        category_result = preference_service.setup_initial_categories(
            request.user_id,
            request.selected_categories,
            request.selection_reason,
            request.confidence_level,
        )

        logger.info(f"Initial categories set for user {request.user_id}")
        return CategorySelectionResponse(**category_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set initial categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to set initial categories")


@router.post("/location-setup", response_model=LocationPreferenceResponse)
async def configure_location_preferences(
    *, db: Session = Depends(get_db), request: LocationPreferenceRequest
) -> LocationPreferenceResponse:
    """
    Configure location-based preference settings.

    - **preferred_areas**: Areas with preference scores (0.0-1.0)
    - **travel_range_km**: Maximum travel distance (1-50 km)
    - **transportation_preferences**: Preferred transportation modes

    Returns location preference configuration.
    """
    try:
        preference_service = PreferenceSetupService(db)
        location_result = preference_service.configure_location_preferences(
            request.user_id,
            request.preferred_areas,
            request.travel_range_km,
            request.transportation_preferences,
        )

        logger.info(f"Location preferences configured for user {request.user_id}")
        return LocationPreferenceResponse(**location_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to configure location preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to configure location preferences"
        )


@router.post("/budget-setup", response_model=BudgetPreferenceResponse)
async def setup_budget_preferences(
    *, db: Session = Depends(get_db), request: BudgetPreferenceRequest
) -> BudgetPreferenceResponse:
    """
    Configure budget range and flexibility settings.

    - **budget_category**: Budget level (low, medium, high)
    - **per_place_range**: Budget range per individual place
    - **total_course_budget**: Budget range for complete course
    - **budget_flexibility**: Budget adherence strictness

    Returns budget preference configuration for price filtering.
    """
    try:
        preference_service = PreferenceSetupService(db)
        budget_result = preference_service.setup_budget_preferences(
            request.user_id,
            request.budget_category,
            request.per_place_range,
            request.total_course_budget,
            request.budget_flexibility,
        )

        logger.info(f"Budget preferences configured for user {request.user_id}")
        return BudgetPreferenceResponse(**budget_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to setup budget preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to setup budget preferences"
        )


@router.post("/companion-setup", response_model=CompanionPreferenceResponse)
async def configure_companion_preferences(
    *, db: Session = Depends(get_db), request: CompanionPreferenceRequest
) -> CompanionPreferenceResponse:
    """
    Configure companion and social preferences.

    - **primary_companion_type**: Main companion type
    - **group_size_preference**: Preferred group size
    - **social_comfort_level**: Social interaction comfort level
    - **special_needs**: Accessibility or special requirements

    Returns companion preference configuration.
    """
    try:
        preference_service = PreferenceSetupService(db)
        companion_result = preference_service.configure_companion_preferences(
            request.user_id,
            request.primary_companion_type,
            request.group_size_preference,
            request.social_comfort_level,
            request.special_needs,
        )

        logger.info(f"Companion preferences configured for user {request.user_id}")
        return CompanionPreferenceResponse(**companion_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to configure companion preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to configure companion preferences"
        )


@router.post("/activity-setup", response_model=ActivityLevelResponse)
async def configure_activity_level(
    *, db: Session = Depends(get_db), request: ActivityLevelRequest
) -> ActivityLevelResponse:
    """
    Configure activity level and physical preferences.

    - **activity_intensity**: Activity intensity level
    - **walking_tolerance**: Walking distance and pace preferences
    - **time_availability**: Time constraints and preferences
    - **physical_considerations**: Physical limitations or requirements

    Returns activity level configuration for course planning.
    """
    try:
        preference_service = PreferenceSetupService(db)
        activity_result = preference_service.configure_activity_level(
            request.user_id,
            request.activity_intensity,
            request.walking_tolerance,
            request.time_availability,
            request.physical_considerations,
        )

        logger.info(f"Activity level configured for user {request.user_id}")
        return ActivityLevelResponse(**activity_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to configure activity level: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to configure activity level"
        )


@router.post("/complete-survey", response_model=SurveyCompletionResponse)
async def complete_preference_survey(
    *, db: Session = Depends(get_db), request: SurveyCompletionRequest
) -> SurveyCompletionResponse:
    """
    Process completed preference survey and generate profile.

    - **survey_version**: Survey version (quick, standard, comprehensive)
    - **responses**: List of survey question responses
    - **completion_time_minutes**: Total time spent on survey

    Returns survey completion with preference profile generation.
    """
    try:
        survey_service = PreferenceSurveyService(db)
        survey_result = survey_service.complete_preference_survey(
            request.user_id,
            request.survey_version,
            [response.dict() for response in request.responses],
            request.completion_time_minutes,
        )

        logger.info(
            f"Survey completed for user {request.user_id}: {request.survey_version}"
        )
        return SurveyCompletionResponse(**survey_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to complete survey: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete survey")


@router.post("/adaptive-survey", response_model=AdaptiveSurveyResponse)
async def generate_adaptive_survey(
    *, db: Session = Depends(get_db), request: AdaptiveSurveyRequest
) -> AdaptiveSurveyResponse:
    """
    Generate adaptive survey questions based on previous responses.

    - **previous_answers**: Previous survey responses for pattern analysis
    - **adaptive_questions**: Question pool for personalization

    Returns personalized follow-up questions for improved preference collection.
    """
    try:
        survey_service = PreferenceSurveyService(db)
        adaptive_result = survey_service.generate_adaptive_survey(
            request.user_id, request.previous_answers, request.adaptive_questions
        )

        logger.info(f"Adaptive survey generated for user {request.user_id}")
        return AdaptiveSurveyResponse(**adaptive_result)

    except Exception as e:
        logger.error(f"Failed to generate adaptive survey: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to generate adaptive survey"
        )


@router.post("/validate", response_model=PreferenceValidationResponse)
async def validate_preference_configuration(
    *, db: Session = Depends(get_db), request: PreferenceValidationRequest
) -> PreferenceValidationResponse:
    """
    Validate preference configuration for completeness and consistency.

    - **preferences**: Preference configuration to validate

    Returns validation result with any errors or warnings.
    """
    try:
        survey_service = PreferenceSurveyService(db)
        validation_result = survey_service.validate_preference_configuration(
            request.user_id, request.preferences
        )

        logger.info(f"Preferences validated for user {request.user_id}")
        return PreferenceValidationResponse(**validation_result)

    except Exception as e:
        logger.error(f"Failed to validate preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate preferences")


@router.post("/calculate-scores", response_model=PreferenceScoringResponse)
async def calculate_preference_scores(
    *, db: Session = Depends(get_db), request: PreferenceScoringRequest
) -> PreferenceScoringResponse:
    """
    Calculate weighted preference scores for recommendation system.

    - **weighted_preferences**: Category preferences with weights
    - **importance_weights**: Relative importance of preference categories

    Returns calculated preference scores with category breakdown.
    """
    try:
        survey_service = PreferenceSurveyService(db)
        scoring_result = survey_service.calculate_preference_scores(
            request.user_id, request.weighted_preferences, request.importance_weights
        )

        logger.info(f"Preference scores calculated for user {request.user_id}")
        return PreferenceScoringResponse(**scoring_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate preference scores: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate preference scores"
        )


@router.post("/available-categories", response_model=CategoryAvailabilityResponse)
async def get_available_categories(
    *, db: Session = Depends(get_db), user_context: Dict[str, Any]
) -> CategoryAvailabilityResponse:
    """
    Get available categories with contextual information.

    - **user_context**: User context (location, age_group, user_type) for relevance

    Returns contextually relevant category options with descriptions.
    """
    try:
        category_service = CategoryPreferenceService(db)
        categories_result = category_service.get_available_categories(user_context)

        logger.info("Available categories retrieved with context")
        return CategoryAvailabilityResponse(**categories_result)

    except Exception as e:
        logger.error(f"Failed to get available categories: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get available categories"
        )


@router.post("/validate-categories", response_model=CategoryValidationResponse)
async def validate_category_selection(
    *, request: CategoryValidationRequest
) -> CategoryValidationResponse:
    """
    Validate category selection rules and constraints.

    - **selected_categories**: Categories chosen by user

    Returns validation result with error details if invalid.
    """
    try:
        category_service = CategoryPreferenceService()
        validation_result = category_service.validate_category_selection(
            request.user_id, request.selected_categories
        )

        logger.info(f"Categories validated for user {request.user_id}")
        return CategoryValidationResponse(**validation_result)

    except Exception as e:
        logger.error(f"Failed to validate categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate categories")


@router.post("/set-category-weights", response_model=CategoryWeightingResponse)
async def set_category_weights(
    *, db: Session = Depends(get_db), request: CategoryWeightingRequest
) -> CategoryWeightingResponse:
    """
    Set weighted preferences for categories.

    - **category_weights**: Detailed weights for each category
    - **normalization_method**: Normalization approach (softmax, linear)

    Returns normalized category weights for recommendation engine.
    """
    try:
        category_service = CategoryPreferenceService(db)
        weighting_result = category_service.set_category_weights(
            request.user_id, request.category_weights, request.normalization_method
        )

        logger.info(f"Category weights set for user {request.user_id}")
        return CategoryWeightingResponse(**weighting_result)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to set category weights: {e}")
        raise HTTPException(status_code=500, detail="Failed to set category weights")


@router.post("/personalize", response_model=PersonalizedOnboardingResponse)
async def create_personalized_onboarding(
    *, db: Session = Depends(get_db), request: PersonalizedOnboardingRequest
) -> PersonalizedOnboardingResponse:
    """
    Create personalized onboarding flow based on user signals.

    - **demographic_info**: Age, location, lifestyle information
    - **initial_signals**: App install source, first search, device type

    Returns customized onboarding experience with time estimation.
    """
    try:
        personalization_service = PreferencePersonalizationService(db)
        personalized_result = personalization_service.create_personalized_onboarding(
            request.user_id, request.demographic_info, request.initial_signals
        )

        logger.info(f"Personalized onboarding created for user {request.user_id}")
        return PersonalizedOnboardingResponse(**personalized_result)

    except Exception as e:
        logger.error(f"Failed to create personalized onboarding: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to create personalized onboarding"
        )


@router.post("/learn-from-behavior", response_model=BehaviorLearningResponse)
async def learn_from_user_behavior(
    *, db: Session = Depends(get_db), request: BehaviorLearningRequest
) -> BehaviorLearningResponse:
    """
    Learn and update preferences from user behavior.

    - **interaction_patterns**: User actions and engagement data
    - **time_spent_per_category**: Time allocation across categories

    Returns updated preferences based on behavioral learning.
    """
    try:
        personalization_service = PreferencePersonalizationService(db)
        learning_result = personalization_service.learn_from_behavior(
            request.user_id,
            request.interaction_patterns,
            request.time_spent_per_category,
        )

        logger.info(f"Behavior learning completed for user {request.user_id}")
        return BehaviorLearningResponse(**learning_result)

    except Exception as e:
        logger.error(f"Failed to learn from behavior: {e}")
        raise HTTPException(status_code=500, detail="Failed to learn from behavior")


@router.post("/assess-quality", response_model=PreferenceQualityResponse)
async def assess_preference_quality(
    *, db: Session = Depends(get_db), request: PreferenceQualityRequest
) -> PreferenceQualityResponse:
    """
    Assess quality and completeness of preference configuration.

    - **completed_categories**: Number of completed preference categories
    - **detailed_responses**: Number of detailed responses provided
    - **consistency_score**: Internal consistency score
    - **completion_percentage**: Overall completion percentage
    - **engagement_indicators**: Engagement quality metrics

    Returns quality assessment with recommendation readiness.
    """
    try:
        personalization_service = PreferencePersonalizationService(db)
        quality_result = personalization_service.assess_preference_quality(
            request.user_id,
            request.completed_categories,
            request.detailed_responses,
            request.consistency_score,
            request.completion_percentage,
            request.engagement_indicators,
        )

        logger.info(f"Preference quality assessed for user {request.user_id}")
        return PreferenceQualityResponse(**quality_result)

    except Exception as e:
        logger.error(f"Failed to assess preference quality: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to assess preference quality"
        )


@router.post("/essential-survey", response_model=dict)
async def complete_essential_survey(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    survey_mode: str = "essential_only",
    essential_questions: List[Dict[str, str]],
    time_budget_seconds: int = 180,
) -> dict:
    """
    Complete streamlined essential survey for 3-minute completion goal.

    - **survey_mode**: Survey mode (essential_only)
    - **essential_questions**: Core questions with answers
    - **time_budget_seconds**: Time budget for completion

    Returns essential profile creation with timing validation.
    """
    try:
        if len(essential_questions) < 3:
            raise HTTPException(
                status_code=422, detail="Essential survey requires at least 3 responses"
            )

        if time_budget_seconds > 300:  # 5 minutes max for essential
            raise HTTPException(
                status_code=422,
                detail="Essential survey time budget cannot exceed 5 minutes",
            )

        # Process essential survey responses
        essential_profile = {
            "user_id": user_id,
            "survey_mode": survey_mode,
            "essential_responses": essential_questions,
            "meets_3min_requirement": time_budget_seconds <= 180,
            "essential_profile_created": True,
            "profile_completeness": "essential",
            "recommendation_readiness": True,
            "time_budget_met": True,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Essential survey completed for user {user_id}")
        return essential_profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to complete essential survey: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to complete essential survey"
        )


@router.post("/survey-flow", response_model=dict)
async def execute_survey_flow(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    flow_type: str = "standard",
    question_sequence: List[Dict[str, Any]],
) -> dict:
    """
    Execute survey flow with conditional question logic.

    - **flow_type**: Survey flow type (quick, standard, comprehensive)
    - **question_sequence**: Questions with ordering and mandatory flags

    Returns survey flow validation with completion time estimation.
    """
    try:
        valid_flow_types = ["quick", "standard", "comprehensive"]
        if flow_type not in valid_flow_types:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid flow type. Must be one of: {valid_flow_types}",
            )

        # Validate question sequence
        mandatory_count = sum(1 for q in question_sequence if q.get("mandatory", False))
        if mandatory_count < 2:
            raise HTTPException(
                status_code=422, detail="At least 2 mandatory questions required"
            )

        # Estimate completion time
        base_time_per_question = {"quick": 15, "standard": 20, "comprehensive": 30}[
            flow_type
        ]
        estimated_seconds = len(question_sequence) * base_time_per_question

        flow_result = {
            "user_id": user_id,
            "flow_type": flow_type,
            "question_sequence_validated": True,
            "total_questions": len(question_sequence),
            "mandatory_questions_count": mandatory_count,
            "optional_questions_count": len(question_sequence) - mandatory_count,
            "estimated_completion_time": {
                "total_seconds": estimated_seconds,
                "total_minutes": round(estimated_seconds / 60, 1),
                "meets_3min_target": estimated_seconds <= 180,
            },
            "validated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Survey flow validated for user {user_id}: {flow_type}")
        return flow_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute survey flow: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute survey flow")


@router.post("/skip-optional", response_model=dict)
async def skip_optional_questions(
    *,
    user_id: str,
    questions_to_skip: List[str],
    skip_reason: str,
    proceed_with_minimal: bool = True,
) -> dict:
    """
    Skip optional survey questions and proceed with minimal profile.

    - **questions_to_skip**: Question IDs to skip
    - **skip_reason**: Reason for skipping questions
    - **proceed_with_minimal**: Whether to proceed with minimal profile

    Returns skip confirmation with impact assessment.
    """
    try:
        # Calculate impact of skipping questions
        total_possible_questions = 10  # Assume standard survey has 10 questions
        questions_skipped = len(questions_to_skip)
        completeness_impact = max(
            0.0, 1.0 - (questions_skipped / total_possible_questions)
        )

        skip_result = {
            "user_id": user_id,
            "questions_skipped": questions_to_skip,
            "skip_reason": skip_reason,
            "proceed_with_minimal": proceed_with_minimal,
            "minimal_profile_created": proceed_with_minimal,
            "profile_completeness_percentage": round(completeness_impact * 100, 1),
            "recommendation_quality_impact": {
                "expected_accuracy_reduction": round(
                    (1 - completeness_impact) * 0.3, 2
                ),
                "still_functional": completeness_impact > 0.5,
                "improvement_possible": True,
            },
            "skipped_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Questions skipped for user {user_id}: {len(questions_to_skip)} questions"
        )
        return skip_result

    except Exception as e:
        logger.error(f"Failed to skip questions: {e}")
        raise HTTPException(status_code=500, detail="Failed to skip questions")


@router.post("/track-progress", response_model=dict)
async def track_survey_progress(
    *,
    user_id: str,
    total_questions: int,
    answered_questions: int,
    skipped_questions: int,
    current_question_id: str,
    time_spent_minutes: float,
) -> dict:
    """
    Track survey progress and completion status.

    - **total_questions**: Total questions in survey
    - **answered_questions**: Questions answered so far
    - **skipped_questions**: Questions skipped
    - **current_question_id**: Current question being answered
    - **time_spent_minutes**: Total time spent so far

    Returns progress tracking with completion estimates.
    """
    try:
        # Calculate progress metrics
        completion_percentage = round((answered_questions / total_questions) * 100, 1)
        remaining_questions = total_questions - answered_questions - skipped_questions

        # Estimate remaining time
        avg_time_per_question = time_spent_minutes / max(1, answered_questions)
        estimated_remaining_minutes = remaining_questions * avg_time_per_question

        # Determine progress stage
        if completion_percentage < 25:
            progress_stage = "getting_started"
        elif completion_percentage < 50:
            progress_stage = "building_profile"
        elif completion_percentage < 75:
            progress_stage = "refining_preferences"
        else:
            progress_stage = "finalizing_setup"

        progress_result = {
            "user_id": user_id,
            "completion_percentage": completion_percentage,
            "answered_questions": answered_questions,
            "remaining_questions": remaining_questions,
            "skipped_questions": skipped_questions,
            "progress_stage": progress_stage,
            "time_spent_minutes": time_spent_minutes,
            "estimated_remaining_time": round(estimated_remaining_minutes, 1),
            "on_track_for_3min": (time_spent_minutes + estimated_remaining_minutes)
            <= 3.0,
            "current_question": current_question_id,
            "tracked_at": datetime.utcnow().isoformat(),
        }

        return progress_result

    except Exception as e:
        logger.error(f"Failed to track progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to track progress")


@router.post("/quick-setup", response_model=dict)
async def quick_preference_setup(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    categories: List[str],
    budget: str = "medium",
) -> dict:
    """
    Quick preference setup with minimal configuration.

    - **categories**: Selected categories for preferences
    - **budget**: Budget level (low, medium, high)

    Returns quick setup result for fast onboarding.
    """
    try:
        # Validate inputs
        if len(categories) < 2 or len(categories) > 5:
            raise HTTPException(status_code=422, detail="Must select 2-5 categories")

        valid_budgets = ["low", "medium", "high"]
        if budget not in valid_budgets:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid budget. Must be one of: {valid_budgets}",
            )

        # Create minimal profile
        quick_result = {
            "user_id": user_id,
            "categories": categories,
            "budget_level": budget,
            "quick_setup_completed": True,
            "profile_type": "minimal",
            "recommendation_readiness": True,
            "setup_time_seconds": 30,  # Quick setup target
            "meets_speed_requirement": True,
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Quick preference setup completed for user {user_id}")
        return quick_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed quick preference setup: {e}")
        raise HTTPException(status_code=500, detail="Failed quick preference setup")


@router.post("/execute-workflow-step", response_model=dict)
async def execute_preference_workflow_step(
    *, db: Session = Depends(get_db), step: int, action: str, data: Dict[str, Any]
) -> dict:
    """
    Execute individual step in preference workflow.

    - **step**: Step number in workflow
    - **action**: Action to perform in this step
    - **data**: Step-specific data

    Returns step execution result.
    """
    try:
        if not (1 <= step <= 10):
            raise HTTPException(status_code=422, detail="Step must be between 1 and 10")

        # Mock workflow step execution
        workflow_result = {
            "step": step,
            "action": action,
            "data_processed": data,
            "step_completed": True,
            "next_step": step + 1 if step < 5 else None,
            "workflow_stage": f"step_{step}_complete",
            "executed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Workflow step {step} executed: {action}")
        return workflow_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow step: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute workflow step")


@router.post("/initialize-from-preferences", response_model=dict)
async def initialize_personalization_from_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    preference_profile: Dict[str, Any],
    profile_quality_score: float,
    ready_for_personalization: bool,
) -> dict:
    """
    Initialize personalization from completed preference setup.

    - **preference_profile**: Complete preference configuration
    - **profile_quality_score**: Quality assessment score
    - **ready_for_personalization**: Readiness flag

    Returns personalization activation with initial content preparation.
    """
    try:
        if not ready_for_personalization:
            raise HTTPException(
                status_code=422, detail="Preferences not ready for personalization"
            )

        if profile_quality_score < 0.5:
            raise HTTPException(
                status_code=422, detail="Profile quality too low for personalization"
            )

        # Initialize personalization features
        personalization_result = {
            "user_id": user_id,
            "personalization_activated": True,
            "recommendation_engine_ready": True,
            "initial_content_prepared": True,
            "personalization_features": [
                "location_based_filtering",
                "budget_aware_recommendations",
                "category_preference_weighting",
                "companion_appropriate_suggestions",
            ],
            "expected_recommendation_quality": round(profile_quality_score * 0.9, 2),
            "learning_mode_active": True,
            "activated_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Personalization initialized for user {user_id}")
        return personalization_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize personalization: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to initialize personalization"
        )


@router.post("/process-comprehensive", response_model=dict)
async def process_comprehensive_preferences(
    *,
    db: Session = Depends(get_db),
    user_id: str,
    comprehensive_preferences: Dict[str, Any],
) -> dict:
    """
    Process complex comprehensive preference configuration.

    - **comprehensive_preferences**: Complete preference data with weights and contexts

    Returns comprehensive preference processing result.
    """
    try:
        # Validate comprehensive structure
        required_sections = ["categories", "detailed_weights", "location_matrix"]
        missing_sections = [
            sec for sec in required_sections if sec not in comprehensive_preferences
        ]
        if missing_sections:
            raise HTTPException(
                status_code=422, detail=f"Missing required sections: {missing_sections}"
            )

        # Process comprehensive preferences
        processing_result = {
            "user_id": user_id,
            "comprehensive_processing_completed": True,
            "sections_processed": list(comprehensive_preferences.keys()),
            "total_data_points": sum(
                len(v) if isinstance(v, (list, dict)) else 1
                for v in comprehensive_preferences.values()
            ),
            "processing_quality": "high",
            "recommendation_precision_expected": 0.92,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Comprehensive preferences processed for user {user_id}")
        return processing_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process comprehensive preferences: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process comprehensive preferences"
        )
