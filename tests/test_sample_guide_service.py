"""Tests for sample places and guide services."""

from unittest.mock import Mock

import pytest

from app.services.sample_guide_service import (
    FirstCourseGuideService,
    GuideService,
    SamplePlacesService,
)


class TestSamplePlacesService:
    """Test sample places service functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.db_mock = Mock()
        self.service = SamplePlacesService(self.db_mock)

    def test_get_curated_sample_places_success(self):
        """
        Given: User requests sample places for onboarding
        When: Curated sample places are requested
        Then: Should return diverse, high-rated sample places
        """
        # Given
        user_preferences = {
            "categories": ["restaurant", "cafe", "culture"],
            "location": {"lat": 37.5665, "lng": 126.9780},
            "budget_level": "medium",
        }

        # When
        result = self.service.get_curated_sample_places(
            user_preferences=user_preferences,
            limit=6,
        )

        # Then
        assert result["success"] is True
        assert len(result["sample_places"]) == 6

        # Check diversity of categories
        categories_found = set()
        for place in result["sample_places"]:
            categories_found.add(place["category"])

        assert len(categories_found) >= 3  # Should have diverse categories

        # Check all places have required fields
        for place in result["sample_places"]:
            assert "id" in place
            assert "name" in place
            assert "category" in place
            assert "rating" in place
            assert place["rating"] >= 4.0  # High-rated places
            assert "description" in place
            assert "image_url" in place
            assert "sample_reason" in place

    def test_get_location_based_samples_success(self):
        """
        Given: User location and preferences
        When: Location-based samples are requested
        Then: Should return nearby sample places with distance info
        """
        # Given
        location = {"latitude": 37.5665, "longitude": 126.9780}
        preferences = {"categories": ["restaurant", "cafe"]}

        # When
        result = self.service.get_location_based_samples(
            location=location,
            preferences=preferences,
            radius_km=5,
            limit=5,
        )

        # Then
        assert result["success"] is True
        assert len(result["sample_places"]) == 5

        for place in result["sample_places"]:
            assert "distance_km" in place
            assert place["distance_km"] <= 5
            assert "travel_time_minutes" in place
            assert "recommended_transport" in place

    def test_get_category_introduction_samples(self):
        """
        Given: User wants to explore specific category
        When: Category introduction samples are requested
        Then: Should return representative places for that category
        """
        # Given
        category = "culture"
        user_location = {"lat": 37.5665, "lng": 126.9780}

        # When
        result = self.service.get_category_introduction_samples(
            category=category,
            user_location=user_location,
        )

        # Then
        assert result["success"] is True
        assert result["category"] == category
        assert len(result["sample_places"]) >= 3

        # All places should be in the requested category
        for place in result["sample_places"]:
            assert place["category"] == category
            assert "introduction_text" in place
            assert "what_to_expect" in place

    def test_get_personalized_samples_with_history(self):
        """
        Given: User has interaction history
        When: Personalized samples are requested
        Then: Should return samples based on user preferences and behavior
        """
        # Given
        user_id = "user123"
        interaction_history = [
            {"place_id": "place1", "action": "liked", "category": "restaurant"},
            {"place_id": "place2", "action": "saved", "category": "cafe"},
        ]

        # When
        result = self.service.get_personalized_samples(
            user_id=user_id,
            interaction_history=interaction_history,
            limit=8,
        )

        # Then
        assert result["success"] is True
        assert len(result["sample_places"]) == 8
        assert result["personalization_applied"] is True

        # Should include places similar to liked categories
        categories_found = [place["category"] for place in result["sample_places"]]
        assert "restaurant" in categories_found
        assert "cafe" in categories_found

    def test_invalid_category_error(self):
        """
        Given: Invalid category is provided
        When: Category samples are requested
        Then: Should raise ValueError
        """
        # Given
        invalid_category = "invalid_category"

        # When & Then
        with pytest.raises(ValueError) as exc_info:
            self.service.get_category_introduction_samples(
                category=invalid_category,
                user_location={"lat": 37.5665, "lng": 126.9780},
            )

        assert "Invalid category" in str(exc_info.value)


class TestGuideService:
    """Test guide service functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.service = GuideService()

    def test_get_onboarding_guide_steps_success(self):
        """
        Given: User starts onboarding
        When: Guide steps are requested
        Then: Should return step-by-step onboarding guide
        """
        # Given
        current_step = 1

        # When
        result = self.service.get_onboarding_guide_steps(current_step=current_step)

        # Then
        assert result["success"] is True
        assert result["current_step"] == current_step
        assert result["total_steps"] == 5
        assert len(result["guide_steps"]) >= 1

        # Check current step details
        current_guide = result["guide_steps"][0]
        assert current_guide["step_number"] == current_step
        assert "title" in current_guide
        assert "description" in current_guide
        assert "action_required" in current_guide
        assert "tips" in current_guide
        assert isinstance(current_guide["tips"], list)

    def test_get_feature_tutorial_success(self):
        """
        Given: User requests feature tutorial
        When: Tutorial is requested for specific feature
        Then: Should return interactive tutorial steps
        """
        # Given
        feature = "place_saving"

        # When
        result = self.service.get_feature_tutorial(feature=feature)

        # Then
        assert result["success"] is True
        assert result["feature"] == feature
        assert "tutorial_steps" in result
        assert len(result["tutorial_steps"]) >= 3

        for step in result["tutorial_steps"]:
            assert "step_number" in step
            assert "title" in step
            assert "description" in step
            assert "interactive_element" in step

    def test_get_contextual_hints_success(self):
        """
        Given: User is in specific app context
        When: Contextual hints are requested
        Then: Should return relevant hints for current context
        """
        # Given
        context = "first_place_save"
        user_progress = {"places_saved": 0, "courses_created": 0}

        # When
        result = self.service.get_contextual_hints(
            context=context,
            user_progress=user_progress,
        )

        # Then
        assert result["success"] is True
        assert result["context"] == context
        assert "hints" in result
        assert len(result["hints"]) >= 1

        for hint in result["hints"]:
            assert "message" in hint
            assert "importance" in hint
            assert "trigger_condition" in hint

    def test_generate_personalized_tips_success(self):
        """
        Given: User preferences and usage patterns
        When: Personalized tips are generated
        Then: Should return tips tailored to user behavior
        """
        # Given
        user_preferences = {
            "categories": ["restaurant", "cafe"],
            "activity_level": "moderate",
            "social_type": "couple",
        }
        usage_patterns = {
            "frequent_categories": ["restaurant"],
            "avg_session_time": 180,
            "preferred_times": ["evening"],
        }

        # When
        result = self.service.generate_personalized_tips(
            user_preferences=user_preferences,
            usage_patterns=usage_patterns,
        )

        # Then
        assert result["success"] is True
        assert "personalized_tips" in result
        assert len(result["personalized_tips"]) >= 3

        for tip in result["personalized_tips"]:
            assert "category" in tip
            assert "message" in tip
            assert "relevance_score" in tip
            assert 0.0 <= tip["relevance_score"] <= 1.0


