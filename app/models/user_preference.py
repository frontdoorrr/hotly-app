"""User preference and onboarding models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class UserPreference(Base):
    """User preference settings and configuration."""

    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Category preferences
    categories = Column(JSON, nullable=False, default=list)
    category_weights = Column(JSON, nullable=False, default=dict)

    # Location preferences
    location_preferences = Column(JSON, nullable=True)
    max_travel_distance_km = Column(Integer, default=10)

    # Budget preferences
    budget_level = Column(String(20), nullable=False, default="medium")
    budget_ranges = Column(JSON, nullable=True)
    budget_flexibility = Column(String(20), default="medium")

    # Social preferences
    companion_type = Column(String(20), nullable=False, default="couple")
    group_size_preference = Column(Integer, default=2)
    social_comfort_level = Column(String(20), default="medium")

    # Activity preferences
    activity_intensity = Column(String(20), default="moderate")
    physical_limitations = Column(JSON, default=list)
    time_preferences = Column(JSON, nullable=True)

    # Quality and metadata
    quality_score = Column(Float, default=0.0)
    preferences_complete = Column(Boolean, default=False)
    last_survey_completed = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OnboardingSession(Base):
    """Onboarding session tracking."""

    __tablename__ = "onboarding_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Session status
    status = Column(String(20), nullable=False, default="not_started")
    current_step = Column(Integer, nullable=True)
    completed_steps = Column(JSON, default=list)

    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    step_data = Column(JSON, default=dict)

    # Session metadata
    device_info = Column(JSON, nullable=True)
    referral_source = Column(String(100), nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    abandoned_at = Column(DateTime, nullable=True)
    abandonment_reason = Column(String(100), nullable=True)


class PreferenceSurvey(Base):
    """Preference survey instances."""

    __tablename__ = "preference_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Survey configuration
    questions = Column(JSON, nullable=False)
    adaptive_enabled = Column(Boolean, default=True)
    estimated_time_seconds = Column(Integer, nullable=True)

    # Progress tracking
    current_question_index = Column(Integer, default=0)
    responses = Column(JSON, default=list)
    completion_time_seconds = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="active")  # active, completed, abandoned

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    survey_responses = relationship("PreferenceSurveyResponse", back_populates="survey")


class PreferenceSurveyResponse(Base):
    """Individual survey question responses."""

    __tablename__ = "preference_survey_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    survey_id = Column(
        UUID(as_uuid=True), ForeignKey("preference_surveys.id"), nullable=False
    )
    question_id = Column(String(100), nullable=False)

    # Response data
    response_value = Column(JSON, nullable=False)
    response_time_ms = Column(Integer, nullable=True)

    # Metadata
    question_order = Column(Integer, nullable=True)
    skipped = Column(Boolean, default=False)

    # Timestamps
    answered_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    survey = relationship("PreferenceSurvey", back_populates="survey_responses")


class PreferenceLearningSession(Base):
    """User preference learning and improvement sessions."""

    __tablename__ = "preference_learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Learning session data
    session_type = Column(String(50), nullable=False)  # feedback, behavior, survey
    learning_data = Column(JSON, nullable=False)

    # Preference updates
    previous_weights = Column(JSON, nullable=True)
    updated_weights = Column(JSON, nullable=True)
    improvement_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
