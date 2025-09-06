"""User preference and behavior schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class UserBehaviorCreate(BaseModel):
    """Schema for creating user behavior records."""

    action: str = Field(..., description="Action type: visit, save, share, rate")
    place_id: Optional[UUID] = Field(None, description="Related place ID")
    duration_minutes: Optional[int] = Field(
        None, ge=0, le=1440, description="Duration in minutes"
    )
    rating: Optional[float] = Field(
        None, ge=1.0, le=5.0, description="User rating (1-5)"
    )
    tags_added: List[str] = Field(
        default_factory=list, description="Tags added during interaction"
    )
    time_of_day: Optional[str] = Field(
        None, description="Time of day: morning, afternoon, evening, night"
    )
    day_of_week: Optional[str] = Field(None, description="Day of week")

    @validator("action")
    def validate_action(cls, v):
        valid_actions = [
            "visit",
            "save",
            "share",
            "rate",
            "search",
            "view",
            "click",
            "feedback",
        ]
        if v not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {valid_actions}")
        return v

    @validator("time_of_day")
    def validate_time_of_day(cls, v):
        if v is not None:
            valid_times = ["morning", "afternoon", "evening", "night"]
            if v not in valid_times:
                raise ValueError(f"Invalid time_of_day. Must be one of: {valid_times}")
        return v


class UserBehaviorResponse(BaseModel):
    """Response schema for user behavior records."""

    id: str = Field(..., description="Behavior record ID")
    user_id: str = Field(..., description="User ID")
    action: str = Field(..., description="Action performed")
    place_id: Optional[str] = Field(None, description="Related place ID")
    rating: Optional[float] = Field(None, description="User rating")
    created_at: datetime = Field(..., description="When behavior was recorded")

    class Config:
        orm_mode = True


class PreferenceAnalysisResponse(BaseModel):
    """Response schema for preference analysis results."""

    user_id: str = Field(..., description="User identifier")
    cuisine_preferences: Dict[str, float] = Field(
        ..., description="Cuisine category preferences (0-1)"
    )
    ambiance_preferences: Dict[str, float] = Field(
        ..., description="Ambiance preferences (0-1)"
    )
    price_preferences: Dict[str, float] = Field(
        ..., description="Price range preferences (0-1)"
    )
    location_preferences: Dict[str, Any] = Field(
        ..., description="Geographic preferences"
    )
    time_preferences: Dict[str, float] = Field(
        ..., description="Temporal preferences (0-1)"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in analysis"
    )
    analysis_date: datetime = Field(..., description="When analysis was performed")
    data_points_count: int = Field(..., description="Number of data points used")


class UserProfileCreate(BaseModel):
    """Schema for creating user profiles."""

    age_group: Optional[str] = Field(
        None, description="Age group: teens, 20s, 30s, 40s, 50s+"
    )
    location_preference: Optional[str] = Field(None, description="Preferred area")
    budget_range: str = Field(
        "moderate", description="Budget preference: budget, moderate, expensive"
    )
    dietary_restrictions: List[str] = Field(
        default_factory=list, description="Dietary restrictions"
    )
    activity_preferences: List[str] = Field(
        default_factory=list, description="Preferred activities"
    )

    @validator("budget_range")
    def validate_budget_range(cls, v):
        valid_ranges = ["budget", "moderate", "expensive"]
        if v not in valid_ranges:
            raise ValueError(f"Invalid budget_range. Must be one of: {valid_ranges}")
        return v


class UserProfileResponse(BaseModel):
    """Response schema for user profiles."""

    user_id: str = Field(..., description="User identifier")
    preferences: PreferenceAnalysisResponse = Field(
        ..., description="Analyzed preferences"
    )
    profile_completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Profile completeness score"
    )
    last_updated: datetime = Field(..., description="Last profile update")
    total_interactions: int = Field(..., description="Total user interactions")


class FeedbackCreate(BaseModel):
    """Schema for creating user feedback."""

    place_id: Optional[UUID] = Field(None, description="Place being rated")
    recommendation_id: Optional[UUID] = Field(
        None, description="Recommendation being rated"
    )
    rating: float = Field(..., ge=1.0, le=5.0, description="Rating (1-5)")
    feedback_text: Optional[str] = Field(
        None, max_length=1000, description="Text feedback"
    )
    visited: bool = Field(False, description="Whether user actually visited")
    would_recommend: Optional[bool] = Field(
        None, description="Would recommend to others"
    )

    @validator("rating")
    def validate_rating(cls, v):
        if not (1.0 <= v <= 5.0):
            raise ValueError("Rating must be between 1.0 and 5.0")
        return v


class PreferenceUpdateRequest(BaseModel):
    """Request to update specific preference weights."""

    preference_type: str = Field(
        ..., description="Type: cuisine, ambiance, price, location, time"
    )
    updates: Dict[str, float] = Field(..., description="Preference updates")

    @validator("preference_type")
    def validate_preference_type(cls, v):
        valid_types = ["cuisine", "ambiance", "price", "location", "time"]
        if v not in valid_types:
            raise ValueError(f"Invalid preference_type. Must be one of: {valid_types}")
        return v

    @validator("updates")
    def validate_updates(cls, v):
        for key, value in v.items():
            if not (0.0 <= value <= 1.0):
                raise ValueError(
                    f"Preference value for {key} must be between 0.0 and 1.0"
                )
        return v


class PreferenceHistoryResponse(BaseModel):
    """Response schema for preference change history."""

    user_id: str = Field(..., description="User identifier")
    changes: List[Dict[str, Any]] = Field(
        ..., description="Preference changes over time"
    )
    analysis_period_days: int = Field(..., description="Period analyzed")
    total_changes: int = Field(..., description="Total preference changes detected")


class LearningMetricsResponse(BaseModel):
    """Response schema for preference learning metrics."""

    user_id: str = Field(..., description="User identifier")
    prediction_accuracy: float = Field(..., description="Current prediction accuracy")
    feedback_count: int = Field(..., description="Total feedback received")
    positive_feedback_rate: float = Field(..., description="Rate of positive feedback")
    model_confidence: float = Field(..., description="Model confidence in predictions")
    last_learning_update: datetime = Field(
        ..., description="Last time model was updated"
    )


class PreferenceSummary(BaseModel):
    """Summary of user preferences for quick access."""

    top_cuisines: List[str] = Field(..., description="Top preferred cuisine types")
    preferred_ambiance: List[str] = Field(
        ..., description="Preferred ambiance characteristics"
    )
    budget_level: str = Field(..., description="Preferred budget level")
    activity_radius_km: float = Field(..., description="Preferred travel radius")
    peak_activity_times: List[str] = Field(
        ..., description="Preferred times for activities"
    )
    confidence_level: str = Field(
        ..., description="Confidence level: low, medium, high"
    )


class BehaviorAnalyticsRequest(BaseModel):
    """Request for behavior analytics."""

    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    behavior_types: List[str] = Field(
        default_factory=list, description="Specific behaviors to analyze"
    )
    include_trends: bool = Field(True, description="Include trend analysis")


class BehaviorAnalyticsResponse(BaseModel):
    """Response for behavior analytics."""

    user_id: str = Field(..., description="User identifier")
    analysis_period: Dict[str, datetime] = Field(..., description="Period analyzed")
    behavior_summary: Dict[str, int] = Field(..., description="Behavior counts by type")
    engagement_trends: Dict[str, List[float]] = Field(
        ..., description="Engagement trends over time"
    )
    preference_stability: float = Field(..., description="How stable preferences are")
    recommendation_acceptance_rate: float = Field(
        ..., description="Rate of accepting recommendations"
    )


# New schemas for Task 2-1-2 Preference Setup System


class AdaptiveSurveyRequest(BaseModel):
    """Request for adaptive survey generation."""

    user_id: str
    previous_answers: List[Dict[str, Any]]
    adaptive_questions: List[Dict[str, Any]]


class CompanionPreferenceRequest(BaseModel):
    """Request for companion preference setup."""

    user_id: str
    primary_companion_type: str = Field(
        ..., regex="^(alone|romantic_partner|friends|family)$"
    )
    group_size_preference: str = Field(
        ..., regex="^(solo|couple|small_group|large_group)$"
    )
    social_comfort_level: str = Field(..., regex="^(introverted|moderate|extroverted)$")
    special_needs: Optional[List[str]] = []


class ActivityLevelRequest(BaseModel):
    """Request for activity level configuration."""

    user_id: str
    activity_intensity: str = Field(..., regex="^(low|moderate|high)$")
    walking_tolerance: Dict[str, Any]
    time_availability: Dict[str, Any]
    physical_considerations: Optional[List[str]] = []


class BehaviorLearningRequest(BaseModel):
    """Request for behavior-based preference learning."""

    user_id: str
    interaction_patterns: List[Dict[str, Any]]
    time_spent_per_category: Dict[str, int]


class PreferenceQualityRequest(BaseModel):
    """Request for preference quality assessment."""

    user_id: str
    completed_categories: int = Field(..., ge=0)
    detailed_responses: int = Field(..., ge=0)
    consistency_score: float = Field(..., ge=0.0, le=1.0)
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    engagement_indicators: Dict[str, Any]


class CategoryValidationRequest(BaseModel):
    """Request for category selection validation."""

    user_id: str
    selected_categories: List[str]


class CategoryWeightingRequest(BaseModel):
    """Request for category weight configuration."""

    user_id: str
    category_weights: Dict[str, Dict[str, float]]
    normalization_method: str = Field("softmax", regex="^(softmax|linear)$")


class PersonalizedOnboardingRequest(BaseModel):
    """Request for personalized onboarding creation."""

    user_id: str
    demographic_info: Dict[str, Any]
    initial_signals: Dict[str, Any]


# Additional Response Schemas


class LocationPreferenceResponse(BaseModel):
    """Response for location preference setup."""

    user_id: str
    preferred_areas: List[Dict[str, Any]]
    preferred_areas_configured: bool = True
    travel_range_km: float
    travel_range_set: bool = True
    transportation_modes: List[str]
    transport_preferences_saved: bool = True
    location_personalization_ready: bool = True
    configured_at: str


class BudgetPreferenceResponse(BaseModel):
    """Response for budget preference configuration."""

    user_id: str
    budget_category: str
    budget_range_configured: bool = True
    per_place_budget: Dict[str, Any]
    total_course_budget: Dict[str, Any]
    price_filtering_enabled: bool = True
    budget_flexibility: str
    flexibility_level_set: bool = True
    budget_personalization_active: bool = True
    configured_at: str


class CompanionPreferenceResponse(BaseModel):
    """Response for companion preference setup."""

    user_id: str
    primary_companion_type: str
    companion_type_set: bool = True
    group_size_preference: str
    group_size_configured: bool = True
    social_comfort_level: str
    social_preferences_saved: bool = True
    special_needs: List[str]
    accessibility_configured: bool
    configured_at: str


class ActivityLevelResponse(BaseModel):
    """Response for activity level configuration."""

    user_id: str
    activity_intensity: str
    activity_level_configured: bool = True
    walking_tolerance: Dict[str, Any]
    walking_preferences_set: bool = True
    time_availability: Dict[str, Any]
    time_preferences_set: bool = True
    physical_considerations: List[str]
    accessibility_needs_configured: bool
    configured_at: str


class AdaptiveSurveyResponse(BaseModel):
    """Response for adaptive survey generation."""

    user_id: str
    adaptive_questions_generated: bool = True
    personalized_questions: List[Dict[str, Any]]
    adaptation_confidence: float
    personalization_improved: bool
    previous_answers_analyzed: int
    generated_at: str


class CategoryAvailabilityResponse(BaseModel):
    """Response for available categories."""

    available_categories: List[Dict[str, Any]]
    category_descriptions: Dict[str, str]
    total_available: int
    context_applied: Dict[str, str]


class CategoryValidationResponse(BaseModel):
    """Response for category validation."""

    user_id: str
    selected_categories: List[str]
    category_count: int
    validation_passed: bool
    validation_errors: List[str]
    validated_at: str


class CategoryWeightingResponse(BaseModel):
    """Response for category weighting."""

    user_id: str
    category_weights_set: bool = True
    original_weights: Dict[str, Dict[str, float]]
    normalized_weights: Dict[str, float]
    normalization_method: str
    weights_sum: float
    configured_at: str


class PersonalizedOnboardingResponse(BaseModel):
    """Response for personalized onboarding."""

    user_id: str
    personalized_flow_created: bool = True
    customized_questions: List[Dict[str, Any]]
    estimated_completion_time: Dict[str, Any]
    personalization_confidence: float
    signal_analysis: Dict[str, Any]
    created_at: str


class BehaviorLearningResponse(BaseModel):
    """Response for behavior-based learning."""

    user_id: str
    preferences_updated: bool = True
    behavior_insights: Dict[str, Any]
    updated_category_weights: Dict[str, float]
    learning_confidence: float
    recommendation_improvements: List[str]
    analyzed_at: str


class PreferenceQualityResponse(BaseModel):
    """Response for preference quality assessment."""

    user_id: str
    quality_score: float
    completeness_percentage: float
    quality_components: Dict[str, float]
    recommendation_readiness: Dict[str, Any]
    assessed_at: str
