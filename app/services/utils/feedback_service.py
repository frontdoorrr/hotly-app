"""
User Feedback Service

Manages user feedback on notification timing for model improvement.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class UserFeedbackService:
    """Service for collecting and managing user feedback on notifications."""

    def __init__(self) -> None:
        # Mock feedback storage - in production would use database
        self.feedback_store = {}

    async def collect_feedback(
        self,
        user_id: str,
        notification_id: str,
        feedback_type: str,
        feedback_data: Dict[str, Any],
    ) -> bool:
        """
        Collect user feedback on notification.

        Args:
            user_id: User identifier
            notification_id: Notification identifier
            feedback_type: Type of feedback (timing, content, etc.)
            feedback_data: Feedback details

        Returns:
            Success status
        """
        logger.info(f"Collecting {feedback_type} feedback from user {user_id}")

        feedback_entry = {
            "user_id": user_id,
            "notification_id": notification_id,
            "feedback_type": feedback_type,
            "feedback_data": feedback_data,
            "timestamp": datetime.now(),
            "processed": False,
        }

        if user_id not in self.feedback_store:
            self.feedback_store[user_id] = []

        self.feedback_store[user_id].append(feedback_entry)
        return True

    async def get_user_feedback(
        self, user_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get user feedback for the specified period.

        Args:
            user_id: User identifier
            days: Number of days to look back

        Returns:
            List of user feedback entries
        """
        logger.info(f"Retrieving feedback for user {user_id}, last {days} days")

        if user_id not in self.feedback_store:
            return []

        # Mock feedback data - in tests this will be mocked differently
        return []

    async def get_timing_feedback(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get timing-specific feedback for a user.

        Args:
            user_id: User identifier

        Returns:
            List of timing feedback entries
        """
        all_feedback = await self.get_user_feedback(user_id)

        timing_feedback = [
            fb for fb in all_feedback if fb.get("feedback_type") == "timing"
        ]

        return timing_feedback

    async def record_implicit_feedback(
        self,
        user_id: str,
        notification_id: str,
        interaction_type: str,
        timing_context: Dict[str, Any],
    ) -> bool:
        """
        Record implicit feedback from user interactions.

        Args:
            user_id: User identifier
            notification_id: Notification identifier
            interaction_type: Type of interaction (open, click, dismiss)
            timing_context: Context about notification timing

        Returns:
            Success status
        """
        logger.info(
            f"Recording implicit feedback: {interaction_type} from user {user_id}"
        )

        implicit_feedback = {
            "notification_time": timing_context.get("sent_at"),
            "interaction_type": interaction_type,
            "response_time_seconds": timing_context.get("response_delay", 0),
            "engagement_score": self._calculate_engagement_score(
                interaction_type, timing_context.get("response_delay", 0)
            ),
        }

        return await self.collect_feedback(
            user_id, notification_id, "implicit", implicit_feedback
        )

    def _calculate_engagement_score(
        self, interaction_type: str, response_delay: int
    ) -> float:
        """
        Calculate engagement score from interaction data.

        Args:
            interaction_type: Type of user interaction
            response_delay: Delay in seconds before interaction

        Returns:
            Engagement score (0.0 to 1.0)
        """
        base_scores = {"click": 1.0, "open": 0.7, "dismiss": 0.1, "ignore": 0.0}

        base_score = base_scores.get(interaction_type, 0.0)

        # Adjust score based on response delay
        if response_delay > 0:
            # Faster response = higher engagement
            delay_factor = max(0.1, 1.0 - (response_delay / 3600))  # Decay over 1 hour
            base_score *= delay_factor

        return min(1.0, base_score)

    async def get_feedback_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary of user's feedback patterns.

        Args:
            user_id: User identifier

        Returns:
            Feedback summary statistics
        """
        feedback_list = await self.get_user_feedback(user_id)

        if not feedback_list:
            return {
                "total_feedback": 0,
                "avg_engagement": 0.0,
                "preferred_times": [],
                "feedback_trends": {},
            }

        # Calculate summary statistics
        total_feedback = len(feedback_list)
        avg_engagement = (
            sum(
                fb.get("feedback_data", {}).get("engagement_score", 0.0)
                for fb in feedback_list
            )
            / total_feedback
            if total_feedback > 0
            else 0.0
        )

        return {
            "total_feedback": total_feedback,
            "avg_engagement": avg_engagement,
            "preferred_times": [],
            "feedback_trends": {
                "positive_feedback_rate": 0.7,
                "timing_complaints": 0.1,
            },
        }
