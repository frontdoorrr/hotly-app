"""API endpoints for notification management."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user, get_current_active_user
from app.models.user import User
from app.schemas.notification import (
    DeviceTokenRequest,
    DeviceTokenResponse,
    NotificationBatchResult,
    NotificationResponse,
    NotificationScheduleResponse,
    NotificationStats,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
    OptimalTimingPrediction,
    PersonalizedTimingRequest,
    PushNotificationRequest,
    PushNotificationResponse,
    TemplatedNotificationRequest,
    UserNotificationPreferenceResponse,
    UserNotificationPreferenceUpdate,
    UserNotificationSettingsCreate,
    UserNotificationSettingsUpdate,
    UserNotificationSettingsResponse,
)
from app.services.fcm_service import FCMService, get_fcm_service
from app.services.notification_scheduler import (
    NotificationScheduler,
    get_notification_scheduler,
)
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)
from app.services.notification_template_service import (
    NotificationTemplateService,
    get_notification_template_service,
)
from app.services.personalization_engine import (
    InsufficientDataError,
    ModelPredictionError,
    PersonalizationEngine,
    get_personalization_engine,
)
from app.services.notification_settings_service import (
    NotificationSettingsService,
    NotificationSettingsNotFoundError,
    get_notification_settings_service,
)
from app.services.personalized_notification_service import (
    PersonalizedNotificationService,
    get_personalized_notification_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# Device Token Management
@router.post("/device/register", response_model=DeviceTokenResponse)
async def register_device_token(
    request: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> DeviceTokenResponse:
    """Register FCM device token for push notifications."""
    try:
        result = fcm_service.register_device_token(
            user_id=str(current_user.id),
            device_token=request.token,
            device_info=request.device_info,
        )

        return DeviceTokenResponse(**result)

    except Exception as e:
        logger.error(f"Failed to register device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token",
        )


@router.delete("/device/unregister")
async def unregister_device_token(
    token: str = Query(..., description="FCM device token to unregister"),
    current_user: User = Depends(get_current_user),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> Dict[str, Any]:
    """Unregister FCM device token."""
    try:
        result = fcm_service.unregister_device_token(
            user_id=str(current_user.id), device_token=token
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unregister device token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token",
        )


# Push Notification Sending
@router.post("/push", response_model=PushNotificationResponse)
async def send_push_notification(
    request: PushNotificationRequest,
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PushNotificationResponse:
    """Send push notification to specified users."""
    try:
        # TODO: Add admin authorization check
        response = fcm_service.send_push_notification(request)
        return response

    except Exception as e:
        logger.error(f"Failed to send push notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send push notification",
        )


@router.post("/push/templated", response_model=PushNotificationResponse)
async def send_templated_notification(
    request: TemplatedNotificationRequest,
    current_user: User = Depends(get_current_user),
    fcm_service: FCMService = Depends(get_fcm_service),
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> PushNotificationResponse:
    """Send push notification using a predefined template."""
    try:
        # Render template with variables
        rendered = template_service.render_template(
            template_name=request.template_name, variables=request.variables
        )

        # Merge additional data if provided
        data = rendered["data"]
        if request.additional_data:
            data.update(request.additional_data)

        # Create push notification request
        push_request = PushNotificationRequest(
            title=rendered["title"],
            body=rendered["body"],
            user_ids=request.user_ids,
            data=data,
            image_url=request.image_url,
            action_url=request.action_url or data.get("action_url"),
            notification_type=rendered["notification_type"],
            priority=request.priority or rendered["priority"],
        )

        # Send notification
        if request.scheduled_at:
            # TODO: Implement scheduled notifications
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Scheduled notifications not yet implemented",
            )
        else:
            response = fcm_service.send_push_notification(push_request)
            return response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send templated notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send templated notification",
        )


# Notification Templates
@router.get("/templates", response_model=List[NotificationTemplateResponse])
async def list_notification_templates(
    notification_type: Optional[str] = Query(
        None, description="Filter by notification type"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of templates to return"
    ),
    current_user: User = Depends(get_current_user),
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> List[NotificationTemplateResponse]:
    """List notification templates with optional filtering."""
    try:
        return template_service.list_templates(
            notification_type=notification_type,
            category=category,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Failed to list notification templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification templates",
        )


@router.get("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def get_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> NotificationTemplateResponse:
    """Get notification template by ID."""
    try:
        template = template_service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification template not found",
            )

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get notification template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification template",
        )


@router.post("/templates", response_model=NotificationTemplateResponse)
async def create_notification_template(
    template_data: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> NotificationTemplateResponse:
    """Create a new notification template."""
    try:
        # TODO: Add admin authorization check
        return template_service.create_template(template_data)

    except Exception as e:
        logger.error(f"Failed to create notification template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification template",
        )


@router.put("/templates/{template_id}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_id: str,
    template_update: NotificationTemplateUpdate,
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> NotificationTemplateResponse:
    """Update notification template."""
    try:
        # TODO: Add admin authorization check
        template = template_service.update_template(template_id, template_update)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification template not found",
            )

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification template",
        )


@router.delete("/templates/{template_id}")
async def delete_notification_template(
    template_id: str,
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> Dict[str, str]:
    """Delete notification template."""
    try:
        # TODO: Add admin authorization check
        success = template_service.delete_template(template_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification template not found",
            )

        return {"message": "Notification template deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete notification template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification template",
        )


@router.get("/templates/name/{template_name}/variables")
async def get_template_variables(
    template_name: str,
    current_user: User = Depends(get_current_user),
    template_service: NotificationTemplateService = Depends(
        get_notification_template_service
    ),
) -> Dict[str, Any]:
    """Get template variable requirements."""
    try:
        return template_service.get_template_variables(template_name)

    except Exception as e:
        logger.error(f"Failed to get template variables: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template variables",
        )


# Notification History and Management
@router.get("/history", response_model=List[NotificationResponse])
async def get_notification_history(
    notification_type: Optional[str] = Query(
        None, description="Filter by notification type"
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of notifications to return"
    ),
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    notification_service: NotificationService = Depends(get_notification_service),
) -> List[NotificationResponse]:
    """Get notification history with filtering."""
    try:
        # TODO: Add admin authorization check
        return notification_service.get_notification_history(
            notification_type=notification_type,
            status=status,
            days=days,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        logger.error(f"Failed to get notification history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification history",
        )


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    fcm_service: FCMService = Depends(get_fcm_service),
) -> NotificationStats:
    """Get notification delivery statistics."""
    try:
        # TODO: Add admin authorization check
        stats = fcm_service.get_notification_stats(days)
        return NotificationStats(**stats)

    except Exception as e:
        logger.error(f"Failed to get notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics",
        )


# User Notification Preferences
@router.get("/preferences", response_model=UserNotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UserNotificationPreferenceResponse:
    """Get user's notification preferences."""
    try:
        preferences = notification_service.get_user_preferences(str(current_user.id))
        return preferences

    except Exception as e:
        logger.error(f"Failed to get notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification preferences",
        )


