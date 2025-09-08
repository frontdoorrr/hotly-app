"""
API dependencies for database sessions and authentication.

Common dependencies used across API endpoints.
"""

from typing import Generator

from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

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
