"""Test configuration and shared fixtures."""

import asyncio
from datetime import datetime
from typing import Generator
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db() -> Generator[Session, None, None]:
    """Create database session for testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create FastAPI test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db_session():
    """Create a mock database session for testing."""
    mock_session = Mock(spec=Session)
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.rollback = Mock()
    mock_session.refresh = Mock()
    mock_session.close = Mock()

    # Setup query mock
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.filter_by.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.first.return_value = None
    mock_query.all.return_value = []
    mock_query.count.return_value = 0

    mock_session.query.return_value = mock_query

    return mock_session


@pytest.fixture
def sample_user_data():
    """Provide sample user data for testing."""
    return {
        "user_id": str(uuid4()),
        "email": "test@example.com",
        "user_segment": "tech_savvy",
        "device_info": {"platform": "ios", "version": "15.0"},
        "signup_source": "organic",
        "location": {"country": "KR", "city": "Seoul"},
        "demographic_info": {"age_group": "25-34"},
        "created_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_onboarding_session():
    """Provide sample onboarding session data."""
    return {
        "session_id": f"session_{uuid4()}",
        "user_id": str(uuid4()),
        "current_step": "welcome",
        "progress_percentage": 0.0,
        "status": "active",
        "step_data": {},
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@pytest.fixture
def sample_preference_data():
    """Provide sample preference data for testing."""
    return {
        "categories": ["restaurant", "cafe", "culture"],
        "budget_level": "medium",
        "location_preferences": {
            "current_location": {"lat": 37.5665, "lng": 126.9780},
            "preferred_areas": ["강남구", "서초구"],
            "max_travel_distance_km": 10,
        },
        "companion_preferences": {
            "companion_type": "couple",
            "group_size_preference": 2,
            "social_comfort_level": "medium",
        },
        "activity_preferences": {
            "activity_intensity": "moderate",
            "physical_limitations": [],
            "time_preferences": {"preferred_duration_hours": 3},
        },
    }


# Test data builders
class TestDataBuilder:
    """Builder class for creating test data objects."""

    @staticmethod
    def create_onboarding_session(
        user_id: str = None,
        current_step: str = "welcome",
        progress: float = 0.0,
        status: str = "active",
        **kwargs,
    ):
        """Create onboarding session test data."""
        return {
            "session_id": f"session_{uuid4()}",
            "user_id": user_id or str(uuid4()),
            "current_step": current_step,
            "progress_percentage": progress,
            "status": status,
            "step_data": kwargs.get("step_data", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            **kwargs,
        }

    @staticmethod
    def create_user_behavior(
        user_id: str = None, action: str = "visit", rating: float = 4.0, **kwargs
    ):
        """Create user behavior test data."""
        return {
            "user_id": user_id or str(uuid4()),
            "action": action,
            "place_id": str(uuid4()),
            "duration_minutes": kwargs.get("duration_minutes", 30),
            "rating": rating,
            "tags_added": kwargs.get("tags_added", []),
            "time_of_day": kwargs.get("time_of_day", "evening"),
            "day_of_week": kwargs.get("day_of_week", "friday"),
            "created_at": datetime.utcnow(),
            **kwargs,
        }


@pytest.fixture
def test_data_builder():
    """Provide test data builder instance."""
    return TestDataBuilder
