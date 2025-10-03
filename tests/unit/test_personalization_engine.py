"""
Tests for PersonalizationEngine service.
Task 2-2-3: 소유권 기반 추천 시간대
Following TDD Red-Green-Refactor approach as specified in rules.md.
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.notification import NotificationType
from app.schemas.notification import (
    EngagementMetrics,
    PersonalizedTimingRequest,
    UserBehaviorPattern,
)
from app.services.personalization_engine import (
    InsufficientDataError,
    PersonalizationEngine,
)


class TestPersonalizationEngine:
    """Test suite for PersonalizationEngine service."""

    @pytest.fixture
    def personalization_engine(self):
        """Create PersonalizationEngine instance for testing."""
        from unittest.mock import Mock

        mock_db = Mock()
        return PersonalizationEngine(db=mock_db)

    @pytest.fixture
    def sample_user_behavior_data(self):
        """Sample user behavior pattern data."""
        base_user_id = str(uuid4())
        return [
            UserBehaviorPattern(
                user_id=base_user_id,
                timestamp=datetime.now() - timedelta(days=7),
                notification_type=NotificationType.PREPARATION_REMINDER,
                sent_at=time(18, 0),
                opened_at=time(18, 15),
                clicked=True,
                day_of_week="monday",
                engagement_score=0.85,
            ),
            UserBehaviorPattern(
                user_id=base_user_id,
                timestamp=datetime.now() - timedelta(days=6),
                notification_type=NotificationType.DEPARTURE_REMINDER,
                sent_at=time(19, 0),
                opened_at=time(19, 5),
                clicked=True,
                day_of_week="tuesday",
                engagement_score=0.92,
            ),
            UserBehaviorPattern(
                user_id=base_user_id,
                timestamp=datetime.now() - timedelta(days=5),
                notification_type=NotificationType.PREPARATION_REMINDER,
                sent_at=time(17, 0),
                opened_at=None,  # 미열람
                clicked=False,
                day_of_week="wednesday",
                engagement_score=0.0,
            ),
            UserBehaviorPattern(
                user_id=base_user_id,
                timestamp=datetime.now() - timedelta(days=4),
                notification_type=NotificationType.PREPARATION_REMINDER,
                sent_at=time(18, 0),
                opened_at=time(18, 10),
                clicked=True,
                day_of_week="thursday",
                engagement_score=0.78,
            ),
            UserBehaviorPattern(
                user_id=base_user_id,
                timestamp=datetime.now() - timedelta(days=3),
                notification_type=NotificationType.DEPARTURE_REMINDER,
                sent_at=time(19, 0),
                opened_at=time(19, 8),
                clicked=False,  # 열람했지만 클릭하지 않음
                day_of_week="friday",
                engagement_score=0.55,
            ),
        ]

    @pytest.fixture
    def sample_engagement_metrics(self):
        """Sample engagement metrics for user."""
        return EngagementMetrics(
            user_id=str(uuid4()),
            total_notifications=50,
            opened_count=35,
            clicked_count=20,
            open_rate=0.7,
            click_rate=0.4,
            average_open_delay_minutes=8.5,
            peak_engagement_hours=[18, 19, 20],
            preferred_days=["monday", "tuesday", "wednesday", "thursday", "friday"],
            last_updated=datetime.now(),
        )

    async def test_analyze_user_behavior_patterns_success(
        self, personalization_engine, sample_user_behavior_data
    ):
        """
        Given: 사용자의 충분한 알림 히스토리 데이터
        When: 사용자 행동 패턴을 분석함
        Then: 참여도 높은 시간대와 요일이 식별됨
        """
        # Given
        user_id = str(uuid4())
        # Fix the sample data to use the same user_id
        for data in sample_user_behavior_data:
            data.user_id = user_id

        personalization_engine.notification_history_service.get_user_history = (
            AsyncMock(return_value=sample_user_behavior_data)
        )

        # When
        behavior_analysis = await personalization_engine.analyze_user_behavior_patterns(
            user_id
        )

        # Then
        assert behavior_analysis.user_id == user_id
        assert len(behavior_analysis.optimal_hours) > 0
        assert behavior_analysis.overall_engagement_rate > 0

        # 높은 참여도 시간대 확인
        peak_hours = behavior_analysis.optimal_hours
        assert 18 in peak_hours or 19 in peak_hours  # 높은 참여도 시간대 포함

        # 요일별 선호도 확인
        preferred_days = behavior_analysis.preferred_days
        assert len(preferred_days) > 0

    async def test_predict_optimal_timing_based_on_ml_model(
        self, personalization_engine, sample_engagement_metrics
    ):
        """
        Given: 개인화된 타이밍 예측 요청과 사용자 패턴
        When: ML 모델로 최적 알림 시간을 예측함
        Then: 개인화된 알림 시간 추천이 반환됨
        """
        # Given
        user_id = str(uuid4())
        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
            course_context={
                "location": "홍대",
                "date": "friday",
                "course_type": "cafe_restaurant",
            },
        )

        # Mock behavior analysis to return sufficient data
        sample_engagement_metrics.user_id = user_id
        personalization_engine.analyze_user_behavior_patterns = AsyncMock(
            return_value=sample_engagement_metrics
        )

        # ML 모델이 19시를 최적 시간으로 예측
        personalization_engine.ml_model.predict_optimal_hour = AsyncMock(
            return_value=19
        )
        personalization_engine.behavior_analyzer.get_engagement_probability = AsyncMock(
            return_value=0.85
        )

        # When
        prediction = await personalization_engine.predict_optimal_timing(timing_request)

        # Then
        assert prediction.user_id == user_id
        assert prediction.predicted_time.hour == 19
        assert prediction.confidence_score > 0.6
        assert prediction.engagement_probability == 0.85
        assert len(prediction.alternative_times) > 0

    async def test_insufficient_data_handling(self, personalization_engine):
        """
        Given: 신규 사용자로 알림 히스토리가 부족함
        When: 개인화된 시간 예측을 시도함
        Then: InsufficientDataError가 발생하고 기본값 사용
        """
        # Given
        new_user_id = str(uuid4())
        personalization_engine.notification_history_service.get_user_history = (
            AsyncMock(return_value=[])
        )

        timing_request = PersonalizedTimingRequest(
            user_id=new_user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        # When & Then
        with pytest.raises(InsufficientDataError):
            await personalization_engine.predict_optimal_timing(timing_request)

    async def test_personalized_timing_with_context_awareness(
        self, personalization_engine, sample_engagement_metrics
    ):
        """
        Given: 특정 코스 컨텍스트(위치, 요일, 코스 타입)
        When: 컨텍스트를 고려한 개인화된 타이밍을 예측함
        Then: 컨텍스트에 맞는 최적화된 시간이 반환됨
        """
        # Given
        user_id = str(uuid4())

        # 금요일 강남 저녁 데이트 컨텍스트
        friday_evening_context = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.DEPARTURE_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
            course_context={
                "location": "강남",
                "date": "friday",
                "course_type": "restaurant_bar",
                "expected_crowd_level": "high",
            },
        )

        # Mock behavior analysis
        sample_engagement_metrics.user_id = user_id
        personalization_engine.analyze_user_behavior_patterns = AsyncMock(
            return_value=sample_engagement_metrics
        )

        # 컨텍스트 기반 예측: 금요일 강남은 교통 혼잡으로 더 일찍 출발 권장
        personalization_engine.context_analyzer.analyze_course_context = AsyncMock(
            return_value={"recommended_advance_minutes": 45}
        )
        personalization_engine.ml_model.predict_optimal_hour = AsyncMock(
            return_value=17
        )  # 17시 예측
        personalization_engine.behavior_analyzer.get_engagement_probability = AsyncMock(
            return_value=0.75
        )

        # When
        prediction = await personalization_engine.predict_optimal_timing(
            friday_evening_context
        )

        # Then
        assert prediction.predicted_time.hour == 17  # 컨텍스트 반영된 시간
        assert "crowd_level" in prediction.reasoning
        assert prediction.context_factors["location"] == "강남"

    async def test_engagement_based_timing_optimization(
        self, personalization_engine, sample_engagement_metrics
    ):
        """
        Given: 사용자의 과거 참여도 메트릭스
        When: 참여도 기반 타이밍 최적화를 수행함
        Then: 높은 참여도 시간대로 조정된 알림 시간이 반환됨
        """
        # Given
        user_id = sample_engagement_metrics.user_id
        personalization_engine.engagement_analyzer.get_user_metrics = AsyncMock(
            return_value=sample_engagement_metrics
        )

        default_time = datetime.now().replace(hour=16, minute=0)  # 낮은 참여도 시간
        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=default_time,
        )

        # When
        optimized_timing = await personalization_engine.optimize_timing_for_engagement(
            timing_request
        )

        # Then
        # 높은 참여도 시간대(18-20시)로 조정되어야 함
        assert optimized_timing.predicted_time.hour in [18, 19, 20]
        assert optimized_timing.improvement_score > 0
        assert "engagement optimization" in optimized_timing.reasoning.lower()

    async def test_a_b_testing_framework_integration(self, personalization_engine):
        """
        Given: A/B 테스트 그룹에 속한 사용자들
        When: 개인화된 타이밍 예측을 요청함
        Then: 테스트 그룹에 따라 다른 알고리즘이 적용됨
        """
        # Given
        control_user_id = str(uuid4())
        test_user_id = str(uuid4())

        # A/B 테스트: 기존 알고리즘 vs ML 개인화 알고리즘
        personalization_engine.ab_testing_service.get_user_group = AsyncMock(
            side_effect=lambda user_id: "control"
            if user_id == control_user_id
            else "treatment"
        )

        timing_request_control = PersonalizedTimingRequest(
            user_id=control_user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        timing_request_test = PersonalizedTimingRequest(
            user_id=test_user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        # When
        control_result = await personalization_engine.predict_with_ab_testing(
            timing_request_control
        )
        treatment_result = await personalization_engine.predict_with_ab_testing(
            timing_request_test
        )

        # Then
        assert control_result.algorithm_used == "default"
        assert treatment_result.algorithm_used == "ml_personalized"
        assert control_result.ab_test_group == "control"
        assert treatment_result.ab_test_group == "treatment"

    async def test_model_prediction_error_handling(self, personalization_engine):
        """
        Given: ML 모델 예측 중 오류 발생
        When: 예측을 시도함
        Then: 기본값으로 fallback하고 에러를 로깅함
        """
        # Given
        user_id = str(uuid4())
        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        # ML 모델 예측 실패
        personalization_engine.ml_model.predict_optimal_hour = AsyncMock(
            side_effect=Exception("Model server unavailable")
        )

        # When
        result = await personalization_engine.predict_optimal_timing_with_fallback(
            timing_request
        )

        # Then
        assert result.predicted_time.hour == 18  # 기본값 사용
        assert result.fallback_used is True
        assert "model error" in result.reasoning.lower()

    async def test_batch_timing_optimization(self, personalization_engine):
        """
        Given: 여러 사용자의 알림 타이밍 최적화 요청
        When: 배치로 처리함
        Then: 모든 사용자에 대해 효율적으로 개인화된 타이밍이 반환됨
        """
        # Given
        batch_requests = [
            PersonalizedTimingRequest(
                user_id=str(uuid4()),
                notification_type=NotificationType.PREPARATION_REMINDER,
                default_time=datetime.now().replace(hour=18, minute=0),
            )
            for _ in range(100)
        ]

        personalization_engine.ml_model.batch_predict = AsyncMock(
            return_value=[19] * 100  # 모든 사용자에게 19시 예측
        )

        # When
        batch_results = await personalization_engine.optimize_batch_timing(
            batch_requests
        )

        # Then
        assert len(batch_results) == 100
        assert all(result.predicted_time.hour == 19 for result in batch_results)
        assert batch_results[0].processing_time_ms < 1000  # 효율적 처리

    async def test_user_feedback_learning_integration(self, personalization_engine):
        """
        Given: 사용자의 알림 피드백 데이터
        When: 피드백을 기반으로 모델을 업데이트함
        Then: 개선된 예측 성능이 반영됨
        """
        # Given
        user_id = str(uuid4())

        # 사용자가 18시 알림에 부정적 피드백, 20시 알림에 긍정적 피드백
        feedback_data = [
            {
                "user_id": user_id,
                "notification_time": time(18, 0),
                "feedback": "too_early",
                "engagement": 0.2,
            },
            {
                "user_id": user_id,
                "notification_time": time(20, 0),
                "feedback": "perfect_timing",
                "engagement": 0.9,
            },
        ]

        personalization_engine.feedback_service.get_user_feedback = AsyncMock(
            return_value=feedback_data
        )

        # When
        await personalization_engine.update_model_with_feedback(user_id)

        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        updated_prediction = await personalization_engine.predict_optimal_timing(
            timing_request
        )

        # Then
        # 피드백 반영으로 20시 근처로 조정되어야 함
        assert updated_prediction.predicted_time.hour >= 19
        assert "user feedback" in updated_prediction.reasoning.lower()

    async def test_real_time_context_adaptation(self, personalization_engine):
        """
        Given: 실시간 컨텍스트 변화 (날씨, 교통, 이벤트)
        When: 실시간 상황을 반영한 타이밍 조정을 요청함
        Then: 현재 상황에 맞게 동적으로 조정된 시간이 반환됨
        """
        # Given
        user_id = str(uuid4())
        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.DEPARTURE_REMINDER,
            default_time=datetime.now().replace(hour=17, minute=30),
            real_time_context={
                "weather": "heavy_rain",
                "traffic_level": "severe",
                "public_event": "concert_nearby",
            },
        )

        # 실시간 컨텍스트 분석: 악천후+교통체증으로 더 일찍 출발 권장
        personalization_engine.real_time_analyzer.analyze_current_conditions = (
            AsyncMock(return_value={"recommended_advance_minutes": 60})
        )

        # When
        adapted_timing = await personalization_engine.adapt_timing_to_real_time_context(
            timing_request
        )

        # Then
        assert adapted_timing.predicted_time.hour <= 16  # 1시간 앞당겨짐
        assert "weather" in adapted_timing.context_factors
        assert "traffic" in adapted_timing.context_factors
        assert adapted_timing.adaptation_reason == "real_time_conditions"


class TestPersonalizedTimingValidation:
    """Test suite for personalized timing validation and constraints."""

    @pytest.fixture
    def personalization_engine(self):
        """Create PersonalizationEngine instance for testing."""
        from unittest.mock import Mock

        mock_db = Mock()
        return PersonalizationEngine(db=mock_db)

    async def test_timing_constraint_validation(self, personalization_engine):
        """
        Given: 시간 제약 조건 (너무 이른/늦은 시간)
        When: 개인화된 타이밍을 예측함
        Then: 제약 조건 내에서 적절한 시간이 반환됨
        """
        # Given
        user_id = str(uuid4())

        # 새벽 3시 예측 시도 (비현실적)
        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
        )

        personalization_engine.ml_model.predict_optimal_hour = AsyncMock(
            return_value=3
        )  # 새벽 3시

        # When
        prediction = await personalization_engine.predict_optimal_timing(timing_request)

        # Then
        # 합리적인 시간대로 조정되어야 함 (8-22시 범위)
        assert 8 <= prediction.predicted_time.hour <= 22
        assert prediction.constraint_applied is True
        assert "time constraint" in prediction.reasoning.lower()

    async def test_user_quiet_hours_respect(self, personalization_engine):
        """
        Given: 사용자의 조용한 시간 설정
        When: 해당 시간대에 예측이 시도됨
        Then: 조용한 시간을 피한 시간이 반환됨
        """
        # Given
        user_id = str(uuid4())
        quiet_hours = {"start": "22:00", "end": "08:00"}

        timing_request = PersonalizedTimingRequest(
            user_id=user_id,
            notification_type=NotificationType.PREPARATION_REMINDER,
            default_time=datetime.now().replace(hour=18, minute=0),
            user_constraints={
                "quiet_hours": quiet_hours,
                "max_notifications_per_day": 3,
            },
        )

        # ML이 23시를 예측했지만 조용한 시간
        personalization_engine.ml_model.predict_optimal_hour = AsyncMock(
            return_value=23
        )

        # When
        prediction = await personalization_engine.predict_optimal_timing(timing_request)

        # Then
        # 조용한 시간을 피해 조정되어야 함
        predicted_hour = prediction.predicted_time.hour
        assert not (22 <= predicted_hour or predicted_hour <= 8)
        assert prediction.quiet_hours_adjusted is True
