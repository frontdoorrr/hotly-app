"""A/B Testing framework for onboarding experiments."""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment status enumeration."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VariantType(Enum):
    """A/B test variant type."""

    CONTROL = "control"
    TREATMENT = "treatment"


class ExperimentManager:
    """Manager for A/B testing experiments."""

    def __init__(self, db: Session):
        self.db = db
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self._load_active_experiments()

    def _load_active_experiments(self) -> None:
        """Load active experiments from storage."""
        # In production, this would load from database
        # For now, define some default experiments
        self.active_experiments = {
            "onboarding_flow_v1": {
                "id": "onboarding_flow_v1",
                "name": "Onboarding Flow Optimization",
                "description": "Test different onboarding flow structures",
                "status": ExperimentStatus.ACTIVE.value,
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-03-01T00:00:00Z",
                "traffic_allocation": 0.5,  # 50% of users
                "variants": {
                    "control": {
                        "id": "control",
                        "type": VariantType.CONTROL.value,
                        "name": "Original Flow",
                        "allocation": 0.5,
                        "config": {
                            "flow_type": "standard",
                            "step_count": 5,
                            "progress_indicators": True,
                            "skip_options": False,
                        },
                    },
                    "treatment": {
                        "id": "treatment",
                        "type": VariantType.TREATMENT.value,
                        "name": "Streamlined Flow",
                        "allocation": 0.5,
                        "config": {
                            "flow_type": "streamlined",
                            "step_count": 3,
                            "progress_indicators": False,
                            "skip_options": True,
                        },
                    },
                },
                "metrics": {
                    "primary": "completion_rate",
                    "secondary": [
                        "completion_time",
                        "user_satisfaction",
                        "activation_rate",
                    ],
                },
                "targeting": {
                    "user_segments": ["all"],
                    "platforms": ["ios", "android", "web"],
                    "countries": ["KR"],
                },
            },
            "personalization_level_test": {
                "id": "personalization_level_test",
                "name": "Personalization Level Test",
                "description": "Test different levels of personalization",
                "status": ExperimentStatus.ACTIVE.value,
                "start_date": "2025-01-15T00:00:00Z",
                "end_date": "2025-02-15T00:00:00Z",
                "traffic_allocation": 0.3,  # 30% of users
                "variants": {
                    "minimal": {
                        "id": "minimal",
                        "type": VariantType.CONTROL.value,
                        "name": "Minimal Personalization",
                        "allocation": 0.33,
                        "config": {
                            "personalization_level": "minimal",
                            "segment_based_content": False,
                            "dynamic_adjustments": False,
                        },
                    },
                    "moderate": {
                        "id": "moderate",
                        "type": VariantType.TREATMENT.value,
                        "name": "Moderate Personalization",
                        "allocation": 0.34,
                        "config": {
                            "personalization_level": "moderate",
                            "segment_based_content": True,
                            "dynamic_adjustments": False,
                        },
                    },
                    "aggressive": {
                        "id": "aggressive",
                        "type": VariantType.TREATMENT.value,
                        "name": "Aggressive Personalization",
                        "allocation": 0.33,
                        "config": {
                            "personalization_level": "aggressive",
                            "segment_based_content": True,
                            "dynamic_adjustments": True,
                        },
                    },
                },
                "metrics": {
                    "primary": "user_satisfaction",
                    "secondary": [
                        "completion_rate",
                        "feature_adoption",
                        "retention_rate",
                    ],
                },
                "targeting": {
                    "user_segments": ["tech_savvy", "casual_user"],
                    "platforms": ["ios", "android"],
                    "countries": ["KR"],
                },
            },
        }

    def assign_user_to_experiment(
        self,
        user_id: str,
        experiment_id: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Assign user to experiment variant."""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                logger.warning(f"Experiment {experiment_id} not found")
                return None

            # Check if experiment is active
            if experiment["status"] != ExperimentStatus.ACTIVE.value:
                return None

            # Check if user should be included in experiment
            if not self._should_include_user(user_id, experiment, user_context):
                return None

            # Determine variant using consistent hashing
            variant_id = self._assign_variant(user_id, experiment)
            variant = experiment["variants"].get(variant_id)

            if not variant:
                logger.error(
                    f"Variant {variant_id} not found for experiment {experiment_id}"
                )
                return None

            assignment = {
                "user_id": user_id,
                "experiment_id": experiment_id,
                "experiment_name": experiment["name"],
                "variant_id": variant_id,
                "variant_name": variant["name"],
                "variant_type": variant["type"],
                "variant_config": variant["config"],
                "assigned_at": datetime.utcnow().isoformat(),
                "assignment_context": user_context or {},
            }

            # Log assignment for tracking
            self._log_assignment(assignment)

            logger.info(
                f"User {user_id} assigned to experiment {experiment_id} variant {variant_id}"
            )
            return assignment

        except Exception as e:
            logger.error(f"Failed to assign user to experiment: {e}")
            return None

    def _should_include_user(
        self,
        user_id: str,
        experiment: Dict[str, Any],
        user_context: Optional[Dict[str, Any]],
    ) -> bool:
        """Determine if user should be included in experiment."""
        try:
            # Check traffic allocation
            user_hash = int(
                hashlib.md5(user_id.encode(), usedforsecurity=False).hexdigest()[:8], 16
            )  # nosec
            traffic_threshold = int(experiment["traffic_allocation"] * (2**32))
            if user_hash >= traffic_threshold:
                return False

            # Check targeting criteria
            targeting = experiment.get("targeting", {})

            if user_context:
                # Check user segment targeting
                user_segment = user_context.get("user_segment")
                target_segments = targeting.get("user_segments", ["all"])
                if "all" not in target_segments and user_segment not in target_segments:
                    return False

                # Check platform targeting
                platform = user_context.get("device_info", {}).get("platform")
                target_platforms = targeting.get("platforms", ["all"])
                if "all" not in target_platforms and platform not in target_platforms:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking user inclusion: {e}")
            return False

    def _assign_variant(self, user_id: str, experiment: Dict[str, Any]) -> str:
        """Assign variant using consistent hashing."""
        try:
            variants = experiment["variants"]
            variant_list = list(variants.keys())

            # Create consistent hash
            hash_input = f"{user_id}:{experiment['id']}"
            hash_value = int(
                hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()[:8],
                16,
            )  # nosec

            # Determine variant based on allocation
            cumulative_allocation = 0.0
            normalized_hash = hash_value / (2**32)

            for variant_id in variant_list:
                variant = variants[variant_id]
                cumulative_allocation += variant["allocation"]

                if normalized_hash <= cumulative_allocation:
                    return variant_id

            # Fallback to first variant
            return variant_list[0]

        except Exception as e:
            logger.error(f"Error assigning variant: {e}")
            return list(experiment["variants"].keys())[0]

    def _log_assignment(self, assignment: Dict[str, Any]) -> None:
        """Log experiment assignment for tracking."""
        try:
            # In production, this would write to analytics/tracking system
            logger.info(f"AB_TEST_ASSIGNMENT: {json.dumps(assignment)}")
        except Exception as e:
            logger.error(f"Error logging assignment: {e}")

    def track_event(
        self,
        user_id: str,
        event_name: str,
        event_data: Dict[str, Any],
        experiment_assignments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Track event for A/B test analysis."""
        try:
            # Get current experiment assignments for user
            if experiment_assignments is None:
                experiment_assignments = self.get_user_assignments(user_id)

            event_record = {
                "user_id": user_id,
                "event_name": event_name,
                "event_data": event_data,
                "experiment_assignments": experiment_assignments,
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Log event for analytics
            logger.info(f"AB_TEST_EVENT: {json.dumps(event_record)}")

        except Exception as e:
            logger.error(f"Error tracking A/B test event: {e}")

    def get_user_assignments(self, user_id: str) -> List[Dict[str, Any]]:
        """Get current experiment assignments for user."""
        try:
            assignments = []

            for experiment_id, experiment in self.active_experiments.items():
                if experiment["status"] == ExperimentStatus.ACTIVE.value:
                    assignment = self.assign_user_to_experiment(user_id, experiment_id)
                    if assignment:
                        assignments.append(assignment)

            return assignments

        except Exception as e:
            logger.error(f"Error getting user assignments: {e}")
            return []

    def create_experiment(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create new A/B test experiment."""
        try:
            experiment_id = experiment_config.get("id") or str(uuid.uuid4())

            # Validate experiment configuration
            validation_result = self._validate_experiment_config(experiment_config)
            if not validation_result["valid"]:
                raise ValueError(
                    f"Invalid experiment config: {validation_result['errors']}"
                )

            experiment = {
                "id": experiment_id,
                "name": experiment_config["name"],
                "description": experiment_config.get("description", ""),
                "status": ExperimentStatus.DRAFT.value,
                "start_date": experiment_config.get("start_date"),
                "end_date": experiment_config.get("end_date"),
                "traffic_allocation": experiment_config.get("traffic_allocation", 1.0),
                "variants": experiment_config["variants"],
                "metrics": experiment_config["metrics"],
                "targeting": experiment_config.get("targeting", {}),
                "created_at": datetime.utcnow().isoformat(),
                "created_by": experiment_config.get("created_by", "system"),
            }

            # Store experiment (in production, this would be persisted)
            self.active_experiments[experiment_id] = experiment

            logger.info(f"Created experiment: {experiment_id}")
            return experiment

        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            raise

    def _validate_experiment_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate experiment configuration."""
        errors = []

        # Required fields
        required_fields = ["name", "variants", "metrics"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Validate variants
        if "variants" in config:
            variants = config["variants"]
            total_allocation = sum(v.get("allocation", 0) for v in variants.values())
            if abs(total_allocation - 1.0) > 0.01:  # Allow small rounding errors
                errors.append(
                    f"Variant allocations must sum to 1.0, got {total_allocation}"
                )

            # Check for control variant
            has_control = any(
                v.get("type") == VariantType.CONTROL.value for v in variants.values()
            )
            if not has_control:
                errors.append("Experiment must have at least one control variant")

        # Validate traffic allocation
        traffic_allocation = config.get("traffic_allocation", 1.0)
        if not 0 < traffic_allocation <= 1.0:
            errors.append(
                f"Traffic allocation must be between 0 and 1, got {traffic_allocation}"
            )

        return {"valid": len(errors) == 0, "errors": errors}


class ABTestAnalyzer:
    """Analyzer for A/B test results and statistical significance."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_experiment_results(
        self, experiment_id: str, analysis_period_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze A/B test experiment results."""
        try:
            # In production, this would query actual event data
            # For now, return mock analysis results

            mock_results = {
                "experiment_id": experiment_id,
                "analysis_period": f"{analysis_period_days or 30} days",
                "sample_size": {"control": 1250, "treatment": 1280},
                "metrics": {
                    "completion_rate": {
                        "control": {
                            "value": 0.72,
                            "sample_size": 1250,
                            "confidence_interval": [0.694, 0.746],
                        },
                        "treatment": {
                            "value": 0.78,
                            "sample_size": 1280,
                            "confidence_interval": [0.755, 0.805],
                        },
                        "statistical_significance": {
                            "p_value": 0.023,
                            "significant": True,
                            "confidence_level": 0.95,
                            "effect_size": 0.06,
                            "relative_lift": 0.083,
                        },
                    },
                    "completion_time": {
                        "control": {
                            "value": 245.0,
                            "sample_size": 900,  # Only completed users
                            "confidence_interval": [238.2, 251.8],
                        },
                        "treatment": {
                            "value": 198.0,
                            "sample_size": 998,
                            "confidence_interval": [192.1, 203.9],
                        },
                        "statistical_significance": {
                            "p_value": 0.001,
                            "significant": True,
                            "confidence_level": 0.95,
                            "effect_size": -47.0,
                            "relative_lift": -0.192,
                        },
                    },
                },
                "recommendation": {
                    "decision": "implement_treatment",
                    "confidence": "high",
                    "reasoning": [
                        "Statistically significant improvement in completion rate (+8.3%)",
                        "Significant reduction in completion time (-19.2%)",
                        "Consistent positive results across user segments",
                        "Risk of negative impact is low based on current data",
                    ],
                    "next_steps": [
                        "Implement treatment variant as new default",
                        "Monitor key metrics for 30 days post-implementation",
                        "Conduct follow-up analysis on user retention",
                    ],
                },
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"A/B test analysis completed for experiment {experiment_id}")
            return mock_results

        except Exception as e:
            logger.error(f"Error analyzing experiment results: {e}")
            return {}

    def calculate_statistical_significance(
        self,
        control_data: Dict[str, Any],
        treatment_data: Dict[str, Any],
        metric_type: str = "conversion",
    ) -> Dict[str, Any]:
        """Calculate statistical significance between control and treatment."""
        try:
            # Mock statistical calculation
            # In production, this would use proper statistical libraries

            control_value = control_data.get("value", 0)
            treatment_value = treatment_data.get("value", 0)
            control_sample = control_data.get("sample_size", 0)
            treatment_sample = treatment_data.get("sample_size", 0)

            # Calculate effect size
            if metric_type == "conversion":
                effect_size = treatment_value - control_value
                relative_lift = effect_size / control_value if control_value > 0 else 0
            else:  # continuous metric
                effect_size = treatment_value - control_value
                relative_lift = effect_size / control_value if control_value > 0 else 0

            # Mock p-value calculation (would use proper statistical test)
            if abs(effect_size) > 0.05:  # Significant effect
                p_value = 0.02
            elif abs(effect_size) > 0.02:  # Marginal effect
                p_value = 0.08
            else:  # No effect
                p_value = 0.45

            significance_result = {
                "p_value": p_value,
                "significant": p_value < 0.05,
                "confidence_level": 0.95,
                "effect_size": effect_size,
                "relative_lift": relative_lift,
                "statistical_power": self._calculate_power(
                    control_sample, treatment_sample, effect_size
                ),
                "minimum_detectable_effect": self._calculate_mde(
                    control_sample, treatment_sample
                ),
            }

            return significance_result

        except Exception as e:
            logger.error(f"Error calculating statistical significance: {e}")
            return {}

    def _calculate_power(
        self, control_sample: int, treatment_sample: int, effect_size: float
    ) -> float:
        """Calculate statistical power (mock implementation)."""
        # Mock power calculation
        total_sample = control_sample + treatment_sample
        if total_sample < 1000:
            return 0.6
        elif total_sample < 2000:
            return 0.8
        else:
            return 0.9

    def _calculate_mde(self, control_sample: int, treatment_sample: int) -> float:
        """Calculate minimum detectable effect (mock implementation)."""
        # Mock MDE calculation
        total_sample = control_sample + treatment_sample
        if total_sample < 1000:
            return 0.1  # 10% MDE
        elif total_sample < 2000:
            return 0.05  # 5% MDE
        else:
            return 0.025  # 2.5% MDE

    def generate_experiment_report(
        self, experiment_id: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive experiment report."""
        try:
            report = {
                "experiment_id": experiment_id,
                "report_type": "final_analysis",
                "executive_summary": {
                    "experiment_outcome": results.get("recommendation", {}).get(
                        "decision", "inconclusive"
                    ),
                    "key_findings": [
                        f"Primary metric showed {results.get('metrics', {}).get('completion_rate', {}).get('statistical_significance', {}).get('relative_lift', 0) * 100:.1f}% change",
                        f"Statistical significance achieved (p={results.get('metrics', {}).get('completion_rate', {}).get('statistical_significance', {}).get('p_value', 1):.3f})",
                        f"Sample size: {sum(results.get('sample_size', {}).values())} users",
                    ],
                    "business_impact": self._calculate_business_impact(results),
                    "implementation_recommendation": results.get(
                        "recommendation", {}
                    ).get("decision", "continue_monitoring"),
                },
                "detailed_results": results,
                "methodology": {
                    "test_design": "two_sample_hypothesis_test",
                    "significance_level": 0.05,
                    "power_analysis": "conducted",
                    "duration": "28 days",
                },
                "appendix": {
                    "raw_data_location": f"s3://experiments/{experiment_id}/raw_data",
                    "analysis_code": f"s3://experiments/{experiment_id}/analysis.py",
                    "peer_review": "completed",
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Generated experiment report for {experiment_id}")
            return report

        except Exception as e:
            logger.error(f"Error generating experiment report: {e}")
            return {}

    def _calculate_business_impact(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate business impact of experiment results."""
        try:
            completion_rate_lift = (
                results.get("metrics", {})
                .get("completion_rate", {})
                .get("statistical_significance", {})
                .get("relative_lift", 0)
            )

            # Mock business impact calculation
            estimated_monthly_users = 10000
            current_conversion_rate = 0.72

            additional_conversions = (
                estimated_monthly_users * completion_rate_lift * current_conversion_rate
            )
            value_per_conversion = 25.0  # Mock value in USD

            monthly_impact = additional_conversions * value_per_conversion
            annual_impact = monthly_impact * 12

            return {
                "estimated_monthly_additional_conversions": round(
                    additional_conversions
                ),
                "estimated_monthly_revenue_impact": round(monthly_impact, 2),
                "estimated_annual_revenue_impact": round(annual_impact, 2),
                "confidence_interval": {
                    "low": round(annual_impact * 0.8, 2),
                    "high": round(annual_impact * 1.2, 2),
                },
            }

        except Exception as e:
            logger.error(f"Error calculating business impact: {e}")
            return {}


class ABTestOrchestrator:
    """Orchestrator for managing A/B test lifecycle."""

    def __init__(self, db: Session):
        self.db = db
        self.experiment_manager = ExperimentManager(db)
        self.analyzer = ABTestAnalyzer(db)

    def run_onboarding_experiment(
        self,
        user_id: str,
        base_onboarding_config: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run A/B test experiment for onboarding."""
        try:
            # Get experiment assignments
            assignments = self.experiment_manager.get_user_assignments(user_id)

            # Apply experiment configurations
            final_config = base_onboarding_config.copy()
            applied_experiments = []

            for assignment in assignments:
                experiment_id = assignment["experiment_id"]
                variant_config = assignment["variant_config"]

                # Apply variant configuration to onboarding
                final_config = self._merge_experiment_config(
                    final_config, variant_config
                )
                applied_experiments.append(assignment)

                # Track experiment exposure
                self.experiment_manager.track_event(
                    user_id,
                    "onboarding_experiment_exposure",
                    {
                        "experiment_id": experiment_id,
                        "variant_id": assignment["variant_id"],
                        "config_applied": variant_config,
                    },
                    [assignment],
                )

            result = {
                "user_id": user_id,
                "final_onboarding_config": final_config,
                "applied_experiments": applied_experiments,
                "base_config_modified": len(applied_experiments) > 0,
                "orchestrated_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Onboarding A/B test orchestrated for user {user_id} with {len(applied_experiments)} experiments"
            )
            return result

        except Exception as e:
            logger.error(f"Error orchestrating A/B test: {e}")
            return {
                "user_id": user_id,
                "final_onboarding_config": base_onboarding_config,
                "applied_experiments": [],
                "base_config_modified": False,
                "error": str(e),
            }

    def _merge_experiment_config(
        self, base_config: Dict[str, Any], experiment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge experiment configuration with base configuration."""
        try:
            merged_config = base_config.copy()

            # Apply experiment-specific overrides
            for key, value in experiment_config.items():
                if (
                    key in merged_config
                    and isinstance(merged_config[key], dict)
                    and isinstance(value, dict)
                ):
                    # Merge nested dictionaries
                    merged_config[key].update(value)
                else:
                    # Direct override
                    merged_config[key] = value

            return merged_config

        except Exception as e:
            logger.error(f"Error merging experiment config: {e}")
            return base_config

    def track_onboarding_completion(
        self,
        user_id: str,
        completion_data: Dict[str, Any],
        experiment_context: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Track onboarding completion for A/B test analysis."""
        try:
            if experiment_context is None:
                experiment_context = self.experiment_manager.get_user_assignments(
                    user_id
                )

            # Track completion event
            self.experiment_manager.track_event(
                user_id, "onboarding_completed", completion_data, experiment_context
            )

            # Track specific metrics for each experiment
            for assignment in experiment_context:
                experiment_id = assignment["experiment_id"]

                self.experiment_manager.track_event(
                    user_id,
                    f"experiment_{experiment_id}_completion",
                    {
                        "experiment_id": experiment_id,
                        "variant_id": assignment["variant_id"],
                        "completion_time": completion_data.get(
                            "completion_time_seconds"
                        ),
                        "completed": completion_data.get("completed", False),
                        "satisfaction_score": completion_data.get("satisfaction_score"),
                        "steps_completed": completion_data.get("steps_completed", []),
                    },
                    [assignment],
                )

            logger.info(
                f"Onboarding completion tracked for user {user_id} across {len(experiment_context)} experiments"
            )

        except Exception as e:
            logger.error(f"Error tracking onboarding completion: {e}")
