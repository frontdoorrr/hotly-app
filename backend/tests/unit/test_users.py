"""Unit tests for user profile, preferences, and settings API."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from io import BytesIO

from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.user import (
    UserProfileUpdate,
    UserPreferencesUpdate,
    UserSettingsUpdate,
    PreferenceTagsSchema,
)
from app.services.image_upload_service import ImageUploadService, ImageUploadError


# Test fixtures
@pytest.fixture
def mock_current_user():
    """Mock authenticated user."""
    return {
        "uid": "test-firebase-uid-123",
        "user_id": "test-firebase-uid-123",
        "email": "test@example.com",
        "name": "Test User",
        "nickname": "tester",
        "picture": "https://example.com/photo.jpg",
        "bio": "Test bio",
    }


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


class TestUserProfileEndpoints:
    """Tests for user profile endpoints."""

    def test_get_profile_returns_user_data(self, client, mock_current_user):
        """Test GET /users/me/profile returns user profile data."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            response = client.get("/api/v1/users/me/profile")

            assert response.status_code == 200
            data = response.json()
            assert data["firebase_uid"] == mock_current_user["uid"]
            assert data["email"] == mock_current_user["email"]

    def test_update_profile_updates_fields(self, client, mock_current_user):
        """Test PUT /users/me/profile updates profile fields."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            update_data = {
                "nickname": "new_nickname",
                "bio": "Updated bio",
                "full_name": "New Name",
            }

            response = client.put("/api/v1/users/me/profile", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["nickname"] == "new_nickname"
            assert data["bio"] == "Updated bio"
            assert data["full_name"] == "New Name"

    def test_update_profile_partial_update(self, client, mock_current_user):
        """Test PUT /users/me/profile allows partial updates."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            # Only update nickname
            update_data = {"nickname": "partial_update"}

            response = client.put("/api/v1/users/me/profile", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["nickname"] == "partial_update"


class TestImageUploadService:
    """Tests for image upload service."""

    def test_validate_file_accepts_valid_extensions(self):
        """Test file validation accepts valid image extensions."""
        service = ImageUploadService()

        # Create mock file with valid extension
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.jpg"

        # Should not raise exception
        service._validate_file(mock_file)

    def test_validate_file_rejects_invalid_extensions(self):
        """Test file validation rejects invalid extensions."""
        service = ImageUploadService()

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.exe"

        with pytest.raises(ImageUploadError) as exc_info:
            service._validate_file(mock_file)

        assert "Invalid file type" in str(exc_info.value)

    def test_generate_filename_creates_unique_names(self):
        """Test filename generation creates unique filenames."""
        service = ImageUploadService()

        filename1 = service._generate_filename("user1", "photo.jpg")
        filename2 = service._generate_filename("user1", "photo.jpg")

        assert filename1 != filename2
        assert filename1.endswith(".jpg")
        assert "user1" in filename1

    @pytest.mark.asyncio
    async def test_upload_profile_image_success(self, tmp_path):
        """Test successful image upload."""
        service = ImageUploadService(upload_dir=tmp_path)

        # Create mock file
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.read = AsyncMock(return_value=b"fake image content")

        result = await service.upload_profile_image("user123", mock_file)

        assert "/uploads/profile_images/" in result
        assert result.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_upload_profile_image_file_too_large(self, tmp_path):
        """Test upload rejects files that are too large."""
        service = ImageUploadService(upload_dir=tmp_path)

        mock_file = AsyncMock(spec=UploadFile)
        mock_file.filename = "large.jpg"
        # Create content larger than 5MB
        mock_file.read = AsyncMock(return_value=b"x" * (6 * 1024 * 1024))

        with pytest.raises(ImageUploadError) as exc_info:
            await service.upload_profile_image("user123", mock_file)

        assert "too large" in str(exc_info.value)


class TestUserPreferencesEndpoints:
    """Tests for user preferences endpoints."""

    def test_get_preferences_returns_default_values(self, client, mock_current_user):
        """Test GET /users/me/preferences returns default preferences."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            response = client.get("/api/v1/users/me/preferences")

            assert response.status_code == 200
            data = response.json()
            assert data["budget_level"] == "medium"
            assert data["max_travel_distance_km"] == 10

    def test_update_preferences_updates_values(self, client, mock_current_user):
        """Test PUT /users/me/preferences updates preference values."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            update_data = {
                "food_preferences": {
                    "preset": ["한식", "양식"],
                    "custom": ["퓨전"],
                },
                "budget_level": "high",
                "max_travel_distance_km": 20,
            }

            response = client.put("/api/v1/users/me/preferences", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["budget_level"] == "high"
            assert data["max_travel_distance_km"] == 20


class TestUserSettingsEndpoints:
    """Tests for user settings endpoints."""

    def test_get_settings_returns_default_values(self, client, mock_current_user):
        """Test GET /users/me/settings returns default settings."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            response = client.get("/api/v1/users/me/settings")

            assert response.status_code == 200
            data = response.json()
            assert data["push_enabled"] is True
            assert data["email_enabled"] is True
            assert data["profile_visibility"] == "public"
            assert data["language"] == "ko"

    def test_update_settings_updates_values(self, client, mock_current_user):
        """Test PUT /users/me/settings updates setting values."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            update_data = {
                "push_enabled": False,
                "profile_visibility": "private",
                "theme": "dark",
            }

            response = client.put("/api/v1/users/me/settings", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["push_enabled"] is False
            assert data["profile_visibility"] == "private"
            assert data["theme"] == "dark"


class TestAccountManagementEndpoints:
    """Tests for account management endpoints."""

    def test_delete_account_requires_confirmation(self, client, mock_current_user):
        """Test DELETE /users/me requires confirmation."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            # Without confirmation
            response = client.delete(
                "/api/v1/users/me",
                json={"confirm": False}
            )

            assert response.status_code == 400
            assert "confirm" in response.json()["detail"].lower()

    def test_delete_account_with_confirmation(self, client, mock_current_user):
        """Test DELETE /users/me succeeds with confirmation."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            response = client.delete(
                "/api/v1/users/me",
                json={"confirm": True, "reason": "Testing"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "deleted_at" in data
            assert "restore_deadline" in data

    def test_export_data_returns_all_user_data(self, client, mock_current_user):
        """Test GET /users/me/export returns all user data."""
        with patch("app.api.api_v1.endpoints.users.get_current_active_user") as mock_auth:
            mock_auth.return_value = mock_current_user

            response = client.get("/api/v1/users/me/export")

            assert response.status_code == 200
            data = response.json()
            assert "profile" in data
            assert "preferences" in data
            assert "settings" in data
            assert "exported_at" in data


class TestSchemaValidation:
    """Tests for schema validation."""

    def test_user_profile_update_nickname_max_length(self):
        """Test nickname max length validation."""
        # Valid nickname
        valid = UserProfileUpdate(nickname="a" * 50)
        assert len(valid.nickname) == 50

        # Invalid nickname (too long)
        with pytest.raises(ValueError):
            UserProfileUpdate(nickname="a" * 51)

    def test_preference_tags_schema_structure(self):
        """Test PreferenceTagsSchema structure."""
        tags = PreferenceTagsSchema(
            preset=["한식", "양식"],
            custom=["퓨전", "건강식"]
        )
        assert tags.preset == ["한식", "양식"]
        assert tags.custom == ["퓨전", "건강식"]

    def test_user_settings_update_partial(self):
        """Test UserSettingsUpdate allows partial updates."""
        # Only update one field
        settings = UserSettingsUpdate(push_enabled=False)
        assert settings.push_enabled is False
        assert settings.email_enabled is None  # Not set
