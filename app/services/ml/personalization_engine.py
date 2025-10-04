"""
Personalization Engine Service

Implements personalized notification timing based on user behavior patterns,
ML predictions, and real-time context. Supports task 2-2-3: 소유권 기반 추천 시간대.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.notification import NotificationType
from app.schemas.notification import (
    EngagementMetrics,
    OptimalTimingPrediction,
    PersonalizedTimingRequest,
    UserBehaviorPattern,
)
from app.services.experiments.ab_testing_service import ABTestingService
from app.services.ml.context_analyzer import ContextAnalyzer
from app.services.ml.ml_timing_model import MLTimingModel
from app.services.ml.real_time_analyzer import RealTimeAnalyzer
from app.services.ml.user_engagement_analyzer import UserEngagementAnalyzer
from app.services.notifications.notification_history_service import (
    NotificationHistoryService,
)
from app.services.utils.feedback_service import UserFeedbackService

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when there's insufficient data for personalization."""


class ModelPredictionError(Exception):
    """Raised when ML model prediction fails."""


class PersonalizationEngine:
    """
    Engine for personalizing notification timing based on user behavior and ML predictions.

    Core Features:
    - User behavior pattern analysis
    - ML-based optimal timing prediction
    - Context-aware timing adjustments
    - A/B testing integration
    - Real-time adaptation
    """

    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
        self.engagement_analyzer = UserEngagementAnalyzer()
        self.notification_history_service = NotificationHistoryService()
        self.ml_model = MLTimingModel()
        self.context_analyzer = ContextAnalyzer()
        self.ab_testing_service = ABTestingService()
        self.feedback_service = UserFeedbackService()
        self.real_time_analyzer = RealTimeAnalyzer()
        self.behavior_analyzer = UserEngagementAnalyzer()  # For backward compatibility

    async def analyze_user_behavior_patterns(
        self, user_id: str
    ) -> EngagementMetrics:  # noqa: C901
        """
        Analyze user's notification interaction patterns to identify optimal timing.

        Args:
            user_id: User identifier

        Returns:
            User engagement metrics with optimal timing patterns

        Raises:
            InsufficientDataError: If user has insufficient notification history
        """
        logger.info(f"Analyzing behavior patterns for user {user_id}")

        # Get user's notification history
        history = await self.notification_history_service.get_user_history(user_id)

        if len(history) < 5:  # Minimum data requirement
            raise InsufficientDataError(
                f"User {user_id} has insufficient notification history"
            )

        # Analyze engagement patterns
        total_notifications = len(history)
        opened_count = sum(1 for h in history if h.opened_at is not None)
        clicked_count = sum(1 for h in history if h.clicked)

        open_rate = opened_count / total_notifications if total_notifications > 0 else 0
        click_rate = (
            clicked_count / total_notifications if total_notifications > 0 else 0
        )

        # Calculate average open delay
        open_delays = []
        for h in history:
            if h.opened_at and h.sent_at:
                # Calculate delay in minutes between sent and opened
                sent_datetime = datetime.combine(datetime.today(), h.sent_at)
                opened_datetime = datetime.combine(datetime.today(), h.opened_at)
                delay_minutes = (opened_datetime - sent_datetime).total_seconds() / 60
                open_delays.append(delay_minutes)

        avg_open_delay = sum(open_delays) / len(open_delays) if open_delays else 0

        # Find peak engagement hours
        hour_engagement = {}
        for h in history:
            hour = h.sent_at.hour
            if hour not in hour_engagement:
                hour_engagement[hour] = {"total": 0, "engaged": 0}

            hour_engagement[hour]["total"] += 1
            if h.clicked or (h.opened_at and h.engagement_score > 0.5):
                hour_engagement[hour]["engaged"] += 1

        # Calculate engagement rates by hour and find peaks
        peak_hours = []
        for hour, stats in hour_engagement.items():
            engagement_rate = (
                stats["engaged"] / stats["total"] if stats["total"] > 0 else 0
            )
            if engagement_rate > 0.6:  # High engagement threshold
                peak_hours.append(hour)

        peak_hours.sort()

        # Identify preferred days
        day_engagement = {}
        for h in history:
            day = h.day_of_week
            if day not in day_engagement:
                day_engagement[day] = {"total": 0, "engaged": 0}

            day_engagement[day]["total"] += 1
            if h.clicked or h.engagement_score > 0.5:
                day_engagement[day]["engaged"] += 1

        preferred_days = []
        for day, stats in day_engagement.items():
            engagement_rate = (
                stats["engaged"] / stats["total"] if stats["total"] > 0 else 0
            )
            if engagement_rate > 0.5:
                preferred_days.append(day)

        # Calculate overall engagement rate
        overall_engagement = sum(h.engagement_score for h in history) / len(history)

        metrics = EngagementMetrics(
            user_id=user_id,
            total_notifications=total_notifications,
            opened_count=opened_count,
            clicked_count=clicked_count,
            open_rate=open_rate,
            click_rate=click_rate,
            average_open_delay_minutes=avg_open_delay,
            peak_engagement_hours=peak_hours,
            preferred_days=preferred_days,
            last_updated=datetime.now(),
            optimal_hours=peak_hours,
            overall_engagement_rate=overall_engagement,
        )

        logger.info(
            f"Analyzed {total_notifications} notifications for user {user_id}, "
            f"engagement rate: {overall_engagement:.2f}"
        )

        return metrics

    async def predict_optimal_timing(
        self, request: PersonalizedTimingRequest
    ) -> OptimalTimingPrediction:
        """
        Predict optimal notification timing using ML model and user patterns.

        Args:
            request: Personalized timing request

        Returns:
            Optimal timing prediction with confidence and alternatives

        Raises:
            InsufficientDataError: If user lacks sufficient data for prediction
            ModelPredictionError: If ML model fails
        """
        logger.info(f"Predicting optimal timing for user {request.user_id}")

        try:
            # Analyze user behavior patterns first
            behavior_metrics = await self.analyze_user_behavior_patterns(
                request.user_id
            )

            # Get ML model prediction
            optimal_hour = await self.ml_model.predict_optimal_hour(
                user_id=request.user_id,
                notification_type=request.notification_type,
                default_hour=request.default_time.hour,
                context=request.course_context or {},
            )

            # Calculate engagement probability
            engagement_prob = await self.behavior_analyzer.get_engagement_probability(
                request.user_id, request.notification_type, optimal_hour
            )

            # Create optimized time
            predicted_time = request.default_time.replace(
                hour=optimal_hour, minute=0, second=0, microsecond=0
            )

            # Generate alternative times
            alternatives = []
            for hour_offset in [-1, 1, -2, 2]:
                alt_hour = optimal_hour + hour_offset
                if 8 <= alt_hour <= 22:  # Reasonable hours only
                    alt_time = predicted_time.replace(hour=alt_hour)
                    alternatives.append(alt_time)

            # Calculate confidence score based on data quality and model certainty
            confidence = min(
                0.9, 0.5 + (behavior_metrics.total_notifications / 100) * 0.4
            )

            # Generate reasoning
            reasoning = f"ML model predicted hour {optimal_hour} based on user behavior patterns. "
            reasoning += f"User shows high engagement during {behavior_metrics.peak_engagement_hours}. "
            if request.course_context:
                reasoning += (
                    f"Context factors: {', '.join(request.course_context.keys())}."
                )

            prediction = OptimalTimingPrediction(
                user_id=request.user_id,
                predicted_time=predicted_time,
                confidence_score=confidence,
                engagement_probability=engagement_prob,
                alternative_times=alternatives,
                reasoning=reasoning,
                context_factors=request.course_context or {},
                fallback_used=False,
                constraint_applied=False,
                quiet_hours_adjusted=False,
            )

            logger.info(
                f"Predicted optimal timing for user {request.user_id}: "
                f"{predicted_time.hour}:00 (confidence: {confidence:.2f})"
            )

            return prediction

        except InsufficientDataError:
            # Let InsufficientDataError propagate directly
            raise
        except Exception as e:
            logger.error(
                f"Failed to predict optimal timing for user {request.user_id}: {e}"
            )
            raise ModelPredictionError(f"ML prediction failed: {e}")

    async def optimize_timing_for_engagement(
        self, request: PersonalizedTimingRequest
    ) -> OptimalTimingPrediction:
        """
        Optimize notification timing to maximize user engagement.

        Args:
            request: Timing optimization request

        Returns:
            Engagement-optimized timing prediction
        """
        logger.info(f"Optimizing timing for engagement, user {request.user_id}")

        # Get user engagement metrics
        metrics = await self.engagement_analyzer.get_user_metrics(request.user_id)

        if not metrics or len(metrics.peak_engagement_hours) == 0:
            # Fallback to default time if no engagement data
            return OptimalTimingPrediction(
                user_id=request.user_id,
                predicted_time=request.default_time,
                confidence_score=0.3,
                engagement_probability=0.5,
                alternative_times=[],
                reasoning="Insufficient engagement data, using default timing",
                fallback_used=True,
            )

        # Find the best engagement hour closest to default time
        default_hour = request.default_time.hour
        peak_hours = metrics.peak_engagement_hours

        # Select optimal hour from peak hours
        optimal_hour = min(peak_hours, key=lambda h: abs(h - default_hour))

        # Create optimized time
        optimized_time = request.default_time.replace(
            hour=optimal_hour, minute=0, second=0, microsecond=0
        )

        # Calculate improvement score
        default_engagement = 0.4  # Baseline engagement assumption
        peak_engagement = metrics.click_rate if metrics.click_rate > 0 else 0.6
        improvement_score = peak_engagement - default_engagement

        prediction = OptimalTimingPrediction(
            user_id=request.user_id,
            predicted_time=optimized_time,
            confidence_score=0.8,
            engagement_probability=peak_engagement,
            alternative_times=peak_hours,
            reasoning=f"Engagement optimization: adjusted to peak hour {optimal_hour} "
            f"based on {metrics.total_notifications} historical interactions",
            improvement_score=improvement_score,
            fallback_used=False,
        )

        logger.info(
            f"Optimized timing for engagement: {optimal_hour}:00 "
            f"(improvement: +{improvement_score:.2f})"
        )

        return prediction

    async def predict_with_ab_testing(
        self, request: PersonalizedTimingRequest
    ) -> OptimalTimingPrediction:
        """
        Predict optimal timing with A/B testing integration.

        Args:
            request: Timing request

        Returns:
            Prediction with A/B test group information
        """
        # Get user's A/B test group
        test_group = await self.ab_testing_service.get_user_group(request.user_id)

        if test_group == "control":
            # Use default algorithm
            prediction = OptimalTimingPrediction(
                user_id=request.user_id,
                predicted_time=request.default_time,
                confidence_score=0.5,
                engagement_probability=0.5,
                alternative_times=[],
                reasoning="Control group: using default timing",
                algorithm_used="default",
                ab_test_group="control",
            )
        else:
            # Use ML personalized algorithm
            prediction = await self.predict_optimal_timing(request)
            prediction.algorithm_used = "ml_personalized"
            prediction.ab_test_group = "treatment"

        return prediction

    async def predict_optimal_timing_with_fallback(
        self, request: PersonalizedTimingRequest
    ) -> OptimalTimingPrediction:
        """
        Predict optimal timing with fallback to default on errors.

        Args:
            request: Timing request

        Returns:
            Prediction with fallback handling
        """
        try:
            return await self.predict_optimal_timing(request)
        except Exception as e:
            logger.warning(
                f"ML prediction failed for user {request.user_id}, using fallback: {e}"
            )

            return OptimalTimingPrediction(
                user_id=request.user_id,
                predicted_time=request.default_time,
                confidence_score=0.3,
                engagement_probability=0.4,
                alternative_times=[],
                reasoning=f"Model error fallback: {str(e)}",
                fallback_used=True,
            )

    async def optimize_batch_timing(
        self, requests: List[PersonalizedTimingRequest]
    ) -> List[OptimalTimingPrediction]:
        """
        Optimize timing for multiple users efficiently.

        Args:
            requests: List of timing requests

        Returns:
            List of timing predictions
        """
        logger.info(f"Optimizing timing for {len(requests)} users in batch")

        start_time = datetime.now()

        # Extract user IDs and parameters for batch prediction
        user_ids = [req.user_id for req in requests]
        default_hours = [req.default_time.hour for req in requests]
        notification_types = [req.notification_type for req in requests]

        # Get batch predictions from ML model
        predicted_hours = await self.ml_model.batch_predict(
            user_ids=user_ids,
            notification_types=notification_types,
            default_hours=default_hours,
        )

        # Create prediction results
        results = []
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        for i, request in enumerate(requests):
            predicted_time = request.default_time.replace(
                hour=predicted_hours[i], minute=0, second=0, microsecond=0
            )

            prediction = OptimalTimingPrediction(
                user_id=request.user_id,
                predicted_time=predicted_time,
                confidence_score=0.7,
                engagement_probability=0.6,
                alternative_times=[],
                reasoning=f"Batch optimization: predicted hour {predicted_hours[i]}",
                processing_time_ms=processing_time_ms / len(requests),
            )

            results.append(prediction)

        logger.info(
            f"Completed batch timing optimization in {processing_time_ms:.1f}ms"
        )
        return results

    async def update_model_with_feedback(self, user_id: str) -> bool:
        """
        Update ML model with user feedback data.

        Args:
            user_id: User identifier

        Returns:
            Success status of model update
        """
        logger.info(f"Updating model with feedback for user {user_id}")

        # Get user feedback data
        feedback_data = await self.feedback_service.get_user_feedback(user_id)

        if not feedback_data:
            logger.info(f"No feedback data available for user {user_id}")
            return False

        # Process feedback and update model
        training_data = []
        for feedback in feedback_data:
            training_data.append(
                {
                    "user_id": user_id,
                    "notification_time": feedback["notification_time"],
                    "engagement": feedback["engagement"],
                    "feedback_score": 1.0
                    if feedback["feedback"] == "perfect_timing"
                    else 0.2,
                }
            )

        # Update model (simplified - in practice would be more complex)
        success = await self.ml_model.update_with_feedback(user_id, training_data)

        if success:
            logger.info(
                f"Successfully updated model with {len(training_data)} feedback points"
            )
        else:
            logger.error(f"Failed to update model with feedback for user {user_id}")

        return success

    async def adapt_timing_to_real_time_context(
        self, request: PersonalizedTimingRequest
    ) -> OptimalTimingPrediction:
        """
        Adapt timing based on real-time context (weather, traffic, events).

        Args:
            request: Timing request with real-time context

        Returns:
            Context-adapted timing prediction
        """
        logger.info(f"Adapting timing to real-time context for user {request.user_id}")

        # Analyze current conditions
        context_analysis = await self.real_time_analyzer.analyze_current_conditions(
            request.real_time_context or {}
        )

        # Get base prediction
        base_prediction = await self.predict_optimal_timing(request)

        # Apply real-time adjustments
        advance_minutes = context_analysis.get("recommended_advance_minutes", 0)

        if advance_minutes > 0:
            # Adjust timing earlier due to adverse conditions
            adapted_time = base_prediction.predicted_time - timedelta(
                minutes=advance_minutes
            )
            adaptation_reason = "real_time_conditions"
        else:
            adapted_time = base_prediction.predicted_time
            adaptation_reason = "no_adjustment_needed"

        # Create adapted prediction
        adapted_prediction = OptimalTimingPrediction(
            user_id=request.user_id,
            predicted_time=adapted_time,
            confidence_score=base_prediction.confidence_score,
            engagement_probability=base_prediction.engagement_probability,
            alternative_times=base_prediction.alternative_times,
            reasoning=f"Real-time adaptation: {adaptation_reason}. "
            + base_prediction.reasoning,
            context_factors=request.real_time_context or {},
            adaptation_reason=adaptation_reason,
        )

        logger.info(
            f"Adapted timing by {advance_minutes} minutes due to real-time conditions"
        )

        return adapted_prediction