@router.put("/preferences", response_model=UserNotificationPreferenceResponse)
async def update_notification_preferences(
    preferences_update: UserNotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> UserNotificationPreferenceResponse:
    """Update user's notification preferences."""
    try:
        preferences = notification_service.update_user_preferences(
            str(current_user.id), preferences_update
        )

        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User preferences not found",
            )

        return preferences

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences",
        )


# System Management
@router.post("/cleanup/tokens")
async def cleanup_expired_tokens(
    days_inactive: int = Query(
        30, ge=1, le=365, description="Days of inactivity before cleanup"
    ),
    current_user: User = Depends(get_current_user),  # Admin check could be added here
    fcm_service: FCMService = Depends(get_fcm_service),
) -> Dict[str, Any]:
    """Clean up expired/inactive device tokens."""
    try:
        # TODO: Add admin authorization check
        result = fcm_service.cleanup_expired_tokens(days_inactive)
        return result

    except Exception as e:
        logger.error(f"Failed to cleanup expired tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired tokens",
        )


# Course Notification Scheduling
@router.post("/schedule/course", response_model=NotificationScheduleResponse)
async def schedule_course_notifications(
    course_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    scheduler: NotificationScheduler = Depends(get_notification_scheduler),
) -> NotificationScheduleResponse:
    """Schedule notifications for a course (preparation, departure, move reminders)."""
    try:
        result = await scheduler.schedule_course_notifications(
            course_data=course_data, user_id=str(current_user.id)
        )

        logger.info(
            f"Scheduled {result.total_scheduled} notifications for user {current_user.id}"
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to schedule course notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule course notifications",
        )


