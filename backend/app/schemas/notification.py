"""Pydantic schemas for notification system."""

from datetime import datetime, time
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.notification import NotificationPriority, NotificationType


class DeviceTokenRequest(BaseModel):
    """Request model for device token registration."""

    token: str = Field(..., description="FCM device token")
    device_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Device information (platform, model, version, etc.)"
    )


class DeviceTokenResponse(BaseModel):
    """Response model for device token registration."""

    success: bool
    message: str
    device_id: Optional[str] = None
    is_new: bool = False


class PushNotificationRequest(BaseModel):
    """Request model for sending push notifications."""

    title: str = Field(..., max_length=255, description="Notification title")
    body: str = Field(..., description="Notification body")
    user_ids: List[str] = Field(..., description="Target user IDs")
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional data payload"
    )
    image_url: Optional[str] = Field(
        default=None, description="Image URL for rich notification"
    )
    action_url: Optional[str] = Field(
        default=None, description="Action URL when notification is tapped"
    )
    notification_type: str = Field(
        default="general", description="Type of notification"
    )
    priority: str = Field(
        default="normal", description="Notification priority (normal, high)"
    )
    time_to_live: Optional[int] = Field(
        default=None,
        ge=0,
        le=2419200,  # 4 weeks max
        description="Time to live in seconds",
    )

    @validator("priority")
    def validate_priority(cls, v):
        if v not in ["normal", "high"]:
            raise ValueError('Priority must be "normal" or "high"')
        return v


class PushNotificationResponse(BaseModel):
    """Response model for push notification sending."""

    success: bool
    message_id: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    failed_tokens: List[str] = []
    error: Optional[str] = None


class NotificationTemplateCreate(BaseModel):
    """Schema for creating notification templates."""

    name: str = Field(..., max_length=100, description="Template name (unique)")
    description: Optional[str] = Field(default=None, description="Template description")
    title_template: str = Field(
        ..., max_length=255, description="Title template with variables"
    )
    body_template: str = Field(..., description="Body template with variables")
    notification_type: str = Field(..., description="Type of notification")
    category: Optional[str] = Field(
        default=None, max_length=100, description="Notification category"
    )
    priority: str = Field(default="normal", description="Default priority")
    required_variables: List[str] = Field(
        default=[], description="Required template variables"
    )
    optional_variables: List[str] = Field(
        default=[], description="Optional template variables"
    )
    default_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Default data values"
    )
    is_active: bool = Field(default=True, description="Whether template is active")

    @validator("notification_type")
    def validate_notification_type(cls, v):
        valid_types = [t.value for t in NotificationType]
        if v not in valid_types:
            raise ValueError(f"notification_type must be one of: {valid_types}")
        return v

    @validator("priority")
    def validate_priority(cls, v):
        if v not in ["normal", "high", "urgent"]:
            raise ValueError('Priority must be "normal", "high", or "urgent"')
        return v


class NotificationTemplateUpdate(BaseModel):
    """Schema for updating notification templates."""

    description: Optional[str] = None
    title_template: Optional[str] = Field(None, max_length=255)
    body_template: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = None
    required_variables: Optional[List[str]] = None
    optional_variables: Optional[List[str]] = None
    default_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator("priority")
    def validate_priority(cls, v):
        if v is not None and v not in ["normal", "high", "urgent"]:
            raise ValueError('Priority must be "normal", "high", or "urgent"')
        return v


class NotificationTemplateResponse(BaseModel):
    """Response schema for notification templates."""

    id: UUID
    name: str
    description: Optional[str]
    title_template: str
    body_template: str
    notification_type: str
    category: Optional[str]
    priority: str
    required_variables: List[str]
    optional_variables: List[str]
    default_data: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplatedNotificationRequest(BaseModel):
    """Request model for sending templated notifications."""

    template_name: str = Field(..., description="Name of the notification template")
    user_ids: List[str] = Field(..., description="Target user IDs")
    variables: Dict[str, Any] = Field(default={}, description="Template variables")
    additional_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional data to merge with template data"
    )
    image_url: Optional[str] = Field(
        default=None, description="Override template image URL"
    )
    action_url: Optional[str] = Field(
        default=None, description="Override template action URL"
    )
    priority: Optional[str] = Field(
        default=None, description="Override template priority"
    )
    scheduled_at: Optional[datetime] = Field(
        default=None, description="Schedule notification for future"
    )


class NotificationCreate(BaseModel):
    """Schema for creating notifications."""

    title: str = Field(..., max_length=255)
    body: str
    image_url: Optional[str] = None
    action_url: Optional[str] = None
    notification_type: str = Field(default=NotificationType.GENERAL.value)
    category: Optional[str] = None
    priority: str = Field(default="normal")
    target_user_ids: List[str] = Field(default=[])
    target_segments: Optional[List[str]] = None
    target_criteria: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    campaign_id: Optional[str] = None


