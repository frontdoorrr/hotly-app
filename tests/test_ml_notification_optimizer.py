"""Test cases for ML notification timing optimizer (TDD Red phase)."""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.notification_analytics import (
    NotificationInteraction,
    NotificationLog,
    UserNotificationPattern,
)
from app.services.ml_notification_optimizer import NotificationTimingOptimizer


class TestMLNotificationOptimizer:
    """Test suite for ML notification timing optimizer."""

    def setup_method(self):
        """Setup test dependencies."""
        self.test_user_id = str(uuid4())
        self.target_time = datetime(2025, 1, 15, 18, 0, 0)  # 6 PM

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_user_pattern(self):
        """Sample user notification pattern."""
        return UserNotificationPattern(
            user_id=self.test_user_id,
            total_notifications_received=50,
            total_notifications_opened=30,
            open_rate=0.6,
            engagement_rate=0.65,
            preferred_hours={
                "17": 0.8,  # 5 PM - highest engagement
                "18": 0.7,  # 6 PM - good engagement
                "19": 0.5,  # 7 PM - moderate engagement
                "20": 0.3,  # 8 PM - low engagement
            },
            most_active_hour=17,
        )

    async def test_heuristic_timing_prediction_with_pattern(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 사용자의 알림 패턴 데이터가 있음
        When: ML 모델 없이 휴리스틱 기반으로 최적 시간 예측
        Then: 가장 높은 참여율을 보이는 시간으로 조정
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_user_pattern
        )

        # When
        optimized_time, confidence = await optimizer._heuristic_timing_prediction(
            self.test_user_id, self.target_time
        )

        # Then
        assert optimized_time.hour == 17  # Best hour from pattern
        assert 0.4 <= confidence <= 0.8
        assert optimized_time.minute == 0  # Should be rounded to the hour

    async def test_heuristic_timing_prediction_no_pattern(self, mock_db):
        """
        Given: 사용자 패턴 데이터가 없음
        When: 휴리스틱 기반 예측 수행
        Then: 원본 시간 유지 및 낮은 신뢰도
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # When
        optimized_time, confidence = await optimizer._heuristic_timing_prediction(
            self.test_user_id, self.target_time
        )

        # Then
        assert optimized_time == self.target_time
        assert confidence == 0.4

    async def test_predict_optimal_timing_without_ml_model(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: ML 모델이 훈련되지 않은 상태
        When: predict_optimal_timing 호출
        Then: 휴리스틱 방식으로 fallback하여 최적 시간 예측
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        optimizer.is_trained = False
        optimizer._heuristic_timing_prediction = AsyncMock(
            return_value=(self.target_time.replace(hour=17), 0.7)
        )

        # When
        optimized_time, confidence = await optimizer.predict_optimal_timing(
            self.test_user_id, "preparation_reminder", self.target_time
        )

        # Then
        optimizer._heuristic_timing_prediction.assert_called_once_with(
            self.test_user_id, self.target_time
        )
        assert optimized_time.hour == 17
        assert confidence == 0.7

    @patch("app.services.ml_notification_optimizer.StandardScaler")
    @patch("app.services.ml_notification_optimizer.RandomForestClassifier")
    async def test_predict_optimal_timing_with_trained_model(
        self, mock_rf, mock_scaler, mock_db, sample_user_pattern
    ):
        """
        Given: 훈련된 ML 모델이 있음
        When: predict_optimal_timing 호출
        Then: ML 모델을 사용하여 최적 시간 예측
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        optimizer.is_trained = True

        # Mock trained model
        mock_model = Mock()
        mock_model.predict_proba.return_value = [
            [0.2, 0.8]
        ]  # 80% engagement probability
        optimizer.model = mock_model

        mock_scaler_instance = Mock()
        mock_scaler_instance.transform.return_value = [[0.1, 0.2, 0.3]]
        optimizer.feature_scaler = mock_scaler_instance

        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_user_pattern
        )

        # When
        optimized_time, confidence = await optimizer.predict_optimal_timing(
            self.test_user_id,
            "preparation_reminder",
            self.target_time,
            time_window_hours=4,
        )

        # Then
        assert confidence > 0.5  # Should be high confidence
        mock_model.predict_proba.assert_called()

    async def test_extract_prediction_features(self, mock_db, sample_user_pattern):
        """
        Given: 사용자 패턴과 알림 시간 정보
        When: _extract_prediction_features 호출
        Then: ML 모델 입력용 특성 벡터 생성
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        send_time = datetime(2025, 1, 15, 17, 30, 0)  # 5:30 PM, Wednesday
        notification_type = "preparation_reminder"

        # When
        features = optimizer._extract_prediction_features(
            sample_user_pattern, notification_type, send_time
        )

        # Then
        assert len(features) >= 10  # Should have multiple features
        assert features[0] == 17  # Hour of day
        assert features[1] == 2  # Wednesday (0=Monday)
        assert features[2] == 0.5  # Normalized minutes (30/60)
        assert 0.0 <= features[3] <= 1.0  # Engagement score (normalized)

    async def test_train_timing_model_insufficient_data(self, mock_db):
        """
        Given: 훈련 데이터가 부족함
        When: train_timing_model 호출
        Then: False 반환 및 모델 미훈련
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        optimizer._prepare_training_data = AsyncMock(
            return_value=([], [])
        )  # Empty data

        # When
        success = await optimizer.train_timing_model(min_samples=100)

        # Then
        assert success is False
        assert optimizer.is_trained is False

    @patch("app.services.ml_notification_optimizer.RandomForestClassifier")
    @patch("app.services.ml_notification_optimizer.StandardScaler")
    @patch("app.services.ml_notification_optimizer.train_test_split")
    async def test_train_timing_model_success(
        self, mock_split, mock_scaler, mock_rf, mock_db
    ):
        """
        Given: 충분한 훈련 데이터가 있음
        When: train_timing_model 호출
        Then: 모델 훈련 성공 및 is_trained = True
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)

        # Mock sufficient training data
        mock_features = [[0.5, 0.6, 0.7] for _ in range(200)]
        mock_labels = [1, 0] * 100  # Alternating labels
        optimizer._prepare_training_data = AsyncMock(
            return_value=(mock_features, mock_labels)
        )

        # Mock scikit-learn components
        mock_scaler_instance = Mock()
        mock_scaler_instance.fit_transform.return_value = mock_features
        mock_scaler.return_value = mock_scaler_instance

        mock_model = Mock()
        mock_model.predict.return_value = [1] * 40  # Mock predictions
        mock_rf.return_value = mock_model

        mock_split.return_value = (
            mock_features[:160],
            mock_features[160:],  # X_train, X_test
            mock_labels[:160],
            [1] * 40,  # y_train, y_test
        )

        optimizer._save_model = Mock()

        # When
        success = await optimizer.train_timing_model(min_samples=100)

        # Then
        assert success is True
        assert optimizer.is_trained is True
        optimizer._save_model.assert_called_once()

    async def test_update_model_with_feedback_positive(self, mock_db):
        """
        Given: 사용자가 최적화된 알림에 긍정적으로 반응
        When: update_model_with_feedback 호출
        Then: 피드백 로깅 및 향후 모델 개선을 위한 데이터 저장
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        notification_log_id = str(uuid4())

        mock_log = NotificationLog(
            id=notification_log_id,
            user_id=self.test_user_id,
            sent_at=datetime.now(),
            notification_type="preparation_reminder",
            timing_optimization_used=True,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_log

        # When
        await optimizer.update_model_with_feedback(
            self.test_user_id, notification_log_id, was_engaged=True
        )

        # Then
        # Should not raise exception and log feedback
        mock_db.query.assert_called_once()

    async def test_get_user_timing_insights_high_engagement(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 높은 참여율을 보이는 사용자
        When: get_user_timing_insights 호출
        Then: 상세한 타이밍 인사이트 및 최적화 권장사항 반환
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        sample_user_pattern.total_notifications_received = 100
        sample_user_pattern.engagement_rate = 0.8

        mock_db.query.return_value.filter.return_value.first.return_value = (
            sample_user_pattern
        )

        # When
        insights = await optimizer.get_user_timing_insights(self.test_user_id)

        # Then
        assert insights["status"] == "available"
        assert 17 in insights["optimal_hours"]  # Best hour from pattern
        assert insights["confidence"] > 0.5
        assert insights["engagement_score"] > 70
        assert any("높은 참여율" in insight for insight in insights["insights"])

    async def test_get_user_timing_insights_insufficient_data(self, mock_db):
        """
        Given: 데이터가 부족한 새로운 사용자
        When: get_user_timing_insights 호출
        Then: 기본 권장사항과 낮은 신뢰도 반환
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # When
        insights = await optimizer.get_user_timing_insights(self.test_user_id)

        # Then
        assert insights["status"] == "insufficient_data"
        assert insights["optimal_hours"] == [18]  # Default hour
        assert insights["confidence"] == 0.3
        assert any("더 많은 데이터" in insight for insight in insights["insights"])

    async def test_is_valid_send_time_with_preferences(
        self, mock_db, sample_user_pattern
    ):
        """
        Given: 사용자의 시간 선호도 데이터가 있음
        When: _is_valid_send_time으로 특정 시간 검증
        Then: 참여율 기반으로 유효성 판단
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)

        good_time = datetime(2025, 1, 15, 17, 0)  # 5 PM (0.8 engagement)
        poor_time = datetime(2025, 1, 15, 20, 0)  # 8 PM (0.3 engagement)
        invalid_time = datetime(2025, 1, 15, 3, 0)  # 3 AM (not in preferences)

        # When
        is_good_valid = optimizer._is_valid_send_time(good_time, sample_user_pattern)
        is_poor_valid = optimizer._is_valid_send_time(poor_time, sample_user_pattern)
        is_invalid_valid = optimizer._is_valid_send_time(
            invalid_time, sample_user_pattern
        )

        # Then
        assert is_good_valid is True  # High engagement rate
        assert is_poor_valid is True  # Above 0.1 threshold
        assert is_invalid_valid is False  # No engagement data

    async def test_prepare_training_data_creates_features_and_labels(self, mock_db):
        """
        Given: 데이터베이스에 알림 로그와 상호작용 데이터가 있음
        When: _prepare_training_data 호출
        Then: ML 훈련용 특성과 라벨 생성
        """
        # Given
        optimizer = NotificationTimingOptimizer(mock_db)

        # Mock user patterns
        mock_patterns = [
            Mock(
                user_id=str(uuid4()),
                total_notifications_received=20,
                open_rate=0.6,
                engagement_rate=0.7,
                preferred_hours={"18": 0.7},
            )
        ]

        # Mock notification logs
        mock_logs = [
            Mock(
                id=str(uuid4()),
                notification_type="preparation_reminder",
                sent_at=datetime(2025, 1, 15, 18, 0),
                success=True,
            )
        ]

        # Mock interactions (engaged)
        mock_interaction = Mock(
            notification_log_id=mock_logs[0].id, interaction_type="opened"
        )

        # Setup query mocks
        def query_side_effect(*args):
            if args[0] == optimizer.db.query(UserNotificationPattern):
                return Mock(
                    filter=Mock(return_value=Mock(all=Mock(return_value=mock_patterns)))
                )
            elif args[0] == optimizer.db.query(NotificationLog):
                return Mock(
                    filter=Mock(
                        return_value=Mock(
                            limit=Mock(
                                return_value=Mock(all=Mock(return_value=mock_logs))
                            )
                        )
                    )
                )
            elif args[0] == optimizer.db.query(NotificationInteraction):
                return Mock(
                    filter=Mock(
                        return_value=Mock(first=Mock(return_value=mock_interaction))
                    )
                )

        mock_db.query.side_effect = query_side_effect

        # When
        features, labels = await optimizer._prepare_training_data(min_samples=1)

        # Then
        assert len(features) > 0
        assert len(labels) > 0
        assert len(features) == len(labels)
        assert all(isinstance(f, list) for f in features)
        assert all(isinstance(label, int) for label in labels)
        assert all(label in [0, 1] for label in labels)  # Binary labels
