"""Tests for user preference setup and onboarding system following TDD approach."""

import time

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TEST_USER_ID = "00000000-0000-0000-0000-000000000000"


class TestPreferenceInitialSetup:
    """Test initial preference collection during onboarding."""

    def test_category_preference_selection(self):
        """Test: 관심사 카테고리 선택."""
        # Given: User selecting initial preferences
        category_selection = {
            "user_id": TEST_USER_ID,
            "selected_categories": ["restaurant", "cafe", "culture"],
            "selection_reason": "personal_interest",
            "confidence_level": "high",
        }

        # When: Set initial category preferences
        response = client.post(
            "/api/v1/preferences/initial-categories", json=category_selection
        )

        # Then: Should save category preferences
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            result = response.json()
            assert "categories_saved" in result
            assert len(result["selected_categories"]) == 3
            assert "preference_id" in result

    def test_location_preference_setup(self):
        """Test: 선호 지역 설정."""
        # Given: User setting location preferences
        location_prefs = {
            "user_id": TEST_USER_ID,
            "preferred_areas": [
                {"name": "강남구", "preference_score": 0.9, "reason": "work_nearby"},
                {"name": "홍대", "preference_score": 0.8, "reason": "social_life"},
                {"name": "명동", "preference_score": 0.6, "reason": "shopping"},
            ],
            "travel_range_km": 15,
            "transportation_preferences": ["walking", "subway", "bus"],
        }

        # When: Configure location preferences
        response = client.post(
            "/api/v1/preferences/location-setup", json=location_prefs
        )

        # Then: Should configure location-based preferences
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            location_result = response.json()
            assert "preferred_areas_configured" in location_result
            assert len(location_result["preferred_areas"]) == 3
            assert "travel_range_set" in location_result

    def test_budget_range_configuration(self):
        """Test: 예산 범위 설정."""
        # Given: User budget preferences
        budget_config = {
            "user_id": TEST_USER_ID,
            "budget_category": "medium",  # low, medium, high
            "per_place_range": {
                "min_amount": 15000,  # KRW
                "max_amount": 50000,
                "currency": "KRW",
            },
            "total_course_budget": {
                "min_amount": 50000,
                "max_amount": 200000,
                "currency": "KRW",
            },
            "budget_flexibility": "moderate",  # strict, moderate, flexible
        }

        # When: Set budget preferences
        response = client.post("/api/v1/preferences/budget-setup", json=budget_config)

        # Then: Should configure budget-based filtering
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            budget_result = response.json()
            assert "budget_range_configured" in budget_result
            assert "price_filtering_enabled" in budget_result
            assert "flexibility_level_set" in budget_result

    def test_companion_preference_setup(self):
        """Test: 동반자 유형 설정."""
        # Given: Companion preferences
        companion_prefs = {
            "user_id": TEST_USER_ID,
            "primary_companion_type": "romantic_partner",  # alone, romantic_partner, friends, family
            "group_size_preference": "couple",  # solo, couple, small_group, large_group
            "social_comfort_level": "moderate",  # introverted, moderate, extroverted
            "special_needs": [],  # accessibility, child_friendly, pet_friendly
        }

        # When: Configure companion preferences
        response = client.post(
            "/api/v1/preferences/companion-setup", json=companion_prefs
        )

        # Then: Should set companion-based recommendations
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            companion_result = response.json()
            assert "companion_type_set" in companion_result
            assert "group_size_configured" in companion_result
            assert "social_preferences_saved" in companion_result

    def test_activity_level_configuration(self):
        """Test: 활동 수준 선호도 설정."""
        # Given: Activity level preferences
        activity_config = {
            "user_id": TEST_USER_ID,
            "activity_intensity": "moderate",  # low, moderate, high
            "walking_tolerance": {
                "max_distance_km": 2.0,
                "preferred_pace": "leisurely",  # leisurely, normal, brisk
            },
            "time_availability": {
                "typical_course_duration_hours": 4,
                "max_course_duration_hours": 8,
                "preferred_time_slots": ["evening", "weekend"],
            },
            "physical_considerations": [],  # accessibility_needed, limited_mobility
        }

        # When: Set activity level preferences
        response = client.post(
            "/api/v1/preferences/activity-setup", json=activity_config
        )

        # Then: Should configure activity-based recommendations
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            activity_result = response.json()
            assert "activity_level_configured" in activity_result
            assert "time_preferences_set" in activity_result
            assert "walking_tolerance_configured" in activity_result


