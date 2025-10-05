"""Integration and E2E tests for onboarding flow."""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.ab_testing.framework import ABTestOrchestrator
from app.analytics.onboarding import OnboardingAnalytics

# from app.schemas.preference import OnboardingStepRequest
from app.services.auth.onboarding_service import (
    OnboardingFlowManager,
    OnboardingService,
)
from app.services.auth.preference_service import (
    PreferenceSetupService,
    PreferenceSurveyService,
)
from app.services.auth.user_preference_service import UserPreferenceService
from app.services.ml.personalization_service import OnboardingPersonalizationEngine


@pytest.mark.integration
class TestOnboardingSystemIntegration:
    """Integration tests for the complete onboarding system."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session for all services."""
        db = Mock()
        db.query().filter().first.return_value = None
        db.query().filter().all.return_value = []
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        return db

    @pytest.fixture
    def onboarding_system(self, mock_db):
        """Create integrated onboarding system with all components."""
        return {
            "onboarding_service": OnboardingService(db=mock_db),
            "flow_manager": OnboardingFlowManager(),
            "preference_service": PreferenceSetupService(db_session=mock_db),
            "survey_service": PreferenceSurveyService(),
            "personalization_engine": OnboardingPersonalizationEngine(db=mock_db),
            "user_preference_service": UserPreferenceService(db=mock_db),
            "ab_orchestrator": ABTestOrchestrator(db=mock_db),
            "analytics": OnboardingAnalytics(db=mock_db),
        }

    @pytest.fixture
    def sample_user_profile(self):
        """Sample user profile for testing."""
        return {
            "user_id": str(uuid4()),
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios", "version": "15.0"},
            "signup_source": "organic",
            "location": {"country": "KR", "city": "Seoul"},
            "demographic_info": {"age_group": "25-34"},
        }

    def test_complete_onboarding_flow_tech_savvy_user(
        self, onboarding_system, sample_user_profile
    ):
        """Test complete onboarding flow for tech-savvy user."""
        # Given
        user_id = sample_user_profile["user_id"]
        user_context = {
            "user_segment": sample_user_profile["user_segment"],
            "device_info": sample_user_profile["device_info"],
        }

        onboarding_service = onboarding_system["onboarding_service"]
        onboarding_system["flow_manager"]
        onboarding_system["preference_service"]
        personalization_engine = onboarding_system["personalization_engine"]

        # Mock database interactions
        self._setup_database_mocks(onboarding_system, user_id)

        # When - Step 1: Create onboarding session
        session_result = onboarding_service.create_onboarding_session(user_id)

        # When - Step 2: Get personalized flow
        personalized_flow = personalization_engine.get_personalized_onboarding_flow(
            user_id, user_context
        )

        # When - Step 3: Process each step of onboarding
        onboarding_steps = [
            (
                OnboardingStep.CATEGORY_SELECTION,
                {"categories": ["restaurant", "cafe", "culture"]},
            ),
            (
                OnboardingStep.PREFERENCES_SETUP,
                {
                    "budget_level": "medium",
                    "location": {"lat": 37.5665, "lng": 126.9780},
                    "companion_type": "couple",
                },
            ),
            (
                OnboardingStep.SAMPLE_INTERACTION,
                {"samples_viewed": 3, "samples_saved": 1},
            ),
            (OnboardingStep.COMPLETION, {}),
        ]

        step_results = []
        for step, step_data in onboarding_steps:
            step_request = OnboardingStepRequest(
                user_id=user_id, step=step, step_data=step_data, completed=True
            )
            step_result = onboarding_service.update_onboarding_step(step_request)
            step_results.append(step_result)

        # When - Step 4: Complete onboarding
        completion_result = onboarding_service.complete_onboarding(user_id)

        # Then - Verify complete flow
        assert session_result["user_id"] == user_id
        assert session_result["status"] == "active"

        assert personalized_flow["user_segment"] == "tech_savvy"
        assert personalized_flow["flow_configuration"]["step_count"] <= 4

        assert all(result["step_updated"] for result in step_results)
        assert completion_result["onboarding_completed"] is True

        # Verify final state
        final_status = onboarding_service.get_onboarding_status(user_id)
        assert final_status["status"] == "completed"
        assert final_status["progress_percentage"] == 100.0

    def test_complete_onboarding_flow_casual_user(
        self, onboarding_system, sample_user_profile
    ):
        """Test complete onboarding flow for casual user with guidance."""
        # Given
        sample_user_profile["user_segment"] = "casual_user"
        user_id = sample_user_profile["user_id"]
        user_context = {"user_segment": "casual_user"}

        onboarding_service = onboarding_system["onboarding_service"]
        personalization_engine = onboarding_system["personalization_engine"]
        survey_service = onboarding_system["survey_service"]

        self._setup_database_mocks(onboarding_system, user_id)

        # When - Create session and get personalized flow
        onboarding_service.create_onboarding_session(user_id)
        personalized_flow = personalization_engine.get_personalized_onboarding_flow(
            user_id, user_context
        )

        # When - Generate adaptive survey for casual user
        initial_preferences = {"categories": ["restaurant", "cafe"]}
        survey = survey_service.generate_adaptive_survey(user_id, initial_preferences)

        # When - Process survey responses
        survey_responses = [
            ("dining_frequency", "주 2-3회", 8000),  # Normal response time
            ("cuisine_preferences", ["한식", "일식"], 12000),  # Thoughtful response
            ("social_vs_quiet", 3, 6000),  # Scale response
        ]

        response_results = []
        for question_id, response, response_time in survey_responses:
            response_result = survey_service.process_survey_response(
                survey["survey_id"], question_id, response, response_time
            )
            response_results.append(response_result)

        # Then - Verify casual user experience
        assert personalized_flow["flow_configuration"]["step_count"] == 5
        assert personalized_flow["flow_configuration"]["provide_explanations"] is True

        assert survey["adaptive_enabled"] is True
        assert survey["estimated_time_seconds"] <= 180

        assert all(result["response_recorded"] for result in response_results)
        # Casual user should have more moderate confidence levels
        confidence_levels = [
            result["adaptation_signals"]["confidence_level"]
            for result in response_results
        ]
        assert "medium" in confidence_levels

    def test_onboarding_with_ab_testing_integration(
        self, onboarding_system, sample_user_profile
    ):
        """Test onboarding flow with A/B testing integration."""
        # Given
        user_id = sample_user_profile["user_id"]
        user_context = sample_user_profile

        onboarding_service = onboarding_system["onboarding_service"]
        ab_orchestrator = onboarding_system["ab_orchestrator"]

        self._setup_database_mocks(onboarding_system, user_id)

        # Mock A/B test assignments
        mock_experiment_assignments = [
            {
                "user_id": user_id,
                "experiment_id": "onboarding_flow_v1",
                "variant_id": "treatment",
                "variant_config": {
                    "flow_type": "streamlined",
                    "step_count": 3,
                    "skip_optional_steps": True,
                },
            }
        ]

        ab_orchestrator.experiment_manager.get_user_assignments.return_value = (
            mock_experiment_assignments
        )
        ab_orchestrator.experiment_manager.track_event = Mock()

        # When - Run onboarding with A/B testing
        base_config = {"step_count": 5, "flow_type": "standard"}
        experiment_result = ab_orchestrator.run_onboarding_experiment(
            user_id, base_config, user_context
        )

        # When - Process onboarding with experimental config
        onboarding_service.create_onboarding_session(user_id)

        # Simulate streamlined flow (fewer steps)
        streamlined_steps = [
            (OnboardingStep.CATEGORY_SELECTION, {"categories": ["restaurant", "cafe"]}),
            (OnboardingStep.PREFERENCES_SETUP, {"budget_level": "medium"}),
            (OnboardingStep.COMPLETION, {}),
        ]

        for step, step_data in streamlined_steps:
            step_request = OnboardingStepRequest(
                user_id=user_id, step=step, step_data=step_data, completed=True
            )
            onboarding_service.update_onboarding_step(step_request)

        completion_result = onboarding_service.complete_onboarding(user_id)

        # When - Track A/B test completion
        completion_data = {
            "completed": True,
            "completion_time_seconds": 120,  # Fast due to streamlined flow
            "satisfaction_score": 4.5,
            "steps_completed": len(streamlined_steps),
        }

        ab_orchestrator.track_onboarding_completion(
            user_id, completion_data, mock_experiment_assignments
        )

        # Then - Verify A/B testing integration
        assert experiment_result["base_config_modified"] is True
        assert experiment_result["final_onboarding_config"]["step_count"] == 3
        assert (
            experiment_result["final_onboarding_config"]["flow_type"] == "streamlined"
        )

        assert completion_result["onboarding_completed"] is True
        assert ab_orchestrator.experiment_manager.track_event.call_count >= 2

    def test_onboarding_analytics_integration(
        self, onboarding_system, sample_user_profile
    ):
        """Test onboarding analytics integration throughout the flow."""
        # Given
        user_id = sample_user_profile["user_id"]

        onboarding_service = onboarding_system["onboarding_service"]
        analytics = onboarding_system["analytics"]

        self._setup_database_mocks(onboarding_system, user_id)

        # Mock analytics data
        mock_sessions = self._create_analytics_mock_data(user_id)
        analytics.db.query().filter().all.return_value = mock_sessions

        # When - Create session and track start
        session_start_time = datetime.utcnow()
        session_result = onboarding_service.create_onboarding_session(user_id)

        # When - Process onboarding with analytics tracking
        session_data = {
            "session_id": session_result["session_id"],
            "start_time": session_start_time,
            "end_time": None,  # Will be updated
            "steps_completed": [],
            "total_steps": 5,
            "interactions": [],
            "help_requests": 0,
            "back_navigations": 0,
            "completion_status": "in_progress",
        }

        # Simulate step-by-step progression with analytics
        steps = [
            OnboardingStep.CATEGORY_SELECTION,
            OnboardingStep.PREFERENCES_SETUP,
            OnboardingStep.SAMPLE_INTERACTION,
            OnboardingStep.COMPLETION,
        ]

        for i, step in enumerate(steps):
            # Update session data
            session_data["steps_completed"].append(step.value)
            session_data["interactions"].append(
                {
                    "step": step.value,
                    "action": "complete",
                    "timestamp": datetime.utcnow(),
                }
            )

            # Process step
            step_request = OnboardingStepRequest(
                user_id=user_id,
                step=step,
                step_data={"step_index": i},
                completed=True,
            )
            onboarding_service.update_onboarding_step(step_request)

            # Analyze behavior at each step
            behavior_analysis = analytics.analyze_user_behavior_patterns(
                user_id, session_data
            )

            # Track milestone
            milestone_data = {
                "milestone": f"{step.value}_completed",
                "step": step.value,
                "timestamp": datetime.utcnow(),
                "user_context": sample_user_profile,
                "metadata": {"step_index": i},
            }
            analytics.track_user_journey_milestone(user_id, milestone_data)

        # When - Complete onboarding
        session_data["end_time"] = datetime.utcnow()
        session_data["completion_status"] = "completed"

        completion_result = onboarding_service.complete_onboarding(user_id)

        # When - Predict completion likelihood (simulate mid-flow)
        mid_progress = {
            "steps_completed": ["welcome", "categories"],
            "total_steps": 5,
            "time_spent_minutes": 2.0,
            "interaction_count": 5,
            "help_requests": 0,
        }
        completion_prediction = analytics.predict_completion_likelihood(
            user_id, mid_progress
        )

        # When - Generate analytics reports
        funnel_analysis = analytics.calculate_conversion_funnel(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
        )

        dashboard_data = analytics.generate_performance_dashboard_data(
            {
                "start_date": datetime.utcnow() - timedelta(days=7),
                "end_date": datetime.utcnow(),
            }
        )

        # Then - Verify analytics integration
        assert completion_result["onboarding_completed"] is True
        assert completion_prediction["completion_probability"] > 0.0
        assert funnel_analysis["total_sessions"] > 0
        assert dashboard_data["summary_metrics"]["total_sessions"] > 0

    def test_onboarding_error_recovery_and_resilience(
        self, onboarding_system, sample_user_profile
    ):
        """Test error recovery and system resilience during onboarding."""
        # Given
        user_id = sample_user_profile["user_id"]
        onboarding_service = onboarding_system["onboarding_service"]
        preference_service = onboarding_system["preference_service"]

        # When - Test database failure recovery
        onboarding_service.db.commit.side_effect = Exception("Database error")
        onboarding_service.db.rollback = Mock()

        with pytest.raises(Exception):
            onboarding_service.create_onboarding_session(user_id)

        # Verify rollback was called
        onboarding_service.db.rollback.assert_called_once()

        # When - Reset and test successful recovery
        onboarding_service.db.commit.side_effect = None
        onboarding_service.db.commit = Mock()

        session_result = onboarding_service.create_onboarding_session(user_id)
        assert session_result["user_id"] == user_id

        # When - Test invalid preference data handling
        with pytest.raises(ValueError, match="Invalid categories"):
            preference_service.setup_initial_categories(user_id, ["invalid_category"])

        # When - Test valid recovery after error
        valid_result = preference_service.setup_initial_categories(
            user_id, ["restaurant", "cafe"]
        )
        assert valid_result["success"] is True

        # When - Test partial completion recovery
        # Simulate user abandoning mid-flow and returning
        step_request = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={"categories": ["restaurant"]},
            completed=True,
        )

        # Mock existing session
        mock_session = Mock()
        mock_session.user_id = user_id
        mock_session.current_step = OnboardingStep.WELCOME.value
        mock_session.progress_percentage = 0.0
        mock_session.status = "active"

        onboarding_service.db.query().filter().first.return_value = mock_session

        step_result = onboarding_service.update_onboarding_step(step_request)
        assert step_result["step_updated"] is True

    @pytest.mark.asyncio
    async def test_concurrent_onboarding_sessions(
        self, onboarding_system, sample_user_profile
    ):
        """Test handling of concurrent onboarding sessions."""
        # Given
        onboarding_service = onboarding_system["onboarding_service"]
        user_ids = [str(uuid4()) for _ in range(5)]

        # Mock database to handle concurrent operations
        self._setup_database_mocks(onboarding_system, user_ids[0])

        async def create_onboarding_session_async(user_id):
            """Async wrapper for session creation."""
            return onboarding_service.create_onboarding_session(user_id)

        # When - Create multiple sessions concurrently
        session_tasks = [
            create_onboarding_session_async(user_id) for user_id in user_ids
        ]

        session_results = await asyncio.gather(*session_tasks, return_exceptions=True)

        # Then - Verify all sessions were created successfully
        successful_results = [
            r for r in session_results if not isinstance(r, Exception)
        ]
        assert len(successful_results) == len(user_ids)

        for i, result in enumerate(successful_results):
            assert result["user_id"] == user_ids[i]
            assert result["status"] == "active"

    def test_cross_platform_onboarding_consistency(
        self, onboarding_system, sample_user_profile
    ):
        """Test onboarding consistency across different platforms."""
        # Given
        user_id = sample_user_profile["user_id"]
        personalization_engine = onboarding_system["personalization_engine"]

        platforms = [
            {"platform": "ios", "version": "15.0"},
            {"platform": "android", "version": "12.0"},
            {"platform": "web", "version": "chrome-95"},
        ]

        # When - Test personalization for each platform
        platform_flows = {}
        for platform_info in platforms:
            user_context = {
                "user_segment": "tech_savvy",
                "device_info": platform_info,
            }

            flow = personalization_engine.get_personalized_onboarding_flow(
                f"{user_id}_{platform_info['platform']}", user_context
            )
            platform_flows[platform_info["platform"]] = flow

        # Then - Verify consistent core experience across platforms
        for platform, flow in platform_flows.items():
            assert flow["user_segment"] == "tech_savvy"
            assert (
                flow["flow_configuration"]["step_count"] <= 4
            )  # Tech-savvy users get streamlined flow
            assert "personalized_content" in flow

        # Verify platform-specific adaptations exist but core flow is consistent
        step_counts = [
            flow["flow_configuration"]["step_count"] for flow in platform_flows.values()
        ]
        assert max(step_counts) - min(step_counts) <= 1  # Minimal variation

    def _setup_database_mocks(self, onboarding_system, user_id):
        """Setup database mocks for testing."""
        # Mock onboarding session
        mock_session = Mock()
        if isinstance(user_id, list):
            # For multiple users
            for uid in user_id:
                mock_session.user_id = uid
        else:
            mock_session.user_id = user_id

        mock_session.session_id = f"session_{uuid4()}"
        mock_session.current_step = OnboardingStep.WELCOME.value
        mock_session.progress_percentage = 0.0
        mock_session.status = "active"
        mock_session.created_at = datetime.utcnow()
        mock_session.updated_at = datetime.utcnow()

        # Setup mock returns
        for service_name, service in onboarding_system.items():
            if hasattr(service, "db"):
                service.db.query().filter().first.return_value = mock_session

    def _create_analytics_mock_data(self, user_id):
        """Create mock analytics data."""
        return [
            Mock(
                user_id=user_id,
                session_id=f"session_{uuid4()}",
                steps_completed=["welcome", "categories", "preferences", "completion"],
                total_steps=5,
                completion_status="completed",
                created_at=datetime.utcnow() - timedelta(hours=1),
                updated_at=datetime.utcnow(),
                session_duration_minutes=3.5,
            ),
            Mock(
                user_id=f"other_user_{uuid4()}",
                steps_completed=["welcome", "categories"],
                total_steps=5,
                completion_status="abandoned",
                created_at=datetime.utcnow() - timedelta(hours=2),
                session_duration_minutes=8.0,
                last_active_step="categories",
            ),
        ]


