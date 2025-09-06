"""User behavior and preference models."""

import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func

from app.db.base_class import Base


class UserBehavior(Base):
    """User behavior tracking for preference learning."""

    __tablename__ = "user_behaviors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Behavior details
    action = Column(String(50), nullable=False)  # visit, save, share, rate, etc.
    place_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Interaction metrics
    duration_minutes = Column(Integer, nullable=True)  # Time spent
    rating = Column(Float, nullable=True)  # User rating if provided

    # Context information
    tags_added = Column(ARRAY(String), nullable=True)
    time_of_day = Column(
        String(20), nullable=True
    )  # morning, afternoon, evening, night
    day_of_week = Column(String(10), nullable=True)  # monday, tuesday, etc.

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    session_id = Column(String(100), nullable=True)  # For session tracking

    # Additional context
    device_type = Column(String(20), nullable=True)  # mobile, desktop, tablet
    referrer = Column(String(200), nullable=True)  # How they found the place


class UserBehaviorProfile(Base):
    """User preference profile learned from behavior."""

    __tablename__ = "user_behavior_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)

    # Preference dimensions (stored as JSON for flexibility)
    cuisine_preferences = Column(JSON, nullable=True)  # {"italian": 0.8, "korean": 0.6}
    ambiance_preferences = Column(
        JSON, nullable=True
    )  # {"quiet": 0.7, "romantic": 0.9}
    price_preferences = Column(JSON, nullable=True)  # {"budget": 0.3, "moderate": 0.7}
    location_preferences = Column(JSON, nullable=True)  # Geographic preferences
    time_preferences = Column(JSON, nullable=True)  # Temporal preferences

    # Learning metadata
    confidence_score = Column(Float, default=0.0, nullable=False)
    data_points_count = Column(Integer, default=0, nullable=False)
    last_learning_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UserFeedback(Base):
    """User feedback on recommendations for learning."""

    __tablename__ = "user_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Feedback target
    place_id = Column(UUID(as_uuid=True), nullable=True)
    recommendation_id = Column(UUID(as_uuid=True), nullable=True)
    course_id = Column(UUID(as_uuid=True), nullable=True)

    # Feedback content
    rating = Column(Float, nullable=False)  # 1-5 rating
    feedback_text = Column(String(1000), nullable=True)

    # Behavioral feedback
    visited = Column(Boolean, default=False)
    would_recommend = Column(Boolean, nullable=True)
    shared_with_others = Column(Boolean, default=False)

    # Context
    feedback_type = Column(String(50), nullable=False)  # place, recommendation, course
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserInteractionLog(Base):
    """Detailed interaction logging for analytics."""

    __tablename__ = "user_interaction_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Interaction details
    event_type = Column(String(50), nullable=False)  # click, view, search, etc.
    target_type = Column(String(50), nullable=False)  # place, recommendation, filter
    target_id = Column(String(100), nullable=True)

    # Context data
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible

    # Timing
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    duration_ms = Column(Integer, nullable=True)  # How long the interaction lasted

    # Additional metadata
    extra_data = Column(JSON, nullable=True)  # Flexible additional data


class PreferenceLearningMetrics(Base):
    """Metrics for preference learning system performance."""

    __tablename__ = "preference_learning_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Learning performance metrics
    prediction_accuracy = Column(Float, nullable=True)  # How accurate predictions were
    feedback_count = Column(Integer, default=0)
    positive_feedback_rate = Column(Float, nullable=True)

    # Model performance
    model_version = Column(String(50), nullable=True)
    training_data_count = Column(Integer, default=0)
    last_model_update = Column(DateTime(timezone=True), nullable=True)

    # Time tracking
    analysis_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
