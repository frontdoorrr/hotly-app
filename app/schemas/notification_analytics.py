"""Schemas for notification analytics and personalization."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


# Base schemas
class NotificationLogBase(BaseModel):
    """Base schema for notification logs."""

    notification_id: Optional[str] = None
    notification_type: str
    priority: str
    category: Optional[str] = None
    platform: str  # ios, android
    device_token: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    personalization_version: Optional[str] = None
    ab_test_group: Optional[str] = None
    timing_optimization_used: bool = False
    content_personalization_used: bool = False


class NotificationLogCreate(NotificationLogBase):
    """Schema for creating notification logs."""

    user_id: UUID
    sent_at: datetime
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    message_id: Optional[str] = None
    delivery_time_seconds: Optional[float] = None


class NotificationLogResponse(NotificationLogBase):
    """Schema for notification log responses."""

    id: UUID
    user_id: UUID
    sent_at: datetime
    delivered_at: Optional[datetime]
    success: bool
    error_code: Optional[str]
    error_message: Optional[str]
    message_id: Optional[str]
    delivery_time_seconds: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Interaction schemas
class NotificationInteractionBase(BaseModel):
    """Base schema for notification interactions."""

    interaction_type: str
    interaction_data: Optional[Dict[str, Any]] = None
    device_info: Optional[Dict[str, Any]] = None
    app_version: Optional[str] = None


class NotificationInteractionCreate(NotificationInteractionBase):
    """Schema for creating notification interactions."""

    notification_log_id: UUID
    user_id: UUID
    timestamp: datetime
    time_from_delivery: Optional[float] = None


class NotificationInteractionResponse(NotificationInteractionBase):
    """Schema for notification interaction responses."""

    id: UUID
    notification_log_id: UUID
    user_id: UUID
    timestamp: datetime
    time_from_delivery: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# User pattern schemas
class UserNotificationPatternBase(BaseModel):
    """Base schema for user notification patterns."""

    total_notifications_received: int = 0
    total_notifications_opened: int = 0
    total_notifications_clicked: int = 0
    total_notifications_dismissed: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    engagement_rate: float = 0.0
    preferred_hours: Optional[Dict[str, float]] = None
    most_active_hour: Optional[int] = None
    least_active_hour: Optional[int] = None
    preferred_days: Optional[Dict[str, float]] = None
    most_active_day: Optional[int] = None
    avg_response_time_seconds: Optional[float] = None
    fastest_response_time_seconds: Optional[float] = None
    type_preferences: Optional[Dict[str, Dict[str, int]]] = None
    personalized_open_rate: Optional[float] = None
    non_personalized_open_rate: Optional[float] = None
    personalization_lift: Optional[float] = None
    analysis_period_days: int = 30


class UserNotificationPatternCreate(UserNotificationPatternBase):
    """Schema for creating user notification patterns."""

    user_id: UUID
    last_analyzed_at: Optional[datetime] = None


class UserNotificationPatternUpdate(BaseModel):
    """Schema for updating user notification patterns."""

    total_notifications_received: Optional[int] = None
    total_notifications_opened: Optional[int] = None
    total_notifications_clicked: Optional[int] = None
    total_notifications_dismissed: Optional[int] = None
    open_rate: Optional[float] = None
    click_rate: Optional[float] = None
    engagement_rate: Optional[float] = None
    preferred_hours: Optional[Dict[str, float]] = None
    most_active_hour: Optional[int] = None
    least_active_hour: Optional[int] = None
    preferred_days: Optional[Dict[str, float]] = None
    most_active_day: Optional[int] = None
    avg_response_time_seconds: Optional[float] = None
    fastest_response_time_seconds: Optional[float] = None
    type_preferences: Optional[Dict[str, Dict[str, int]]] = None
    personalized_open_rate: Optional[float] = None
    non_personalized_open_rate: Optional[float] = None
    personalization_lift: Optional[float] = None
    last_analyzed_at: Optional[datetime] = None
    analysis_period_days: Optional[int] = None


class UserNotificationPatternResponse(UserNotificationPatternBase):
    """Schema for user notification pattern responses."""

    id: UUID
    user_id: UUID
    last_analyzed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    overall_engagement_score: float
    optimal_send_hour: int
    should_personalize_timing: bool

    class Config:
        from_attributes = True


# A/B Testing schemas
class ABTestCohortBase(BaseModel):
    """Base schema for A/B test cohorts."""

    test_name: str = Field(..., min_length=1, max_length=100)
    test_description: Optional[str] = None
    cohort_name: str = Field(..., min_length=1, max_length=50)
    traffic_allocation: float = Field(..., ge=0.0, le=1.0)
    test_parameters: Dict[str, Any]
    target_metric: str = Field(..., min_length=1, max_length=50)
    significance_threshold: float = Field(0.05, ge=0.001, le=0.1)
    minimum_sample_size: int = Field(100, ge=10)
    start_date: datetime
    end_date: Optional[datetime] = None

    @validator("end_date")
    def end_date_after_start_date(cls, v, values):
        if v and "start_date" in values and v <= values["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v


class ABTestCohortCreate(ABTestCohortBase):
    """Schema for creating A/B test cohorts."""

    is_active: bool = True


class ABTestCohortUpdate(BaseModel):
    """Schema for updating A/B test cohorts."""

    test_description: Optional[str] = None
    traffic_allocation: Optional[float] = Field(None, ge=0.0, le=1.0)
    test_parameters: Optional[Dict[str, Any]] = None
    significance_threshold: Optional[float] = Field(None, ge=0.001, le=0.1)
    minimum_sample_size: Optional[int] = Field(None, ge=10)
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_statistically_significant: Optional[bool] = None
    p_value: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None


class ABTestCohortResponse(ABTestCohortBase):
    """Schema for A/B test cohort responses."""

    id: UUID
    is_active: bool
    total_users: int
    total_notifications: int
    total_opens: int
    total_clicks: int
    is_statistically_significant: Optional[bool]
    p_value: Optional[float]
    confidence_interval_lower: Optional[float]
    confidence_interval_upper: Optional[float]
    current_open_rate: float
    current_click_rate: float
    sample_size_reached: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserABTestAssignmentBase(BaseModel):
    """Base schema for user A/B test assignments."""

    assignment_method: str = Field(..., min_length=1, max_length=50)
    user_segment: Optional[str] = Field(None, max_length=50)
    user_engagement_score: Optional[float] = None
    is_active: bool = True
    excluded_reason: Optional[str] = None


class UserABTestAssignmentCreate(UserABTestAssignmentBase):
    """Schema for creating user A/B test assignments."""

    user_id: UUID
    cohort_id: UUID


class UserABTestAssignmentResponse(UserABTestAssignmentBase):
    """Schema for user A/B test assignment responses."""

    id: UUID
    user_id: UUID
    cohort_id: UUID
    assigned_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics response schemas
class NotificationAnalyticsReport(BaseModel):
    """Comprehensive notification analytics report."""

    period_start: datetime
    period_end: datetime
    total_notifications_sent: int
    total_notifications_delivered: int
    total_notifications_opened: int
    total_notifications_clicked: int
    overall_delivery_rate: float
    overall_open_rate: float
    overall_click_rate: float
    avg_delivery_time_seconds: float

    # Breakdown by type
    type_breakdown: Dict[str, Dict[str, Any]]

    # Breakdown by platform
    platform_breakdown: Dict[str, Dict[str, Any]]

    # Hourly patterns
    hourly_performance: Dict[str, float]

    # A/B test performance
    ab_test_performance: List[Dict[str, Any]]

    # Personalization effectiveness
    personalization_lift: Optional[float] = None
    personalized_performance: Optional[Dict[str, float]] = None

    generated_at: datetime


class PersonalizationInsights(BaseModel):
    """Insights for notification personalization optimization."""

    user_id: UUID
    overall_engagement_score: float
    optimal_send_times: List[int]  # Hours
    preferred_notification_types: List[str]
    response_time_pattern: Dict[str, float]
    personalization_recommendations: List[str]
    should_use_timing_optimization: bool
    should_use_content_personalization: bool
    estimated_improvement: Optional[float] = None  # Expected % improvement

    class Config:
        from_attributes = True


class ABTestResults(BaseModel):
    """A/B test statistical results."""

    test_name: str
    control_cohort: Dict[str, Any]
    variant_cohorts: List[Dict[str, Any]]
    winner: Optional[str] = None
    statistical_significance: bool
    p_value: float
    effect_size: float
    confidence_interval: Dict[str, float]
    recommendation: str
    test_duration_days: int

    class Config:
        from_attributes = True
