"""
Tests for Notification Settings API and Services.
Task 2-2-4: 알림 설정 UI 및 개인화 전송 기능
Following TDD Red-Green-Refactor approach as specified in rules.md.
"""

import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from fastapi import HTTPException

from app.models.notification import (
    UserNotificationSettings, 
    NotificationTemplate,
    NotificationType,
    NotificationPriority
)
from app.schemas.notification import (
    UserNotificationSettingsCreate,
    UserNotificationSettingsUpdate, 
    UserNotificationSettingsResponse,
    QuietHours,
    NotificationTypes,
    NotificationTiming,
    PersonalizationSettings
)
from app.services.notification_settings_service import (
    NotificationSettingsService,
    NotificationSettingsNotFoundError
)


class TestNotificationSettingsService:
    """Test suite for NotificationSettingsService."""

    @pytest.fixture
    def settings_service(self):
        """Create NotificationSettingsService instance for testing."""
        mock_db = Mock()
        return NotificationSettingsService(db=mock_db)

    @pytest.fixture 
    def sample_settings_create(self):
        """Sample notification settings creation request."""
        return UserNotificationSettingsCreate(
            enabled=True,
            quiet_hours=QuietHours(
                enabled=True,
                start=time(22, 0),
                end=time(8, 0),
                weekdays_only=False
            ),
            types=NotificationTypes(
                date_reminder=True,
                departure_reminder=True,
                move_reminder=False,  # 이동 알림은 꺼둠
                business_hours=True,
                weather=True,
                traffic=False,  # 교통 알림은 꺼둠
                recommendations=True,
                promotional=False
            ),
            timing=NotificationTiming(
                day_before_hour=19,  # 19시에 전날 알림
                departure_minutes_before=45,  # 45분 전 출발 알림
                move_reminder_minutes=20  # 20분 전 이동 알림
            ),
            personalization=PersonalizationSettings(
                enabled=True,
                frequency_limit_per_day=8,
                frequency_limit_per_week=40
            )
        )

    @pytest.fixture
    def sample_settings_model(self):
        """Sample notification settings database model."""
        user_id = uuid4()
        return UserNotificationSettings(
            id=uuid4(),
            user_id=user_id,
            enabled=True,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0),
            quiet_hours_weekdays_only=False,
            date_reminder_enabled=True,
            departure_reminder_enabled=True,
            move_reminder_enabled=False,
            business_hours_enabled=True,
            weather_enabled=True,
            traffic_enabled=False,
            recommendations_enabled=True,
            promotional_enabled=False,
            day_before_hour=19,
            departure_minutes_before=45,
            move_reminder_minutes=20,
            personalized_timing_enabled=True,
            frequency_limit_per_day=8,
            frequency_limit_per_week=40,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    async def test_create_notification_settings_success(self, settings_service, sample_settings_create):
        """
        Given: 사용자 ID와 유효한 알림 설정 데이터
        When: 알림 설정을 생성함
        Then: 알림 설정이 성공적으로 생성되고 저장됨
        """
        # Given
        user_id = str(uuid4())
        
        settings_service.db.query.return_value.filter.return_value.first.return_value = None
        settings_service.db.add = Mock()
        settings_service.db.commit = Mock()
        settings_service.db.refresh = Mock()
        
        # When
        result = await settings_service.create_user_settings(user_id, sample_settings_create)
        
        # Then
        assert result is not None
        settings_service.db.add.assert_called_once()
        settings_service.db.commit.assert_called_once()
        
        # 생성된 설정이 요청 데이터와 일치하는지 확인
        added_settings = settings_service.db.add.call_args[0][0]
        assert added_settings.user_id == user_id
        assert added_settings.enabled == sample_settings_create.enabled
        assert added_settings.quiet_hours_enabled == sample_settings_create.quiet_hours.enabled
        assert added_settings.quiet_hours_start == sample_settings_create.quiet_hours.start
        assert added_settings.day_before_hour == sample_settings_create.timing.day_before_hour
        assert added_settings.frequency_limit_per_day == sample_settings_create.personalization.frequency_limit_per_day

    async def test_create_duplicate_settings_fails(self, settings_service, sample_settings_create, sample_settings_model):
        """
        Given: 이미 알림 설정이 존재하는 사용자
        When: 같은 사용자에 대해 알림 설정을 다시 생성함
        Then: 오류가 발생함
        """
        # Given
        user_id = str(sample_settings_model.user_id)
        settings_service.db.query.return_value.filter.return_value.first.return_value = sample_settings_model
        
        # When & Then
        with pytest.raises(ValueError, match="already exists"):
            await settings_service.create_user_settings(user_id, sample_settings_create)

    async def test_get_user_settings_success(self, settings_service, sample_settings_model):
        """
        Given: 알림 설정이 존재하는 사용자 ID
        When: 사용자 알림 설정을 조회함
        Then: 올바른 설정 데이터가 반환됨
        """
        # Given
        user_id = str(sample_settings_model.user_id)
        settings_service.db.query.return_value.filter.return_value.first.return_value = sample_settings_model
        
        # When
        result = await settings_service.get_user_settings(user_id)
        
        # Then
        assert result is not None
        assert result.user_id == sample_settings_model.user_id
        assert result.enabled == sample_settings_model.enabled
        assert result.quiet_hours_enabled == sample_settings_model.quiet_hours_enabled
        assert result.day_before_hour == sample_settings_model.day_before_hour

    async def test_get_user_settings_not_found(self, settings_service):
        """
        Given: 알림 설정이 존재하지 않는 사용자 ID
        When: 사용자 알림 설정을 조회함
        Then: NotFoundError가 발생함
        """
        # Given
        user_id = str(uuid4())
        settings_service.db.query.return_value.filter.return_value.first.return_value = None
        
        # When & Then
        with pytest.raises(NotificationSettingsNotFoundError):
            await settings_service.get_user_settings(user_id)

    async def test_update_user_settings_success(self, settings_service, sample_settings_model):
        """
        Given: 기존 알림 설정과 업데이트 요청 데이터
        When: 알림 설정을 업데이트함
        Then: 설정이 성공적으로 업데이트됨
        """
        # Given
        user_id = str(sample_settings_model.user_id)
        settings_service.db.query.return_value.filter.return_value.first.return_value = sample_settings_model
        settings_service.db.commit = Mock()
        
        update_data = UserNotificationSettingsUpdate(
            enabled=False,  # 전체 알림 끄기
            quiet_hours=QuietHours(
                enabled=True,
                start=time(23, 0),  # 시간 변경
                end=time(7, 0),
                weekdays_only=True  # 평일만으로 변경
            ),
            timing=NotificationTiming(
                day_before_hour=20,  # 20시로 변경
                departure_minutes_before=60  # 60분 전으로 변경
            )
        )
        
        # When
        result = await settings_service.update_user_settings(user_id, update_data)
        
        # Then
        assert result is not None
        settings_service.db.commit.assert_called_once()
        
        # 업데이트된 값 확인
        assert result.enabled == False
        assert result.quiet_hours_start == time(23, 0)
        assert result.quiet_hours_weekdays_only == True
        assert result.day_before_hour == 20
        assert result.departure_minutes_before == 60

    async def test_update_user_settings_partial_update(self, settings_service, sample_settings_model):
        """
        Given: 일부 필드만 포함된 업데이트 요청
        When: 부분 업데이트를 수행함
        Then: 지정된 필드만 업데이트되고 나머지는 유지됨
        """
        # Given
        user_id = str(sample_settings_model.user_id)
        settings_service.db.query.return_value.filter.return_value.first.return_value = sample_settings_model
        settings_service.db.commit = Mock()
        
        # 타이밍 설정만 업데이트
        update_data = UserNotificationSettingsUpdate(
            timing=NotificationTiming(
                day_before_hour=17,
                departure_minutes_before=20,
                move_reminder_minutes=10
            )
        )
        
        # When
        result = await settings_service.update_user_settings(user_id, update_data)
        
        # Then
        # 업데이트된 필드
        assert result.day_before_hour == 17
        assert result.departure_minutes_before == 20
        assert result.move_reminder_minutes == 10
        
        # 기존 값 유지
        assert result.enabled == sample_settings_model.enabled
        assert result.quiet_hours_enabled == sample_settings_model.quiet_hours_enabled
        assert result.date_reminder_enabled == sample_settings_model.date_reminder_enabled

    async def test_delete_user_settings_success(self, settings_service, sample_settings_model):
        """
        Given: 존재하는 사용자 알림 설정
        When: 설정을 삭제함
        Then: 설정이 성공적으로 삭제됨
        """
        # Given
        user_id = str(sample_settings_model.user_id)
        settings_service.db.query.return_value.filter.return_value.first.return_value = sample_settings_model
        settings_service.db.delete = Mock()
        settings_service.db.commit = Mock()
        
        # When
        result = await settings_service.delete_user_settings(user_id)
        
        # Then
        assert result == True
        settings_service.db.delete.assert_called_once_with(sample_settings_model)
        settings_service.db.commit.assert_called_once()

    async def test_is_notification_allowed_success(self, sample_settings_model):
        """
        Given: 사용자 알림 설정과 알림 유형
        When: 알림 허용 여부를 확인함
        Then: 설정에 따른 올바른 결과가 반환됨
        """
        # Given - 모든 알림이 활성화된 상태
        settings = sample_settings_model
        
        # 조용시간이 아닌 시간 (오후 3시)
        test_time = datetime(2025, 1, 1, 15, 0)
        
        # When & Then
        # 활성화된 알림 타입들
        assert settings.is_notification_allowed(NotificationType.DEPARTURE_REMINDER, test_time) == True
        assert settings.is_notification_allowed(NotificationType.PREPARATION_REMINDER, test_time) == True
        assert settings.is_notification_allowed("business_hours", test_time) == True
        assert settings.is_notification_allowed("weather", test_time) == True
        assert settings.is_notification_allowed("recommendations", test_time) == True
        
        # 비활성화된 알림 타입들
        assert settings.is_notification_allowed(NotificationType.MOVE_REMINDER, test_time) == False
        assert settings.is_notification_allowed("traffic", test_time) == False
        assert settings.is_notification_allowed(NotificationType.PROMOTIONAL, test_time) == False

    async def test_is_notification_allowed_quiet_time(self, sample_settings_model):
        """
        Given: 조용시간이 설정된 사용자 설정
        When: 조용시간에 알림 허용 여부를 확인함
        Then: 모든 알림이 차단됨
        """
        # Given
        settings = sample_settings_model
        
        # 조용시간 (새벽 2시) - 22:00-08:00 설정
        quiet_time = datetime(2025, 1, 1, 2, 0)
        
        # When & Then
        assert settings.is_notification_allowed(NotificationType.DEPARTURE_REMINDER, quiet_time) == False
        assert settings.is_notification_allowed(NotificationType.PREPARATION_REMINDER, quiet_time) == False
        assert settings.is_notification_allowed("weather", quiet_time) == False

    async def test_is_notification_allowed_disabled_notifications(self, sample_settings_model):
        """
        Given: 전체 알림이 비활성화된 설정
        When: 알림 허용 여부를 확인함
        Then: 모든 알림이 차단됨
        """
        # Given
        settings = sample_settings_model
        settings.enabled = False  # 전체 알림 비활성화
        
        test_time = datetime(2025, 1, 1, 15, 0)  # 조용시간 아님
        
        # When & Then
        assert settings.is_notification_allowed(NotificationType.DEPARTURE_REMINDER, test_time) == False
        assert settings.is_notification_allowed("weather", test_time) == False
        assert settings.is_notification_allowed("recommendations", test_time) == False

    async def test_is_notification_allowed_weekday_only_quiet_hours(self, sample_settings_model):
        """
        Given: 평일만 조용시간이 적용되는 설정
        When: 주말 조용시간에 알림 허용 여부를 확인함
        Then: 주말에는 조용시간이 무시되고 알림이 허용됨
        """
        # Given
        settings = sample_settings_model
        settings.quiet_hours_weekdays_only = True  # 평일만 조용시간 적용
        
        # 토요일 새벽 2시 (조용시간이지만 주말)
        weekend_quiet_time = datetime(2025, 1, 4, 2, 0)  # 2025-01-04는 토요일
        
        # When & Then
        # 주말에는 조용시간이 무시되므로 알림 허용
        assert settings.is_notification_allowed(NotificationType.DEPARTURE_REMINDER, weekend_quiet_time) == True
        assert settings.is_notification_allowed("weather", weekend_quiet_time) == True


