"""API endpoints for notification management."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.notification import (
    DeviceTokenRequest,
    DeviceTokenResponse,
    NotificationResponse,
    NotificationStats,
    NotificationTemplateCreate,
    NotificationTemplateResponse,
    NotificationTemplateUpdate,
    PushNotificationRequest,
    PushNotificationResponse,
    TemplatedNotificationRequest,
    UserNotificationPreferenceResponse,
    UserNotificationPreferenceUpdate,
)
from app.services.fcm_service import FCMService, get_fcm_service
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)
from app.services.notification_template_service import (
    NotificationTemplateService,
    get_notification_template_service,
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
