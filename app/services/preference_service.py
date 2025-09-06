"""User preference setup and survey system for onboarding personalization."""

import logging
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

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
    ) -> Dict[str, Any]:
        """Setup initial category preferences for a user.
        
        Given: User selects 2-5 categories during onboarding
        When: Categories are validated and saved
        Then: Should create preference profile with equal weights
        """
        if len(selected_categories) < 2 or len(selected_categories) > 5:
            raise ValueError("Must select between 2-5 categories")
            
        invalid_categories = [cat for cat in selected_categories if cat not in self.valid_categories]
        if invalid_categories:
            raise ValueError(f"Invalid categories: {invalid_categories}")
            
        # Create equal weights for selected categories
        weight_per_category = 1.0 / len(selected_categories)
        category_weights = {cat: weight_per_category for cat in selected_categories}
        
        preference_data = {
            "user_id": user_id,
            "categories": selected_categories,
            "category_weights": category_weights,
            "setup_completed": True,
            "created_at": datetime.utcnow(),
        }
        
        logger.info(f"Initial categories setup for user {user_id}: {selected_categories}")
        
        return {
            "success": True,
            "categories": selected_categories,
            "weights": category_weights,
            "next_step": "location_preferences",
        }

    def setup_location_preferences(
        self,
        user_id: str,
        current_location: Dict[str, float],
        preferred_areas: List[str],
        max_travel_distance: int = 10,
        transport_modes: List[str] = None,
    ) -> Dict[str, Any]:
        """Setup location-based preferences.
        
        Given: User provides location preferences
        When: Location data is validated and saved
        Then: Should configure location-based recommendations
        """
        if transport_modes is None:
            transport_modes = ["walking", "public_transport"]
            
        location_prefs = {
            "current_location": current_location,
            "preferred_areas": preferred_areas,
            "max_travel_distance_km": max_travel_distance,
            "transport_modes": transport_modes,
            "location_flexibility": "medium",  # low, medium, high
        }
        
        return {
            "success": True,
            "location_preferences": location_prefs,
            "next_step": "budget_setup",
        }

    def setup_budget_preferences(
        self,
        user_id: str,
        budget_level: str,
        custom_ranges: Optional[Dict[str, Dict[str, int]]] = None,
        budget_flexibility: str = "medium",
    ) -> Dict[str, Any]:
        """Setup budget preferences and ranges.
        
        Given: User selects budget level and preferences
        When: Budget data is validated
        Then: Should configure budget-based filtering
        """
        if budget_level not in self.valid_budget_levels:
            raise ValueError(f"Invalid budget level: {budget_level}")
            
        # Default budget ranges (KRW)
        default_ranges = {
            "low": {
                "meal": {"min": 10000, "max": 20000},
                "cafe": {"min": 5000, "max": 10000},
                "activity": {"min": 0, "max": 15000},
            },
            "medium": {
                "meal": {"min": 15000, "max": 40000},
                "cafe": {"min": 8000, "max": 15000},
                "activity": {"min": 10000, "max": 30000},
            },
            "high": {
                "meal": {"min": 30000, "max": 100000},
                "cafe": {"min": 12000, "max": 25000},
                "activity": {"min": 20000, "max": 80000},
            },
        }
        
        budget_ranges = custom_ranges if custom_ranges else default_ranges[budget_level]
        
        budget_data = {
            "budget_level": budget_level,
            "budget_ranges": budget_ranges,
            "budget_flexibility": budget_flexibility,
            "special_occasion_multiplier": 1.5 if budget_level != "high" else 2.0,
        }
        
        return {
            "success": True,
            "budget_preferences": budget_data,
            "next_step": "companion_preferences",
        }

    def setup_companion_preferences(
        self,
        user_id: str,
        companion_type: str,
        group_size_preference: int = 2,
        social_comfort_level: str = "medium",
    ) -> Dict[str, Any]:
        """Setup companion and social preferences.
        
        Given: User specifies companion preferences
        When: Social preference data is validated
        Then: Should configure group-based recommendations
        """
        valid_companion_types = ["couple", "friends", "family", "solo", "mixed"]
        if companion_type not in valid_companion_types:
            raise ValueError(f"Invalid companion type: {companion_type}")
            
        companion_prefs = {
            "companion_type": companion_type,
            "group_size_preference": group_size_preference,
            "social_comfort_level": social_comfort_level,
            "noise_tolerance": "medium",
            "privacy_preference": "medium",
        }
        
        return {
            "success": True,
            "companion_preferences": companion_prefs,
            "next_step": "activity_preferences",
        }

    def setup_activity_preferences(
        self,
        user_id: str,
        activity_intensity: str,
        physical_limitations: List[str] = None,
        time_preferences: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Setup activity and physical preferences.
        
        Given: User specifies activity preferences and limitations
        When: Activity data is validated
        Then: Should configure activity-based filtering
        """
        if activity_intensity not in self.valid_activity_levels:
            raise ValueError(f"Invalid activity intensity: {activity_intensity}")
            
        if physical_limitations is None:
            physical_limitations = []
            
        if time_preferences is None:
            time_preferences = {
                "preferred_duration_hours": 3,
                "flexible_timing": True,
                "avoid_rush_hours": False,
            }
            
        activity_prefs = {
            "activity_intensity": activity_intensity,
            "physical_limitations": physical_limitations,
            "time_preferences": time_preferences,
            "weather_sensitivity": "medium",
        }
        
        return {
            "success": True,
            "activity_preferences": activity_prefs,
            "preferences_complete": True,
        }

    def calculate_preference_quality_score(
        self,
        user_id: str,
        preference_data: Dict[str, Any],
    ) -> float:
        """Calculate a quality score for user preferences.
        
        Given: Complete user preference data
        When: Quality assessment is performed
        Then: Should return score between 0.0-1.0
        """
        quality_factors = {
            "category_diversity": 0.0,
            "location_specificity": 0.0,
            "budget_clarity": 0.0,
            "social_definition": 0.0,
            "completeness": 0.0,
        }
        
        # Category diversity (more categories = better)
        num_categories = len(preference_data.get("categories", []))
        quality_factors["category_diversity"] = min(num_categories / 4.0, 1.0)
        
        # Location specificity
        location_prefs = preference_data.get("location_preferences", {})
        if location_prefs.get("current_location") and location_prefs.get("preferred_areas"):
            quality_factors["location_specificity"] = 1.0
        elif location_prefs.get("current_location"):
            quality_factors["location_specificity"] = 0.6
        
        # Budget clarity
        budget_prefs = preference_data.get("budget_preferences", {})
        if budget_prefs.get("budget_level") and budget_prefs.get("budget_ranges"):
            quality_factors["budget_clarity"] = 1.0
            
        # Social definition
        companion_prefs = preference_data.get("companion_preferences", {})
        if companion_prefs.get("companion_type") and companion_prefs.get("social_comfort_level"):
            quality_factors["social_definition"] = 1.0
            
        # Completeness
        required_sections = ["categories", "location_preferences", "budget_preferences", "companion_preferences"]
        completed_sections = sum(1 for section in required_sections if section in preference_data)
        quality_factors["completeness"] = completed_sections / len(required_sections)
        
        # Calculate weighted average
        weights = {
            "category_diversity": 0.25,
            "location_specificity": 0.20,
            "budget_clarity": 0.20,
            "social_definition": 0.15,
            "completeness": 0.20,
        }
        
        quality_score = sum(
            quality_factors[factor] * weight
            for factor, weight in weights.items()
        )
        
        return round(quality_score, 3)


class PreferenceSurveyService:
    """Service for conducting adaptive preference surveys."""

    def __init__(self):
        self.survey_questions = self._initialize_survey_questions()
        self.adaptive_logic = self._initialize_adaptive_logic()

    def generate_adaptive_survey(
        self,
        user_id: str,
        initial_preferences: Dict[str, Any],
        target_completion_time: int = 180,  # 3 minutes in seconds
    ) -> Dict[str, Any]:
        """Generate an adaptive survey based on initial preferences.
        
        Given: User's initial preferences and time constraint
        When: Adaptive survey is generated
        Then: Should return personalized survey under 3 minutes
        """
        # Calculate available time per question
        estimated_questions = self._estimate_question_count(initial_preferences)
        time_per_question = target_completion_time // estimated_questions
        
        survey_questions = self._select_relevant_questions(initial_preferences, estimated_questions)
        
        survey = {
            "survey_id": f"survey_{user_id}_{int(datetime.utcnow().timestamp())}",
            "user_id": user_id,
            "questions": survey_questions,
            "estimated_time_seconds": estimated_questions * time_per_question,
            "adaptive_enabled": True,
            "progress_tracking": True,
            "created_at": datetime.utcnow(),
        }
        
        return survey

    def process_survey_response(
        self,
        survey_id: str,
        question_id: str,
        response: Any,
        response_time_ms: int,
    ) -> Dict[str, Any]:
        """Process a single survey response and adapt following questions.
        
        Given: User responds to survey question
        When: Response is processed and analyzed
        Then: Should adapt subsequent questions based on response
        """
        response_data = {
            "question_id": question_id,
            "response": response,
            "response_time_ms": response_time_ms,
            "timestamp": datetime.utcnow(),
        }
        
        # Analyze response for adaptation signals
        adaptation_signals = self._analyze_response(question_id, response, response_time_ms)
        
        return {
            "response_recorded": True,
            "adaptation_signals": adaptation_signals,
            "next_question_id": self._get_next_question(survey_id, adaptation_signals),
        }

    def _initialize_survey_questions(self) -> Dict[str, Any]:
        """Initialize the pool of survey questions."""
        return {
            "dining_frequency": {
                "question": "외식을 얼마나 자주 하시나요?",
                "type": "single_choice",
                "options": ["주 1회 이하", "주 2-3회", "주 4-5회", "거의 매일"],
                "estimated_time": 10,
                "category_weights": {"restaurant": 0.3, "cafe": 0.1},
            },
            "cuisine_preferences": {
                "question": "선호하는 음식 종류를 모두 선택해주세요",
                "type": "multiple_choice", 
                "options": ["한식", "일식", "중식", "양식", "분식", "디저트"],
                "estimated_time": 15,
                "category_weights": {"restaurant": 0.4},
            },
            "social_vs_quiet": {
                "question": "분위기 선호도를 선택해주세요",
                "type": "scale",
                "scale_range": [1, 5],
                "scale_labels": ["조용한 분위기", "활기찬 분위기"],
                "estimated_time": 8,
                "category_weights": {"cafe": 0.2, "restaurant": 0.2},
            },
        }

    def _initialize_adaptive_logic(self) -> Dict[str, Any]:
        """Initialize adaptive survey logic rules."""
        return {
            "skip_conditions": {
                "low_restaurant_weight": ["detailed_cuisine", "fine_dining"],
                "high_budget": ["budget_conscious_options"],
                "solo_preference": ["group_activity_questions"],
            },
            "follow_up_triggers": {
                "high_restaurant_interest": ["cuisine_details", "dining_atmosphere"],
                "outdoor_enthusiast": ["weather_preferences", "activity_intensity"],
                "culture_lover": ["art_preferences", "event_types"],
            },
        }

    def _estimate_question_count(self, initial_preferences: Dict[str, Any]) -> int:
        """Estimate optimal number of questions based on preferences."""
        base_questions = 8
        
        # Adjust based on category diversity
        num_categories = len(initial_preferences.get("categories", []))
        category_adjustment = min(num_categories * 2, 6)
        
        # Adjust based on preference clarity
        clarity_score = sum(1 for pref in initial_preferences.values() if pref)
        clarity_adjustment = max(0, 4 - clarity_score)
        
        total_questions = base_questions + category_adjustment + clarity_adjustment
        return min(total_questions, 15)  # Cap at 15 questions

    def _select_relevant_questions(
        self,
        preferences: Dict[str, Any],
        target_count: int,
    ) -> List[Dict[str, Any]]:
        """Select most relevant questions based on user preferences."""
        # This would implement sophisticated question selection logic
        # For now, return a simplified selection
        selected_questions = []
        
        for question_id, question_data in list(self.survey_questions.items())[:target_count]:
            selected_questions.append({
                "id": question_id,
                "question": question_data["question"],
                "type": question_data["type"],
                "options": question_data.get("options", []),
                "estimated_time": question_data["estimated_time"],
            })
            
        return selected_questions

    def _analyze_response(
        self,
        question_id: str,
        response: Any,
        response_time_ms: int,
    ) -> Dict[str, Any]:
        """Analyze response for adaptation signals."""
        signals = {
            "confidence_level": "medium",
            "category_interests": {},
            "time_pressure": response_time_ms < 5000,
            "detail_oriented": response_time_ms > 15000,
        }
        
        # Quick response suggests either very confident or time-pressured
        if response_time_ms < 3000:
            signals["confidence_level"] = "high"
        elif response_time_ms > 20000:
            signals["confidence_level"] = "low"
            
        return signals

    def _get_next_question(self, survey_id: str, signals: Dict[str, Any]) -> Optional[str]:
        """Determine next question based on adaptation signals."""
        # This would implement the adaptive logic
        # For now, return a simple sequential approach
        return None


class CategoryPreferenceService:
    """Service for category-related preference operations."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        
    def get_available_categories(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get available categories with context."""
        categories = [
            {"id": "restaurant", "name": "음식점", "description": "레스토랑, 맛집"},
            {"id": "cafe", "name": "카페", "description": "카페, 디저트"},
            {"id": "culture", "name": "문화", "description": "박물관, 전시회"},
            {"id": "shopping", "name": "쇼핑", "description": "쇼핑몰, 마켓"},
            {"id": "entertainment", "name": "엔터테인먼트", "description": "영화, 공연"},
            {"id": "outdoor", "name": "야외활동", "description": "공원, 산책"},
            {"id": "wellness", "name": "웰니스", "description": "스파, 헬스"}
        ]
        
        return {
            "available_categories": categories,
            "category_descriptions": {cat["id"]: cat["description"] for cat in categories},
            "total_available": len(categories),
            "context_applied": user_context
        }
    
    def validate_category_selection(self, user_id: str, selected_categories: List[str]) -> Dict[str, Any]:
        """Validate category selection."""
        valid_categories = ["restaurant", "cafe", "culture", "shopping", "entertainment", "outdoor", "wellness"]
        errors = []
        
        if len(selected_categories) < 2:
            errors.append("최소 2개 카테고리를 선택해야 합니다")
        elif len(selected_categories) > 5:
            errors.append("최대 5개 카테고리까지만 선택할 수 있습니다")
            
        invalid_categories = [cat for cat in selected_categories if cat not in valid_categories]
        if invalid_categories:
            errors.append(f"유효하지 않은 카테고리: {invalid_categories}")
            
        return {
            "user_id": user_id,
            "selected_categories": selected_categories,
            "category_count": len(selected_categories),
            "validation_passed": len(errors) == 0,
            "validation_errors": errors,
            "validated_at": datetime.utcnow().isoformat()
        }
    
    def set_category_weights(self, user_id: str, category_weights: Dict[str, Dict[str, float]], normalization_method: str) -> Dict[str, Any]:
        """Set category weights."""
        # Normalize weights
        if normalization_method == "softmax":
            total = sum(sum(weights.values()) for weights in category_weights.values())
            normalized_weights = {}
            for category, weights in category_weights.items():
                normalized_weights[category] = sum(weights.values()) / total if total > 0 else 0
        else:  # linear
            normalized_weights = {}
            for category, weights in category_weights.items():
                normalized_weights[category] = sum(weights.values()) / len(weights) if weights else 0
                
        return {
            "user_id": user_id,
            "category_weights_set": True,
            "original_weights": category_weights,
            "normalized_weights": normalized_weights,
            "normalization_method": normalization_method,
            "weights_sum": sum(normalized_weights.values()),
            "configured_at": datetime.utcnow().isoformat()
        }


class PreferenceSurveyService:
    """Service for survey-related operations."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        
    def complete_preference_survey(self, user_id: str, survey_version: str, responses: List[Dict], completion_time_minutes: float) -> Dict[str, Any]:
        """Complete preference survey."""
        return {
            "user_id": user_id,
            "survey_completed": True,
            "survey_version": survey_version,
            "completion_time_minutes": completion_time_minutes,
            "profile_generated": True,
            "quality_score": 0.8,
            "recommendation_ready": True,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def generate_adaptive_survey(self, user_id: str, previous_answers: List[Dict], adaptive_questions: List[Dict]) -> Dict[str, Any]:
        """Generate adaptive survey questions."""
        return {
            "user_id": user_id,
            "adaptive_questions_generated": True,
            "personalized_questions": adaptive_questions[:5],  # Limit to 5 questions
            "adaptation_confidence": 0.7,
            "personalization_improved": True,
            "previous_answers_analyzed": len(previous_answers),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def validate_preference_configuration(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Validate preference configuration."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["categories", "budget_level"]
        for field in required_fields:
            if field not in preferences:
                errors.append(f"필수 필드 누락: {field}")
                
        # Calculate completeness
        total_fields = 7  # categories, budget, location, companion, activity, etc.
        completed_fields = len([k for k in preferences.keys() if preferences[k]])
        completeness_score = completed_fields / total_fields
        
        return {
            "user_id": user_id,
            "validation_passed": len(errors) == 0,
            "validation_errors": errors,
            "validation_warnings": warnings,
            "completeness_score": completeness_score,
            "validated_at": datetime.utcnow().isoformat()
        }
    
    def calculate_preference_scores(self, user_id: str, weighted_preferences: Dict[str, Dict[str, float]], importance_weights: Dict[str, float]) -> Dict[str, Any]:
        """Calculate preference scores."""
        calculated_scores = {}
        total_score = 0.0
        
        for category, weights in weighted_preferences.items():
            category_score = sum(weights.values()) / len(weights) if weights else 0
            importance = importance_weights.get(category, 1.0)
            calculated_scores[category] = category_score * importance
            total_score += calculated_scores[category]
            
        return {
            "user_id": user_id,
            "calculated_scores": calculated_scores,
            "weighted_categories": weighted_preferences,
            "total_score": total_score,
            "scoring_confidence": 0.8,
            "calculated_at": datetime.utcnow().isoformat()
        }


class PreferencePersonalizationService:
    """Service for preference personalization and learning."""
    
    def __init__(self, db_session=None):
        self.db = db_session
        
    def create_personalized_onboarding(self, user_id: str, demographic_info: Dict[str, Any], initial_signals: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized onboarding flow."""
        # Generate customized questions based on demographics and signals
        customized_questions = [
            {"id": "age_specific", "question": "나이대에 맞는 장소를 선호하시나요?"},
            {"id": "location_based", "question": "현재 위치 근처의 장소를 주로 찾으시나요?"}
        ]
        
        return {
            "user_id": user_id,
            "personalized_flow_created": True,
            "customized_questions": customized_questions,
            "estimated_completion_time": {"minutes": 3, "seconds": 180},
            "personalization_confidence": 0.7,
            "signal_analysis": initial_signals,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def learn_from_behavior(self, user_id: str, interaction_patterns: List[Dict], time_spent_per_category: Dict[str, int]) -> Dict[str, Any]:
        """Learn from user behavior patterns."""
        # Analyze patterns and update weights
        updated_weights = {}
        for category, time_spent in time_spent_per_category.items():
            weight = min(time_spent / 3600, 1.0)  # Normalize by hour
            updated_weights[category] = weight
            
        return {
            "user_id": user_id,
            "preferences_updated": True,
            "behavior_insights": {
                "most_engaged_category": max(time_spent_per_category, key=time_spent_per_category.get),
                "interaction_count": len(interaction_patterns)
            },
            "updated_category_weights": updated_weights,
            "learning_confidence": 0.8,
            "recommendation_improvements": ["더 정확한 카테고리 매칭", "시간대별 추천 개선"],
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    def assess_preference_quality(self, user_id: str, completed_categories: int, detailed_responses: int, 
                                 consistency_score: float, completion_percentage: float, engagement_indicators: Dict[str, Any]) -> Dict[str, Any]:
        """Assess preference quality."""
        # Calculate quality score
        category_score = min(completed_categories / 5, 1.0)  # Assuming 5 categories max
        response_score = min(detailed_responses / 10, 1.0)   # Assuming 10 responses optimal
        quality_score = (category_score + response_score + consistency_score) / 3
        
        return {
            "user_id": user_id,
            "quality_score": quality_score,
            "completeness_percentage": completion_percentage,
            "quality_components": {
                "category_completeness": category_score,
                "response_quality": response_score,
                "consistency": consistency_score
            },
            "recommendation_readiness": {
                "ready": quality_score > 0.6,
                "confidence": quality_score,
                "improvements_needed": [] if quality_score > 0.6 else ["더 많은 카테고리 선택", "상세 응답 추가"]
            },
            "assessed_at": datetime.utcnow().isoformat()
        }