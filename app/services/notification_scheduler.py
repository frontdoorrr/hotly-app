"""
Notification Scheduler Service

Handles scheduling and targeting of notifications based on user preferences,
course data, and real-time context. Follows TDD principles from rules.md.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from app.schemas.notification import (
    NotificationBatchResult,
    NotificationScheduleResponse,
    QuietHours,
    ScheduledNotificationRequest,
    UserNotificationSettings,
)
from app.services.duplicate_detector import NotificationDuplicateDetector
from app.services.redis_queue import RedisQueueService
from app.services.travel_time_calculator import TravelTimeCalculator
from app.services.user_engagement_analyzer import UserEngagementAnalyzer
from app.services.user_preference_service import UserPreferencesService

logger = logging.getLogger(__name__)


class ScheduleConflictError(Exception):
    """Raised when there's a conflict in notification scheduling."""


class InvalidScheduleTimeError(Exception):
    """Raised when attempting to schedule notification for invalid time."""


class NotificationScheduler:
    """
    Service for scheduling and managing notification delivery.

    Handles:
    - Course-based notification scheduling
    - User preference-based targeting
    - Quiet hours and frequency limits
    - Batch processing and optimization
    """

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.redis_queue = RedisQueueService()
        self.travel_time_calculator = TravelTimeCalculator()
        self.user_engagement_analyzer = UserEngagementAnalyzer()
        self.duplicate_detector = NotificationDuplicateDetector()
        self.user_preferences_service = UserPreferencesService()

    async def schedule_course_notifications(
        self, course_data: Dict[str, Any], user_id: str
    ) -> NotificationScheduleResponse:
        """
        Schedule all notifications for a course.

        Args:
            course_data: Course information with places and timing
            user_id: User identifier

        Returns:
            Schedule response with created notifications
        """
        logger.info(
            f"Scheduling course notifications for user {user_id}, course {course_data.get('course_id')}"
        )

        # Get user notification preferences
        user_settings = await self.user_preferences_service.get_settings(user_id)

        if not user_settings or not user_settings.enabled:
            logger.info(f"Notifications disabled for user {user_id}")
            return NotificationScheduleResponse(
                scheduled_notifications=[], total_scheduled=0, skipped_count=0
            )

        notifications = []

        try:
            # 1. Preparation reminder (day before)
            if user_settings.timing and user_settings.timing.day_before_hour:
                prep_notification = await self._create_preparation_notification(
                    course_data, user_settings
                )
                notifications.append(prep_notification)

            # 2. Departure reminder
            if user_settings.timing and user_settings.timing.departure_minutes_before:
                departure_notification = await self._create_departure_notification(
                    course_data, user_settings
                )
                notifications.append(departure_notification)

            # 3. Move reminders between places
            if (
                user_settings.timing
                and user_settings.timing.move_reminder_minutes
                and len(course_data.get("places", [])) > 1
            ):
                move_notification = await self._create_move_notification(
                    course_data, user_settings
                )
                notifications.append(move_notification)

            # Schedule all notifications
            scheduled_count = 0
            for notification in notifications:
                try:
                    await self._schedule_single_notification(notification)
                    scheduled_count += 1
                except (ScheduleConflictError, InvalidScheduleTimeError) as e:
                    logger.warning(f"Failed to schedule notification: {e}")

            logger.info(
                f"Successfully scheduled {scheduled_count} notifications for course"
            )

            return NotificationScheduleResponse(
                scheduled_notifications=notifications,
                total_scheduled=scheduled_count,
                skipped_count=len(notifications) - scheduled_count,
            )

        except Exception as e:
            logger.error(f"Failed to schedule course notifications: {e}")
            raise

    async def _create_preparation_notification(
        self, course_data: Dict[str, Any], settings: UserNotificationSettings
    ) -> ScheduledNotificationRequest:
        """Create preparation reminder notification for day before course."""

        course_date = course_data["scheduled_date"]

        # Schedule for day before at specified hour
        scheduled_time = course_date.replace(
            hour=settings.timing.day_before_hour, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)

        notification = ScheduledNotificationRequest(
            id=str(uuid4()),
            user_id=course_data["user_id"],
            course_id=course_data["course_id"],
            type=NotificationType.PREPARATION_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=scheduled_time,
            message=await self._generate_preparation_message(course_data),
            deep_link=f"hotly://course/{course_data['course_id']}",
        )

        # Adjust for quiet hours
        adjusted_time = await self._adjust_for_quiet_hours(notification, settings)
        notification.scheduled_time = adjusted_time

        return notification

    async def _create_departure_notification(
        self, course_data: Dict[str, Any], settings: UserNotificationSettings
    ) -> ScheduledNotificationRequest:
        """Create departure reminder notification."""

        places = course_data.get("places", [])
        if not places:
            raise ValueError(
                "Course must have at least one place for departure notification"
            )

        first_place = places[0]
        arrival_time = course_data["scheduled_date"].replace(
            hour=first_place["arrival_time"].hour,
            minute=first_place["arrival_time"].minute,
            second=0,
            microsecond=0,
        )

        # Calculate travel time to first place
        travel_time_minutes = await self.travel_time_calculator.calculate(
            destination_place_id=first_place["id"], arrival_time=arrival_time
        )

        # Calculate departure time and notification time
        departure_time = arrival_time - timedelta(minutes=travel_time_minutes)
        notification_time = departure_time - timedelta(
            minutes=settings.timing.departure_minutes_before
        )

        notification = ScheduledNotificationRequest(
            id=str(uuid4()),
            user_id=course_data["user_id"],
            course_id=course_data["course_id"],
            type=NotificationType.DEPARTURE_REMINDER,
            priority=NotificationPriority.HIGH,
            scheduled_time=notification_time,
            message=await self._generate_departure_message(
                course_data, travel_time_minutes
            ),
            deep_link=f"hotly://navigation/{first_place['id']}",
        )

        # Important notifications can be sent during quiet hours with delay
        if settings.quiet_hours and self._is_in_quiet_hours(
            notification_time, settings.quiet_hours
        ):
            if notification.priority != NotificationPriority.URGENT:
                # Delay by 1 hour but don't move to next day for important notifications
                notification.scheduled_time = notification_time + timedelta(hours=1)

        return notification

    async def _create_move_notification(
        self, course_data: Dict[str, Any], settings: UserNotificationSettings
    ) -> ScheduledNotificationRequest:
        """Create move reminder notification between places."""

        places = course_data.get("places", [])
        if len(places) < 2:
            return None

        # Create notification for moving from first to second place
        first_place = places[0]
        second_place = places[1]

        # Calculate when to leave first place
        leave_time = course_data["scheduled_date"].replace(
            hour=second_place["arrival_time"].hour,
            minute=second_place["arrival_time"].minute,
        ) - timedelta(
            minutes=30
        )  # Assume 30min travel between places

        notification_time = leave_time - timedelta(
            minutes=settings.timing.move_reminder_minutes
        )

        notification = ScheduledNotificationRequest(
            id=str(uuid4()),
            user_id=course_data["user_id"],
            course_id=course_data["course_id"],
            type=NotificationType.MOVE_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=notification_time,
            message=await self._generate_move_message(first_place, second_place),
            deep_link=f"hotly://navigation/{second_place['id']}",
        )

        # Adjust for quiet hours
        adjusted_time = await self._adjust_for_quiet_hours(notification, settings)
        notification.scheduled_time = adjusted_time

        return notification

    async def _adjust_for_quiet_hours(
        self,
        notification: ScheduledNotificationRequest,
        settings: UserNotificationSettings,
    ) -> datetime:
        """
        Adjust notification time if it falls within quiet hours.

        Args:
            notification: The notification to adjust
            settings: User notification settings

        Returns:
            Adjusted datetime for notification
        """
        if not settings.quiet_hours:
            return notification.scheduled_time

        # Urgent notifications bypass quiet hours
        if notification.priority == NotificationPriority.URGENT:
            return notification.scheduled_time

        scheduled_time = notification.scheduled_time
        quiet_hours = settings.quiet_hours

        if self._is_in_quiet_hours(scheduled_time, quiet_hours):
            # Move to next active time (end of quiet hours)
            next_active = scheduled_time.replace(
                hour=quiet_hours.end.hour,
                minute=quiet_hours.end.minute,
                second=0,
                microsecond=0,
            )

            # If quiet hours end is earlier in the day, it's next day
            if quiet_hours.end <= scheduled_time.time():
                next_active += timedelta(days=1)

            return next_active

        return scheduled_time

    def _is_in_quiet_hours(self, dt: datetime, quiet_hours: QuietHours) -> bool:
        """Check if datetime falls within quiet hours."""
        if not quiet_hours:
            return False

        current_time = dt.time()
        start_time = quiet_hours.start
        end_time = quiet_hours.end

        # Check if current day is in quiet hours days
        weekday_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        current_weekday = weekday_names[dt.weekday()]

        if current_weekday not in quiet_hours.days_of_week:
            return False

        # Handle quiet hours that span midnight
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:
            return current_time >= start_time or current_time <= end_time

    async def schedule_single_notification(
        self, notification: ScheduledNotificationRequest
    ) -> Dict[str, Any]:
        """
        Schedule a single notification.

        Args:
            notification: Notification to schedule

        Returns:
            Result of scheduling operation
        """
        return await self._schedule_single_notification(notification)

    async def _schedule_single_notification(
        self, notification: ScheduledNotificationRequest
    ) -> Dict[str, Any]:
        """Internal method to schedule single notification with validation."""

        # Validate schedule time
        if notification.scheduled_time <= datetime.now():
            raise InvalidScheduleTimeError("Cannot schedule notification for past time")

        # Check for duplicates
        if await self.duplicate_detector.is_duplicate(notification):
            raise ScheduleConflictError("Duplicate notification detected")

        # Check frequency limits
        if notification.priority != NotificationPriority.URGENT:
            weekly_count = (
                await self.user_engagement_analyzer.get_weekly_notification_count(
                    notification.user_id
                )
            )
            frequency_limit = await self.user_engagement_analyzer.get_frequency_limit(
                notification.user_id
            )

            if weekly_count >= frequency_limit:
                raise ScheduleConflictError("User weekly frequency limit exceeded")

        # Schedule in Redis queue
        delay_seconds = (notification.scheduled_time - datetime.now()).total_seconds()

        await self.redis_queue.schedule(
            notification_id=notification.id,
            payload=notification.dict(),
            delay_seconds=int(delay_seconds),
        )

        # Save to database for tracking
        db_notification = Notification(
            title=notification.message,
            body=notification.message,
            notification_type=notification.type.value,
            priority=notification.priority.value,
            target_user_ids=[notification.user_id],
            scheduled_at=notification.scheduled_time,
            status=NotificationStatus.SCHEDULED.value,
            data={
                "course_id": notification.course_id,
                "deep_link": notification.deep_link,
                "user_id": notification.user_id,
                "notification_id": notification.id,
            },
        )

        self.db.add(db_notification)
        self.db.commit()

        logger.info(
            f"Scheduled notification {notification.id} for {notification.scheduled_time}"
        )

        return {
            "success": True,
            "notification_id": notification.id,
            "scheduled_time": notification.scheduled_time,
        }

    async def schedule_batch_notifications(
        self, notifications: List[ScheduledNotificationRequest]
    ) -> NotificationBatchResult:
        """
        Schedule multiple notifications efficiently.

        Args:
            notifications: List of notifications to schedule

        Returns:
            Batch processing result
        """
        success_count = 0
        error_count = 0
        errors = []

        # Process in batches for efficiency
        batch_size = 50

        for i in range(0, len(notifications), batch_size):
            batch = notifications[i : i + batch_size]

            # Prepare batch data for Redis
            batch_items = []
            for notification in batch:
                try:
                    # Basic validation
                    if notification.scheduled_time <= datetime.now():
                        error_count += 1
                        errors.append(
                            f"Invalid time for notification {notification.id}"
                        )
                        continue

                    delay_seconds = (
                        notification.scheduled_time - datetime.now()
                    ).total_seconds()
                    batch_items.append(
                        {
                            "notification_id": notification.id,
                            "payload": notification.dict(),
                            "delay_seconds": int(delay_seconds),
                        }
                    )

                    # Save to database
                    db_notification = Notification(
                        id=notification.id,
                        user_id=notification.user_id,
                        course_id=notification.course_id,
                        type=notification.type,
                        priority=notification.priority,
                        scheduled_time=notification.scheduled_time,
                        message=notification.message,
                        status=NotificationStatus.SCHEDULED,
                    )
                    self.db.add(db_notification)
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    errors.append(
                        f"Error processing notification {notification.id}: {e}"
                    )

            # Schedule batch in Redis
            if batch_items:
                await self.redis_queue.schedule_batch(batch_items)

        self.db.commit()

        return NotificationBatchResult(
            total_scheduled=len(notifications),
            success_count=success_count,
            error_count=error_count,
            errors=errors,
        )

    async def cancel_notification(self, notification_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled notification.

        Args:
            notification_id: ID of notification to cancel

        Returns:
            Cancellation result
        """
        try:
            # Cancel from Redis queue
            cancelled = await self.redis_queue.cancel(notification_id)

            if cancelled:
                # Update database status
                notification = (
                    self.db.query(Notification)
                    .filter(Notification.id == notification_id)
                    .first()
                )

                if notification:
                    notification.status = NotificationStatus.CANCELLED
                    self.db.commit()

                logger.info(f"Successfully cancelled notification {notification_id}")
                return {"success": True, "message": "Notification cancelled"}
            else:
                return {"success": False, "message": "Notification not found in queue"}

        except Exception as e:
            logger.error(f"Failed to cancel notification {notification_id}: {e}")
            return {"success": False, "message": str(e)}

    async def _generate_preparation_message(self, course_data: Dict[str, Any]) -> str:
        """Generate preparation reminder message."""
        places = course_data.get("places", [])
        if not places:
            return "내일 데이트를 준비하세요!"

        first_place = places[0]
        return f"내일 {first_place['name']} 데이트 준비! 📍 미리 체크해보세요."

    async def _generate_departure_message(
        self, course_data: Dict[str, Any], travel_time: int
    ) -> str:
        """Generate departure reminder message."""
        places = course_data.get("places", [])
        if not places:
            return "출발 시간입니다! 🚇"

        first_place = places[0]
        return f"🚇 {travel_time}분 후 {first_place['name']} 도착 예정! 지금 출발하세요."

    async def _generate_move_message(
        self, from_place: Dict[str, Any], to_place: Dict[str, Any]
    ) -> str:
        """Generate move reminder message."""
        return f"📍 {from_place['name']}에서 {to_place['name']}으로 이동할 시간입니다!"


class UserTargetingService:
    """
    Service for user targeting and personalization logic.

    Handles:
    - Personalized timing optimization
    - Engagement-based frequency adjustment
    - Contextual notification filtering
    """

    def __init__(self):
        self.engagement_analyzer = UserEngagementAnalyzer()
        self.user_context_service = None  # Will be injected

    async def optimize_notification_timing(
        self, user_id: str, default_time: datetime, notification_type: NotificationType
    ) -> datetime:
        """
        Optimize notification timing based on user engagement patterns.

        Args:
            user_id: User identifier
            default_time: Default scheduled time
            notification_type: Type of notification

        Returns:
            Optimized datetime for notification
        """
        try:
            # Get user's optimal hour based on historical engagement
            optimal_hour = await self.engagement_analyzer.get_optimal_hour(user_id)

            if optimal_hour is not None:
                # Adjust only the hour, keep other components
                optimized_time = default_time.replace(
                    hour=optimal_hour, minute=0, second=0, microsecond=0
                )
                return optimized_time

            return default_time

        except Exception as e:
            logger.warning(f"Failed to optimize timing for user {user_id}: {e}")
            return default_time

    async def get_personalized_frequency_limit(self, user_id: str) -> int:
        """
        Get personalized notification frequency limit based on user engagement.

        Args:
            user_id: User identifier

        Returns:
            Maximum notifications per week for this user
        """
        try:
            engagement_rate = await self.engagement_analyzer.calculate_engagement_rate(
                user_id
            )

            # Adjust frequency based on engagement level
            if engagement_rate >= 0.7:
                return 10  # High engagement: more notifications
            elif engagement_rate >= 0.4:
                return 7  # Medium engagement: standard limit
            else:
                return 3  # Low engagement: minimal notifications

        except Exception as e:
            logger.warning(
                f"Failed to calculate personalized limit for user {user_id}: {e}"
            )
            return 7  # Default limit

    async def should_send_notification(
        self, notification: ScheduledNotificationRequest
    ) -> bool:
        """
        Determine if notification should be sent based on user context.

        Args:
            notification: Notification to evaluate

        Returns:
            True if notification should be sent
        """
        try:
            # Always send urgent notifications
            if notification.priority == NotificationPriority.URGENT:
                return True

            # Check if user is currently active (if context service available)
            if self.user_context_service:
                is_active = await self.user_context_service.is_user_active(
                    notification.user_id
                )
                if not is_active:
                    # User is not active, lower chance of engagement
                    pass

            # Predict engagement probability
            engagement_probability = (
                await self.engagement_analyzer.predict_engagement_probability(
                    notification.user_id, notification
                )
            )

            # Send if probability is above threshold
            return engagement_probability >= 0.3  # 30% threshold

        except Exception as e:
            logger.error(f"Error evaluating notification send decision: {e}")
            return True  # Default to sending if error occurs


# Factory function for dependency injection
def get_notification_scheduler(db: Session = Depends(get_db)) -> NotificationScheduler:
    """Get notification scheduler instance."""
    return NotificationScheduler(db)
