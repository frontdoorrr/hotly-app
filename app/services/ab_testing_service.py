"""
A/B Testing Service

Manages A/B test group assignments and experiment tracking for notification timing optimization.
"""

import hashlib
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ABTestingService:
    """Service for managing A/B testing experiments."""

    def __init__(self) -> None:
        self.active_experiments = {
            "personalized_timing_v1": {
                "name": "Personalized Timing Algorithm",
                "start_date": "2025-01-01",
                "end_date": "2025-02-01",
                "control_ratio": 0.5,
                "treatment_ratio": 0.5,
                "status": "active",
            }
        }

    async def get_user_group(
        self, user_id: str, experiment_name: str = "personalized_timing_v1"
    ) -> str:
        """
        Get A/B test group assignment for a user.

        Args:
            user_id: User identifier
            experiment_name: Name of the experiment

        Returns:
            Group assignment ("control" or "treatment")
        """
        logger.debug(
            f"Getting A/B test group for user {user_id}, experiment {experiment_name}"
        )

        if experiment_name not in self.active_experiments:
            logger.warning(
                f"Experiment {experiment_name} not found, defaulting to control"
            )
            return "control"

        experiment = self.active_experiments[experiment_name]
        if experiment["status"] != "active":
            return "control"

        # Hash-based assignment for consistent grouping
        hash_input = f"{user_id}_{experiment_name}"
        hash_value = int(
            hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest(), 16
        )  # nosec B324

        # Use hash to determine group
        if hash_value % 2 == 0:
            return "control"
        else:
            return "treatment"

    async def record_experiment_result(
        self, user_id: str, experiment_name: str, group: str, outcome: Dict[str, Any]
    ) -> bool:
        """
        Record experiment outcome for analysis.

        Args:
            user_id: User identifier
            experiment_name: Name of the experiment
            group: User's group assignment
            outcome: Experiment outcome data

        Returns:
            Success status
        """
        logger.info(
            f"Recording experiment result for user {user_id}, "
            f"experiment {experiment_name}, group {group}, "
            f"outcome keys: {list(outcome.keys())}"
        )

        # Mock implementation - in production would store to analytics database

        # Store result (mock)
        return True

    async def get_experiment_stats(self, experiment_name: str) -> Dict[str, Any]:
        """
        Get statistics for an A/B test experiment.

        Args:
            experiment_name: Name of the experiment

        Returns:
            Experiment statistics
        """
        if experiment_name not in self.active_experiments:
            return {"error": "Experiment not found"}

        # Mock statistics - in production would compute from stored results
        return {
            "experiment_name": experiment_name,
            "total_users": 1000,
            "control_users": 500,
            "treatment_users": 500,
            "control_conversion_rate": 0.15,
            "treatment_conversion_rate": 0.18,
            "statistical_significance": 0.85,
            "winner": "treatment",
            "confidence_interval": [0.02, 0.04],
        }

    async def is_user_in_experiment(self, user_id: str, experiment_name: str) -> bool:
        """
        Check if user is enrolled in experiment.

        Args:
            user_id: User identifier
            experiment_name: Name of the experiment

        Returns:
            True if user is in experiment
        """
        logger.debug(f"Checking experiment enrollment for user {user_id}")
        return experiment_name in self.active_experiments

    def get_active_experiments(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all active experiments."""
        return {
            name: exp
            for name, exp in self.active_experiments.items()
            if exp["status"] == "active"
        }
