"""ML-based notification timing optimization service."""

import logging
import pickle
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from app.models.notification_analytics import (
    InteractionType,
    NotificationInteraction,
    NotificationLog,
    UserNotificationPattern,
)

logger = logging.getLogger(__name__)


class NotificationTimingOptimizer:
    """ML-based notification timing optimizer."""

    def __init__(self, db: Session, model_path: Optional[str] = None) -> None:
        self.db: Session = db
        self.model_path = model_path or "models/notification_timing_model.pkl"
        self.model = None
        self.feature_scaler = None
        self.is_trained = False

        # Load existing model if available
        self._load_model()

    def _load_model(self) -> None:
        """Load pre-trained model if available."""
        try:
            model_file = Path(self.model_path)
            if model_file.exists():
                with open(model_file, "rb") as f:
                    model_data = pickle.load(f)
                    self.model = model_data.get("model")
                    self.feature_scaler = model_data.get("scaler")
                    self.is_trained = True
                logger.info("Loaded pre-trained notification timing model")
        except Exception as e:
            logger.warning(f"Failed to load model: {e}")

    def _save_model(self) -> None:
        """Save trained model to disk."""
        try:
            model_file = Path(self.model_path)
            model_file.parent.mkdir(parents=True, exist_ok=True)

            model_data = {
                "model": self.model,
                "scaler": self.feature_scaler,
                "trained_at": datetime.now(timezone.utc).isoformat(),
            }

            with open(model_file, "wb") as f:
                pickle.dump(model_data, f)

            logger.info(f"Saved model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")

    async def train_timing_model(self, min_samples: int = 100) -> bool:
        """Train ML model for optimal notification timing."""
        try:
            # Get training data
            features, labels = await self._prepare_training_data(min_samples)

            if len(features) < min_samples:
                logger.warning(
                    f"Insufficient training data: {len(features)} < {min_samples}"
                )
                return False

            # Use scikit-learn for training (would be imported here)
            try:
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split
                from sklearn.preprocessing import StandardScaler
            except ImportError:
                logger.error("scikit-learn not available for ML training")
                return False

            # Prepare features and labels
            X = np.array(features)
            y = np.array(labels)

            # Scale features
            self.feature_scaler = StandardScaler()
            X_scaled = self.feature_scaler.fit_transform(X)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )

            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
            )

            self.model.fit(X_train, y_train)

            # Evaluate model
            predictions = self.model.predict(X_test)
            accuracy = (predictions == y_test).mean()

            logger.info(f"Model trained with accuracy: {accuracy:.3f}")

            if accuracy > 0.6:  # Minimum acceptable accuracy
                self.is_trained = True
                self._save_model()
                return True
            else:
                logger.warning(f"Model accuracy too low: {accuracy:.3f}")
                return False

        except Exception as e:
            logger.error(f"Failed to train timing model: {e}")
            return False

    async def predict_optimal_timing(
        self,
        user_id: str,
        notification_type: str,
        target_time: datetime,
        time_window_hours: int = 6,
    ) -> Tuple[datetime, float]:
        """Predict optimal timing for a notification within a time window."""
        try:
            if not self.is_trained:
                # Fallback to heuristic approach
                return await self._heuristic_timing_prediction(user_id, target_time)

            # Get user pattern
            user_pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not user_pattern:
                return target_time, 0.5  # Default confidence

            # Generate candidate times within window
            candidates = []
            start_time = target_time - timedelta(hours=time_window_hours // 2)
            end_time = target_time + timedelta(hours=time_window_hours // 2)

            current_time = start_time
            while current_time <= end_time:
                # Skip if outside user's preferred hours or in quiet time
                if self._is_valid_send_time(current_time, user_pattern):
                    candidates.append(current_time)
                current_time += timedelta(minutes=30)  # 30-minute intervals

            if not candidates:
                return target_time, 0.3  # Low confidence fallback

            # Predict engagement probability for each candidate
            best_time = target_time
            best_score = 0.0

            for candidate_time in candidates:
                features = self._extract_prediction_features(
                    user_pattern, notification_type, candidate_time
                )

                if self.feature_scaler and self.model:
                    features_scaled = self.feature_scaler.transform([features])
                    # Get probability of engagement (positive class)
                    engagement_prob = self.model.predict_proba(features_scaled)[0][1]

                    if engagement_prob > best_score:
                        best_score = engagement_prob
                        best_time = candidate_time

            return best_time, min(best_score, 0.95)  # Cap confidence at 95%

        except Exception as e:
            logger.error(f"Failed to predict optimal timing: {e}")
            return target_time, 0.3

    async def update_model_with_feedback(
        self, user_id: str, notification_log_id: str, was_engaged: bool
    ) -> None:
        """Update model with real engagement feedback (online learning)."""
        try:
            # For now, just log the feedback
            # In a full implementation, this would trigger incremental learning
            log_entry = (
                self.db.query(NotificationLog)
                .filter(NotificationLog.id == notification_log_id)
                .first()
            )

            if log_entry and log_entry.timing_optimization_used:
                feedback_data = {
                    "user_id": user_id,
                    "notification_id": notification_log_id,
                    "sent_at": log_entry.sent_at,
                    "notification_type": log_entry.notification_type,
                    "was_engaged": was_engaged,
                    "timing_optimized": True,
                }

                # Log feedback for future model retraining
                logger.info(f"Timing optimization feedback: {feedback_data}")

                # TODO: Implement incremental learning or store feedback for batch retraining

        except Exception as e:
            logger.error(f"Failed to update model with feedback: {e}")

    async def get_user_timing_insights(self, user_id: str) -> Dict[str, Any]:
        """Get timing insights for a specific user."""
        try:
            user_pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not user_pattern:
                return {
                    "status": "insufficient_data",
                    "optimal_hours": [18],  # Default
                    "confidence": 0.3,
                    "insights": ["더 많은 데이터가 필요합니다"],
                }

            insights = []
            optimal_hours = []

            # Extract optimal hours from pattern
            if user_pattern.preferred_hours:
                sorted_hours = sorted(
                    user_pattern.preferred_hours.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )

                # Top 3 hours with engagement rate > 0.4
                for hour_str, engagement_rate in sorted_hours[:3]:
                    if engagement_rate > 0.4:
                        optimal_hours.append(int(hour_str))

            if not optimal_hours:
                optimal_hours = [18]  # Default

            # Generate insights
            if user_pattern.overall_engagement_score > 70:
                insights.append(
                    f"높은 참여율 사용자 ({user_pattern.overall_engagement_score:.1f}%)"
                )
                insights.append("개인화된 타이밍으로 더 나은 결과 기대")
            elif user_pattern.overall_engagement_score < 30:
                insights.append(
                    f"낮은 참여율 사용자 ({user_pattern.overall_engagement_score:.1f}%)"
                )
                insights.append("알림 빈도와 내용 최적화 필요")

            if user_pattern.should_personalize_timing():
                insights.append("명확한 시간 선호도 패턴 발견")
                insights.append(f"최적 시간: {optimal_hours[0]}시 권장")
            else:
                insights.append("시간 선호도 패턴이 불분명함")

            confidence = min(
                user_pattern.total_notifications_received / 50.0, 0.9
            )  # More data = higher confidence

            return {
                "status": "available",
                "optimal_hours": optimal_hours,
                "confidence": confidence,
                "insights": insights,
                "engagement_score": user_pattern.overall_engagement_score,
                "total_notifications": user_pattern.total_notifications_received,
            }

        except Exception as e:
            logger.error(f"Failed to get user timing insights: {e}")
            return {
                "status": "error",
                "optimal_hours": [18],
                "confidence": 0.3,
                "insights": ["데이터 분석 중 오류 발생"],
            }

    async def _prepare_training_data(
        self, min_samples: int
    ) -> Tuple[List[List[float]], List[int]]:
        """Prepare training data for ML model."""
        features = []
        labels = []

        try:
            # Get users with sufficient notification history
            patterns = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.total_notifications_received >= 10)
                .all()
            )

            for pattern in patterns:
                # Get notification logs for this user
                logs = (
                    self.db.query(NotificationLog)
                    .filter(
                        NotificationLog.user_id == pattern.user_id,
                        NotificationLog.success.is_(True),
                    )
                    .limit(100)  # Limit to prevent memory issues
                    .all()
                )

                for log in logs:
                    # Get interactions for this notification
                    interactions = (
                        self.db.query(NotificationInteraction)
                        .filter(
                            NotificationInteraction.notification_log_id == log.id,
                            NotificationInteraction.interaction_type.in_(
                                [InteractionType.OPENED, InteractionType.CLICKED]
                            ),
                        )
                        .first()
                    )

                    # Create training sample
                    feature_vector = self._extract_prediction_features(
                        pattern, log.notification_type, log.sent_at
                    )

                    label = 1 if interactions else 0  # 1 = engaged, 0 = not engaged

                    features.append(feature_vector)
                    labels.append(label)

            logger.info(f"Prepared {len(features)} training samples")
            return features, labels

        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return [], []

    def _extract_prediction_features(
        self,
        user_pattern: UserNotificationPattern,
        notification_type: str,
        send_time: datetime,
    ) -> List[float]:
        """Extract features for ML prediction."""
        features = []

        # Time-based features
        features.append(send_time.hour)  # Hour of day (0-23)
        features.append(send_time.weekday())  # Day of week (0-6)
        features.append(send_time.minute / 60.0)  # Normalized minutes

        # User engagement features
        features.append(user_pattern.overall_engagement_score / 100.0)
        features.append(user_pattern.open_rate or 0.0)
        features.append(user_pattern.click_rate or 0.0)
        features.append(user_pattern.total_notifications_received / 100.0)  # Normalized

        # Historical hour preference
        hour_preference = 0.0
        if user_pattern.preferred_hours:
            hour_preference = user_pattern.preferred_hours.get(str(send_time.hour), 0.0)
        features.append(hour_preference)

        # Day of week preference
        day_preference = 0.0
        if user_pattern.preferred_days:
            day_preference = user_pattern.preferred_days.get(
                str(send_time.weekday()), 0.0
            )
        features.append(day_preference)

        # Notification type features (one-hot encoded)
        notification_types = [
            "preparation_reminder",
            "departure_reminder",
            "move_reminder",
            "business_hours",
            "weather",
            "traffic",
            "recommendations",
            "promotional",
        ]

        for nt in notification_types:
            features.append(1.0 if notification_type == nt else 0.0)

        # Response time features
        features.append(
            (user_pattern.avg_response_time_seconds or 3600) / 3600.0
        )  # Normalized to hours

        return features

    async def _heuristic_timing_prediction(
        self, user_id: str, target_time: datetime
    ) -> Tuple[datetime, float]:
        """Heuristic-based timing prediction when ML model is not available."""
        try:
            user_pattern = (
                self.db.query(UserNotificationPattern)
                .filter(UserNotificationPattern.user_id == user_id)
                .first()
            )

            if not user_pattern or not user_pattern.preferred_hours:
                return target_time, 0.4

            # Find the best hour within ±3 hours of target
            target_hour = target_time.hour
            candidate_hours = []

            for hour_offset in range(-3, 4):  # ±3 hours
                candidate_hour = (target_hour + hour_offset) % 24
                engagement_rate = user_pattern.preferred_hours.get(
                    str(candidate_hour), 0.0
                )
                candidate_hours.append((candidate_hour, engagement_rate))

            # Sort by engagement rate
            candidate_hours.sort(key=lambda x: x[1], reverse=True)
            best_hour, best_engagement = candidate_hours[0]

            # Create optimized time
            optimized_time = target_time.replace(hour=best_hour, minute=0, second=0)
            confidence = min(best_engagement + 0.2, 0.8)  # Add base confidence

            return optimized_time, confidence

        except Exception as e:
            logger.error(f"Heuristic timing prediction failed: {e}")
            return target_time, 0.3

    def _is_valid_send_time(
        self, send_time: datetime, user_pattern: UserNotificationPattern
    ) -> bool:
        """Check if a send time is valid for the user."""
        hour = send_time.hour

        # Check against preferred hours if available
        if user_pattern.preferred_hours:
            engagement_rate = user_pattern.preferred_hours.get(str(hour), 0.0)
            return engagement_rate > 0.1  # Minimum engagement threshold

        # Default business hours check
        return 8 <= hour <= 22  # 8 AM to 10 PM


def get_ml_notification_optimizer(db: Session) -> NotificationTimingOptimizer:
    """Get ML notification timing optimizer instance."""
    return NotificationTimingOptimizer(db)