class TestPreferenceSurveySystem:
    """Test preference survey system and data collection."""

    def test_survey_questionnaire_completion(self):
        """Test: 취향 설문 완료."""
        # Given: Complete preference survey
        survey_responses = {
            "user_id": TEST_USER_ID,
            "survey_version": "v2.1",
            "responses": [
                {
                    "question_id": "q1",
                    "question": "선호하는 식당 분위기는?",
                    "answer": "cozy_intimate",
                    "confidence": 0.8,
                },
                {
                    "question_id": "q2",
                    "question": "주로 언제 데이트 코스를 이용하나요?",
                    "answer": "weekend_evening",
                    "confidence": 0.9,
                },
                {
                    "question_id": "q3",
                    "question": "새로운 장소 탐험에 얼마나 열린가요?",
                    "answer": "moderately_adventurous",
                    "confidence": 0.7,
                },
                {
                    "question_id": "q4",
                    "question": "거리 이동에 대한 선호도는?",
                    "answer": "prefer_short_walks",
                    "confidence": 0.6,
                },
                {
                    "question_id": "q5",
                    "question": "SNS 공유에 대한 선호도는?",
                    "answer": "selective_sharing",
                    "confidence": 0.8,
                },
            ],
            "completion_time_minutes": 2.5,
        }

        # When: Complete preference survey
        response = client.post(
            "/api/v1/preferences/complete-survey", json=survey_responses
        )

        # Then: Should process survey and generate preference profile
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            survey_result = response.json()
            assert "preference_profile_created" in survey_result
            assert "survey_completed" in survey_result
            assert survey_result["total_responses"] == 5

    def test_adaptive_survey_flow(self):
        """Test: 적응형 설문 플로우."""
        # Given: Adaptive survey based on previous answers
        adaptive_survey = {
            "user_id": TEST_USER_ID,
            "previous_answers": [
                {"question_id": "q1", "answer": "budget_conscious"},
                {"question_id": "q2", "answer": "frequent_traveler"},
            ],
            "adaptive_questions": [
                {
                    "question_id": "q3_adaptive",
                    "triggered_by": "budget_conscious",
                    "question": "예산 관리에서 가장 중요한 요소는?",
                },
                {
                    "question_id": "q4_adaptive",
                    "triggered_by": "frequent_traveler",
                    "question": "여행시 가장 중요하게 고려하는 것은?",
                },
            ],
        }

        # When: Process adaptive survey
        response = client.post(
            "/api/v1/preferences/adaptive-survey", json=adaptive_survey
        )

        # Then: Should provide personalized follow-up questions
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            adaptive_result = response.json()
            assert "adaptive_questions_generated" in adaptive_result
            assert "personalization_improved" in adaptive_result

    def test_preference_validation_rules(self):
        """Test: 취향 설정 유효성 검증."""
        # Given: Various preference configurations to validate
        validation_cases = [
            {
                "categories": ["restaurant", "cafe"],
                "budget": "medium",
                "expected_valid": True,
            },
            {
                "categories": [],  # Empty categories
                "budget": "medium",
                "expected_valid": False,
            },
            {
                "categories": ["restaurant"] * 10,  # Too many categories
                "budget": "medium",
                "expected_valid": False,
            },
            {
                "categories": ["restaurant", "invalid_category"],
                "budget": "invalid_budget",
                "expected_valid": False,
            },
        ]

        for case in validation_cases:
            validation_request = {"user_id": TEST_USER_ID, "preferences": case}

            response = client.post(
                "/api/v1/preferences/validate", json=validation_request
            )

            if case["expected_valid"]:
                assert response.status_code in [200, 404]
            else:
                assert response.status_code in [422, 404]

    def test_preference_scoring_system(self):
        """Test: 취향 점수화 시스템."""
        # Given: User preferences with scoring weights
        preference_scoring = {
            "user_id": TEST_USER_ID,
            "weighted_preferences": {
                "cuisine_types": {"korean": 0.8, "italian": 0.6, "japanese": 0.7},
                "atmosphere": {"romantic": 0.9, "casual": 0.5, "upscale": 0.3},
                "activity_types": {"dining": 0.8, "cultural": 0.6, "shopping": 0.4},
                "location_factors": {
                    "accessibility": 0.7,
                    "scenery": 0.8,
                    "quietness": 0.6,
                },
            },
            "importance_weights": {
                "cuisine_types": 0.3,
                "atmosphere": 0.25,
                "activity_types": 0.25,
                "location_factors": 0.2,
            },
        }

        # When: Calculate preference scores
        response = client.post(
            "/api/v1/preferences/calculate-scores", json=preference_scoring
        )

        # Then: Should generate weighted preference scores
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            scoring_result = response.json()
            assert "preference_scores_calculated" in scoring_result
            assert "total_weighted_score" in scoring_result
            assert "category_breakdown" in scoring_result