class NotificationResponse(BaseModel):
    """Response schema for notifications."""

    id: UUID
    title: str
    body: str
    image_url: Optional[str]
    action_url: Optional[str]
    notification_type: str
    category: Optional[str]
    priority: str
    target_user_ids: List[str]
    target_segments: Optional[List[str]]
    data: Dict[str, Any]
    status: str
    success_count: int
    failure_count: int
    delivery_rate: float
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    campaign_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    """Schema for notification statistics."""

    period_days: int
    total_notifications_sent: int
    total_success_count: int
    total_failure_count: int
    success_rate: float
    by_notification_type: Dict[str, Dict[str, int]]
    generated_at: str


class UserNotificationPreferenceUpdate(BaseModel):
    """Schema for updating user notification preferences."""

    push_notifications_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    onboarding_notifications: Optional[bool] = None
    place_recommendations: Optional[bool] = None
    course_recommendations: Optional[bool] = None
    social_activity_notifications: Optional[bool] = None
    reminder_notifications: Optional[bool] = None
    promotional_notifications: Optional[bool] = None
    system_update_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)
    max_daily_notifications: Optional[int] = Field(None, ge=0, le=100)
    max_weekly_notifications: Optional[int] = Field(None, ge=0, le=500)
    preferred_language: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)


class UserNotificationPreferenceResponse(BaseModel):
    """Response schema for user notification preferences."""

    id: UUID
    user_id: str
    push_notifications_enabled: bool
    email_notifications_enabled: bool
    onboarding_notifications: bool
    place_recommendations: bool
    course_recommendations: bool
    social_activity_notifications: bool
    reminder_notifications: bool
    promotional_notifications: bool
    system_update_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    max_daily_notifications: int
    max_weekly_notifications: int
    preferred_language: str
    timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceResponse(BaseModel):
    """Response schema for user devices."""

    id: UUID
    user_id: str
    device_info: Dict[str, Any]
    is_active: bool
    push_enabled: bool
    quiet_hours_start: Optional[int]
    quiet_hours_end: Optional[int]
    registered_at: datetime
    last_active: datetime
    device_platform: Optional[str] = None
    device_model: Optional[str] = None

    class Config:
        from_attributes = True


# Additional schemas for scheduling system
class QuietHours(BaseModel):
    """User's quiet hours configuration."""

    start: time
    end: time
    days_of_week: List[str] = ["monday", "tuesday", "wednesday", "thursday", "friday"]


class NotificationTiming(BaseModel):
    """User's notification timing preferences."""

    day_before_hour: int = 18
    departure_minutes_before: int = 30
    move_reminder_minutes: int = 15


class UserNotificationSettings(BaseModel):
    """User's complete notification settings."""

    enabled: bool = True
    quiet_hours: Optional[QuietHours] = None
    timing: Optional[NotificationTiming] = None


class ScheduledNotificationRequest(BaseModel):
    """Request to schedule a notification."""

    id: Optional[str] = None
    user_id: str
    course_id: Optional[str] = None
    type: NotificationType
    priority: NotificationPriority
    scheduled_time: datetime
    message: str
    deep_link: Optional[str] = None


class NotificationScheduleResponse(BaseModel):
    """Response from scheduling notifications."""

    scheduled_notifications: List[ScheduledNotificationRequest]
    total_scheduled: int
    skipped_count: int = 0


class NotificationBatchResult(BaseModel):
    """Result of batch notification processing."""

    total_scheduled: int
    success_count: int
    error_count: int
    errors: List[str] = []


# Personalization schemas for task 2-2-3
class UserBehaviorPattern(BaseModel):
    """User behavior pattern from notification interactions."""

    user_id: str
    timestamp: datetime
    notification_type: NotificationType
    sent_at: time
    opened_at: Optional[time] = None
    clicked: bool = False
    day_of_week: str
    engagement_score: float = 0.0


class EngagementMetrics(BaseModel):
    """User engagement metrics and patterns."""

    user_id: str
    total_notifications: int
    opened_count: int
    clicked_count: int
    open_rate: float
    click_rate: float
    average_open_delay_minutes: float
    peak_engagement_hours: List[int]
    preferred_days: List[str]
    last_updated: datetime
    optimal_hours: List[int] = []
    overall_engagement_rate: float = 0.0


class PersonalizedTimingRequest(BaseModel):
    """Request for personalized timing prediction."""

    user_id: str
    notification_type: NotificationType
    default_time: datetime
    course_context: Optional[Dict[str, Any]] = None
    real_time_context: Optional[Dict[str, Any]] = None
    user_constraints: Optional[Dict[str, Any]] = None


