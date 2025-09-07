"""Test cases for A/B testing framework functionality."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.ab_testing.framework import (
    ABTestAnalyzer,
    ABTestOrchestrator,
    ExperimentManager,
    ExperimentStatus,
    VariantType,
)


class TestExperimentManager:
    """Test cases for ExperimentManager."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def experiment_manager(self, mock_db):
        """Create ExperimentManager instance."""
        return ExperimentManager(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios", "version": "15.0"},
            "location": {"country": "KR"},
        }

    def test_load_active_experiments_success(self, experiment_manager):
        """Test successful loading of active experiments."""
        # When
        experiment_manager._load_active_experiments()

        # Then
        assert len(experiment_manager.active_experiments) >= 2
        assert "onboarding_flow_v1" in experiment_manager.active_experiments
        assert "personalization_level_test" in experiment_manager.active_experiments

    def test_assign_user_to_experiment_success(
        self, experiment_manager, sample_user_id, sample_user_context
    ):
        """Test successful user assignment to experiment."""
        # Given
        experiment_id = "onboarding_flow_v1"

        with (
            patch.object(experiment_manager, "_should_include_user") as mock_include,
            patch.object(experiment_manager, "_assign_variant") as mock_variant,
            patch.object(experiment_manager, "_log_assignment") as mock_log,
        ):
            mock_include.return_value = True
            mock_variant.return_value = "control"
            mock_log.return_value = None

            # When
            result = experiment_manager.assign_user_to_experiment(
                sample_user_id, experiment_id, sample_user_context
            )

        # Then
        assert result is not None
        assert result["user_id"] == sample_user_id
        assert result["experiment_id"] == experiment_id
        assert result["variant_id"] == "control"
        assert "variant_config" in result
        assert "assigned_at" in result

    def test_assign_user_to_experiment_not_included(
        self, experiment_manager, sample_user_id, sample_user_context
    ):
        """Test user assignment when user should not be included."""
        # Given
        experiment_id = "onboarding_flow_v1"

        with patch.object(experiment_manager, "_should_include_user") as mock_include:
            mock_include.return_value = False

            # When
            result = experiment_manager.assign_user_to_experiment(
                sample_user_id, experiment_id, sample_user_context
            )

        # Then
        assert result is None

    def test_assign_user_to_experiment_inactive(
        self, experiment_manager, sample_user_id, sample_user_context
    ):
        """Test user assignment to inactive experiment."""
        # Given
        experiment_id = "inactive_experiment"
        experiment_manager.active_experiments[experiment_id] = {
            "id": experiment_id,
            "status": ExperimentStatus.PAUSED.value,
        }

        # When
        result = experiment_manager.assign_user_to_experiment(
            sample_user_id, experiment_id, sample_user_context
        )

        # Then
        assert result is None

    def test_assign_user_to_experiment_not_found(
        self, experiment_manager, sample_user_id, sample_user_context
    ):
        """Test user assignment to non-existent experiment."""
        # Given
        experiment_id = "non_existent_experiment"

        # When
        result = experiment_manager.assign_user_to_experiment(
            sample_user_id, experiment_id, sample_user_context
        )

        # Then
        assert result is None

    def test_should_include_user_traffic_allocation_included(self, experiment_manager):
        """Test user inclusion with traffic allocation - user included."""
        # Given
        user_id = "user_with_low_hash"  # This should result in low hash
        experiment = {"traffic_allocation": 1.0}  # 100% traffic

        # When
        result = experiment_manager._should_include_user(user_id, experiment, None)

        # Then
        assert result is True

    def test_should_include_user_traffic_allocation_excluded(self, experiment_manager):
        """Test user inclusion with traffic allocation - user excluded."""
        # Given
        user_id = "user_with_high_hash"  # This might result in high hash
        experiment = {"traffic_allocation": 0.01}  # 1% traffic only

        with patch("hashlib.md5") as mock_md5:
            mock_hash = Mock()
            mock_hash.hexdigest.return_value = "ffffffff"  # High hash value
            mock_md5.return_value = mock_hash

            # When
            result = experiment_manager._should_include_user(user_id, experiment, None)

        # Then
        assert result is False

    def test_should_include_user_segment_targeting_match(self, experiment_manager):
        """Test user inclusion with segment targeting - match."""
        # Given
        user_id = "test_user"
        experiment = {
            "traffic_allocation": 1.0,
            "targeting": {"user_segments": ["tech_savvy"]},
        }
        user_context = {"user_segment": "tech_savvy"}

        # When
        result = experiment_manager._should_include_user(
            user_id, experiment, user_context
        )

        # Then
        assert result is True

    def test_should_include_user_segment_targeting_no_match(self, experiment_manager):
        """Test user inclusion with segment targeting - no match."""
        # Given
        user_id = "test_user"
        experiment = {
            "traffic_allocation": 1.0,
            "targeting": {"user_segments": ["casual_user"]},
        }
        user_context = {"user_segment": "tech_savvy"}

        # When
        result = experiment_manager._should_include_user(
            user_id, experiment, user_context
        )

        # Then
        assert result is False

    def test_should_include_user_platform_targeting_match(self, experiment_manager):
        """Test user inclusion with platform targeting - match."""
        # Given
        user_id = "test_user"
        experiment = {
            "traffic_allocation": 1.0,
            "targeting": {"platforms": ["ios", "android"]},
        }
        user_context = {"device_info": {"platform": "ios"}}

        # When
        result = experiment_manager._should_include_user(
            user_id, experiment, user_context
        )

        # Then
        assert result is True

    def test_assign_variant_consistent_hashing(self, experiment_manager):
        """Test variant assignment consistency with same user ID."""
        # Given
        user_id = "consistent_user"
        experiment = {
            "id": "test_experiment",
            "variants": {
                "control": {"allocation": 0.5},
                "treatment": {"allocation": 0.5},
            },
        }

        # When - Call multiple times with same user ID
        variant1 = experiment_manager._assign_variant(user_id, experiment)
        variant2 = experiment_manager._assign_variant(user_id, experiment)
        variant3 = experiment_manager._assign_variant(user_id, experiment)

        # Then - Should always return same variant
        assert variant1 == variant2 == variant3
        assert variant1 in ["control", "treatment"]

    def test_assign_variant_allocation_distribution(self, experiment_manager):
        """Test variant assignment follows allocation distribution."""
        # Given
        experiment = {
            "id": "test_experiment",
            "variants": {
                "control": {"allocation": 0.3},
                "treatment_a": {"allocation": 0.4},
                "treatment_b": {"allocation": 0.3},
            },
        }

        # When - Assign many users
        assignments = {}
        for i in range(1000):
            user_id = f"user_{i}"
            variant = experiment_manager._assign_variant(user_id, experiment)
            assignments[variant] = assignments.get(variant, 0) + 1

        # Then - Distribution should roughly match allocation
        control_ratio = assignments.get("control", 0) / 1000
        treatment_a_ratio = assignments.get("treatment_a", 0) / 1000
        treatment_b_ratio = assignments.get("treatment_b", 0) / 1000

        assert 0.25 <= control_ratio <= 0.35  # Around 30%
        assert 0.35 <= treatment_a_ratio <= 0.45  # Around 40%
        assert 0.25 <= treatment_b_ratio <= 0.35  # Around 30%

    def test_track_event_success(self, experiment_manager, sample_user_id):
        """Test successful event tracking."""
        # Given
        event_name = "onboarding_step_completed"
        event_data = {"step": "category_selection", "completion_time": 45}
        experiment_assignments = [
            {
                "user_id": sample_user_id,
                "experiment_id": "onboarding_flow_v1",
                "variant_id": "treatment",
            }
        ]

        with patch("app.ab_testing.framework.logger") as mock_logger:
            # When
            experiment_manager.track_event(
                sample_user_id, event_name, event_data, experiment_assignments
            )

        # Then
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert "AB_TEST_EVENT:" in call_args

    def test_get_user_assignments_success(self, experiment_manager, sample_user_id):
        """Test successful retrieval of user assignments."""
        # Given
        with patch.object(
            experiment_manager, "assign_user_to_experiment"
        ) as mock_assign:
            mock_assign.side_effect = [
                {
                    "user_id": sample_user_id,
                    "experiment_id": "onboarding_flow_v1",
                    "variant_id": "control",
                },
                None,  # Second experiment excludes user
            ]

            # When
            assignments = experiment_manager.get_user_assignments(sample_user_id)

        # Then
        assert len(assignments) == 1
        assert assignments[0]["experiment_id"] == "onboarding_flow_v1"

    def test_create_experiment_success(self, experiment_manager):
        """Test successful experiment creation."""
        # Given
        experiment_config = {
            "name": "Test Experiment",
            "description": "A test experiment",
            "variants": {
                "control": {"allocation": 0.5, "type": VariantType.CONTROL.value},
                "treatment": {"allocation": 0.5, "type": VariantType.TREATMENT.value},
            },
            "metrics": {"primary": "completion_rate"},
            "traffic_allocation": 0.5,
        }

        # When
        result = experiment_manager.create_experiment(experiment_config)

        # Then
        assert result["name"] == "Test Experiment"
        assert result["status"] == ExperimentStatus.DRAFT.value
        assert "id" in result
        assert result["id"] in experiment_manager.active_experiments

    def test_create_experiment_invalid_config(self, experiment_manager):
        """Test experiment creation with invalid configuration."""
        # Given
        invalid_config = {
            "name": "Invalid Experiment",
            "variants": {
                "control": {"allocation": 0.7},  # Allocations don't sum to 1.0
                "treatment": {"allocation": 0.5},
            },
            "metrics": {"primary": "completion_rate"},
        }

        # When & Then
        with pytest.raises(ValueError, match="Invalid experiment config"):
            experiment_manager.create_experiment(invalid_config)

    def test_validate_experiment_config_valid(self, experiment_manager):
        """Test experiment configuration validation - valid config."""
        # Given
        valid_config = {
            "name": "Valid Experiment",
            "variants": {
                "control": {
                    "allocation": 0.5,
                    "type": VariantType.CONTROL.value,
                },
                "treatment": {
                    "allocation": 0.5,
                    "type": VariantType.TREATMENT.value,
                },
            },
            "metrics": {"primary": "completion_rate"},
            "traffic_allocation": 0.8,
        }

        # When
        result = experiment_manager._validate_experiment_config(valid_config)

        # Then
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_experiment_config_invalid_allocation(self, experiment_manager):
        """Test experiment configuration validation - invalid allocation."""
        # Given
        invalid_config = {
            "name": "Invalid Experiment",
            "variants": {
                "control": {"allocation": 0.3},
                "treatment": {"allocation": 0.5},  # Sum is 0.8, not 1.0
            },
            "metrics": {"primary": "completion_rate"},
        }

        # When
        result = experiment_manager._validate_experiment_config(invalid_config)

        # Then
        assert result["valid"] is False
        assert any("must sum to 1.0" in error for error in result["errors"])

    def test_validate_experiment_config_no_control(self, experiment_manager):
        """Test experiment configuration validation - no control variant."""
        # Given
        invalid_config = {
            "name": "No Control Experiment",
            "variants": {
                "treatment_a": {
                    "allocation": 0.5,
                    "type": VariantType.TREATMENT.value,
                },
                "treatment_b": {
                    "allocation": 0.5,
                    "type": VariantType.TREATMENT.value,
                },
            },
            "metrics": {"primary": "completion_rate"},
        }

        # When
        result = experiment_manager._validate_experiment_config(invalid_config)

        # Then
        assert result["valid"] is False
        assert any("control variant" in error for error in result["errors"])


