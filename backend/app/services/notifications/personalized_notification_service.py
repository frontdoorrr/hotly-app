"""
Personalized Notification Service
Task 2-2-4: 알림 설정 UI 및 개인화 전송 기능 - 개인화 전송 부분

Handles personalized notification delivery with timing optimization
based on user preferences and behavioral patterns.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.notification import PersonalizedTimingRequest, PushNotificationRequest
from app.services.ml.personalization_engine import (
    PersonalizationEngine,
    get_personalization_engine,
)
from app.services.notifications.fcm_service import FCMService, get_fcm_service
from app.services.notifications.notification_settings_service import (
    NotificationSettingsService,
    get_notification_settings_service,
)

logger = logging.getLogger(__name__)


class PersonalizedNotificationService:
    """Service for sending personalized notifications with timing optimization."""

    def __init__(
        self,
        db: Session = Depends(get_db),
        settings_service: NotificationSettingsService = Depends(
            get_notification_settings_service
        ),
        personalization_engine: PersonalizationEngine = Depends(
            get_personalization_engine
        ),
        fcm_service: FCMService = Depends(get_fcm_service),
    ):
        self.db = db
        self.settings_service = settings_service
        self.personalization_engine = personalization_engine
        self.fcm_service = fcm_service

    async def send_personalized_notification(
        self,
        user_id: str,
        notification_request: PushNotificationRequest,
        optimize_timing: bool = True,
    ) -> Dict[str, Any]:
        """
        Send a personalized notification to a user with timing optimization.

        Args:
            user_id: Target user ID
            notification_request: Notification content and settings
            optimize_timing: Whether to optimize delivery timing

        Returns:
            Dictionary with sending results and optimization info
        """
        logger.info(f"Sending personalized notification to user {user_id}")

        try:
            # 1. Check user notification permissions
            is_allowed = self.settings_service.is_notification_allowed_for_user(
                user_id=user_id,
                notification_type=notification_request.notification_type,
                current_time=datetime.utcnow(),
            )

            if not is_allowed:
                logger.info(f"Notification blocked by user settings for user {user_id}")
                return {
                    "success": False,
                    "reason": "blocked_by_user_settings",
                    "message": "Notification blocked by user preferences or quiet hours",
                    "user_id": user_id,
                    "notification_type": notification_request.notification_type,
                }

            # 2. Optimize timing if requested
            optimized_time = None
            optimization_info = {}

            if optimize_timing:
                try:
                    timing_request = PersonalizedTimingRequest(
                        user_id=user_id,
                        notification_type=notification_request.notification_type,
                        default_time=datetime.utcnow(),
                        real_time_context={
                            "urgency_level": notification_request.priority,
                            "content_type": notification_request.notification_type,
                        },
                    )

                    prediction = await self.personalization_engine.predict_optimal_timing_with_fallback(
                        timing_request
                    )

                    optimized_time = prediction.predicted_time
                    optimization_info = {
                        "original_time": datetime.utcnow().isoformat(),
                        "optimized_time": optimized_time.isoformat(),
                        "confidence": prediction.confidence_score,
                        "improvement_score": prediction.improvement_score,
                        "reasoning": prediction.reasoning,
                    }

                    logger.info(
                        f"Timing optimized for user {user_id}: {optimization_info}"
                    )

                except Exception as e:
                    logger.warning(
                        f"Timing optimization failed for user {user_id}: {e}"
                    )
                    optimized_time = datetime.utcnow()
                    optimization_info = {"optimization_failed": True, "error": str(e)}

            # 3. Check if we should send immediately or schedule
            current_time = datetime.utcnow()
            send_immediately = (
                not optimize_timing
                or optimized_time is None
                or optimized_time
                <= current_time + timedelta(minutes=5)  # Send if within 5 minutes
            )

            if send_immediately:
                # Send notification immediately
                # Update the user_ids to include only this user
                notification_request.user_ids = [user_id]

                response = self.fcm_service.send_push_notification(notification_request)

                return {
                    "success": response.success,
                    "message_id": response.message_id,
                    "delivery_method": "immediate",
                    "sent_at": current_time.isoformat(),
                    "optimization_info": optimization_info,
                    "fcm_response": {
                        "success_count": response.success_count,
                        "failure_count": response.failure_count,
                        "failed_tokens": response.failed_tokens,
                    },
                }
            else:
                # Schedule for later (this would integrate with a job scheduler in production)
                logger.info(
                    f"Scheduling notification for user {user_id} at {optimized_time}"
                )

                return {
                    "success": True,
                    "delivery_method": "scheduled",
                    "scheduled_for": optimized_time.isoformat(),
                    "optimization_info": optimization_info,
                    "message": "Notification scheduled for optimal timing",
                }

        except Exception as e:
            logger.error(
                f"Failed to send personalized notification to user {user_id}: {e}"
            )
            return {"success": False, "error": str(e), "user_id": user_id}

    async def send_bulk_personalized_notifications(
        self, notification_requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Send personalized notifications to multiple users efficiently.

        Args:
            notification_requests: List of dicts with user_id and notification_request

        Returns:
            Bulk sending results with per-user optimization info
        """
        logger.info(
            f"Sending bulk personalized notifications to {len(notification_requests)} users"
        )

        results = {
            "total_users": len(notification_requests),
            "immediate_sends": [],
            "scheduled_sends": [],
            "blocked_sends": [],
            "failed_sends": [],
            "optimization_stats": {
                "optimized_count": 0,
                "fallback_count": 0,
                "blocked_count": 0,
            },
        }

        # 1. Check permissions for all users first
        user_permissions = {}
        for request in notification_requests:
            user_id = request["user_id"]
            notification_req = request["notification_request"]

            is_allowed = self.settings_service.is_notification_allowed_for_user(
                user_id=user_id, notification_type=notification_req.notification_type
            )

            user_permissions[user_id] = is_allowed

            if not is_allowed:
                results["blocked_sends"].append(
                    {"user_id": user_id, "reason": "blocked_by_user_settings"}
                )
                results["optimization_stats"]["blocked_count"] += 1

        # 2. Batch optimize timing for allowed users
        allowed_requests = [
            req
            for req in notification_requests
            if user_permissions.get(req["user_id"], False)
        ]

        if allowed_requests:
            # Prepare timing requests for batch optimization
            timing_requests = []
            for request in allowed_requests:
                timing_requests.append(
                    PersonalizedTimingRequest(
                        user_id=request["user_id"],
                        notification_type=request[
                            "notification_request"
                        ].notification_type,
                        default_time=datetime.utcnow(),
                    )
                )

            try:
                predictions = await self.personalization_engine.optimize_batch_timing(
                    timing_requests
                )
            except Exception as e:
                logger.error(f"Batch timing optimization failed: {e}")
                predictions = []  # Fall back to immediate sending

            # 3. Process each user's notification
            current_time = datetime.utcnow()

            for i, request in enumerate(allowed_requests):
                user_id = request["user_id"]
                notification_req = request["notification_request"]

                try:
                    # Get optimization result if available
                    prediction = predictions[i] if i < len(predictions) else None

                    if prediction:
                        optimized_time = prediction.predicted_time
                        optimization_info = {
                            "optimized": True,
                            "confidence": prediction.confidence_score,
                            "improvement_score": prediction.improvement_score,
                        }
                        results["optimization_stats"]["optimized_count"] += 1
                    else:
                        optimized_time = current_time
                        optimization_info = {"optimized": False, "fallback": True}
                        results["optimization_stats"]["fallback_count"] += 1

                    # Decide immediate vs scheduled
                    if optimized_time <= current_time + timedelta(minutes=5):
                        # Send immediately
                        notification_req.user_ids = [user_id]
                        response = self.fcm_service.send_push_notification(
                            notification_req
                        )

                        results["immediate_sends"].append(
                            {
                                "user_id": user_id,
                                "success": response.success,
                                "optimization_info": optimization_info,
                            }
                        )
                    else:
                        # Schedule for later
                        results["scheduled_sends"].append(
                            {
                                "user_id": user_id,
                                "scheduled_for": optimized_time.isoformat(),
                                "optimization_info": optimization_info,
                            }
                        )

                except Exception as e:
                    logger.error(
                        f"Failed to process notification for user {user_id}: {e}"
                    )
                    results["failed_sends"].append(
                        {"user_id": user_id, "error": str(e)}
                    )

        logger.info(
            f"Bulk personalized notifications complete: {results['optimization_stats']}"
        )
        return results

    async def get_user_notification_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Get insights about a user's notification preferences and patterns.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with user's notification insights
        """
        try:
            # Get user settings
            settings = await self.settings_service.get_user_settings(user_id)

            # Get behavior analysis
            behavior_metrics = (
                await self.personalization_engine.analyze_user_behavior_patterns(
                    user_id
                )
            )

            # Compile insights
            insights = {
                "user_id": user_id,
                "settings": {
                    "notifications_enabled": settings.enabled,
                    "quiet_hours_enabled": settings.quiet_hours_enabled,
                    "personalization_enabled": settings.personalized_timing_enabled,
                    "frequency_limits": {
                        "daily": settings.frequency_limit_per_day,
                        "weekly": settings.frequency_limit_per_week,
                    },
                },
                "behavior_patterns": {
                    "optimal_hours": behavior_metrics.optimal_hours,
                    "engagement_rate": behavior_metrics.overall_engagement_rate,
                    "preferred_days": behavior_metrics.preferred_days,
                    "total_notifications": behavior_metrics.total_notifications,
                    "open_rate": behavior_metrics.open_rate,
                },
                "recommendations": self._generate_user_recommendations(
                    settings, behavior_metrics
                ),
            }

            return insights

        except Exception as e:
            logger.error(f"Failed to get insights for user {user_id}: {e}")
            return {"user_id": user_id, "error": str(e), "insights_available": False}

    def _generate_user_recommendations(self, settings, behavior_metrics) -> List[str]:
        """Generate recommendations for improving user engagement."""
        recommendations = []

        if behavior_metrics.overall_engagement_rate < 0.3:
            recommendations.append("Consider reducing notification frequency")

        if not settings.personalized_timing_enabled:
            recommendations.append("Enable personalized timing for better engagement")

        if settings.frequency_limit_per_day > 15:
            recommendations.append("Consider lowering daily notification limit")

        if len(behavior_metrics.optimal_hours) > 0:
            recommendations.append(
                f"Best engagement hours: {', '.join(map(str, behavior_metrics.optimal_hours[:3]))}"
            )

        return recommendations


# Dependency injection function
def get_personalized_notification_service(
    db: Session = Depends(get_db),
    settings_service: NotificationSettingsService = Depends(
        get_notification_settings_service
    ),
    personalization_engine: PersonalizationEngine = Depends(get_personalization_engine),
    fcm_service: FCMService = Depends(get_fcm_service),
) -> PersonalizedNotificationService:
    """Get personalized notification service instance."""
    return PersonalizedNotificationService(
        db=db,
        settings_service=settings_service,
        personalization_engine=personalization_engine,
        fcm_service=fcm_service,
    )