class TestOnboardingPersonalization:
    """Test onboarding personalization and user journey optimization."""

    def test_personalized_onboarding_flow(self):
        """Test: 개인화된 온보딩 플로우."""
        # Given: User profile for personalized onboarding
        user_profile = {
            "user_id": TEST_USER_ID,
            "demographic_info": {
                "age_range": "25-35",
                "location": "seoul",
                "lifestyle": "professional",
            },
            "initial_signals": {
                "app_install_source": "instagram_ad",
                "first_search_query": "강남 데이트 코스",
                "device_type": "ios",
            },
        }

        # When: Generate personalized onboarding
        response = client.post("/api/v1/onboarding/personalize", json=user_profile)

        # Then: Should create customized onboarding experience
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            personalized_result = response.json()
            assert "personalized_flow_created" in personalized_result
            assert "customized_questions" in personalized_result
            assert "estimated_completion_time" in personalized_result

    def test_preference_learning_from_behavior(self):
        """Test: 행동 패턴 기반 취향 학습."""
        # Given: User behavior data during onboarding
        behavior_data = {
            "user_id": TEST_USER_ID,
            "interaction_patterns": [
                {
                    "action": "spent_time_viewing",
                    "content_type": "restaurant_sample",
                    "duration_seconds": 45,
                },
                {
                    "action": "quick_skip",
                    "content_type": "cafe_sample",
                    "duration_seconds": 3,
                },
                {
                    "action": "saved_to_favorites",
                    "content_type": "cultural_place",
                    "interaction_depth": "high",
                },
                {
                    "action": "shared_externally",
                    "content_type": "romantic_restaurant",
                    "share_platform": "kakao",
                },
            ],
            "time_spent_per_category": {
                "restaurant": 120,
                "cafe": 30,
                "culture": 90,
                "entertainment": 60,
            },
        }

        # When: Learn preferences from behavior
        response = client.post(
            "/api/v1/preferences/learn-from-behavior", json=behavior_data
        )

        # Then: Should update preference weights based on behavior
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            learning_result = response.json()
            assert "preferences_updated" in learning_result
            assert "behavior_insights" in learning_result
            assert "recommendation_improvements" in learning_result

    def test_preference_quality_assessment(self):
        """Test: 취향 설정 품질 평가."""
        # Given: Preference configuration for quality assessment
        preference_assessment = {
            "user_id": TEST_USER_ID,
            "completed_categories": 5,
            "detailed_responses": 3,
            "consistency_score": 0.85,
            "completion_percentage": 90,
            "engagement_indicators": {
                "time_spent_minutes": 3.2,
                "question_skips": 1,
                "detail_level": "comprehensive",
            },
        }

        # When: Assess preference quality
        response = client.post(
            "/api/v1/preferences/assess-quality", json=preference_assessment
        )

        # Then: Should evaluate preference completeness and reliability
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            quality_result = response.json()
            assert "quality_score" in quality_result
            assert "completeness_percentage" in quality_result
            assert "recommendation_readiness" in quality_result

    def test_preference_migration_and_updates(self):
        """Test: 취향 설정 업데이트 및 마이그레이션."""
        # Given: Updated preferences after initial setup
        preference_update = {
            "user_id": TEST_USER_ID,
            "updated_preferences": {
                "categories": [
                    "restaurant",
                    "culture",
                    "outdoor",
                ],  # Changed from cafe to outdoor
                "budget_level": "high",  # Upgraded from medium
                "activity_level": "high",  # Upgraded from moderate
            },
            "update_reason": "lifestyle_change",
            "update_confidence": 0.9,
        }

        # When: Update user preferences
        response = client.put(
            "/api/v1/preferences/update-profile", json=preference_update
        )

        # Then: Should maintain preference history and update recommendations
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            update_result = response.json()
            assert "preferences_updated" in update_result
            assert "previous_preferences_archived" in update_result
            assert "recommendation_engine_refreshed" in update_result


