"""Onboarding personalization and optimization service."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OnboardingPersonalizationEngine:
    """Engine for personalizing onboarding experience based on user behavior."""

    def __init__(self, db: Session):
        self.db = db
        self.personalization_rules = self._load_personalization_rules()

    def _load_personalization_rules(self) -> Dict[str, Any]:
        """Load personalization rules and configurations."""
        return {
            "user_segments": {
                "tech_savvy": {
                    "characteristics": [
                        "quick_navigation",
                        "skip_tutorials",
                        "advanced_features",
                    ],
                    "onboarding_adjustments": {
                        "reduce_explanation_text": True,
                        "enable_quick_setup": True,
                        "show_advanced_options": True,
                        "skip_basic_tutorials": True,
                    },
                },
                "casual_user": {
                    "characteristics": [
                        "slow_navigation",
                        "needs_guidance",
                        "basic_features",
                    ],
                    "onboarding_adjustments": {
                        "increase_explanation_text": True,
                        "enable_step_by_step": True,
                        "show_progress_indicators": True,
                        "add_helpful_tips": True,
                    },
                },
                "visual_learner": {
                    "characteristics": [
                        "image_focused",
                        "video_engagement",
                        "visual_cues",
                    ],
                    "onboarding_adjustments": {
                        "emphasize_visual_content": True,
                        "add_screenshots": True,
                        "use_animations": True,
                        "reduce_text_density": True,
                    },
                },
                "goal_oriented": {
                    "characteristics": [
                        "task_focused",
                        "efficiency_seeking",
                        "outcome_driven",
                    ],
                    "onboarding_adjustments": {
                        "show_clear_outcomes": True,
                        "emphasize_benefits": True,
                        "use_progress_tracking": True,
                        "highlight_achievements": True,
                    },
                },
                "social_user": {
                    "characteristics": [
                        "sharing_behavior",
                        "social_features",
                        "community_engagement",
                    ],
                    "onboarding_adjustments": {
                        "highlight_social_features": True,
                        "show_sharing_options": True,
                        "emphasize_community": True,
                        "add_social_proof": True,
                    },
                },
            },
            "behavioral_triggers": {
                "quick_progression": {
                    "condition": "step_completion_time < 30",
                    "adjustment": "reduce_content_density",
                },
                "hesitation_detected": {
                    "condition": "step_completion_time > 120",
                    "adjustment": "add_guidance_hints",
                },
                "repeated_errors": {
                    "condition": "error_count > 2",
                    "adjustment": "simplify_interface",
                },
                "high_engagement": {
                    "condition": "interaction_score > 0.8",
                    "adjustment": "show_advanced_features",
                },
            },
            "content_variants": {
                "welcome_messages": [
                    "안녕하세요! 핫플레이스 발견의 여정을 시작해볼까요?",
                    "환영합니다! 당신만의 특별한 장소를 찾아보세요.",
                    "반갑습니다! 개인화된 추천을 위해 몇 가지 설정을 해보겠습니다.",
                    "어서 오세요! 맞춤형 장소 추천을 준비했습니다.",
                ],
                "category_descriptions": {
                    "short": "카테고리를 선택해주세요",
                    "medium": "관심있는 장소 유형을 2-5개 선택해주세요",
                    "detailed": "어떤 종류의 장소에 관심이 있나요? 맞춤 추천을 위해 2-5개의 카테고리를 선택해주세요.",
                },
                "completion_messages": [
                    "축하합니다! 이제 개인화된 추천을 받을 준비가 되었습니다.",
                    "완료! 당신의 취향에 맞는 장소들을 찾아드릴게요.",
                    "설정 완료! 지금 바로 맞춤 추천을 확인해보세요.",
                ],
            },
        }

    def get_personalized_onboarding_flow(
        self, user_id: str, user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate personalized onboarding flow based on user profile and context."""
        try:
            # Analyze user segment
            user_segment = self._determine_user_segment(user_id, user_context)

            # Get segment-specific adjustments
            adjustments = (
                self.personalization_rules["user_segments"]
                .get(user_segment, {})
                .get("onboarding_adjustments", {})
            )

            # Generate personalized content
            personalized_content = self._generate_personalized_content(
                user_segment, adjustments
            )

            # Determine optimal flow structure
            flow_structure = self._optimize_flow_structure(user_segment, adjustments)

            personalized_flow = {
                "user_id": user_id,
                "user_segment": user_segment,
                "personalization_applied": True,
                "flow_structure": flow_structure,
                "personalized_content": personalized_content,
                "adjustments": adjustments,
                "estimated_completion_time": self._estimate_completion_time(
                    user_segment
                ),
                "personalization_confidence": self._calculate_personalization_confidence(
                    user_context
                ),
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Personalized onboarding flow generated for user {user_id} (segment: {user_segment})"
            )
            return personalized_flow

        except Exception as e:
            logger.error(f"Failed to generate personalized onboarding: {e}")
            return self._get_default_onboarding_flow(user_id)

    def _determine_user_segment(
        self, user_id: str, user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine user segment based on available data and context."""
        try:
            # Default to casual_user if no context available
            if not user_context:
                return "casual_user"

            # Analyze behavioral indicators
            behavioral_score = self._calculate_behavioral_score(user_context)

            # Device and platform indicators
            device_info = user_context.get("device_info", {})
            device_info.get("platform", "unknown")

            # Referral source analysis
            user_context.get("referral_source", "unknown")

            # Segment determination logic
            if behavioral_score.get("tech_savvy_score", 0) > 0.7:
                return "tech_savvy"
            elif behavioral_score.get("visual_preference_score", 0) > 0.6:
                return "visual_learner"
            elif behavioral_score.get("social_engagement_score", 0) > 0.6:
                return "social_user"
            elif behavioral_score.get("goal_orientation_score", 0) > 0.7:
                return "goal_oriented"
            else:
                return "casual_user"

        except Exception as e:
            logger.error(f"Failed to determine user segment: {e}")
            return "casual_user"

    def _calculate_behavioral_score(
        self, user_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate behavioral scores for segment classification."""
        scores = {
            "tech_savvy_score": 0.0,
            "visual_preference_score": 0.0,
            "social_engagement_score": 0.0,
            "goal_orientation_score": 0.0,
        }

        # Analyze device sophistication
        device_info = user_context.get("device_info", {})
        if device_info.get("platform") == "ios" and device_info.get(
            "app_version", ""
        ).endswith("beta"):
            scores["tech_savvy_score"] += 0.3

        # Analyze referral patterns
        referral_source = user_context.get("referral_source", "")
        if referral_source in ["developer_community", "tech_blog", "hackernews"]:
            scores["tech_savvy_score"] += 0.4
        elif referral_source in ["instagram", "tiktok", "pinterest"]:
            scores["visual_preference_score"] += 0.5
        elif referral_source in ["facebook", "twitter", "friend_referral"]:
            scores["social_engagement_score"] += 0.4

        # Analyze stated goals or preferences
        user_goals = user_context.get("stated_goals", [])
        if "efficiency" in user_goals or "productivity" in user_goals:
            scores["goal_orientation_score"] += 0.6

        return scores

    def _generate_personalized_content(
        self, user_segment: str, adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized content based on user segment and adjustments."""
        content_variants = self.personalization_rules["content_variants"]

        # Select appropriate welcome message
        welcome_messages = content_variants["welcome_messages"]
        welcome_message = welcome_messages[0]  # Default

        if user_segment == "tech_savvy":
            welcome_message = welcome_messages[2]  # More direct
        elif user_segment == "visual_learner":
            welcome_message = welcome_messages[1]  # Visual focus
        elif user_segment == "social_user":
            welcome_message = welcome_messages[3]  # Community focus

        # Select category description length
        category_descriptions = content_variants["category_descriptions"]
        if adjustments.get("reduce_explanation_text"):
            category_description = category_descriptions["short"]
        elif adjustments.get("increase_explanation_text"):
            category_description = category_descriptions["detailed"]
        else:
            category_description = category_descriptions["medium"]

        # Select completion message
        completion_messages = content_variants["completion_messages"]
        completion_message = completion_messages[0]  # Default

        if user_segment == "goal_oriented":
            completion_message = completion_messages[2]  # Action-oriented

        return {
            "welcome_message": welcome_message,
            "category_description": category_description,
            "completion_message": completion_message,
            "content_tone": self._determine_content_tone(user_segment),
            "visual_elements": self._determine_visual_elements(
                user_segment, adjustments
            ),
        }

    def _optimize_flow_structure(
        self, user_segment: str, adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize onboarding flow structure based on user segment."""
        base_flow = {
            "step_order": [1, 2, 3, 4, 5],
            "optional_steps": [],
            "progress_indicators": True,
            "step_transitions": "standard",
        }

        # Apply segment-specific optimizations
        if adjustments.get("enable_quick_setup"):
            base_flow["quick_setup_option"] = True
            base_flow["optional_steps"] = [4]  # Make sample guide optional

        if adjustments.get("enable_step_by_step"):
            base_flow["step_transitions"] = "guided"
            base_flow["confirmation_required"] = True

        if adjustments.get("skip_basic_tutorials"):
            base_flow["tutorial_level"] = "minimal"

        if adjustments.get("show_progress_indicators"):
            base_flow["progress_indicators"] = True
            base_flow["progress_style"] = "detailed"

        return base_flow

    def _determine_content_tone(self, user_segment: str) -> str:
        """Determine appropriate content tone for user segment."""
        tone_mapping = {
            "tech_savvy": "professional",
            "casual_user": "friendly",
            "visual_learner": "descriptive",
            "goal_oriented": "direct",
            "social_user": "enthusiastic",
        }
        return tone_mapping.get(user_segment, "friendly")

    def _determine_visual_elements(
        self, user_segment: str, adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine visual elements to include based on personalization."""
        visual_config = {
            "use_animations": False,
            "show_screenshots": False,
            "emphasize_visual_content": False,
            "progress_visualization": "basic",
        }

        if adjustments.get("emphasize_visual_content"):
            visual_config.update(
                {
                    "use_animations": True,
                    "show_screenshots": True,
                    "emphasize_visual_content": True,
                    "progress_visualization": "visual",
                }
            )

        if adjustments.get("use_progress_tracking"):
            visual_config["progress_visualization"] = "detailed"

        return visual_config

    def _estimate_completion_time(self, user_segment: str) -> Dict[str, int]:
        """Estimate completion time based on user segment."""
        base_times = {
            "tech_savvy": {"min": 120, "max": 180, "target": 150},  # 2-3 minutes
            "casual_user": {"min": 240, "max": 360, "target": 300},  # 4-6 minutes
            "visual_learner": {"min": 180, "max": 300, "target": 240},  # 3-5 minutes
            "goal_oriented": {"min": 90, "max": 180, "target": 135},  # 1.5-3 minutes
            "social_user": {"min": 150, "max": 240, "target": 195},  # 2.5-4 minutes
        }
        return base_times.get(user_segment, base_times["casual_user"])

    def _calculate_personalization_confidence(
        self, user_context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate confidence score for personalization decisions."""
        if not user_context:
            return 0.2  # Low confidence without context

        confidence_factors = []

        # Device info availability
        if user_context.get("device_info"):
            confidence_factors.append(0.2)

        # Referral source known
        if user_context.get("referral_source", "unknown") != "unknown":
            confidence_factors.append(0.3)

        # Behavioral indicators
        if user_context.get("behavioral_indicators"):
            confidence_factors.append(0.3)

        # Demographic info
        if user_context.get("demographic_info"):
            confidence_factors.append(0.2)

        return min(sum(confidence_factors), 1.0)

    def _get_default_onboarding_flow(self, user_id: str) -> Dict[str, Any]:
        """Return default onboarding flow when personalization fails."""
        return {
            "user_id": user_id,
            "user_segment": "default",
            "personalization_applied": False,
            "flow_structure": {
                "step_order": [1, 2, 3, 4, 5],
                "optional_steps": [],
                "progress_indicators": True,
                "step_transitions": "standard",
            },
            "personalized_content": {
                "welcome_message": "안녕하세요! 핫플레이스 발견의 여정을 시작해볼까요?",
                "category_description": "관심있는 장소 유형을 2-5개 선택해주세요",
                "completion_message": "축하합니다! 이제 개인화된 추천을 받을 준비가 되었습니다.",
                "content_tone": "friendly",
                "visual_elements": {
                    "use_animations": False,
                    "show_screenshots": False,
                    "emphasize_visual_content": False,
                    "progress_visualization": "basic",
                },
            },
            "adjustments": {},
            "estimated_completion_time": {"min": 180, "max": 300, "target": 240},
            "personalization_confidence": 0.1,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def track_personalization_effectiveness(
        self,
        user_id: str,
        onboarding_session: Dict[str, Any],
        completion_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Track effectiveness of personalization decisions."""
        try:
            user_segment = onboarding_session.get("user_segment", "unknown")
            personalization_applied = onboarding_session.get(
                "personalization_applied", False
            )

            # Calculate effectiveness metrics
            effectiveness_score = self._calculate_effectiveness_score(
                completion_metrics,
                onboarding_session.get("estimated_completion_time", {}),
            )

            # Compare against benchmarks
            benchmark_comparison = self._compare_against_benchmarks(
                user_segment, completion_metrics, effectiveness_score
            )

            effectiveness_data = {
                "user_id": user_id,
                "user_segment": user_segment,
                "personalization_applied": personalization_applied,
                "effectiveness_score": effectiveness_score,
                "completion_time_actual": completion_metrics.get(
                    "completion_time_seconds", 0
                ),
                "completion_rate": completion_metrics.get("completed", False),
                "user_satisfaction": completion_metrics.get("satisfaction_score", 0),
                "benchmark_comparison": benchmark_comparison,
                "tracked_at": datetime.utcnow().isoformat(),
            }

            # Log for analytics
            logger.info(
                f"Personalization effectiveness tracked for user {user_id}: {effectiveness_score}"
            )

            return effectiveness_data

        except Exception as e:
            logger.error(f"Failed to track personalization effectiveness: {e}")
            return {}

    def _calculate_effectiveness_score(
        self, completion_metrics: Dict[str, Any], estimated_time: Dict[str, int]
    ) -> float:
        """Calculate overall effectiveness score for personalization."""
        score_components = []

        # Completion rate (40% weight)
        if completion_metrics.get("completed", False):
            score_components.append(0.4)

        # Time efficiency (30% weight)
        actual_time = completion_metrics.get("completion_time_seconds", 0)
        target_time = estimated_time.get("target", 240)
        if actual_time > 0 and actual_time <= target_time * 1.2:  # Within 20% of target
            time_score = max(0, 1 - (actual_time - target_time) / target_time)
            score_components.append(time_score * 0.3)

        # User satisfaction (20% weight)
        satisfaction = completion_metrics.get("satisfaction_score", 0) / 5.0
        score_components.append(satisfaction * 0.2)

        # Error rate (10% weight - inverted)
        error_count = completion_metrics.get("error_count", 0)
        error_score = max(0, 1 - (error_count / 5))  # Normalize to max 5 errors
        score_components.append(error_score * 0.1)

        return sum(score_components)

    def _compare_against_benchmarks(
        self,
        user_segment: str,
        completion_metrics: Dict[str, Any],
        effectiveness_score: float,
    ) -> Dict[str, Any]:
        """Compare results against segment benchmarks."""
        # Default benchmarks (would be loaded from analytics in production)
        segment_benchmarks = {
            "tech_savvy": {
                "avg_completion_rate": 0.85,
                "avg_time": 150,
                "avg_effectiveness": 0.75,
            },
            "casual_user": {
                "avg_completion_rate": 0.70,
                "avg_time": 300,
                "avg_effectiveness": 0.65,
            },
            "visual_learner": {
                "avg_completion_rate": 0.75,
                "avg_time": 240,
                "avg_effectiveness": 0.70,
            },
            "goal_oriented": {
                "avg_completion_rate": 0.90,
                "avg_time": 135,
                "avg_effectiveness": 0.80,
            },
            "social_user": {
                "avg_completion_rate": 0.80,
                "avg_time": 195,
                "avg_effectiveness": 0.72,
            },
        }

        benchmark = segment_benchmarks.get(
            user_segment, segment_benchmarks["casual_user"]
        )
        actual_time = completion_metrics.get("completion_time_seconds", 0)

        return {
            "completion_rate_vs_benchmark": {
                "actual": completion_metrics.get("completed", False),
                "benchmark": benchmark["avg_completion_rate"],
                "performance": (
                    "above"
                    if completion_metrics.get("completed")
                    and benchmark["avg_completion_rate"] < 1
                    else "at_benchmark"
                ),
            },
            "time_vs_benchmark": {
                "actual": actual_time,
                "benchmark": benchmark["avg_time"],
                "performance": (
                    "better" if actual_time < benchmark["avg_time"] else "worse"
                ),
            },
            "effectiveness_vs_benchmark": {
                "actual": effectiveness_score,
                "benchmark": benchmark["avg_effectiveness"],
                "performance": (
                    "above"
                    if effectiveness_score > benchmark["avg_effectiveness"]
                    else "below"
                ),
            },
        }


class PersonalizationOptimizer:
    """Optimizer for improving personalization rules based on performance data."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_personalization_performance(
        self, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze personalization performance over time period."""
        try:
            # This would query actual performance data in production
            # For now, return mock analysis

            analysis_results = {
                "analysis_period": f"{time_period_days} days",
                "total_users_analyzed": 1000,  # Mock data
                "segment_performance": {
                    "tech_savvy": {
                        "user_count": 200,
                        "avg_completion_rate": 0.87,
                        "avg_completion_time": 145,
                        "avg_effectiveness_score": 0.78,
                        "improvement_opportunities": [
                            "Further reduce explanation text",
                            "Add more advanced quick-setup options",
                        ],
                    },
                    "casual_user": {
                        "user_count": 400,
                        "avg_completion_rate": 0.72,
                        "avg_completion_time": 285,
                        "avg_effectiveness_score": 0.68,
                        "improvement_opportunities": [
                            "Add more progress indicators",
                            "Simplify category selection interface",
                        ],
                    },
                    "visual_learner": {
                        "user_count": 150,
                        "avg_completion_rate": 0.78,
                        "avg_completion_time": 230,
                        "avg_effectiveness_score": 0.73,
                        "improvement_opportunities": [
                            "Increase visual content density",
                            "Add more interactive elements",
                        ],
                    },
                },
                "overall_metrics": {
                    "personalization_effectiveness": 0.73,
                    "completion_rate_improvement": 0.12,  # vs non-personalized
                    "time_efficiency_improvement": 0.08,
                    "user_satisfaction_improvement": 0.15,
                },
                "recommendations": [
                    "Implement dynamic content adjustment based on real-time behavior",
                    "Expand user segmentation to include behavioral sub-segments",
                    "Add predictive models for early dropout prevention",
                    "Introduce contextual help based on user hesitation patterns",
                ],
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Personalization performance analysis completed for {time_period_days} days"
            )
            return analysis_results

        except Exception as e:
            logger.error(f"Failed to analyze personalization performance: {e}")
            return {}

    def generate_optimization_recommendations(
        self, performance_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations based on analysis."""
        try:
            recommendations = []

            segment_performance = performance_analysis.get("segment_performance", {})

            for segment, metrics in segment_performance.items():
                completion_rate = metrics.get("avg_completion_rate", 0)
                effectiveness_score = metrics.get("avg_effectiveness_score", 0)

                # Low completion rate recommendations
                if completion_rate < 0.75:
                    recommendations.append(
                        {
                            "priority": "high",
                            "segment": segment,
                            "issue": "low_completion_rate",
                            "current_rate": completion_rate,
                            "recommendation": f"Implement guided mode for {segment} users",
                            "expected_improvement": 0.10,
                            "implementation_effort": "medium",
                        }
                    )

                # Low effectiveness recommendations
                if effectiveness_score < 0.70:
                    recommendations.append(
                        {
                            "priority": "medium",
                            "segment": segment,
                            "issue": "low_effectiveness",
                            "current_score": effectiveness_score,
                            "recommendation": f"A/B test alternative flows for {segment}",
                            "expected_improvement": 0.08,
                            "implementation_effort": "high",
                        }
                    )

            # Sort by priority and expected improvement
            recommendations.sort(
                key=lambda x: (x["priority"] == "high", x["expected_improvement"]),
                reverse=True,
            )

            logger.info(
                f"Generated {len(recommendations)} optimization recommendations"
            )
            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            return []
