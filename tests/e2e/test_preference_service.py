"""Test cases for preference service functionality."""

from datetime import datetime
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.schemas.preference import (
    PreferenceAnalysisResponse,
    UserBehaviorCreate,
    UserProfileResponse,
)
from app.services.auth.preference_service import (
    CategoryPreferenceService,
    PreferencePersonalizationService,
    PreferenceSetupService,
    PreferenceSurveyService,
)
from app.services.auth.user_preference_service import UserPreferenceService


class TestPreferenceSetupService:
    """Test cases for PreferenceSetupService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def preference_setup_service(self, mock_db):
        """Create PreferenceSetupService instance."""
        return PreferenceSetupService(db_session=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_setup_initial_categories_success(
        self, preference_setup_service, sample_user_id
    ):
        """Test successful initial category setup."""
        # Given
        selected_categories = ["restaurant", "cafe", "culture"]

        # When
        result = preference_setup_service.setup_initial_categories(
            sample_user_id, selected_categories
        )

        # Then
        assert result["success"] is True
        assert result["categories"] == selected_categories
        assert len(result["weights"]) == 3
        assert all(
            weight == 1.0 / 3 for weight in result["weights"].values()
        )  # Equal weights
        assert result["next_step"] == "location_preferences"

    def test_setup_initial_categories_too_few(
        self, preference_setup_service, sample_user_id
    ):
        """Test category setup with too few categories."""
        # Given
        selected_categories = ["restaurant"]  # Only 1 category

        # When & Then
        with pytest.raises(ValueError, match="Must select between 2-5 categories"):
            preference_setup_service.setup_initial_categories(
                sample_user_id, selected_categories
            )

    def test_setup_initial_categories_too_many(
        self, preference_setup_service, sample_user_id
    ):
        """Test category setup with too many categories."""
        # Given
        selected_categories = [
            "restaurant",
            "cafe",
            "culture",
            "shopping",
            "entertainment",
            "outdoor",
        ]  # 6 categories

        # When & Then
        with pytest.raises(ValueError, match="Must select between 2-5 categories"):
            preference_setup_service.setup_initial_categories(
                sample_user_id, selected_categories
            )

    def test_setup_initial_categories_invalid(
        self, preference_setup_service, sample_user_id
    ):
        """Test category setup with invalid categories."""
        # Given
        selected_categories = ["restaurant", "invalid_category"]

        # When & Then
        with pytest.raises(ValueError, match="Invalid categories"):
            preference_setup_service.setup_initial_categories(
                sample_user_id, selected_categories
            )

    def test_setup_location_preferences_success(
        self, preference_setup_service, sample_user_id
    ):
        """Test successful location preferences setup."""
        # Given
        current_location = {"lat": 37.5665, "lng": 126.9780}
        preferred_areas = ["강남구", "서초구"]

        # When
        result = preference_setup_service.setup_location_preferences(
            sample_user_id, current_location, preferred_areas
        )

        # Then
        assert result["success"] is True
        assert result["location_preferences"]["current_location"] == current_location
        assert result["location_preferences"]["preferred_areas"] == preferred_areas
        assert result["location_preferences"]["max_travel_distance_km"] == 10
        assert result["next_step"] == "budget_setup"

    def test_setup_budget_preferences_success(
        self, preference_setup_service, sample_user_id
    ):
        """Test successful budget preferences setup."""
        # Given
        budget_level = "medium"

        # When
        result = preference_setup_service.setup_budget_preferences(
            sample_user_id, budget_level
        )

        # Then
        assert result["success"] is True
        assert result["budget_preferences"]["budget_level"] == budget_level
        assert "budget_ranges" in result["budget_preferences"]
        assert result["budget_preferences"]["budget_flexibility"] == "medium"
        assert result["next_step"] == "companion_preferences"

    def test_setup_budget_preferences_invalid_level(
        self, preference_setup_service, sample_user_id
    ):
        """Test budget preferences setup with invalid level."""
        # Given
        budget_level = "invalid_level"

        # When & Then
        with pytest.raises(ValueError, match="Invalid budget level"):
            preference_setup_service.setup_budget_preferences(
                sample_user_id, budget_level
            )

    def test_setup_companion_preferences_success(
        self, preference_setup_service, sample_user_id
    ):
        """Test successful companion preferences setup."""
        # Given
        companion_type = "couple"

        # When
        result = preference_setup_service.setup_companion_preferences(
            sample_user_id, companion_type
        )

        # Then
        assert result["success"] is True
        assert result["companion_preferences"]["companion_type"] == companion_type
        assert result["companion_preferences"]["group_size_preference"] == 2
        assert result["next_step"] == "activity_preferences"

    def test_setup_companion_preferences_invalid_type(
        self, preference_setup_service, sample_user_id
    ):
        """Test companion preferences setup with invalid type."""
        # Given
        companion_type = "invalid_type"

        # When & Then
        with pytest.raises(ValueError, match="Invalid companion type"):
            preference_setup_service.setup_companion_preferences(
                sample_user_id, companion_type
            )

    def test_setup_activity_preferences_success(
        self, preference_setup_service, sample_user_id
    ):
        """Test successful activity preferences setup."""
        # Given
        activity_intensity = "moderate"

        # When
        result = preference_setup_service.setup_activity_preferences(
            sample_user_id, activity_intensity
        )

        # Then
        assert result["success"] is True
        assert (
            result["activity_preferences"]["activity_intensity"] == activity_intensity
        )
        assert result["preferences_complete"] is True

    def test_calculate_preference_quality_score_high_quality(
        self, preference_setup_service, sample_user_id
    ):
        """Test quality score calculation for high-quality preferences."""
        # Given
        preference_data = {
            "categories": ["restaurant", "cafe", "culture", "shopping"],
            "location_preferences": {
                "current_location": {"lat": 37.5665, "lng": 126.9780},
                "preferred_areas": ["강남구"],
            },
            "budget_preferences": {
                "budget_level": "medium",
                "budget_ranges": {"meal": {"min": 15000, "max": 40000}},
            },
            "companion_preferences": {
                "companion_type": "couple",
                "social_comfort_level": "medium",
            },
        }

        # When
        score = preference_setup_service.calculate_preference_quality_score(
            sample_user_id, preference_data
        )

        # Then
        assert 0.8 <= score <= 1.0  # High quality score

    def test_calculate_preference_quality_score_low_quality(
        self, preference_setup_service, sample_user_id
    ):
        """Test quality score calculation for low-quality preferences."""
        # Given
        preference_data = {
            "categories": ["restaurant"],  # Only one category
            # Missing other required sections
        }

        # When
        score = preference_setup_service.calculate_preference_quality_score(
            sample_user_id, preference_data
        )

        # Then
        assert 0.0 <= score <= 0.3  # Low quality score


class TestPreferenceSurveyService:
    """Test cases for PreferenceSurveyService."""

    @pytest.fixture
    def survey_service(self):
        """Create PreferenceSurveyService instance."""
        return PreferenceSurveyService()

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_generate_adaptive_survey_basic(self, survey_service, sample_user_id):
        """Test basic adaptive survey generation."""
        # Given
        initial_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget_level": "medium",
        }

        # When
        result = survey_service.generate_adaptive_survey(
            sample_user_id, initial_preferences
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert "survey_id" in result
        assert "questions" in result
        assert len(result["questions"]) > 0
        assert result["adaptive_enabled"] is True
        assert result["estimated_time_seconds"] <= 180  # 3 minutes max

    def test_generate_adaptive_survey_with_many_categories(
        self, survey_service, sample_user_id
    ):
        """Test adaptive survey with many initial categories."""
        # Given
        initial_preferences = {
            "categories": [
                "restaurant",
                "cafe",
                "culture",
                "shopping",
                "entertainment",
            ],
            "budget_level": "high",
            "companion_type": "family",
        }

        # When
        result = survey_service.generate_adaptive_survey(
            sample_user_id, initial_preferences
        )

        # Then
        assert len(result["questions"]) > 5  # More questions for more categories
        assert result["estimated_time_seconds"] <= 180

    def test_process_survey_response_quick_response(
        self, survey_service, sample_user_id
    ):
        """Test processing quick survey response."""
        # Given
        survey_id = "survey_123"
        question_id = "dining_frequency"
        response = "주 2-3회"
        response_time_ms = 2500  # Quick response

        # When
        result = survey_service.process_survey_response(
            survey_id, question_id, response, response_time_ms
        )

        # Then
        assert result["response_recorded"] is True
        assert result["adaptation_signals"]["confidence_level"] == "high"
        assert result["adaptation_signals"]["time_pressure"] is True

    def test_process_survey_response_slow_response(
        self, survey_service, sample_user_id
    ):
        """Test processing slow survey response."""
        # Given
        survey_id = "survey_123"
        question_id = "cuisine_preferences"
        response = ["한식", "일식", "중식"]
        response_time_ms = 25000  # Slow response

        # When
        result = survey_service.process_survey_response(
            survey_id, question_id, response, response_time_ms
        )

        # Then
        assert result["response_recorded"] is True
        assert result["adaptation_signals"]["confidence_level"] == "low"
        assert result["adaptation_signals"]["detail_oriented"] is True

    def test_estimate_question_count_few_categories(self, survey_service):
        """Test question count estimation with few categories."""
        # Given
        initial_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget_level": "medium",
        }

        # When
        count = survey_service._estimate_question_count(initial_preferences)

        # Then
        assert 8 <= count <= 12  # Base + some category questions

    def test_estimate_question_count_many_categories(self, survey_service):
        """Test question count estimation with many categories."""
        # Given
        initial_preferences = {
            "categories": [
                "restaurant",
                "cafe",
                "culture",
                "shopping",
                "entertainment",
            ],
            "budget_level": "high",
            "companion_type": "friends",
        }

        # When
        count = survey_service._estimate_question_count(initial_preferences)

        # Then
        assert count <= 15  # Capped at maximum

    def test_analyze_response_signals(self, survey_service):
        """Test response analysis for adaptation signals."""
        # Given
        question_id = "social_vs_quiet"
        response = 4  # Scale response
        response_time_ms = 8000  # Moderate response time

        # When
        signals = survey_service._analyze_response(
            question_id, response, response_time_ms
        )

        # Then
        assert "confidence_level" in signals
        assert "category_interests" in signals
        assert "time_pressure" in signals
        assert "detail_oriented" in signals


class TestCategoryPreferenceService:
    """Test cases for CategoryPreferenceService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def category_service(self, mock_db):
        """Create CategoryPreferenceService instance."""
        return CategoryPreferenceService(db_session=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_get_available_categories_success(self, category_service):
        """Test retrieval of available categories."""
        # Given
        user_context = {"user_segment": "tech_savvy"}

        # When
        result = category_service.get_available_categories(user_context)

        # Then
        assert "available_categories" in result
        assert len(result["available_categories"]) == 7
        assert all(
            "id" in cat and "name" in cat and "description" in cat
            for cat in result["available_categories"]
        )
        assert result["total_available"] == 7

    def test_validate_category_selection_valid(self, category_service, sample_user_id):
        """Test valid category selection validation."""
        # Given
        selected_categories = ["restaurant", "cafe", "culture"]

        # When
        result = category_service.validate_category_selection(
            sample_user_id, selected_categories
        )

        # Then
        assert result["validation_passed"] is True
        assert result["category_count"] == 3
        assert result["validation_errors"] == []

    def test_validate_category_selection_too_few(
        self, category_service, sample_user_id
    ):
        """Test category selection validation with too few categories."""
        # Given
        selected_categories = ["restaurant"]

        # When
        result = category_service.validate_category_selection(
            sample_user_id, selected_categories
        )

        # Then
        assert result["validation_passed"] is False
        assert "최소 2개 카테고리" in result["validation_errors"][0]

    def test_validate_category_selection_too_many(
        self, category_service, sample_user_id
    ):
        """Test category selection validation with too many categories."""
        # Given
        selected_categories = [
            "restaurant",
            "cafe",
            "culture",
            "shopping",
            "entertainment",
            "outdoor",
        ]

        # When
        result = category_service.validate_category_selection(
            sample_user_id, selected_categories
        )

        # Then
        assert result["validation_passed"] is False
        assert "최대 5개 카테고리" in result["validation_errors"][0]

    def test_validate_category_selection_invalid_categories(
        self, category_service, sample_user_id
    ):
        """Test category selection validation with invalid categories."""
        # Given
        selected_categories = ["restaurant", "invalid_category"]

        # When
        result = category_service.validate_category_selection(
            sample_user_id, selected_categories
        )

        # Then
        assert result["validation_passed"] is False
        assert "유효하지 않은 카테고리" in result["validation_errors"][0]

    def test_set_category_weights_softmax(self, category_service, sample_user_id):
        """Test category weights setting with softmax normalization."""
        # Given
        category_weights = {
            "restaurant": {"preference": 0.8, "frequency": 0.6},
            "cafe": {"preference": 0.6, "frequency": 0.4},
        }

        # When
        result = category_service.set_category_weights(
            sample_user_id, category_weights, "softmax"
        )

        # Then
        assert result["category_weights_set"] is True
        assert "normalized_weights" in result
        assert result["normalization_method"] == "softmax"
        assert abs(sum(result["normalized_weights"].values()) - 1.0) < 0.01

    def test_set_category_weights_linear(self, category_service, sample_user_id):
        """Test category weights setting with linear normalization."""
        # Given
        category_weights = {
            "restaurant": {"preference": 0.8, "frequency": 0.6},
            "cafe": {"preference": 0.6, "frequency": 0.4},
        }

        # When
        result = category_service.set_category_weights(
            sample_user_id, category_weights, "linear"
        )

        # Then
        assert result["category_weights_set"] is True
        assert result["normalization_method"] == "linear"
        assert "normalized_weights" in result


class TestUserPreferenceService:
    """Test cases for UserPreferenceService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.query().filter().all.return_value = []
        db.query().filter().first.return_value = None
        return db

    @pytest.fixture
    def user_preference_service(self, mock_db):
        """Create UserPreferenceService instance."""
        return UserPreferenceService(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return uuid4()

    def test_record_user_behavior_success(
        self, user_preference_service, sample_user_id
    ):
        """Test successful user behavior recording."""
        # Given
        behavior_data = UserBehaviorCreate(
            action="visit",
            place_id=uuid4(),
            duration_minutes=45,
            rating=4.5,
            tags_added=["romantic", "quiet"],
            time_of_day="evening",
            day_of_week="friday",
        )

        user_preference_service.db.add = Mock()
        user_preference_service.db.commit = Mock()
        user_preference_service.db.refresh = Mock()

        # When
        result = user_preference_service.record_user_behavior(
            sample_user_id, behavior_data
        )

        # Then
        assert result.action == "visit"
        assert result.user_id == sample_user_id
        assert result.rating == 4.5
        user_preference_service.db.add.assert_called_once()
        user_preference_service.db.commit.assert_called_once()

    def test_record_user_behavior_failure(
        self, user_preference_service, sample_user_id
    ):
        """Test user behavior recording failure handling."""
        # Given
        behavior_data = UserBehaviorCreate(
            action="visit",
            place_id=uuid4(),
            duration_minutes=45,
            rating=4.5,
            tags_added=[],
            time_of_day="evening",
            day_of_week="friday",
        )

        user_preference_service.db.add.side_effect = Exception("DB Error")
        user_preference_service.db.rollback = Mock()

        # When & Then
        with pytest.raises(Exception):
            user_preference_service.record_user_behavior(sample_user_id, behavior_data)

        user_preference_service.db.rollback.assert_called_once()

    def test_analyze_user_preferences_no_data(
        self, user_preference_service, sample_user_id
    ):
        """Test preference analysis with no behavior data."""
        # Given
        user_preference_service.db.query().filter().all.return_value = []

        # When
        result = user_preference_service.analyze_user_preferences(sample_user_id)

        # Then
        assert isinstance(result, PreferenceAnalysisResponse)
        assert result.confidence_score == 0.0
        assert result.data_points_count == 0

    def test_analyze_user_preferences_with_data(
        self, user_preference_service, sample_user_id
    ):
        """Test preference analysis with behavior data."""
        # Given
        mock_behaviors = [
            Mock(
                place_id=uuid4(),
                rating=4.5,
                action="visit",
                tags_added=["romantic"],
                time_of_day="evening",
                day_of_week="friday",
                created_at=datetime.utcnow(),
            ),
            Mock(
                place_id=uuid4(),
                rating=4.0,
                action="save",
                tags_added=["cozy"],
                time_of_day="afternoon",
                day_of_week="saturday",
                created_at=datetime.utcnow(),
            ),
        ]

        user_preference_service.db.query().filter().all.return_value = mock_behaviors

        # Mock place data
        mock_places = [
            Mock(id=mock_behaviors[0].place_id, category="restaurant"),
            Mock(id=mock_behaviors[1].place_id, category="cafe"),
        ]
        user_preference_service.db.query().filter().all.return_value = mock_places

        # When
        with (
            patch.object(
                user_preference_service, "_analyze_cuisine_preferences"
            ) as mock_cuisine,
            patch.object(
                user_preference_service, "_analyze_ambiance_preferences"
            ) as mock_ambiance,
            patch.object(
                user_preference_service, "_analyze_price_preferences"
            ) as mock_price,
            patch.object(
                user_preference_service, "_analyze_location_preferences"
            ) as mock_location,
            patch.object(
                user_preference_service, "_analyze_time_preferences"
            ) as mock_time,
        ):
            mock_cuisine.return_value = {"restaurant": 0.8, "cafe": 0.6}
            mock_ambiance.return_value = {"romantic": 0.7}
            mock_price.return_value = {"moderate": 0.6}
            mock_location.return_value = {"travel_radius_km": 5.0}
            mock_time.return_value = {"evening": 0.8}

            result = user_preference_service.analyze_user_preferences(sample_user_id)

        # Then
        assert isinstance(result, PreferenceAnalysisResponse)
        assert result.confidence_score > 0.0
        assert result.data_points_count == 2

    def test_update_preferences_from_feedback_success(
        self, user_preference_service, sample_user_id
    ):
        """Test successful preference update from feedback."""
        # Given
        place_id = uuid4()
        mock_place = Mock(id=place_id, category="restaurant", tags=["romantic"])

        user_preference_service.db.query().filter().first.return_value = mock_place

        with (
            patch.object(
                user_preference_service, "record_user_behavior"
            ) as mock_record,
            patch.object(
                user_preference_service, "_update_preference_weights"
            ) as mock_update,
            patch.object(
                user_preference_service, "_get_current_time_of_day"
            ) as mock_time,
        ):
            mock_record.return_value = Mock()
            mock_update.return_value = None
            mock_time.return_value = "evening"

            # When
            result = user_preference_service.update_preferences_from_feedback(
                sample_user_id, place_id, 4.5, "Great food!", True
            )

        # Then
        assert result is True
        mock_record.assert_called_once()
        mock_update.assert_called_once()

    def test_update_preferences_from_feedback_place_not_found(
        self, user_preference_service, sample_user_id
    ):
        """Test preference update with non-existent place."""
        # Given
        place_id = uuid4()
        user_preference_service.db.query().filter().first.return_value = None

        # When
        result = user_preference_service.update_preferences_from_feedback(
            sample_user_id, place_id, 4.5, "Great food!", True
        )

        # Then
        assert result is False

    def test_calculate_confidence_score_high_confidence(self, user_preference_service):
        """Test confidence score calculation with high-quality data."""
        # Given
        mock_behaviors = [
            Mock(rating=4.5, created_at=datetime.utcnow()) for _ in range(50)
        ]

        # When
        score = user_preference_service._calculate_confidence_score(mock_behaviors)

        # Then
        assert 0.8 <= score <= 1.0  # High confidence

    def test_calculate_confidence_score_low_confidence(self, user_preference_service):
        """Test confidence score calculation with low-quality data."""
        # Given
        mock_behaviors = [
            Mock(rating=3.0, created_at=datetime.utcnow() - timedelta(days=60))
        ]

        # When
        score = user_preference_service._calculate_confidence_score(mock_behaviors)

        # Then
        assert 0.0 <= score <= 0.3  # Low confidence

    def test_get_user_profile_success(self, user_preference_service, sample_user_id):
        """Test successful user profile retrieval."""
        # Given
        mock_preferences = PreferenceAnalysisResponse(
            user_id=str(sample_user_id),
            cuisine_preferences={"restaurant": 0.8},
            ambiance_preferences={"romantic": 0.7},
            price_preferences={"moderate": 0.6},
            location_preferences={"travel_radius_km": 5.0},
            time_preferences={"evening": 0.8},
            confidence_score=0.8,
            analysis_date=datetime.utcnow(),
            data_points_count=10,
        )

        with patch.object(
            user_preference_service, "analyze_user_preferences"
        ) as mock_analyze:
            mock_analyze.return_value = mock_preferences

            # When
            result = user_preference_service.get_user_profile(sample_user_id)

        # Then
        assert isinstance(result, UserProfileResponse)
        assert result.user_id == str(sample_user_id)
        assert result.profile_completeness == 0.8


class TestPreferencePersonalizationService:
    """Test cases for PreferencePersonalizationService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def personalization_service(self, mock_db):
        """Create PreferencePersonalizationService instance."""
        return PreferencePersonalizationService(db_session=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    def test_create_personalized_onboarding_success(
        self, personalization_service, sample_user_id
    ):
        """Test successful personalized onboarding creation."""
        # Given
        demographic_info = {"age_group": "25-34", "location": "Seoul"}
        initial_signals = {"tech_savvy": True, "social_media_active": True}

        # When
        result = personalization_service.create_personalized_onboarding(
            sample_user_id, demographic_info, initial_signals
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["personalized_flow_created"] is True
        assert "customized_questions" in result
        assert len(result["customized_questions"]) > 0
        assert result["personalization_confidence"] >= 0.0

    def test_learn_from_behavior_success(self, personalization_service, sample_user_id):
        """Test successful learning from user behavior."""
        # Given
        interaction_patterns = [
            {"action": "view", "category": "restaurant", "duration": 30},
            {"action": "save", "category": "cafe", "duration": 15},
        ]
        time_spent_per_category = {"restaurant": 1800, "cafe": 900}

        # When
        result = personalization_service.learn_from_behavior(
            sample_user_id, interaction_patterns, time_spent_per_category
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["preferences_updated"] is True
        assert "behavior_insights" in result
        assert "updated_category_weights" in result
        assert result["learning_confidence"] >= 0.0

    def test_assess_preference_quality_high_quality(
        self, personalization_service, sample_user_id
    ):
        """Test preference quality assessment for high-quality preferences."""
        # Given
        completed_categories = 5
        detailed_responses = 10
        consistency_score = 0.9
        completion_percentage = 0.95
        engagement_indicators = {"time_spent": 300, "interactions": 20}

        # When
        result = personalization_service.assess_preference_quality(
            sample_user_id,
            completed_categories,
            detailed_responses,
            consistency_score,
            completion_percentage,
            engagement_indicators,
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["quality_score"] >= 0.8  # High quality
        assert result["recommendation_readiness"]["ready"] is True
        assert result["recommendation_readiness"]["improvements_needed"] == []

    def test_assess_preference_quality_low_quality(
        self, personalization_service, sample_user_id
    ):
        """Test preference quality assessment for low-quality preferences."""
        # Given
        completed_categories = 1
        detailed_responses = 2
        consistency_score = 0.3
        completion_percentage = 0.4
        engagement_indicators = {"time_spent": 60, "interactions": 3}

        # When
        result = personalization_service.assess_preference_quality(
            sample_user_id,
            completed_categories,
            detailed_responses,
            consistency_score,
            completion_percentage,
            engagement_indicators,
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["quality_score"] <= 0.6  # Low quality
        assert result["recommendation_readiness"]["ready"] is False
        assert len(result["recommendation_readiness"]["improvements_needed"]) > 0


@pytest.mark.integration
class TestPreferenceIntegration:
    """Integration tests for preference system."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def preference_system(self, mock_db):
        """Create full preference system with all components."""
        return {
            "setup_service": PreferenceSetupService(db_session=mock_db),
            "survey_service": PreferenceSurveyService(),
            "category_service": CategoryPreferenceService(db_session=mock_db),
            "user_service": UserPreferenceService(db=mock_db),
            "personalization_service": PreferencePersonalizationService(
                db_session=mock_db
            ),
        }

    def test_complete_preference_setup_flow_e2e(self, preference_system):
        """Test complete end-to-end preference setup flow."""
        # Given
        user_id = str(uuid4())
        setup_service = preference_system["setup_service"]
        survey_service = preference_system["survey_service"]

        # Mock database operations
        setup_service.db = Mock()

        # When - Step 1: Setup initial categories
        category_result = setup_service.setup_initial_categories(
            user_id, ["restaurant", "cafe", "culture"]
        )

        # When - Step 2: Setup location preferences
        location_result = setup_service.setup_location_preferences(
            user_id,
            {"lat": 37.5665, "lng": 126.9780},
            ["강남구", "서초구"],
        )

        # When - Step 3: Setup budget preferences
        budget_result = setup_service.setup_budget_preferences(user_id, "medium")

        # When - Step 4: Setup companion preferences
        companion_result = setup_service.setup_companion_preferences(user_id, "couple")

        # When - Step 5: Setup activity preferences
        activity_result = setup_service.setup_activity_preferences(user_id, "moderate")

        # When - Step 6: Generate adaptive survey
        survey_result = survey_service.generate_adaptive_survey(
            user_id,
            {
                "categories": ["restaurant", "cafe", "culture"],
                "budget_level": "medium",
            },
        )

        # Then
        assert category_result["success"] is True
        assert location_result["success"] is True
        assert budget_result["success"] is True
        assert companion_result["success"] is True
        assert activity_result["success"] is True
        assert activity_result["preferences_complete"] is True
        assert survey_result["adaptive_enabled"] is True

    def test_preference_learning_and_adaptation_e2e(self, preference_system):
        """Test preference learning and adaptation flow."""
        # Given
        user_id = uuid4()
        user_service = preference_system["user_service"]
        personalization_service = preference_system["personalization_service"]

        # Mock database operations
        user_service.db.add = Mock()
        user_service.db.commit = Mock()
        user_service.db.refresh = Mock()

        # When - Step 1: Record user behaviors
        behaviors = [
            UserBehaviorCreate(
                action="visit",
                place_id=uuid4(),
                rating=4.5,
                duration_minutes=60,
                tags_added=["romantic", "quiet"],
                time_of_day="evening",
                day_of_week="friday",
            ),
            UserBehaviorCreate(
                action="save",
                place_id=uuid4(),
                rating=4.0,
                duration_minutes=None,
                tags_added=["cozy"],
                time_of_day="afternoon",
                day_of_week="saturday",
            ),
        ]

        for behavior in behaviors:
            recorded = user_service.record_user_behavior(user_id, behavior)
            assert recorded.user_id == user_id

        # When - Step 2: Learn from behavior patterns
        interaction_patterns = [
            {"action": "visit", "category": "restaurant", "duration": 60},
            {"action": "save", "category": "cafe", "duration": 0},
        ]
        time_spent = {"restaurant": 3600, "cafe": 1800}

        learning_result = personalization_service.learn_from_behavior(
            str(user_id), interaction_patterns, time_spent
        )

        # When - Step 3: Assess preference quality
        quality_result = personalization_service.assess_preference_quality(
            str(user_id),
            completed_categories=3,
            detailed_responses=8,
            consistency_score=0.8,
            completion_percentage=0.9,
            engagement_indicators={"time_spent": 240, "interactions": 15},
        )

        # Then
        assert learning_result["preferences_updated"] is True
        assert (
            learning_result["behavior_insights"]["most_engaged_category"]
            == "restaurant"
        )
        assert quality_result["quality_score"] > 0.7
        assert quality_result["recommendation_readiness"]["ready"] is True