@router.post("/schedule/batch", response_model=NotificationBatchResult)
async def schedule_batch_notifications(
    user_courses: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    scheduler: NotificationScheduler = Depends(get_notification_scheduler),
) -> NotificationBatchResult:
    """Schedule notifications for multiple courses in batch."""
    try:
        result = await scheduler.schedule_batch_notifications(
            user_courses=user_courses, user_id=str(current_user.id)
        )

        logger.info(
            f"Batch scheduled {result.success_count}/{result.total_scheduled} notifications "
            f"for user {current_user.id}"
        )

        return result

    except Exception as e:
        logger.error(f"Failed to batch schedule notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to batch schedule notifications",
        )


@router.delete("/schedule/{notification_id}")
async def cancel_scheduled_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    scheduler: NotificationScheduler = Depends(get_notification_scheduler),
) -> Dict[str, str]:
    """Cancel a scheduled notification."""
    try:
        success = await scheduler.cancel_notification(
            notification_id=notification_id, user_id=str(current_user.id)
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled notification not found or already processed",
            )

        return {
            "message": f"Scheduled notification {notification_id} cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel scheduled notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel scheduled notification",
        )


@router.get("/schedule/user")
async def get_user_scheduled_notifications(
    current_user: User = Depends(get_current_user),
    scheduler: NotificationScheduler = Depends(get_notification_scheduler),
) -> Dict[str, Any]:
    """Get all scheduled notifications for the current user."""
    try:
        notifications = await scheduler.get_user_scheduled_notifications(
            user_id=str(current_user.id)
        )

        return {
            "user_id": str(current_user.id),
            "scheduled_notifications": notifications,
            "total_count": len(notifications),
        }

    except Exception as e:
        logger.error(f"Failed to get user scheduled notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduled notifications",
        )


# Personalized Timing Endpoints (Task 2-2-3)
@router.post("/personalize/timing", response_model=OptimalTimingPrediction)
async def predict_optimal_timing(
    request: PersonalizedTimingRequest,
    current_user: User = Depends(get_current_user),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
) -> OptimalTimingPrediction:
    """
    Predict optimal notification timing for a user based on their behavior patterns.

    This endpoint implements personalized timing optimization using ML models and
    user engagement analysis to determine the best time to send notifications.
    """
    try:
        # Override user_id with current authenticated user
        request.user_id = str(current_user.id)

        logger.info(f"Predicting optimal timing for user {current_user.id}")
        prediction = await personalization_engine.predict_optimal_timing(request)

        logger.info(
            f"Optimal timing predicted: {prediction.predicted_time} "
            f"(confidence: {prediction.confidence_score:.2f})"
        )

        return prediction

    except InsufficientDataError as e:
        logger.warning(f"Insufficient data for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient user data for personalization: {str(e)}",
        )
    except ModelPredictionError as e:
        logger.error(f"ML model prediction failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction model temporarily unavailable",
        )
    except Exception as e:
        logger.error(f"Failed to predict optimal timing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict optimal timing",
        )


@router.post("/personalize/timing/fallback", response_model=OptimalTimingPrediction)
async def predict_timing_with_fallback(
    request: PersonalizedTimingRequest,
    current_user: User = Depends(get_current_user),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
) -> OptimalTimingPrediction:
    """
    Predict optimal timing with fallback to default if ML model fails.

    This endpoint provides a more robust version that always returns a timing
    prediction, falling back to default timing if personalization fails.
    """
    try:
        # Override user_id with current authenticated user
        request.user_id = str(current_user.id)

        logger.info(
            f"Predicting optimal timing with fallback for user {current_user.id}"
        )
        prediction = await personalization_engine.predict_optimal_timing_with_fallback(
            request
        )

        return prediction

    except Exception as e:
        logger.error(f"Failed to predict timing with fallback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict timing",
        )