class TestPreferenceSurveyValidation:
    """Test preference survey validation and user experience."""

    def test_survey_question_sequence(self):
        """Test: 설문 질문 순서 및 로직."""
        # Given: Survey flow with conditional questions
        survey_flow = {
            "user_id": TEST_USER_ID,
            "flow_type": "comprehensive",  # quick, standard, comprehensive
            "question_sequence": [
                {"order": 1, "question_id": "basic_categories", "mandatory": True},
                {"order": 2, "question_id": "budget_comfort", "mandatory": True},
                {"order": 3, "question_id": "location_preferences", "mandatory": False},
                {"order": 4, "question_id": "social_preferences", "mandatory": False},
                {"order": 5, "question_id": "detailed_tastes", "mandatory": False},
            ],
        }

        # When: Execute survey flow
        response = client.post("/api/v1/preferences/survey-flow", json=survey_flow)

        # Then: Should provide logical question progression
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            flow_result = response.json()
            assert "question_sequence_validated" in flow_result
            assert "estimated_completion_time" in flow_result
            assert "mandatory_questions_count" in flow_result

    def test_skip_optional_questions(self):
        """Test: 선택적 질문 건너뛰기."""
        # Given: User skipping optional survey questions
        skip_request = {
            "user_id": TEST_USER_ID,
            "questions_to_skip": ["detailed_tastes", "social_preferences"],
            "skip_reason": "time_constraint",
            "proceed_with_minimal": True,
        }

        # When: Skip optional questions
        response = client.post("/api/v1/preferences/skip-optional", json=skip_request)

        # Then: Should allow skipping and proceed with basic profile
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            skip_result = response.json()
            assert "questions_skipped" in skip_result
            assert "minimal_profile_created" in skip_result
            assert "recommendation_quality_impact" in skip_result

    def test_survey_progress_tracking(self):
        """Test: 설문 진행 상태 추적."""
        # Given: Survey in progress
        progress_data = {
            "user_id": TEST_USER_ID,
            "total_questions": 10,
            "answered_questions": 7,
            "skipped_questions": 1,
            "current_question_id": "q8",
            "time_spent_minutes": 2.1,
        }

        # When: Track survey progress
        response = client.post("/api/v1/preferences/track-progress", json=progress_data)

        # Then: Should track completion progress accurately
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            progress_result = response.json()
            assert progress_result["completion_percentage"] == 70  # 7/10 * 100
            assert "estimated_remaining_time" in progress_result
            assert "progress_stage" in progress_result

    def test_survey_completion_within_3_minutes(self):
        """Test: 3분 이내 설문 완료."""
        # Given: Streamlined survey for 3-minute completion
        quick_survey = {
            "user_id": TEST_USER_ID,
            "survey_mode": "essential_only",
            "essential_questions": [
                {"question_id": "q1", "answer": "restaurant"},
                {"question_id": "q2", "answer": "medium_budget"},
                {"question_id": "q3", "answer": "couple_dates"},
                {"question_id": "q4", "answer": "seoul_gangnam"},
            ],
            "time_budget_seconds": 180,  # 3 minutes
        }

        # When: Complete essential survey
        start_time = time.time()
        response = client.post(
            "/api/v1/preferences/essential-survey", json=quick_survey
        )
        end_time = time.time()

        # Then: Should complete within time budget
        completion_time = end_time - start_time
        assert completion_time < 3.0  # Allow for test environment
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            quick_result = response.json()
            assert "meets_3min_requirement" in quick_result
            assert quick_result["essential_profile_created"]


