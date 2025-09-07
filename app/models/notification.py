"""Notification models for push notification tracking."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base_class import Base


class NotificationStatus(str, Enum):
    """Notification status enumeration."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationType(str, Enum):
    """Notification type enumeration."""

    GENERAL = "general"
    ONBOARDING = "onboarding"
    PLACE_RECOMMENDATION = "place_recommendation"
    COURSE_RECOMMENDATION = "course_recommendation"
    SOCIAL_ACTIVITY = "social_activity"
    REMINDER = "reminder"
    PROMOTIONAL = "promotional"
    SYSTEM_UPDATE = "system_update"
    EMERGENCY = "emergency"


class Notification(Base):
    """Notification model for tracking sent notifications."""

    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Content
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    action_url = Column(String(500), nullable=True)

    # Classification
    notification_type = Column(
        String(50), nullable=False, default=NotificationType.GENERAL.value, index=True
    )
    category = Column(String(100), nullable=True, index=True)
    priority = Column(
        String(20), nullable=False, default="normal"
    )  # normal, high, urgent

    # Targeting
    target_user_ids = Column(ARRAY(String), nullable=False, default=list)
    target_segments = Column(ARRAY(String), nullable=True)  # user segments
    target_criteria = Column(JSON, nullable=True)  # advanced targeting criteria

    # Payload data
    data = Column(JSON, nullable=True, default=dict)

    # Delivery tracking
    status = Column(
        String(20), nullable=False, default=NotificationStatus.DRAFT.value, index=True
    )
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True, index=True)

    # Analytics
    delivery_attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)

    # Metadata
    created_by = Column(String, nullable=True)  # User who created the notification
    campaign_id = Column(
        String, nullable=True, index=True
    )  # For grouping related notifications

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type={self.notification_type}, status={self.status})>"

    @property
    def total_targeted(self) -> int:
        """Get total number of targeted users."""
        return len(self.target_user_ids)

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery success rate."""
        total = self.success_count + self.failure_count
        return (self.success_count / total) if total > 0 else 0.0

    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future delivery."""
        return (
            self.status == NotificationStatus.SCHEDULED.value
            and self.scheduled_at is not None
            and self.scheduled_at > datetime.utcnow()
        )

    @property
    def is_delivered(self) -> bool:
        """Check if notification has been delivered."""
        return self.status == NotificationStatus.SENT.value

    def mark_as_sending(self) -> None:
        """Mark notification as currently being sent."""
        self.status = NotificationStatus.SENDING.value
        self.delivery_attempts += 1
        self.last_attempt_at = datetime.utcnow()

    def mark_as_sent(self, success_count: int, failure_count: int) -> None:
        """Mark notification as sent with delivery results."""
        self.status = NotificationStatus.SENT.value
        self.success_count = success_count
        self.failure_count = failure_count
        self.sent_at = datetime.utcnow()

    def mark_as_failed(self, failure_count: int) -> None:
        """Mark notification as failed."""
        self.status = NotificationStatus.FAILED.value
        self.failure_count = failure_count
        self.sent_at = datetime.utcnow()


class NotificationTemplate(Base):
    """Notification template model for reusable notification content."""

    __tablename__ = "notification_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Template identification
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Template content
    title_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)

    # Configuration
    notification_type = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    priority = Column(String(20), nullable=False, default="normal")

    # Template variables
    required_variables = Column(ARRAY(String), nullable=False, default=list)
    optional_variables = Column(ARRAY(String), nullable=False, default=list)
    default_data = Column(JSON, nullable=True, default=dict)

    # Settings
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<NotificationTemplate(id={self.id}, name={self.name}, type={self.notification_type})>"

    def render_title(self, variables: Dict[str, Any]) -> str:
        """Render template title with provided variables."""
        try:
            return self.title_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable for title: {e}")

    def render_body(self, variables: Dict[str, Any]) -> str:
        """Render template body with provided variables."""
        try:
            return self.body_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable for body: {e}")

    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required variables are provided."""
        missing = []
        for required_var in self.required_variables:
            if required_var not in variables:
                missing.append(required_var)
        return missing


class UserNotificationPreference(Base):
    """User notification preference model."""

    __tablename__ = "user_notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, nullable=False, unique=True, index=True)

    # General preferences
    push_notifications_enabled = Column(Boolean, default=True, nullable=False)
    email_notifications_enabled = Column(Boolean, default=True, nullable=False)

    # Notification type preferences
    onboarding_notifications = Column(Boolean, default=True, nullable=False)
    place_recommendations = Column(Boolean, default=True, nullable=False)
    course_recommendations = Column(Boolean, default=True, nullable=False)
    social_activity_notifications = Column(Boolean, default=True, nullable=False)
    reminder_notifications = Column(Boolean, default=True, nullable=False)
    promotional_notifications = Column(Boolean, default=False, nullable=False)
    system_update_notifications = Column(Boolean, default=True, nullable=False)

    # Timing preferences
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(Integer, nullable=True)  # Hour of day (0-23)
    quiet_hours_end = Column(Integer, nullable=True)  # Hour of day (0-23)

    # Frequency limits
    max_daily_notifications = Column(Integer, default=10, nullable=False)
    max_weekly_notifications = Column(Integer, default=50, nullable=False)

    # Personalization
    preferred_language = Column(String(10), default="ko", nullable=False)
    timezone = Column(String(50), default="Asia/Seoul", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<UserNotificationPreference(user_id={self.user_id}, push_enabled={self.push_notifications_enabled})>"

    def is_notification_type_enabled(self, notification_type: str) -> bool:
        """Check if specific notification type is enabled for user."""
        type_mapping = {
            NotificationType.ONBOARDING.value: self.onboarding_notifications,
            NotificationType.PLACE_RECOMMENDATION.value: self.place_recommendations,
            NotificationType.COURSE_RECOMMENDATION.value: self.course_recommendations,
            NotificationType.SOCIAL_ACTIVITY.value: self.social_activity_notifications,
            NotificationType.REMINDER.value: self.reminder_notifications,
            NotificationType.PROMOTIONAL.value: self.promotional_notifications,
            NotificationType.SYSTEM_UPDATE.value: self.system_update_notifications,
        }

        return type_mapping.get(notification_type, True)

    def is_in_quiet_hours(self, current_hour: int) -> bool:
        """Check if current time is in user's quiet hours."""
        if (
            not self.quiet_hours_enabled
            or self.quiet_hours_start is None
            or self.quiet_hours_end is None
        ):
            return False

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        if start < end:
            # Normal range (e.g., 9-17)
            return start <= current_hour < end
        else:
            # Overnight range (e.g., 22-6)
            return current_hour >= start or current_hour < end