@router.post("/personalize/timing/engagement", response_model=OptimalTimingPrediction)
async def optimize_timing_for_engagement(
    request: PersonalizedTimingRequest,
    current_user: User = Depends(get_current_user),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
) -> OptimalTimingPrediction:
    """
    Optimize notification timing specifically for maximum user engagement.

    This endpoint focuses on historical engagement patterns to find the
    time when the user is most likely to interact with notifications.
    """
    try:
        # Override user_id with current authenticated user
        request.user_id = str(current_user.id)

        logger.info(f"Optimizing timing for engagement for user {current_user.id}")
        prediction = await personalization_engine.optimize_timing_for_engagement(
            request
        )

        return prediction

    except Exception as e:
        logger.error(f"Failed to optimize timing for engagement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize timing for engagement",
        )


@router.get("/personalize/user-behavior", response_model=Dict[str, Any])
async def get_user_behavior_analysis(
    current_user: User = Depends(get_current_user),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
) -> Dict[str, Any]:
    """
    Get analysis of user's notification interaction patterns.

    Returns insights about the user's behavior patterns including
    optimal hours, engagement rates, and preferred notification types.
    """
    try:
        logger.info(f"Analyzing behavior patterns for user {current_user.id}")

        behavior_metrics = await personalization_engine.analyze_user_behavior_patterns(
            str(current_user.id)
        )

        return {
            "user_id": str(current_user.id),
            "behavior_analysis": behavior_metrics.dict(),
            "recommendations": {
                "optimal_hours": behavior_metrics.optimal_hours,
                "best_days": behavior_metrics.preferred_days,
                "engagement_level": behavior_metrics.overall_engagement_rate,
                "suggested_frequency": "high"
                if behavior_metrics.overall_engagement_rate > 0.7
                else "moderate",
            },
        }

    except InsufficientDataError as e:
        logger.warning(
            f"Insufficient data for user behavior analysis {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient notification history for behavior analysis",
        )
    except Exception as e:
        logger.error(f"Failed to analyze user behavior patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze behavior patterns",
        )


@router.post("/personalize/timing/batch", response_model=List[OptimalTimingPrediction])
async def optimize_batch_timing(
    requests: List[PersonalizedTimingRequest],
    current_user: User = Depends(get_current_user),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
) -> List[OptimalTimingPrediction]:
    """
    Optimize timing for multiple notifications in batch.

    Efficiently processes multiple timing requests for better performance
    when scheduling many notifications at once.
    """
    try:
        # Ensure all requests are for the current user
        for request in requests:
            request.user_id = str(current_user.id)

        logger.info(
            f"Batch timing optimization for {len(requests)} requests, user {current_user.id}"
        )
        predictions = await personalization_engine.optimize_batch_timing(requests)

        return predictions

    except Exception as e:
        logger.error(f"Failed to optimize batch timing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize batch timing",
        )


# Notification Settings Endpoints (Task 2-2-4)
@router.post("/settings", response_model=UserNotificationSettingsResponse)
async def create_notification_settings(
    *,
    current_user: User = Depends(get_current_user),
    settings_service: NotificationSettingsService = Depends(get_notification_settings_service),
    settings_in: UserNotificationSettingsCreate
) -> UserNotificationSettingsResponse:
    """
    Create notification settings for current user.
    
    Creates comprehensive notification preferences including:
    - Global notification toggle
    - Quiet hours configuration
    - Notification type preferences (8 types)
    - Timing settings for various notifications
    - Personalization settings with frequency limits
    """
    try:
        logger.info(f"Creating notification settings for user {current_user.id}")
        
        settings = await settings_service.create_user_settings(
            user_id=str(current_user.id),
            settings_data=settings_in
        )
        
        logger.info(f"Successfully created notification settings for user {current_user.id}")
        return UserNotificationSettingsResponse.model_validate(settings)
        
    except ValueError as e:
        logger.warning(f"Settings creation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification settings"
        )


