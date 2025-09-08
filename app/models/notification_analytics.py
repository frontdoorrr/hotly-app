"""Notification analytics models for personalization and A/B testing."""

from datetime import datetime
from enum import Enum
from uuid import uuid4

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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class InteractionType(str, Enum):
    """Notification interaction types."""

    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    DISMISSED = "dismissed"
    SNOOZED = "snoozed"
    UNSUBSCRIBED = "unsubscribed"


class NotificationLog(Base):
    """Detailed log of sent notifications for analytics."""

    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Notification identification
    notification_id = Column(String, nullable=True, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )

    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False)
    category = Column(String(100), nullable=True)

    # Timing information
    scheduled_time = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)

    # Delivery details
    platform = Column(String(20), nullable=False)  # ios, android
    device_token = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    # Message content (for analysis)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    message_id = Column(String, nullable=True)  # FCM/APNS message ID

    # Personalization metadata
    personalization_version = Column(String(20), nullable=True)
    ab_test_group = Column(String(50), nullable=True)
    timing_optimization_used = Column(Boolean, default=False)
    content_personalization_used = Column(Boolean, default=False)

    # Analytics data
    delivery_time_seconds = Column(Float, nullable=True)  # Time from scheduled to sent

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    interactions = relationship(
        "NotificationInteraction", back_populates="notification_log"
    )
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<NotificationLog(id={self.id}, type={self.notification_type}, success={self.success})>"


