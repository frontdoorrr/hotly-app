"""Notification models for push notification tracking."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

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
    PREPARATION_REMINDER = "preparation_reminder"
    DEPARTURE_REMINDER = "departure_reminder"
    MOVE_REMINDER = "move_reminder"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""

    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    """Notification model for tracking sent notifications."""

    __tablename__ = "notifications"  # type: ignore[assignment]

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
        total = int(self.success_count) + int(self.failure_count)
        return (float(self.success_count) / float(total)) if total > 0 else 0.0

    @property
    def is_scheduled(self) -> bool:
        """Check if notification is scheduled for future delivery."""
        return bool(
            self.status == NotificationStatus.SCHEDULED.value
            and self.scheduled_at is not None
            and self.scheduled_at > datetime.utcnow()
        )

    @property
    def is_delivered(self) -> bool:
        """Check if notification has been delivered."""
        return bool(self.status == NotificationStatus.SENT.value)

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

    __tablename__ = "notification_templates"  # type: ignore[assignment]

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

    __tablename__ = "user_notification_preferences"  # type: ignore[assignment]

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


class UserNotificationSettings(Base):
    """User notification settings model for personalized notifications."""

    __tablename__ = "user_notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True
    )

    # 전체 알림 설정
    enabled = Column(Boolean, default=True, nullable=False)

    # 조용 시간 설정
    quiet_hours_enabled = Column(Boolean, default=False, nullable=False)
    quiet_hours_start = Column(Time, nullable=True)  # 예: 22:00
    quiet_hours_end = Column(Time, nullable=True)  # 예: 08:00
    quiet_hours_weekdays_only = Column(Boolean, default=False, nullable=False)

    # 알림 타입별 설정
    date_reminder_enabled = Column(Boolean, default=True, nullable=False)
    departure_reminder_enabled = Column(Boolean, default=True, nullable=False)
    move_reminder_enabled = Column(Boolean, default=True, nullable=False)
    business_hours_enabled = Column(Boolean, default=True, nullable=False)
    weather_enabled = Column(Boolean, default=True, nullable=False)
    traffic_enabled = Column(Boolean, default=True, nullable=False)
    recommendations_enabled = Column(Boolean, default=True, nullable=False)
    promotional_enabled = Column(Boolean, default=False, nullable=False)

    # 알림 타이밍 설정
    day_before_hour = Column(Integer, default=18, nullable=False)  # 전날 몇 시에 알림
    departure_minutes_before = Column(Integer, default=30, nullable=False)  # 출발 몇 분 전
    move_reminder_minutes = Column(Integer, default=15, nullable=False)  # 이동 몇 분 전

    # 개인화 설정
    personalized_timing_enabled = Column(Boolean, default=True, nullable=False)
    frequency_limit_per_day = Column(Integer, default=10, nullable=False)
    frequency_limit_per_week = Column(Integer, default=50, nullable=False)

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 관계
    user = relationship("User", back_populates="notification_settings")

    def is_notification_allowed(
        self, notification_type: str, current_time: datetime = None
    ) -> bool:
        """주어진 알림 타입이 현재 시간에 허용되는지 확인."""
        if not self.enabled:
            return False

        current_time = current_time or datetime.now()

        # 조용 시간 체크
        if self.quiet_hours_enabled and self._is_quiet_time(current_time):
            return False

        # 타입별 설정 체크
        type_mapping = {
            NotificationType.PREPARATION_REMINDER: self.date_reminder_enabled,
            NotificationType.DEPARTURE_REMINDER: self.departure_reminder_enabled,
            NotificationType.MOVE_REMINDER: self.move_reminder_enabled,
            "business_hours": self.business_hours_enabled,
            "weather": self.weather_enabled,
            "traffic": self.traffic_enabled,
            "recommendations": self.recommendations_enabled,
            NotificationType.PROMOTIONAL: self.promotional_enabled,
        }

        return type_mapping.get(notification_type, True)

    def _is_quiet_time(self, current_time: datetime) -> bool:
        """조용 시간인지 확인."""
        if (
            not self.quiet_hours_enabled
            or not self.quiet_hours_start
            or not self.quiet_hours_end
        ):
            return False

        # 평일만 조용시간 적용하는 경우
        if (
            self.quiet_hours_weekdays_only and current_time.weekday() >= 5
        ):  # 토요일(5), 일요일(6)
            return False

        current_time_only = current_time.time()

        # 같은 날 시간대 (예: 22:00 - 23:59)
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= current_time_only <= self.quiet_hours_end

        # 다음날 넘어가는 시간대 (예: 22:00 - 08:00)
        return (
            current_time_only >= self.quiet_hours_start
            or current_time_only <= self.quiet_hours_end
        )
