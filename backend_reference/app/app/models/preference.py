"""Database models for user preferences and onboarding."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserPreference(Base):
    """User preference profile model."""

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    preference_version = Column(String, default="v1.0")

    # Category preferences
    selected_categories = Column(JSON, nullable=False)  # List of selected categories
    category_weights = Column(JSON, nullable=True)  # Category weight mapping

    # Budget preferences
    budget_level = Column(String, nullable=False)  # low, medium, high
    budget_range_per_place = Column(
        JSON, nullable=True
    )  # {min_amount, max_amount, currency}
    budget_range_total = Column(JSON, nullable=True)  # Total course budget range
    budget_flexibility = Column(
        String, default="moderate"
    )  # strict, moderate, flexible

    # Location preferences
    preferred_areas = Column(JSON, nullable=True)  # List of preferred area objects
    travel_range_km = Column(Float, default=15.0)
    transportation_modes = Column(JSON, nullable=True)  # List of preferred transport

    # Activity preferences
    activity_intensity = Column(String, default="moderate")  # low, moderate, high
    walking_tolerance_km = Column(Float, default=2.0)
    typical_course_duration = Column(Integer, default=4)  # hours
    max_course_duration = Column(Integer, default=8)  # hours

    # Social preferences
    companion_type = Column(String, default="couple")  # solo, couple, friends, family
    group_size_preference = Column(
        String, default="couple"
    )  # solo, couple, small_group, large_group
    social_comfort_level = Column(
        String, default="moderate"
    )  # introverted, moderate, extroverted

    # Quality metrics
    quality_score = Column(Float, default=0.0)
    completeness_percentage = Column(Float, default=0.0)
    consistency_score = Column(Float, default=0.0)

    # Metadata
    setup_method = Column(String, default="survey")  # survey, behavior, import
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    survey_responses = relationship(
        "PreferenceSurveyResponse", back_populates="preference"
    )
    learning_sessions = relationship(
        "PreferenceLearningSession", back_populates="preference"
    )


class PreferenceSurveyResponse(Base):
    """Individual survey question responses."""

    __tablename__ = "preference_survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    preference_id = Column(Integer, ForeignKey("user_preferences.id"), nullable=False)
    user_id = Column(String, index=True, nullable=False)

    # Survey metadata
    survey_version = Column(String, nullable=False)
    question_id = Column(String, nullable=False)
    question_text = Column(Text, nullable=False)

    # Response data
    answer = Column(Text, nullable=False)
    confidence_level = Column(Float, default=0.5)  # 0.0-1.0
    response_time_seconds = Column(Integer, nullable=True)

    # Question metadata
    question_type = Column(String, nullable=False)  # category, budget, location, etc.
    is_mandatory = Column(Boolean, default=False)
    was_skipped = Column(Boolean, default=False)
    skip_reason = Column(String, nullable=True)

    # Timestamps
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    preference = relationship("UserPreference", back_populates="survey_responses")


class PreferenceLearningSession(Base):
    """Preference learning from user behavior."""

    __tablename__ = "preference_learning_sessions"

    id = Column(Integer, primary_key=True, index=True)
    preference_id = Column(Integer, ForeignKey("user_preferences.id"), nullable=False)
    user_id = Column(String, index=True, nullable=False)

    # Learning session metadata
    session_type = Column(
        String, nullable=False
    )  # behavior_analysis, feedback_learning
    learning_period = Column(String, nullable=False)  # 1_week, 1_month, etc.

    # Learning data
    behavior_data = Column(JSON, nullable=True)  # User interaction patterns
    preference_updates = Column(JSON, nullable=True)  # Updated preferences
    learning_confidence = Column(Float, default=0.0)  # Learning quality score

    # Quality metrics
    accuracy_improvement = Column(Float, default=0.0)  # Before vs after accuracy
    recommendation_quality_gain = Column(Float, default=0.0)

    # Metadata
    data_points_analyzed = Column(Integer, default=0)
    is_successful = Column(Boolean, default=False)

    # Timestamps
    session_started_at = Column(DateTime(timezone=True), server_default=func.now())
    session_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    preference = relationship("UserPreference", back_populates="learning_sessions")


class PreferenceCategory(Base):
    """Category definitions and metadata for preferences."""

    __tablename__ = "preference_categories"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(String, unique=True, index=True, nullable=False)

    # Category information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    keywords = Column(JSON, nullable=False)  # Associated keywords

    # Context relevance factors
    location_relevance = Column(JSON, nullable=True)  # Location-specific scores
    demographic_relevance = Column(JSON, nullable=True)  # Age/type-specific scores
    seasonal_relevance = Column(JSON, nullable=True)  # Season-specific scores

    # Usage statistics
    selection_count = Column(Integer, default=0)  # How many users selected this
    avg_satisfaction_score = Column(Float, default=0.0)

    # Configuration
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OnboardingPreferenceSession(Base):
    """Onboarding session tracking for preference setup."""

    __tablename__ = "onboarding_preference_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)

    # Session metadata
    session_id = Column(String, unique=True, index=True, nullable=False)
    onboarding_type = Column(String, nullable=False)  # quick, standard, comprehensive

    # Progress tracking
    total_steps = Column(Integer, default=5)
    completed_steps = Column(Integer, default=0)
    current_step = Column(Integer, default=1)
    progress_percentage = Column(Float, default=0.0)

    # Timing data
    estimated_completion_minutes = Column(Float, nullable=True)
    actual_completion_minutes = Column(Float, nullable=True)
    meets_time_target = Column(Boolean, nullable=True)  # 3-minute goal

    # Quality metrics
    preference_quality_score = Column(Float, default=0.0)
    profile_completeness = Column(Float, default=0.0)
    setup_effectiveness = Column(Float, default=0.0)

    # Session status
    status = Column(
        String, default="in_progress"
    )  # in_progress, completed, abandoned, expired
    abandonment_reason = Column(String, nullable=True)

    # Personalization data
    demographic_context = Column(JSON, nullable=True)
    initial_signals = Column(JSON, nullable=True)
    adaptation_applied = Column(Boolean, default=False)

    # Timestamps
    session_started_at = Column(DateTime(timezone=True), server_default=func.now())
    session_completed_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), onupdate=func.now())


class PreferenceValidation(Base):
    """Preference validation results and consistency checks."""

    __tablename__ = "preference_validations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    preference_id = Column(Integer, ForeignKey("user_preferences.id"), nullable=True)

    # Validation metadata
    validation_type = Column(
        String, nullable=False
    )  # consistency, completeness, quality
    validation_version = Column(String, default="v1.0")

    # Validation results
    is_valid = Column(Boolean, nullable=False)
    validation_score = Column(Float, default=0.0)  # 0.0-1.0

    # Validation details
    validation_errors = Column(JSON, nullable=True)  # List of validation errors
    validation_warnings = Column(JSON, nullable=True)  # List of warnings
    suggestions = Column(JSON, nullable=True)  # Improvement suggestions

    # Consistency metrics
    internal_consistency = Column(
        Float, nullable=True
    )  # Internal preference consistency
    behavioral_consistency = Column(
        Float, nullable=True
    )  # Behavior vs stated preferences

    # Timestamps
    validated_at = Column(DateTime(timezone=True), server_default=func.now())


class PreferenceRecommendationMapping(Base):
    """Mapping between preferences and recommendation configurations."""

    __tablename__ = "preference_recommendation_mappings"

    id = Column(Integer, primary_key=True, index=True)
    preference_id = Column(Integer, ForeignKey("user_preferences.id"), nullable=False)
    user_id = Column(String, index=True, nullable=False)

    # Recommendation configuration
    recommendation_config = Column(JSON, nullable=False)  # Recommendation engine config
    personalization_weights = Column(JSON, nullable=False)  # Personalization weights

    # Effectiveness metrics
    recommendation_accuracy = Column(Float, default=0.0)  # Measured accuracy
    user_satisfaction_score = Column(Float, default=0.0)  # User feedback score
    improvement_potential = Column(Float, default=0.0)  # Potential for improvement

    # Configuration status
    is_active = Column(Boolean, default=True)
    needs_refresh = Column(Boolean, default=False)
    last_effectiveness_check = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    mapped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
