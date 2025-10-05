"""Test cases for notification analytics service (TDD Red phase)."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.notification_analytics import (
    ABTestCohort,
    NotificationInteraction,
    NotificationLog,
    UserNotificationPattern,
)
from app.schemas.notification_analytics import (
    ABTestCohortCreate,
    NotificationAnalyticsReport,
    NotificationInteractionCreate,
    NotificationLogCreate,
    PersonalizationInsights,
)


class TestNotificationAnalyticsService:
    """Test suite for notification analytics service (Task 2-2-5)."""

    def setup_method(self) -> None:
        """Setup test dependencies."""
        self.test_user_id = str(uuid4())
        self.test_notification_id = str(uuid4())

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def sample_notification_log_data(self):
        """Sample notification log data for testing."""
        return NotificationLogCreate(
            user_id=self.test_user_id,
            notification_id=self.test_notification_id,
            notification_type="preparation_reminder",
            priority="normal",
            platform="ios",
            title="내일 홍대 데이트 준비!",
            body="카페 예약 + 우산 필수",
            sent_at=datetime.now(),
            success=True,
            message_id="fcm_123456",
            delivery_time_seconds=2.5,
            timing_optimization_used=True,
        )

    @pytest.fixture
    def sample_interaction_data(self):
        """Sample interaction data for testing."""
        return NotificationInteractionCreate(
            notification_log_id=str(uuid4()),
            user_id=self.test_user_id,
            interaction_type="opened",
            timestamp=datetime.now(),
            time_from_delivery=45.0,
            device_info={"platform": "ios", "version": "15.0"},
        )

    async def test_log_notification_sent_success(
        self, mock_db, sample_notification_log_data
    ):
        """
        Given: 알림 전송 로그 데이터
        When: log_notification_sent 서비스 호출
        Then: 데이터베이스에 로그 저장 및 ID 반환
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        expected_log_id = str(uuid4())
        mock_log = NotificationLog(**sample_notification_log_data.dict())
        mock_log.id = expected_log_id
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # When
        result = await service.log_notification_sent(sample_notification_log_data)

        # Then
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    async def test_log_notification_interaction_success(
        self, mock_db, sample_interaction_data
    ):
        """
        Given: 유효한 알림 상호작용 데이터
        When: log_notification_interaction 호출
        Then: 상호작용 로그 저장 및 패턴 업데이트 트리거
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)
        service.update_user_engagement_pattern = AsyncMock()

        mock_interaction = NotificationInteraction(**sample_interaction_data.dict())
        mock_interaction.id = str(uuid4())
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # When
        result = await service.log_notification_interaction(sample_interaction_data)

        # Then
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        service.update_user_engagement_pattern.assert_called_once_with(
            self.test_user_id
        )

    async def test_analyze_user_notification_pattern_new_user(self, mock_db):
        """
        Given: 알림 기록이 없는 새로운 사용자
        When: analyze_user_notification_pattern 호출
        Then: 기본 패턴으로 새 레코드 생성
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        # Mock empty query results for new user
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # When
        result = await service.analyze_user_notification_pattern(self.test_user_id)

        # Then
        assert result is not None
        assert result.user_id == self.test_user_id
        assert result.total_notifications_received == 0
        assert result.open_rate == 0.0
        assert result.overall_engagement_score == 0.0

    async def test_analyze_user_notification_pattern_existing_user(self, mock_db):
        """
        Given: 알림 기록이 있는 기존 사용자
        When: analyze_user_notification_pattern 호출
        Then: 실제 데이터 기반으로 패턴 분석 및 업데이트
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        # Mock notification logs
        mock_logs = [
            Mock(
                sent_at=datetime.now() - timedelta(hours=i),
                notification_type="preparation_reminder",
                success=True,
            )
            for i in range(5)
        ]

        # Mock interactions (2 out of 5 opened)
        mock_interactions = [
            Mock(
                notification_log_id=mock_logs[i].id,
                interaction_type="opened",
                timestamp=datetime.now() - timedelta(hours=i, minutes=10),
            )
            for i in range(2)
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_logs
        mock_db.query.return_value.filter.return_value.join.return_value.all.return_value = (
            mock_interactions
        )

        # Mock existing pattern
        existing_pattern = UserNotificationPattern(
            user_id=self.test_user_id, total_notifications_received=0
        )
        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_pattern
        )

        # When
        result = await service.analyze_user_notification_pattern(self.test_user_id)

        # Then
        assert result.total_notifications_received == 5
        assert result.total_notifications_opened == 2
        assert result.open_rate == 0.4  # 2/5
        assert result.overall_engagement_score > 0

    async def test_get_optimal_send_time_for_user(self, mock_db):
        """
        Given: 사용자의 알림 패턴 데이터
        When: get_optimal_send_time_for_user 호출
        Then: 가장 높은 참여율을 보이는 시간대 반환
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        # Mock user pattern with hourly preferences
        mock_pattern = UserNotificationPattern(
            user_id=self.test_user_id,
            preferred_hours={"18": 0.8, "19": 0.6, "20": 0.3},
            most_active_hour=18,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pattern

        # When
        optimal_hour = await service.get_optimal_send_time_for_user(self.test_user_id)

        # Then
        assert optimal_hour == 18

    async def test_get_optimal_send_time_for_user_no_pattern(self, mock_db):
        """
        Given: 패턴 데이터가 없는 사용자
        When: get_optimal_send_time_for_user 호출
        Then: 기본 시간(18시) 반환
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # When
        optimal_hour = await service.get_optimal_send_time_for_user(self.test_user_id)

        # Then
        assert optimal_hour == 18  # Default hour

    async def test_should_personalize_notification_high_engagement(self, mock_db):
        """
        Given: 높은 참여율을 보이는 사용자
        When: should_personalize_notification 호출
        Then: True 반환 (개인화 적용)
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        mock_pattern = UserNotificationPattern(
            user_id=self.test_user_id,
            engagement_rate=0.7,  # High engagement
            total_notifications_received=50,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pattern

        # When
        should_personalize = await service.should_personalize_notification(
            self.test_user_id, "preparation_reminder"
        )

        # Then
        assert should_personalize is True

    async def test_should_personalize_notification_low_engagement(self, mock_db):
        """
        Given: 낮은 참여율을 보이는 사용자
        When: should_personalize_notification 호출
        Then: False 반환 (기본 알림만)
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        mock_pattern = UserNotificationPattern(
            user_id=self.test_user_id,
            engagement_rate=0.1,  # Low engagement
            total_notifications_received=20,
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pattern

        # When
        should_personalize = await service.should_personalize_notification(
            self.test_user_id, "preparation_reminder"
        )

        # Then
        assert should_personalize is False

    async def test_generate_analytics_report(self, mock_db):
        """
        Given: 특정 기간의 알림 데이터
        When: generate_analytics_report 호출
        Then: 종합 분석 리포트 생성
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        # Mock aggregated data
        mock_db.query.return_value.filter.return_value.count.return_value = 100
        mock_db.execute.return_value.fetchall.return_value = [
            ("preparation_reminder", 50, 30, 15),
            ("departure_reminder", 50, 35, 20),
        ]

        # When
        report = await service.generate_analytics_report(start_date, end_date)

        # Then
        assert isinstance(report, NotificationAnalyticsReport)
        assert report.period_start == start_date
        assert report.period_end == end_date
        assert report.total_notifications_sent > 0
        assert "preparation_reminder" in report.type_breakdown

    async def test_create_ab_test_cohort_success(self, mock_db):
        """
        Given: 유효한 A/B 테스트 코호트 데이터
        When: create_ab_test_cohort 호출
        Then: 코호트 생성 및 ID 반환
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        cohort_data = ABTestCohortCreate(
            test_name="timing_optimization_test",
            test_description="Test optimal timing vs default timing",
            cohort_name="variant_a",
            traffic_allocation=0.5,
            test_parameters={"timing_optimization": True},
            target_metric="open_rate",
            start_date=datetime.now(),
        )

        mock_cohort = ABTestCohort(**cohort_data.dict())
        mock_cohort.id = str(uuid4())
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # When
        result = await service.create_ab_test_cohort(cohort_data)

        # Then
        assert result is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_assign_user_to_ab_test_success(self, mock_db):
        """
        Given: 사용자와 활성 A/B 테스트 코호트
        When: assign_user_to_ab_test 호출
        Then: 사용자를 적절한 코호트에 할당
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        test_name = "timing_optimization_test"
        mock_cohorts = [
            Mock(id=str(uuid4()), cohort_name="control", traffic_allocation=0.5),
            Mock(id=str(uuid4()), cohort_name="variant_a", traffic_allocation=0.5),
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = mock_cohorts
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # When
        assignment = await service.assign_user_to_ab_test(self.test_user_id, test_name)

        # Then
        assert assignment is not None
        assert assignment.user_id == self.test_user_id
        assert assignment.cohort_id in [c.id for c in mock_cohorts]
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_get_personalization_insights_comprehensive(self, mock_db):
        """
        Given: 충분한 데이터가 있는 사용자
        When: get_personalization_insights 호출
        Then: 상세한 개인화 인사이트 반환
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        mock_pattern = UserNotificationPattern(
            user_id=self.test_user_id,
            total_notifications_received=100,
            total_notifications_opened=70,
            engagement_rate=0.7,
            preferred_hours={"18": 0.8, "19": 0.6, "20": 0.3},
            most_active_hour=18,
            type_preferences={"preparation_reminder": {"sent": 50, "engaged": 40}},
            personalized_open_rate=0.8,
            non_personalized_open_rate=0.6,
            personalization_lift=0.33,  # 33% improvement
        )

        mock_db.query.return_value.filter.return_value.first.return_value = mock_pattern

        # When
        insights = await service.get_personalization_insights(self.test_user_id)

        # Then
        assert isinstance(insights, PersonalizationInsights)
        assert insights.user_id == self.test_user_id
        assert insights.overall_engagement_score > 50
        assert 18 in insights.optimal_send_times
        assert insights.should_use_timing_optimization is True
        assert insights.estimated_improvement > 0

    async def test_update_user_engagement_pattern_incremental(self, mock_db):
        """
        Given: 새로운 알림 상호작용
        When: update_user_engagement_pattern 호출
        Then: 기존 패턴에 새 데이터 반영하여 업데이트
        """
        # Given
        from app.services.notifications.notification_analytics_service import (
            get_notification_analytics_service,
        )

        service = get_notification_analytics_service(mock_db)

        # Mock existing pattern
        existing_pattern = UserNotificationPattern(
            user_id=self.test_user_id,
            total_notifications_received=10,
            total_notifications_opened=6,
            open_rate=0.6,
        )

        # Mock recent interactions
        recent_logs = [
            Mock(notification_type="preparation_reminder", success=True),
            Mock(notification_type="departure_reminder", success=True),
        ]

        recent_interactions = [
            Mock(interaction_type="opened"),
        ]

        mock_db.query.return_value.filter.return_value.first.return_value = (
            existing_pattern
        )
        mock_db.query.return_value.filter.return_value.all.return_value = recent_logs
        mock_db.query.return_value.filter.return_value.join.return_value.filter.return_value.all.return_value = (
            recent_interactions
        )

        mock_db.commit = Mock()

        # When
        updated_pattern = await service.update_user_engagement_pattern(
            self.test_user_id
        )

        # Then
        # New totals: 10 + 2 = 12 received, 6 + 1 = 7 opened
        assert updated_pattern.total_notifications_received == 12
        assert updated_pattern.total_notifications_opened == 7
        assert abs(updated_pattern.open_rate - (7 / 12)) < 0.01
        mock_db.commit.assert_called_once()