class TestFirstCourseGuideService:
    """Test first course guide service functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.service = FirstCourseGuideService()

    def test_generate_first_course_template_success(self):
        """
        Given: User preferences for first course
        When: First course template is generated
        Then: Should return structured course template
        """
        # Given
        user_preferences = {
            "categories": ["restaurant", "cafe", "culture"],
            "budget_level": "medium",
            "companion_type": "couple",
            "location": {"lat": 37.5665, "lng": 126.9780},
        }

        # When
        result = self.service.generate_first_course_template(
            user_preferences=user_preferences
        )

        # Then
        assert result["success"] is True
        assert result["template_type"] == "first_course"
        assert "course_structure" in result

        structure = result["course_structure"]
        assert "places" in structure
        assert len(structure["places"]) >= 2  # At least 2 places for a course
        assert "estimated_duration_hours" in structure
        assert "difficulty_level" in structure
        assert structure["difficulty_level"] == "beginner"

    def test_get_course_creation_guide_success(self):
        """
        Given: User wants to create their first course
        When: Course creation guide is requested
        Then: Should return step-by-step course creation guide
        """
        # When
        result = self.service.get_course_creation_guide()

        # Then
        assert result["success"] is True
        assert "creation_steps" in result
        assert len(result["creation_steps"]) >= 4

        # Check step structure
        for step in result["creation_steps"]:
            assert "step_number" in step
            assert "title" in step
            assert "description" in step
            assert "estimated_time_minutes" in step
            assert "required_actions" in step

    def test_provide_course_feedback_and_suggestions(self):
        """
        Given: User creates their first course
        When: Course feedback is requested
        Then: Should provide constructive feedback and improvement suggestions
        """
        # Given
        user_course = {
            "places": [
                {"name": "Restaurant A", "category": "restaurant"},
                {"name": "Cafe B", "category": "cafe"},
            ],
            "estimated_duration": 4,
            "total_budget": 60000,
        }

        # When
        result = self.service.provide_course_feedback_and_suggestions(user_course)

        # Then
        assert result["success"] is True
        assert "feedback" in result
        assert "suggestions" in result
        assert "course_rating" in result

        feedback = result["feedback"]
        assert "strengths" in feedback
        assert "improvements" in feedback

        assert len(result["suggestions"]) >= 2
        for suggestion in result["suggestions"]:
            assert "type" in suggestion  # e.g., "timing", "budget", "variety"
            assert "message" in suggestion
            assert "priority" in suggestion

    def test_get_success_celebration_content(self):
        """
        Given: User successfully completes their first course
        When: Success celebration content is requested
        Then: Should return congratulatory content and next steps
        """
        # Given
        course_completion_data = {
            "completion_time_minutes": 240,
            "user_rating": 4.5,
            "places_visited": 3,
        }

        # When
        result = self.service.get_success_celebration_content(course_completion_data)

        # Then
        assert result["success"] is True
        assert "celebration_message" in result
        assert "achievements_unlocked" in result
        assert "next_steps" in result

        assert len(result["achievements_unlocked"]) >= 1
        assert len(result["next_steps"]) >= 2

        for achievement in result["achievements_unlocked"]:
            assert "title" in achievement
            assert "description" in achievement
            assert "badge_icon" in achievement