class NotificationInteraction(Base):
    """User interactions with notifications for behavior analysis."""

    __tablename__ = "notification_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Reference
    notification_log_id = Column(
        UUID(as_uuid=True),
        ForeignKey("notification_logs.id"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )

    # Interaction details
    interaction_type = Column(String(20), nullable=False, index=True)
    interaction_data = Column(JSON, nullable=True)  # Additional interaction context

    # Timing
    timestamp = Column(DateTime, nullable=False, index=True)
    time_from_delivery = Column(
        Float, nullable=True
    )  # Seconds from delivery to interaction

    # Context information
    device_info = Column(JSON, nullable=True)
    app_version = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    notification_log = relationship("NotificationLog", back_populates="interactions")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<NotificationInteraction(id={self.id}, type={self.interaction_type})>"


class UserNotificationPattern(Base):
    """User-specific notification behavior patterns for personalization."""

    __tablename__ = "user_notification_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Engagement metrics
    total_notifications_received = Column(Integer, default=0, nullable=False)
    total_notifications_opened = Column(Integer, default=0, nullable=False)
    total_notifications_clicked = Column(Integer, default=0, nullable=False)
    total_notifications_dismissed = Column(Integer, default=0, nullable=False)

    # Calculated engagement rates
    open_rate = Column(Float, default=0.0, nullable=False)
    click_rate = Column(Float, default=0.0, nullable=False)
    engagement_rate = Column(Float, default=0.0, nullable=False)

    # Timing preferences (hours 0-23)
    preferred_hours = Column(JSON, nullable=True)  # {"hour": engagement_rate}
    most_active_hour = Column(Integer, nullable=True)
    least_active_hour = Column(Integer, nullable=True)

    # Day of week preferences (0=Monday, 6=Sunday)
    preferred_days = Column(JSON, nullable=True)  # {"day": engagement_rate}
    most_active_day = Column(Integer, nullable=True)

    # Response timing patterns
    avg_response_time_seconds = Column(Float, nullable=True)
    fastest_response_time_seconds = Column(Float, nullable=True)

    # Notification type preferences
    type_preferences = Column(
        JSON, nullable=True
    )  # {"type": {"sent": N, "engaged": N}}

    # Personalization effectiveness
    personalized_open_rate = Column(Float, nullable=True)
    non_personalized_open_rate = Column(Float, nullable=True)
    personalization_lift = Column(Float, nullable=True)  # % improvement

    # Last analysis
    last_analyzed_at = Column(DateTime, nullable=True)
    analysis_period_days = Column(Integer, default=30, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="notification_pattern")

    @property
    def overall_engagement_score(self) -> float:
        """Calculate overall engagement score (0-100)."""
        if self.total_notifications_received == 0:
            return 0.0

        # Weighted score: open (40%), click (50%), dismissal penalty (10%)
        open_score = (self.open_rate or 0.0) * 40
        click_score = (self.click_rate or 0.0) * 50
        dismissal_penalty = (
            self.total_notifications_dismissed / self.total_notifications_received
        ) * 10

        return max(0.0, min(100.0, open_score + click_score - dismissal_penalty))

    def get_optimal_send_hour(self) -> int:
        """Get the optimal hour to send notifications based on engagement."""
        if not self.preferred_hours or not isinstance(self.preferred_hours, dict):
            return 18  # Default to 6 PM

        # Find hour with highest engagement rate
        best_hour = max(
            self.preferred_hours.items(), key=lambda x: x[1], default=(18, 0.0)
        )

        return int(best_hour[0])

    def should_personalize_timing(self) -> bool:
        """Check if timing personalization is likely to be effective."""
        if not self.preferred_hours:
            return False

        # If there's significant variation in hourly engagement (>20% difference)
        rates = list(self.preferred_hours.values())
        if len(rates) < 3:
            return False

        return (max(rates) - min(rates)) > 0.2

    def __repr__(self) -> str:
        return f"<UserNotificationPattern(user_id={self.user_id}, engagement={self.overall_engagement_score:.1f}%)>"


class ABTestCohort(Base):
    """A/B testing cohorts for notification experiments."""

    __tablename__ = "ab_test_cohorts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Test identification
    test_name = Column(String(100), nullable=False, index=True)
    test_description = Column(Text, nullable=True)
    cohort_name = Column(
        String(50), nullable=False
    )  # control, variant_a, variant_b, etc.

    # Test configuration
    traffic_allocation = Column(Float, nullable=False)  # 0.0 to 1.0
    is_active = Column(Boolean, default=True, nullable=False)

    # Test parameters
    test_parameters = Column(JSON, nullable=False)  # Configuration being tested

    # Success metrics
    target_metric = Column(String(50), nullable=False)  # open_rate, click_rate, etc.
    significance_threshold = Column(Float, default=0.05, nullable=False)
    minimum_sample_size = Column(Integer, default=100, nullable=False)

    # Test period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)

    # Results tracking
    total_users = Column(Integer, default=0, nullable=False)
    total_notifications = Column(Integer, default=0, nullable=False)
    total_opens = Column(Integer, default=0, nullable=False)
    total_clicks = Column(Integer, default=0, nullable=False)

    # Statistical significance
    is_statistically_significant = Column(Boolean, nullable=True)
    p_value = Column(Float, nullable=True)
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    @property
    def current_open_rate(self) -> float:
        """Calculate current open rate for this cohort."""
        if self.total_notifications == 0:
            return 0.0
        return self.total_opens / self.total_notifications

    @property
    def current_click_rate(self) -> float:
        """Calculate current click rate for this cohort."""
        if self.total_notifications == 0:
            return 0.0
        return self.total_clicks / self.total_notifications

    @property
    def sample_size_reached(self) -> bool:
        """Check if minimum sample size has been reached."""
        return self.total_notifications >= self.minimum_sample_size

    def __repr__(self) -> str:
        return f"<ABTestCohort(test={self.test_name}, cohort={self.cohort_name})>"


class UserABTestAssignment(Base):
    """User assignments to A/B test cohorts."""

    __tablename__ = "user_ab_test_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Assignment details
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )
    cohort_id = Column(
        UUID(as_uuid=True), ForeignKey("ab_test_cohorts.id"), nullable=False, index=True
    )

    # Assignment metadata
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assignment_method = Column(
        String(50), nullable=False
    )  # random, criteria_based, etc.

    # User characteristics at assignment time
    user_segment = Column(String(50), nullable=True)
    user_engagement_score = Column(Float, nullable=True)

    # Experiment participation
    is_active = Column(Boolean, default=True, nullable=False)
    excluded_reason = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint
    __table_args__ = {"extend_existing": True}

    def __repr__(self) -> str:
        return f"<UserABTestAssignment(user_id={self.user_id}, cohort_id={self.cohort_id})>"
