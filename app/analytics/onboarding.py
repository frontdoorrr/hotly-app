"""Onboarding analytics and user behavior analysis."""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OnboardingAnalytics:
    """Analytics service for onboarding behavior and optimization."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_user_behavior_patterns(
        self, user_id: str, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze individual user behavior patterns during onboarding."""
        try:
            behavior_analysis = {
                "user_id": user_id,
                "session_analysis": self._analyze_session_behavior(session_data),
                "engagement_patterns": self._analyze_engagement_patterns(session_data),
                "decision_patterns": self._analyze_decision_patterns(session_data),
                "struggle_indicators": self._identify_struggle_indicators(session_data),
                "efficiency_metrics": self._calculate_efficiency_metrics(session_data),
                "personalization_insights": self._extract_personalization_insights(
                    session_data
                ),
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"User behavior analysis completed for {user_id}")
            return behavior_analysis

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")
            return {}

    def _analyze_session_behavior(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall session behavior patterns."""
        try:
            interactions = session_data.get("interactions", [])
            step_timings = session_data.get("step_timings", {})

            # Calculate session metrics
            total_interactions = len(interactions)
            session_duration = session_data.get("total_duration_seconds", 0)

            # Interaction patterns
            interaction_types = defaultdict(int)
            for interaction in interactions:
                interaction_types[interaction.get("type", "unknown")] += 1

            # Timing analysis
            step_durations = []
            for step, timing in step_timings.items():
                duration = timing.get("duration_seconds", 0)
                if duration > 0:
                    step_durations.append(duration)

            avg_step_duration = (
                sum(step_durations) / len(step_durations) if step_durations else 0
            )

            return {
                "total_interactions": total_interactions,
                "session_duration": session_duration,
                "interaction_rate": total_interactions
                / max(session_duration / 60, 1),  # interactions per minute
                "interaction_types": dict(interaction_types),
                "step_timing": {
                    "average_step_duration": avg_step_duration,
                    "longest_step_duration": (
                        max(step_durations) if step_durations else 0
                    ),
                    "shortest_step_duration": (
                        min(step_durations) if step_durations else 0
                    ),
                    "step_duration_variance": self._calculate_variance(step_durations),
                },
            }

        except Exception as e:
            logger.error(f"Error analyzing session behavior: {e}")
            return {}

    def _analyze_engagement_patterns(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user engagement patterns during onboarding."""
        try:
            interactions = session_data.get("interactions", [])

            # Engagement indicators
            engagement_indicators = {
                "scroll_events": 0,
                "click_events": 0,
                "form_interactions": 0,
                "help_requests": 0,
                "back_navigation": 0,
                "skip_actions": 0,
                "exploration_actions": 0,
            }

            for interaction in interactions:
                interaction_type = interaction.get("type", "")

                if interaction_type == "scroll":
                    engagement_indicators["scroll_events"] += 1
                elif interaction_type == "click":
                    engagement_indicators["click_events"] += 1
                elif interaction_type == "form_input":
                    engagement_indicators["form_interactions"] += 1
                elif interaction_type == "help_request":
                    engagement_indicators["help_requests"] += 1
                elif interaction_type == "navigation_back":
                    engagement_indicators["back_navigation"] += 1
                elif interaction_type == "skip":
                    engagement_indicators["skip_actions"] += 1
                elif interaction_type in ["explore", "optional_action"]:
                    engagement_indicators["exploration_actions"] += 1

            # Calculate engagement score
            engagement_score = self._calculate_engagement_score(engagement_indicators)

            # Identify engagement level
            if engagement_score > 0.8:
                engagement_level = "high"
            elif engagement_score > 0.5:
                engagement_level = "medium"
            else:
                engagement_level = "low"

            return {
                "engagement_indicators": engagement_indicators,
                "engagement_score": engagement_score,
                "engagement_level": engagement_level,
                "interaction_diversity": len(
                    [k for k, v in engagement_indicators.items() if v > 0]
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing engagement patterns: {e}")
            return {}

    def _analyze_decision_patterns(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze user decision-making patterns."""
        try:
            choices = session_data.get("user_choices", {})
            decision_times = session_data.get("decision_times", {})

            decision_analysis = {
                "choice_distribution": {},
                "decision_speed": {},
                "choice_confidence": {},
                "revision_patterns": {},
            }

            # Analyze choice distribution
            for choice_type, choice_value in choices.items():
                if isinstance(choice_value, list):
                    decision_analysis["choice_distribution"][choice_type] = {
                        "count": len(choice_value),
                        "diversity": len(set(choice_value)) if choice_value else 0,
                    }
                else:
                    decision_analysis["choice_distribution"][choice_type] = {
                        "value": choice_value,
                        "type": type(choice_value).__name__,
                    }

            # Analyze decision speed
            for decision_point, time_taken in decision_times.items():
                if time_taken < 10:
                    speed_category = "very_fast"
                elif time_taken < 30:
                    speed_category = "fast"
                elif time_taken < 60:
                    speed_category = "moderate"
                else:
                    speed_category = "slow"

                decision_analysis["decision_speed"][decision_point] = {
                    "time_seconds": time_taken,
                    "speed_category": speed_category,
                }

            # Calculate overall decision confidence
            avg_decision_time = (
                sum(decision_times.values()) / len(decision_times)
                if decision_times
                else 0
            )
            decision_confidence = max(
                0, 1 - (avg_decision_time / 120)
            )  # Normalize to 120 seconds
            decision_analysis["overall_decision_confidence"] = decision_confidence

            return decision_analysis

        except Exception as e:
            logger.error(f"Error analyzing decision patterns: {e}")
            return {}

    def _identify_struggle_indicators(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify indicators of user struggle during onboarding."""
        try:
            indicators = {
                "error_indicators": [],
                "confusion_indicators": [],
                "frustration_indicators": [],
                "abandonment_risk_factors": [],
            }

            # Error patterns
            errors = session_data.get("errors", [])
            if len(errors) > 2:
                indicators["error_indicators"].append(
                    {
                        "type": "repeated_errors",
                        "count": len(errors),
                        "severity": "high" if len(errors) > 5 else "medium",
                    }
                )

            # Long delays between steps
            step_timings = session_data.get("step_timings", {})
            for step, timing in step_timings.items():
                duration = timing.get("duration_seconds", 0)
                if duration > 180:  # More than 3 minutes
                    indicators["confusion_indicators"].append(
                        {
                            "type": "prolonged_step_duration",
                            "step": step,
                            "duration": duration,
                            "severity": "high" if duration > 300 else "medium",
                        }
                    )

            # Multiple help requests
            interactions = session_data.get("interactions", [])
            help_requests = [i for i in interactions if i.get("type") == "help_request"]
            if len(help_requests) > 1:
                indicators["frustration_indicators"].append(
                    {
                        "type": "multiple_help_requests",
                        "count": len(help_requests),
                        "severity": "medium",
                    }
                )

            # Back navigation patterns
            back_navigation = [
                i for i in interactions if i.get("type") == "navigation_back"
            ]
            if len(back_navigation) > 3:
                indicators["frustration_indicators"].append(
                    {
                        "type": "excessive_back_navigation",
                        "count": len(back_navigation),
                        "severity": "medium",
                    }
                )

            # Calculate struggle score
            struggle_score = self._calculate_struggle_score(indicators)

            return {
                "struggle_indicators": indicators,
                "struggle_score": struggle_score,
                "risk_level": (
                    "high"
                    if struggle_score > 0.7
                    else "medium" if struggle_score > 0.4 else "low"
                ),
            }

        except Exception as e:
            logger.error(f"Error identifying struggle indicators: {e}")
            return {}

    def _calculate_efficiency_metrics(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate efficiency metrics for the onboarding session."""
        try:
            total_duration = session_data.get("total_duration_seconds", 0)
            steps_completed = len(session_data.get("completed_steps", []))
            total_steps = 5  # Standard onboarding steps

            # Basic efficiency metrics
            completion_rate = steps_completed / total_steps
            time_efficiency = max(
                0, 1 - (total_duration / 300)
            )  # Normalize to 5 minutes

            # Interaction efficiency
            interactions = session_data.get("interactions", [])
            productive_interactions = [
                i
                for i in interactions
                if i.get("type") in ["form_input", "selection", "completion"]
            ]

            interaction_efficiency = (
                len(productive_interactions) / max(len(interactions), 1)
                if interactions
                else 0
            )

            # Overall efficiency score
            efficiency_score = (
                completion_rate * 0.4
                + time_efficiency * 0.3
                + interaction_efficiency * 0.3
            )

            return {
                "completion_rate": completion_rate,
                "time_efficiency": time_efficiency,
                "interaction_efficiency": interaction_efficiency,
                "overall_efficiency": efficiency_score,
                "steps_per_minute": steps_completed / max(total_duration / 60, 1),
                "interactions_per_step": len(interactions) / max(steps_completed, 1),
            }

        except Exception as e:
            logger.error(f"Error calculating efficiency metrics: {e}")
            return {}

    def _extract_personalization_insights(
        self, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract insights for improving personalization."""
        try:
            insights = {
                "user_segment_indicators": [],
                "preference_signals": {},
                "behavioral_traits": [],
                "optimization_opportunities": [],
            }

            # Analyze speed of progression
            step_timings = session_data.get("step_timings", {})
            avg_step_time = sum(
                timing.get("duration_seconds", 0) for timing in step_timings.values()
            ) / max(len(step_timings), 1)

            if avg_step_time < 30:
                insights["behavioral_traits"].append("fast_navigator")
                insights["user_segment_indicators"].append("tech_savvy")
            elif avg_step_time > 90:
                insights["behavioral_traits"].append("careful_reader")
                insights["user_segment_indicators"].append("casual_user")

            # Analyze help-seeking behavior
            interactions = session_data.get("interactions", [])
            help_requests = [i for i in interactions if i.get("type") == "help_request"]

            if len(help_requests) == 0:
                insights["behavioral_traits"].append("self_sufficient")
            elif len(help_requests) > 2:
                insights["behavioral_traits"].append("guidance_seeking")

            # Analyze choice patterns
            choices = session_data.get("user_choices", {})
            categories = choices.get("selected_categories", [])

            if len(categories) > 3:
                insights["preference_signals"]["category_explorer"] = True
            elif len(categories) <= 2:
                insights["preference_signals"]["focused_user"] = True

            # Generate optimization opportunities
            if "fast_navigator" in insights["behavioral_traits"]:
                insights["optimization_opportunities"].append(
                    {
                        "type": "interface_optimization",
                        "suggestion": "Enable quick setup mode",
                        "priority": "high",
                    }
                )

            if "guidance_seeking" in insights["behavioral_traits"]:
                insights["optimization_opportunities"].append(
                    {
                        "type": "content_optimization",
                        "suggestion": "Add more contextual help",
                        "priority": "medium",
                    }
                )

            return insights

        except Exception as e:
            logger.error(f"Error extracting personalization insights: {e}")
            return {}

    def _calculate_engagement_score(self, indicators: Dict[str, int]) -> float:
        """Calculate overall engagement score from indicators."""
        try:
            # Weighted scoring for different interaction types
            weights = {
                "scroll_events": 0.1,
                "click_events": 0.2,
                "form_interactions": 0.3,
                "help_requests": 0.1,
                "back_navigation": -0.1,  # Negative weight
                "skip_actions": -0.15,  # Negative weight
                "exploration_actions": 0.25,
            }

            weighted_score = 0
            max_possible_score = 0

            for indicator, count in indicators.items():
                weight = weights.get(indicator, 0)
                if weight > 0:
                    # Normalize count to reasonable range
                    normalized_count = min(count / 10, 1)
                    weighted_score += normalized_count * weight
                    max_possible_score += weight
                else:
                    # Penalty for negative behaviors
                    penalty = min(count / 5, 1) * abs(weight)
                    weighted_score -= penalty

            # Normalize to 0-1 range
            if max_possible_score > 0:
                engagement_score = max(0, weighted_score / max_possible_score)
            else:
                engagement_score = 0

            return min(engagement_score, 1.0)

        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    def _calculate_struggle_score(self, indicators: Dict[str, List]) -> float:
        """Calculate overall struggle score from indicators."""
        try:
            total_indicators = 0
            weighted_struggle = 0

            weights = {
                "error_indicators": 0.4,
                "confusion_indicators": 0.3,
                "frustration_indicators": 0.2,
                "abandonment_risk_factors": 0.1,
            }

            for indicator_type, indicator_list in indicators.items():
                weight = weights.get(indicator_type, 0.1)

                for indicator in indicator_list:
                    severity = indicator.get("severity", "low")
                    severity_multiplier = {"low": 0.3, "medium": 0.6, "high": 1.0}.get(
                        severity, 0.3
                    )

                    weighted_struggle += weight * severity_multiplier
                    total_indicators += 1

            # Normalize struggle score
            if total_indicators > 0:
                struggle_score = min(weighted_struggle / total_indicators, 1.0)
            else:
                struggle_score = 0.0

            return struggle_score

        except Exception as e:
            logger.error(f"Error calculating struggle score: {e}")
            return 0.0

    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if not values or len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance

    def generate_cohort_analysis(
        self, cohort_period_days: int = 30, user_segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate cohort analysis for onboarding performance."""
        try:
            # Mock cohort analysis - in production, this would query actual data
            cohort_analysis = {
                "analysis_period": f"{cohort_period_days} days",
                "user_segment": user_segment or "all",
                "cohort_size": 2500,  # Mock data
                "completion_rates": {
                    "day_0": 1.0,  # All users start
                    "day_1": 0.85,  # 85% complete within 24h
                    "day_3": 0.78,  # 78% complete within 3 days
                    "day_7": 0.72,  # 72% complete within 1 week
                    "day_30": 0.70,  # Final completion rate
                },
                "time_to_completion": {
                    "median_minutes": 4.2,
                    "p75_minutes": 7.8,
                    "p90_minutes": 15.6,
                    "p95_minutes": 28.4,
                },
                "drop_off_analysis": {
                    "step_1_dropout": 0.05,  # 5% drop at step 1
                    "step_2_dropout": 0.08,  # 8% drop at step 2
                    "step_3_dropout": 0.04,  # 4% drop at step 3
                    "step_4_dropout": 0.02,  # 2% drop at step 4
                    "step_5_dropout": 0.01,  # 1% drop at step 5
                },
                "segment_comparison": {
                    "tech_savvy": {
                        "completion_rate": 0.87,
                        "avg_time_minutes": 3.1,
                        "satisfaction_score": 4.2,
                    },
                    "casual_user": {
                        "completion_rate": 0.68,
                        "avg_time_minutes": 6.8,
                        "satisfaction_score": 3.9,
                    },
                    "visual_learner": {
                        "completion_rate": 0.74,
                        "avg_time_minutes": 5.2,
                        "satisfaction_score": 4.1,
                    },
                },
                "trends": {
                    "completion_rate_trend": "stable",  # +2% vs previous period
                    "time_efficiency_trend": "improving",  # -8% avg time
                    "satisfaction_trend": "stable",  # +0.1 score
                },
                "insights": [
                    "Step 2 (category selection) has highest dropout rate",
                    "Tech savvy users complete 2x faster than casual users",
                    "Visual learners show improved completion when images added",
                    "Weekend completion rates 15% lower than weekdays",
                ],
                "recommendations": [
                    "Simplify category selection interface",
                    "Add progressive disclosure for casual users",
                    "Implement time-of-day based optimizations",
                    "A/B test visual elements for all segments",
                ],
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Cohort analysis generated for {cohort_period_days} days")
            return cohort_analysis

        except Exception as e:
            logger.error(f"Error generating cohort analysis: {e}")
            return {}

    def track_optimization_impact(
        self,
        optimization_id: str,
        before_metrics: Dict[str, Any],
        after_metrics: Dict[str, Any],
        time_period_days: int = 30,
    ) -> Dict[str, Any]:
        """Track impact of optimization changes."""
        try:
            impact_analysis = {
                "optimization_id": optimization_id,
                "analysis_period": f"{time_period_days} days",
                "before_period": before_metrics,
                "after_period": after_metrics,
                "impact_metrics": {},
                "statistical_significance": {},
                "business_impact": {},
            }

            # Calculate percentage changes
            for metric in ["completion_rate", "avg_time_minutes", "satisfaction_score"]:
                before_value = before_metrics.get(metric, 0)
                after_value = after_metrics.get(metric, 0)

                if before_value > 0:
                    percentage_change = (
                        (after_value - before_value) / before_value
                    ) * 100
                    impact_analysis["impact_metrics"][metric] = {
                        "before": before_value,
                        "after": after_value,
                        "absolute_change": after_value - before_value,
                        "percentage_change": percentage_change,
                        "improvement": (
                            percentage_change > 0
                            if metric != "avg_time_minutes"
                            else percentage_change < 0
                        ),
                    }

            # Mock statistical significance (would use proper tests in production)
            for metric, impact in impact_analysis["impact_metrics"].items():
                abs_change = abs(impact["percentage_change"])
                if abs_change > 10:
                    significance = {
                        "significant": True,
                        "confidence": 0.95,
                        "p_value": 0.01,
                    }
                elif abs_change > 5:
                    significance = {
                        "significant": True,
                        "confidence": 0.90,
                        "p_value": 0.05,
                    }
                else:
                    significance = {
                        "significant": False,
                        "confidence": 0.50,
                        "p_value": 0.25,
                    }

                impact_analysis["statistical_significance"][metric] = significance

            # Business impact calculation
            completion_rate_change = (
                impact_analysis["impact_metrics"]
                .get("completion_rate", {})
                .get("percentage_change", 0)
            )
            estimated_monthly_users = 10000

            impact_analysis["business_impact"] = {
                "additional_completions_per_month": int(
                    estimated_monthly_users * (completion_rate_change / 100)
                ),
                "estimated_revenue_impact": estimated_monthly_users
                * (completion_rate_change / 100)
                * 25,  # $25 per conversion
                "user_experience_improvement": (
                    "positive" if completion_rate_change > 0 else "neutral"
                ),
            }

            logger.info(f"Optimization impact tracked for {optimization_id}")
            return impact_analysis

        except Exception as e:
            logger.error(f"Error tracking optimization impact: {e}")
            return {}
