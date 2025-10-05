"""Test cases for personalization service functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.services.content.dynamic_content_service import DynamicContentGenerator
from app.services.ml.personalization_service import (
    OnboardingPersonalizationEngine,
    PersonalizationOptimizer,
)
from app.services.monitoring.performance_metrics_service import (
    MetricsAggregator,
    PerformanceMetricsCollector,
)


class TestOnboardingPersonalizationEngine:
    """Test cases for OnboardingPersonalizationEngine."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def personalization_engine(self, mock_db):
        """Create OnboardingPersonalizationEngine instance."""
        return OnboardingPersonalizationEngine(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "device_info": {"platform": "ios", "version": "15.0"},
            "signup_source": "organic",
            "time_of_signup": "evening",
            "referral_data": None,
        }

    def test_get_personalized_onboarding_flow_tech_savvy(
        self, personalization_engine, sample_user_id, sample_user_context
    ):
        """Test personalized flow for tech-savvy users."""
        # Given
        sample_user_context["user_behavior_signals"] = {
            "quick_decisions": True,
            "skips_tutorials": True,
        }

        with patch.object(
            personalization_engine, "_determine_user_segment"
        ) as mock_segment:
            mock_segment.return_value = "tech_savvy"

            # When
            result = personalization_engine.get_personalized_onboarding_flow(
                sample_user_id, sample_user_context
            )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["user_segment"] == "tech_savvy"
        assert result["flow_configuration"]["step_count"] <= 4
        assert result["flow_configuration"]["skip_optional_steps"] is True
        assert "personalized_content" in result

    def test_get_personalized_onboarding_flow_casual_user(
        self, personalization_engine, sample_user_id, sample_user_context
    ):
        """Test personalized flow for casual users."""
        # Given
        sample_user_context["user_behavior_signals"] = {
            "quick_decisions": False,
            "needs_guidance": True,
        }

        with patch.object(
            personalization_engine, "_determine_user_segment"
        ) as mock_segment:
            mock_segment.return_value = "casual_user"

            # When
            result = personalization_engine.get_personalized_onboarding_flow(
                sample_user_id, sample_user_context
            )

        # Then
        assert result["user_segment"] == "casual_user"
        assert result["flow_configuration"]["step_count"] == 5
        assert result["flow_configuration"]["provide_explanations"] is True
        assert result["flow_configuration"]["show_progress"] is True

    def test_get_personalized_onboarding_flow_visual_learner(
        self, personalization_engine, sample_user_id, sample_user_context
    ):
        """Test personalized flow for visual learners."""
        # Given
        with patch.object(
            personalization_engine, "_determine_user_segment"
        ) as mock_segment:
            mock_segment.return_value = "visual_learner"

            # When
            result = personalization_engine.get_personalized_onboarding_flow(
                sample_user_id, sample_user_context
            )

        # Then
        assert result["user_segment"] == "visual_learner"
        assert result["flow_configuration"]["visual_elements"] is True
        assert result["flow_configuration"]["use_images"] is True
        assert "image_suggestions" in result["personalized_content"]

    def test_determine_user_segment_tech_savvy(self, personalization_engine):
        """Test user segment determination for tech-savvy users."""
        # Given
        user_context = {
            "device_info": {"platform": "android"},
            "user_behavior_signals": {
                "quick_decisions": True,
                "skips_tutorials": True,
                "uses_shortcuts": True,
            },
        }

        # When
        segment = personalization_engine._determine_user_segment(
            "user123", user_context
        )

        # Then
        assert segment == "tech_savvy"

    def test_determine_user_segment_goal_oriented(self, personalization_engine):
        """Test user segment determination for goal-oriented users."""
        # Given
        user_context = {
            "signup_source": "search",
            "user_behavior_signals": {
                "focused_interaction": True,
                "task_oriented": True,
            },
        }

        # When
        segment = personalization_engine._determine_user_segment(
            "user123", user_context
        )

        # Then
        assert segment == "goal_oriented"

    def test_optimize_flow_structure_streamlined(self, personalization_engine):
        """Test flow structure optimization for streamlined flow."""
        # Given
        segment = "tech_savvy"
        adjustments = {"step_count": 3, "skip_optional_steps": True}

        # When
        structure = personalization_engine._optimize_flow_structure(
            segment, adjustments
        )

        # Then
        assert structure["flow_type"] == "streamlined"
        assert len(structure["required_steps"]) <= 3
        assert structure["optional_steps"] == []

    def test_optimize_flow_structure_guided(self, personalization_engine):
        """Test flow structure optimization for guided flow."""
        # Given
        segment = "casual_user"
        adjustments = {"step_count": 5, "provide_explanations": True}

        # When
        structure = personalization_engine._optimize_flow_structure(
            segment, adjustments
        )

        # Then
        assert structure["flow_type"] == "guided"
        assert len(structure["required_steps"]) == 5
        assert structure["include_help_text"] is True

    def test_generate_personalized_content_tech_savvy(self, personalization_engine):
        """Test personalized content generation for tech-savvy users."""
        # Given
        segment = "tech_savvy"
        adjustments = {"concise_language": True, "technical_terms": True}

        # When
        content = personalization_engine._generate_personalized_content(
            segment, adjustments
        )

        # Then
        assert content["tone"] == "concise"
        assert content["use_technical_terms"] is True
        assert "shortcuts_available" in content["hints"]

    def test_generate_personalized_content_visual_learner(self, personalization_engine):
        """Test personalized content generation for visual learners."""
        # Given
        segment = "visual_learner"
        adjustments = {"visual_elements": True, "use_images": True}

        # When
        content = personalization_engine._generate_personalized_content(
            segment, adjustments
        )

        # Then
        assert content["visual_emphasis"] is True
        assert "image_suggestions" in content
        assert content["use_icons"] is True

    def test_analyze_user_engagement_high_engagement(self, personalization_engine):
        """Test user engagement analysis for highly engaged users."""
        # Given
        user_id = "user123"
        session_data = {
            "total_time_seconds": 180,
            "steps_completed": 4,
            "interactions": 15,
            "help_requested": 0,
        }

        # When
        analysis = personalization_engine.analyze_user_engagement(user_id, session_data)

        # Then
        assert analysis["user_id"] == user_id
        assert analysis["engagement_level"] == "high"
        assert analysis["engagement_score"] >= 0.8
        assert analysis["needs_assistance"] is False

    def test_analyze_user_engagement_low_engagement(self, personalization_engine):
        """Test user engagement analysis for low engagement users."""
        # Given
        user_id = "user123"
        session_data = {
            "total_time_seconds": 600,  # Spending too much time
            "steps_completed": 1,
            "interactions": 3,
            "help_requested": 5,
        }

        # When
        analysis = personalization_engine.analyze_user_engagement(user_id, session_data)

        # Then
        assert analysis["engagement_level"] == "low"
        assert analysis["engagement_score"] <= 0.4
        assert analysis["needs_assistance"] is True
        assert "struggling_indicators" in analysis

    def test_update_personalization_rules_success(
        self, personalization_engine, sample_user_id
    ):
        """Test successful personalization rules update."""
        # Given
        performance_data = {
            "completion_rates": {"tech_savvy": 0.85, "casual_user": 0.72},
            "average_time": {"tech_savvy": 120, "casual_user": 240},
            "satisfaction_scores": {"tech_savvy": 4.2, "casual_user": 4.0},
        }

        personalization_engine.db.add = Mock()
        personalization_engine.db.commit = Mock()

        # When
        result = personalization_engine.update_personalization_rules(
            sample_user_id, performance_data
        )

        # Then
        assert result["rules_updated"] is True
        assert result["updated_segments"] > 0
        personalization_engine.db.commit.assert_called_once()

    def test_get_adaptive_recommendations_success(
        self, personalization_engine, sample_user_id
    ):
        """Test adaptive recommendations generation."""
        # Given
        current_behavior = {
            "time_on_current_step": 45,
            "interactions_count": 5,
            "help_requests": 1,
        }

        # When
        result = personalization_engine.get_adaptive_recommendations(
            sample_user_id, current_behavior
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert "adaptation_confidence" in result

    def test_track_personalization_effectiveness(
        self, personalization_engine, sample_user_id
    ):
        """Test personalization effectiveness tracking."""
        # Given
        outcome_data = {
            "completed": True,
            "completion_time": 180,
            "satisfaction_rating": 4.5,
            "steps_skipped": 1,
        }

        personalization_engine.db.add = Mock()
        personalization_engine.db.commit = Mock()

        # When
        result = personalization_engine.track_personalization_effectiveness(
            sample_user_id, outcome_data
        )

        # Then
        assert result["tracking_recorded"] is True
        assert result["user_id"] == sample_user_id
        personalization_engine.db.commit.assert_called_once()


class TestPersonalizationOptimizer:
    """Test cases for PersonalizationOptimizer."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def optimizer(self, mock_db):
        """Create PersonalizationOptimizer instance."""
        return PersonalizationOptimizer(db=mock_db)

    def test_optimize_personalization_rules_success(self, optimizer):
        """Test successful personalization rules optimization."""
        # Given
        historical_data = {
            "user_segments": {
                "tech_savvy": {
                    "completion_rate": 0.85,
                    "avg_time": 120,
                    "satisfaction": 4.2,
                    "sample_size": 1000,
                },
                "casual_user": {
                    "completion_rate": 0.72,
                    "avg_time": 240,
                    "satisfaction": 4.0,
                    "sample_size": 800,
                },
            }
        }

        # When
        result = optimizer.optimize_personalization_rules(historical_data)

        # Then
        assert result["optimization_completed"] is True
        assert "optimized_rules" in result
        assert len(result["performance_improvements"]) > 0

    def test_analyze_segment_performance_high_performing(self, optimizer):
        """Test segment performance analysis for high-performing segments."""
        # Given
        segment_data = {
            "completion_rate": 0.90,
            "avg_completion_time": 120,
            "satisfaction_score": 4.5,
            "dropout_rate": 0.05,
            "sample_size": 1000,
        }

        # When
        analysis = optimizer._analyze_segment_performance("tech_savvy", segment_data)

        # Then
        assert analysis["segment"] == "tech_savvy"
        assert analysis["performance_score"] >= 0.8
        assert analysis["needs_optimization"] is False
        assert analysis["strengths"] is not None

    def test_analyze_segment_performance_low_performing(self, optimizer):
        """Test segment performance analysis for low-performing segments."""
        # Given
        segment_data = {
            "completion_rate": 0.45,
            "avg_completion_time": 400,
            "satisfaction_score": 3.0,
            "dropout_rate": 0.35,
            "sample_size": 500,
        }

        # When
        analysis = optimizer._analyze_segment_performance(
            "struggling_user", segment_data
        )

        # Then
        assert analysis["performance_score"] <= 0.5
        assert analysis["needs_optimization"] is True
        assert len(analysis["improvement_areas"]) > 0

    def test_generate_optimization_recommendations(self, optimizer):
        """Test optimization recommendations generation."""
        # Given
        performance_issues = [
            {
                "segment": "casual_user",
                "issue": "high_dropout_rate",
                "severity": "high",
                "current_value": 0.35,
                "target_value": 0.15,
            },
            {
                "segment": "visual_learner",
                "issue": "low_satisfaction",
                "severity": "medium",
                "current_value": 3.2,
                "target_value": 4.0,
            },
        ]

        # When
        recommendations = optimizer._generate_optimization_recommendations(
            performance_issues
        )

        # Then
        assert len(recommendations) >= 2
        assert all("segment" in rec for rec in recommendations)
        assert all("recommendation" in rec for rec in recommendations)
        assert all("expected_impact" in rec for rec in recommendations)

    def test_calculate_roi_positive_impact(self, optimizer):
        """Test ROI calculation for positive impact changes."""
        # Given
        current_metrics = {"completion_rate": 0.70, "avg_satisfaction": 3.8}
        optimized_metrics = {"completion_rate": 0.85, "avg_satisfaction": 4.3}
        implementation_cost = 5000

        # When
        roi = optimizer._calculate_roi(
            current_metrics, optimized_metrics, implementation_cost
        )

        # Then
        assert roi["roi_percentage"] > 0
        assert roi["estimated_additional_revenue"] > 0
        assert roi["payback_period_months"] > 0

    def test_validate_optimization_parameters(self, optimizer):
        """Test optimization parameters validation."""
        # Given
        valid_params = {
            "min_sample_size": 100,
            "confidence_level": 0.95,
            "target_completion_rate": 0.80,
            "max_completion_time": 300,
        }

        invalid_params = {
            "min_sample_size": 10,  # Too small
            "confidence_level": 1.5,  # Invalid range
            "target_completion_rate": -0.1,  # Negative
        }

        # When
        valid_result = optimizer._validate_optimization_parameters(valid_params)
        invalid_result = optimizer._validate_optimization_parameters(invalid_params)

        # Then
        assert valid_result["valid"] is True
        assert len(valid_result["errors"]) == 0

        assert invalid_result["valid"] is False
        assert len(invalid_result["errors"]) > 0


class TestDynamicContentGenerator:
    """Test cases for DynamicContentGenerator."""

    @pytest.fixture
    def content_generator(self):
        """Create DynamicContentGenerator instance."""
        return DynamicContentGenerator()

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios"},
            "preferences": {"categories": ["restaurant", "cafe"]},
            "location": "Seoul",
        }

    def test_generate_personalized_content_tech_savvy(
        self, content_generator, sample_user_context
    ):
        """Test personalized content generation for tech-savvy users."""
        # Given
        content_type = "onboarding_welcome"

        # When
        result = content_generator.generate_personalized_content(
            content_type, sample_user_context
        )

        # Then
        assert result["content_type"] == content_type
        assert result["user_segment"] == "tech_savvy"
        assert result["personalization_applied"] is True
        assert "title" in result["content"]
        assert "description" in result["content"]

    def test_generate_personalized_content_visual_learner(self, content_generator):
        """Test personalized content generation for visual learners."""
        # Given
        user_context = {
            "user_segment": "visual_learner",
            "device_info": {"platform": "android"},
        }
        content_type = "category_selection_help"

        # When
        result = content_generator.generate_personalized_content(
            content_type, user_context
        )

        # Then
        assert result["user_segment"] == "visual_learner"
        assert result["content"]["visual_elements"] is True
        assert "image_urls" in result["content"]
        assert "icons" in result["content"]

    def test_adapt_content_for_segment_casual_user(self, content_generator):
        """Test content adaptation for casual users."""
        # Given
        base_content = {
            "title": "Select Categories",
            "description": "Choose your preferred place types",
        }
        segment = "casual_user"

        # When
        adapted = content_generator._adapt_content_for_segment(base_content, segment)

        # Then
        assert adapted["tone"] == "friendly"
        assert adapted["explanation_level"] == "detailed"
        assert len(adapted["description"]) > len(base_content["description"])

    def test_adapt_content_for_segment_goal_oriented(self, content_generator):
        """Test content adaptation for goal-oriented users."""
        # Given
        base_content = {
            "title": "Set Preferences",
            "description": "Configure your settings",
        }
        segment = "goal_oriented"

        # When
        adapted = content_generator._adapt_content_for_segment(base_content, segment)

        # Then
        assert adapted["tone"] == "efficient"
        assert adapted["focus"] == "outcome"
        assert "benefits" in adapted

    def test_get_contextual_variables(self, content_generator, sample_user_context):
        """Test contextual variables extraction."""
        # When
        variables = content_generator._get_contextual_variables(sample_user_context)

        # Then
        assert "user_segment" in variables
        assert "device_platform" in variables
        assert "location" in variables
        assert variables["user_segment"] == "tech_savvy"
        assert variables["device_platform"] == "ios"

    def test_apply_template_with_variables(self, content_generator):
        """Test template application with variables."""
        # Given
        template = (
            "Welcome, {{user_name}}! Let's set up your {{device_platform}} experience."
        )
        variables = {"user_name": "John", "device_platform": "iOS"}

        # When
        result = content_generator._apply_template(template, variables)

        # Then
        assert result == "Welcome, John! Let's set up your iOS experience."

    def test_generate_adaptive_hints_struggling_user(self, content_generator):
        """Test adaptive hints generation for struggling users."""
        # Given
        user_progress = {
            "current_step": "category_selection",
            "time_on_step": 180,  # 3 minutes - struggling
            "attempts": 3,
            "help_requested": 2,
        }
        user_context = {"user_segment": "casual_user"}

        # When
        hints = content_generator.generate_adaptive_hints(user_progress, user_context)

        # Then
        assert hints["struggling_detected"] is True
        assert hints["hint_level"] == "detailed"
        assert len(hints["suggestions"]) >= 3
        assert hints["encouragement_message"] is not None

    def test_generate_adaptive_hints_smooth_progress(self, content_generator):
        """Test adaptive hints generation for smooth progress."""
        # Given
        user_progress = {
            "current_step": "preferences_setup",
            "time_on_step": 30,  # Quick progress
            "attempts": 1,
            "help_requested": 0,
        }
        user_context = {"user_segment": "tech_savvy"}

        # When
        hints = content_generator.generate_adaptive_hints(user_progress, user_context)

        # Then
        assert hints["struggling_detected"] is False
        assert hints["hint_level"] == "minimal"
        assert len(hints["suggestions"]) <= 2


class TestPerformanceMetricsCollector:
    """Test cases for PerformanceMetricsCollector."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def metrics_collector(self, mock_db):
        """Create PerformanceMetricsCollector instance."""
        return PerformanceMetricsCollector(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_collect_onboarding_metrics_success(
        self, metrics_collector, sample_user_id
    ):
        """Test successful onboarding metrics collection."""
        # Given
        session_data = {
            "session_id": "session_123",
            "start_time": datetime.utcnow() - timedelta(minutes=5),
            "end_time": datetime.utcnow(),
            "completed": True,
            "steps_completed": 5,
            "total_steps": 5,
        }

        metrics_collector.db.add = Mock()
        metrics_collector.db.commit = Mock()

        # When
        result = metrics_collector.collect_onboarding_metrics(
            sample_user_id, session_data
        )

        # Then
        assert result["metrics_collected"] is True
        assert result["user_id"] == sample_user_id
        assert result["completion_rate"] == 1.0
        assert result["completion_time_minutes"] == 5.0
        metrics_collector.db.commit.assert_called_once()

    def test_collect_engagement_metrics_success(
        self, metrics_collector, sample_user_id
    ):
        """Test successful engagement metrics collection."""
        # Given
        engagement_data = {
            "session_duration_seconds": 300,
            "interactions_count": 15,
            "help_requests": 1,
            "feature_usage": {"skip_step": 1, "back_navigation": 2},
        }

        metrics_collector.db.add = Mock()
        metrics_collector.db.commit = Mock()

        # When
        result = metrics_collector.collect_engagement_metrics(
            sample_user_id, engagement_data
        )

        # Then
        assert result["metrics_collected"] is True
        assert result["engagement_score"] > 0
        assert result["interaction_rate"] > 0

    def test_collect_conversion_metrics_success(
        self, metrics_collector, sample_user_id
    ):
        """Test successful conversion metrics collection."""
        # Given
        conversion_data = {
            "funnel_stage": "onboarding_complete",
            "converted": True,
            "conversion_value": 25.0,
            "time_to_conversion_hours": 0.5,
        }

        metrics_collector.db.add = Mock()
        metrics_collector.db.commit = Mock()

        # When
        result = metrics_collector.collect_conversion_metrics(
            sample_user_id, conversion_data
        )

        # Then
        assert result["metrics_collected"] is True
        assert result["conversion_recorded"] is True
        assert result["conversion_value"] == 25.0

    def test_calculate_quality_score_high_quality(self, metrics_collector):
        """Test quality score calculation for high-quality session."""
        # Given
        metrics_data = {
            "completion_rate": 1.0,
            "completion_time_minutes": 3.5,
            "interaction_quality": 0.9,
            "help_usage_rate": 0.1,
        }

        # When
        score = metrics_collector._calculate_quality_score(metrics_data)

        # Then
        assert 0.8 <= score <= 1.0

    def test_calculate_quality_score_low_quality(self, metrics_collector):
        """Test quality score calculation for low-quality session."""
        # Given
        metrics_data = {
            "completion_rate": 0.3,
            "completion_time_minutes": 15.0,
            "interaction_quality": 0.2,
            "help_usage_rate": 0.8,
        }

        # When
        score = metrics_collector._calculate_quality_score(metrics_data)

        # Then
        assert 0.0 <= score <= 0.4

    def test_aggregate_metrics_by_timeframe(self, metrics_collector):
        """Test metrics aggregation by timeframe."""
        # Given
        timeframe = "daily"
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()

        mock_metrics = [
            Mock(
                completion_rate=0.85,
                completion_time_minutes=3.5,
                quality_score=0.8,
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            Mock(
                completion_rate=0.90,
                completion_time_minutes=3.0,
                quality_score=0.9,
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
        ]

        metrics_collector.db.query().filter().all.return_value = mock_metrics

        # When
        result = metrics_collector.aggregate_metrics_by_timeframe(
            timeframe, start_date, end_date
        )

        # Then
        assert result["timeframe"] == timeframe
        assert result["aggregated_data"] is not None
        assert "avg_completion_rate" in result["aggregated_data"]
        assert "avg_quality_score" in result["aggregated_data"]


class TestMetricsAggregator:
    """Test cases for MetricsAggregator."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def metrics_aggregator(self, mock_db):
        """Create MetricsAggregator instance."""
        return MetricsAggregator(db=mock_db)

    def test_generate_performance_dashboard_data(self, metrics_aggregator):
        """Test performance dashboard data generation."""
        # Given
        date_range = {
            "start_date": datetime.utcnow() - timedelta(days=30),
            "end_date": datetime.utcnow(),
        }

        mock_metrics = self._create_mock_metrics_data()
        metrics_aggregator.db.query().filter().all.return_value = mock_metrics

        # When
        result = metrics_aggregator.generate_performance_dashboard_data(date_range)

        # Then
        assert "summary" in result
        assert "trends" in result
        assert "segment_performance" in result
        assert result["summary"]["total_sessions"] > 0

    def test_calculate_business_impact_positive(self, metrics_aggregator):
        """Test business impact calculation with positive metrics."""
        # Given
        metrics_data = {
            "baseline_completion_rate": 0.70,
            "current_completion_rate": 0.85,
            "monthly_users": 10000,
            "avg_conversion_value": 25.0,
        }

        # When
        impact = metrics_aggregator.calculate_business_impact(metrics_data)

        # Then
        assert impact["completion_rate_improvement"] > 0
        assert impact["estimated_additional_revenue"] > 0
        assert impact["roi_percentage"] > 0

    def test_identify_optimization_opportunities_success(self, metrics_aggregator):
        """Test optimization opportunities identification."""
        # Given
        performance_data = {
            "segment_performance": {
                "tech_savvy": {"completion_rate": 0.90, "satisfaction": 4.5},
                "casual_user": {"completion_rate": 0.60, "satisfaction": 3.2},
                "visual_learner": {"completion_rate": 0.75, "satisfaction": 4.0},
            }
        }

        # When
        opportunities = metrics_aggregator.identify_optimization_opportunities(
            performance_data
        )

        # Then
        assert len(opportunities) > 0
        assert any(opp["segment"] == "casual_user" for opp in opportunities)
        assert all("priority" in opp for opp in opportunities)

    def _create_mock_metrics_data(self):
        """Create mock metrics data for testing."""
        return [
            Mock(
                user_segment="tech_savvy",
                completion_rate=0.90,
                completion_time_minutes=2.5,
                quality_score=0.9,
                satisfaction_rating=4.5,
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            Mock(
                user_segment="casual_user",
                completion_rate=0.70,
                completion_time_minutes=4.0,
                quality_score=0.7,
                satisfaction_rating=3.8,
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
        ]


@pytest.mark.integration
class TestPersonalizationIntegration:
    """Integration tests for personalization system."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def personalization_system(self, mock_db):
        """Create full personalization system."""
        return {
            "engine": OnboardingPersonalizationEngine(db=mock_db),
            "optimizer": PersonalizationOptimizer(db=mock_db),
            "content_generator": DynamicContentGenerator(),
            "metrics_collector": PerformanceMetricsCollector(db=mock_db),
            "metrics_aggregator": MetricsAggregator(db=mock_db),
        }

    def test_complete_personalization_flow_e2e(self, personalization_system):
        """Test complete end-to-end personalization flow."""
        # Given
        user_id = str(uuid4())
        user_context = {
            "device_info": {"platform": "ios"},
            "user_behavior_signals": {"quick_decisions": True},
        }

        engine = personalization_system["engine"]
        content_generator = personalization_system["content_generator"]
        metrics_collector = personalization_system["metrics_collector"]

        # Mock database operations
        engine.db.add = Mock()
        engine.db.commit = Mock()
        metrics_collector.db.add = Mock()
        metrics_collector.db.commit = Mock()

        # When - Step 1: Get personalized flow
        with patch.object(engine, "_determine_user_segment") as mock_segment:
            mock_segment.return_value = "tech_savvy"
            flow_result = engine.get_personalized_onboarding_flow(user_id, user_context)

        # When - Step 2: Generate personalized content
        content_result = content_generator.generate_personalized_content(
            "onboarding_welcome", {"user_segment": "tech_savvy"}
        )

        # When - Step 3: Track engagement
        session_data = {
            "session_id": "test_session",
            "start_time": datetime.utcnow() - timedelta(minutes=3),
            "end_time": datetime.utcnow(),
            "completed": True,
            "steps_completed": 3,
            "total_steps": 3,
        }
        metrics_result = metrics_collector.collect_onboarding_metrics(
            user_id, session_data
        )

        # When - Step 4: Analyze engagement
        engagement_analysis = engine.analyze_user_engagement(
            user_id,
            {
                "total_time_seconds": 180,
                "steps_completed": 3,
                "interactions": 10,
                "help_requested": 0,
            },
        )

        # Then
        assert flow_result["user_segment"] == "tech_savvy"
        assert flow_result["flow_configuration"]["step_count"] <= 4
        assert content_result["personalization_applied"] is True
        assert metrics_result["metrics_collected"] is True
        assert engagement_analysis["engagement_level"] == "high"

    def test_personalization_optimization_cycle_e2e(self, personalization_system):
        """Test complete personalization optimization cycle."""
        # Given
        optimizer = personalization_system["optimizer"]
        metrics_aggregator = personalization_system["metrics_aggregator"]

        historical_data = {
            "user_segments": {
                "tech_savvy": {
                    "completion_rate": 0.85,
                    "avg_time": 120,
                    "satisfaction": 4.2,
                    "sample_size": 1000,
                },
                "casual_user": {
                    "completion_rate": 0.65,
                    "avg_time": 280,
                    "satisfaction": 3.5,
                    "sample_size": 800,
                },
            }
        }

        # When - Step 1: Analyze current performance
        dashboard_data = metrics_aggregator.generate_performance_dashboard_data(
            {
                "start_date": datetime.utcnow() - timedelta(days=30),
                "end_date": datetime.utcnow(),
            }
        )

        # When - Step 2: Identify optimization opportunities
        opportunities = metrics_aggregator.identify_optimization_opportunities(
            {"segment_performance": historical_data["user_segments"]}
        )

        # When - Step 3: Optimize personalization rules
        optimization_result = optimizer.optimize_personalization_rules(historical_data)

        # When - Step 4: Calculate business impact
        impact = metrics_aggregator.calculate_business_impact(
            {
                "baseline_completion_rate": 0.65,
                "current_completion_rate": 0.85,
                "monthly_users": 10000,
                "avg_conversion_value": 25.0,
            }
        )

        # Then
        assert "summary" in dashboard_data
        assert len(opportunities) > 0
        assert optimization_result["optimization_completed"] is True
        assert impact["estimated_additional_revenue"] > 0