@pytest.mark.e2e
class TestOnboardingE2E:
    """End-to-end tests for complete onboarding user journeys."""

    @pytest.fixture
    def mock_external_services(self):
        """Mock external services for E2E testing."""
        return {
            "gemini_ai": Mock(),
            "firebase_auth": Mock(),
            "analytics_service": Mock(),
            "notification_service": Mock(),
        }

    @pytest.fixture
    def e2e_onboarding_system(self, mock_external_services):
        """Create E2E onboarding system with mocked external dependencies."""
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None
        mock_db.query().filter().all.return_value = []
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        return {
            "onboarding_service": OnboardingService(db=mock_db),
            "flow_manager": OnboardingFlowManager(),
            "preference_service": PreferenceSetupService(db_session=mock_db),
            "survey_service": PreferenceSurveyService(),
            "personalization_engine": OnboardingPersonalizationEngine(db=mock_db),
            "user_preference_service": UserPreferenceService(db=mock_db),
            "ab_orchestrator": ABTestOrchestrator(db=mock_db),
            "analytics": OnboardingAnalytics(db=mock_db),
            "external_services": mock_external_services,
        }

    def test_new_user_complete_journey_success_path(self, e2e_onboarding_system):
        """Test complete new user journey - success path."""
        # Given - New user starts onboarding
        user_profile = {
            "user_id": str(uuid4()),
            "email": "test@example.com",
            "signup_source": "organic",
            "device_info": {"platform": "ios", "version": "15.0"},
            "location": {"country": "KR", "city": "Seoul"},
        }

        user_id = user_profile["user_id"]
        system = e2e_onboarding_system

        # Setup mocks
        self._setup_e2e_mocks(system, user_id)

        # When - User Journey Step 1: Initial app launch and session creation
        session_result = system["onboarding_service"].create_onboarding_session(user_id)

        # When - User Journey Step 2: Personalization engine determines user type
        user_context = {
            "user_segment": "casual_user",  # System determines this
            "device_info": user_profile["device_info"],
            "signup_source": user_profile["signup_source"],
        }

        personalized_flow = system[
            "personalization_engine"
        ].get_personalized_onboarding_flow(user_id, user_context)

        # When - User Journey Step 3: A/B testing assigns user to experiment
        base_config = {"step_count": 5, "flow_type": "standard"}
        experiment_result = system["ab_orchestrator"].run_onboarding_experiment(
            user_id, base_config, user_context
        )

        # When - User Journey Step 4: User completes category selection
        category_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={
                "categories": ["restaurant", "cafe", "culture"],
                "time_spent_seconds": 45,
            },
            completed=True,
        )

        category_result = system["onboarding_service"].update_onboarding_step(
            category_step
        )

        # Track analytics for this step
        system["analytics"].track_user_journey_milestone(
            user_id,
            {
                "milestone": "categories_selected",
                "step": "category_selection",
                "timestamp": datetime.utcnow(),
                "user_context": user_context,
                "metadata": {"categories": ["restaurant", "cafe", "culture"]},
            },
        )

        # When - User Journey Step 5: Preferences setup with validation
        preferences_data = {
            "budget_level": "medium",
            "location": {"lat": 37.5665, "lng": 126.9780, "address": "강남구"},
            "companion_type": "couple",
            "activity_intensity": "moderate",
        }

        # Setup each preference component
        budget_result = system["preference_service"].setup_budget_preferences(
            user_id, preferences_data["budget_level"]
        )

        companion_result = system["preference_service"].setup_companion_preferences(
            user_id, preferences_data["companion_type"]
        )

        activity_result = system["preference_service"].setup_activity_preferences(
            user_id, preferences_data["activity_intensity"]
        )

        # Update onboarding step
        preferences_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.PREFERENCES_SETUP,
            step_data=preferences_data,
            completed=True,
        )

        preferences_result = system["onboarding_service"].update_onboarding_step(
            preferences_step
        )

        # When - User Journey Step 6: Adaptive survey based on preferences
        initial_preferences = {
            "categories": ["restaurant", "cafe", "culture"],
            "budget_level": "medium",
        }

        survey = system["survey_service"].generate_adaptive_survey(
            user_id,
            initial_preferences,
            target_completion_time=120,  # 2 minutes for casual user
        )

        # Simulate survey completion
        survey_responses = [
            ("dining_frequency", "주 2-3회", 8000),
            ("cuisine_preferences", ["한식", "일식", "양식"], 15000),
            ("social_vs_quiet", 4, 6000),  # Prefers lively atmosphere
        ]

        for question_id, response, response_time in survey_responses:
            system["survey_service"].process_survey_response(
                survey["survey_id"], question_id, response, response_time
            )

        # When - User Journey Step 7: Sample interaction and guidance
        sample_interaction_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.SAMPLE_INTERACTION,
            step_data={
                "samples_viewed": 5,
                "samples_saved": 2,
                "time_spent_seconds": 90,
                "interactions": [
                    {"type": "view", "sample_id": "sample1"},
                    {"type": "save", "sample_id": "sample2"},
                ],
            },
            completed=True,
        )

        sample_result = system["onboarding_service"].update_onboarding_step(
            sample_interaction_step
        )

        # When - User Journey Step 8: Completion and final setup
        completion_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.COMPLETION,
            step_data={
                "satisfaction_rating": 4.5,
                "feedback": "Great experience!",
            },
            completed=True,
        )

        completion_step_result = system["onboarding_service"].update_onboarding_step(
            completion_step
        )
        final_completion = system["onboarding_service"].complete_onboarding(user_id)

        # When - User Journey Step 9: Post-completion analytics and A/B tracking
        completion_data = {
            "completed": True,
            "completion_time_seconds": 300,  # 5 minutes total
            "satisfaction_score": 4.5,
            "steps_completed": 4,
            "total_steps": 4,  # Adjusted for casual user flow
        }

        system["ab_orchestrator"].track_onboarding_completion(user_id, completion_data)

        # Generate final analytics
        final_status = system["onboarding_service"].get_onboarding_status(user_id)

        # Then - Verify complete successful journey
        assert session_result["user_id"] == user_id
        assert session_result["status"] == "active"

        assert personalized_flow["user_segment"] == "casual_user"
        assert personalized_flow["flow_configuration"]["provide_explanations"] is True

        assert category_result["step_updated"] is True
        assert budget_result["success"] is True
        assert companion_result["success"] is True
        assert activity_result["success"] is True
        assert preferences_result["step_updated"] is True

        assert survey["adaptive_enabled"] is True
        assert len(survey["questions"]) > 0

        assert sample_result["step_updated"] is True
        assert completion_step_result["step_updated"] is True
        assert final_completion["onboarding_completed"] is True

        assert final_status["status"] == "completed"
        assert final_status["progress_percentage"] == 100.0

    def test_user_abandonment_and_recovery_journey(self, e2e_onboarding_system):
        """Test user abandonment and recovery journey."""
        # Given - User starts onboarding but abandons mid-way
        user_id = str(uuid4())
        system = e2e_onboarding_system

        self._setup_e2e_mocks(system, user_id)

        # When - Initial session creation
        session_result = system["onboarding_service"].create_onboarding_session(user_id)

        # When - User completes first step but abandons
        category_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={"categories": ["restaurant", "cafe"]},
            completed=True,
        )

        system["onboarding_service"].update_onboarding_step(category_step)

        # Simulate abandonment - user leaves app
        abandonment_time = datetime.utcnow()

        # When - Analytics detects abandonment pattern
        session_data = {
            "session_id": session_result["session_id"],
            "start_time": datetime.utcnow() - timedelta(minutes=10),
            "end_time": None,  # No completion
            "steps_completed": ["welcome", "categories"],
            "total_steps": 5,
            "interactions": [
                {
                    "step": "welcome",
                    "action": "next",
                    "timestamp": datetime.utcnow() - timedelta(minutes=10),
                },
                {
                    "step": "categories",
                    "action": "select",
                    "timestamp": datetime.utcnow() - timedelta(minutes=8),
                },
            ],
            "help_requests": 2,  # User seemed confused
            "back_navigations": 3,
            "completion_status": "abandoned",
        }

        behavior_analysis = system["analytics"].analyze_user_behavior_patterns(
            user_id, session_data
        )

        # When - User returns after some time (recovery scenario)
        return_time = abandonment_time + timedelta(hours=2)

        # Get current status
        current_status = system["onboarding_service"].get_onboarding_status(user_id)

        # When - System provides recovery experience
        # Check completion likelihood
        recovery_progress = {
            "steps_completed": ["welcome", "categories"],
            "total_steps": 5,
            "time_spent_minutes": 10.0,
            "interaction_count": 5,
            "help_requests": 2,
        }

        completion_prediction = system["analytics"].predict_completion_likelihood(
            user_id, recovery_progress
        )

        # If prediction suggests intervention needed, provide assistance
        if completion_prediction.get("intervention_recommended", False):
            # Generate adaptive hints for struggling user
            user_progress = {
                "current_step": "preferences_setup",
                "time_on_step": 0,  # Just returning
                "attempts": 1,
                "help_requested": 2,
            }

            adaptive_hints = system[
                "personalization_engine"
            ].get_adaptive_recommendations(user_id, {"struggling_detected": True})

        # When - User continues with assistance
        preferences_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.PREFERENCES_SETUP,
            step_data={
                "budget_level": "low",  # Different choice than before
                "companion_type": "solo",
            },
            completed=True,
        )

        recovery_result = system["onboarding_service"].update_onboarding_step(
            preferences_step
        )

        # Skip sample interaction and go to completion
        completion_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.COMPLETION,
            step_data={
                "satisfaction_rating": 3.5
            },  # Lower satisfaction due to struggle
            completed=True,
        )

        system["onboarding_service"].update_onboarding_step(completion_step)
        final_completion = system["onboarding_service"].complete_onboarding(user_id)

        # Then - Verify recovery journey
        assert behavior_analysis["struggle_indicators"]["struggling_detected"] is True
        assert current_status["current_step"] == OnboardingStep.CATEGORY_SELECTION.value
        assert completion_prediction["completion_probability"] <= 0.5
        assert completion_prediction["intervention_recommended"] is True

        assert recovery_result["step_updated"] is True
        assert final_completion["onboarding_completed"] is True

        # Verify final state shows recovery
        final_status = system["onboarding_service"].get_onboarding_status(user_id)
        assert final_status["status"] == "completed"

    def test_high_engagement_power_user_journey(self, e2e_onboarding_system):
        """Test high-engagement power user journey."""
        # Given - Power user with high engagement signals
        user_profile = {
            "user_id": str(uuid4()),
            "user_segment": "tech_savvy",
            "device_info": {"platform": "android", "version": "12.0"},
            "signup_source": "referral",
            "behavioral_signals": {
                "quick_decisions": True,
                "skips_tutorials": True,
                "uses_shortcuts": True,
            },
        }

        user_id = user_profile["user_id"]
        system = e2e_onboarding_system

        self._setup_e2e_mocks(system, user_id)

        # When - Power user gets streamlined experience
        session_result = system["onboarding_service"].create_onboarding_session(user_id)

        user_context = {
            "user_segment": "tech_savvy",
            "device_info": user_profile["device_info"],
            "user_behavior_signals": user_profile["behavioral_signals"],
        }

        personalized_flow = system[
            "personalization_engine"
        ].get_personalized_onboarding_flow(user_id, user_context)

        # When - A/B test assigns to streamlined variant
        base_config = {"step_count": 5, "flow_type": "standard"}
        experiment_result = system["ab_orchestrator"].run_onboarding_experiment(
            user_id, base_config, user_context
        )

        # When - Power user speeds through streamlined flow
        # Combined category and preferences step
        combined_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={
                "categories": ["restaurant", "cafe", "culture", "entertainment"],
                "budget_level": "high",
                "companion_type": "friends",
                "time_spent_seconds": 25,  # Very fast
            },
            completed=True,
        )

        system["onboarding_service"].update_onboarding_step(combined_step)

        # Skip sample interaction - power user doesn't need it
        completion_step = OnboardingStepRequest(
            user_id=user_id,
            step=OnboardingStep.COMPLETION,
            step_data={
                "satisfaction_rating": 4.8,
                "feedback": "Fast and efficient!",
                "skip_reason": "experienced_user",
            },
            completed=True,
        )

        system["onboarding_service"].update_onboarding_step(completion_step)
        final_completion = system["onboarding_service"].complete_onboarding(user_id)

        # When - Analytics tracks high engagement
        session_data = {
            "session_id": session_result["session_id"],
            "start_time": datetime.utcnow() - timedelta(minutes=2),
            "end_time": datetime.utcnow(),
            "steps_completed": ["welcome", "categories", "completion"],
            "total_steps": 3,  # Streamlined flow
            "interactions": [
                {
                    "step": "categories",
                    "action": "multi_select",
                    "timestamp": datetime.utcnow() - timedelta(minutes=1.5),
                },
                {
                    "step": "completion",
                    "action": "complete",
                    "timestamp": datetime.utcnow(),
                },
            ],
            "help_requests": 0,
            "back_navigations": 0,
            "completion_status": "completed",
        }

        behavior_analysis = system["analytics"].analyze_user_behavior_patterns(
            user_id, session_data
        )

        # Track completion
        completion_data = {
            "completed": True,
            "completion_time_seconds": 120,  # 2 minutes - very fast
            "satisfaction_score": 4.8,
            "steps_completed": 3,
            "efficiency_score": 0.95,
        }

        system["ab_orchestrator"].track_onboarding_completion(user_id, completion_data)

        # Then - Verify power user experience
        assert personalized_flow["flow_configuration"]["step_count"] <= 4
        assert personalized_flow["flow_configuration"]["skip_optional_steps"] is True

        assert experiment_result["final_onboarding_config"]["flow_type"] in [
            "streamlined",
            "standard",
        ]

        assert final_completion["onboarding_completed"] is True

        assert behavior_analysis["engagement_patterns"]["engagement_level"] == "high"
        assert behavior_analysis["engagement_patterns"]["engagement_score"] >= 0.8

        # Verify final state
        final_status = system["onboarding_service"].get_onboarding_status(user_id)
        assert final_status["status"] == "completed"
        assert final_status["progress_percentage"] == 100.0

    def _setup_e2e_mocks(self, system, user_id):
        """Setup mocks for E2E testing."""
        # Mock onboarding session
        mock_session = Mock()
        mock_session.user_id = user_id
        mock_session.session_id = f"session_{uuid4()}"
        mock_session.current_step = OnboardingStep.WELCOME.value
        mock_session.progress_percentage = 0.0
        mock_session.status = "active"
        mock_session.created_at = datetime.utcnow()
        mock_session.updated_at = datetime.utcnow()
        mock_session.step_data = {}

        # Setup all services with mock database
        for service_name, service in system.items():
            if hasattr(service, "db") and service_name != "external_services":
                service.db.query().filter().first.return_value = mock_session

        # Mock A/B test assignments
        if "ab_orchestrator" in system:
            system[
                "ab_orchestrator"
            ].experiment_manager.get_user_assignments.return_value = [
                {
                    "user_id": user_id,
                    "experiment_id": "onboarding_flow_v1",
                    "variant_id": "treatment",
                    "variant_config": {"flow_type": "streamlined", "step_count": 3},
                }
            ]
            system["ab_orchestrator"].experiment_manager.track_event = Mock()

        # Mock analytics data
        if "analytics" in system:
            system["analytics"].db.query().filter().all.return_value = [mock_session]