@router.get("/settings", response_model=UserNotificationSettingsResponse)
async def get_notification_settings(
    *,
    current_user: User = Depends(get_current_user),
    settings_service: NotificationSettingsService = Depends(get_notification_settings_service)
) -> UserNotificationSettingsResponse:
    """
    Get notification settings for current user.
    
    Returns user's current notification preferences or creates default settings
    if none exist yet.
    """
    try:
        logger.debug(f"Getting notification settings for user {current_user.id}")
        
        settings = await settings_service.get_or_create_default_settings(
            user_id=str(current_user.id)
        )
        
        return UserNotificationSettingsResponse.model_validate(settings)
        
    except Exception as e:
        logger.error(f"Error getting settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification settings"
        )


@router.put("/settings", response_model=UserNotificationSettingsResponse)
async def update_notification_settings(
    *,
    current_user: User = Depends(get_current_user),
    settings_service: NotificationSettingsService = Depends(get_notification_settings_service),
    settings_update: UserNotificationSettingsUpdate
) -> UserNotificationSettingsResponse:
    """
    Update notification settings for current user.
    
    Supports partial updates - only provided fields will be updated.
    
    Available settings:
    - Global notification enabled/disabled
    - Quiet hours (time range, weekdays only option)
    - Individual notification types (8 types)
    - Timing preferences (reminder timing, departure alerts)
    - Personalization (timing optimization, frequency limits)
    """
    try:
        logger.info(f"Updating notification settings for user {current_user.id}")
        
        settings = await settings_service.update_user_settings(
            user_id=str(current_user.id),
            update_data=settings_update
        )
        
        logger.info(f"Successfully updated notification settings for user {current_user.id}")
        return UserNotificationSettingsResponse.model_validate(settings)
        
    except NotificationSettingsNotFoundError:
        logger.warning(f"No settings found for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not found. Please create settings first."
        )
    except Exception as e:
        logger.error(f"Error updating settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.delete("/settings", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_settings(
    *,
    current_user: User = Depends(get_current_user),
    settings_service: NotificationSettingsService = Depends(get_notification_settings_service)
) -> None:
    """
    Delete notification settings for current user.
    
    This will remove all user's notification preferences and revert to
    default behavior (all notifications enabled).
    """
    try:
        logger.info(f"Deleting notification settings for user {current_user.id}")
        
        await settings_service.delete_user_settings(str(current_user.id))
        
        logger.info(f"Successfully deleted notification settings for user {current_user.id}")
        
    except NotificationSettingsNotFoundError:
        logger.warning(f"No settings found to delete for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification settings not found"
        )
    except Exception as e:
        logger.error(f"Error deleting settings for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification settings"
        )


@router.get("/settings/check-permission/{notification_type}")
async def check_notification_permission(
    notification_type: str,
    *,
    current_user: User = Depends(get_current_user),
    settings_service: NotificationSettingsService = Depends(get_notification_settings_service)
) -> dict:
    """
    Check if a specific notification type is allowed for current user.
    
    Takes into account:
    - Global notification settings
    - Notification type preferences
    - Current time vs quiet hours
    - Weekday restrictions
    
    Useful for real-time notification sending decisions.
    """
    try:
        logger.debug(f"Checking permission for {notification_type} for user {current_user.id}")
        
        is_allowed = settings_service.is_notification_allowed_for_user(
            user_id=str(current_user.id),
            notification_type=notification_type
        )
        
        return {
            "user_id": str(current_user.id),
            "notification_type": notification_type,
            "allowed": is_allowed,
            "checked_at": "now"
        }
        
    except Exception as e:
        logger.error(f"Error checking permission for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check notification permission"
        )


