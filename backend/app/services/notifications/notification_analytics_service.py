"""Notification analytics service for personalization and A/B testing."""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.notification_analytics import (
    ABTestCohort,
    InteractionType,
    NotificationInteraction,
    NotificationLog,
    UserABTestAssignment,
    UserNotificationPattern,
)
from app.schemas.notification_analytics import (
    ABTestCohortCreate,
    NotificationAnalyticsReport,
    NotificationInteractionCreate,
    NotificationLogCreate,
    PersonalizationInsights,
)

logger = logging.getLogger(__name__)


class NotificationAnalyticsService:
    """Service for notification analytics, personalization, and A/B testing."""

    def __init__(self, db: Session) -> None:
        self.db: Session = db

    async def log_notification_sent(
        self, log_data: NotificationLogCreate
    ) -> NotificationLog:
        """알림 전송 로그 기록."""
        try:
            # Create notification log entry
            notification_log = NotificationLog(**log_data.model_dump())
            self.db.add(notification_log)
            self.db.commit()
            self.db.refresh(notification_log)

            logger.info(f"Logged notification sent: {notification_log.id}")
            return notification_log

        except Exception as e:
            logger.error(f"Failed to log notification sent: {e}")
            self.db.rollback()
            raise

    async def log_notification_interaction(
        self, interaction_data: NotificationInteractionCreate
    ) -> NotificationInteraction:
        """알림 상호작용 로그 기록 및 사용자 패턴 업데이트."""
        try:
            # Create interaction entry
            interaction = NotificationInteraction(**interaction_data.model_dump())
            self.db.add(interaction)
            self.db.commit()
            self.db.refresh(interaction)

            # Update user engagement pattern asynchronously
            await self.update_user_engagement_pattern(str(interaction_data.user_id))

            logger.info(f"Logged notification interaction: {interaction.id}")
            return interaction

        except Exception as e:
            logger.error(f"Failed to log notification interaction: {e}")
            self.db.rollback()
            raise

    async def analyze_user_notification_pattern(
        self, user_id: str, analysis_period_days: int = 30
    ) -> UserNotificationPattern:
        """사용자 알림 패턴 분석 및 업데이트."""
        try:
            # Check if pattern already exists
            existing_pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            # Get notification logs for the period
            since_date = datetime.now(timezone.utc) - timedelta(
                days=analysis_period_days
            )
            notification_logs = (
                self.db.query(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.user_id == user_id,
                        NotificationLog.sent_at >= since_date,
                        NotificationLog.success.is_(True),
                    )
                )
                .all()
            )

            if not notification_logs:
                # Return default pattern for new users
                if existing_pattern:
                    return existing_pattern
                else:
                    return await self._create_default_pattern(user_id)

            # Get interactions for these notifications
            notification_ids = [log.id for log in notification_logs]
            interactions = (
                self.db.query(NotificationInteraction)
                .filter(
                    and_(
                        NotificationInteraction.notification_log_id.in_(
                            notification_ids
                        ),
                        NotificationInteraction.user_id == user_id,
                    )
                )
                .all()
            )

            # Analyze patterns
            pattern_data = self._analyze_patterns(notification_logs, interactions)

            if existing_pattern:
                # Update existing pattern
                for key, value in pattern_data.items():
                    setattr(existing_pattern, key, value)
                existing_pattern.last_analyzed_at = datetime.now(timezone.utc)
                existing_pattern.analysis_period_days = analysis_period_days
                self.db.commit()
                self.db.refresh(existing_pattern)
                return existing_pattern
            else:
                # Create new pattern
                pattern_data["user_id"] = user_id
                pattern_data["last_analyzed_at"] = datetime.now(timezone.utc)
                pattern_data["analysis_period_days"] = analysis_period_days

                new_pattern = UserNotificationPattern(**pattern_data)
                self.db.add(new_pattern)
                self.db.commit()
                self.db.refresh(new_pattern)
                return new_pattern

        except Exception as e:
            logger.error(f"Failed to analyze user notification pattern: {e}")
            self.db.rollback()
            raise

    async def get_optimal_send_time_for_user(self, user_id: str) -> int:
        """사용자별 최적 알림 전송 시간 조회."""
        try:
            pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not pattern or not pattern.preferred_hours:
                return 18  # Default hour

            return pattern.get_optimal_send_hour()

        except Exception as e:
            logger.error(f"Failed to get optimal send time: {e}")
            return 18  # Fallback to default

    async def should_personalize_notification(
        self, user_id: str, notification_type: str
    ) -> bool:
        """개인화 적용 여부 결정."""
        try:
            pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not pattern:
                return False

            # High engagement users get personalization
            if (
                pattern.engagement_rate > 0.5
                and pattern.total_notifications_received >= 20
            ):
                return True

            # Users with clear timing preferences
            if pattern.should_personalize_timing():
                return True

            # Users showing positive response to personalization
            if (
                pattern.personalized_open_rate
                and pattern.non_personalized_open_rate
                and pattern.personalized_open_rate > pattern.non_personalized_open_rate
            ):
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to determine personalization: {e}")
            return False

    async def generate_analytics_report(
        self, start_date: datetime, end_date: datetime
    ) -> NotificationAnalyticsReport:
        """종합 알림 분석 리포트 생성."""
        try:
            # Basic metrics
            total_sent = (
                self.db.query(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.sent_at >= start_date,
                        NotificationLog.sent_at <= end_date,
                    )
                )
                .count()
            )

            total_delivered = (
                self.db.query(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.sent_at >= start_date,
                        NotificationLog.sent_at <= end_date,
                        NotificationLog.success.is_(True),
                    )
                )
                .count()
            )

            # Interaction metrics
            opened_count = (
                self.db.query(NotificationInteraction)
                .join(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.sent_at >= start_date,
                        NotificationLog.sent_at <= end_date,
                        NotificationInteraction.interaction_type
                        == InteractionType.OPENED,
                    )
                )
                .count()
            )

            clicked_count = (
                self.db.query(NotificationInteraction)
                .join(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.sent_at >= start_date,
                        NotificationLog.sent_at <= end_date,
                        NotificationInteraction.interaction_type
                        == InteractionType.CLICKED,
                    )
                )
                .count()
            )

            # Calculate rates
            delivery_rate = (total_delivered / total_sent) if total_sent > 0 else 0
            open_rate = (opened_count / total_delivered) if total_delivered > 0 else 0
            click_rate = (clicked_count / total_delivered) if total_delivered > 0 else 0

            # Average delivery time
            avg_delivery_time = (
                self.db.query(func.avg(NotificationLog.delivery_time_seconds))
                .filter(
                    and_(
                        NotificationLog.sent_at >= start_date,
                        NotificationLog.sent_at <= end_date,
                        NotificationLog.success.is_(True),
                    )
                )
                .scalar()
                or 0.0
            )

            # Type breakdown (simplified for now)
            type_breakdown = {}
            platform_breakdown = {}
            hourly_performance = {}
            ab_test_performance = []

            # Personalization effectiveness (if available)
            personalization_lift = await self._calculate_personalization_lift(
                start_date, end_date
            )

            return NotificationAnalyticsReport(
                period_start=start_date,
                period_end=end_date,
                total_notifications_sent=total_sent,
                total_notifications_delivered=total_delivered,
                total_notifications_opened=opened_count,
                total_notifications_clicked=clicked_count,
                overall_delivery_rate=delivery_rate,
                overall_open_rate=open_rate,
                overall_click_rate=click_rate,
                avg_delivery_time_seconds=avg_delivery_time,
                type_breakdown=type_breakdown,
                platform_breakdown=platform_breakdown,
                hourly_performance=hourly_performance,
                ab_test_performance=ab_test_performance,
                personalization_lift=personalization_lift,
                generated_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Failed to generate analytics report: {e}")
            raise

    async def create_ab_test_cohort(
        self, cohort_data: ABTestCohortCreate
    ) -> ABTestCohort:
        """A/B 테스트 코호트 생성."""
        try:
            cohort = ABTestCohort(**cohort_data.model_dump())
            self.db.add(cohort)
            self.db.commit()
            self.db.refresh(cohort)

            logger.info(
                f"Created A/B test cohort: {cohort.test_name}/{cohort.cohort_name}"
            )
            return cohort

        except Exception as e:
            logger.error(f"Failed to create A/B test cohort: {e}")
            self.db.rollback()
            raise

    async def assign_user_to_ab_test(
        self, user_id: str, test_name: str
    ) -> UserABTestAssignment:
        """사용자를 A/B 테스트 코호트에 할당."""
        try:
            # Get active cohorts for the test
            cohorts = (
                self.db.query(ABTestCohort)
                .filter(
                    and_(
                        ABTestCohort.test_name == test_name,
                        ABTestCohort.is_active.is_(True),
                    )
                )
                .all()
            )

            if not cohorts:
                raise ValueError(f"No active cohorts found for test: {test_name}")

            # Random assignment based on traffic allocation
            random_value = random.random()
            cumulative_allocation = 0.0

            selected_cohort = None
            for cohort in cohorts:
                cumulative_allocation += cohort.traffic_allocation
                if random_value <= cumulative_allocation:
                    selected_cohort = cohort
                    break

            if not selected_cohort:
                selected_cohort = cohorts[-1]  # Fallback to last cohort

            # Create assignment
            assignment = UserABTestAssignment(
                user_id=user_id,
                cohort_id=selected_cohort.id,
                assignment_method="random",
                assigned_at=datetime.now(timezone.utc),
            )

            self.db.add(assignment)
            self.db.commit()
            self.db.refresh(assignment)

            logger.info(
                f"Assigned user {user_id} to cohort {selected_cohort.cohort_name}"
            )
            return assignment

        except Exception as e:
            logger.error(f"Failed to assign user to A/B test: {e}")
            self.db.rollback()
            raise

    async def get_personalization_insights(
        self, user_id: str
    ) -> PersonalizationInsights:
        """사용자별 개인화 인사이트 조회."""
        try:
            pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not pattern:
                # Analyze pattern first
                pattern = await self.analyze_user_notification_pattern(user_id)

            # Build insights
            optimal_times = []
            if pattern.preferred_hours:
                # Get top 3 hours
                sorted_hours = sorted(
                    pattern.preferred_hours.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]
                optimal_times = [int(hour) for hour, _ in sorted_hours]

            preferred_types = []
            if pattern.type_preferences:
                # Get types with high engagement
                for type_name, stats in pattern.type_preferences.items():
                    if stats.get("sent", 0) > 0:
                        engagement = stats.get("engaged", 0) / stats["sent"]
                        if engagement > 0.5:
                            preferred_types.append(type_name)

            recommendations = self._generate_personalization_recommendations(pattern)

            # Calculate estimated improvement
            estimated_improvement = None
            if pattern.personalization_lift:
                estimated_improvement = pattern.personalization_lift * 100

            return PersonalizationInsights(
                user_id=user_id,
                overall_engagement_score=pattern.overall_engagement_score,
                optimal_send_times=optimal_times or [18],  # Default if none
                preferred_notification_types=preferred_types,
                response_time_pattern={
                    "avg_seconds": pattern.avg_response_time_seconds or 0,
                    "fastest_seconds": pattern.fastest_response_time_seconds or 0,
                },
                personalization_recommendations=recommendations,
                should_use_timing_optimization=pattern.should_personalize_timing(),
                should_use_content_personalization=pattern.engagement_rate > 0.3,
                estimated_improvement=estimated_improvement,
            )

        except Exception as e:
            logger.error(f"Failed to get personalization insights: {e}")
            raise

    async def update_user_engagement_pattern(
        self, user_id: str
    ) -> UserNotificationPattern:
        """사용자 참여 패턴 실시간 업데이트."""
        try:
            # Get existing pattern
            pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not pattern:
                return await self.analyze_user_notification_pattern(user_id)

            # Get recent activity (last 24 hours)
            since = datetime.now(timezone.utc) - timedelta(hours=24)

            recent_logs = (
                self.db.query(NotificationLog)
                .filter(
                    and_(
                        NotificationLog.user_id == user_id,
                        NotificationLog.sent_at >= since,
                        NotificationLog.success.is_(True),
                    )
                )
                .all()
            )

            if not recent_logs:
                return pattern

            # Get interactions for recent logs
            recent_log_ids = [log.id for log in recent_logs]
            recent_interactions = (
                self.db.query(NotificationInteraction)
                .filter(
                    and_(
                        NotificationInteraction.notification_log_id.in_(recent_log_ids),
                        NotificationInteraction.user_id == user_id,
                    )
                )
                .all()
            )

            # Update counters
            new_notifications = len(recent_logs)
            new_opens = len(
                [
                    i
                    for i in recent_interactions
                    if i.interaction_type == InteractionType.OPENED
                ]
            )
            new_clicks = len(
                [
                    i
                    for i in recent_interactions
                    if i.interaction_type == InteractionType.CLICKED
                ]
            )

            pattern.total_notifications_received += new_notifications
            pattern.total_notifications_opened += new_opens
            pattern.total_notifications_clicked += new_clicks

            # Recalculate rates
            if pattern.total_notifications_received > 0:
                pattern.open_rate = (
                    pattern.total_notifications_opened
                    / pattern.total_notifications_received
                )
                pattern.click_rate = (
                    pattern.total_notifications_clicked
                    / pattern.total_notifications_received
                )
                pattern.engagement_rate = (
                    pattern.total_notifications_opened
                    + pattern.total_notifications_clicked
                ) / pattern.total_notifications_received

            pattern.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(pattern)

            return pattern

        except Exception as e:
            logger.error(f"Failed to update user engagement pattern: {e}")
            self.db.rollback()
            raise

    async def _create_default_pattern(self, user_id: str) -> UserNotificationPattern:
        """새 사용자를 위한 기본 패턴 생성."""
        default_pattern = UserNotificationPattern(
            user_id=user_id,
            total_notifications_received=0,
            total_notifications_opened=0,
            total_notifications_clicked=0,
            total_notifications_dismissed=0,
            open_rate=0.0,
            click_rate=0.0,
            engagement_rate=0.0,
            last_analyzed_at=datetime.now(timezone.utc),
        )

        self.db.add(default_pattern)
        self.db.commit()
        self.db.refresh(default_pattern)
        return default_pattern

    def _analyze_patterns(
        self, logs: List[NotificationLog], interactions: List[NotificationInteraction]
    ) -> Dict[str, Any]:
        """알림 로그와 상호작용 데이터를 분석하여 패턴 추출."""
        total_notifications = len(logs)
        opens = len(
            [i for i in interactions if i.interaction_type == InteractionType.OPENED]
        )
        clicks = len(
            [i for i in interactions if i.interaction_type == InteractionType.CLICKED]
        )
        dismissals = len(
            [i for i in interactions if i.interaction_type == InteractionType.DISMISSED]
        )

        # Calculate rates
        open_rate = opens / total_notifications if total_notifications > 0 else 0
        click_rate = clicks / total_notifications if total_notifications > 0 else 0
        engagement_rate = (
            (opens + clicks) / total_notifications if total_notifications > 0 else 0
        )

        # Hourly pattern analysis
        hourly_stats = {}
        for log in logs:
            hour = str(log.sent_at.hour)
            if hour not in hourly_stats:
                hourly_stats[hour] = {"sent": 0, "engaged": 0}
            hourly_stats[hour]["sent"] += 1

        # Count engagements by hour
        for interaction in interactions:
            if interaction.interaction_type in [
                InteractionType.OPENED,
                InteractionType.CLICKED,
            ]:
                # Find the corresponding log
                log = next(
                    (
                        log_item
                        for log_item in logs
                        if log_item.id == interaction.notification_log_id
                    ),
                    None,
                )
                if log:
                    hour = str(log.sent_at.hour)
                    if hour in hourly_stats:
                        hourly_stats[hour]["engaged"] += 1

        # Calculate engagement rates by hour
        preferred_hours = {}
        for hour, stats in hourly_stats.items():
            if stats["sent"] > 0:
                preferred_hours[hour] = stats["engaged"] / stats["sent"]

        # Find most/least active hours
        most_active_hour = None
        least_active_hour = None
        if preferred_hours:
            most_active_hour = int(max(preferred_hours, key=preferred_hours.get))
            least_active_hour = int(min(preferred_hours, key=preferred_hours.get))

        # Response time analysis
        response_times = []
        for interaction in interactions:
            if interaction.time_from_delivery:
                response_times.append(interaction.time_from_delivery)

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else None
        )
        fastest_response_time = min(response_times) if response_times else None

        return {
            "total_notifications_received": total_notifications,
            "total_notifications_opened": opens,
            "total_notifications_clicked": clicks,
            "total_notifications_dismissed": dismissals,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "engagement_rate": engagement_rate,
            "preferred_hours": preferred_hours if preferred_hours else None,
            "most_active_hour": most_active_hour,
            "least_active_hour": least_active_hour,
            "avg_response_time_seconds": avg_response_time,
            "fastest_response_time_seconds": fastest_response_time,
        }

    def _generate_personalization_recommendations(
        self, pattern: UserNotificationPattern
    ) -> List[str]:
        """개인화 추천사항 생성."""
        recommendations = []

        if pattern.overall_engagement_score < 30:
            recommendations.append("낮은 참여율: 알림 빈도를 줄이고 내용을 더 개인화하세요")

        if pattern.should_personalize_timing():
            recommendations.append(
                f"최적 시간 활용: {pattern.get_optimal_send_hour()}시 전후 발송 권장"
            )

        if pattern.engagement_rate > 0.7:
            recommendations.append("높은 참여율: 현재 전략 유지하고 추가 개인화 테스트")

        if not recommendations:
            recommendations.append("충분한 데이터가 축적되면 더 정확한 추천을 제공합니다")

        return recommendations

    async def _calculate_personalization_lift(
        self, start_date: datetime, end_date: datetime
    ) -> Optional[float]:
        """개인화 적용 효과 계산."""
        try:
            # Get patterns with personalization data
            patterns = (
                self.db.query(UserNotificationPattern)
                .filter(
                    and_(
                        UserNotificationPattern.personalized_open_rate.isnot(None),
                        UserNotificationPattern.non_personalized_open_rate.isnot(None),
                    )
                )
                .all()
            )

            if not patterns:
                return None

            total_lift = 0.0
            count = 0

            for pattern in patterns:
                if pattern.non_personalized_open_rate > 0:
                    lift = (
                        pattern.personalized_open_rate
                        - pattern.non_personalized_open_rate
                    ) / pattern.non_personalized_open_rate
                    total_lift += lift
                    count += 1

            return total_lift / count if count > 0 else None

        except Exception as e:
            logger.error(f"Failed to calculate personalization lift: {e}")
            return None


def get_notification_analytics_service(db: Session) -> NotificationAnalyticsService:
    """Get notification analytics service instance."""
    return NotificationAnalyticsService(db)
