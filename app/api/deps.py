"""
API dependencies for database sessions and authentication.

Common dependencies used across API endpoints.
"""

from typing import Generator, Optional

import redis.asyncio as redis
from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.cache import CacheService, MemoryCacheService
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth.user_data_service import (
    AuthenticatedUserService,
    UserActivityLogService,
    UserDataPrivacyService,
    UserPersonalDataService,
    UserSettingsService,
)

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """
    Get database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user() -> User:
    """
    Mock current user dependency for development.

    Returns:
        User: Mock user instance
    """
    # Create a mock User instance for testing
    user = User()
    user.id = "test_user_123"
    user.email = "test@example.com"
    return user


def get_current_active_user() -> User:
    """
    Get current active user dependency.

    Returns:
        User: Current active user instance
    """
    # For now, same as get_current_user (mock implementation)
    return get_current_user()


def get_current_active_superuser() -> User:
    """
    Get current active superuser dependency.

    Returns:
        User: Current active superuser instance
    """
    # Mock superuser for development
    user = get_current_user()
    user.is_superuser = True
    return user


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get Redis client for caching and session management.

    Returns:
        Optional[redis.Redis]: Redis client instance or None if not available
    """
    try:
        redis_client = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            password=getattr(settings, "REDIS_PASSWORD", None),
            decode_responses=True,
        )
        # Test connection
        await redis_client.ping()
        return redis_client
    except Exception:
        # Redis is optional - return None if not available
        return None


def get_cache_service() -> CacheService:
    """
    Get cache service dependency.

    For development, uses memory cache.
    In production, should use Redis cache.

    Returns:
        CacheService: Cache service instance
    """
    # For development/testing, use memory cache
    return MemoryCacheService()


def get_authenticated_user_service(
    db: Session = Depends(get_db),
) -> AuthenticatedUserService:
    """
    Get authenticated user service dependency.

    Args:
        db: Database session

    Returns:
        AuthenticatedUserService: Service instance
    """
    return AuthenticatedUserService(db=db)


def get_personal_data_service(
    db: Session = Depends(get_db),
) -> UserPersonalDataService:
    """
    Get user personal data service dependency.

    Args:
        db: Database session

    Returns:
        UserPersonalDataService: Service instance
    """
    return UserPersonalDataService(db=db)


def get_activity_log_service(
    db: Session = Depends(get_db),
) -> UserActivityLogService:
    """
    Get user activity log service dependency.

    Args:
        db: Database session

    Returns:
        UserActivityLogService: Service instance
    """
    return UserActivityLogService(db=db)


def get_settings_service(
    db: Session = Depends(get_db),
) -> UserSettingsService:
    """
    Get user settings service dependency.

    Args:
        db: Database session

    Returns:
        UserSettingsService: Service instance
    """
    return UserSettingsService(db=db)


def get_privacy_service(
    db: Session = Depends(get_db),
) -> UserDataPrivacyService:
    """
    Get user data privacy service dependency.

    Args:
        db: Database session

    Returns:
        UserDataPrivacyService: Service instance
    """
    return UserDataPrivacyService(db=db)
