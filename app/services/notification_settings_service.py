"""
Notification Settings Service

Handles CRUD operations for user notification preferences and settings.
Task 2-2-4: 알림 설정 UI 및 개인화 전송 기능
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.notification import UserNotificationSettings
from app.schemas.notification import (
    UserNotificationSettingsCreate,
    UserNotificationSettingsUpdate,
    UserNotificationSettingsResponse
)

logger = logging.getLogger(__name__)


class NotificationSettingsNotFoundError(Exception):
    """Raised when notification settings are not found for a user."""


class NotificationSettingsService:
    """Service for managing user notification settings."""

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    async def create_user_settings(
        self, 
        user_id: str, 
        settings_data: UserNotificationSettingsCreate
    ) -> UserNotificationSettings:
        """
        Create notification settings for a user.
        
        Args:
            user_id: User identifier
            settings_data: Notification settings data
            
        Returns:
            Created notification settings
            
        Raises:
            ValueError: If settings already exist for the user
        """
        logger.info(f"Creating notification settings for user {user_id}")
        
        # Check if settings already exist
        existing_settings = self.db.query(UserNotificationSettings).filter(
            UserNotificationSettings.user_id == user_id
        ).first()
        
        if existing_settings:
            raise ValueError(f"Notification settings already exists for user {user_id}")
        
        # Create new settings
        db_settings = UserNotificationSettings(
            user_id=user_id,
            enabled=settings_data.enabled,
            
            # Quiet hours
            quiet_hours_enabled=settings_data.quiet_hours.enabled,
            quiet_hours_start=settings_data.quiet_hours.start,
            quiet_hours_end=settings_data.quiet_hours.end,
            quiet_hours_weekdays_only=settings_data.quiet_hours.weekdays_only,
            
            # Notification types
            date_reminder_enabled=settings_data.types.date_reminder,
            departure_reminder_enabled=settings_data.types.departure_reminder,
            move_reminder_enabled=settings_data.types.move_reminder,
            business_hours_enabled=settings_data.types.business_hours,
            weather_enabled=settings_data.types.weather,
            traffic_enabled=settings_data.types.traffic,
            recommendations_enabled=settings_data.types.recommendations,
            promotional_enabled=settings_data.types.promotional,
            
            # Timing settings
            day_before_hour=settings_data.timing.day_before_hour,
            departure_minutes_before=settings_data.timing.departure_minutes_before,
            move_reminder_minutes=settings_data.timing.move_reminder_minutes,
            
            # Personalization settings
            personalized_timing_enabled=settings_data.personalization.enabled,
            frequency_limit_per_day=settings_data.personalization.frequency_limit_per_day,
            frequency_limit_per_week=settings_data.personalization.frequency_limit_per_week,
        )
        
        self.db.add(db_settings)
        self.db.commit()
        self.db.refresh(db_settings)
        
        logger.info(f"Created notification settings for user {user_id}")
        return db_settings

    async def get_user_settings(self, user_id: str) -> UserNotificationSettings:
        """
        Get notification settings for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            User notification settings
            
        Raises:
            NotificationSettingsNotFoundError: If settings don't exist
        """
        logger.debug(f"Getting notification settings for user {user_id}")
        
        settings = self.db.query(UserNotificationSettings).filter(
            UserNotificationSettings.user_id == user_id
        ).first()
        
        if not settings:
            raise NotificationSettingsNotFoundError(f"Notification settings not found for user {user_id}")
        
        return settings

    async def update_user_settings(
        self, 
        user_id: str, 
        update_data: UserNotificationSettingsUpdate
    ) -> UserNotificationSettings:
        """
        Update notification settings for a user.
        
        Args:
            user_id: User identifier
            update_data: Settings update data
            
        Returns:
            Updated notification settings
            
        Raises:
            NotificationSettingsNotFoundError: If settings don't exist
        """
        logger.info(f"Updating notification settings for user {user_id}")
        
        # Get existing settings
        settings = await self.get_user_settings(user_id)
        
        # Update fields that are provided
        if update_data.enabled is not None:
            settings.enabled = update_data.enabled
            
        if update_data.quiet_hours is not None:
            settings.quiet_hours_enabled = update_data.quiet_hours.enabled
            settings.quiet_hours_start = update_data.quiet_hours.start
            settings.quiet_hours_end = update_data.quiet_hours.end
            settings.quiet_hours_weekdays_only = update_data.quiet_hours.weekdays_only
            
        if update_data.types is not None:
            settings.date_reminder_enabled = update_data.types.date_reminder
            settings.departure_reminder_enabled = update_data.types.departure_reminder
            settings.move_reminder_enabled = update_data.types.move_reminder
            settings.business_hours_enabled = update_data.types.business_hours
            settings.weather_enabled = update_data.types.weather
            settings.traffic_enabled = update_data.types.traffic
            settings.recommendations_enabled = update_data.types.recommendations
            settings.promotional_enabled = update_data.types.promotional
            
        if update_data.timing is not None:
            settings.day_before_hour = update_data.timing.day_before_hour
            settings.departure_minutes_before = update_data.timing.departure_minutes_before
            settings.move_reminder_minutes = update_data.timing.move_reminder_minutes
            
        if update_data.personalization is not None:
            settings.personalized_timing_enabled = update_data.personalization.enabled
            settings.frequency_limit_per_day = update_data.personalization.frequency_limit_per_day
            settings.frequency_limit_per_week = update_data.personalization.frequency_limit_per_week
        
        # Update timestamp
        settings.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(settings)
        
        logger.info(f"Updated notification settings for user {user_id}")
        return settings

    async def delete_user_settings(self, user_id: str) -> bool:
        """
        Delete notification settings for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotificationSettingsNotFoundError: If settings don't exist
        """
        logger.info(f"Deleting notification settings for user {user_id}")
        
        # Get existing settings
        settings = await self.get_user_settings(user_id)
        
        self.db.delete(settings)
        self.db.commit()
        
        logger.info(f"Deleted notification settings for user {user_id}")
        return True

    async def get_or_create_default_settings(self, user_id: str) -> UserNotificationSettings:
        """
        Get user settings or create default settings if they don't exist.
        
        Args:
            user_id: User identifier
            
        Returns:
            User notification settings (existing or newly created)
        """
        try:
            return await self.get_user_settings(user_id)
        except NotificationSettingsNotFoundError:
            logger.info(f"Creating default notification settings for user {user_id}")
            
            # Create default settings
            from app.schemas.notification import (
                QuietHours, NotificationTypes, 
                NotificationTiming, PersonalizationSettings
            )
            
            default_settings = UserNotificationSettingsCreate(
                enabled=True,
                quiet_hours=QuietHours(
                    enabled=False,  # 기본적으로 조용시간 비활성화
                    start=None,
                    end=None,
                    weekdays_only=False
                ),
                types=NotificationTypes(),  # 모든 기본값 사용
                timing=NotificationTiming(),  # 모든 기본값 사용
                personalization=PersonalizationSettings()  # 모든 기본값 사용
            )
            
            return await self.create_user_settings(user_id, default_settings)

    def is_notification_allowed_for_user(
        self, 
        user_id: str, 
        notification_type: str, 
        current_time: datetime = None
    ) -> bool:
        """
        Check if a notification is allowed for a user at the current time.
        
        Args:
            user_id: User identifier
            notification_type: Type of notification
            current_time: Current time (defaults to now)
            
        Returns:
            True if notification is allowed
        """
        try:
            settings = self.db.query(UserNotificationSettings).filter(
                UserNotificationSettings.user_id == user_id
            ).first()
            
            if not settings:
                # If no settings exist, allow all notifications
                return True
                
            return settings.is_notification_allowed(notification_type, current_time)
            
        except Exception as e:
            logger.error(f"Error checking notification permission for user {user_id}: {e}")
            # In case of error, be permissive and allow the notification
            return True

    async def bulk_check_notification_permissions(
        self, 
        user_notification_pairs: list, 
        current_time: datetime = None
    ) -> dict:
        """
        Check notification permissions for multiple users efficiently.
        
        Args:
            user_notification_pairs: List of (user_id, notification_type) tuples
            current_time: Current time (defaults to now)
            
        Returns:
            Dictionary mapping (user_id, notification_type) -> bool
        """
        current_time = current_time or datetime.utcnow()
        
        # Get all unique user IDs
        user_ids = list(set(pair[0] for pair in user_notification_pairs))
        
        # Bulk fetch all user settings
        user_settings = self.db.query(UserNotificationSettings).filter(
            UserNotificationSettings.user_id.in_(user_ids)
        ).all()
        
        # Create lookup dictionary
        settings_lookup = {str(settings.user_id): settings for settings in user_settings}
        
        # Check permissions for each pair
        results = {}
        for user_id, notification_type in user_notification_pairs:
            settings = settings_lookup.get(user_id)
            if settings:
                allowed = settings.is_notification_allowed(notification_type, current_time)
            else:
                # No settings = allow all notifications
                allowed = True
                
            results[(user_id, notification_type)] = allowed
        
        return results


# Factory function for dependency injection
def get_notification_settings_service(db: Session = Depends(get_db)) -> NotificationSettingsService:
    """Get notification settings service instance."""
    return NotificationSettingsService(db)