class OptimalTimingPrediction(BaseModel):
    """Prediction of optimal notification timing."""

    user_id: str
    predicted_time: datetime
    confidence_score: float
    engagement_probability: float
    alternative_times: List[datetime] = []
    reasoning: str = ""
    context_factors: Dict[str, Any] = {}
    fallback_used: bool = False
    constraint_applied: bool = False
    quiet_hours_adjusted: bool = False
    improvement_score: Optional[float] = None
    algorithm_used: Optional[str] = None
    ab_test_group: Optional[str] = None
    processing_time_ms: Optional[float] = None
    adaptation_reason: Optional[str] = None


class PersonalizedTimingResponse(BaseModel):
    """Response from personalized timing service."""

    user_id: str
    original_time: datetime
    optimized_time: datetime
    improvement_score: float
    confidence: float
    reasoning: str


class PersonalizedTimingBatchResult(BaseModel):
    """Result of batch personalized timing optimization."""

    total_processed: int
    success_count: int
    error_count: int
    average_improvement: float
    processing_time_ms: float


# User Notification Settings Schemas


class QuietHours(BaseModel):
    """Quiet hours configuration."""

    enabled: bool = False
    start: Optional[time] = Field(
        None, description="Start time for quiet hours (e.g., 22:00)"
    )
    end: Optional[time] = Field(
        None, description="End time for quiet hours (e.g., 08:00)"
    )
    weekdays_only: bool = Field(False, description="Apply quiet hours only on weekdays")

    @validator("end")
    def validate_end_time(cls, v, values):
        if v and "start" in values and values["start"] and v == values["start"]:
            raise ValueError("End time must be different from start time")
        return v


class NotificationTypes(BaseModel):
    """Notification type settings."""

    date_reminder: bool = Field(True, description="Enable date preparation reminders")
    departure_reminder: bool = Field(
        True, description="Enable departure time reminders"
    )
    move_reminder: bool = Field(
        True, description="Enable move between places reminders"
    )
    business_hours: bool = Field(
        True, description="Enable business hours change notifications"
    )
    weather: bool = Field(True, description="Enable weather update notifications")
    traffic: bool = Field(True, description="Enable traffic update notifications")
    recommendations: bool = Field(
        True, description="Enable place/course recommendations"
    )
    promotional: bool = Field(False, description="Enable promotional notifications")


class NotificationTiming(BaseModel):
    """Notification timing configuration."""

    day_before_hour: int = Field(
        18, ge=8, le=22, description="Hour to send day-before reminders"
    )
    departure_minutes_before: int = Field(
        30, ge=5, le=120, description="Minutes before departure"
    )
    move_reminder_minutes: int = Field(
        15, ge=5, le=60, description="Minutes before moving to next place"
    )


class PersonalizationSettings(BaseModel):
    """Personalization configuration."""

    enabled: bool = Field(True, description="Enable personalized timing optimization")
    frequency_limit_per_day: int = Field(
        10, ge=1, le=50, description="Max notifications per day"
    )
    frequency_limit_per_week: int = Field(
        50, ge=5, le=200, description="Max notifications per week"
    )


class UserNotificationSettingsBase(BaseModel):
    """Base user notification settings schema."""

    enabled: bool = Field(True, description="Enable all notifications")
    quiet_hours: QuietHours = QuietHours()
    types: NotificationTypes = NotificationTypes()
    timing: NotificationTiming = NotificationTiming()
    personalization: PersonalizationSettings = PersonalizationSettings()


class UserNotificationSettingsCreate(UserNotificationSettingsBase):
    """Create user notification settings request."""


class UserNotificationSettingsUpdate(BaseModel):
    """Update user notification settings request."""

    enabled: Optional[bool] = None
    quiet_hours: Optional[QuietHours] = None
    types: Optional[NotificationTypes] = None
    timing: Optional[NotificationTiming] = None
    personalization: Optional[PersonalizationSettings] = None


class UserNotificationSettingsResponse(UserNotificationSettingsBase):
    """User notification settings response."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Notification Template Schemas


class NotificationTemplateBase(BaseModel):
    """Base notification template schema."""

    name: str = Field(..., max_length=100, description="Template name")
    notification_type: str = Field(..., description="Notification type")
    priority: str = Field("normal", description="Default priority")
    title_template: str = Field(
        ..., max_length=200, description="Title template with variables"
    )
    body_template: str = Field(..., description="Body template with variables")
    category: Optional[str] = Field(
        None, max_length=50, description="Template category"
    )
    ios_settings: Optional[Dict[str, Any]] = Field(
        None, description="iOS-specific settings"
    )
    android_settings: Optional[Dict[str, Any]] = Field(
        None, description="Android-specific settings"
    )
    required_variables: Optional[List[str]] = Field(
        None, description="Required template variables"
    )
    optional_variables: Optional[List[str]] = Field(
        None, description="Optional template variables"
    )
