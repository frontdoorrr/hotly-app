"""Test cases for FCM service functionality."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.services.fcm_service import FCMService, PushNotificationRequest


class TestFCMService:
    """Test cases for FCMService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def fcm_service(self, mock_db):
        """Create FCMService instance."""
        with patch("app.services.fcm_service.FCMService._initialize_firebase"):
            return FCMService(db=mock_db)

    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing."""
        return str(uuid4())

    @pytest.fixture
    def sample_device_token(self):
        """Sample FCM device token."""
        return "sample_fcm_token_123456789"

    @pytest.fixture
    def sample_device_info(self):
        """Sample device information."""
        return {
            "platform": "ios",
            "model": "iPhone 13",
            "version": "15.0",
            "app_version": "1.0.0",
        }

    def test_register_device_token_new_device(
        self, fcm_service, sample_user_id, sample_device_token, sample_device_info
    ):
        """Test registering new device token."""
        # Given
        fcm_service.db.query().filter().first.return_value = None
        fcm_service.db.add = Mock()
        fcm_service.db.commit = Mock()
        fcm_service.db.refresh = Mock()

        # When
        result = fcm_service.register_device_token(
            sample_user_id, sample_device_token, sample_device_info
        )

        # Then
        assert result["success"] is True
        assert result["is_new"] is True
        assert "device_id" in result
        fcm_service.db.add.assert_called_once()
        fcm_service.db.commit.assert_called_once()

    def test_register_device_token_existing_device(
        self, fcm_service, sample_user_id, sample_device_token, sample_device_info
    ):
        """Test updating existing device token."""
        # Given
        mock_device = Mock()
        mock_device.id = uuid4()
        fcm_service.db.query().filter().first.return_value = mock_device
        fcm_service.db.commit = Mock()

        # When
        result = fcm_service.register_device_token(
            sample_user_id, sample_device_token, sample_device_info
        )

        # Then
        assert result["success"] is True
        assert result["is_new"] is False
        assert mock_device.is_active is True
        assert mock_device.device_info == sample_device_info
        fcm_service.db.commit.assert_called_once()

    def test_register_device_token_failure(
        self, fcm_service, sample_user_id, sample_device_token
    ):
        """Test device token registration failure."""
        # Given
        fcm_service.db.query.side_effect = Exception("Database error")
        fcm_service.db.rollback = Mock()

        # When
        result = fcm_service.register_device_token(sample_user_id, sample_device_token)

        # Then
        assert result["success"] is False
        assert "error" in result
        fcm_service.db.rollback.assert_called_once()

    def test_unregister_device_token_success(
        self, fcm_service, sample_user_id, sample_device_token
    ):
        """Test successful device token unregistration."""
        # Given
        mock_device = Mock()
        fcm_service.db.query().filter().first.return_value = mock_device
        fcm_service.db.commit = Mock()

        # When
        result = fcm_service.unregister_device_token(
            sample_user_id, sample_device_token
        )

        # Then
        assert result["success"] is True
        assert mock_device.is_active is False
        assert mock_device.unregistered_at is not None
        fcm_service.db.commit.assert_called_once()

    def test_unregister_device_token_not_found(
        self, fcm_service, sample_user_id, sample_device_token
    ):
        """Test unregistering non-existent device token."""
        # Given
        fcm_service.db.query().filter().first.return_value = None

        # When
        result = fcm_service.unregister_device_token(
            sample_user_id, sample_device_token
        )

        # Then
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_user_device_tokens_success(self, fcm_service, sample_user_id):
        """Test retrieving user device tokens."""
        # Given
        mock_devices = [
            Mock(fcm_token="token1"),
            Mock(fcm_token="token2"),
            Mock(fcm_token="token3"),
        ]
        fcm_service.db.query().filter().all.return_value = mock_devices

        # When
        tokens = fcm_service.get_user_device_tokens(sample_user_id)

        # Then
        assert len(tokens) == 3
        assert "token1" in tokens
        assert "token2" in tokens
        assert "token3" in tokens

    def test_get_user_device_tokens_empty(self, fcm_service, sample_user_id):
        """Test retrieving device tokens for user with no devices."""
        # Given
        fcm_service.db.query().filter().all.return_value = []

        # When
        tokens = fcm_service.get_user_device_tokens(sample_user_id)

        # Then
        assert tokens == []

    def test_get_user_device_tokens_error(self, fcm_service, sample_user_id):
        """Test error handling in device token retrieval."""
        # Given
        fcm_service.db.query.side_effect = Exception("Database error")

        # When
        tokens = fcm_service.get_user_device_tokens(sample_user_id)

        # Then
        assert tokens == []

    def test_send_push_notification_success(self, fcm_service):
        """Test successful push notification sending."""
        # Given
        request = PushNotificationRequest(
            title="Test Notification",
            body="This is a test notification",
            user_ids=["user1", "user2"],
            data={"key": "value"},
        )

        fcm_service.get_user_device_tokens = Mock(return_value=["token1", "token2"])

        mock_response = Mock()
        mock_response.success_count = 2
        mock_response.failure_count = 0
        mock_response.responses = [Mock(success=True), Mock(success=True)]

        with patch(
            "firebase_admin.messaging.send_multicast", return_value=mock_response
        ):
            fcm_service._record_notification = Mock()

            # When
            result = fcm_service.send_push_notification(request)

        # Then
        assert result.success is True
        assert result.success_count == 2
        assert result.failure_count == 0
        fcm_service._record_notification.assert_called_once()

    def test_send_push_notification_no_tokens(self, fcm_service):
        """Test push notification sending with no device tokens."""
        # Given
        request = PushNotificationRequest(
            title="Test Notification",
            body="This is a test notification",
            user_ids=["user1"],
        )

        fcm_service.get_user_device_tokens = Mock(return_value=[])

        # When
        result = fcm_service.send_push_notification(request)

        # Then
        assert result.success is False
        assert "No active device tokens found" in result.error
        assert result.failure_count == 1

    def test_send_push_notification_partial_failure(self, fcm_service):
        """Test push notification sending with partial failures."""
        # Given
        request = PushNotificationRequest(
            title="Test Notification",
            body="This is a test notification",
            user_ids=["user1", "user2"],
        )

        fcm_service.get_user_device_tokens = Mock(return_value=["token1", "token2"])

        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 1
        mock_response.responses = [
            Mock(success=True),
            Mock(success=False, exception=Exception("Invalid token")),
        ]

        with patch(
            "firebase_admin.messaging.send_multicast", return_value=mock_response
        ):
            fcm_service._record_notification = Mock()
            fcm_service._handle_invalid_tokens = Mock()

            # When
            result = fcm_service.send_push_notification(request)

        # Then
        assert result.success is True  # At least one success
        assert result.success_count == 1
        assert result.failure_count == 1
        assert len(result.failed_tokens) == 1
        fcm_service._handle_invalid_tokens.assert_called_once()

    def test_send_to_single_device_success(self, fcm_service, sample_device_token):
        """Test sending notification to single device."""
        # Given
        with patch("firebase_admin.messaging.send", return_value="message_id_123"):
            # When
            result = fcm_service.send_to_single_device(
                sample_device_token, "Title", "Body", {"key": "value"}
            )

        # Then
        assert result.success is True
        assert result.message_id == "message_id_123"
        assert result.success_count == 1

    def test_send_to_single_device_failure(self, fcm_service, sample_device_token):
        """Test sending notification to single device failure."""
        # Given
        with patch(
            "firebase_admin.messaging.send", side_effect=Exception("Send failed")
        ):
            # When
            result = fcm_service.send_to_single_device(
                sample_device_token, "Title", "Body"
            )

        # Then
        assert result.success is False
        assert "Send failed" in result.error
        assert result.failure_count == 1

    def test_build_fcm_message_basic(self, fcm_service, sample_device_token):
        """Test building basic FCM message."""
        # Given
        request = PushNotificationRequest(
            title="Test Title", body="Test Body", user_ids=["user1"]
        )

        # When
        message = fcm_service._build_fcm_message(request, sample_device_token)

        # Then
        assert message.token == sample_device_token
        assert message.notification.title == "Test Title"
        assert message.notification.body == "Test Body"
        assert message.data["notification_type"] == "general"

    def test_build_fcm_message_with_data(self, fcm_service, sample_device_token):
        """Test building FCM message with custom data."""
        # Given
        request = PushNotificationRequest(
            title="Test Title",
            body="Test Body",
            user_ids=["user1"],
            data={"custom_key": "custom_value"},
            action_url="https://example.com",
            image_url="https://example.com/image.jpg",
            priority="high",
        )

        # When
        message = fcm_service._build_fcm_message(request, sample_device_token)

        # Then
        assert message.notification.image == "https://example.com/image.jpg"
        assert message.data["custom_key"] == "custom_value"
        assert message.data["action_url"] == "https://example.com"
        assert message.android.priority == "high"

    def test_record_notification_success(self, fcm_service):
        """Test recording notification in database."""
        # Given
        request = PushNotificationRequest(
            title="Test Notification", body="Test Body", user_ids=["user1", "user2"]
        )

        fcm_service.db.add = Mock()
        fcm_service.db.commit = Mock()

        # When
        fcm_service._record_notification(request, success_count=2, failure_count=0)

        # Then
        fcm_service.db.add.assert_called_once()
        fcm_service.db.commit.assert_called_once()

    def test_handle_invalid_tokens(self, fcm_service):
        """Test handling invalid FCM tokens."""
        # Given
        failed_tokens = ["invalid_token1", "invalid_token2"]
        fcm_service.db.query().filter().update = Mock()
        fcm_service.db.commit = Mock()

        # When
        fcm_service._handle_invalid_tokens(failed_tokens)

        # Then
        fcm_service.db.query().filter().update.assert_called_once()
        fcm_service.db.commit.assert_called_once()

    def test_get_notification_stats_success(self, fcm_service):
        """Test getting notification statistics."""
        # Given
        mock_notifications = [
            Mock(
                success_count=10,
                failure_count=2,
                notification_type="onboarding",
                sent_at=datetime.utcnow() - timedelta(days=1),
            ),
            Mock(
                success_count=5,
                failure_count=1,
                notification_type="recommendation",
                sent_at=datetime.utcnow() - timedelta(days=2),
            ),
        ]

        fcm_service.db.query().filter().all.return_value = mock_notifications

        # When
        stats = fcm_service.get_notification_stats(days=7)

        # Then
        assert stats["period_days"] == 7
        assert stats["total_notifications_sent"] == 2
        assert stats["total_success_count"] == 15
        assert stats["total_failure_count"] == 3
        assert stats["success_rate"] == 15 / 18
        assert "onboarding" in stats["by_notification_type"]
        assert "recommendation" in stats["by_notification_type"]

    def test_get_notification_stats_error(self, fcm_service):
        """Test error handling in notification stats."""
        # Given
        fcm_service.db.query.side_effect = Exception("Database error")

        # When
        stats = fcm_service.get_notification_stats()

        # Then
        assert "error" in stats
        assert "Database error" in stats["error"]

    def test_cleanup_expired_tokens_success(self, fcm_service):
        """Test cleaning up expired device tokens."""
        # Given
        cutoff_date = datetime.utcnow() - timedelta(days=30)

        mock_devices = [Mock(id=uuid4()) for _ in range(5)]
        fcm_service.db.query().filter().all.return_value = mock_devices
        fcm_service.db.query().filter().update = Mock()
        fcm_service.db.commit = Mock()

        # When
        result = fcm_service.cleanup_expired_tokens(days_inactive=30)

        # Then
        assert result["cleaned_up_count"] == 5
        assert "cutoff_date" in result
        fcm_service.db.commit.assert_called_once()

    def test_cleanup_expired_tokens_none_to_cleanup(self, fcm_service):
        """Test cleanup when no tokens need cleanup."""
        # Given
        fcm_service.db.query().filter().all.return_value = []
        fcm_service.db.commit = Mock()

        # When
        result = fcm_service.cleanup_expired_tokens(days_inactive=30)

        # Then
        assert result["cleaned_up_count"] == 0
        fcm_service.db.commit.assert_not_called()

    def test_cleanup_expired_tokens_error(self, fcm_service):
        """Test error handling in token cleanup."""
        # Given
        fcm_service.db.query.side_effect = Exception("Database error")
        fcm_service.db.rollback = Mock()

        # When
        result = fcm_service.cleanup_expired_tokens()

        # Then
        assert "error" in result
        assert "Database error" in result["error"]
        fcm_service.db.rollback.assert_called_once()


@pytest.mark.integration
class TestFCMServiceIntegration:
    """Integration tests for FCM service."""

    @pytest.fixture
    def mock_db(self):
        """Mock database for integration tests."""
        return Mock()

    @pytest.fixture
    def fcm_service(self, mock_db):
        """Create FCM service for integration testing."""
        with patch("app.services.fcm_service.FCMService._initialize_firebase"):
            return FCMService(db=mock_db)

    def test_complete_notification_flow_e2e(self, fcm_service):
        """Test complete end-to-end notification flow."""
        # Given
        user_id = str(uuid4())
        device_token = "integration_test_token"
        device_info = {"platform": "ios", "model": "iPhone"}

        # Mock database operations
        fcm_service.db.query().filter().first.return_value = None
        fcm_service.db.add = Mock()
        fcm_service.db.commit = Mock()
        fcm_service.db.refresh = Mock()
        fcm_service.db.query().filter().all.return_value = [
            Mock(fcm_token=device_token)
        ]

        # When - Step 1: Register device
        register_result = fcm_service.register_device_token(
            user_id, device_token, device_info
        )

        # When - Step 2: Send notification
        notification_request = PushNotificationRequest(
            title="Integration Test",
            body="This is an integration test notification",
            user_ids=[user_id],
            data={"test": "true"},
        )

        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 0
        mock_response.responses = [Mock(success=True)]

        with patch(
            "firebase_admin.messaging.send_multicast", return_value=mock_response
        ):
            fcm_service._record_notification = Mock()
            send_result = fcm_service.send_push_notification(notification_request)

        # When - Step 3: Get stats
        fcm_service.db.query().filter().all.return_value = [
            Mock(
                success_count=1,
                failure_count=0,
                notification_type="general",
                sent_at=datetime.utcnow(),
            )
        ]
        stats = fcm_service.get_notification_stats(days=1)

        # When - Step 4: Unregister device
        fcm_service.db.query().filter().first.return_value = Mock()
        unregister_result = fcm_service.unregister_device_token(user_id, device_token)

        # Then
        assert register_result["success"] is True
        assert register_result["is_new"] is True

        assert send_result.success is True
        assert send_result.success_count == 1
        assert send_result.failure_count == 0

        assert stats["total_success_count"] == 1
        assert stats["success_rate"] == 1.0

        assert unregister_result["success"] is True

    def test_bulk_notification_handling(self, fcm_service):
        """Test handling of bulk notifications."""
        # Given
        user_ids = [str(uuid4()) for _ in range(100)]
        device_tokens = [
            f"token_{i}" for i in range(150)
        ]  # Some users have multiple devices

        fcm_service.get_user_device_tokens = Mock(
            side_effect=lambda uid: [
                token for token in device_tokens if hash(uid + token) % 2 == 0
            ][:2]
        )  # Max 2 tokens per user

        notification_request = PushNotificationRequest(
            title="Bulk Notification",
            body="This is a bulk notification test",
            user_ids=user_ids,
            priority="normal",
        )

        # Mock successful sending
        mock_response = Mock()
        mock_response.success_count = 150
        mock_response.failure_count = 0
        mock_response.responses = [Mock(success=True) for _ in range(150)]

        with patch(
            "firebase_admin.messaging.send_multicast", return_value=mock_response
        ):
            fcm_service._record_notification = Mock()

            # When
            result = fcm_service.send_push_notification(notification_request)

        # Then
        assert result.success is True
        assert result.success_count == 150
        assert result.failure_count == 0
        fcm_service._record_notification.assert_called_once()

    def test_error_recovery_and_retry_simulation(self, fcm_service):
        """Test error recovery and retry scenarios."""
        # Given
        user_id = str(uuid4())
        device_tokens = ["valid_token", "invalid_token", "expired_token"]

        fcm_service.get_user_device_tokens = Mock(return_value=device_tokens)

        notification_request = PushNotificationRequest(
            title="Retry Test", body="Testing error recovery", user_ids=[user_id]
        )

        # Mock mixed success/failure response
        mock_response = Mock()
        mock_response.success_count = 1
        mock_response.failure_count = 2
        mock_response.responses = [
            Mock(success=True),
            Mock(success=False, exception=Exception("Invalid registration token")),
            Mock(
                success=False, exception=Exception("Registration token not registered")
            ),
        ]

        with patch(
            "firebase_admin.messaging.send_multicast", return_value=mock_response
        ):
            fcm_service._record_notification = Mock()
            fcm_service._handle_invalid_tokens = Mock()

            # When
            result = fcm_service.send_push_notification(notification_request)

        # Then
        assert result.success is True  # At least one success
        assert result.success_count == 1
        assert result.failure_count == 2
        assert len(result.failed_tokens) == 2
        assert "invalid_token" in result.failed_tokens
        assert "expired_token" in result.failed_tokens

        fcm_service._handle_invalid_tokens.assert_called_once_with(
            ["invalid_token", "expired_token"]
        )
