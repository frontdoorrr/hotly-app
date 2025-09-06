"""Onboarding flow state management and user preference collection service."""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Onboarding step enumeration."""

    PERMISSIONS = 1
    PREFERENCES = 2
    LOCATION_SETUP = 3
    SAMPLE_EXPLORATION = 4
    FIRST_COURSE = 5


class OnboardingStatus(Enum):
    """Onboarding status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    EXPIRED = "expired"


class OnboardingService:
    """Service for managing onboarding flow and user progression."""

    def __init__(self, db: Session):
        self.db = db
        self.onboarding_sessions = {}  # In-memory storage for onboarding state
        self.timeout_minutes = 15  # Onboarding session timeout

    def start_onboarding_flow(
        self,
        user_id: str,
        device_info: Dict[str, Any],
        referral_source: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Initialize onboarding flow for new user.

        Args:
            user_id: User identifier
            device_info: Device and platform information
            referral_source: How user found the app

        Returns:
            Onboarding session initialization data
        """
        try:
            onboarding_id = f"onboarding_{uuid4()}"

            # Create onboarding session
            session_data = {
                "onboarding_id": onboarding_id,
                "user_id": user_id,
                "status": OnboardingStatus.IN_PROGRESS.value,
                "current_step": OnboardingStep.PERMISSIONS.value,
                "total_steps": len(OnboardingStep),
                "progress_percentage": 0,
                "started_at": datetime.utcnow().isoformat(),
                "expires_at": (
                    datetime.utcnow() + timedelta(minutes=self.timeout_minutes)
                ).isoformat(),
                "device_info": device_info,
                "referral_source": referral_source,
                "completed_steps": [],
                "step_data": {},
            }

            # Store session
            self.onboarding_sessions[onboarding_id] = session_data

            # Prepare initial response
            onboarding_state = {
                "onboarding_id": onboarding_id,
                "current_step": session_data["current_step"],
                "total_steps": session_data["total_steps"],
                "progress_percentage": session_data["progress_percentage"],
                "step_requirements": self._get_step_requirements(
                    OnboardingStep.PERMISSIONS
                ),
                "estimated_completion_time": "3 minutes",
                "timeout_minutes": self.timeout_minutes,
            }

            logger.info(f"Onboarding started for user {user_id}: {onboarding_id}")
            return onboarding_state

        except Exception as e:
            logger.error(f"Error starting onboarding: {e}")
            raise

    def progress_to_next_step(
        self,
        onboarding_id: str,
        user_id: str,
        current_step: int,
        step_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Progress to next onboarding step.

        Args:
            onboarding_id: Onboarding session ID
            user_id: User identifier
            current_step: Current step number
            step_data: Data collected in current step

        Returns:
            Next step information and progress
        """
        try:
            # Validate session
            if onboarding_id not in self.onboarding_sessions:
                raise ValueError("Onboarding session not found")

            session = self.onboarding_sessions[onboarding_id]

            # Validate user and session
            if session["user_id"] != user_id:
                raise ValueError("Invalid user for onboarding session")

            # Check timeout
            if self._is_session_expired(session):
                session["status"] = OnboardingStatus.EXPIRED.value
                raise ValueError("Onboarding session expired")

            # Validate step progression
            if session["current_step"] != current_step:
                raise ValueError(
                    f"Step mismatch: expected {session['current_step']}, got {current_step}"
                )

            # Store step data
            session["step_data"][f"step_{current_step}"] = {
                **step_data,
                "completed_at": datetime.utcnow().isoformat(),
            }
            session["completed_steps"].append(current_step)

            # Calculate next step
            next_step_number = current_step + 1

            if next_step_number > len(OnboardingStep):
                # Onboarding completed
                session["status"] = OnboardingStatus.COMPLETED.value
                session["completed_at"] = datetime.utcnow().isoformat()

                completion_result = {
                    "onboarding_completed": True,
                    "completion_time": session["completed_at"],
                    "total_steps_completed": len(session["completed_steps"]),
                    "personalization_ready": True,
                }

                logger.info(f"Onboarding completed for user {user_id}")
                return completion_result
            else:
                # Progress to next step
                next_step = OnboardingStep(next_step_number)
                session["current_step"] = next_step_number
                session["progress_percentage"] = int(
                    (current_step / len(OnboardingStep)) * 100
                )
                session["updated_at"] = datetime.utcnow().isoformat()

                next_step_response = {
                    "current_step": next_step_number,
                    "step_name": next_step.name.lower(),
                    "progress_percentage": session["progress_percentage"],
                    "next_step_requirements": self._get_step_requirements(next_step),
                    "estimated_remaining_time": f"{len(OnboardingStep) - current_step} minutes",
                    "step_completed": current_step,
                }

                logger.info(
                    f"Onboarding progressed to step {next_step_number} for user {user_id}"
                )
                return next_step_response

        except Exception as e:
            logger.error(f"Error progressing onboarding step: {e}")
            raise

    def track_onboarding_progress(
        self,
        user_id: str,
        completed_steps: List[int],
        current_step: int,
        total_steps: int,
    ) -> Dict[str, Any]:
        """
        Track and analyze onboarding progress.

        Args:
            user_id: User identifier
            completed_steps: List of completed step numbers
            current_step: Current step number
            total_steps: Total number of steps

        Returns:
            Progress tracking information
        """
        try:
            progress_percentage = int((len(completed_steps) / total_steps) * 100)
            remaining_steps = [
                i for i in range(1, total_steps + 1) if i not in completed_steps
            ]

            # Estimate completion time
            avg_time_per_step = 36  # seconds (3 minutes / 5 steps)
            estimated_remaining_seconds = len(remaining_steps) * avg_time_per_step

            progress_data = {
                "user_id": user_id,
                "progress_percentage": progress_percentage,
                "completed_steps": completed_steps,
                "current_step": current_step,
                "remaining_steps": remaining_steps,
                "estimated_completion_minutes": round(
                    estimated_remaining_seconds / 60, 1
                ),
                "on_track_for_3min_goal": estimated_remaining_seconds
                <= 180,  # 3 minutes
                "progress_tracked_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Onboarding progress tracked: {progress_percentage}% for user {user_id}"
            )
            return progress_data

        except Exception as e:
            logger.error(f"Error tracking onboarding progress: {e}")
            raise

    def skip_onboarding_step(
        self,
        user_id: str,
        step_to_skip: int,
        skip_reason: str,
        continue_to_step: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Handle skipping of optional onboarding steps.

        Args:
            user_id: User identifier
            step_to_skip: Step number to skip
            skip_reason: Reason for skipping
            continue_to_step: Step to continue to

        Returns:
            Step skip result and progression
        """
        try:
            # Define mandatory steps that cannot be skipped
            mandatory_steps = [1, 2]  # Permissions and basic preferences

            if step_to_skip in mandatory_steps:
                raise ValueError(
                    f"Step {step_to_skip} is mandatory and cannot be skipped"
                )

            # Find user's onboarding session
            user_session = None
            for session_id, session in self.onboarding_sessions.items():
                if (
                    session["user_id"] == user_id
                    and session["status"] == OnboardingStatus.IN_PROGRESS.value
                ):
                    user_session = session
                    break

            if not user_session:
                raise ValueError("No active onboarding session found")

            # Record skip
            user_session["step_data"][f"step_{step_to_skip}"] = {
                "skipped": True,
                "skip_reason": skip_reason,
                "skipped_at": datetime.utcnow().isoformat(),
            }
            user_session["completed_steps"].append(step_to_skip)

            # Progress to next step
            target_step = continue_to_step or (step_to_skip + 1)
            user_session["current_step"] = target_step
            user_session["progress_percentage"] = int(
                (len(user_session["completed_steps"]) / len(OnboardingStep)) * 100
            )

            skip_result = {
                "step_skipped": step_to_skip,
                "skip_reason": skip_reason,
                "current_step": target_step,
                "progress_percentage": user_session["progress_percentage"],
                "skip_allowed": True,
            }

            logger.info(
                f"User {user_id} skipped step {step_to_skip}, reason: {skip_reason}"
            )
            return skip_result

        except Exception as e:
            logger.error(f"Error skipping onboarding step: {e}")
            raise

    def check_session_timeout(
        self,
        user_id: str,
        onboarding_started_at: str,
        current_time: str,
        timeout_threshold_minutes: int = 10,
    ) -> Dict[str, Any]:
        """
        Check for onboarding session timeout.

        Args:
            user_id: User identifier
            onboarding_started_at: When onboarding started
            current_time: Current timestamp
            timeout_threshold_minutes: Timeout threshold

        Returns:
            Timeout status and handling information
        """
        try:
            started_time = datetime.fromisoformat(
                onboarding_started_at.replace("Z", "+00:00")
            )
            current_time_dt = datetime.fromisoformat(
                current_time.replace("Z", "+00:00")
            )

            time_elapsed = (
                current_time_dt - started_time
            ).total_seconds() / 60  # minutes
            is_timeout = time_elapsed > timeout_threshold_minutes

            if is_timeout:
                # Handle timeout
                timeout_result = {
                    "session_timed_out": True,
                    "time_elapsed_minutes": round(time_elapsed, 1),
                    "timeout_threshold": timeout_threshold_minutes,
                    "action_required": "restart_onboarding",
                    "timeout_handled_at": datetime.utcnow().isoformat(),
                }

                # Mark sessions as expired for this user
                for session in self.onboarding_sessions.values():
                    if (
                        session["user_id"] == user_id
                        and session["status"] == OnboardingStatus.IN_PROGRESS.value
                    ):
                        session["status"] = OnboardingStatus.EXPIRED.value
                        session["timeout_at"] = datetime.utcnow().isoformat()

                logger.warning(
                    f"Onboarding timeout for user {user_id} after {time_elapsed:.1f} minutes"
                )
                return timeout_result
            else:
                # Still active
                active_result = {
                    "session_timed_out": False,
                    "time_elapsed_minutes": round(time_elapsed, 1),
                    "remaining_minutes": timeout_threshold_minutes - time_elapsed,
                    "session_active": True,
                    "checked_at": datetime.utcnow().isoformat(),
                }

                return active_result

        except Exception as e:
            logger.error(f"Error checking session timeout: {e}")
            raise

    def _get_step_requirements(self, step: OnboardingStep) -> Dict[str, Any]:
        """Get requirements for specific onboarding step."""
        step_requirements = {
            OnboardingStep.PERMISSIONS: {
                "required_permissions": ["location", "notifications"],
                "optional_permissions": ["contacts", "camera"],
                "step_description": "앱 사용을 위한 기본 권한을 설정해주세요",
                "estimated_time_seconds": 30,
            },
            OnboardingStep.PREFERENCES: {
                "required_selections": ["categories", "budget_level"],
                "optional_selections": ["activity_level", "group_size"],
                "min_categories": 2,
                "max_categories": 5,
                "step_description": "관심 있는 장소 유형을 선택해주세요",
                "estimated_time_seconds": 60,
            },
            OnboardingStep.LOCATION_SETUP: {
                "required_data": ["current_location"],
                "optional_data": ["home_address", "work_address"],
                "location_accuracy_required": "city_level",
                "step_description": "현재 위치를 설정하여 맞춤 추천을 받으세요",
                "estimated_time_seconds": 30,
            },
            OnboardingStep.SAMPLE_EXPLORATION: {
                "sample_count": 3,
                "interaction_required": "view_at_least_one",
                "sample_types": ["popular_local", "category_matched", "trending"],
                "step_description": "주변 인기 장소를 둘러보세요",
                "estimated_time_seconds": 90,
            },
            OnboardingStep.FIRST_COURSE: {
                "min_places": 2,
                "creation_assistance": True,
                "template_provided": True,
                "step_description": "첫 번째 코스를 만들어보세요",
                "estimated_time_seconds": 120,
            },
        }

        return step_requirements.get(step, {})

    def _is_session_expired(self, session: Dict[str, Any]) -> bool:
        """Check if onboarding session has expired."""
        expires_at = datetime.fromisoformat(session["expires_at"])
        return datetime.utcnow() > expires_at


class UserPreferenceService:
    """Service for collecting and managing user preferences during onboarding."""

    def __init__(self, db: Session):
        self.db = db
        self.user_preferences = {}  # In-memory storage for user preferences

    def set_user_preferences(
        self,
        user_id: str,
        selected_categories: List[str],
        activity_level: str = "moderate",
        budget_range: str = "medium",
        group_size_preference: str = "couple",
    ) -> Dict[str, Any]:
        """
        Set user preferences during onboarding.

        Args:
            user_id: User identifier
            selected_categories: Selected place categories
            activity_level: Activity intensity preference
            budget_range: Budget preference level
            group_size_preference: Preferred group size

        Returns:
            Preference configuration result
        """
        try:
            # Validate categories
            valid_categories = [
                "restaurant",
                "cafe",
                "shopping",
                "entertainment",
                "culture",
                "outdoor",
                "wellness",
            ]
            invalid_categories = [
                cat for cat in selected_categories if cat not in valid_categories
            ]

            if invalid_categories:
                raise ValueError(f"Invalid categories: {invalid_categories}")

            if len(selected_categories) < 2 or len(selected_categories) > 5:
                raise ValueError("Must select 2-5 categories")

            # Validate other preferences
            valid_activity_levels = ["low", "moderate", "high"]
            valid_budget_ranges = ["low", "medium", "high"]
            valid_group_sizes = ["solo", "couple", "group"]

            if activity_level not in valid_activity_levels:
                raise ValueError(f"Invalid activity level: {activity_level}")
            if budget_range not in valid_budget_ranges:
                raise ValueError(f"Invalid budget range: {budget_range}")
            if group_size_preference not in valid_group_sizes:
                raise ValueError(f"Invalid group size: {group_size_preference}")

            # Create preference profile
            preference_profile = {
                "user_id": user_id,
                "categories": selected_categories,
                "activity_level": activity_level,
                "budget_range": budget_range,
                "group_size_preference": group_size_preference,
                "preference_weights": self._calculate_preference_weights(
                    selected_categories
                ),
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": datetime.utcnow().isoformat(),
                "preference_version": "1.0",
            }

            # Store preferences
            self.user_preferences[user_id] = preference_profile

            result = {
                "preferences_saved": True,
                "category_count": len(selected_categories),
                "preference_profile_id": f"profile_{user_id}",
                "personalization_enabled": True,
                "configured_at": preference_profile["created_at"],
            }

            logger.info(f"Preferences set for user {user_id}: {selected_categories}")
            return result

        except Exception as e:
            logger.error(f"Error setting user preferences: {e}")
            raise

    def configure_location_preferences(
        self,
        user_id: str,
        home_location: Dict[str, Any],
        work_location: Optional[Dict[str, Any]] = None,
        preferred_radius_km: float = 15.0,
        transportation_modes: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Configure location-based preferences.

        Args:
            user_id: User identifier
            home_location: Home location coordinates and address
            work_location: Optional work location
            preferred_radius_km: Preferred activity radius
            transportation_modes: Preferred transportation methods

        Returns:
            Location preference configuration result
        """
        try:
            # Validate home location
            required_fields = ["latitude", "longitude", "address"]
            for field in required_fields:
                if field not in home_location:
                    raise ValueError(f"Home location missing {field}")

            # Validate coordinates
            lat, lng = home_location["latitude"], home_location["longitude"]
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError("Invalid home location coordinates")

            # Default transportation modes
            if transportation_modes is None:
                transportation_modes = ["walking", "transit"]

            valid_transport_modes = ["walking", "bicycling", "transit", "driving"]
            invalid_modes = [
                mode
                for mode in transportation_modes
                if mode not in valid_transport_modes
            ]
            if invalid_modes:
                raise ValueError(f"Invalid transportation modes: {invalid_modes}")

            # Create location preferences
            location_preferences = {
                "user_id": user_id,
                "home_location": home_location,
                "work_location": work_location,
                "preferred_radius_km": preferred_radius_km,
                "transportation_modes": transportation_modes,
                "location_based_filtering": True,
                "configured_at": datetime.utcnow().isoformat(),
            }

            # Store or update user preferences
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}

            self.user_preferences[user_id][
                "location_preferences"
            ] = location_preferences

            result = {
                "home_location_set": True,
                "work_location_set": work_location is not None,
                "activity_radius_configured": True,
                "radius_km": preferred_radius_km,
                "transportation_modes_count": len(transportation_modes),
                "location_based_recommendations_enabled": True,
            }

            logger.info(f"Location preferences configured for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error configuring location preferences: {e}")
            raise

    def _calculate_preference_weights(self, categories: List[str]) -> Dict[str, float]:
        """Calculate preference weights for recommendation algorithms."""
        # Equal weight distribution for selected categories
        weight_per_category = 1.0 / len(categories)

        weights = {}
        for category in categories:
            weights[category] = weight_per_category

        return weights


class OnboardingSampleService:
    """Service for providing sample places and guides during onboarding."""

    def __init__(self, db: Session):
        self.db = db

    def generate_sample_places(
        self,
        user_id: str,
        user_location: Dict[str, float],
        selected_categories: List[str],
        sample_count: int = 3,
    ) -> Dict[str, Any]:
        """
        Generate sample places for onboarding exploration.

        Args:
            user_id: User identifier
            user_location: User's current location
            selected_categories: User's selected categories
            sample_count: Number of samples to generate

        Returns:
            Sample places for onboarding exploration
        """
        try:
            # Generate diverse samples based on user preferences
            sample_places = []

            for i in range(sample_count):
                category = selected_categories[i % len(selected_categories)]

                # Mock sample place generation
                sample_place = {
                    "sample_id": f"sample_{category}_{i}",
                    "place_name": f"추천 {category} #{i+1}",
                    "category": category,
                    "latitude": user_location["latitude"] + (i * 0.001),
                    "longitude": user_location["longitude"] + (i * 0.001),
                    "distance_km": 0.5 + (i * 0.3),
                    "rating": 4.2 + (i * 0.1),
                    "why_recommended": f"{category} 카테고리 관심사 기반 추천",
                    "sample_type": "category_matched" if i < 2 else "popular_local",
                    "interaction_encouragement": "탭해서 자세한 정보를 확인해보세요!",
                }

                sample_places.append(sample_place)

            sample_result = {
                "sample_places": sample_places,
                "sample_count": len(sample_places),
                "user_location": user_location,
                "categories_represented": list(
                    set([p["category"] for p in sample_places])
                ),
                "sample_generated_at": datetime.utcnow().isoformat(),
                "personalization_applied": True,
            }

            logger.info(f"Generated {sample_count} sample places for user {user_id}")
            return sample_result

        except Exception as e:
            logger.error(f"Error generating sample places: {e}")
            raise

    def process_sample_feedback(
        self, user_id: str, sample_interactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process user feedback on sample places to refine preferences.

        Args:
            user_id: User identifier
            sample_interactions: List of user interactions with samples

        Returns:
            Processed feedback and preference refinements
        """
        try:
            # Analyze interaction patterns
            interaction_analysis = {
                "total_interactions": len(sample_interactions),
                "positive_interactions": 0,
                "negative_interactions": 0,
                "saved_samples": 0,
                "category_feedback": {},
            }

            for interaction in sample_interactions:
                action = interaction.get("action", "")
                interaction.get("reason", "")

                if action in ["liked", "saved"]:
                    interaction_analysis["positive_interactions"] += 1
                    if action == "saved":
                        interaction_analysis["saved_samples"] += 1
                elif action in ["disliked", "skipped"]:
                    interaction_analysis["negative_interactions"] += 1

                # Track category-specific feedback
                sample_category = interaction.get("sample_category", "unknown")
                if sample_category not in interaction_analysis["category_feedback"]:
                    interaction_analysis["category_feedback"][sample_category] = {
                        "positive": 0,
                        "negative": 0,
                    }

                if action in ["liked", "saved"]:
                    interaction_analysis["category_feedback"][sample_category][
                        "positive"
                    ] += 1
                elif action in ["disliked", "skipped"]:
                    interaction_analysis["category_feedback"][sample_category][
                        "negative"
                    ] += 1

            # Generate preference refinements
            refinements = []
            for category, feedback in interaction_analysis["category_feedback"].items():
                total_feedback = feedback["positive"] + feedback["negative"]
                if total_feedback > 0:
                    positivity_ratio = feedback["positive"] / total_feedback

                    if positivity_ratio >= 0.7:
                        refinements.append(
                            {
                                "category": category,
                                "adjustment": "increase_weight",
                                "confidence": positivity_ratio,
                            }
                        )
                    elif positivity_ratio <= 0.3:
                        refinements.append(
                            {
                                "category": category,
                                "adjustment": "decrease_weight",
                                "confidence": 1 - positivity_ratio,
                            }
                        )

            feedback_result = {
                "feedback_processed": True,
                "interaction_summary": interaction_analysis,
                "preference_refinement": refinements,
                "learning_applied": len(refinements) > 0,
                "next_recommendations_improved": True,
                "processed_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Processed sample feedback for user {user_id}: {len(refinements)} refinements"
            )
            return feedback_result

        except Exception as e:
            logger.error(f"Error processing sample feedback: {e}")
            raise

    def provide_onboarding_guidance(
        self,
        user_id: str,
        current_step: int,
        user_action: str,
        help_needed: bool = False,
    ) -> Dict[str, Any]:
        """
        Provide contextual guidance during onboarding.

        Args:
            user_id: User identifier
            current_step: Current onboarding step
            user_action: User's current action or state
            help_needed: Whether user explicitly requested help

        Returns:
            Contextual guidance and next actions
        """
        try:
            step_guidance = {
                1: {
                    "guidance_text": "권한 설정을 통해 더 정확한 맞춤 추천을 받을 수 있어요",
                    "next_actions": ["위치 권한 허용", "알림 권한 허용", "다음 단계로 진행"],
                    "help_tips": ["권한은 나중에 설정에서 변경 가능합니다", "위치 권한으로 주변 장소 추천이 정확해집니다"],
                },
                2: {
                    "guidance_text": "관심 있는 장소 유형을 선택하면 맞춤 추천을 받을 수 있어요",
                    "next_actions": ["카테고리 2-5개 선택", "예산 범위 설정", "활동 수준 선택"],
                    "help_tips": ["나중에 설정에서 언제든 변경 가능합니다", "선택한 카테고리는 추천 정확도에 영향을 줍니다"],
                },
                3: {
                    "guidance_text": "현재 위치 설정으로 주변 장소를 추천받으세요",
                    "next_actions": ["현재 위치 허용", "홈/직장 위치 설정 (선택사항)"],
                    "help_tips": ["위치 정보는 추천에만 사용됩니다", "정확한 위치일수록 좋은 추천을 받을 수 있어요"],
                },
                4: {
                    "guidance_text": "추천된 샘플 장소들을 둘러보고 마음에 드는 곳을 저장해보세요",
                    "next_actions": ["샘플 장소 탐색", "관심 있는 곳 저장", "피드백 제공"],
                    "help_tips": [
                        "탭하면 장소 상세 정보를 볼 수 있어요",
                        "저장한 장소는 나중에 코스에 추가할 수 있습니다",
                    ],
                },
                5: {
                    "guidance_text": "이제 첫 번째 코스를 만들어보세요!",
                    "next_actions": ["저장된 장소 선택", "코스 순서 정하기", "코스 이름 정하기"],
                    "help_tips": ["최소 2개 장소로 코스를 만들 수 있어요", "나중에 언제든 수정 가능합니다"],
                },
            }

            current_guidance = step_guidance.get(current_step, {})

            # Customize guidance based on user action
            if user_action == "confused":
                current_guidance["additional_help"] = "차근차근 따라해보시면 쉽게 완료할 수 있어요"
            elif user_action == "impatient":
                current_guidance["quick_path"] = "핵심 설정만 하고 나중에 상세 설정하실 수 있어요"

            guidance_result = {
                "current_step": current_step,
                "guidance_text": current_guidance.get("guidance_text", "다음 단계로 진행해주세요"),
                "next_actions": current_guidance.get("next_actions", []),
                "help_tips": current_guidance.get("help_tips", []),
                "user_action": user_action,
                "help_provided": help_needed,
                "guidance_generated_at": datetime.utcnow().isoformat(),
            }

            if help_needed:
                guidance_result.update(current_guidance)

            logger.info(f"Guidance provided for user {user_id} at step {current_step}")
            return guidance_result

        except Exception as e:
            logger.error(f"Error providing onboarding guidance: {e}")
            raise

    def set_budget_preferences(
        self,
        user_id: str,
        budget_level: str,
        budget_range: Dict[str, Any],
        budget_flexibility: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Set user budget preferences for personalized recommendations.

        Args:
            user_id: User identifier
            budget_level: Budget level (low, medium, high)
            budget_range: Specific budget range with min/max
            budget_flexibility: Flexibility in budget adherence

        Returns:
            Budget preference configuration result
        """
        try:
            # Validate budget data
            if (
                "min_per_place" not in budget_range
                or "max_per_place" not in budget_range
            ):
                raise ValueError(
                    "Budget range must include min_per_place and max_per_place"
                )

            if budget_range["min_per_place"] >= budget_range["max_per_place"]:
                raise ValueError("Minimum budget must be less than maximum budget")

            budget_preferences = {
                "user_id": user_id,
                "budget_level": budget_level,
                "budget_range": budget_range,
                "budget_flexibility": budget_flexibility,
                "price_filtering_enabled": True,
                "budget_alerts_enabled": budget_flexibility != "flexible",
                "configured_at": datetime.utcnow().isoformat(),
            }

            # Store budget preferences
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}

            self.user_preferences[user_id]["budget_preferences"] = budget_preferences

            result = {
                "budget_configured": True,
                "price_filtering_enabled": True,
                "budget_level": budget_level,
                "budget_range_krw": budget_range,
                "flexibility": budget_flexibility,
            }

            logger.info(f"Budget preferences set for user {user_id}: {budget_level}")
            return result

        except Exception as e:
            logger.error(f"Error setting budget preferences: {e}")
            raise

    def configure_social_preferences(
        self,
        user_id: str,
        sharing_comfort: str,
        discovery_preferences: str,
        interaction_level: str,
        privacy_settings: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Configure social interaction and privacy preferences.

        Args:
            user_id: User identifier
            sharing_comfort: Comfort level with sharing (private, friends_only, public)
            discovery_preferences: Content discovery preferences
            interaction_level: Social interaction activity level
            privacy_settings: Detailed privacy configuration

        Returns:
            Social preference configuration result
        """
        try:
            # Validate social preference options
            valid_sharing_levels = ["private", "friends_only", "public"]
            valid_discovery_levels = ["closed", "curated", "open"]
            valid_interaction_levels = ["passive", "moderate", "active"]

            if sharing_comfort not in valid_sharing_levels:
                raise ValueError(f"Invalid sharing comfort: {sharing_comfort}")
            if discovery_preferences not in valid_discovery_levels:
                raise ValueError(
                    f"Invalid discovery preference: {discovery_preferences}"
                )
            if interaction_level not in valid_interaction_levels:
                raise ValueError(f"Invalid interaction level: {interaction_level}")

            social_preferences = {
                "user_id": user_id,
                "sharing_comfort": sharing_comfort,
                "discovery_preferences": discovery_preferences,
                "interaction_level": interaction_level,
                "privacy_settings": privacy_settings,
                "social_features_enabled": interaction_level != "passive",
                "content_discovery_enabled": discovery_preferences != "closed",
                "configured_at": datetime.utcnow().isoformat(),
            }

            # Store social preferences
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}

            self.user_preferences[user_id]["social_preferences"] = social_preferences

            result = {
                "social_preferences_configured": True,
                "sharing_level": sharing_comfort,
                "discovery_enabled": discovery_preferences != "closed",
                "privacy_settings_applied": len(privacy_settings),
                "social_features_active": social_preferences["social_features_enabled"],
            }

            logger.info(f"Social preferences configured for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error configuring social preferences: {e}")
            raise


class OnboardingAnalyticsService:
    """Service for onboarding analytics and optimization."""

    def __init__(self):
        self.analytics_data = {}

    def track_completion_analytics(
        self, time_period: str = "30_days", segment: str = "new_users"
    ) -> Dict[str, Any]:
        """
        Track onboarding completion analytics.

        Args:
            time_period: Analysis time period
            segment: User segment to analyze

        Returns:
            Onboarding completion analytics
        """
        try:
            # Mock analytics data for development
            mock_analytics = {
                "completion_rate": 0.72,  # 72% completion rate (above 70% goal)
                "average_completion_time_minutes": 2.8,  # Under 3 minute goal
                "step_analytics": {
                    "step_1_completion": 0.95,
                    "step_2_completion": 0.88,
                    "step_3_completion": 0.82,
                    "step_4_completion": 0.79,
                    "step_5_completion": 0.72,
                },
                "drop_off_points": [
                    {
                        "step": 2,
                        "drop_off_rate": 0.12,
                        "primary_reason": "too_many_options",
                    },
                    {
                        "step": 4,
                        "drop_off_rate": 0.08,
                        "primary_reason": "sample_not_relevant",
                    },
                ],
                "time_period": time_period,
                "segment": segment,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Onboarding analytics generated for {time_period}, {segment}")
            return mock_analytics

        except Exception as e:
            logger.error(f"Error tracking completion analytics: {e}")
            raise

    def predict_user_dropoff(
        self, user_id: str, onboarding_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict likelihood of user dropping off during onboarding.

        Args:
            user_id: User identifier
            onboarding_session: Current session behavior data

        Returns:
            Drop-off risk assessment and intervention recommendations
        """
        try:
            behavior = onboarding_session

            # Calculate risk factors
            time_spent = behavior.get("time_spent_per_step", [])
            interaction_patterns = behavior.get("interaction_patterns", [])
            help_requests = behavior.get("help_requests", 0)
            step_retries = behavior.get("step_retries", 0)

            # Risk scoring algorithm
            risk_score = 0.0

            # Time-based risk
            if time_spent:
                avg_time = sum(time_spent) / len(time_spent)
                if avg_time > 120:  # More than 2 minutes per step
                    risk_score += 0.3
                elif avg_time < 30:  # Less than 30 seconds (too rushed)
                    risk_score += 0.2

            # Interaction pattern risk
            struggle_patterns = ["hesitant", "struggling", "confused"]
            struggle_count = sum(
                1 for pattern in interaction_patterns if pattern in struggle_patterns
            )
            risk_score += (struggle_count / len(interaction_patterns)) * 0.4

            # Help and retry risk
            if help_requests > 1:
                risk_score += 0.2
            if step_retries > 0:
                risk_score += 0.1

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            # Determine intervention recommendations
            interventions = []
            if risk_score > 0.7:
                interventions = [
                    "provide_simplified_flow",
                    "offer_personal_assistance",
                    "reduce_required_steps",
                ]
            elif risk_score > 0.4:
                interventions = [
                    "show_helpful_tips",
                    "highlight_progress",
                    "offer_skip_options",
                ]

            prediction_result = {
                "user_id": user_id,
                "drop_off_risk": round(risk_score, 3),
                "risk_level": "high"
                if risk_score > 0.7
                else "medium"
                if risk_score > 0.4
                else "low",
                "completion_probability": round(1 - risk_score, 3),
                "risk_factors_identified": {
                    "time_based": avg_time > 120 if time_spent else False,
                    "interaction_struggles": struggle_count
                    > len(interaction_patterns) // 2,
                    "help_dependency": help_requests > 1,
                    "retry_issues": step_retries > 0,
                },
                "intervention_recommendations": interventions,
                "prediction_confidence": 0.8,
                "predicted_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"Drop-off prediction for user {user_id}: {risk_score:.3f} risk score"
            )
            return prediction_result

        except Exception as e:
            logger.error(f"Error predicting user dropoff: {e}")
            raise
