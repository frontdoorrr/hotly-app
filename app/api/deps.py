"""
API dependencies for database sessions and authentication.

Common dependencies used across API endpoints.
"""

from typing import Generator, Optional

import redis.asyncio as redis
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User

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
