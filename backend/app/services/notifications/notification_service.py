"""Notification service for managing notifications and user preferences."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.notification import (
    Notification,
    NotificationStatus,
    UserNotificationPreference,
)
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    UserNotificationPreferenceResponse,
    UserNotificationPreferenceUpdate,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications and user preferences."""

    def __init__(self, db: Session):
        """Initialize notification service with database session."""
        self.db = db

    def create_notification(
        self, notification_data: NotificationCreate
    ) -> NotificationResponse:
        """Create a new notification record."""
        try:
            notification = Notification(
                title=notification_data.title,
                body=notification_data.body,
                image_url=notification_data.image_url,
                action_url=notification_data.action_url,
                notification_type=notification_data.notification_type,
                category=notification_data.category,
                priority=notification_data.priority,
                target_user_ids=notification_data.target_user_ids,
                target_segments=notification_data.target_segments,
                target_criteria=notification_data.target_criteria,
                data=notification_data.data or {},
                scheduled_at=notification_data.scheduled_at,
                campaign_id=notification_data.campaign_id,
                status=NotificationStatus.DRAFT.value,
            )

            self.db.add(notification)
            self.db.commit()
            self.db.refresh(notification)

            logger.info(f"Created notification: {notification.id}")

            return NotificationResponse.from_orm(notification)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create notification: {e}")
            raise

    def get_notification_history(
        self,
        notification_type: Optional[str] = None,
        status: Optional[str] = None,
        days: int = 7,
        skip: int = 0,
        limit: int = 50,
    ) -> List[NotificationResponse]:
        """Get notification history with filtering."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = self.db.query(Notification).filter(
                Notification.created_at >= start_date
            )

            if notification_type:
                query = query.filter(
                    Notification.notification_type == notification_type
                )

            if status:
                query = query.filter(Notification.status == status)

            notifications = (
                query.order_by(Notification.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )

            return [
                NotificationResponse.from_orm(notification)
                for notification in notifications
            ]

        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return []

    def get_user_preferences(self, user_id: str) -> UserNotificationPreferenceResponse:
        """Get user's notification preferences."""
        try:
            preferences = (
                self.db.query(UserNotificationPreference)
                .filter(UserNotificationPreference.user_id == user_id)
                .first()
            )

            if not preferences:
                # Create default preferences for user
                preferences = self._create_default_preferences(user_id)

            return UserNotificationPreferenceResponse.from_orm(preferences)

        except Exception as e:
            logger.error(f"Failed to get user preferences for {user_id}: {e}")
            raise

    def update_user_preferences(
        self, user_id: str, preferences_update: UserNotificationPreferenceUpdate
    ) -> Optional[UserNotificationPreferenceResponse]:
        """Update user's notification preferences."""
        try:
            preferences = (
                self.db.query(UserNotificationPreference)
                .filter(UserNotificationPreference.user_id == user_id)
                .first()
            )

            if not preferences:
                preferences = self._create_default_preferences(user_id)

            # Update preferences with provided data
            update_data = preferences_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preferences, field, value)

            preferences.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(preferences)

            logger.info(f"Updated notification preferences for user {user_id}")

            return UserNotificationPreferenceResponse.from_orm(preferences)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user preferences for {user_id}: {e}")
            return None

    def _create_default_preferences(self, user_id: str) -> UserNotificationPreference:
        """Create default notification preferences for user."""
        preferences = UserNotificationPreference(
            user_id=user_id,
            push_notifications_enabled=True,
            email_notifications_enabled=True,
            onboarding_notifications=True,
            place_recommendations=True,
            course_recommendations=True,
            social_activity_notifications=True,
            reminder_notifications=True,
            promotional_notifications=False,  # Opt-in for promotional
            system_update_notifications=True,
            quiet_hours_enabled=False,
            max_daily_notifications=10,
            max_weekly_notifications=50,
            preferred_language="ko",
            timezone="Asia/Seoul",
        )

        self.db.add(preferences)
        self.db.commit()
        self.db.refresh(preferences)

        logger.info(f"Created default preferences for user {user_id}")
        return preferences

    def can_send_notification(
        self, user_id: str, notification_type: str, current_hour: Optional[int] = None
    ) -> Dict[str, Any]:
        """Check if notification can be sent to user based on preferences."""
        try:
            preferences = (
                self.db.query(UserNotificationPreference)
                .filter(UserNotificationPreference.user_id == user_id)
                .first()
            )

            if not preferences:
                # No preferences means default allow
                return {"can_send": True, "reason": "default_allowed"}

            # Check if push notifications are enabled
            if not preferences.push_notifications_enabled:
                return {"can_send": False, "reason": "push_disabled"}

            # Check if specific notification type is enabled
            if not preferences.is_notification_type_enabled(notification_type):
                return {"can_send": False, "reason": "type_disabled"}

            # Check quiet hours
            if current_hour is not None:
                if preferences.is_in_quiet_hours(current_hour):
                    return {"can_send": False, "reason": "quiet_hours"}

            # Check daily notification limit
            today = datetime.utcnow().date()
            daily_count = (
                self.db.query(Notification)
                .filter(
                    Notification.target_user_ids.contains([user_id]),
                    Notification.sent_at
                    >= datetime.combine(today, datetime.min.time()),
                    Notification.status == NotificationStatus.SENT.value,
                )
                .count()
            )

            if daily_count >= preferences.max_daily_notifications:
                return {"can_send": False, "reason": "daily_limit_exceeded"}

            return {"can_send": True, "reason": "allowed"}

        except Exception as e:
            logger.error(f"Failed to check notification permission for {user_id}: {e}")
            return {"can_send": False, "reason": "error"}

    def get_notification_stats_by_user(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get notification statistics for specific user."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            notifications = (
                self.db.query(Notification)
                .filter(
                    Notification.target_user_ids.contains([user_id]),
                    Notification.sent_at >= start_date,
                )
                .all()
            )

            total_sent = len(notifications)
            by_type = {}
            by_status = {}

            for notification in notifications:
                # Group by type
                ntype = notification.notification_type
                if ntype not in by_type:
                    by_type[ntype] = 0
                by_type[ntype] += 1

                # Group by status
                status = notification.status
                if status not in by_status:
                    by_status[status] = 0
                by_status[status] += 1

            return {
                "user_id": user_id,
                "period_days": days,
                "total_notifications": total_sent,
                "by_type": by_type,
                "by_status": by_status,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get notification stats for user {user_id}: {e}")
            return {"error": str(e)}

    def mark_notification_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read by user."""
        try:
            # For now, we'll just log this
            # In a full implementation, we'd have a separate table for read status
            logger.info(f"User {user_id} marked notification {notification_id} as read")
            return True

        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False

    def schedule_notification(
        self, notification_data: NotificationCreate, scheduled_at: datetime
    ) -> NotificationResponse:
        """Schedule a notification for future delivery."""
        try:
            notification_data.scheduled_at = scheduled_at
            notification = self.create_notification(notification_data)

            # Update status to scheduled
            notification_record = (
                self.db.query(Notification)
                .filter(Notification.id == notification.id)
                .first()
            )

            if notification_record:
                notification_record.status = NotificationStatus.SCHEDULED.value
                self.db.commit()

            logger.info(f"Scheduled notification {notification.id} for {scheduled_at}")

            return notification

        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            raise

    def get_scheduled_notifications(
        self, due_before: Optional[datetime] = None
    ) -> List[NotificationResponse]:
        """Get scheduled notifications that are due for sending."""
        try:
            if due_before is None:
                due_before = datetime.utcnow()

            notifications = (
                self.db.query(Notification)
                .filter(
                    Notification.status == NotificationStatus.SCHEDULED.value,
                    Notification.scheduled_at <= due_before,
                )
                .all()
            )

            return [
                NotificationResponse.from_orm(notification)
                for notification in notifications
            ]

        except Exception as e:
            logger.error(f"Failed to get scheduled notifications: {e}")
            return []


# Factory function for dependency injection
def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """Get notification service instance."""
    return NotificationService(db)
