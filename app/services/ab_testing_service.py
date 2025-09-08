"""A/B testing service for notification optimization."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

try:
    import numpy as np
    import scipy.stats
    from scipy.stats import chi2_contingency
except ImportError:
    np = None
    scipy = None
    chi2_contingency = None

from app.models.notification_analytics import (
    ABTestCohort,
    InteractionType,
    NotificationInteraction,
    NotificationLog,
    UserABTestAssignment,
)
from app.schemas.notification_analytics import ABTestCohortCreate, ABTestResults

logger = logging.getLogger(__name__)


class ABTestingService:
    """Service for managing A/B tests for notification optimization."""

    def __init__(self, db: Session) -> None:
        self.db: Session = db

    async def create_notification_ab_test(
        self,
        test_name: str,
        test_description: str,
        variants: List[Dict[str, Any]],
        traffic_split: Optional[List[float]] = None,
    ) -> List[ABTestCohort]:
        """알림 최적화를 위한 A/B 테스트 생성."""
        try:
            if not variants:
                raise ValueError("At least one variant is required")

            if traffic_split and len(traffic_split) != len(variants):
                raise ValueError("Traffic split must match number of variants")

            # Default even split if not specified
            if not traffic_split:
                split_size = 1.0 / len(variants)
                traffic_split = [split_size] * len(variants)

            # Validate traffic split sums to 1.0
            if abs(sum(traffic_split) - 1.0) > 0.01:
                raise ValueError("Traffic split must sum to 1.0")

            cohorts = []
            for i, (variant, allocation) in enumerate(zip(variants, traffic_split)):
                cohort_data = ABTestCohortCreate(
                    test_name=test_name,
                    cohort_name=f"{test_name}_variant_{chr(65 + i)}",  # A, B, C, etc.
                    description=test_description,
                    variant_config=variant,
                    traffic_allocation=allocation,
                    is_control=i == 0,  # First variant is control
                    is_active=True,
                    created_by="system",
                )

                cohort = ABTestCohort(**cohort_data.model_dump())
                self.db.add(cohort)
                cohorts.append(cohort)

            self.db.commit()
            for cohort in cohorts:
                self.db.refresh(cohort)

            logger.info(f"Created A/B test '{test_name}' with {len(cohorts)} cohorts")
            return cohorts

        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            self.db.rollback()
            raise

    async def assign_user_to_test(
        self, user_id: str, test_name: str
    ) -> UserABTestAssignment:
        """사용자를 A/B 테스트에 할당."""
        try:
            # Check if user is already assigned to this test
            existing_assignment = (
                self.db.query(UserABTestAssignment)
                .join(ABTestCohort)
                .filter(
                    and_(
                        UserABTestAssignment.user_id == user_id,
                        ABTestCohort.test_name == test_name,
                        ABTestCohort.is_active.is_(True),
                    )
                )
                .first()
            )

            if existing_assignment:
                return existing_assignment

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

            # Deterministic assignment based on user ID hash
            user_hash = hash(user_id) % 100
            cumulative_allocation = 0.0

            selected_cohort = None
            for cohort in cohorts:
                allocation_percentage = cohort.traffic_allocation * 100
                if user_hash < cumulative_allocation + allocation_percentage:
                    selected_cohort = cohort
                    break
                cumulative_allocation += allocation_percentage

            if not selected_cohort:
                selected_cohort = cohorts[-1]  # Fallback to last cohort

            # Create assignment
            assignment = UserABTestAssignment(
                user_id=user_id,
                cohort_id=selected_cohort.id,
                assignment_method="deterministic_hash",
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

    async def get_user_test_variant(
        self, user_id: str, test_name: str
    ) -> Optional[Dict[str, Any]]:
        """사용자의 A/B 테스트 변형 설정 조회."""
        try:
            assignment = (
                self.db.query(UserABTestAssignment)
                .join(ABTestCohort)
                .filter(
                    and_(
                        UserABTestAssignment.user_id == user_id,
                        ABTestCohort.test_name == test_name,
                        ABTestCohort.is_active.is_(True),
                    )
                )
                .first()
            )

            if not assignment:
                # Auto-assign user to test
                assignment = await self.assign_user_to_test(user_id, test_name)

            if assignment and assignment.cohort:
                return {
                    "cohort_name": assignment.cohort.cohort_name,
                    "variant_config": assignment.cohort.variant_config,
                    "is_control": assignment.cohort.is_control,
                    "assigned_at": assignment.assigned_at,
                }

            return None

        except Exception as e:
            logger.error(f"Failed to get user test variant: {e}")
            return None

    async def analyze_ab_test_results(
        self, test_name: str, analysis_period_days: int = 30
    ) -> ABTestResults:
        """A/B 테스트 결과 분석."""
        try:
            # Get test cohorts
            cohorts = (
                self.db.query(ABTestCohort)
                .filter(ABTestCohort.test_name == test_name)
                .all()
            )

            if not cohorts:
                raise ValueError(f"No cohorts found for test: {test_name}")

            # Analysis period
            since_date = datetime.now(timezone.utc) - timedelta(
                days=analysis_period_days
            )

            cohort_results = []
            control_metrics = None

            for cohort in cohorts:
                # Get assignments for this cohort
                assignments = (
                    self.db.query(UserABTestAssignment)
                    .filter(
                        and_(
                            UserABTestAssignment.cohort_id == cohort.id,
                            UserABTestAssignment.assigned_at >= since_date,
                        )
                    )
                    .all()
                )

                user_ids = [a.user_id for a in assignments]
                total_users = len(user_ids)

                if total_users == 0:
                    continue

                # Get notification metrics for users in this cohort
                logs = (
                    self.db.query(NotificationLog)
                    .filter(
                        and_(
                            NotificationLog.user_id.in_(user_ids),
                            NotificationLog.sent_at >= since_date,
                            NotificationLog.success.is_(True),
                        )
                    )
                    .all()
                )

                total_notifications = len(logs)
                if total_notifications == 0:
                    continue

                # Get interactions
                log_ids = [log.id for log in logs]
                interactions = (
                    self.db.query(NotificationInteraction)
                    .filter(NotificationInteraction.notification_log_id.in_(log_ids))
                    .all()
                )

                # Calculate metrics
                opens = len(
                    [
                        i
                        for i in interactions
                        if i.interaction_type == InteractionType.OPENED
                    ]
                )
                clicks = len(
                    [
                        i
                        for i in interactions
                        if i.interaction_type == InteractionType.CLICKED
                    ]
                )

                open_rate = (
                    opens / total_notifications if total_notifications > 0 else 0
                )
                click_rate = (
                    clicks / total_notifications if total_notifications > 0 else 0
                )
                engagement_rate = (
                    (opens + clicks) / total_notifications
                    if total_notifications > 0
                    else 0
                )

                # Calculate conversion metrics (simplified)
                conversion_rate = click_rate  # Using click rate as conversion proxy

                metrics = {
                    "total_users": total_users,
                    "total_notifications": total_notifications,
                    "total_opens": opens,
                    "total_clicks": clicks,
                    "open_rate": open_rate,
                    "click_rate": click_rate,
                    "engagement_rate": engagement_rate,
                    "conversion_rate": conversion_rate,
                }

                if cohort.is_control:
                    control_metrics = metrics

                cohort_results.append(
                    {
                        "cohort_name": cohort.cohort_name,
                        "is_control": cohort.is_control,
                        "variant_config": cohort.variant_config,
                        "metrics": metrics,
                    }
                )

            # Calculate statistical significance and lift
            statistical_results = await self._calculate_statistical_significance(
                cohort_results, control_metrics
            )

            # Determine winner
            winner = await self._determine_test_winner(
                cohort_results, statistical_results
            )

            return ABTestResults(
                test_name=test_name,
                analysis_period_days=analysis_period_days,
                cohort_results=cohort_results,
                statistical_significance=statistical_results,
                winner=winner,
                confidence_level=0.95,
                analyzed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            logger.error(f"Failed to analyze A/B test results: {e}")
            raise

    async def end_ab_test(self, test_name: str, winner_cohort: str) -> bool:
        """A/B 테스트 종료 및 승자 적용."""
        try:
            # Mark all cohorts for this test as inactive
            cohorts = (
                self.db.query(ABTestCohort)
                .filter(ABTestCohort.test_name == test_name)
                .all()
            )

            for cohort in cohorts:
                cohort.is_active = False
                cohort.ended_at = datetime.now(timezone.utc)

                if cohort.cohort_name == winner_cohort:
                    cohort.is_winner = True
                    cohort.variant_config

            self.db.commit()

            logger.info(f"Ended A/B test '{test_name}' with winner '{winner_cohort}'")
            return True

        except Exception as e:
            logger.error(f"Failed to end A/B test: {e}")
            self.db.rollback()
            return False

    async def get_active_tests_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자가 참여 중인 활성 A/B 테스트 목록."""
        try:
            assignments = (
                self.db.query(UserABTestAssignment)
                .join(ABTestCohort)
                .filter(
                    and_(
                        UserABTestAssignment.user_id == user_id,
                        ABTestCohort.is_active.is_(True),
                    )
                )
                .all()
            )

            active_tests = []
            for assignment in assignments:
                active_tests.append(
                    {
                        "test_name": assignment.cohort.test_name,
                        "cohort_name": assignment.cohort.cohort_name,
                        "variant_config": assignment.cohort.variant_config,
                        "is_control": assignment.cohort.is_control,
                        "assigned_at": assignment.assigned_at,
                    }
                )

            return active_tests

        except Exception as e:
            logger.error(f"Failed to get active tests for user: {e}")
            return []

    async def _calculate_statistical_significance(
        self, cohort_results: List[Dict], control_metrics: Optional[Dict]
    ) -> Dict[str, Any]:
        """통계적 유의성 계산."""
        try:
            if not control_metrics:
                return {"has_significance": False, "reason": "No control group found"}

            # Use scipy for statistical testing (would be imported here)
            try:
                import numpy as np
                from scipy.stats import chi2_contingency
            except ImportError:
                logger.warning("scipy not available for statistical testing")
                return {
                    "has_significance": False,
                    "reason": "Statistical library not available",
                }

            significance_results = {}

            for result in cohort_results:
                if result["is_control"]:
                    continue

                metrics = result["metrics"]
                cohort_name = result["cohort_name"]

                # Chi-square test for engagement rates
                control_engaged = (
                    control_metrics["total_opens"] + control_metrics["total_clicks"]
                )
                control_not_engaged = (
                    control_metrics["total_notifications"] - control_engaged
                )

                test_engaged = metrics["total_opens"] + metrics["total_clicks"]
                test_not_engaged = metrics["total_notifications"] - test_engaged

                if (
                    min(
                        control_engaged,
                        control_not_engaged,
                        test_engaged,
                        test_not_engaged,
                    )
                    >= 5
                ):
                    # Chi-square test
                    contingency_table = np.array(
                        [
                            [control_engaged, control_not_engaged],
                            [test_engaged, test_not_engaged],
                        ]
                    )

                    chi2, p_value, _, _ = chi2_contingency(contingency_table)
                    is_significant = p_value < 0.05

                    # Calculate lift
                    lift = (
                        (
                            metrics["engagement_rate"]
                            - control_metrics["engagement_rate"]
                        )
                        / control_metrics["engagement_rate"]
                        if control_metrics["engagement_rate"] > 0
                        else 0
                    )

                    significance_results[cohort_name] = {
                        "test_statistic": chi2,
                        "p_value": p_value,
                        "is_significant": is_significant,
                        "confidence_level": 0.95,
                        "lift": lift,
                        "sample_size": metrics["total_notifications"],
                    }
                else:
                    significance_results[cohort_name] = {
                        "is_significant": False,
                        "reason": "Insufficient sample size for statistical testing",
                        "lift": 0,
                        "sample_size": metrics["total_notifications"],
                    }

            return {
                "has_significance": any(
                    r.get("is_significant", False)
                    for r in significance_results.values()
                ),
                "results": significance_results,
            }

        except Exception as e:
            logger.error(f"Failed to calculate statistical significance: {e}")
            return {"has_significance": False, "reason": f"Calculation error: {str(e)}"}

    async def _determine_test_winner(
        self, cohort_results: List[Dict], statistical_results: Dict[str, Any]
    ) -> Optional[str]:
        """테스트 승자 결정."""
        try:
            if not statistical_results.get("has_significance", False):
                return None

            # Find the cohort with the best performance and statistical significance
            best_cohort = None
            best_engagement = 0

            significance_data = statistical_results.get("results", {})

            for result in cohort_results:
                if result["is_control"]:
                    continue

                cohort_name = result["cohort_name"]
                engagement_rate = result["metrics"]["engagement_rate"]

                # Check if this cohort has statistical significance
                sig_result = significance_data.get(cohort_name, {})
                if (
                    sig_result.get("is_significant", False)
                    and engagement_rate > best_engagement
                ):
                    best_engagement = engagement_rate
                    best_cohort = cohort_name

            return best_cohort

        except Exception as e:
            logger.error(f"Failed to determine test winner: {e}")
            return None


def get_ab_testing_service(db: Session) -> ABTestingService:
    """Get A/B testing service instance."""
    return ABTestingService(db)