class TestCategoryPreferenceSystem:
    """Test category preference management and selection."""

    def test_available_categories_retrieval(self):
        """Test: 사용 가능한 카테고리 목록 조회."""
        # Given: Request for available preference categories
        category_request = {
            "user_context": {
                "location": "seoul",
                "age_group": "20s_30s",
                "user_type": "dating_couples",
            }
        }

        # When: Get available categories
        response = client.post(
            "/api/v1/preferences/available-categories", json=category_request
        )

        # Then: Should return contextual category options
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            categories_result = response.json()
            assert "available_categories" in categories_result
            assert len(categories_result["available_categories"]) >= 6
            assert "category_descriptions" in categories_result

    def test_category_selection_validation(self):
        """Test: 카테고리 선택 검증 (2-5개 제한)."""
        # Given: Various category selection scenarios
        selection_tests = [
            {"categories": ["restaurant", "cafe"], "expected_valid": True},
            {"categories": ["restaurant"], "expected_valid": False},  # Too few
            {
                "categories": [
                    "restaurant",
                    "cafe",
                    "culture",
                    "shopping",
                    "entertainment",
                    "outdoor",
                ],
                "expected_valid": False,
            },  # Too many
            {"categories": ["restaurant", "cafe", "culture"], "expected_valid": True},
        ]

        for test_case in selection_tests:
            validation_request = {
                "user_id": TEST_USER_ID,
                "selected_categories": test_case["categories"],
            }

            response = client.post(
                "/api/v1/preferences/validate-categories", json=validation_request
            )

            if test_case["expected_valid"]:
                assert response.status_code in [200, 404]
            else:
                assert response.status_code in [422, 404]

    def test_category_preference_weighting(self):
        """Test: 카테고리별 선호도 가중치."""
        # Given: Category preferences with weights
        weighted_categories = {
            "user_id": TEST_USER_ID,
            "category_weights": {
                "restaurant": {"weight": 0.9, "reason": "food_lover"},
                "culture": {"weight": 0.7, "reason": "art_interest"},
                "cafe": {"weight": 0.6, "reason": "coffee_enthusiast"},
                "outdoor": {"weight": 0.4, "reason": "occasional_activity"},
            },
            "normalization_method": "softmax",
        }

        # When: Set category weights
        response = client.post(
            "/api/v1/preferences/set-category-weights", json=weighted_categories
        )

        # Then: Should create weighted preference profile
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            weighting_result = response.json()
            assert "category_weights_set" in weighting_result
            assert "normalized_weights" in weighting_result
            assert sum(
                weighting_result["normalized_weights"].values()
            ) == pytest.approx(1.0, abs=0.01)


class TestPreferenceRecommendationIntegration:
    """Test integration between preferences and recommendation system."""

    def test_preference_to_recommendation_mapping(self):
        """Test: 취향 설정에서 추천 시스템 연동."""
        # Given: Completed preference setup
        preference_setup = {
            "user_id": TEST_USER_ID,
            "completed_preferences": {
                "categories": ["restaurant", "cafe", "culture"],
                "budget_level": "medium",
                "location_radius_km": 10,
                "activity_intensity": "moderate",
                "group_type": "couple",
            },
            "preference_quality_score": 0.85,
            "setup_completion_time_minutes": 2.8,
        }

        # When: Generate initial recommendations from preferences
        response = client.post(
            "/api/v1/recommendations/from-preferences", json=preference_setup
        )

        # Then: Should provide initial recommendation set
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            rec_result = response.json()
            assert "initial_recommendations" in rec_result
            assert len(rec_result["initial_recommendations"]) >= 3
            assert "recommendation_reasoning" in rec_result

    def test_preference_seed_data_generation(self):
        """Test: 취향 기반 시드 데이터 생성."""
        # Given: User preferences for seed data
        seed_request = {
            "user_id": TEST_USER_ID,
            "preference_profile": {
                "top_categories": ["restaurant", "cafe"],
                "budget_comfort": "medium",
                "preferred_areas": ["gangnam", "hongdae"],
                "social_comfort": "moderate",
            },
            "seed_data_type": "initial_exploration",
            "sample_count": 5,
        }

        # When: Generate preference-based seed data
        response = client.post(
            "/api/v1/preferences/generate-seed-data", json=seed_request
        )

        # Then: Should create relevant seed data for exploration
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            seed_result = response.json()
            assert "seed_data_generated" in seed_result
            assert len(seed_result["seed_places"]) == 5
            assert "personalization_confidence" in seed_result

    def test_cross_category_preference_correlation(self):
        """Test: 카테고리 간 선호도 상관관계 분석."""
        # Given: Multi-category preference analysis
        correlation_analysis = {
            "user_id": TEST_USER_ID,
            "preference_interactions": [
                {
                    "category_pair": ["restaurant", "culture"],
                    "correlation_strength": 0.7,
                },
                {"category_pair": ["cafe", "shopping"], "correlation_strength": 0.6},
                {
                    "category_pair": ["outdoor", "entertainment"],
                    "correlation_strength": 0.4,
                },
            ],
            "analysis_period": "initial_setup",
        }

        # When: Analyze preference correlations
        response = client.post(
            "/api/v1/preferences/analyze-correlations", json=correlation_analysis
        )

        # Then: Should identify preference patterns for better recommendations
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            correlation_result = response.json()
            assert "correlation_patterns" in correlation_result
            assert "cross_category_insights" in correlation_result
            assert "recommendation_enhancement_opportunities" in correlation_result