class TestABTestAnalyzer:
    """Test cases for ABTestAnalyzer."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def ab_analyzer(self, mock_db):
        """Create ABTestAnalyzer instance."""
        return ABTestAnalyzer(db=mock_db)

    def test_analyze_experiment_results_success(self, ab_analyzer):
        """Test successful experiment results analysis."""
        # Given
        experiment_id = "test_experiment_123"

        # When
        result = ab_analyzer.analyze_experiment_results(experiment_id)

        # Then
        assert result["experiment_id"] == experiment_id
        assert "sample_size" in result
        assert "metrics" in result
        assert "recommendation" in result
        assert result["recommendation"]["decision"] in [
            "implement_treatment",
            "keep_control",
            "continue_monitoring",
        ]

    def test_analyze_experiment_results_with_period(self, ab_analyzer):
        """Test experiment results analysis with specific period."""
        # Given
        experiment_id = "test_experiment_123"
        analysis_period = 14  # 2 weeks

        # When
        result = ab_analyzer.analyze_experiment_results(experiment_id, analysis_period)

        # Then
        assert result["analysis_period"] == "14 days"
        assert "metrics" in result

    def test_calculate_statistical_significance_conversion_significant(
        self, ab_analyzer
    ):
        """Test statistical significance calculation for conversion metrics - significant."""
        # Given
        control_data = {"value": 0.70, "sample_size": 1000}
        treatment_data = {"value": 0.80, "sample_size": 1000}

        # When
        result = ab_analyzer.calculate_statistical_significance(
            control_data, treatment_data, "conversion"
        )

        # Then
        assert result["significant"] is True
        assert result["effect_size"] == 0.10
        assert result["relative_lift"] > 0
        assert result["p_value"] < 0.05

    def test_calculate_statistical_significance_conversion_not_significant(
        self, ab_analyzer
    ):
        """Test statistical significance calculation - not significant."""
        # Given
        control_data = {"value": 0.70, "sample_size": 1000}
        treatment_data = {"value": 0.71, "sample_size": 1000}  # Small difference

        # When
        result = ab_analyzer.calculate_statistical_significance(
            control_data, treatment_data, "conversion"
        )

        # Then
        assert result["significant"] is False
        assert abs(result["effect_size"]) < 0.05
        assert result["p_value"] >= 0.05

    def test_calculate_statistical_significance_continuous_metric(self, ab_analyzer):
        """Test statistical significance calculation for continuous metrics."""
        # Given
        control_data = {"value": 240.0, "sample_size": 500}  # Average time in seconds
        treatment_data = {"value": 200.0, "sample_size": 500}  # Improvement

        # When
        result = ab_analyzer.calculate_statistical_significance(
            control_data, treatment_data, "continuous"
        )

        # Then
        assert result["effect_size"] == -40.0  # Negative because it's an improvement
        assert result["relative_lift"] < 0  # Reduction in time is improvement
        assert "statistical_power" in result
        assert "minimum_detectable_effect" in result

    def test_calculate_power_high_sample_size(self, ab_analyzer):
        """Test statistical power calculation with high sample size."""
        # Given
        control_sample = 1500
        treatment_sample = 1500
        effect_size = 0.08

        # When
        power = ab_analyzer._calculate_power(
            control_sample, treatment_sample, effect_size
        )

        # Then
        assert power >= 0.8  # High power with large sample

    def test_calculate_power_low_sample_size(self, ab_analyzer):
        """Test statistical power calculation with low sample size."""
        # Given
        control_sample = 200
        treatment_sample = 200
        effect_size = 0.05

        # When
        power = ab_analyzer._calculate_power(
            control_sample, treatment_sample, effect_size
        )

        # Then
        assert power <= 0.7  # Lower power with small sample

    def test_calculate_mde_high_sample_size(self, ab_analyzer):
        """Test minimum detectable effect calculation with high sample size."""
        # Given
        control_sample = 2500
        treatment_sample = 2500

        # When
        mde = ab_analyzer._calculate_mde(control_sample, treatment_sample)

        # Then
        assert mde <= 0.05  # Lower MDE with large sample

    def test_calculate_mde_low_sample_size(self, ab_analyzer):
        """Test minimum detectable effect calculation with low sample size."""
        # Given
        control_sample = 300
        treatment_sample = 300

        # When
        mde = ab_analyzer._calculate_mde(control_sample, treatment_sample)

        # Then
        assert mde >= 0.05  # Higher MDE with small sample

    def test_generate_experiment_report_success(self, ab_analyzer):
        """Test successful experiment report generation."""
        # Given
        experiment_id = "test_experiment_123"
        results = {
            "experiment_id": experiment_id,
            "sample_size": {"control": 1000, "treatment": 1000},
            "metrics": {
                "completion_rate": {
                    "statistical_significance": {
                        "p_value": 0.023,
                        "relative_lift": 0.08,
                    }
                }
            },
            "recommendation": {"decision": "implement_treatment"},
        }

        # When
        report = ab_analyzer.generate_experiment_report(experiment_id, results)

        # Then
        assert report["experiment_id"] == experiment_id
        assert report["report_type"] == "final_analysis"
        assert "executive_summary" in report
        assert "detailed_results" in report
        assert "methodology" in report
        assert (
            report["executive_summary"]["implementation_recommendation"]
            == "implement_treatment"
        )

    def test_calculate_business_impact_positive(self, ab_analyzer):
        """Test business impact calculation with positive results."""
        # Given
        results = {
            "metrics": {
                "completion_rate": {
                    "statistical_significance": {
                        "relative_lift": 0.10
                    }  # 10% improvement
                }
            }
        }

        # When
        impact = ab_analyzer._calculate_business_impact(results)

        # Then
        assert impact["estimated_monthly_additional_conversions"] > 0
        assert impact["estimated_monthly_revenue_impact"] > 0
        assert impact["estimated_annual_revenue_impact"] > 0
        assert "confidence_interval" in impact

    def test_calculate_business_impact_negative(self, ab_analyzer):
        """Test business impact calculation with negative results."""
        # Given
        results = {
            "metrics": {
                "completion_rate": {
                    "statistical_significance": {"relative_lift": -0.05}  # 5% decrease
                }
            }
        }

        # When
        impact = ab_analyzer._calculate_business_impact(results)

        # Then
        assert impact["estimated_monthly_additional_conversions"] < 0
        assert impact["estimated_monthly_revenue_impact"] < 0
        assert impact["estimated_annual_revenue_impact"] < 0


class TestABTestOrchestrator:
    """Test cases for ABTestOrchestrator."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def ab_orchestrator(self, mock_db):
        """Create ABTestOrchestrator instance."""
        return ABTestOrchestrator(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def base_onboarding_config(self):
        """Base onboarding configuration for testing."""
        return {
            "step_count": 5,
            "progress_indicators": True,
            "skip_options": False,
            "flow_type": "standard",
        }

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios"},
        }

    def test_run_onboarding_experiment_with_assignments(
        self,
        ab_orchestrator,
        sample_user_id,
        base_onboarding_config,
        sample_user_context,
    ):
        """Test running onboarding experiment with active assignments."""
        # Given
        mock_assignments = [
            {
                "user_id": sample_user_id,
                "experiment_id": "onboarding_flow_v1",
                "variant_id": "treatment",
                "variant_config": {
                    "flow_type": "streamlined",
                    "step_count": 3,
                    "skip_options": True,
                },
            }
        ]

        ab_orchestrator.experiment_manager.get_user_assignments.return_value = (
            mock_assignments
        )
        ab_orchestrator.experiment_manager.track_event = Mock()

        # When
        result = ab_orchestrator.run_onboarding_experiment(
            sample_user_id, base_onboarding_config, sample_user_context
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["base_config_modified"] is True
        assert len(result["applied_experiments"]) == 1
        assert result["final_onboarding_config"]["flow_type"] == "streamlined"
        assert result["final_onboarding_config"]["step_count"] == 3

    def test_run_onboarding_experiment_no_assignments(
        self,
        ab_orchestrator,
        sample_user_id,
        base_onboarding_config,
        sample_user_context,
    ):
        """Test running onboarding experiment with no active assignments."""
        # Given
        ab_orchestrator.experiment_manager.get_user_assignments.return_value = []

        # When
        result = ab_orchestrator.run_onboarding_experiment(
            sample_user_id, base_onboarding_config, sample_user_context
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["base_config_modified"] is False
        assert len(result["applied_experiments"]) == 0
        assert result["final_onboarding_config"] == base_onboarding_config

    def test_run_onboarding_experiment_error_handling(
        self,
        ab_orchestrator,
        sample_user_id,
        base_onboarding_config,
        sample_user_context,
    ):
        """Test error handling in onboarding experiment orchestration."""
        # Given
        ab_orchestrator.experiment_manager.get_user_assignments.side_effect = Exception(
            "Database error"
        )

        # When
        result = ab_orchestrator.run_onboarding_experiment(
            sample_user_id, base_onboarding_config, sample_user_context
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["base_config_modified"] is False
        assert result["final_onboarding_config"] == base_onboarding_config
        assert "error" in result

    def test_merge_experiment_config_simple_override(self, ab_orchestrator):
        """Test simple configuration merging with override."""
        # Given
        base_config = {"step_count": 5, "flow_type": "standard"}
        experiment_config = {"step_count": 3, "skip_options": True}

        # When
        merged = ab_orchestrator._merge_experiment_config(
            base_config, experiment_config
        )

        # Then
        assert merged["step_count"] == 3  # Overridden
        assert merged["flow_type"] == "standard"  # Preserved
        assert merged["skip_options"] is True  # Added

    def test_merge_experiment_config_nested_merge(self, ab_orchestrator):
        """Test configuration merging with nested objects."""
        # Given
        base_config = {
            "ui_settings": {"theme": "light", "animations": True},
            "flow_type": "standard",
        }
        experiment_config = {
            "ui_settings": {"theme": "dark"},  # Should merge, not replace
            "step_count": 3,
        }

        # When
        merged = ab_orchestrator._merge_experiment_config(
            base_config, experiment_config
        )

        # Then
        assert merged["ui_settings"]["theme"] == "dark"  # Overridden
        assert merged["ui_settings"]["animations"] is True  # Preserved
        assert merged["step_count"] == 3  # Added

    def test_merge_experiment_config_error_handling(self, ab_orchestrator):
        """Test configuration merging error handling."""
        # Given
        base_config = {"step_count": 5}
        invalid_experiment_config = None  # This should cause an error

        with patch("app.ab_testing.framework.logger") as mock_logger:
            # When
            result = ab_orchestrator._merge_experiment_config(
                base_config, invalid_experiment_config
            )

        # Then
        assert result == base_config  # Should return original config
        mock_logger.error.assert_called_once()

    def test_track_onboarding_completion_success(self, ab_orchestrator, sample_user_id):
        """Test successful onboarding completion tracking."""
        # Given
        completion_data = {
            "completed": True,
            "completion_time_seconds": 180,
            "satisfaction_score": 4.5,
            "steps_completed": ["welcome", "categories", "preferences"],
        }
        experiment_context = [
            {
                "user_id": sample_user_id,
                "experiment_id": "onboarding_flow_v1",
                "variant_id": "treatment",
            }
        ]

        ab_orchestrator.experiment_manager.track_event = Mock()

        # When
        ab_orchestrator.track_onboarding_completion(
            sample_user_id, completion_data, experiment_context
        )

        # Then
        assert ab_orchestrator.experiment_manager.track_event.call_count == 2
        # Check that both general and experiment-specific events were tracked

    def test_track_onboarding_completion_no_context(
        self, ab_orchestrator, sample_user_id
    ):
        """Test onboarding completion tracking without experiment context."""
        # Given
        completion_data = {"completed": True, "completion_time_seconds": 120}

        ab_orchestrator.experiment_manager.get_user_assignments.return_value = []
        ab_orchestrator.experiment_manager.track_event = Mock()

        # When
        ab_orchestrator.track_onboarding_completion(sample_user_id, completion_data)

        # Then
        ab_orchestrator.experiment_manager.get_user_assignments.assert_called_once_with(
            sample_user_id
        )
        ab_orchestrator.experiment_manager.track_event.assert_called_once()

    def test_track_onboarding_completion_error_handling(
        self, ab_orchestrator, sample_user_id
    ):
        """Test error handling in completion tracking."""
        # Given
        completion_data = {"completed": True}
        ab_orchestrator.experiment_manager.track_event.side_effect = Exception(
            "Tracking error"
        )

        with patch("app.ab_testing.framework.logger") as mock_logger:
            # When
            ab_orchestrator.track_onboarding_completion(sample_user_id, completion_data)

        # Then
        mock_logger.error.assert_called()


@pytest.mark.integration
class TestABTestingIntegration:
    """Integration tests for A/B testing framework."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def ab_testing_system(self, mock_db):
        """Create complete A/B testing system."""
        return {
            "experiment_manager": ExperimentManager(db=mock_db),
            "analyzer": ABTestAnalyzer(db=mock_db),
            "orchestrator": ABTestOrchestrator(db=mock_db),
        }

    def test_complete_ab_test_lifecycle_e2e(self, ab_testing_system):
        """Test complete A/B test lifecycle end-to-end."""
        # Given
        user_id = str(uuid4())
        experiment_manager = ab_testing_system["experiment_manager"]
        analyzer = ab_testing_system["analyzer"]
        orchestrator = ab_testing_system["orchestrator"]

        user_context = {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios"},
        }

        base_config = {"step_count": 5, "flow_type": "standard"}

        # When - Step 1: Create experiment
        experiment_config = {
            "name": "Integration Test Experiment",
            "variants": {
                "control": {
                    "allocation": 0.5,
                    "type": VariantType.CONTROL.value,
                    "config": {"flow_type": "standard"},
                },
                "treatment": {
                    "allocation": 0.5,
                    "type": VariantType.TREATMENT.value,
                    "config": {"flow_type": "streamlined", "step_count": 3},
                },
            },
            "metrics": {"primary": "completion_rate"},
        }

        created_experiment = experiment_manager.create_experiment(experiment_config)

        # When - Step 2: Run experiment for user
        with patch.object(
            experiment_manager, "get_user_assignments"
        ) as mock_assignments:
            mock_assignments.return_value = [
                {
                    "user_id": user_id,
                    "experiment_id": created_experiment["id"],
                    "variant_id": "treatment",
                    "variant_config": {"flow_type": "streamlined", "step_count": 3},
                }
            ]

            experiment_result = orchestrator.run_onboarding_experiment(
                user_id, base_config, user_context
            )

        # When - Step 3: Track completion
        completion_data = {
            "completed": True,
            "completion_time_seconds": 120,
            "satisfaction_score": 4.5,
        }

        orchestrator.experiment_manager.track_event = Mock()
        orchestrator.track_onboarding_completion(user_id, completion_data)

        # When - Step 4: Analyze results
        analysis_result = analyzer.analyze_experiment_results(created_experiment["id"])

        # When - Step 5: Generate report
        report = analyzer.generate_experiment_report(
            created_experiment["id"], analysis_result
        )

        # Then
        assert created_experiment["status"] == ExperimentStatus.DRAFT.value
        assert experiment_result["base_config_modified"] is True
        assert experiment_result["final_onboarding_config"]["step_count"] == 3
        assert analysis_result["experiment_id"] == created_experiment["id"]
        assert report["experiment_id"] == created_experiment["id"]
        assert report["report_type"] == "final_analysis"

    def test_multi_experiment_assignment_e2e(self, ab_testing_system):
        """Test user assignment to multiple experiments simultaneously."""
        # Given
        user_id = str(uuid4())
        experiment_manager = ab_testing_system["experiment_manager"]
        orchestrator = ab_testing_system["orchestrator"]

        user_context = {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios"},
        }

        # Mock multiple experiment assignments
        mock_assignments = [
            {
                "user_id": user_id,
                "experiment_id": "onboarding_flow_v1",
                "variant_id": "treatment",
                "variant_config": {"step_count": 3},
            },
            {
                "user_id": user_id,
                "experiment_id": "personalization_level_test",
                "variant_id": "moderate",
                "variant_config": {"personalization_level": "moderate"},
            },
        ]

        # When
        with patch.object(
            experiment_manager, "get_user_assignments"
        ) as mock_get_assignments:
            mock_get_assignments.return_value = mock_assignments

            base_config = {"step_count": 5, "personalization_level": "minimal"}
            result = orchestrator.run_onboarding_experiment(
                user_id, base_config, user_context
            )

        # Then
        assert len(result["applied_experiments"]) == 2
        assert result["final_onboarding_config"]["step_count"] == 3
        assert result["final_onboarding_config"]["personalization_level"] == "moderate"

    def test_experiment_statistical_analysis_e2e(self, ab_testing_system):
        """Test end-to-end statistical analysis workflow."""
        # Given
        analyzer = ab_testing_system["analyzer"]
        experiment_id = "statistical_test_experiment"

        # When - Step 1: Analyze experiment results
        analysis_results = analyzer.analyze_experiment_results(experiment_id)

        # When - Step 2: Calculate statistical significance
        control_data = {"value": 0.72, "sample_size": 1250}
        treatment_data = {"value": 0.78, "sample_size": 1280}

        significance = analyzer.calculate_statistical_significance(
            control_data, treatment_data, "conversion"
        )

        # When - Step 3: Calculate business impact
        business_impact = analyzer._calculate_business_impact(analysis_results)

        # When - Step 4: Generate comprehensive report
        report = analyzer.generate_experiment_report(experiment_id, analysis_results)

        # Then
        assert analysis_results["experiment_id"] == experiment_id
        assert "recommendation" in analysis_results
        assert significance["significant"] in [True, False]
        assert "statistical_power" in significance
        assert "estimated_annual_revenue_impact" in business_impact
        assert report["executive_summary"]["business_impact"] == business_impact
