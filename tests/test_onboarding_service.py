"""Test cases for onboarding service functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.schemas.onboarding import OnboardingStep, OnboardingStepRequest
from app.services.onboarding_service import (
    OnboardingFlowManager,
    OnboardingService,
    SampleGuideService,
)


class TestOnboardingService:
    """Test cases for OnboardingService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def onboarding_service(self, mock_db):
        """Create OnboardingService instance with mocked dependencies."""
        return OnboardingService(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_create_onboarding_session_success(
        self, onboarding_service, sample_user_id
    ):
        """Test successful creation of onboarding session."""
        # Given
        expected_session = {
            "user_id": sample_user_id,
            "session_id": "test-session-id",
            "current_step": OnboardingStep.WELCOME,
            "status": "active",
            "progress_percentage": 0.0,
        }

        # Mock session creation
        onboarding_service.db.add = Mock()
        onboarding_service.db.commit = Mock()
        onboarding_service.db.refresh = Mock()

        with patch("uuid.uuid4") as mock_uuid:
            mock_uuid.return_value = "test-session-id"

            # When
            result = onboarding_service.create_onboarding_session(sample_user_id)

            # Then
            assert result["user_id"] == sample_user_id
            assert result["current_step"] == OnboardingStep.WELCOME.value
            assert result["status"] == "active"
            assert result["progress_percentage"] == 0.0
            assert "session_id" in result
            assert "created_at" in result

    def test_get_onboarding_status_existing_session(
        self, onboarding_service, sample_user_id
    ):
        """Test retrieving status for existing onboarding session."""
        # Given
        mock_session = Mock()
        mock_session.user_id = sample_user_id
        mock_session.session_id = "existing-session"
        mock_session.current_step = OnboardingStep.CATEGORY_SELECTION.value
        mock_session.progress_percentage = 40.0
        mock_session.status = "active"
        mock_session.created_at = datetime.utcnow()

        onboarding_service.db.query().filter().first.return_value = mock_session

        # When
        result = onboarding_service.get_onboarding_status(sample_user_id)

        # Then
        assert result["user_id"] == sample_user_id
        assert result["current_step"] == OnboardingStep.CATEGORY_SELECTION.value
        assert result["progress_percentage"] == 40.0
        assert result["status"] == "active"

    def test_get_onboarding_status_no_session(self, onboarding_service, sample_user_id):
        """Test retrieving status when no onboarding session exists."""
        # Given
        onboarding_service.db.query().filter().first.return_value = None

        # When
        result = onboarding_service.get_onboarding_status(sample_user_id)

        # Then
        assert result is None

    def test_update_onboarding_step_success(self, onboarding_service, sample_user_id):
        """Test successful step update in onboarding."""
        # Given
        mock_session = Mock()
        mock_session.user_id = sample_user_id
        mock_session.current_step = OnboardingStep.WELCOME.value
        mock_session.progress_percentage = 0.0
        mock_session.step_data = {}

        onboarding_service.db.query().filter().first.return_value = mock_session
        onboarding_service.db.commit = Mock()

        step_request = OnboardingStepRequest(
            user_id=sample_user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={"categories": ["restaurant", "cafe"]},
            completed=True,
        )

        # When
        result = onboarding_service.update_onboarding_step(step_request)

        # Then
        assert result["step_updated"] is True
        assert result["current_step"] == OnboardingStep.CATEGORY_SELECTION.value
        assert mock_session.current_step == OnboardingStep.CATEGORY_SELECTION.value
        assert mock_session.progress_percentage == 20.0  # 1/5 steps completed

    def test_update_onboarding_step_invalid_session(
        self, onboarding_service, sample_user_id
    ):
        """Test step update with invalid session."""
        # Given
        onboarding_service.db.query().filter().first.return_value = None

        step_request = OnboardingStepRequest(
            user_id=sample_user_id,
            step=OnboardingStep.CATEGORY_SELECTION,
            step_data={},
            completed=True,
        )

        # When
        result = onboarding_service.update_onboarding_step(step_request)

        # Then
        assert result["step_updated"] is False
        assert "error" in result

    def test_complete_onboarding_success(self, onboarding_service, sample_user_id):
        """Test successful completion of onboarding."""
        # Given
        mock_session = Mock()
        mock_session.user_id = sample_user_id
        mock_session.current_step = OnboardingStep.COMPLETION.value
        mock_session.progress_percentage = 100.0
        mock_session.status = "active"

        onboarding_service.db.query().filter().first.return_value = mock_session
        onboarding_service.db.commit = Mock()

        # When
        result = onboarding_service.complete_onboarding(sample_user_id)

        # Then
        assert result["onboarding_completed"] is True
        assert result["user_id"] == sample_user_id
        assert mock_session.status == "completed"
        assert "completed_at" in result

    def test_calculate_progress_percentage(self, onboarding_service):
        """Test progress percentage calculation."""
        # Given
        steps = [
            OnboardingStep.WELCOME,
            OnboardingStep.CATEGORY_SELECTION,
            OnboardingStep.PREFERENCES_SETUP,
        ]

        # When
        result = onboarding_service._calculate_progress_percentage(
            OnboardingStep.CATEGORY_SELECTION, steps
        )

        # Then
        assert result == 33.33  # 1/3 * 100, rounded to 2 decimal places

    def test_validate_step_data_categories(self, onboarding_service):
        """Test step data validation for category selection."""
        # Given
        step_data = {"categories": ["restaurant", "cafe", "entertainment"]}

        # When
        result = onboarding_service._validate_step_data(
            OnboardingStep.CATEGORY_SELECTION, step_data
        )

        # Then
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_step_data_invalid_categories(self, onboarding_service):
        """Test step data validation with invalid categories."""
        # Given
        step_data = {"categories": ["invalid_category"]}

        # When
        result = onboarding_service._validate_step_data(
            OnboardingStep.CATEGORY_SELECTION, step_data
        )

        # Then
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_get_onboarding_analytics_success(self, onboarding_service, sample_user_id):
        """Test retrieval of onboarding analytics."""
        # Given
        mock_sessions = [
            Mock(
                user_id=sample_user_id,
                current_step=OnboardingStep.COMPLETION.value,
                status="completed",
                created_at=datetime.utcnow() - timedelta(days=1),
                updated_at=datetime.utcnow(),
            )
        ]

        onboarding_service.db.query().filter().all.return_value = mock_sessions

        # When
        result = onboarding_service.get_onboarding_analytics(days_back=7)

        # Then
        assert "total_sessions" in result
        assert "completion_rate" in result
        assert "average_completion_time" in result
        assert "step_conversion_rates" in result

    @pytest.mark.asyncio
    async def test_track_onboarding_event(self, onboarding_service, sample_user_id):
        """Test tracking of onboarding events."""
        # Given
        event_data = {
            "event_type": "step_completed",
            "step": OnboardingStep.CATEGORY_SELECTION.value,
            "duration_seconds": 45,
        }

        with (
            patch("app.services.onboarding_service.logger") as mock_logger,
            patch.object(onboarding_service, "_store_event") as mock_store,
        ):
            mock_store.return_value = True

            # When
            result = await onboarding_service.track_onboarding_event(
                sample_user_id, event_data
            )

            # Then
            assert result["event_tracked"] is True
            mock_logger.info.assert_called_once()
            mock_store.assert_called_once()


class TestOnboardingFlowManager:
    """Test cases for OnboardingFlowManager."""

    @pytest.fixture
    def flow_manager(self):
        """Create OnboardingFlowManager instance."""
        return OnboardingFlowManager()

    @pytest.fixture
    def sample_user_context(self):
        """Sample user context for testing."""
        return {
            "user_segment": "tech_savvy",
            "device_info": {"platform": "ios", "version": "15.0"},
            "signup_source": "organic",
        }

    def test_get_personalized_flow_tech_savvy(self, flow_manager, sample_user_context):
        """Test personalized flow generation for tech-savvy users."""
        # When
        result = flow_manager.get_personalized_flow("user123", sample_user_context)

        # Then
        assert result["user_id"] == "user123"
        assert result["flow_type"] == "streamlined"
        assert len(result["steps"]) <= 4  # Shorter flow for tech-savvy users
        assert result["personalization_applied"] is True

    def test_get_personalized_flow_casual_user(self, flow_manager):
        """Test personalized flow generation for casual users."""
        # Given
        user_context = {
            "user_segment": "casual_user",
            "device_info": {"platform": "android"},
            "signup_source": "referral",
        }

        # When
        result = flow_manager.get_personalized_flow("user456", user_context)

        # Then
        assert result["user_id"] == "user456"
        assert result["flow_type"] == "guided"
        assert len(result["steps"]) == 5  # Full guided flow
        assert result["estimated_time_minutes"] > 4  # More time for casual users

    def test_get_step_content_with_personalization(
        self, flow_manager, sample_user_context
    ):
        """Test step content generation with personalization."""
        # When
        result = flow_manager.get_step_content(
            OnboardingStep.CATEGORY_SELECTION, sample_user_context
        )

        # Then
        assert result["step"] == OnboardingStep.CATEGORY_SELECTION.value
        assert "content" in result
        assert "personalized_hints" in result
        assert len(result["personalized_hints"]) > 0

    def test_validate_step_transition_valid(self, flow_manager):
        """Test valid step transition validation."""
        # When
        result = flow_manager.validate_step_transition(
            OnboardingStep.WELCOME, OnboardingStep.CATEGORY_SELECTION
        )

        # Then
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_step_transition_invalid(self, flow_manager):
        """Test invalid step transition validation."""
        # When
        result = flow_manager.validate_step_transition(
            OnboardingStep.WELCOME, OnboardingStep.COMPLETION
        )

        # Then
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_get_flow_config_for_segment(self, flow_manager):
        """Test flow configuration retrieval for different segments."""
        # When
        tech_savvy_config = flow_manager._get_flow_config_for_segment("tech_savvy")
        casual_config = flow_manager._get_flow_config_for_segment("casual_user")

        # Then
        assert tech_savvy_config["flow_type"] == "streamlined"
        assert casual_config["flow_type"] == "guided"
        assert tech_savvy_config["step_count"] < casual_config["step_count"]


class TestSampleGuideService:
    """Test cases for SampleGuideService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def sample_guide_service(self, mock_db):
        """Create SampleGuideService instance."""
        return SampleGuideService(db=mock_db)

    def test_get_sample_places_success(self, sample_guide_service):
        """Test successful retrieval of sample places."""
        # Given
        mock_places = [
            Mock(
                id="place1",
                name="샘플 카페",
                category="cafe",
                description="아늑한 분위기의 카페",
                image_url="https://example.com/cafe.jpg",
            ),
            Mock(
                id="place2",
                name="샘플 레스토랑",
                category="restaurant",
                description="맛있는 한식당",
                image_url="https://example.com/restaurant.jpg",
            ),
        ]

        sample_guide_service.db.query().limit().all.return_value = mock_places

        # When
        result = sample_guide_service.get_sample_places(limit=5)

        # Then
        assert len(result["sample_places"]) == 2
        assert result["total_samples"] == 2
        assert all("id" in place for place in result["sample_places"])

    def test_get_interactive_tutorial_basic(self, sample_guide_service):
        """Test basic interactive tutorial generation."""
        # When
        result = sample_guide_service.get_interactive_tutorial("user123")

        # Then
        assert result["user_id"] == "user123"
        assert "tutorial_steps" in result
        assert len(result["tutorial_steps"]) > 0
        assert result["tutorial_type"] == "basic"

    def test_get_interactive_tutorial_advanced(self, sample_guide_service):
        """Test advanced interactive tutorial for experienced users."""
        # Given
        user_context = {"experience_level": "advanced", "previous_apps": ["similar"]}

        # When
        result = sample_guide_service.get_interactive_tutorial("user123", user_context)

        # Then
        assert result["tutorial_type"] == "advanced"
        assert len(result["tutorial_steps"]) < 5  # Shorter for advanced users

    def test_generate_sample_course_success(self, sample_guide_service):
        """Test successful sample course generation."""
        # Given
        user_preferences = {
            "categories": ["cafe", "restaurant"],
            "budget_level": "medium",
            "location": {"lat": 37.5665, "lng": 126.9780},
        }

        mock_places = [
            {"id": "place1", "name": "카페", "category": "cafe"},
            {"id": "place2", "name": "레스토랑", "category": "restaurant"},
        ]

        with patch.object(
            sample_guide_service, "_get_nearby_places"
        ) as mock_get_places:
            mock_get_places.return_value = mock_places

            # When
            result = sample_guide_service.generate_sample_course(
                "user123", user_preferences
            )

            # Then
            assert result["user_id"] == "user123"
            assert "course_places" in result
            assert len(result["course_places"]) > 0
            assert result["course_generated"] is True

    def test_track_sample_interaction(self, sample_guide_service):
        """Test tracking of sample interaction."""
        # Given
        interaction_data = {
            "interaction_type": "place_viewed",
            "sample_id": "place1",
            "duration_seconds": 15,
        }

        sample_guide_service.db.add = Mock()
        sample_guide_service.db.commit = Mock()

        # When
        result = sample_guide_service.track_sample_interaction(
            "user123", interaction_data
        )

        # Then
        assert result["interaction_tracked"] is True
        assert result["user_id"] == "user123"
        sample_guide_service.db.add.assert_called_once()
        sample_guide_service.db.commit.assert_called_once()

    def test_get_contextual_help_category_selection(self, sample_guide_service):
        """Test contextual help for category selection step."""
        # When
        result = sample_guide_service.get_contextual_help(
            OnboardingStep.CATEGORY_SELECTION
        )

        # Then
        assert result["step"] == OnboardingStep.CATEGORY_SELECTION.value
        assert "help_content" in result
        assert "tips" in result
        assert len(result["tips"]) > 0

    def test_provide_guided_hints_struggling_user(self, sample_guide_service):
        """Test guided hints for users struggling with a step."""
        # Given
        user_progress = {
            "current_step": OnboardingStep.CATEGORY_SELECTION.value,
            "time_on_step": 120,  # 2 minutes - struggling
            "attempts": 3,
        }

        # When
        result = sample_guide_service.provide_guided_hints("user123", user_progress)

        # Then
        assert result["user_id"] == "user123"
        assert result["struggling_detected"] is True
        assert "guided_hints" in result
        assert len(result["guided_hints"]) > 0
        assert result["hint_intensity"] == "high"


@pytest.mark.integration
class TestOnboardingIntegration:
    """Integration tests for onboarding system."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def full_onboarding_system(self, mock_db):
        """Create full onboarding system with all components."""
        return {
            "onboarding_service": OnboardingService(db=mock_db),
            "flow_manager": OnboardingFlowManager(),
            "sample_guide_service": SampleGuideService(db=mock_db),
        }

    def test_complete_onboarding_flow_e2e(self, full_onboarding_system):
        """Test complete end-to-end onboarding flow."""
        # Given
        user_id = str(uuid4())
        user_context = {
            "user_segment": "casual_user",
            "device_info": {"platform": "ios"},
        }

        onboarding_service = full_onboarding_system["onboarding_service"]
        flow_manager = full_onboarding_system["flow_manager"]

        # Mock database operations
        onboarding_service.db.add = Mock()
        onboarding_service.db.commit = Mock()
        onboarding_service.db.refresh = Mock()

        mock_session = Mock()
        mock_session.user_id = user_id
        mock_session.current_step = OnboardingStep.WELCOME.value
        mock_session.progress_percentage = 0.0
        mock_session.status = "active"

        onboarding_service.db.query().filter().first.return_value = mock_session

        # When - Step 1: Create session
        session_result = onboarding_service.create_onboarding_session(user_id)

        # When - Step 2: Get personalized flow
        flow_result = flow_manager.get_personalized_flow(user_id, user_context)

        # When - Step 3: Update through each step
        steps = [
            (OnboardingStep.CATEGORY_SELECTION, {"categories": ["cafe", "restaurant"]}),
            (
                OnboardingStep.PREFERENCES_SETUP,
                {"budget_level": "medium", "location_enabled": True},
            ),
            (OnboardingStep.SAMPLE_INTERACTION, {"sample_viewed": True}),
            (OnboardingStep.COMPLETION, {}),
        ]

        for step, step_data in steps:
            mock_session.current_step = step.value
            mock_session.progress_percentage += 20.0

            step_request = OnboardingStepRequest(
                user_id=user_id, step=step, step_data=step_data, completed=True
            )

            step_result = onboarding_service.update_onboarding_step(step_request)
            assert step_result["step_updated"] is True

        # When - Step 4: Complete onboarding
        mock_session.status = "completed"
        completion_result = onboarding_service.complete_onboarding(user_id)

        # Then
        assert session_result["user_id"] == user_id
        assert flow_result["flow_type"] == "guided"  # Casual user gets guided flow
        assert completion_result["onboarding_completed"] is True

    def test_onboarding_analytics_calculation(self, full_onboarding_system):
        """Test onboarding analytics calculation across sessions."""
        # Given
        onboarding_service = full_onboarding_system["onboarding_service"]

        # Mock multiple sessions with different outcomes
        mock_sessions = [
            Mock(
                user_id="user1",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=2),
                updated_at=datetime.utcnow() - timedelta(hours=1),
            ),
            Mock(
                user_id="user2",
                status="abandoned",
                created_at=datetime.utcnow() - timedelta(hours=3),
                updated_at=datetime.utcnow() - timedelta(hours=2),
            ),
            Mock(
                user_id="user3",
                status="completed",
                created_at=datetime.utcnow() - timedelta(hours=4),
                updated_at=datetime.utcnow() - timedelta(hours=3),
            ),
        ]

        onboarding_service.db.query().filter().all.return_value = mock_sessions

        # When
        analytics = onboarding_service.get_onboarding_analytics(days_back=1)

        # Then
        assert analytics["total_sessions"] == 3
        assert analytics["completion_rate"] == 2 / 3  # 2 completed out of 3
        assert analytics["average_completion_time"] > 0
