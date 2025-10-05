"""
Redis Queue Service for notification scheduling.

Handles delayed notification scheduling using Redis as message queue.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from redis import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Service for managing notification queue with Redis."""

    def __init__(self) -> None:
        self.redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.queue_name = "hotly:notifications"
        self.scheduled_set = "hotly:scheduled_notifications"

    async def schedule(
        self, notification_id: str, payload: Dict[str, Any], delay_seconds: int
    ) -> bool:
        """
        Schedule a notification for delayed execution.

        Args:
            notification_id: Unique notification identifier
            payload: Notification data
            delay_seconds: Delay before execution

        Returns:
            True if successfully scheduled
        """
        try:
            # Calculate execution time
            execute_at = datetime.now().timestamp() + delay_seconds

            # Store notification data
            notification_data = {
                "id": notification_id,
                "payload": payload,
                "scheduled_for": execute_at,
                "created_at": datetime.now().isoformat(),
            }

            # Add to sorted set with execution time as score
            self.redis_client.zadd(
                self.scheduled_set, {json.dumps(notification_data): execute_at}
            )

            logger.info(
                f"Scheduled notification {notification_id} for execution in {delay_seconds} seconds"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to schedule notification {notification_id}: {e}")
            return False

    async def schedule_batch(self, batch_items: List[Dict[str, Any]]) -> bool:
        """
        Schedule multiple notifications in batch.

        Args:
            batch_items: List of items with notification_id, payload, delay_seconds

        Returns:
            True if batch was successfully scheduled
        """
        try:
            pipe = self.redis_client.pipeline()

            for item in batch_items:
                notification_id: str = item["notification_id"]
                payload: Dict[str, Any] = item["payload"]
                delay_seconds: int = int(item["delay_seconds"])

                execute_at = datetime.now().timestamp() + delay_seconds

                notification_data = {
                    "id": notification_id,
                    "payload": payload,
                    "scheduled_for": execute_at,
                    "created_at": datetime.now().isoformat(),
                }

                pipe.zadd(
                    self.scheduled_set, {json.dumps(notification_data): execute_at}
                )

            pipe.execute()

            logger.info(f"Scheduled batch of {len(batch_items)} notifications")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule notification batch: {e}")
            return False

    async def cancel(self, notification_id: str) -> bool:
        """
        Cancel a scheduled notification.

        Args:
            notification_id: ID of notification to cancel

        Returns:
            True if notification was found and cancelled
        """
        try:
            # Find and remove the notification from scheduled set
            all_scheduled = self.redis_client.zrange(self.scheduled_set, 0, -1)

            for item in all_scheduled:
                try:
                    notification_data = json.loads(item)
                    if notification_data.get("id") == notification_id:
                        # Remove from scheduled set
                        self.redis_client.zrem(self.scheduled_set, item)
                        logger.info(f"Cancelled notification {notification_id}")
                        return True
                except (json.JSONDecodeError, KeyError):
                    continue

            logger.warning(f"Notification {notification_id} not found for cancellation")
            return False

        except Exception as e:
            logger.error(f"Failed to cancel notification {notification_id}: {e}")
            return False

    async def get_ready_notifications(self) -> List[Dict[str, Any]]:
        """
        Get notifications that are ready for execution.

        Returns:
            List of notifications ready to be sent
        """
        try:
            current_time = datetime.now().timestamp()

            # Get notifications with score (execution time) <= current time
            ready_items = self.redis_client.zrangebyscore(
                self.scheduled_set, 0, current_time
            )

            notifications: List[Dict[str, Any]] = []
            pipe = self.redis_client.pipeline()

            for item in ready_items:
                try:
                    notification_data = json.loads(item)
                    notifications.append(notification_data)

                    # Mark for removal from scheduled set
                    pipe.zrem(self.scheduled_set, item)

                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse notification data: {item}")
                    pipe.zrem(self.scheduled_set, item)  # Remove corrupt data

            # Remove processed notifications
            pipe.execute()

            logger.info(f"Found {len(notifications)} ready notifications")
            return notifications

        except Exception as e:
            logger.error(f"Failed to get ready notifications: {e}")
            return []

    async def get_scheduled_count(self) -> int:
        """
        Get count of scheduled notifications.

        Returns:
            Number of scheduled notifications
        """
        try:
            return int(self.redis_client.zcard(self.scheduled_set))
        except Exception as e:
            logger.error(f"Failed to get scheduled count: {e}")
            return 0

    async def cleanup_expired(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired/stale notifications.

        Args:
            max_age_hours: Maximum age for notifications

        Returns:
            Number of cleaned up items
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

            # Remove items older than cutoff
            removed_count = int(
                self.redis_client.zremrangebyscore(
                    self.scheduled_set,
                    0,
                    cutoff_time
                    - 86400,  # Only remove very old items to avoid removing current ones
                )
            )

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} expired notifications")

            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup expired notifications: {e}")
            return 0
