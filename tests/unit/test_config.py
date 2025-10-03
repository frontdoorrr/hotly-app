"""Test configuration management and environment variables."""

import os
from unittest.mock import patch

from app.core.config import Settings


def test_settings_creation() -> None:
    """Test that settings can be created with defaults."""
    settings = Settings()

    assert settings.PROJECT_NAME == "Hotly App"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.SECRET_KEY is not None
    assert len(settings.SECRET_KEY) > 20


def test_settings_environment_override() -> None:
    """Test that environment variables override defaults."""
    with patch.dict(
        os.environ,
        {
            "PROJECT_NAME": "test-app",
            "API_V1_STR": "/api/v2",
            "SECRET_KEY": "test-secret-key",
        },
    ):
        settings = Settings()

        assert settings.PROJECT_NAME == "test-app"
        assert settings.API_V1_STR == "/api/v2"
        assert settings.SECRET_KEY == "test-secret-key"


def test_database_uri_assembly() -> None:
    """Test database URI is properly assembled from components."""
    with patch.dict(
        os.environ,
        {
            "POSTGRES_SERVER": "localhost",
            "POSTGRES_USER": "test_user",
            "POSTGRES_PASSWORD": "test_pass",
            "POSTGRES_DB": "test_db",
            "POSTGRES_PORT": "5432",
        },
    ):
        settings = Settings()

        expected_uri = "postgresql://test_user:test_pass@localhost:5432/test_db"
        assert settings.SQLALCHEMY_DATABASE_URI == expected_uri


def test_redis_url_assembly() -> None:
    """Test Redis URL is properly assembled."""
    with patch.dict(
        os.environ,
        {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_PASSWORD": "test_pass",
        },
    ):
        settings = Settings()

        expected_url = "redis://:test_pass@localhost:6379/0"
        assert settings.REDIS_URL == expected_url


def test_cors_origins_default() -> None:
    """Test CORS origins default configuration."""
    # Test with empty/default value
    settings = Settings()
    assert isinstance(settings.BACKEND_CORS_ORIGINS, list)
    assert settings.BACKEND_CORS_ORIGINS == []
