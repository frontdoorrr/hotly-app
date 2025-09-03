"""Test database connection and basic operations."""
import pytest


def test_database_uri_assembly() -> None:
    """Test that database URI is properly assembled."""
    from app.core.config import settings

    uri = settings.SQLALCHEMY_DATABASE_URI
    assert "postgresql" in uri
    assert settings.POSTGRES_USER in uri
    assert settings.POSTGRES_DB in uri


def test_database_connection_config() -> None:
    """Test database connection configuration."""
    from app.db.session import engine

    # Test that engine is configured
    assert engine is not None
    assert str(engine.url).startswith("postgresql")


def test_database_session_factory() -> None:
    """Test database session factory."""
    from app.db.session import SessionLocal

    # Test that session factory exists
    assert SessionLocal is not None


@pytest.mark.integration
def test_database_health_check() -> None:
    """Test database health check endpoint."""
    # This will be implemented when we create the health endpoint