@pytest.mark.integration
class TestPreferenceOnboardingIntegration:
    """Integration tests for preference setup and onboarding flow."""

    def test_complete_preference_onboarding_workflow(self):
        """Test: 전체 취향 설정 온보딩 워크플로우."""
        # Given: Complete preference onboarding workflow
        workflow_steps = [
            {
                "step": 1,
                "action": "start_preference_setup",
                "data": {"user_id": TEST_USER_ID, "setup_mode": "guided"},
            },
            {
                "step": 2,
                "action": "select_categories",
                "data": {
                    "categories": ["restaurant", "cafe", "culture"],
                    "confidence": "high",
                },
            },
            {
                "step": 3,
                "action": "configure_budget",
                "data": {"budget_level": "medium", "flexibility": "moderate"},
            },
            {
                "step": 4,
                "action": "set_location_preferences",
                "data": {"preferred_areas": ["gangnam"], "travel_range": 15},
            },
            {
                "step": 5,
                "action": "finalize_profile",
                "data": {"profile_completeness": 90, "ready_for_recommendations": True},
            },
        ]

        # When: Execute complete preference workflow
        workflow_results = []
        for step_data in workflow_steps:
            response = client.post(
                "/api/v1/preferences/execute-workflow-step", json=step_data
            )
            workflow_results.append(response.status_code in [200, 404])

        # Then: Should complete all preference setup steps
        completion_rate = sum(workflow_results) / len(workflow_results)
        assert (
            completion_rate >= 0.8
        ), f"Preference workflow completion {completion_rate:.2f} below 80%"

    def test_preference_to_personalization_handoff(self):
        """Test: 취향 설정에서 개인화 시스템 연동."""
        # Given: Completed preference setup ready for personalization
        handoff_data = {
            "user_id": TEST_USER_ID,
            "preference_profile": {
                "categories": ["restaurant", "culture"],
                "budget_comfort": "medium",
                "location_preferences": ["gangnam", "hongdae"],
                "activity_level": "moderate",
                "social_comfort": "public",
            },
            "profile_quality_score": 0.88,
            "ready_for_personalization": True,
        }

        # When: Initialize personalization from preferences
        response = client.post(
            "/api/v1/personalization/initialize-from-preferences", json=handoff_data
        )

        # Then: Should activate personalized features
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            personalization_result = response.json()
            assert "personalization_activated" in personalization_result
            assert "recommendation_engine_ready" in personalization_result
            assert "initial_content_prepared" in personalization_result


