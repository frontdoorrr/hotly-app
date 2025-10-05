"""Test cases for notification service functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.models.notification import NotificationStatus, NotificationType
from app.schemas.notification import (
    NotificationCreate,
    UserNotificationPreferenceUpdate,
)
from app.services.notifications.notification_service import NotificationService


class TestNotificationService:
    """Test cases for NotificationService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def notification_service(self, mock_db):
        """Create NotificationService instance."""
        return NotificationService(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def sample_notification_data(self):
        """Sample notification data."""
        return NotificationCreate(
            title="Test Notification",
            body="This is a test notification body",
            notification_type=NotificationType.PLACE_RECOMMENDATION.value,
            category="recommendation",
            priority="normal",
            target_user_ids=["user1", "user2"],
            data={"place_id": "123", "category": "restaurant"},
        )

    def test_create_notification_success(
        self, notification_service, sample_notification_data
    ):
        """Test successful notification creation."""
        # Given
        mock_notification = Mock()
        mock_notification.id = uuid4()

        notification_service.db.add = Mock()
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        with patch(
            "app.services.notification_service.Notification",
            return_value=mock_notification,
        ):
            with patch(
                "app.schemas.notification.NotificationResponse"
            ) as mock_response:
                mock_response.from_orm.return_value = Mock(id=mock_notification.id)

                # When
                notification_service.create_notification(sample_notification_data)

        # Then
        notification_service.db.add.assert_called_once_with(mock_notification)
        notification_service.db.commit.assert_called_once()
        notification_service.db.refresh.assert_called_once_with(mock_notification)
        assert mock_notification.status == NotificationStatus.DRAFT.value

    def test_create_notification_failure(
        self, notification_service, sample_notification_data
    ):
        """Test notification creation failure."""
        # Given
        notification_service.db.add.side_effect = Exception("Database error")
        notification_service.db.rollback = Mock()

        # When & Then
        with pytest.raises(Exception, match="Database error"):
            notification_service.create_notification(sample_notification_data)

        notification_service.db.rollback.assert_called_once()

    def test_get_notification_history_success(self, notification_service):
        """Test successful notification history retrieval."""
        # Given
        mock_notifications = [
            Mock(
                id=uuid4(),
                title="Notification 1",
                notification_type="general",
                status="sent",
                created_at=datetime.utcnow() - timedelta(days=1),
            ),
            Mock(
                id=uuid4(),
                title="Notification 2",
                notification_type="reminder",
                status="sent",
                created_at=datetime.utcnow() - timedelta(days=2),
            ),
        ]

        notification_service.db.query().filter().order_by().offset().limit().all.return_value = (
            mock_notifications
        )

        with patch("app.schemas.notification.NotificationResponse") as mock_response:
            mock_response.from_orm.side_effect = lambda n: Mock(id=n.id, title=n.title)

            # When
            result = notification_service.get_notification_history(
                notification_type="general", status="sent", days=7
            )

        # Then
        assert len(result) == 2
        mock_response.from_orm.assert_called()

    def test_get_notification_history_with_filters(self, notification_service):
        """Test notification history with type and status filters."""
        # Given
        notification_service.db.query().filter().order_by().offset().limit().all.return_value = (
            []
        )

        # When
        result = notification_service.get_notification_history(
            notification_type="onboarding", status="sent", days=30, skip=10, limit=20
        )

        # Then
        assert result == []
        # Verify that filters were applied (would check query in real implementation)

    def test_get_user_preferences_existing(self, notification_service, sample_user_id):
        """Test getting existing user preferences."""
        # Given
        mock_preferences = Mock()
        mock_preferences.user_id = sample_user_id
        mock_preferences.push_notifications_enabled = True

        notification_service.db.query().filter().first.return_value = mock_preferences

        with patch(
            "app.schemas.notification.UserNotificationPreferenceResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(user_id=sample_user_id)

            # When
            notification_service.get_user_preferences(sample_user_id)

        # Then
        mock_response.from_orm.assert_called_once_with(mock_preferences)

    def test_get_user_preferences_create_default(
        self, notification_service, sample_user_id
    ):
        """Test creating default preferences for new user."""
        # Given
        notification_service.db.query().filter().first.return_value = None
        notification_service._create_default_preferences = Mock(return_value=Mock())

        with patch(
            "app.schemas.notification.UserNotificationPreferenceResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(user_id=sample_user_id)

            # When
            notification_service.get_user_preferences(sample_user_id)

        # Then
        notification_service._create_default_preferences.assert_called_once_with(
            sample_user_id
        )

    def test_update_user_preferences_success(
        self, notification_service, sample_user_id
    ):
        """Test successful user preferences update."""
        # Given
        mock_preferences = Mock()
        mock_preferences.user_id = sample_user_id

        notification_service.db.query().filter().first.return_value = mock_preferences
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        preferences_update = UserNotificationPreferenceUpdate(
            push_notifications_enabled=False,
            promotional_notifications=True,
            quiet_hours_enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=7,
        )

        with patch(
            "app.schemas.notification.UserNotificationPreferenceResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(user_id=sample_user_id)

            # When
            result = notification_service.update_user_preferences(
                sample_user_id, preferences_update
            )

        # Then
        assert mock_preferences.push_notifications_enabled is False
        assert mock_preferences.promotional_notifications is True
        assert mock_preferences.quiet_hours_enabled is True
        assert mock_preferences.quiet_hours_start == 22
        assert mock_preferences.quiet_hours_end == 7
        notification_service.db.commit.assert_called_once()

    def test_update_user_preferences_create_if_not_exists(
        self, notification_service, sample_user_id
    ):
        """Test creating preferences if they don't exist during update."""
        # Given
        notification_service.db.query().filter().first.return_value = None
        mock_new_preferences = Mock()
        notification_service._create_default_preferences = Mock(
            return_value=mock_new_preferences
        )
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        preferences_update = UserNotificationPreferenceUpdate(
            push_notifications_enabled=False
        )

        with patch(
            "app.schemas.notification.UserNotificationPreferenceResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(user_id=sample_user_id)

            # When
            result = notification_service.update_user_preferences(
                sample_user_id, preferences_update
            )

        # Then
        notification_service._create_default_preferences.assert_called_once_with(
            sample_user_id
        )
        assert mock_new_preferences.push_notifications_enabled is False

    def test_create_default_preferences(self, notification_service, sample_user_id):
        """Test creating default user preferences."""
        # Given
        notification_service.db.add = Mock()
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        # When
        result = notification_service._create_default_preferences(sample_user_id)

        # Then
        assert result.user_id == sample_user_id
        assert result.push_notifications_enabled is True
        assert result.promotional_notifications is False  # Opt-in only
        assert result.preferred_language == "ko"
        assert result.timezone == "Asia/Seoul"
        notification_service.db.add.assert_called_once()
        notification_service.db.commit.assert_called_once()

    def test_can_send_notification_allowed(self, notification_service, sample_user_id):
        """Test notification permission check - allowed."""
        # Given
        mock_preferences = Mock()
        mock_preferences.push_notifications_enabled = True
        mock_preferences.is_notification_type_enabled.return_value = True
        mock_preferences.is_in_quiet_hours.return_value = False
        mock_preferences.max_daily_notifications = 10

        notification_service.db.query().filter().first.return_value = mock_preferences
        notification_service.db.query().filter().count.return_value = 5  # Below limit

        # When
        result = notification_service.can_send_notification(
            sample_user_id, "place_recommendation", current_hour=14
        )

        # Then
        assert result["can_send"] is True
        assert result["reason"] == "allowed"

    def test_can_send_notification_push_disabled(
        self, notification_service, sample_user_id
    ):
        """Test notification permission check - push disabled."""
        # Given
        mock_preferences = Mock()
        mock_preferences.push_notifications_enabled = False

        notification_service.db.query().filter().first.return_value = mock_preferences

        # When
        result = notification_service.can_send_notification(
            sample_user_id, "place_recommendation"
        )

        # Then
        assert result["can_send"] is False
        assert result["reason"] == "push_disabled"

    def test_can_send_notification_type_disabled(
        self, notification_service, sample_user_id
    ):
        """Test notification permission check - notification type disabled."""
        # Given
        mock_preferences = Mock()
        mock_preferences.push_notifications_enabled = True
        mock_preferences.is_notification_type_enabled.return_value = False

        notification_service.db.query().filter().first.return_value = mock_preferences

        # When
        result = notification_service.can_send_notification(
            sample_user_id, "promotional"
        )

        # Then
        assert result["can_send"] is False
        assert result["reason"] == "type_disabled"

    def test_can_send_notification_quiet_hours(
        self, notification_service, sample_user_id
    ):
        """Test notification permission check - in quiet hours."""
        # Given
        mock_preferences = Mock()
        mock_preferences.push_notifications_enabled = True
        mock_preferences.is_notification_type_enabled.return_value = True
        mock_preferences.is_in_quiet_hours.return_value = True

        notification_service.db.query().filter().first.return_value = mock_preferences

        # When
        result = notification_service.can_send_notification(
            sample_user_id, "reminder", current_hour=23
        )

        # Then
        assert result["can_send"] is False
        assert result["reason"] == "quiet_hours"

    def test_can_send_notification_daily_limit_exceeded(
        self, notification_service, sample_user_id
    ):
        """Test notification permission check - daily limit exceeded."""
        # Given
        mock_preferences = Mock()
        mock_preferences.push_notifications_enabled = True
        mock_preferences.is_notification_type_enabled.return_value = True
        mock_preferences.is_in_quiet_hours.return_value = False
        mock_preferences.max_daily_notifications = 5

        notification_service.db.query().filter().first.return_value = mock_preferences
        notification_service.db.query().filter().count.return_value = 5  # At limit

        # When
        result = notification_service.can_send_notification(sample_user_id, "reminder")

        # Then
        assert result["can_send"] is False
        assert result["reason"] == "daily_limit_exceeded"

    def test_can_send_notification_no_preferences(
        self, notification_service, sample_user_id
    ):
        """Test notification permission check - no preferences (default allow)."""
        # Given
        notification_service.db.query().filter().first.return_value = None

        # When
        result = notification_service.can_send_notification(sample_user_id, "general")

        # Then
        assert result["can_send"] is True
        assert result["reason"] == "default_allowed"

    def test_get_notification_stats_by_user(self, notification_service, sample_user_id):
        """Test getting notification statistics for specific user."""
        # Given
        mock_notifications = [
            Mock(notification_type="onboarding", status="sent"),
            Mock(notification_type="recommendation", status="sent"),
            Mock(notification_type="onboarding", status="failed"),
            Mock(notification_type="reminder", status="sent"),
        ]

        notification_service.db.query().filter().all.return_value = mock_notifications

        # When
        result = notification_service.get_notification_stats_by_user(
            sample_user_id, days=30
        )

        # Then
        assert result["user_id"] == sample_user_id
        assert result["period_days"] == 30
        assert result["total_notifications"] == 4
        assert result["by_type"]["onboarding"] == 2
        assert result["by_type"]["recommendation"] == 1
        assert result["by_type"]["reminder"] == 1
        assert result["by_status"]["sent"] == 3
        assert result["by_status"]["failed"] == 1

    def test_mark_notification_as_read_success(
        self, notification_service, sample_user_id
    ):
        """Test marking notification as read."""
        # Given
        notification_id = str(uuid4())

        # When
        result = notification_service.mark_notification_as_read(
            notification_id, sample_user_id
        )

        # Then
        assert result is True

    def test_schedule_notification_success(
        self, notification_service, sample_notification_data
    ):
        """Test scheduling notification for future delivery."""
        # Given
        scheduled_time = datetime.utcnow() + timedelta(hours=2)

        notification_service.create_notification = Mock()
        mock_notification_response = Mock()
        mock_notification_response.id = uuid4()
        notification_service.create_notification.return_value = (
            mock_notification_response
        )

        mock_notification_record = Mock()
        notification_service.db.query().filter().first.return_value = (
            mock_notification_record
        )
        notification_service.db.commit = Mock()

        # When
        result = notification_service.schedule_notification(
            sample_notification_data, scheduled_time
        )

        # Then
        assert result == mock_notification_response
        assert mock_notification_record.status == NotificationStatus.SCHEDULED.value
        notification_service.db.commit.assert_called_once()

    def test_get_scheduled_notifications_success(self, notification_service):
        """Test getting scheduled notifications due for sending."""
        # Given
        due_time = datetime.utcnow() + timedelta(minutes=30)

        mock_notifications = [
            Mock(
                id=uuid4(),
                status=NotificationStatus.SCHEDULED.value,
                scheduled_at=datetime.utcnow() + timedelta(minutes=15),
            ),
            Mock(
                id=uuid4(),
                status=NotificationStatus.SCHEDULED.value,
                scheduled_at=datetime.utcnow() + timedelta(minutes=25),
            ),
        ]

        notification_service.db.query().filter().all.return_value = mock_notifications

        with patch("app.schemas.notification.NotificationResponse") as mock_response:
            mock_response.from_orm.side_effect = lambda n: Mock(id=n.id)

            # When
            result = notification_service.get_scheduled_notifications(
                due_before=due_time
            )

        # Then
        assert len(result) == 2
        mock_response.from_orm.assert_called()


@pytest.mark.integration
class TestNotificationServiceIntegration:
    """Integration tests for notification service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def notification_service(self, mock_db):
        """Create notification service for integration testing."""
        return NotificationService(db=mock_db)

    def test_complete_user_preference_workflow_e2e(self, notification_service):
        """Test complete user preference management workflow."""
        # Given
        user_id = str(uuid4())

        # Mock initial state (no preferences)
        notification_service.db.query().filter().first.return_value = None
        notification_service.db.add = Mock()
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        # When - Step 1: Get preferences (should create default)
        with patch(
            "app.schemas.notification.UserNotificationPreferenceResponse"
        ) as mock_response:
            mock_response.from_orm.return_value = Mock(
                user_id=user_id,
                push_notifications_enabled=True,
                promotional_notifications=False,
            )

            initial_prefs = notification_service.get_user_preferences(user_id)

        # When - Step 2: Update preferences
        mock_existing_prefs = Mock()
        notification_service.db.query().filter().first.return_value = (
            mock_existing_prefs
        )

        preferences_update = UserNotificationPreferenceUpdate(
            promotional_notifications=True,
            quiet_hours_enabled=True,
            quiet_hours_start=22,
            quiet_hours_end=7,
            max_daily_notifications=5,
        )

        updated_prefs = notification_service.update_user_preferences(
            user_id, preferences_update
        )

        # When - Step 3: Check notification permissions
        mock_existing_prefs.push_notifications_enabled = True
        mock_existing_prefs.is_notification_type_enabled.return_value = True
        mock_existing_prefs.is_in_quiet_hours.return_value = False
        mock_existing_prefs.max_daily_notifications = 5

        notification_service.db.query().filter().count.return_value = 2

        permission_result = notification_service.can_send_notification(
            user_id, "promotional", current_hour=14
        )

        # When - Step 4: Get user stats
        mock_notifications = [
            Mock(notification_type="promotional", status="sent"),
            Mock(notification_type="reminder", status="sent"),
        ]
        notification_service.db.query().filter().all.return_value = mock_notifications

        stats = notification_service.get_notification_stats_by_user(user_id, days=7)

        # Then
        assert initial_prefs.user_id == user_id
        assert updated_prefs is not None
        assert permission_result["can_send"] is True
        assert stats["total_notifications"] == 2
        assert stats["by_type"]["promotional"] == 1

    def test_notification_lifecycle_management_e2e(self, notification_service):
        """Test complete notification lifecycle management."""
        # Given
        notification_data = NotificationCreate(
            title="Lifecycle Test",
            body="Testing notification lifecycle",
            notification_type="reminder",
            target_user_ids=["user1", "user2"],
            data={"reminder_type": "visit_place"},
        )

        # Mock database operations
        mock_notification = Mock()
        mock_notification.id = uuid4()
        notification_service.db.add = Mock()
        notification_service.db.commit = Mock()
        notification_service.db.refresh = Mock()

        # When - Step 1: Create notification
        with patch(
            "app.services.notification_service.Notification",
            return_value=mock_notification,
        ):
            with patch(
                "app.schemas.notification.NotificationResponse"
            ) as mock_response:
                mock_response.from_orm.return_value = Mock(id=mock_notification.id)

                created_notification = notification_service.create_notification(
                    notification_data
                )

        # When - Step 2: Schedule future notification
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        notification_service.create_notification = Mock(
            return_value=created_notification
        )

        mock_scheduled_record = Mock()
        notification_service.db.query().filter().first.return_value = (
            mock_scheduled_record
        )

        scheduled_notification = notification_service.schedule_notification(
            notification_data, scheduled_time
        )

        # When - Step 3: Get scheduled notifications
        mock_due_notifications = [mock_scheduled_record]
        notification_service.db.query().filter().all.return_value = (
            mock_due_notifications
        )

        with patch("app.schemas.notification.NotificationResponse") as mock_response:
            mock_response.from_orm.return_value = Mock(id=mock_notification.id)

            due_notifications = notification_service.get_scheduled_notifications(
                due_before=datetime.utcnow() + timedelta(hours=2)
            )

        # When - Step 4: Get notification history
        notification_service.db.query().filter().order_by().offset().limit().all.return_value = [
            mock_notification
        ]

        with patch("app.schemas.notification.NotificationResponse") as mock_response:
            mock_response.from_orm.return_value = Mock(id=mock_notification.id)

            history = notification_service.get_notification_history(days=1)

        # Then
        assert created_notification.id == mock_notification.id
        assert scheduled_notification.id == mock_notification.id
        assert mock_scheduled_record.status == NotificationStatus.SCHEDULED.value
        assert len(due_notifications) == 1
        assert len(history) == 1
