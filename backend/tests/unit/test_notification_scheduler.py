"""
Tests for NotificationScheduler service.
Following TDD approach as specified in rules.md.
"""

from datetime import datetime, time, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.notification import NotificationPriority, NotificationType
from app.schemas.notification import (
    NotificationTiming,
    QuietHours,
    ScheduledNotificationRequest,
    UserNotificationSettings,
)
from app.services.notifications.notification_scheduler import (
    InvalidScheduleTimeError,
    NotificationScheduler,
    ScheduleConflictError,
)


class TestNotificationScheduler:
    """Test suite for NotificationScheduler service."""

    @pytest.fixture
    def scheduler(self):
        """Create NotificationScheduler instance for testing."""
        from unittest.mock import Mock

        mock_db = Mock()
        return NotificationScheduler(db=mock_db)

    @pytest.fixture
    def sample_user_settings(self):
        """Sample user notification settings."""
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

    @pytest.fixture
    def sample_course_data(self):
        """Sample course data for scheduling."""
        return {
            "course_id": str(uuid4()),
            "user_id": str(uuid4()),
            "scheduled_date": datetime.now() + timedelta(days=1),
            "places": [
                {
                    "id": str(uuid4()),
                    "name": "카페 A",
                    "arrival_time": time(14, 0),
                    "stay_duration": 120,  # 2시간
                },
                {
                    "id": str(uuid4()),
                    "name": "레스토랑 B",
                    "arrival_time": time(16, 30),
                    "stay_duration": 90,  # 1.5시간
                },
            ],
        }

    async def test_schedule_course_notifications_success(
        self, scheduler, sample_course_data, sample_user_settings
    ):
        """
        Given: 유효한 코스 데이터와 사용자 설정
        When: 코스 알림을 스케줄링함
        Then: 3개의 알림이 생성됨 (사전준비, 출발, 이동)
        """
        # Given
        scheduler.user_preferences_service.get_settings = AsyncMock(
            return_value=sample_user_settings
        )
        scheduler.redis_queue.schedule = AsyncMock()

        # When
        result = await scheduler.schedule_course_notifications(
            course_data=sample_course_data, user_id=sample_course_data["user_id"]
        )

        # Then
        assert len(result.scheduled_notifications) == 3
        assert result.total_scheduled == 3

        # 알림 타입 확인
        notification_types = [notif.type for notif in result.scheduled_notifications]
        assert NotificationType.PREPARATION_REMINDER in notification_types
        assert NotificationType.DEPARTURE_REMINDER in notification_types
        assert NotificationType.MOVE_REMINDER in notification_types

        # Redis 큐에 스케줄링 호출 확인
        assert scheduler.redis_queue.schedule.call_count == 3

    async def test_schedule_preparation_notification_timing(
        self, scheduler, sample_course_data, sample_user_settings
    ):
        """
        Given: 내일 14:00 데이트 일정과 전날 18:00 알림 설정
        When: 사전 준비 알림을 스케줄링함
        Then: 오늘 18:00에 알림이 예약됨
        """
        # Given
        scheduler.user_preferences_service.get_settings = AsyncMock(
            return_value=sample_user_settings
        )
        scheduler.redis_queue.schedule = AsyncMock()

        # When
        notifications = await scheduler._create_preparation_notification(
            course_data=sample_course_data, settings=sample_user_settings
        )

        # Then
        expected_time = sample_course_data["scheduled_date"].replace(
            hour=18, minute=0, second=0, microsecond=0
        ) - timedelta(days=1)

        assert notifications.scheduled_time == expected_time
        assert notifications.type == NotificationType.PREPARATION_REMINDER
        assert notifications.priority == NotificationPriority.NORMAL

    async def test_schedule_departure_notification_with_travel_time(
        self, scheduler, sample_course_data, sample_user_settings
    ):
        """
        Given: 첫 장소 도착 시간이 14:00이고 이동시간 45분, 30분 전 알림 설정
        When: 출발 시간 알림을 스케줄링함
        Then: 12:45에 알림이 예약됨 (14:00 - 45분 - 30분)
        """
        # Given
        scheduler.user_preferences_service.get_settings = AsyncMock(
            return_value=sample_user_settings
        )
        scheduler.travel_time_calculator.calculate = AsyncMock(
            return_value=45
        )  # 45분 소요

        # When
        notification = await scheduler._create_departure_notification(
            course_data=sample_course_data, settings=sample_user_settings
        )

        # Then
        first_place_arrival = sample_course_data["scheduled_date"].replace(
            hour=14, minute=0
        )
        departure_time = first_place_arrival - timedelta(minutes=45)  # 13:15
        expected_notification_time = departure_time - timedelta(minutes=30)  # 12:45

        assert notification.scheduled_time.replace(
            second=0, microsecond=0
        ) == expected_notification_time.replace(second=0, microsecond=0)
        assert notification.type == NotificationType.DEPARTURE_REMINDER
        assert notification.priority == NotificationPriority.HIGH

    async def test_quiet_hours_rescheduling(self, scheduler, sample_course_data):
        """
        Given: 조용시간(22:00-08:00) 설정된 사용자
        When: 조용시간에 예약된 일반 알림이 있음
        Then: 다음 활성 시간(08:00)으로 연기됨
        """
        # Given
        quiet_settings = UserNotificationSettings(
            enabled=True,
            quiet_hours=QuietHours(
                start=time(22, 0),
                end=time(8, 0),
                days_of_week=[
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                    "sunday",
                ],
            ),
        )

        scheduler.user_preferences_service.get_settings = AsyncMock(
            return_value=quiet_settings
        )

        notification_in_quiet_time = ScheduledNotificationRequest(
            user_id=sample_course_data["user_id"],
            type=NotificationType.PREPARATION_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=datetime.now().replace(hour=23, minute=0),  # 조용시간
            message="테스트 메시지",
        )

        # When
        adjusted_time = await scheduler._adjust_for_quiet_hours(
            notification_in_quiet_time, quiet_settings
        )

        # Then
        next_day_8am = (datetime.now() + timedelta(days=1)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        assert adjusted_time == next_day_8am

    async def test_urgent_notification_bypasses_quiet_hours(
        self, scheduler, sample_course_data
    ):
        """
        Given: 조용시간 설정된 사용자
        When: 긴급 알림이 조용시간에 예약됨
        Then: 조용시간을 무시하고 즉시 발송됨
        """
        # Given
        quiet_settings = UserNotificationSettings(
            enabled=True, quiet_hours=QuietHours(start=time(22, 0), end=time(8, 0))
        )

        urgent_notification = ScheduledNotificationRequest(
            user_id=sample_course_data["user_id"],
            type=NotificationType.URGENT_CHANGE,
            priority=NotificationPriority.URGENT,
            scheduled_time=datetime.now().replace(hour=23, minute=0),  # 조용시간
            message="긴급 변경 알림",
        )

        # When
        adjusted_time = await scheduler._adjust_for_quiet_hours(
            urgent_notification, quiet_settings
        )

        # Then
        assert adjusted_time == urgent_notification.scheduled_time  # 변경되지 않음

    async def test_duplicate_notification_prevention(
        self, scheduler, sample_course_data
    ):
        """
        Given: 24시간 내 동일한 내용의 알림이 이미 예약됨
        When: 같은 내용의 알림을 다시 스케줄링 시도함
        Then: 중복으로 감지되어 거부됨
        """
        # Given
        duplicate_notification = ScheduledNotificationRequest(
            user_id=sample_course_data["user_id"],
            type=NotificationType.PREPARATION_REMINDER,
            course_id=sample_course_data["course_id"],
            scheduled_time=datetime.now() + timedelta(hours=2),
            message="내일 데이트 준비하세요",
        )

        scheduler.duplicate_detector.is_duplicate = AsyncMock(return_value=True)

        # When & Then
        with pytest.raises(ScheduleConflictError):
            await scheduler.schedule_single_notification(duplicate_notification)

    async def test_frequency_limit_enforcement(self, scheduler):
        """
        Given: 주당 7개 알림 제한 설정된 사용자
        When: 이미 7개 알림이 발송된 상태에서 추가 알림 시도
        Then: 빈도 제한으로 거부됨
        """
        # Given
        user_id = str(uuid4())

        scheduler.user_engagement_analyzer.get_weekly_notification_count = AsyncMock(
            return_value=7
        )
        scheduler.user_engagement_analyzer.get_frequency_limit = AsyncMock(
            return_value=7
        )

        new_notification = ScheduledNotificationRequest(
            user_id=user_id,
            type=NotificationType.PREPARATION_REMINDER,
            priority=NotificationPriority.NORMAL,
            scheduled_time=datetime.now() + timedelta(hours=1),
            message="추가 알림",
        )

        # When & Then
        with pytest.raises(ScheduleConflictError, match="frequency limit exceeded"):
            await scheduler.schedule_single_notification(new_notification)

    async def test_batch_notification_scheduling(self, scheduler):
        """
        Given: 여러 사용자의 알림들이 배치로 전달됨
        When: 배치 스케줄링을 실행함
        Then: 모든 알림이 효율적으로 처리됨
        """
        # Given
        batch_notifications = [
            ScheduledNotificationRequest(
                user_id=str(uuid4()),
                type=NotificationType.DEPARTURE_REMINDER,
                scheduled_time=datetime.now() + timedelta(hours=i),
                message=f"사용자 {i} 알림",
            )
            for i in range(100)
        ]

        scheduler.redis_queue.schedule_batch = AsyncMock()

        # When
        result = await scheduler.schedule_batch_notifications(batch_notifications)

        # Then
        assert result.total_scheduled == 100
        assert result.success_count == 100
        assert result.error_count == 0
        scheduler.redis_queue.schedule_batch.assert_called_once()

    async def test_notification_cancellation(self, scheduler):
        """
        Given: 예약된 알림이 있음
        When: 알림 취소를 요청함
        Then: 큐에서 제거되고 취소 상태로 업데이트됨
        """
        # Given
        notification_id = str(uuid4())
        scheduler.redis_queue.cancel = AsyncMock(return_value=True)
        scheduler.db.update_notification_status = AsyncMock()

        # When
        result = await scheduler.cancel_notification(notification_id)

        # Then
        assert result.success is True
        scheduler.redis_queue.cancel.assert_called_once_with(notification_id)
        scheduler.db.update_notification_status.assert_called_once()

    async def test_invalid_schedule_time_validation(self, scheduler):
        """
        Given: 과거 시간으로 알림 스케줄링 시도
        When: 스케줄링 요청을 처리함
        Then: InvalidScheduleTimeError가 발생함
        """
        # Given
        past_notification = ScheduledNotificationRequest(
            user_id=str(uuid4()),
            type=NotificationType.PREPARATION_REMINDER,
            scheduled_time=datetime.now() - timedelta(hours=1),  # 과거 시간
            message="과거 알림",
        )

        # When & Then
        with pytest.raises(InvalidScheduleTimeError):
            await scheduler.schedule_single_notification(past_notification)


class TestUserTargetingLogic:
    """Test suite for user targeting and personalization logic."""

    @pytest.fixture
    def targeting_service(self):
        """Create targeting service for testing."""
        from app.services.notifications.notification_scheduler import (
            UserTargetingService,
        )

        return UserTargetingService()

    async def test_personalized_timing_optimization(self, targeting_service):
        """
        Given: 사용자의 과거 알림 반응 데이터
        When: 개인화된 알림 시간을 계산함
        Then: 사용자의 활동 패턴에 맞는 시간이 반환됨
        """
        # Given
        user_id = str(uuid4())
        default_time = datetime.now().replace(hour=18, minute=0)

        # 사용자가 오후 7시에 가장 높은 반응률을 보임
        targeting_service.engagement_analyzer.get_optimal_hour = AsyncMock(
            return_value=19
        )

        # When
        optimized_time = await targeting_service.optimize_notification_timing(
            user_id=user_id,
            default_time=default_time,
            notification_type=NotificationType.PREPARATION_REMINDER,
        )

        # Then
        assert optimized_time.hour == 19  # 개인화된 시간
        assert optimized_time.minute == 0

    async def test_engagement_based_frequency_adjustment(self, targeting_service):
        """
        Given: 사용자의 알림 반응률 데이터
        When: 개인화된 빈도 제한을 계산함
        Then: 반응률에 따른 적절한 제한값이 반환됨
        """
        # Given
        high_engagement_user = str(uuid4())
        low_engagement_user = str(uuid4())

        targeting_service.engagement_analyzer.calculate_engagement_rate = AsyncMock(
            side_effect=lambda user_id: 0.8 if user_id == high_engagement_user else 0.2
        )

        # When
        high_limit = await targeting_service.get_personalized_frequency_limit(
            high_engagement_user
        )
        low_limit = await targeting_service.get_personalized_frequency_limit(
            low_engagement_user
        )

        # Then
        assert high_limit > low_limit  # 고반응 사용자는 더 많은 알림 허용
        assert high_limit <= 10  # 최대 제한
        assert low_limit >= 3  # 최소 제한

    async def test_contextual_notification_filtering(self, targeting_service):
        """
        Given: 사용자의 현재 상황과 설정
        When: 알림 발송 여부를 결정함
        Then: 컨텍스트를 고려한 적절한 판단이 내려짐
        """
        # Given
        user_id = str(uuid4())
        notification = ScheduledNotificationRequest(
            user_id=user_id,
            type=NotificationType.PREPARATION_REMINDER,
            scheduled_time=datetime.now(),
            message="내일 데이트 준비",
        )

        # 사용자가 현재 앱을 사용 중이고 높은 참여도를 보임
        targeting_service.user_context_service.is_user_active = AsyncMock(
            return_value=True
        )
        targeting_service.engagement_analyzer.predict_engagement_probability = (
            AsyncMock(return_value=0.7)
        )

        # When
        should_send = await targeting_service.should_send_notification(notification)

        # Then
        assert should_send is True
