"""User preference analysis and profiling service."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.place import Place
from app.models.user_behavior import UserBehavior, UserBehaviorProfile
from app.schemas.preference import (
    PreferenceAnalysisResponse,
    UserBehaviorCreate,
    UserProfileResponse,
)

logger = logging.getLogger(__name__)


class UserPreferenceService:
    """Service for analyzing user preferences and building user profiles."""

    def __init__(self, db: Session):
        self.db = db

    def record_user_behavior(
        self, user_id: UUID, behavior_data: UserBehaviorCreate
    ) -> UserBehavior:
        """
        Record user behavior for preference learning.

        Args:
            user_id: User identifier
            behavior_data: Behavior data to record

        Returns:
            Created UserBehavior record
        """
        try:
            # Create behavior record
            behavior = UserBehavior(
                user_id=user_id,
                action=behavior_data.action,
                place_id=behavior_data.place_id,
                duration_minutes=behavior_data.duration_minutes,
                rating=behavior_data.rating,
                tags_added=behavior_data.tags_added,
                time_of_day=behavior_data.time_of_day,
                day_of_week=behavior_data.day_of_week,
                created_at=datetime.utcnow(),
            )

            self.db.add(behavior)
            self.db.commit()
            self.db.refresh(behavior)

            logger.info(f"Recorded behavior for user {user_id}: {behavior_data.action}")
            return behavior

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to record user behavior: {e}")
            raise

    def analyze_user_preferences(
        self, user_id: UUID, analysis_window_days: int = 90
    ) -> PreferenceAnalysisResponse:
        """
        Analyze user preferences based on behavior history.

        Args:
            user_id: User identifier
            analysis_window_days: Days of history to analyze

        Returns:
            Comprehensive preference analysis
        """
        try:
            # Get user behavior data
            cutoff_date = datetime.utcnow() - timedelta(days=analysis_window_days)

            behaviors = (
                self.db.query(UserBehavior)
                .filter(
                    UserBehavior.user_id == user_id,
                    UserBehavior.created_at >= cutoff_date,
                )
                .all()
            )

            if not behaviors:
                return self._default_preferences()

            # Analyze different preference dimensions
            cuisine_prefs = self._analyze_cuisine_preferences(user_id, behaviors)
            ambiance_prefs = self._analyze_ambiance_preferences(behaviors)
            price_prefs = self._analyze_price_preferences(user_id, behaviors)
            location_prefs = self._analyze_location_preferences(user_id, behaviors)
            time_prefs = self._analyze_time_preferences(behaviors)

            # Calculate overall confidence
            confidence_score = self._calculate_confidence_score(behaviors)

            logger.info(f"Preference analysis completed for user {user_id}")

            return PreferenceAnalysisResponse(
                user_id=str(user_id),
                cuisine_preferences=cuisine_prefs,
                ambiance_preferences=ambiance_prefs,
                price_preferences=price_prefs,
                location_preferences=location_prefs,
                time_preferences=time_prefs,
                confidence_score=confidence_score,
                analysis_date=datetime.utcnow(),
                data_points_count=len(behaviors),
            )

        except Exception as e:
            logger.error(f"Failed to analyze preferences for user {user_id}: {e}")
            raise

    def update_preferences_from_feedback(
        self,
        user_id: UUID,
        place_id: UUID,
        rating: float,
        feedback_text: Optional[str] = None,
        visited: bool = True,
    ) -> bool:
        """
        Update user preferences based on feedback.

        Args:
            user_id: User identifier
            place_id: Place that was recommended/visited
            rating: User rating (1-5)
            feedback_text: Optional feedback text
            visited: Whether user actually visited

        Returns:
            True if preferences were updated
        """
        try:
            # Get place details
            place = (
                self.db.query(Place)
                .filter(Place.id == place_id, Place.user_id == user_id)
                .first()
            )

            if not place:
                logger.warning(f"Place {place_id} not found for user {user_id}")
                return False

            # Record feedback as behavior
            feedback_behavior = UserBehaviorCreate(
                action="feedback",
                place_id=place_id,
                rating=rating,
                duration_minutes=None,
                tags_added=[],
                time_of_day=self._get_current_time_of_day(),
                day_of_week=datetime.now().strftime("%A").lower(),
            )

            self.record_user_behavior(user_id, feedback_behavior)

            # Update preference weights based on feedback
            self._update_preference_weights(user_id, place, rating, visited)

            logger.info(f"Updated preferences from feedback for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update preferences from feedback: {e}")
            return False

    def _analyze_cuisine_preferences(
        self, user_id: UUID, behaviors: List[UserBehavior]
    ) -> Dict[str, float]:
        """Analyze cuisine preferences from behavior data."""
        # Get places associated with behaviors
        place_ids = [b.place_id for b in behaviors if b.place_id]
        places = self.db.query(Place).filter(Place.id.in_(place_ids)).all()
        place_map = {str(p.id): p for p in places}

        # Count interactions by category
        category_scores = defaultdict(list)

        for behavior in behaviors:
            if behavior.place_id and str(behavior.place_id) in place_map:
                place = place_map[str(behavior.place_id)]
                score = behavior.rating or 3.0  # Default neutral rating

                # Weight by action type
                if behavior.action == "visit":
                    score *= 1.5
                elif behavior.action == "save":
                    score *= 1.2
                elif behavior.action == "share":
                    score *= 1.3

                category_scores[place.category].append(score)

        # Calculate preference scores
        preferences = {}
        for category, scores in category_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                preferences[category] = min(avg_score / 5.0, 1.0)  # Normalize to 0-1

        return preferences

    def _analyze_ambiance_preferences(
        self, behaviors: List[UserBehavior]
    ) -> Dict[str, float]:
        """Analyze ambiance preferences from tags and behavior."""
        ambiance_tags = defaultdict(list)

        for behavior in behaviors:
            if behavior.tags_added and behavior.rating:
                for tag in behavior.tags_added:
                    # Categorize ambiance-related tags
                    if any(amb in tag for amb in ["조용", "분위기", "로맨틱", "활기", "편안"]):
                        ambiance_tags[tag].append(behavior.rating)

        # Calculate preferences
        preferences = {}
        for tag, ratings in ambiance_tags.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                preferences[tag] = min(avg_rating / 5.0, 1.0)

        return preferences

    def _analyze_price_preferences(
        self, user_id: UUID, behaviors: List[UserBehavior]
    ) -> Dict[str, float]:
        """Analyze price range preferences."""
        # This would analyze price-related behavior
        # For now, return default preferences
        return {"budget": 0.3, "moderate": 0.5, "expensive": 0.2}

    async def get_notification_settings(self, user_id: str):
        """Get user's notification settings."""
        # Mock implementation for now
        from datetime import time

        from app.schemas.notification import (
            NotificationTiming,
            QuietHours,
            UserNotificationSettings,
        )

        return UserNotificationSettings(
            enabled=True,
            quiet_hours=QuietHours(
                start=time(22, 0),
                end=time(8, 0),
                days_of_week=["monday", "tuesday", "wednesday", "thursday", "friday"],
            ),
            timing=NotificationTiming(
                day_before_hour=18,
                departure_minutes_before=30,
                move_reminder_minutes=15,
            ),
        )

    def _analyze_location_preferences(
        self, user_id: UUID, behaviors: List[UserBehavior]
    ) -> Dict[str, Any]:
        """Analyze location preferences."""
        place_ids = [b.place_id for b in behaviors if b.place_id]
        places = self.db.query(Place).filter(Place.id.in_(place_ids)).all()

        if not places:
            return {"preferred_areas": [], "travel_radius_km": 5.0}

        # Analyze preferred geographic areas
        coordinates = [
            (p.latitude, p.longitude) for p in places if p.latitude and p.longitude
        ]

        if coordinates:
            # Calculate center of activity
            center_lat = sum(lat for lat, lng in coordinates) / len(coordinates)
            center_lng = sum(lng for lat, lng in coordinates) / len(coordinates)

            # Calculate average travel distance
            from app.utils.distance_calculator import DistanceCalculator

            calc = DistanceCalculator()

            distances = []
            for lat, lng in coordinates:
                dist = calc.haversine_distance(center_lat, center_lng, lat, lng)
                distances.append(dist)

            avg_radius = sum(distances) / len(distances) if distances else 5.0

            return {
                "preferred_center": {"latitude": center_lat, "longitude": center_lng},
                "travel_radius_km": round(avg_radius, 1),
                "activity_hotspots": self._identify_hotspots(coordinates),
            }

        return {"preferred_areas": [], "travel_radius_km": 5.0}

    def _analyze_time_preferences(
        self, behaviors: List[UserBehavior]
    ) -> Dict[str, float]:
        """Analyze temporal preferences."""
        time_patterns = defaultdict(list)

        for behavior in behaviors:
            if behavior.time_of_day and behavior.rating:
                time_patterns[behavior.time_of_day].append(behavior.rating)

            if behavior.day_of_week and behavior.rating:
                time_patterns[behavior.day_of_week].append(behavior.rating)

        preferences = {}
        for time_period, ratings in time_patterns.items():
            if ratings:
                avg_rating = sum(ratings) / len(ratings)
                preferences[time_period] = min(avg_rating / 5.0, 1.0)

        return preferences

    def _calculate_confidence_score(self, behaviors: List[UserBehavior]) -> float:
        """Calculate confidence in preference analysis."""
        if not behaviors:
            return 0.0

        # Factors affecting confidence:
        # 1. Number of data points
        # 2. Recency of data
        # 3. Consistency of ratings

        data_points_score = min(len(behaviors) / 50, 1.0)  # Normalize to 50 behaviors

        # Recency score
        now = datetime.utcnow()
        recent_behaviors = [b for b in behaviors if (now - b.created_at).days <= 30]
        recency_score = len(recent_behaviors) / len(behaviors) if behaviors else 0

        # Consistency score (lower variance in ratings = higher consistency)
        ratings = [b.rating for b in behaviors if b.rating]
        if len(ratings) > 1:
            import statistics

            rating_variance = statistics.variance(ratings)
            consistency_score = max(
                0, 1.0 - (rating_variance / 4.0)
            )  # Normalize variance
        else:
            consistency_score = 0.5

        # Combined confidence score
        confidence = (data_points_score + recency_score + consistency_score) / 3
        return round(confidence, 3)

    def _default_preferences(self) -> PreferenceAnalysisResponse:
        """Return default preferences for new users."""
        return PreferenceAnalysisResponse(
            user_id=str(uuid4()),
            cuisine_preferences={"restaurant": 0.5, "cafe": 0.3, "bar": 0.2},
            ambiance_preferences={"comfortable": 0.6, "quiet": 0.4},
            price_preferences={"moderate": 0.6, "budget": 0.3, "expensive": 0.1},
            location_preferences={"travel_radius_km": 5.0},
            time_preferences={"evening": 0.4, "afternoon": 0.3, "morning": 0.3},
            confidence_score=0.0,
            analysis_date=datetime.utcnow(),
            data_points_count=0,
        )

    def _get_current_time_of_day(self) -> str:
        """Get current time of day category."""
        hour = datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"

    def _identify_hotspots(
        self, coordinates: List[Tuple[float, float]]
    ) -> List[Dict[str, Any]]:
        """Identify geographic hotspots from coordinate data."""
        if not coordinates:
            return []

        # Simple clustering to identify hotspots
        # In production, would use more sophisticated clustering algorithm

        hotspots = []
        used_coords = set()

        for i, (lat1, lng1) in enumerate(coordinates):
            if i in used_coords:
                continue

            cluster_coords = [(lat1, lng1)]
            used_coords.add(i)

            # Find nearby coordinates
            for j, (lat2, lng2) in enumerate(coordinates):
                if j in used_coords or j <= i:
                    continue

                from app.utils.distance_calculator import DistanceCalculator

                calc = DistanceCalculator()
                distance = calc.haversine_distance(lat1, lng1, lat2, lng2)

                if distance <= 2.0:  # 2km threshold for hotspot
                    cluster_coords.append((lat2, lng2))
                    used_coords.add(j)

            # Create hotspot if enough points
            if len(cluster_coords) >= 2:
                center_lat = sum(lat for lat, lng in cluster_coords) / len(
                    cluster_coords
                )
                center_lng = sum(lng for lat, lng in cluster_coords) / len(
                    cluster_coords
                )

                hotspots.append(
                    {
                        "center": {"latitude": center_lat, "longitude": center_lng},
                        "visit_count": len(cluster_coords),
                        "radius_km": 2.0,
                    }
                )

        return hotspots

    def _update_preference_weights(
        self, user_id: UUID, place: Place, rating: float, visited: bool
    ):
        """Update preference weights based on feedback."""
        try:
            # Get or create user preferences
            user_pref = (
                self.db.query(UserBehaviorProfile)
                .filter(UserBehaviorProfile.user_id == user_id)
                .first()
            )

            if not user_pref:
                # Create new preference record
                user_pref = UserBehaviorProfile(
                    user_id=user_id,
                    cuisine_preferences={},
                    ambiance_preferences={},
                    price_preferences={},
                    location_preferences={},
                    time_preferences={},
                    confidence_score=0.0,
                )
                self.db.add(user_pref)

            # Update cuisine preferences based on rating
            if place.category:
                current_cuisine_prefs = user_pref.cuisine_preferences or {}

                # Learning rate (how much new feedback affects preferences)
                learning_rate = 0.1

                # Update category preference
                current_score = current_cuisine_prefs.get(place.category, 0.5)
                normalized_rating = rating / 5.0  # Normalize to 0-1

                # Positive or negative feedback affects preference
                if visited:
                    new_score = current_score + learning_rate * (
                        normalized_rating - current_score
                    )
                else:
                    # Didn't visit - negative signal
                    new_score = current_score + learning_rate * (0.3 - current_score)

                current_cuisine_prefs[place.category] = max(0.0, min(1.0, new_score))
                user_pref.cuisine_preferences = current_cuisine_prefs

            # Update ambiance preferences from tags
            if place.tags:
                current_ambiance_prefs = user_pref.ambiance_preferences or {}

                for tag in place.tags:
                    if tag in current_ambiance_prefs:
                        current_score = current_ambiance_prefs[tag]
                        normalized_rating = rating / 5.0
                        new_score = current_score + 0.1 * (
                            normalized_rating - current_score
                        )
                        current_ambiance_prefs[tag] = max(0.0, min(1.0, new_score))

                user_pref.ambiance_preferences = current_ambiance_prefs

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update preference weights: {e}")

    def get_user_profile(self, user_id: UUID) -> Optional[UserProfileResponse]:
        """Get comprehensive user profile with preferences."""
        try:
            # Get preference analysis
            preferences = self.analyze_user_preferences(user_id)

            # Get user preference record
            user_pref = (
                self.db.query(UserBehaviorProfile)
                .filter(UserBehaviorProfile.user_id == user_id)
                .first()
            )

            return UserProfileResponse(
                user_id=str(user_id),
                preferences=preferences,
                profile_completeness=preferences.confidence_score,
                last_updated=user_pref.updated_at if user_pref else datetime.utcnow(),
                total_interactions=preferences.data_points_count,
            )

        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {e}")
            return None

    def track_preference_changes(
        self, user_id: UUID, window_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Track how user preferences have changed over time."""
        try:
            # Get preference snapshots over time
            # This would require storing historical preference data
            # For now, return basic change tracking

            current_prefs = self.analyze_user_preferences(user_id, window_days)
            past_prefs = self.analyze_user_preferences(user_id, window_days * 2)

            changes = []

            # Compare cuisine preferences
            for category in set(
                list(current_prefs.cuisine_preferences.keys())
                + list(past_prefs.cuisine_preferences.keys())
            ):
                current_score = current_prefs.cuisine_preferences.get(category, 0)
                past_score = past_prefs.cuisine_preferences.get(category, 0)

                if abs(current_score - past_score) > 0.1:  # Significant change
                    changes.append(
                        {
                            "preference_type": "cuisine",
                            "category": category,
                            "change": current_score - past_score,
                            "trend": (
                                "increasing"
                                if current_score > past_score
                                else "decreasing"
                            ),
                        }
                    )

            return changes

        except Exception as e:
            logger.error(f"Failed to track preference changes: {e}")
            return []


class UserPreferencesService:
    """Service for managing user notification preferences."""

    def __init__(self):
        pass

    async def get_settings(self, user_id: str):
        """Get user's notification settings."""
        # Mock implementation for now
        from datetime import time

        from app.schemas.notification import (
            NotificationTiming,
            QuietHours,
            UserNotificationSettings,
        )

        return UserNotificationSettings(
            enabled=True,
            quiet_hours=QuietHours(
                start=time(22, 0),
                end=time(8, 0),
                days_of_week=["monday", "tuesday", "wednesday", "thursday", "friday"],
            ),
            timing=NotificationTiming(
                day_before_hour=18,
                departure_minutes_before=30,
                move_reminder_minutes=15,
            ),
        )
