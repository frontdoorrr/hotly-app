"""Test cases for onboarding analytics functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.analytics.onboarding import OnboardingAnalytics


class TestOnboardingAnalytics:
    """Test cases for OnboardingAnalytics."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def onboarding_analytics(self, mock_db):
        """Create OnboardingAnalytics instance."""
        return OnboardingAnalytics(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def sample_session_data(self):
        """Sample session data for testing."""
        return {
            "session_id": "session_123",
            "start_time": datetime.utcnow() - timedelta(minutes=5),
            "end_time": datetime.utcnow(),
            "steps_completed": ["welcome", "categories", "preferences"],
            "total_steps": 5,
            "interactions": [
                {
                    "step": "welcome",
                    "action": "next",
                    "timestamp": datetime.utcnow() - timedelta(minutes=5),
                },
                {
                    "step": "categories",
                    "action": "select",
                    "value": "restaurant",
                    "timestamp": datetime.utcnow() - timedelta(minutes=4),
                },
                {
                    "step": "categories",
                    "action": "select",
                    "value": "cafe",
                    "timestamp": datetime.utcnow() - timedelta(minutes=3.5),
                },
                {
                    "step": "preferences",
                    "action": "set_budget",
                    "value": "medium",
                    "timestamp": datetime.utcnow() - timedelta(minutes=2),
                },
            ],
            "help_requests": 1,
            "back_navigations": 0,
            "completion_status": "completed",
        }

    def test_analyze_user_behavior_patterns_success(
        self, onboarding_analytics, sample_user_id, sample_session_data
    ):
        """Test successful user behavior pattern analysis."""
        # When
        result = onboarding_analytics.analyze_user_behavior_patterns(
            sample_user_id, sample_session_data
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert "session_analysis" in result
        assert "engagement_patterns" in result
        assert "struggle_indicators" in result
        assert result["session_analysis"]["completion_rate"] == 0.6  # 3/5 steps
        assert result["session_analysis"]["total_time_minutes"] == 5.0

    def test_analyze_session_behavior_completed_session(
        self, onboarding_analytics, sample_session_data
    ):
        """Test session behavior analysis for completed session."""
        # When
        result = onboarding_analytics._analyze_session_behavior(sample_session_data)

        # Then
        assert result["completion_status"] == "completed"
        assert result["completion_rate"] == 0.6
        assert result["total_time_minutes"] == 5.0
        assert result["average_time_per_step"] == 5.0 / 3  # Only completed steps
        assert result["help_requests"] == 1
        assert result["back_navigations"] == 0

    def test_analyze_session_behavior_abandoned_session(self, onboarding_analytics):
        """Test session behavior analysis for abandoned session."""
        # Given
        abandoned_session_data = {
            "session_id": "abandoned_123",
            "start_time": datetime.utcnow() - timedelta(minutes=10),
            "end_time": None,  # Not completed
            "steps_completed": ["welcome"],
            "total_steps": 5,
            "interactions": [
                {
                    "step": "welcome",
                    "action": "next",
                    "timestamp": datetime.utcnow() - timedelta(minutes=10),
                },
            ],
            "help_requests": 3,
            "back_navigations": 2,
            "completion_status": "abandoned",
        }

        # When
        result = onboarding_analytics._analyze_session_behavior(abandoned_session_data)

        # Then
        assert result["completion_status"] == "abandoned"
        assert result["completion_rate"] == 0.2  # 1/5 steps
        assert result["help_requests"] == 3
        assert result["back_navigations"] == 2

    def test_analyze_engagement_patterns_high_engagement(
        self, onboarding_analytics, sample_session_data
    ):
        """Test engagement pattern analysis for highly engaged user."""
        # Given
        high_engagement_data = sample_session_data.copy()
        high_engagement_data["interactions"].extend(
            [
                {
                    "step": "preferences",
                    "action": "explore",
                    "timestamp": datetime.utcnow() - timedelta(minutes=1.5),
                },
                {
                    "step": "preferences",
                    "action": "customize",
                    "timestamp": datetime.utcnow() - timedelta(minutes=1),
                },
            ]
        )

        # When
        result = onboarding_analytics._analyze_engagement_patterns(high_engagement_data)

        # Then
        assert result["engagement_level"] == "high"
        assert result["interaction_rate"] > 1.0  # More than 1 interaction per minute
        assert result["engagement_score"] >= 0.7

    def test_analyze_engagement_patterns_low_engagement(self, onboarding_analytics):
        """Test engagement pattern analysis for low engagement user."""
        # Given
        low_engagement_data = {
            "session_id": "low_engagement_123",
            "start_time": datetime.utcnow() - timedelta(minutes=15),
            "end_time": datetime.utcnow(),
            "interactions": [
                {
                    "step": "welcome",
                    "action": "next",
                    "timestamp": datetime.utcnow() - timedelta(minutes=15),
                },
            ],
            "help_requests": 0,
        }

        # When
        result = onboarding_analytics._analyze_engagement_patterns(low_engagement_data)

        # Then
        assert result["engagement_level"] == "low"
        assert result["interaction_rate"] < 0.5
        assert result["engagement_score"] <= 0.4

    def test_identify_struggle_indicators_struggling_user(self, onboarding_analytics):
        """Test struggle indicator identification for struggling user."""
        # Given
        struggling_session_data = {
            "start_time": datetime.utcnow() - timedelta(minutes=20),
            "end_time": datetime.utcnow(),
            "steps_completed": ["welcome", "categories"],
            "total_steps": 5,
            "help_requests": 5,
            "back_navigations": 8,
            "interactions": [
                {
                    "step": "categories",
                    "action": "select",
                    "value": "restaurant",
                    "timestamp": datetime.utcnow() - timedelta(minutes=18),
                },
                {
                    "step": "categories",
                    "action": "deselect",
                    "value": "restaurant",
                    "timestamp": datetime.utcnow() - timedelta(minutes=17),
                },
                {
                    "step": "categories",
                    "action": "select",
                    "value": "cafe",
                    "timestamp": datetime.utcnow() - timedelta(minutes=16),
                },
                {
                    "step": "categories",
                    "action": "help_request",
                    "timestamp": datetime.utcnow() - timedelta(minutes=15),
                },
            ],
        }

        # When
        result = onboarding_analytics._identify_struggle_indicators(
            struggling_session_data
        )

        # Then
        assert result["struggling_detected"] is True
        assert result["struggle_score"] >= 0.6
        assert "excessive_time" in result["indicators"]
        assert "high_help_usage" in result["indicators"]
        assert "frequent_back_navigation" in result["indicators"]

    def test_identify_struggle_indicators_smooth_user(
        self, onboarding_analytics, sample_session_data
    ):
        """Test struggle indicator identification for smooth progression."""
        # When
        result = onboarding_analytics._identify_struggle_indicators(sample_session_data)

        # Then
        assert result["struggling_detected"] is False
        assert result["struggle_score"] <= 0.3
        assert len(result["indicators"]) <= 1  # Minimal struggle indicators

    def test_calculate_conversion_funnel_success(
        self, onboarding_analytics, sample_user_id
    ):
        """Test successful conversion funnel calculation."""
        # Given
        mock_sessions = [
            Mock(
                user_id=sample_user_id,
                steps_completed=["welcome", "categories", "preferences", "completion"],
                total_steps=5,
                completion_status="completed",
            ),
            Mock(
                user_id="user2",
                steps_completed=["welcome", "categories"],
                total_steps=5,
                completion_status="abandoned",
            ),
            Mock(
                user_id="user3",
                steps_completed=["welcome"],
                total_steps=5,
                completion_status="abandoned",
            ),
        ]

        onboarding_analytics.db.query().filter().all.return_value = mock_sessions

        # When
        result = onboarding_analytics.calculate_conversion_funnel(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
        )

        # Then
        assert result["total_sessions"] == 3
        assert result["funnel_stages"]["welcome"]["users"] == 3
        assert result["funnel_stages"]["welcome"]["conversion_rate"] == 1.0
        assert result["funnel_stages"]["categories"]["users"] == 2
        assert result["funnel_stages"]["categories"]["conversion_rate"] == 2 / 3
        assert result["funnel_stages"]["completion"]["users"] == 1
        assert result["overall_completion_rate"] == 1 / 3

    def test_analyze_drop_off_points_success(self, onboarding_analytics):
        """Test drop-off point analysis."""
        # Given
        mock_sessions = [
            Mock(
                steps_completed=["welcome", "categories"],
                total_steps=5,
                completion_status="abandoned",
                last_active_step="categories",
            ),
            Mock(
                steps_completed=["welcome", "categories", "preferences"],
                total_steps=5,
                completion_status="abandoned",
                last_active_step="preferences",
            ),
            Mock(
                steps_completed=["welcome"],
                total_steps=5,
                completion_status="abandoned",
                last_active_step="welcome",
            ),
        ]

        onboarding_analytics.db.query().filter().all.return_value = mock_sessions

        # When
        result = onboarding_analytics.analyze_drop_off_points(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
        )

        # Then
        assert "drop_off_analysis" in result
        assert len(result["drop_off_points"]) > 0
        assert any(point["step"] == "categories" for point in result["drop_off_points"])

    def test_generate_cohort_analysis_success(self, onboarding_analytics):
        """Test cohort analysis generation."""
        # Given
        mock_sessions = self._create_mock_cohort_data()
        onboarding_analytics.db.query().filter().all.return_value = mock_sessions

        # When
        result = onboarding_analytics.generate_cohort_analysis(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            cohort_type="weekly",
        )

        # Then
        assert result["cohort_type"] == "weekly"
        assert "cohorts" in result
        assert len(result["cohorts"]) > 0
        assert "overall_trends" in result

    def test_identify_optimization_opportunities_success(self, onboarding_analytics):
        """Test optimization opportunities identification."""
        # Given
        performance_data = {
            "funnel_analysis": {
                "funnel_stages": {
                    "welcome": {"conversion_rate": 0.95},
                    "categories": {"conversion_rate": 0.60},  # Low conversion
                    "preferences": {"conversion_rate": 0.85},
                    "completion": {"conversion_rate": 0.75},
                }
            },
            "drop_off_analysis": {
                "drop_off_points": [
                    {"step": "categories", "drop_off_rate": 0.40, "user_count": 400},
                    {"step": "preferences", "drop_off_rate": 0.15, "user_count": 150},
                ]
            },
            "average_completion_time": 450,  # 7.5 minutes - quite long
        }

        # When
        result = onboarding_analytics.identify_optimization_opportunities(
            performance_data
        )

        # Then
        assert len(result["opportunities"]) > 0
        assert any(
            opp["type"] == "conversion_optimization"
            and "categories" in opp["description"]
            for opp in result["opportunities"]
        )
        assert any(
            opp["type"] == "time_optimization" for opp in result["opportunities"]
        )

    def test_calculate_engagement_score_high_engagement(self, onboarding_analytics):
        """Test engagement score calculation for highly engaged session."""
        # Given
        session_data = {
            "total_time_minutes": 3.5,  # Good time
            "interactions": [
                {"action": "interact"} for _ in range(15)
            ],  # Many interactions
            "help_requests": 0,  # No help needed
            "back_navigations": 0,  # No confusion
            "completion_rate": 1.0,  # Completed
        }

        # When
        score = onboarding_analytics._calculate_engagement_score(session_data)

        # Then
        assert 0.8 <= score <= 1.0

    def test_calculate_engagement_score_low_engagement(self, onboarding_analytics):
        """Test engagement score calculation for low engagement session."""
        # Given
        session_data = {
            "total_time_minutes": 15.0,  # Too long
            "interactions": [
                {"action": "interact"} for _ in range(2)
            ],  # Few interactions
            "help_requests": 5,  # Many help requests
            "back_navigations": 8,  # Lots of confusion
            "completion_rate": 0.2,  # Barely started
        }

        # When
        score = onboarding_analytics._calculate_engagement_score(session_data)

        # Then
        assert 0.0 <= score <= 0.3

    def test_generate_performance_dashboard_data(self, onboarding_analytics):
        """Test performance dashboard data generation."""
        # Given
        date_range = {
            "start_date": datetime.utcnow() - timedelta(days=30),
            "end_date": datetime.utcnow(),
        }

        mock_sessions = self._create_mock_performance_data()
        onboarding_analytics.db.query().filter().all.return_value = mock_sessions

        # When
        result = onboarding_analytics.generate_performance_dashboard_data(date_range)

        # Then
        assert "summary_metrics" in result
        assert "trend_data" in result
        assert "segment_performance" in result
        assert result["summary_metrics"]["total_sessions"] > 0
        assert result["summary_metrics"]["completion_rate"] >= 0

    def test_track_user_journey_milestone_success(
        self, onboarding_analytics, sample_user_id
    ):
        """Test user journey milestone tracking."""
        # Given
        milestone_data = {
            "milestone": "first_category_selection",
            "step": "categories",
            "timestamp": datetime.utcnow(),
            "user_context": {"user_segment": "tech_savvy"},
            "metadata": {"categories_selected": ["restaurant", "cafe"]},
        }

        onboarding_analytics.db.add = Mock()
        onboarding_analytics.db.commit = Mock()

        # When
        result = onboarding_analytics.track_user_journey_milestone(
            sample_user_id, milestone_data
        )

        # Then
        assert result["milestone_tracked"] is True
        assert result["user_id"] == sample_user_id
        assert result["milestone"] == "first_category_selection"
        onboarding_analytics.db.commit.assert_called_once()

    def test_predict_completion_likelihood_high_likelihood(
        self, onboarding_analytics, sample_user_id
    ):
        """Test completion likelihood prediction for high probability user."""
        # Given
        current_progress = {
            "steps_completed": ["welcome", "categories", "preferences"],
            "total_steps": 5,
            "time_spent_minutes": 2.5,
            "interaction_count": 12,
            "help_requests": 0,
        }

        # When
        result = onboarding_analytics.predict_completion_likelihood(
            sample_user_id, current_progress
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["completion_probability"] >= 0.7
        assert result["confidence_level"] == "high"
        assert len(result["key_factors"]) > 0

    def test_predict_completion_likelihood_low_likelihood(
        self, onboarding_analytics, sample_user_id
    ):
        """Test completion likelihood prediction for low probability user."""
        # Given
        current_progress = {
            "steps_completed": ["welcome"],
            "total_steps": 5,
            "time_spent_minutes": 8.0,  # Taking too long
            "interaction_count": 3,  # Very few interactions
            "help_requests": 4,  # Lots of help needed
        }

        # When
        result = onboarding_analytics.predict_completion_likelihood(
            sample_user_id, current_progress
        )

        # Then
        assert result["completion_probability"] <= 0.4
        assert result["confidence_level"] in ["medium", "high"]
        assert "intervention_recommended" in result
        assert result["intervention_recommended"] is True

    def _create_mock_cohort_data(self):
        """Create mock cohort data for testing."""
        cohorts = []
        base_date = datetime.utcnow() - timedelta(days=21)

        for week in range(3):
            week_start = base_date + timedelta(days=week * 7)
            for user in range(10):
                cohorts.append(
                    Mock(
                        user_id=f"user_{week}_{user}",
                        created_at=week_start + timedelta(days=user % 7),
                        steps_completed=(
                            ["welcome", "categories"][:2]
                            if user < 7
                            else ["welcome", "categories", "preferences", "completion"]
                        ),
                        completion_status="completed" if user >= 7 else "abandoned",
                        total_steps=5,
                    )
                )

        return cohorts

    def _create_mock_performance_data(self):
        """Create mock performance data for testing."""
        sessions = []
        base_date = datetime.utcnow() - timedelta(days=30)

        for day in range(30):
            session_date = base_date + timedelta(days=day)
            for session in range(5):  # 5 sessions per day
                completion_rate = 0.8 if session < 4 else 0.2  # 80% completion rate
                sessions.append(
                    Mock(
                        user_id=f"user_{day}_{session}",
                        created_at=session_date,
                        steps_completed=(
                            ["welcome", "categories", "preferences", "completion"]
                            if completion_rate > 0.5
                            else ["welcome"]
                        ),
                        completion_status=(
                            "completed" if completion_rate > 0.5 else "abandoned"
                        ),
                        total_steps=5,
                        session_duration_minutes=3.5 if completion_rate > 0.5 else 1.0,
                    )
                )

        return sessions


@pytest.mark.integration
class TestOnboardingAnalyticsIntegration:
    """Integration tests for onboarding analytics system."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def analytics_system(self, mock_db):
        """Create analytics system with dependencies."""
        return OnboardingAnalytics(db=mock_db)

    def test_complete_analytics_workflow_e2e(self, analytics_system):
        """Test complete analytics workflow end-to-end."""
        # Given
        user_id = str(uuid4())
        analytics_system.db.query().filter().all.return_value = (
            self._create_comprehensive_mock_data()
        )
        analytics_system.db.add = Mock()
        analytics_system.db.commit = Mock()

        session_data = {
            "session_id": "integration_test_session",
            "start_time": datetime.utcnow() - timedelta(minutes=4),
            "end_time": datetime.utcnow(),
            "steps_completed": ["welcome", "categories", "preferences"],
            "total_steps": 5,
            "interactions": [
                {
                    "step": "welcome",
                    "action": "next",
                    "timestamp": datetime.utcnow() - timedelta(minutes=4),
                },
                {
                    "step": "categories",
                    "action": "select",
                    "value": "restaurant",
                    "timestamp": datetime.utcnow() - timedelta(minutes=3),
                },
                {
                    "step": "preferences",
                    "action": "set_budget",
                    "value": "medium",
                    "timestamp": datetime.utcnow() - timedelta(minutes=1),
                },
            ],
            "help_requests": 1,
            "back_navigations": 0,
            "completion_status": "in_progress",
        }

        # When - Step 1: Analyze user behavior
        behavior_analysis = analytics_system.analyze_user_behavior_patterns(
            user_id, session_data
        )

        # When - Step 2: Calculate funnel conversion
        funnel_analysis = analytics_system.calculate_conversion_funnel(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
        )

        # When - Step 3: Identify drop-off points
        dropoff_analysis = analytics_system.analyze_drop_off_points(
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
        )

        # When - Step 4: Generate cohort analysis
        cohort_analysis = analytics_system.generate_cohort_analysis(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            cohort_type="weekly",
        )

        # When - Step 5: Predict completion likelihood
        completion_prediction = analytics_system.predict_completion_likelihood(
            user_id,
            {
                "steps_completed": ["welcome", "categories", "preferences"],
                "total_steps": 5,
                "time_spent_minutes": 4.0,
                "interaction_count": 3,
                "help_requests": 1,
            },
        )

        # When - Step 6: Identify optimization opportunities
        performance_data = {
            "funnel_analysis": funnel_analysis,
            "drop_off_analysis": dropoff_analysis,
            "average_completion_time": 4.0,
        }
        optimization_opportunities = (
            analytics_system.identify_optimization_opportunities(performance_data)
        )

        # When - Step 7: Generate dashboard data
        dashboard_data = analytics_system.generate_performance_dashboard_data(
            {
                "start_date": datetime.utcnow() - timedelta(days=7),
                "end_date": datetime.utcnow(),
            }
        )

        # When - Step 8: Track milestone
        milestone_result = analytics_system.track_user_journey_milestone(
            user_id,
            {
                "milestone": "preferences_completed",
                "step": "preferences",
                "timestamp": datetime.utcnow(),
                "user_context": {"user_segment": "tech_savvy"},
                "metadata": {"budget_level": "medium"},
            },
        )

        # Then
        assert behavior_analysis["user_id"] == user_id
        assert behavior_analysis["engagement_patterns"]["engagement_level"] in [
            "low",
            "medium",
            "high",
        ]
        assert funnel_analysis["total_sessions"] > 0
        assert dropoff_analysis["drop_off_analysis"] is not None
        assert cohort_analysis["cohort_type"] == "weekly"
        assert completion_prediction["completion_probability"] >= 0.0
        assert len(optimization_opportunities["opportunities"]) >= 0
        assert dashboard_data["summary_metrics"]["total_sessions"] > 0
        assert milestone_result["milestone_tracked"] is True

    def test_analytics_performance_optimization_cycle(self, analytics_system):
        """Test analytics-driven performance optimization cycle."""
        # Given
        analytics_system.db.query().filter().all.return_value = (
            self._create_performance_test_data()
        )

        date_range = {
            "start_date": datetime.utcnow() - timedelta(days=30),
            "end_date": datetime.utcnow(),
        }

        # When - Step 1: Baseline performance analysis
        baseline_dashboard = analytics_system.generate_performance_dashboard_data(
            date_range
        )
        baseline_funnel = analytics_system.calculate_conversion_funnel(
            date_range["start_date"], date_range["end_date"]
        )

        # When - Step 2: Identify optimization opportunities
        opportunities = analytics_system.identify_optimization_opportunities(
            {
                "funnel_analysis": baseline_funnel,
                "drop_off_analysis": analytics_system.analyze_drop_off_points(
                    date_range["start_date"], date_range["end_date"]
                ),
                "average_completion_time": 6.0,  # Above optimal
            }
        )

        # When - Step 3: Simulate improvement tracking
        # In a real scenario, this would be after implementing optimizations
        improved_data = self._create_improved_performance_data()
        analytics_system.db.query().filter().all.return_value = improved_data

        improved_dashboard = analytics_system.generate_performance_dashboard_data(
            date_range
        )
        improved_funnel = analytics_system.calculate_conversion_funnel(
            date_range["start_date"], date_range["end_date"]
        )

        # Then
        assert len(opportunities["opportunities"]) > 0
        assert (
            improved_dashboard["summary_metrics"]["completion_rate"]
            >= baseline_dashboard["summary_metrics"]["completion_rate"]
        )
        # In improved scenario, completion rate should be better or equal

    def _create_comprehensive_mock_data(self):
        """Create comprehensive mock data for integration testing."""
        sessions = []
        base_date = datetime.utcnow() - timedelta(days=7)

        # Create varied session data
        session_types = [
            {
                "completion_rate": 1.0,
                "time": 3,
                "status": "completed",
            },  # Fast completers
            {
                "completion_rate": 0.6,
                "time": 5,
                "status": "abandoned",
            },  # Slow progressers
            {
                "completion_rate": 0.2,
                "time": 1,
                "status": "abandoned",
            },  # Quick abandoners
        ]

        for day in range(7):
            session_date = base_date + timedelta(days=day)
            for session_type in session_types:
                for i in range(10):  # 10 sessions per type per day
                    steps = int(5 * session_type["completion_rate"])
                    sessions.append(
                        Mock(
                            user_id=f"user_{day}_{i}",
                            created_at=session_date,
                            steps_completed=[
                                "welcome",
                                "categories",
                                "preferences",
                                "setup",
                                "completion",
                            ][:steps],
                            completion_status=session_type["status"],
                            total_steps=5,
                            session_duration_minutes=session_type["time"],
                            last_active_step=[
                                "welcome",
                                "categories",
                                "preferences",
                                "setup",
                                "completion",
                            ][min(steps, 4)],
                        )
                    )

        return sessions

    def _create_performance_test_data(self):
        """Create performance test data with known characteristics."""
        sessions = []
        base_date = datetime.utcnow() - timedelta(days=30)

        # Create data with specific performance characteristics
        for day in range(30):
            session_date = base_date + timedelta(days=day)

            # 70% completion rate baseline
            for i in range(7):  # Completed sessions
                sessions.append(
                    Mock(
                        user_id=f"completed_user_{day}_{i}",
                        created_at=session_date,
                        steps_completed=[
                            "welcome",
                            "categories",
                            "preferences",
                            "setup",
                            "completion",
                        ],
                        completion_status="completed",
                        total_steps=5,
                        session_duration_minutes=4.0,
                    )
                )

            for i in range(3):  # Abandoned sessions
                sessions.append(
                    Mock(
                        user_id=f"abandoned_user_{day}_{i}",
                        created_at=session_date,
                        steps_completed=["welcome", "categories"],
                        completion_status="abandoned",
                        total_steps=5,
                        session_duration_minutes=8.0,
                        last_active_step="categories",
                    )
                )

        return sessions

    def _create_improved_performance_data(self):
        """Create improved performance data for comparison."""
        sessions = []
        base_date = datetime.utcnow() - timedelta(days=30)

        # Create data with improved performance characteristics
        for day in range(30):
            session_date = base_date + timedelta(days=day)

            # 85% completion rate - improved
            for i in range(8):  # More completed sessions
                sessions.append(
                    Mock(
                        user_id=f"completed_user_{day}_{i}",
                        created_at=session_date,
                        steps_completed=[
                            "welcome",
                            "categories",
                            "preferences",
                            "setup",
                            "completion",
                        ],
                        completion_status="completed",
                        total_steps=5,
                        session_duration_minutes=3.0,  # Faster completion
                    )
                )

            for i in range(2):  # Fewer abandoned sessions
                sessions.append(
                    Mock(
                        user_id=f"abandoned_user_{day}_{i}",
                        created_at=session_date,
                        steps_completed=[
                            "welcome",
                            "categories",
                            "preferences",
                        ],  # Get further
                        completion_status="abandoned",
                        total_steps=5,
                        session_duration_minutes=5.0,  # Less time wasted
                        last_active_step="preferences",
                    )
                )

        return sessions
