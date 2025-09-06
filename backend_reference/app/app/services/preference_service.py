"""User preference setup and survey system for onboarding personalization."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class PreferenceProfile:
    """Comprehensive user preference profile."""

    user_id: str
    categories: List[str]
    category_weights: Dict[str, float]
    budget_level: str
    budget_range: Dict[str, int]
    location_preferences: List[Dict[str, Any]]
    activity_intensity: str
    social_comfort: str
    companion_type: str
    quality_score: float
    created_at: datetime
    updated_at: datetime


class PreferenceSetupService:
    """Service for managing initial preference setup and collection."""

    def __init__(self, db_session=None):
        self.db = db_session
        self.valid_categories = [
            "restaurant",
            "cafe",
            "culture",
            "shopping",
            "entertainment",
            "outdoor",
            "wellness",
        ]
        self.valid_budget_levels = ["low", "medium", "high"]
        self.valid_activity_levels = ["low", "moderate", "high"]

    def setup_initial_categories(
        self,
        user_id: str,
        selected_categories: List[str],
        selection_reason: str = "personal_interest",
        confidence_level: str = "medium",
    ) -> Dict[str, Any]:
        """Set initial category preferences during onboarding."""

        # Validate category selection (2-5 categories required)
        if len(selected_categories) < 2:
            raise ValueError("Must select at least 2 categories")
        if len(selected_categories) > 5:
            raise ValueError("Cannot select more than 5 categories")

        # Validate category names
        invalid_categories = [
            cat for cat in selected_categories if cat not in self.valid_categories
        ]
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}")

        # Create initial preference profile
        preference_id = f"pref_{user_id}_{int(datetime.utcnow().timestamp())}"

        # Equal weights initially, will be refined through learning
        equal_weight = 1.0 / len(selected_categories)
        category_weights = {cat: equal_weight for cat in selected_categories}

        preference_profile = {
            "preference_id": preference_id,
            "user_id": user_id,
            "selected_categories": selected_categories,
            "category_weights": category_weights,
            "selection_metadata": {
                "reason": selection_reason,
                "confidence": confidence_level,
                "method": "initial_selection",
            },
            "categories_saved": True,
            "setup_stage": "categories_complete",
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Initial categories set for user {user_id}: {selected_categories}")
        return preference_profile

    def configure_location_preferences(
        self,
        user_id: str,
        preferred_areas: List[Dict[str, Any]],
        travel_range_km: float,
        transportation_preferences: List[str],
    ) -> Dict[str, Any]:
        """Configure location-based preference settings."""

        # Validate travel range
        if not (1.0 <= travel_range_km <= 50.0):
            raise ValueError("Travel range must be between 1 and 50 km")

        # Validate transportation modes
        valid_transport = ["walking", "subway", "bus", "taxi", "driving"]
        invalid_transport = [
            mode for mode in transportation_preferences if mode not in valid_transport
        ]
        if invalid_transport:
            raise ValueError(f"Invalid transportation modes: {invalid_transport}")

        # Process preferred areas with scoring
        processed_areas = []
        for area in preferred_areas:
            if "name" not in area or "preference_score" not in area:
                raise ValueError("Each area must have name and preference_score")
            if not (0.0 <= area["preference_score"] <= 1.0):
                raise ValueError("Preference score must be between 0.0 and 1.0")
            processed_areas.append(area)

        location_config = {
            "user_id": user_id,
            "preferred_areas": processed_areas,
            "preferred_areas_configured": True,
            "travel_range_km": travel_range_km,
            "travel_range_set": True,
            "transportation_modes": transportation_preferences,
            "transport_preferences_saved": True,
            "location_personalization_ready": True,
            "configured_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Location preferences configured for user {user_id}")
        return location_config

    def setup_budget_preferences(
        self,
        user_id: str,
        budget_category: str,
        per_place_range: Dict[str, int],
        total_course_budget: Dict[str, int],
        budget_flexibility: str = "moderate",
    ) -> Dict[str, Any]:
        """Configure budget range and flexibility settings."""

        # Validate budget category
        if budget_category not in self.valid_budget_levels:
            raise ValueError(
                f"Budget category must be one of: {self.valid_budget_levels}"
            )

        # Validate budget flexibility
        valid_flexibility = ["strict", "moderate", "flexible"]
        if budget_flexibility not in valid_flexibility:
            raise ValueError(f"Budget flexibility must be one of: {valid_flexibility}")

        # Validate budget ranges
        required_fields = ["min_amount", "max_amount", "currency"]
        for budget_type, budget_data in [
            ("per_place", per_place_range),
            ("total_course", total_course_budget),
        ]:
            for field in required_fields:
                if field not in budget_data:
                    raise ValueError(f"{budget_type} budget missing {field}")

            if budget_data["min_amount"] >= budget_data["max_amount"]:
                raise ValueError(
                    f"{budget_type} min_amount must be less than max_amount"
                )

        budget_config = {
            "user_id": user_id,
            "budget_category": budget_category,
            "budget_range_configured": True,
            "per_place_budget": per_place_range,
            "total_course_budget": total_course_budget,
            "price_filtering_enabled": True,
            "budget_flexibility": budget_flexibility,
            "flexibility_level_set": True,
            "budget_personalization_active": True,
            "configured_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Budget preferences configured for user {user_id}: {budget_category}"
        )
        return budget_config

    def configure_companion_preferences(
        self,
        user_id: str,
        primary_companion_type: str,
        group_size_preference: str,
        social_comfort_level: str,
        special_needs: List[str] = None,
    ) -> Dict[str, Any]:
        """Configure companion and social preferences."""

        # Validate companion types
        valid_companions = ["alone", "romantic_partner", "friends", "family"]
        if primary_companion_type not in valid_companions:
            raise ValueError(f"Companion type must be one of: {valid_companions}")

        # Validate group sizes
        valid_group_sizes = ["solo", "couple", "small_group", "large_group"]
        if group_size_preference not in valid_group_sizes:
            raise ValueError(f"Group size must be one of: {valid_group_sizes}")

        # Validate social comfort levels
        valid_comfort = ["introverted", "moderate", "extroverted"]
        if social_comfort_level not in valid_comfort:
            raise ValueError(f"Social comfort must be one of: {valid_comfort}")

        companion_config = {
            "user_id": user_id,
            "primary_companion_type": primary_companion_type,
            "companion_type_set": True,
            "group_size_preference": group_size_preference,
            "group_size_configured": True,
            "social_comfort_level": social_comfort_level,
            "social_preferences_saved": True,
            "special_needs": special_needs or [],
            "accessibility_configured": len(special_needs or []) > 0,
            "configured_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Companion preferences configured for user {user_id}")
        return companion_config

    def configure_activity_level(
        self,
        user_id: str,
        activity_intensity: str,
        walking_tolerance: Dict[str, Any],
        time_availability: Dict[str, Any],
        physical_considerations: List[str] = None,
    ) -> Dict[str, Any]:
        """Configure activity level and physical preferences."""

        # Validate activity intensity
        if activity_intensity not in self.valid_activity_levels:
            raise ValueError(
                f"Activity intensity must be one of: {self.valid_activity_levels}"
            )

        # Validate walking tolerance
        if "max_distance_km" not in walking_tolerance:
            raise ValueError("Walking tolerance must include max_distance_km")
        if not (0.5 <= walking_tolerance["max_distance_km"] <= 10.0):
            raise ValueError("Max walking distance must be between 0.5 and 10 km")

        # Validate time availability
        required_time_fields = [
            "typical_course_duration_hours",
            "max_course_duration_hours",
        ]
        for field in required_time_fields:
            if field not in time_availability:
                raise ValueError(f"Time availability missing {field}")

        activity_config = {
            "user_id": user_id,
            "activity_intensity": activity_intensity,
            "activity_level_configured": True,
            "walking_tolerance": walking_tolerance,
            "walking_preferences_set": True,
            "time_availability": time_availability,
            "time_preferences_set": True,
            "physical_considerations": physical_considerations or [],
            "accessibility_needs_configured": len(physical_considerations or []) > 0,
            "configured_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Activity level configured for user {user_id}: {activity_intensity}"
        )
        return activity_config


class PreferenceSurveyService:
    """Service for managing preference survey and questionnaire system."""

    def __init__(self, db_session=None):
        self.db = db_session
        self.survey_versions = {
            "quick": {"questions": 4, "estimated_minutes": 1.5},
            "standard": {"questions": 8, "estimated_minutes": 3.0},
            "comprehensive": {"questions": 15, "estimated_minutes": 5.0},
        }

    def complete_preference_survey(
        self,
        user_id: str,
        survey_version: str,
        responses: List[Dict[str, Any]],
        completion_time_minutes: float,
    ) -> Dict[str, Any]:
        """Process completed preference survey and generate profile."""

        # Validate survey version
        if survey_version not in self.survey_versions:
            raise ValueError(f"Invalid survey version: {survey_version}")

        # Validate response completeness
        expected_questions = self.survey_versions[survey_version]["questions"]
        if len(responses) < expected_questions * 0.8:  # Allow 20% incomplete
            raise ValueError(
                f"Insufficient responses: {len(responses)}/{expected_questions}"
            )

        # Analyze response patterns
        response_analysis = self._analyze_survey_responses(responses)

        # Generate preference profile from survey
        preference_profile = self._generate_profile_from_survey(
            user_id, responses, response_analysis
        )

        survey_result = {
            "user_id": user_id,
            "survey_completed": True,
            "survey_version": survey_version,
            "total_responses": len(responses),
            "completion_time_minutes": completion_time_minutes,
            "meets_time_requirement": completion_time_minutes <= 3.0,
            "preference_profile_created": True,
            "profile_quality_score": preference_profile["quality_score"],
            "response_analysis": response_analysis,
            "completed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Survey completed for user {user_id}: {survey_version} in {completion_time_minutes:.1f}min"
        )
        return survey_result

    def generate_adaptive_survey(
        self,
        user_id: str,
        previous_answers: List[Dict[str, Any]],
        adaptive_questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate adaptive survey questions based on previous responses."""

        # Analyze previous answers for patterns
        answer_patterns = self._analyze_response_patterns(previous_answers)

        # Generate personalized follow-up questions
        personalized_questions = []
        for question in adaptive_questions:
            if self._should_include_adaptive_question(question, answer_patterns):
                personalized_questions.append(question)

        # Calculate adaptation confidence
        adaptation_confidence = self._calculate_adaptation_confidence(
            previous_answers, personalized_questions
        )

        adaptive_result = {
            "user_id": user_id,
            "adaptive_questions_generated": True,
            "personalized_questions": personalized_questions,
            "adaptation_confidence": adaptation_confidence,
            "personalization_improved": adaptation_confidence > 0.7,
            "previous_answers_analyzed": len(previous_answers),
            "generated_at": datetime.utcnow().isoformat(),
        }

        return adaptive_result

    def validate_preference_configuration(
        self, user_id: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate preference configuration for completeness and consistency."""

        validation_results = {
            "is_valid": True,
            "validation_errors": [],
            "validation_warnings": [],
        }

        # Validate categories
        if "categories" in preferences:
            categories = preferences["categories"]
            if len(categories) < 2:
                validation_results["is_valid"] = False
                validation_results["validation_errors"].append(
                    "Must select at least 2 categories"
                )
            elif len(categories) > 5:
                validation_results["is_valid"] = False
                validation_results["validation_errors"].append(
                    "Cannot select more than 5 categories"
                )

            invalid_cats = [
                cat for cat in categories if cat not in self.valid_categories
            ]
            if invalid_cats:
                validation_results["is_valid"] = False
                validation_results["validation_errors"].append(
                    f"Invalid categories: {invalid_cats}"
                )

        # Validate budget consistency
        if "budget" in preferences:
            budget = preferences["budget"]
            if budget not in self.valid_budget_levels:
                validation_results["is_valid"] = False
                validation_results["validation_errors"].append(
                    f"Invalid budget level: {budget}"
                )

        validation_result = {
            "user_id": user_id,
            "validation_passed": validation_results["is_valid"],
            "validation_details": validation_results,
            "validated_at": datetime.utcnow().isoformat(),
        }

        return validation_result

    def calculate_preference_scores(
        self,
        user_id: str,
        weighted_preferences: Dict[str, Dict[str, float]],
        importance_weights: Dict[str, float],
    ) -> Dict[str, Any]:
        """Calculate weighted preference scores for recommendation system."""

        # Normalize importance weights to sum to 1.0
        total_importance = sum(importance_weights.values())
        if total_importance == 0:
            raise ValueError("Importance weights cannot all be zero")

        normalized_importance = {
            category: weight / total_importance
            for category, weight in importance_weights.items()
        }

        # Calculate weighted scores
        category_scores = {}
        total_weighted_score = 0.0

        for category, preferences in weighted_preferences.items():
            if category in normalized_importance:
                # Calculate average preference for this category
                avg_preference = sum(preferences.values()) / len(preferences)

                # Weight by category importance
                weighted_score = avg_preference * normalized_importance[category]
                category_scores[category] = weighted_score
                total_weighted_score += weighted_score

        # Generate score breakdown
        scoring_result = {
            "user_id": user_id,
            "preference_scores_calculated": True,
            "total_weighted_score": round(total_weighted_score, 3),
            "category_breakdown": {
                category: round(score, 3) for category, score in category_scores.items()
            },
            "normalized_weights": normalized_importance,
            "scoring_quality": "high" if total_weighted_score > 0.7 else "medium",
            "calculated_at": datetime.utcnow().isoformat(),
        }

        return scoring_result

    def _analyze_survey_responses(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze survey responses for patterns and quality."""

        # Calculate response quality metrics
        total_responses = len(responses)
        high_confidence_responses = sum(
            1 for r in responses if r.get("confidence", 0.5) > 0.7
        )
        avg_confidence = (
            sum(r.get("confidence", 0.5) for r in responses) / total_responses
        )

        # Identify preference patterns
        category_mentions = {}
        for response in responses:
            answer = response.get("answer", "")
            for category in self.valid_categories:
                if category in answer or category.replace("_", " ") in answer:
                    category_mentions[category] = category_mentions.get(category, 0) + 1

        analysis = {
            "total_responses": total_responses,
            "average_confidence": round(avg_confidence, 3),
            "high_confidence_percentage": round(
                high_confidence_responses / total_responses * 100, 1
            ),
            "category_patterns": category_mentions,
            "response_quality": "high" if avg_confidence > 0.7 else "medium",
        }

        return analysis

    def _generate_profile_from_survey(
        self, user_id: str, responses: List[Dict[str, Any]], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate preference profile from survey responses."""

        # Extract categories from response analysis
        category_patterns = analysis.get("category_patterns", {})
        top_categories = sorted(
            category_patterns.items(), key=lambda x: x[1], reverse=True
        )[
            :4
        ]  # Top 4 categories

        # Generate quality score based on response completeness and confidence
        quality_factors = [
            analysis["average_confidence"],
            min(1.0, len(responses) / 10),  # Response completeness
            min(1.0, len(top_categories) / 3),  # Category coverage
        ]
        quality_score = sum(quality_factors) / len(quality_factors)

        profile = {
            "user_id": user_id,
            "derived_categories": [cat for cat, _ in top_categories],
            "category_confidence_scores": dict(top_categories),
            "quality_score": round(quality_score, 3),
            "profile_completeness": "high" if quality_score > 0.8 else "medium",
            "ready_for_recommendations": quality_score > 0.6,
        }

        return profile

    def _analyze_response_patterns(
        self, previous_answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze response patterns for adaptive questioning."""

        patterns = {
            "response_speed": [],
            "confidence_levels": [],
            "category_interests": {},
            "detail_preferences": [],
        }

        for answer in previous_answers:
            # Track confidence patterns
            if "confidence" in answer:
                patterns["confidence_levels"].append(answer["confidence"])

            # Extract category interests from answers
            answer_text = str(answer.get("answer", "")).lower()
            for category in self.valid_categories:
                if category in answer_text:
                    patterns["category_interests"][category] = (
                        patterns["category_interests"].get(category, 0) + 1
                    )

        return patterns

    def _should_include_adaptive_question(
        self, question: Dict[str, Any], patterns: Dict[str, Any]
    ) -> bool:
        """Determine if adaptive question should be included based on patterns."""

        triggered_by = question.get("triggered_by", "")

        # Check if trigger condition is met in patterns
        if triggered_by in patterns.get("category_interests", {}):
            return patterns["category_interests"][triggered_by] >= 2

        # Default inclusion for unrecognized triggers
        return True

    def _calculate_adaptation_confidence(
        self,
        previous_answers: List[Dict[str, Any]],
        adaptive_questions: List[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in adaptive question selection."""

        if not previous_answers or not adaptive_questions:
            return 0.5

        # Base confidence on response quality and pattern strength
        avg_confidence = sum(
            answer.get("confidence", 0.5) for answer in previous_answers
        ) / len(previous_answers)

        pattern_strength = min(
            1.0, len(adaptive_questions) / 3
        )  # More questions = stronger patterns

        adaptation_confidence = (avg_confidence + pattern_strength) / 2

        return round(adaptation_confidence, 3)


class CategoryPreferenceService:
    """Service for managing category preferences and weighting."""

    def __init__(self, db_session=None):
        self.db = db_session
        self.category_definitions = {
            "restaurant": {
                "description": "식당, 맛집, 다이닝",
                "keywords": ["food", "dining", "restaurant"],
            },
            "cafe": {
                "description": "카페, 커피샵, 디저트",
                "keywords": ["coffee", "cafe", "dessert"],
            },
            "culture": {
                "description": "박물관, 갤러리, 전시",
                "keywords": ["museum", "gallery", "art"],
            },
            "shopping": {
                "description": "쇼핑, 시장, 백화점",
                "keywords": ["shopping", "market", "mall"],
            },
            "entertainment": {
                "description": "영화, 공연, 게임",
                "keywords": ["movie", "show", "game"],
            },
            "outdoor": {
                "description": "공원, 산책, 야외활동",
                "keywords": ["park", "outdoor", "nature"],
            },
            "wellness": {
                "description": "스파, 마사지, 힐링",
                "keywords": ["spa", "wellness", "healing"],
            },
        }

    def get_available_categories(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get available categories with contextual information."""

        # Customize categories based on user context
        location = user_context.get("location", "seoul")
        age_group = user_context.get("age_group", "20s_30s")
        user_type = user_context.get("user_type", "dating_couples")

        # Filter relevant categories based on context
        contextual_categories = self.category_definitions.copy()

        # Add context-specific descriptions
        for category, definition in contextual_categories.items():
            definition["contextual_relevance"] = self._calculate_category_relevance(
                category, location, age_group, user_type
            )

        # Sort by relevance
        sorted_categories = sorted(
            contextual_categories.items(),
            key=lambda x: x[1]["contextual_relevance"],
            reverse=True,
        )

        categories_result = {
            "available_categories": [
                {
                    "category_id": category,
                    "name": category,
                    "description": definition["description"],
                    "relevance_score": definition["contextual_relevance"],
                    "keywords": definition["keywords"],
                }
                for category, definition in sorted_categories
            ],
            "category_descriptions": {
                cat: def_["description"] for cat, def_ in contextual_categories.items()
            },
            "total_available": len(contextual_categories),
            "context_applied": {
                "location": location,
                "age_group": age_group,
                "user_type": user_type,
            },
        }

        return categories_result

    def validate_category_selection(
        self, user_id: str, selected_categories: List[str]
    ) -> Dict[str, Any]:
        """Validate category selection rules and constraints."""

        validation_result = {"categories_valid": True, "validation_errors": []}

        # Check count constraints (2-5 categories)
        if len(selected_categories) < 2:
            validation_result["categories_valid"] = False
            validation_result["validation_errors"].append(
                "Must select at least 2 categories"
            )
        elif len(selected_categories) > 5:
            validation_result["categories_valid"] = False
            validation_result["validation_errors"].append(
                "Cannot select more than 5 categories"
            )

        # Check valid category names
        invalid_categories = [
            cat for cat in selected_categories if cat not in self.category_definitions
        ]
        if invalid_categories:
            validation_result["categories_valid"] = False
            validation_result["validation_errors"].append(
                f"Invalid categories: {invalid_categories}"
            )

        # Check for balanced selection
        if len(set(selected_categories)) != len(selected_categories):
            validation_result["categories_valid"] = False
            validation_result["validation_errors"].append(
                "Duplicate categories not allowed"
            )

        result = {
            "user_id": user_id,
            "selected_categories": selected_categories,
            "category_count": len(selected_categories),
            "validation_passed": validation_result["categories_valid"],
            "validation_errors": validation_result["validation_errors"],
            "validated_at": datetime.utcnow().isoformat(),
        }

        return result

    def set_category_weights(
        self,
        user_id: str,
        category_weights: Dict[str, Dict[str, float]],
        normalization_method: str = "softmax",
    ) -> Dict[str, Any]:
        """Set weighted preferences for categories."""

        # Validate categories exist
        for category in category_weights.keys():
            if category not in self.category_definitions:
                raise ValueError(f"Unknown category: {category}")

        # Apply normalization
        if normalization_method == "softmax":
            normalized_weights = self._apply_softmax_normalization(category_weights)
        elif normalization_method == "linear":
            normalized_weights = self._apply_linear_normalization(category_weights)
        else:
            raise ValueError(f"Unknown normalization method: {normalization_method}")

        weighting_result = {
            "user_id": user_id,
            "category_weights_set": True,
            "original_weights": category_weights,
            "normalized_weights": normalized_weights,
            "normalization_method": normalization_method,
            "weights_sum": round(sum(normalized_weights.values()), 3),
            "configured_at": datetime.utcnow().isoformat(),
        }

        return weighting_result

    def _calculate_category_relevance(
        self, category: str, location: str, age_group: str, user_type: str
    ) -> float:
        """Calculate category relevance based on user context."""

        # Base relevance scores
        base_scores = {
            "restaurant": 0.9,  # Universal appeal
            "cafe": 0.8,  # High for dating
            "culture": 0.7,  # Moderate appeal
            "shopping": 0.6,  # Context dependent
            "entertainment": 0.8,  # High for couples
            "outdoor": 0.7,  # Weather dependent
            "wellness": 0.5,  # Niche appeal
        }

        base_score = base_scores.get(category, 0.5)

        # Context modifiers
        context_modifiers = 1.0

        if user_type == "dating_couples":
            if category in ["restaurant", "cafe", "culture"]:
                context_modifiers *= 1.2
            elif category == "wellness":
                context_modifiers *= 0.8

        if age_group == "20s_30s":
            if category in ["entertainment", "outdoor"]:
                context_modifiers *= 1.1

        if location == "seoul":
            if category in ["culture", "shopping"]:
                context_modifiers *= 1.1

        final_score = min(1.0, base_score * context_modifiers)
        return round(final_score, 3)

    def _apply_softmax_normalization(
        self, category_weights: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Apply softmax normalization to category weights."""

        # Calculate average weight per category
        avg_weights = {}
        for category, weights in category_weights.items():
            avg_weights[category] = sum(weights.values()) / len(weights)

        # Apply softmax
        exp_weights = {cat: math.exp(weight) for cat, weight in avg_weights.items()}
        sum_exp = sum(exp_weights.values())

        normalized = {
            cat: round(exp_weight / sum_exp, 3)
            for cat, exp_weight in exp_weights.items()
        }

        return normalized

    def _apply_linear_normalization(
        self, category_weights: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Apply linear normalization to category weights."""

        # Calculate average weight per category
        avg_weights = {}
        for category, weights in category_weights.items():
            avg_weights[category] = sum(weights.values()) / len(weights)

        # Linear normalization
        total_weight = sum(avg_weights.values())
        if total_weight == 0:
            # Equal weights if all zero
            equal_weight = 1.0 / len(avg_weights)
            return {cat: equal_weight for cat in avg_weights.keys()}

        normalized = {
            cat: round(weight / total_weight, 3) for cat, weight in avg_weights.items()
        }

        return normalized


class PreferencePersonalizationService:
    """Service for personalizing onboarding based on user preferences."""

    def __init__(self, db_session=None):
        self.db = db_session

    def create_personalized_onboarding(
        self,
        user_id: str,
        demographic_info: Dict[str, Any],
        initial_signals: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create personalized onboarding flow based on user signals."""

        # Analyze initial signals
        signal_analysis = self._analyze_initial_signals(initial_signals)

        # Generate customized questions
        customized_questions = self._generate_personalized_questions(
            demographic_info, signal_analysis
        )

        # Estimate completion time
        estimated_time = self._estimate_completion_time(
            customized_questions, signal_analysis
        )

        personalization_result = {
            "user_id": user_id,
            "personalized_flow_created": True,
            "customized_questions": customized_questions,
            "estimated_completion_time": estimated_time,
            "personalization_confidence": signal_analysis["confidence"],
            "signal_analysis": signal_analysis,
            "created_at": datetime.utcnow().isoformat(),
        }

        return personalization_result

    def learn_from_behavior(
        self,
        user_id: str,
        interaction_patterns: List[Dict[str, Any]],
        time_spent_per_category: Dict[str, int],
    ) -> Dict[str, Any]:
        """Learn and update preferences from user behavior."""

        # Analyze interaction patterns
        behavior_insights = self._analyze_interaction_patterns(interaction_patterns)

        # Update category preferences based on time spent
        updated_weights = self._calculate_behavior_weights(time_spent_per_category)

        # Generate insights and recommendations
        learning_insights = self._generate_learning_insights(
            behavior_insights, updated_weights
        )

        learning_result = {
            "user_id": user_id,
            "preferences_updated": True,
            "behavior_insights": behavior_insights,
            "updated_category_weights": updated_weights,
            "learning_confidence": learning_insights["confidence"],
            "recommendation_improvements": learning_insights["improvements"],
            "analyzed_at": datetime.utcnow().isoformat(),
        }

        return learning_result

    def assess_preference_quality(
        self,
        user_id: str,
        completed_categories: int,
        detailed_responses: int,
        consistency_score: float,
        completion_percentage: float,
        engagement_indicators: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess quality and completeness of preference configuration."""

        # Calculate quality score components
        completeness_factor = min(1.0, completion_percentage / 100)
        detail_factor = (
            min(1.0, detailed_responses / completed_categories)
            if completed_categories > 0
            else 0
        )
        consistency_factor = consistency_score

        # Analyze engagement quality
        engagement_score = self._assess_engagement_quality(engagement_indicators)

        # Overall quality score
        quality_components = [
            completeness_factor,
            detail_factor,
            consistency_factor,
            engagement_score,
        ]
        quality_score = sum(quality_components) / len(quality_components)

        # Determine recommendation readiness
        recommendation_readiness = {
            "is_ready": quality_score > 0.7,
            "confidence_level": "high"
            if quality_score > 0.8
            else "medium"
            if quality_score > 0.6
            else "low",
            "expected_recommendation_quality": quality_score
            * 0.9,  # Conservative estimate
        }

        quality_result = {
            "user_id": user_id,
            "quality_score": round(quality_score, 3),
            "completeness_percentage": completion_percentage,
            "quality_components": {
                "completeness": round(completeness_factor, 3),
                "detail_level": round(detail_factor, 3),
                "consistency": round(consistency_factor, 3),
                "engagement": round(engagement_score, 3),
            },
            "recommendation_readiness": recommendation_readiness,
            "assessed_at": datetime.utcnow().isoformat(),
        }

        return quality_result

    def update_preference_profile(
        self,
        user_id: str,
        updated_preferences: Dict[str, Any],
        update_reason: str,
        update_confidence: float,
    ) -> Dict[str, Any]:
        """Update user preference profile with change tracking."""

        # Archive current preferences (mock)
        current_preferences = {
            "categories": ["restaurant", "cafe"],
            "budget_level": "medium",
            "activity_level": "moderate",
        }

        # Apply updates
        merged_preferences = {**current_preferences, **updated_preferences}

        # Track changes
        changes_detected = []
        for key, new_value in updated_preferences.items():
            if key in current_preferences and current_preferences[key] != new_value:
                changes_detected.append(
                    {
                        "field": key,
                        "old_value": current_preferences[key],
                        "new_value": new_value,
                    }
                )

        update_result = {
            "user_id": user_id,
            "preferences_updated": True,
            "changes_detected": changes_detected,
            "previous_preferences_archived": True,
            "merged_preferences": merged_preferences,
            "update_confidence": update_confidence,
            "recommendation_engine_refreshed": True,
            "update_reason": update_reason,
            "updated_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Preferences updated for user {user_id}: {len(changes_detected)} changes"
        )
        return update_result

    def _analyze_initial_signals(
        self, initial_signals: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze initial user signals for personalization."""

        # Extract insights from signals
        insights = {
            "likely_interests": [],
            "user_sophistication": "medium",
            "urgency_level": "medium",
            "confidence": 0.6,
        }

        # Analyze install source
        install_source = initial_signals.get("app_install_source", "unknown")
        if "instagram" in install_source:
            insights["likely_interests"].extend(["visual_appeal", "trendy_places"])
            insights["user_sophistication"] = "high"

        # Analyze first search
        first_search = initial_signals.get("first_search_query", "").lower()
        if "데이트" in first_search or "date" in first_search:
            insights["likely_interests"].append("romantic_places")
        if "맛집" in first_search or "food" in first_search:
            insights["likely_interests"].append("dining_focused")

        # Adjust confidence based on signal quality
        signal_count = sum(
            1 for signal in initial_signals.values() if signal and signal != "unknown"
        )
        insights["confidence"] = min(0.9, 0.4 + (signal_count * 0.15))

        return insights

    def _generate_personalized_questions(
        self, demographic_info: Dict[str, Any], signal_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate personalized survey questions."""

        base_questions = [
            {"id": "q1", "text": "주로 어떤 유형의 장소를 선호하시나요?", "type": "category_selection"},
            {"id": "q2", "text": "데이트 코스 예산은 어느 정도가 적당한가요?", "type": "budget_range"},
        ]

        # Add personalized questions based on signals
        likely_interests = signal_analysis.get("likely_interests", [])

        if "dining_focused" in likely_interests:
            base_questions.append(
                {
                    "id": "q3_food",
                    "text": "선호하는 음식 타입이나 분위기가 있나요?",
                    "type": "detailed_preference",
                }
            )

        if "romantic_places" in likely_interests:
            base_questions.append(
                {
                    "id": "q3_romantic",
                    "text": "로맨틱한 분위기에서 중요하게 생각하는 요소는?",
                    "type": "detailed_preference",
                }
            )

        return base_questions

    def _estimate_completion_time(
        self, questions: List[Dict[str, Any]], signal_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Estimate completion time based on question complexity and user signals."""

        base_time_per_question = 20  # seconds

        # Adjust based on user sophistication
        sophistication = signal_analysis.get("user_sophistication", "medium")
        sophistication_multiplier = {"low": 1.5, "medium": 1.0, "high": 0.8}[
            sophistication
        ]

        estimated_seconds = (
            len(questions) * base_time_per_question * sophistication_multiplier
        )
        estimated_minutes = estimated_seconds / 60

        return {
            "estimated_minutes": round(estimated_minutes, 1),
            "estimated_seconds": int(estimated_seconds),
            "meets_3min_target": estimated_minutes <= 3.0,
            "sophistication_factor": sophistication_multiplier,
            "question_count": len(questions),
        }

    def _analyze_interaction_patterns(
        self, patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user interaction patterns during onboarding."""

        insights = {
            "engagement_level": "medium",
            "content_preferences": {},
            "interaction_quality": "medium",
        }

        # Analyze time spent patterns
        high_engagement_actions = sum(
            1 for pattern in patterns if pattern.get("duration_seconds", 0) > 30
        )

        if high_engagement_actions >= len(patterns) * 0.6:
            insights["engagement_level"] = "high"
        elif high_engagement_actions <= len(patterns) * 0.3:
            insights["engagement_level"] = "low"

        # Extract content preferences
        for pattern in patterns:
            content_type = pattern.get("content_type", "")
            if content_type:
                action = pattern.get("action", "")
                if action in [
                    "saved_to_favorites",
                    "shared_externally",
                    "spent_time_viewing",
                ]:
                    insights["content_preferences"][content_type] = (
                        insights["content_preferences"].get(content_type, 0) + 1
                    )

        return insights

    def _calculate_behavior_weights(
        self, time_spent: Dict[str, int]
    ) -> Dict[str, float]:
        """Calculate category weights based on time spent."""

        if not time_spent:
            return {}

        total_time = sum(time_spent.values())
        if total_time == 0:
            return {}

        # Convert time to weights
        weights = {
            category: time_seconds / total_time
            for category, time_seconds in time_spent.items()
        }

        return {cat: round(weight, 3) for cat, weight in weights.items()}

    def _generate_learning_insights(
        self, behavior_insights: Dict[str, Any], updated_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate insights from behavior learning."""

        # Calculate learning confidence
        engagement = behavior_insights.get("engagement_level", "medium")
        engagement_scores = {"low": 0.3, "medium": 0.6, "high": 0.9}
        confidence = engagement_scores[engagement]

        # Identify improvements
        improvements = []
        if updated_weights:
            top_category = max(updated_weights.items(), key=lambda x: x[1])
            improvements.append(
                f"Increased focus on {top_category[0]} based on engagement"
            )

        return {
            "confidence": confidence,
            "improvements": improvements,
            "learning_quality": engagement,
        }

    def _assess_engagement_quality(
        self, engagement_indicators: Dict[str, Any]
    ) -> float:
        """Assess engagement quality from indicators."""

        time_spent = engagement_indicators.get("time_spent_minutes", 0)
        question_skips = engagement_indicators.get("question_skips", 0)
        detail_level = engagement_indicators.get("detail_level", "basic")

        # Time factor (optimal around 2-3 minutes)
        if 2.0 <= time_spent <= 3.5:
            time_factor = 1.0
        elif time_spent < 2.0:
            time_factor = time_spent / 2.0
        else:
            time_factor = max(0.5, 3.5 / time_spent)

        # Skip factor (fewer skips = higher engagement)
        skip_factor = max(0.0, 1.0 - (question_skips * 0.2))

        # Detail factor
        detail_factors = {"basic": 0.5, "standard": 0.7, "comprehensive": 1.0}
        detail_factor = detail_factors.get(detail_level, 0.5)

        engagement_score = (time_factor + skip_factor + detail_factor) / 3
        return round(engagement_score, 3)
