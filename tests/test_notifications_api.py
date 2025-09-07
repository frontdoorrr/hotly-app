"""Test cases for notification API endpoints."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.notification import DeviceTokenResponse, PushNotificationResponse

client = TestClient(app)


class TestNotificationAPIEndpoints:
    """Test cases for notification API endpoints."""

    @pytest.fixture
    def mock_current_user(self):
        """Mock current authenticated user."""
        mock_user = Mock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        return mock_user

    @pytest.fixture
    def auth_headers(self):
        """Mock authorization headers."""
        return {"Authorization": "Bearer mock_token"}

    def test_register_device_token_success(self, mock_current_user, auth_headers):
        """Test successful device token registration."""
        # Given
        request_data = {
            "token": "mock_fcm_token_123",
            "device_info": {"platform": "ios", "model": "iPhone 13", "version": "15.0"},
        }

        mock_response = DeviceTokenResponse(
            success=True,
            message="Device token registered successfully",
            device_id="device_123",
            is_new=True,
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.register_device_token.return_value = {
                "success": True,
                "message": "Device token registered successfully",
                "device_id": "device_123",
                "is_new": True,
            }

            # When
            response = client.post(
                "/api/v1/notifications/device/register",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["device_id"] == "device_123"
        assert data["is_new"] is True

    def test_register_device_token_failure(self, mock_current_user, auth_headers):
        """Test device token registration failure."""
        # Given
        request_data = {"token": "invalid_token"}

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.register_device_token.side_effect = Exception(
                "FCM error"
            )

            # When
            response = client.post(
                "/api/v1/notifications/device/register",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_unregister_device_token_success(self, mock_current_user, auth_headers):
        """Test successful device token unregistration."""
        # Given
        token = "token_to_unregister"

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.unregister_device_token.return_value = {
                "success": True,
                "message": "Device token unregistered successfully",
            }

            # When
            response = client.delete(
                f"/api/v1/notifications/device/unregister?token={token}",
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True

    def test_unregister_device_token_not_found(self, mock_current_user, auth_headers):
        """Test unregistering non-existent device token."""
        # Given
        token = "nonexistent_token"

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.unregister_device_token.return_value = {
                "success": False,
                "error": "Device token not found",
            }

            # When
            response = client.delete(
                f"/api/v1/notifications/device/unregister?token={token}",
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_send_push_notification_success(self, mock_current_user, auth_headers):
        """Test successful push notification sending."""
        # Given
        request_data = {
            "title": "Test Notification",
            "body": "This is a test notification",
            "user_ids": ["user1", "user2"],
            "data": {"key": "value"},
            "notification_type": "general",
            "priority": "normal",
        }

        mock_response = PushNotificationResponse(
            success=True,
            message_id="msg_123",
            success_count=2,
            failure_count=0,
            failed_tokens=[],
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.send_push_notification.return_value = (
                mock_response
            )

            # When
            response = client.post(
                "/api/v1/notifications/push", json=request_data, headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["success_count"] == 2
        assert data["failure_count"] == 0

    def test_send_templated_notification_success(self, mock_current_user, auth_headers):
        """Test successful templated notification sending."""
        # Given
        request_data = {
            "template_name": "welcome_template",
            "user_ids": ["user1"],
            "variables": {"user_name": "John Doe", "app_name": "HotlyApp"},
        }

        rendered_template = {
            "title": "Welcome John Doe!",
            "body": "Hi John Doe, welcome to HotlyApp!",
            "notification_type": "onboarding",
            "category": "welcome",
            "priority": "normal",
            "data": {"user_name": "John Doe", "app_name": "HotlyApp"},
        }

        mock_push_response = PushNotificationResponse(
            success=True, success_count=1, failure_count=0
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.render_template.return_value = (
                rendered_template
            )
            mock_fcm_service.return_value.send_push_notification.return_value = (
                mock_push_response
            )

            # When
            response = client.post(
                "/api/v1/notifications/push/templated",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["success_count"] == 1

    def test_send_templated_notification_template_not_found(
        self, mock_current_user, auth_headers
    ):
        """Test templated notification with non-existent template."""
        # Given
        request_data = {
            "template_name": "nonexistent_template",
            "user_ids": ["user1"],
            "variables": {"user_name": "John"},
        }

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.render_template.side_effect = ValueError(
                "Template 'nonexistent_template' not found"
            )

            # When
            response = client.post(
                "/api/v1/notifications/push/templated",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_notification_templates_success(self, mock_current_user, auth_headers):
        """Test successful template listing."""
        # Given
        mock_templates = [
            Mock(
                id=uuid4(),
                name="template1",
                notification_type="onboarding",
                category="welcome",
            ),
            Mock(
                id=uuid4(),
                name="template2",
                notification_type="reminder",
                category="visit",
            ),
        ]

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.list_templates.return_value = (
                mock_templates
            )

            # When
            response = client.get(
                "/api/v1/notifications/templates?notification_type=onboarding&limit=10",
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        mock_template_service.return_value.list_templates.assert_called_once_with(
            notification_type="onboarding",
            category=None,
            is_active=None,
            skip=0,
            limit=10,
        )

    def test_get_notification_template_success(self, mock_current_user, auth_headers):
        """Test successful template retrieval by ID."""
        # Given
        template_id = str(uuid4())
        mock_template = Mock(
            id=template_id,
            name="test_template",
            title_template="Test {user_name}",
            body_template="Hello {user_name}",
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.get_template_by_id.return_value = (
                mock_template
            )

            # When
            response = client.get(
                f"/api/v1/notifications/templates/{template_id}", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "test_template"

    def test_get_notification_template_not_found(self, mock_current_user, auth_headers):
        """Test template retrieval for non-existent template."""
        # Given
        template_id = str(uuid4())

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.get_template_by_id.return_value = None

            # When
            response = client.get(
                f"/api/v1/notifications/templates/{template_id}", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_notification_template_success(
        self, mock_current_user, auth_headers
    ):
        """Test successful template creation."""
        # Given
        request_data = {
            "name": "new_template",
            "description": "A new test template",
            "title_template": "New {user_name}",
            "body_template": "Welcome {user_name} to {app_name}",
            "notification_type": "onboarding",
            "required_variables": ["user_name", "app_name"],
        }

        mock_created_template = Mock(
            id=uuid4(), name="new_template", description="A new test template"
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.create_template.return_value = (
                mock_created_template
            )

            # When
            response = client.post(
                "/api/v1/notifications/templates",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "new_template"

    def test_update_notification_template_success(
        self, mock_current_user, auth_headers
    ):
        """Test successful template update."""
        # Given
        template_id = str(uuid4())
        request_data = {"description": "Updated description", "priority": "high"}

        mock_updated_template = Mock(
            id=template_id, description="Updated description", priority="high"
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.update_template.return_value = (
                mock_updated_template
            )

            # When
            response = client.put(
                f"/api/v1/notifications/templates/{template_id}",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["priority"] == "high"

    def test_delete_notification_template_success(
        self, mock_current_user, auth_headers
    ):
        """Test successful template deletion."""
        # Given
        template_id = str(uuid4())

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.delete_template.return_value = True

            # When
            response = client.delete(
                f"/api/v1/notifications/templates/{template_id}", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "deleted successfully" in data["message"]

    def test_get_template_variables_success(self, mock_current_user, auth_headers):
        """Test successful template variables retrieval."""
        # Given
        template_name = "welcome_template"
        mock_variables = {
            "template_name": template_name,
            "required_variables": ["user_name", "app_name"],
            "optional_variables": ["user_email"],
            "default_data": {"app_name": "HotlyApp"},
            "notification_type": "onboarding",
        }

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_template_service.get_notification_template_service"
            ) as mock_template_service,
        ):
            mock_template_service.return_value.get_template_variables.return_value = (
                mock_variables
            )

            # When
            response = client.get(
                f"/api/v1/notifications/templates/name/{template_name}/variables",
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["template_name"] == template_name
        assert "required_variables" in data

    def test_get_notification_history_success(self, mock_current_user, auth_headers):
        """Test successful notification history retrieval."""
        # Given
        mock_history = [
            Mock(
                id=uuid4(),
                title="Test Notification",
                notification_type="general",
                status="sent",
            )
        ]

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_service.get_notification_service"
            ) as mock_notification_service,
        ):
            mock_notification_service.return_value.get_notification_history.return_value = (
                mock_history
            )

            # When
            response = client.get(
                "/api/v1/notifications/history?days=7&limit=50", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1

    def test_get_notification_stats_success(self, mock_current_user, auth_headers):
        """Test successful notification statistics retrieval."""
        # Given
        mock_stats = {
            "period_days": 7,
            "total_notifications_sent": 100,
            "total_success_count": 95,
            "total_failure_count": 5,
            "success_rate": 0.95,
            "by_notification_type": {
                "onboarding": {"count": 20, "success": 19, "failures": 1},
                "reminder": {"count": 30, "success": 28, "failures": 2},
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.get_notification_stats.return_value = (
                mock_stats
            )

            # When
            response = client.get(
                "/api/v1/notifications/stats?days=7", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_notifications_sent"] == 100
        assert data["success_rate"] == 0.95

    def test_get_notification_preferences_success(
        self, mock_current_user, auth_headers
    ):
        """Test successful notification preferences retrieval."""
        # Given
        mock_preferences = Mock(
            user_id=str(mock_current_user.id),
            push_notifications_enabled=True,
            promotional_notifications=False,
            quiet_hours_enabled=True,
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_service.get_notification_service"
            ) as mock_notification_service,
        ):
            mock_notification_service.return_value.get_user_preferences.return_value = (
                mock_preferences
            )

            # When
            response = client.get(
                "/api/v1/notifications/preferences", headers=auth_headers
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["push_notifications_enabled"] is True
        assert data["promotional_notifications"] is False

    def test_update_notification_preferences_success(
        self, mock_current_user, auth_headers
    ):
        """Test successful notification preferences update."""
        # Given
        request_data = {
            "push_notifications_enabled": False,
            "promotional_notifications": True,
            "quiet_hours_enabled": True,
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
        }

        mock_updated_preferences = Mock(
            user_id=str(mock_current_user.id),
            push_notifications_enabled=False,
            promotional_notifications=True,
            quiet_hours_enabled=True,
        )

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch(
                "app.services.notification_service.get_notification_service"
            ) as mock_notification_service,
        ):
            mock_notification_service.return_value.update_user_preferences.return_value = (
                mock_updated_preferences
            )

            # When
            response = client.put(
                "/api/v1/notifications/preferences",
                json=request_data,
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["push_notifications_enabled"] is False
        assert data["promotional_notifications"] is True

    def test_cleanup_expired_tokens_success(self, mock_current_user, auth_headers):
        """Test successful cleanup of expired tokens."""
        # Given
        mock_cleanup_result = {
            "cleaned_up_count": 15,
            "cutoff_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        }

        with (
            patch("app.api.deps.get_current_user", return_value=mock_current_user),
            patch("app.services.fcm_service.get_fcm_service") as mock_fcm_service,
        ):
            mock_fcm_service.return_value.cleanup_expired_tokens.return_value = (
                mock_cleanup_result
            )

            # When
            response = client.post(
                "/api/v1/notifications/cleanup/tokens?days_inactive=30",
                headers=auth_headers,
            )

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cleaned_up_count"] == 15

    def test_unauthorized_access(self):
        """Test API endpoints without authentication."""
        # When & Then
        endpoints = [
            ("POST", "/api/v1/notifications/device/register"),
            ("GET", "/api/v1/notifications/templates"),
            ("GET", "/api/v1/notifications/preferences"),
        ]

        for method, endpoint in endpoints:
            if method == "POST":
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_validation_errors(self, mock_current_user, auth_headers):
        """Test API validation errors."""
        with patch("app.api.deps.get_current_user", return_value=mock_current_user):
            # Test 1: Invalid device token registration
            response = client.post(
                "/api/v1/notifications/device/register",
                json={},  # Missing required 'token' field
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            # Test 2: Invalid push notification request
            response = client.post(
                "/api/v1/notifications/push",
                json={
                    "title": "",  # Empty title
                    "body": "Test body",
                    "user_ids": [],  # Empty user list
                },
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            # Test 3: Invalid template creation
            response = client.post(
                "/api/v1/notifications/templates",
                json={
                    "name": "test",
                    "title_template": "Test",
                    "body_template": "Test body",
                    "notification_type": "invalid_type",  # Invalid notification type
                },
                headers=auth_headers,
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