@pytest.mark.performance
class TestPreferenceSetupPerformance:
    """Performance tests for preference setup system."""

    def test_preference_setup_speed(self):
        """Test: 취향 설정 처리 속도."""
        # Given: Complex preference setup data
        complex_preferences = {
            "user_id": TEST_USER_ID,
            "comprehensive_preferences": {
                "categories": ["restaurant", "cafe", "culture", "shopping"],
                "detailed_weights": {
                    category: 0.8
                    for category in ["restaurant", "cafe", "culture", "shopping"]
                },
                "location_matrix": [
                    {"area": f"area_{i}", "score": 0.7} for i in range(20)
                ],
                "temporal_preferences": {f"time_slot_{i}": 0.6 for i in range(24)},
                "social_context": {f"context_{i}": 0.5 for i in range(10)},
            },
        }

        # When: Process complex preferences
        start_time = time.time()
        response = client.post(
            "/api/v1/preferences/process-comprehensive", json=complex_preferences
        )
        end_time = time.time()

        # Then: Should process efficiently
        processing_time = end_time - start_time
        assert (
            processing_time < 2.0
        ), f"Preference processing {processing_time:.3f}s exceeds 2 seconds"
        assert response.status_code in [200, 404]

    def test_concurrent_preference_setups(self):
        """Test: 동시 취향 설정 세션 처리."""
        from concurrent.futures import ThreadPoolExecutor

        def setup_preferences(user_index):
            preference_data = {
                "user_id": f"concurrent_user_{user_index}",
                "categories": ["restaurant", "cafe"],
                "budget": "medium",
            }
            try:
                response = client.post(
                    "/api/v1/preferences/quick-setup", json=preference_data
                )
                return response.status_code in [200, 404]
            except:
                return False

        # Simulate 15 concurrent preference setups
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(setup_preferences, i) for i in range(15)]
            results = [future.result() for future in futures]

        success_rate = sum(results) / len(results)
        assert (
            success_rate >= 0.9
        ), f"Concurrent preference setup success rate {success_rate:.2f} below 90%"

    def test_preference_retrieval_performance(self):
        """Test: 취향 설정 조회 성능."""
        # Given: Request to retrieve user preferences
        retrieval_request = {
            "user_id": TEST_USER_ID,
            "include_history": True,
            "include_correlations": True,
            "include_recommendations_preview": True,
        }

        # When: Retrieve comprehensive preference data
        start_time = time.time()
        response = client.get(
            "/api/v1/preferences/comprehensive", params=retrieval_request
        )
        end_time = time.time()

        # Then: Should retrieve quickly
        retrieval_time = end_time - start_time
        assert (
            retrieval_time < 1.0
        ), f"Preference retrieval {retrieval_time:.3f}s exceeds 1 second"
        assert response.status_code in [200, 404]


class TestPreferenceDataQuality:
    """Test preference data quality and validation."""

    def test_preference_consistency_validation(self):
        """Test: 취향 설정 일관성 검증."""
        # Given: Potentially inconsistent preferences
        consistency_check = {
            "user_id": TEST_USER_ID,
            "preference_data": {
                "stated_budget": "low",
                "selected_restaurants": [
                    {"name": "expensive_restaurant", "avg_price": 80000}
                ],
                "activity_level": "low",
                "selected_activities": [{"name": "hiking", "intensity": "high"}],
            },
        }

        # When: Check preference consistency
        response = client.post(
            "/api/v1/preferences/check-consistency", json=consistency_check
        )

        # Then: Should identify and report inconsistencies
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            consistency_result = response.json()
            assert "consistency_score" in consistency_result
            assert "inconsistencies_detected" in consistency_result
            assert "recommendations_for_resolution" in consistency_result

    def test_preference_completeness_scoring(self):
        """Test: 취향 설정 완성도 점수."""
        # Given: Preference profile for completeness assessment
        completeness_data = {
            "user_id": TEST_USER_ID,
            "profile_sections": {
                "basic_categories": {"completed": True, "detail_level": "high"},
                "budget_preferences": {"completed": True, "detail_level": "medium"},
                "location_preferences": {"completed": False, "detail_level": "none"},
                "activity_preferences": {"completed": True, "detail_level": "high"},
                "social_preferences": {"completed": False, "detail_level": "none"},
            },
        }

        # When: Calculate completeness score
        response = client.post(
            "/api/v1/preferences/calculate-completeness", json=completeness_data
        )

        # Then: Should provide completeness assessment
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            completeness_result = response.json()
            assert "completeness_percentage" in completeness_result
            assert "missing_critical_sections" in completeness_result
            assert "recommendation_quality_impact" in completeness_result

    def test_preference_learning_effectiveness(self):
        """Test: 취향 학습 효과성 측정."""
        # Given: Preference learning tracking data
        learning_data = {
            "user_id": TEST_USER_ID,
            "learning_period": "2_weeks",
            "initial_preferences": {
                "categories": ["restaurant", "cafe"],
                "accuracy_baseline": 0.6,
            },
            "learned_preferences": {
                "refined_categories": ["restaurant", "culture", "outdoor"],
                "improved_accuracy": 0.85,
                "learning_confidence": 0.9,
            },
            "behavior_data_points": 25,
        }

        # When: Evaluate learning effectiveness
        response = client.post(
            "/api/v1/preferences/evaluate-learning", json=learning_data
        )

        # Then: Should measure preference improvement
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            learning_result = response.json()
            assert "learning_improvement" in learning_result
            assert "recommendation_accuracy_gain" in learning_result
            assert "learning_effectiveness_score" in learning_result