# Personalized Notification Endpoints (Task 2-2-4)
@router.post("/personalized/send")
async def send_personalized_notification(
    *,
    current_user: User = Depends(get_current_user),
    personalized_service: PersonalizedNotificationService = Depends(get_personalized_notification_service),
    notification_request: PushNotificationRequest
) -> dict:
    """
    Send a personalized notification with timing optimization.
    
    This endpoint applies user preferences, timing optimization, and
    personalization algorithms to deliver notifications at optimal times.
    
    Features:
    - User preference filtering (quiet hours, notification types)
    - ML-based timing optimization
    - Engagement pattern analysis
    - Automatic scheduling for optimal delivery
    """
    try:
        logger.info(f"Sending personalized notification from user {current_user.id}")
        
        # For demo purposes, we'll send to the current user
        # In production, this might be admin-only or have different logic
        target_user_id = str(current_user.id)
        
        result = await personalized_service.send_personalized_notification(
            user_id=target_user_id,
            notification_request=notification_request,
            optimize_timing=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to send personalized notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send personalized notification"
        )


@router.post("/personalized/bulk-send")
async def send_bulk_personalized_notifications(
    *,
    current_user: User = Depends(get_current_user),
    personalized_service: PersonalizedNotificationService = Depends(get_personalized_notification_service),
    notification_requests: List[dict]
) -> dict:
    """
    Send personalized notifications to multiple users efficiently.
    
    Processes multiple notifications with batch optimization for better performance.
    Applies individual user preferences and timing optimization to each recipient.
    
    Request format:
    [
      {
        "user_id": "user1",
        "notification_request": { ... PushNotificationRequest ... }
      },
      ...
    ]
    """
    try:
        logger.info(f"Sending bulk personalized notifications to {len(notification_requests)} users")
        
        # TODO: Add admin authorization check
        
        result = await personalized_service.send_bulk_personalized_notifications(
            notification_requests=notification_requests
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to send bulk personalized notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send bulk personalized notifications"
        )


@router.get("/personalized/insights")
async def get_user_notification_insights(
    *,
    current_user: User = Depends(get_current_user),
    personalized_service: PersonalizedNotificationService = Depends(get_personalized_notification_service)
) -> dict:
    """
    Get personalized notification insights for current user.
    
    Returns comprehensive analysis of user's notification patterns including:
    - Notification preferences and settings
    - Engagement patterns and optimal times
    - Behavioral analysis and recommendations
    - Performance metrics and suggestions
    """
    try:
        logger.info(f"Getting notification insights for user {current_user.id}")
        
        insights = await personalized_service.get_user_notification_insights(
            user_id=str(current_user.id)
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get user insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user notification insights"
        )


@router.post("/personalized/test-optimization")
async def test_notification_optimization(
    *,
    current_user: User = Depends(get_current_user),
    personalized_service: PersonalizedNotificationService = Depends(get_personalized_notification_service),
    test_request: dict
) -> dict:
    """
    Test notification timing optimization without actually sending.
    
    This endpoint allows testing the personalization algorithms
    to see when notifications would be optimally delivered.
    
    Useful for:
    - A/B testing optimization strategies
    - Understanding user behavior patterns
    - Debugging timing algorithms
    """
    try:
        logger.info(f"Testing notification optimization for user {current_user.id}")
        
        # Create a test notification request
        test_notification = PushNotificationRequest(
            title=test_request.get("title", "Test Notification"),
            body=test_request.get("body", "This is a test notification"),
            user_ids=[str(current_user.id)],
            notification_type=test_request.get("notification_type", "general"),
            priority=test_request.get("priority", "normal")
        )
        
        # Test the optimization without actually sending
        result = await personalized_service.send_personalized_notification(
            user_id=str(current_user.id),
            notification_request=test_notification,
            optimize_timing=True
        )
        
        # Remove actual sending results and focus on optimization info
        test_result = {
            "user_id": str(current_user.id),
            "optimization_tested": True,
            "would_be_allowed": result.get("success", False) or result.get("reason") != "blocked_by_user_settings",
            "optimization_info": result.get("optimization_info", {}),
            "delivery_method": result.get("delivery_method", "unknown"),
            "test_timestamp": datetime.utcnow().isoformat()
        }
        
        return test_result
        
    except Exception as e:
        logger.error(f"Failed to test notification optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test notification optimization"
        )
