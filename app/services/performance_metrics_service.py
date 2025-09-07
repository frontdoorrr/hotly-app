"""Performance metrics tracking service for onboarding optimization."""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PerformanceMetricsCollector:
    """Collector for onboarding performance metrics and KPIs."""

    def __init__(self, db: Session):
        self.db = db

    def track_onboarding_metrics(
        self,
        user_id: str,
        onboarding_data: Dict[str, Any],
        personalization_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Track comprehensive onboarding performance metrics."""
        try:
            metrics = {
                "user_id": user_id,
                "basic_metrics": self._collect_basic_metrics(onboarding_data),
                "engagement_metrics": self._collect_engagement_metrics(onboarding_data),
                "conversion_metrics": self._collect_conversion_metrics(onboarding_data),
                "quality_metrics": self._collect_quality_metrics(onboarding_data),
                "personalization_metrics": self._collect_personalization_metrics(
                    onboarding_data, personalization_context
                ),
                "business_metrics": self._collect_business_metrics(onboarding_data),
                "tracked_at": datetime.utcnow().isoformat(),
            }

            # Calculate composite scores
            metrics["composite_scores"] = self._calculate_composite_scores(metrics)

            # Log metrics for analytics pipeline
            self._log_metrics(metrics)

            logger.info(f"Performance metrics tracked for user {user_id}")
            return metrics

        except Exception as e:
            logger.error(f"Error tracking performance metrics: {e}")
            return {}

    def _collect_basic_metrics(self, onboarding_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collect basic onboarding metrics."""
        return {
            "completion_rate": 1.0 if onboarding_data.get("completed", False) else 0.0,
            "total_time_seconds": onboarding_data.get("total_duration_seconds", 0),
            "steps_completed": len(onboarding_data.get("completed_steps", [])),
            "steps_total": 5,  # Standard onboarding steps
            "error_count": len(onboarding_data.get("errors", [])),
            "retry_count": onboarding_data.get("retry_attempts", 0),
            "help_requests": len(
                [
                    i
                    for i in onboarding_data.get("interactions", [])
                    if i.get("type") == "help_request"
                ]
            ),
        }

    def _collect_engagement_metrics(
        self, onboarding_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect user engagement metrics."""
        interactions = onboarding_data.get("interactions", [])

        # Count interaction types
        interaction_counts = defaultdict(int)
        for interaction in interactions:
            interaction_counts[interaction.get("type", "unknown")] += 1

        # Calculate engagement score
        engagement_score = self._calculate_engagement_score(interactions)

        # Time spent per step analysis
        step_timings = onboarding_data.get("step_timings", {})
        avg_step_time = sum(
            timing.get("duration_seconds", 0) for timing in step_timings.values()
        ) / max(len(step_timings), 1)

        return {
            "total_interactions": len(interactions),
            "interaction_types": dict(interaction_counts),
            "engagement_score": engagement_score,
            "avg_step_time_seconds": avg_step_time,
            "session_depth": len(step_timings),
            "exploration_rate": interaction_counts.get("explore", 0)
            / max(len(interactions), 1),
            "bounce_indicators": {
                "quick_exits": interaction_counts.get("exit", 0),
                "back_navigation": interaction_counts.get("navigation_back", 0),
                "skip_actions": interaction_counts.get("skip", 0),
            },
        }

    def _collect_conversion_metrics(
        self, onboarding_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect conversion and funnel metrics."""
        completed_steps = onboarding_data.get("completed_steps", [])
        total_steps = 5

        # Step-by-step conversion rates
        step_conversions = {}
        for step in range(1, total_steps + 1):
            step_conversions[f"step_{step}"] = 1.0 if step in completed_steps else 0.0

        # Funnel analysis
        funnel_completion_rate = len(completed_steps) / total_steps

        # Time-based conversions
        total_time = onboarding_data.get("total_duration_seconds", 0)
        quick_completion = total_time <= 180  # 3 minutes

        return {
            "step_conversions": step_conversions,
            "funnel_completion_rate": funnel_completion_rate,
            "full_completion": len(completed_steps) == total_steps,
            "quick_completion": quick_completion,
            "abandonment_step": self._identify_abandonment_step(completed_steps),
            "conversion_quality": {
                "completed_without_errors": (
                    len(completed_steps) == total_steps
                    and len(onboarding_data.get("errors", [])) == 0
                ),
                "completed_without_help": (
                    len(completed_steps) == total_steps
                    and len(
                        [
                            i
                            for i in onboarding_data.get("interactions", [])
                            if i.get("type") == "help_request"
                        ]
                    )
                    == 0
                ),
            },
        }

    def _collect_quality_metrics(
        self, onboarding_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect data quality and user experience metrics."""
        user_choices = onboarding_data.get("user_choices", {})

        # Choice quality analysis
        categories = user_choices.get("selected_categories", [])
        category_diversity = len(set(categories)) if categories else 0

        # Preference completeness
        preference_fields = ["activity_level", "budget_range", "group_size_preference"]
        preferences_completed = sum(
            1
            for field in preference_fields
            if field in user_choices and user_choices[field]
        )

        return {
            "data_completeness": {
                "categories_selected": len(categories),
                "category_diversity": category_diversity,
                "preferences_completed": preferences_completed,
                "profile_completeness": (len(categories) + preferences_completed)
                / 8,  # Normalize to 8 total fields
            },
            "choice_quality": {
                "appropriate_category_count": 2 <= len(categories) <= 5,
                "balanced_preferences": preferences_completed >= 2,
                "thoughtful_selections": self._assess_thoughtful_selections(
                    onboarding_data
                ),
            },
            "user_satisfaction": {
                "satisfaction_score": onboarding_data.get("satisfaction_score", 0),
                "would_recommend": onboarding_data.get("would_recommend", False),
                "feedback_provided": bool(onboarding_data.get("user_feedback")),
            },
        }

    def _collect_personalization_metrics(
        self,
        onboarding_data: Dict[str, Any],
        personalization_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Collect personalization effectiveness metrics."""
        if not personalization_context:
            return {"personalization_applied": False}

        # Personalization impact analysis
        user_segment = personalization_context.get("user_segment", "default")
        personalization_confidence = personalization_context.get(
            "personalization_confidence", 0
        )

        # Compare against segment benchmarks
        segment_benchmarks = self._get_segment_benchmarks()
        user_performance = self._calculate_user_performance_score(onboarding_data)

        benchmark_performance = segment_benchmarks.get(user_segment, {}).get(
            "avg_performance", 0.7
        )
        personalization_lift = user_performance - benchmark_performance

        return {
            "personalization_applied": True,
            "user_segment": user_segment,
            "personalization_confidence": personalization_confidence,
            "segment_benchmarks": segment_benchmarks.get(user_segment, {}),
            "user_performance_score": user_performance,
            "personalization_lift": personalization_lift,
            "personalization_effectiveness": {
                "positive_impact": personalization_lift > 0.05,
                "significant_impact": abs(personalization_lift) > 0.1,
                "confidence_alignment": (
                    personalization_confidence > 0.7 and personalization_lift > 0
                )
                or (
                    personalization_confidence < 0.3 and abs(personalization_lift) < 0.1
                ),
            },
        }

    def _collect_business_metrics(
        self, onboarding_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect business impact metrics."""
        completed = onboarding_data.get("completed", False)
        total_time = onboarding_data.get("total_duration_seconds", 0)

        # Business value calculations
        completion_value = 100 if completed else 0  # Base value for completion
        efficiency_bonus = max(0, 50 - (total_time / 60) * 10)  # Efficiency bonus
        quality_bonus = self._calculate_quality_bonus(onboarding_data)

        total_business_value = completion_value + efficiency_bonus + quality_bonus

        return {
            "business_value": {
                "completion_value": completion_value,
                "efficiency_bonus": efficiency_bonus,
                "quality_bonus": quality_bonus,
                "total_value": total_business_value,
            },
            "cost_metrics": {
                "estimated_support_cost": len(onboarding_data.get("errors", []))
                * 2.5,  # $2.5 per error
                "time_investment_minutes": total_time / 60,
                "resource_efficiency": total_business_value / max(total_time / 60, 1),
            },
            "retention_indicators": {
                "positive_first_impression": (
                    completed
                    and total_time <= 300
                    and len(onboarding_data.get("errors", [])) <= 1
                ),
                "feature_discovery": len(
                    onboarding_data.get("features_discovered", [])
                ),
                "engagement_depth": len(onboarding_data.get("interactions", []))
                / max(total_time / 60, 1),
            },
        }

    def _calculate_composite_scores(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate composite performance scores."""
        basic_metrics = metrics.get("basic_metrics", {})
        engagement_metrics = metrics.get("engagement_metrics", {})
        metrics.get("conversion_metrics", {})
        quality_metrics = metrics.get("quality_metrics", {})

        # Overall onboarding score (0-100)
        completion_score = basic_metrics.get("completion_rate", 0) * 40
        efficiency_score = (
            min(300 / max(basic_metrics.get("total_time_seconds", 300), 1), 1) * 30
        )
        quality_score = (
            quality_metrics.get("data_completeness", {}).get("profile_completeness", 0)
            * 20
        )
        engagement_score = engagement_metrics.get("engagement_score", 0) * 10

        overall_score = (
            completion_score + efficiency_score + quality_score + engagement_score
        )

        # Success probability (based on leading indicators)
        success_probability = self._calculate_success_probability(metrics)

        # Risk score (inverse of success indicators)
        risk_score = self._calculate_risk_score(metrics)

        return {
            "overall_onboarding_score": round(overall_score, 2),
            "success_probability": round(success_probability, 3),
            "risk_score": round(risk_score, 3),
            "performance_tier": self._determine_performance_tier(overall_score),
            "score_breakdown": {
                "completion": completion_score,
                "efficiency": efficiency_score,
                "quality": quality_score,
                "engagement": engagement_score,
            },
        }

    def _calculate_engagement_score(self, interactions: List[Dict[str, Any]]) -> float:
        """Calculate user engagement score from interactions."""
        if not interactions:
            return 0.0

        # Weight different interaction types
        interaction_weights = {
            "click": 1.0,
            "form_input": 2.0,
            "selection": 1.5,
            "scroll": 0.5,
            "help_request": 0.5,  # Shows engagement but also confusion
            "skip": -1.0,  # Negative engagement
            "exit": -2.0,  # Strong negative signal
            "explore": 2.5,  # High engagement
            "completion": 3.0,  # Highest positive signal
        }

        weighted_score = 0
        for interaction in interactions:
            interaction_type = interaction.get("type", "unknown")
            weight = interaction_weights.get(interaction_type, 0.5)
            weighted_score += weight

        # Normalize to 0-1 scale based on interaction count
        max_possible_score = len(interactions) * 3.0  # Assuming all completions
        normalized_score = min(weighted_score / max(max_possible_score, 1), 1.0)

        return max(0.0, normalized_score)

    def _identify_abandonment_step(self, completed_steps: List[int]) -> Optional[int]:
        """Identify the step where user abandoned the onboarding."""
        if not completed_steps:
            return 1

        max_completed = max(completed_steps)
        if max_completed < 5:
            return max_completed + 1
        return None  # Completed all steps

    def _assess_thoughtful_selections(self, onboarding_data: Dict[str, Any]) -> bool:
        """Assess if user made thoughtful selections based on timing and patterns."""
        step_timings = onboarding_data.get("step_timings", {})

        # Check if user spent reasonable time on decision steps
        decision_steps = ["step_2", "step_3"]  # Category selection and preferences
        thoughtful_timing = True

        for step in decision_steps:
            if step in step_timings:
                duration = step_timings[step].get("duration_seconds", 0)
                if duration < 15:  # Less than 15 seconds seems rushed
                    thoughtful_timing = False
                    break

        # Check choice diversity
        user_choices = onboarding_data.get("user_choices", {})
        categories = user_choices.get("selected_categories", [])
        has_diverse_choices = len(set(categories)) >= 2 if categories else False

        return thoughtful_timing and has_diverse_choices

    def _get_segment_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """Get performance benchmarks for different user segments."""
        return {
            "tech_savvy": {
                "avg_performance": 0.85,
                "avg_completion_time": 150,
                "avg_completion_rate": 0.87,
            },
            "casual_user": {
                "avg_performance": 0.68,
                "avg_completion_time": 285,
                "avg_completion_rate": 0.72,
            },
            "visual_learner": {
                "avg_performance": 0.75,
                "avg_completion_time": 230,
                "avg_completion_rate": 0.78,
            },
            "goal_oriented": {
                "avg_performance": 0.82,
                "avg_completion_time": 135,
                "avg_completion_rate": 0.90,
            },
            "social_user": {
                "avg_performance": 0.73,
                "avg_completion_time": 195,
                "avg_completion_rate": 0.80,
            },
        }

    def _calculate_user_performance_score(
        self, onboarding_data: Dict[str, Any]
    ) -> float:
        """Calculate overall user performance score."""
        # Normalize key metrics to 0-1 scale
        completion = 1.0 if onboarding_data.get("completed", False) else 0.0

        time_efficiency = min(
            300 / max(onboarding_data.get("total_duration_seconds", 300), 1), 1.0
        )

        error_penalty = max(0, 1 - (len(onboarding_data.get("errors", [])) * 0.1))

        # Weighted average
        performance_score = (
            (completion * 0.5) + (time_efficiency * 0.3) + (error_penalty * 0.2)
        )

        return min(performance_score, 1.0)

    def _calculate_quality_bonus(self, onboarding_data: Dict[str, Any]) -> float:
        """Calculate quality bonus for business metrics."""
        bonus = 0.0

        # Bonus for error-free completion
        if len(onboarding_data.get("errors", [])) == 0:
            bonus += 20

        # Bonus for thoughtful selections
        if self._assess_thoughtful_selections(onboarding_data):
            bonus += 15

        # Bonus for high satisfaction
        satisfaction = onboarding_data.get("satisfaction_score", 0)
        if satisfaction >= 4:
            bonus += 10

        return bonus

    def _calculate_success_probability(self, metrics: Dict[str, Any]) -> float:
        """Calculate probability of successful onboarding outcome."""
        # Use various metrics to predict success
        basic_metrics = metrics.get("basic_metrics", {})
        engagement_metrics = metrics.get("engagement_metrics", {})
        conversion_metrics = metrics.get("conversion_metrics", {})

        factors = []

        # Completion factor
        if basic_metrics.get("completion_rate", 0) == 1.0:
            factors.append(0.4)

        # Time efficiency factor
        time_seconds = basic_metrics.get("total_time_seconds", 0)
        if time_seconds <= 180:
            factors.append(0.2)
        elif time_seconds <= 300:
            factors.append(0.1)

        # Engagement factor
        if engagement_metrics.get("engagement_score", 0) > 0.6:
            factors.append(0.2)

        # Error factor
        if basic_metrics.get("error_count", 0) == 0:
            factors.append(0.1)

        # Quality factor
        funnel_rate = conversion_metrics.get("funnel_completion_rate", 0)
        if funnel_rate >= 0.8:
            factors.append(0.1)

        return sum(factors)

    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate risk score for onboarding failure."""
        basic_metrics = metrics.get("basic_metrics", {})
        engagement_metrics = metrics.get("engagement_metrics", {})

        risk_factors = []

        # High error count
        error_count = basic_metrics.get("error_count", 0)
        if error_count > 3:
            risk_factors.append(0.3)
        elif error_count > 1:
            risk_factors.append(0.15)

        # Low engagement
        engagement_score = engagement_metrics.get("engagement_score", 0)
        if engagement_score < 0.3:
            risk_factors.append(0.25)

        # Excessive time
        time_seconds = basic_metrics.get("total_time_seconds", 0)
        if time_seconds > 600:  # 10 minutes
            risk_factors.append(0.2)

        # High bounce indicators
        bounce_indicators = engagement_metrics.get("bounce_indicators", {})
        if bounce_indicators.get("quick_exits", 0) > 0:
            risk_factors.append(0.15)

        # Many help requests
        if basic_metrics.get("help_requests", 0) > 2:
            risk_factors.append(0.1)

        return sum(risk_factors)

    def _determine_performance_tier(self, overall_score: float) -> str:
        """Determine performance tier based on overall score."""
        if overall_score >= 90:
            return "excellent"
        elif overall_score >= 75:
            return "good"
        elif overall_score >= 60:
            return "average"
        elif overall_score >= 40:
            return "below_average"
        else:
            return "poor"

    def _log_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log metrics for analytics pipeline."""
        try:
            logger.info(f"PERFORMANCE_METRICS: {json.dumps(metrics, default=str)}")
        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")


class MetricsAggregator:
    """Aggregator for performance metrics across multiple users and time periods."""

    def __init__(self, db: Session):
        self.db = db

    def generate_performance_dashboard(
        self, time_period_days: int = 30, segment_breakdown: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive performance dashboard data."""
        try:
            # Mock dashboard data - in production would query actual metrics
            dashboard_data = {
                "time_period": f"{time_period_days} days",
                "overview_metrics": {
                    "total_users": 5247,
                    "completion_rate": 0.746,
                    "avg_completion_time_minutes": 4.8,
                    "avg_onboarding_score": 73.2,
                    "success_probability": 0.721,
                    "risk_score": 0.089,
                },
                "trend_analysis": {
                    "completion_rate_trend": "+3.2%",  # vs previous period
                    "efficiency_trend": "-8.5%",  # Time reduction
                    "quality_trend": "+1.8%",
                    "engagement_trend": "+5.1%",
                },
                "performance_distribution": {
                    "excellent": 0.18,  # 18% of users
                    "good": 0.31,  # 31% of users
                    "average": 0.28,  # 28% of users
                    "below_average": 0.15,  # 15% of users
                    "poor": 0.08,  # 8% of users
                },
                "bottleneck_analysis": {
                    "highest_dropout_step": 2,  # Category selection
                    "longest_average_step": 3,  # Preference setup
                    "most_error_prone_step": 2,
                    "improvement_opportunities": [
                        "Simplify category selection interface",
                        "Add progress indicators to preference setup",
                        "Implement smart defaults based on user segment",
                    ],
                },
            }

            # Add segment breakdown if requested
            if segment_breakdown:
                dashboard_data["segment_performance"] = {
                    "tech_savvy": {
                        "users": 945,
                        "completion_rate": 0.87,
                        "avg_score": 84.2,
                        "avg_time_minutes": 2.5,
                    },
                    "casual_user": {
                        "users": 2098,
                        "completion_rate": 0.68,
                        "avg_score": 65.4,
                        "avg_time_minutes": 6.8,
                    },
                    "visual_learner": {
                        "users": 787,
                        "completion_rate": 0.74,
                        "avg_score": 72.1,
                        "avg_time_minutes": 5.2,
                    },
                    "goal_oriented": {
                        "users": 673,
                        "completion_rate": 0.90,
                        "avg_score": 86.7,
                        "avg_time_minutes": 2.3,
                    },
                    "social_user": {
                        "users": 744,
                        "completion_rate": 0.80,
                        "avg_score": 75.8,
                        "avg_time_minutes": 3.9,
                    },
                }

            dashboard_data["generated_at"] = datetime.utcnow().isoformat()

            logger.info(f"Performance dashboard generated for {time_period_days} days")
            return dashboard_data

        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            return {}