# Supporting service stubs (to be implemented separately)
class NotificationHistoryServiceStub:
    """Service for retrieving notification history data."""

    async def get_user_history(self, user_id: str) -> List[UserBehaviorPattern]:
        """Get user's notification history."""
        # Mock implementation for testing
        return []


class MLTimingModelStub:
    """Machine learning model for timing predictions."""

    async def predict_optimal_hour(
        self,
        user_id: str,
        notification_type: NotificationType,
        default_hour: int,
        context: Dict[str, Any],
    ) -> int:
        """Predict optimal hour for notification."""
        # Mock implementation - in practice would call actual ML model
        return default_hour + 1  # Simple adjustment

    async def batch_predict(
        self,
        user_ids: List[str],
        notification_types: List[NotificationType],
        default_hours: List[int],
    ) -> List[int]:
        """Batch prediction for multiple users."""
        # Mock implementation
        return [hour + 1 for hour in default_hours]

    async def update_with_feedback(
        self, user_id: str, training_data: List[Dict]
    ) -> bool:
        """Update model with user feedback."""
        return True


class ContextAnalyzerStub:
    """Service for analyzing course and user context."""

    async def analyze_course_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze course context for timing adjustments."""
        return {"recommended_advance_minutes": 30}


class ABTestingServiceStub:
    """Service for A/B testing group management."""

    async def get_user_group(self, user_id: str) -> str:
        """Get user's A/B test group."""
        # Simple hash-based assignment
        return "control" if hash(user_id) % 2 == 0 else "treatment"


class UserFeedbackServiceStub:
    """Service for managing user feedback."""

    async def get_user_feedback(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user feedback data."""
        return []


class RealTimeAnalyzerStub:
    """Service for real-time context analysis."""

    async def analyze_current_conditions(
        self, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze real-time conditions."""
        advance_minutes = 0

        # Weather impact
        if context.get("weather") == "heavy_rain":
            advance_minutes += 30

        # Traffic impact
        if context.get("traffic_level") == "severe":
            advance_minutes += 30

        # Event impact
        if context.get("public_event"):
            advance_minutes += 15

        return {"recommended_advance_minutes": advance_minutes}


# Factory function for dependency injection
def get_personalization_engine(db: Session = Depends(get_db)) -> PersonalizationEngine:
    """Get personalization engine instance."""
    return PersonalizationEngine(db)