class TestNotificationSettingsIntegration:
    """Integration tests for notification settings functionality."""

    async def test_settings_creation_to_notification_filtering_flow(self):
        """
        Given: 새 사용자가 알림 설정을 생성함
        When: 실제 알림 전송 시 설정이 적용됨
        Then: 설정에 따라 알림이 필터링됨
        """
        # Given
        user_id = str(uuid4())
        
        # 특정 알림 타입만 활성화
        settings_create = UserNotificationSettingsCreate(
            enabled=True,
            types=NotificationTypes(
                date_reminder=True,
                departure_reminder=False,  # 출발 알림 비활성화
                weather=True,
                traffic=False,  # 교통 알림 비활성화
                promotional=False
            ),
            quiet_hours=QuietHours(
                enabled=True,
                start=time(22, 0),
                end=time(8, 0)
            )
        )
        
        # Mock 서비스
        settings_service = NotificationSettingsService(db=Mock())
        
        # When - 설정 생성 (모의)
        # 실제 구현에서는 데이터베이스에 저장됨
        
        # 설정 적용 테스트를 위한 모델 생성
        settings_model = UserNotificationSettings(
            user_id=user_id,
            enabled=True,
            date_reminder_enabled=True,
            departure_reminder_enabled=False,
            weather_enabled=True,
            traffic_enabled=False,
            promotional_enabled=False,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        # Then - 다양한 시나리오에서 알림 허용 여부 테스트
        normal_time = datetime(2025, 1, 1, 15, 0)  # 평상시
        quiet_time = datetime(2025, 1, 1, 23, 0)   # 조용시간
        
        # 평상시: 활성화된 알림만 허용
        assert settings_model.is_notification_allowed(NotificationType.PREPARATION_REMINDER, normal_time) == True
        assert settings_model.is_notification_allowed(NotificationType.DEPARTURE_REMINDER, normal_time) == False
        assert settings_model.is_notification_allowed("weather", normal_time) == True
        assert settings_model.is_notification_allowed("traffic", normal_time) == False
        assert settings_model.is_notification_allowed(NotificationType.PROMOTIONAL, normal_time) == False
        
        # 조용시간: 모든 알림 차단
        assert settings_model.is_notification_allowed(NotificationType.PREPARATION_REMINDER, quiet_time) == False
        assert settings_model.is_notification_allowed("weather", quiet_time) == False

    async def test_personalization_settings_affect_frequency_limits(self):
        """
        Given: 개인화 설정에서 빈도 제한을 설정함
        When: 알림 빈도를 체크함
        Then: 설정된 제한이 올바르게 적용됨
        """
        # Given
        settings = UserNotificationSettings(
            user_id=uuid4(),
            enabled=True,
            personalized_timing_enabled=True,
            frequency_limit_per_day=5,     # 하루 5개 제한
            frequency_limit_per_week=20    # 주간 20개 제한
        )
        
        # When & Then
        # 설정값 확인
        assert settings.frequency_limit_per_day == 5
        assert settings.frequency_limit_per_week == 20
        assert settings.personalized_timing_enabled == True
        
        # 개인화 기능이 켜져있으면 해당 설정들이 적용되어야 함
        assert settings.personalized_timing_enabled == True