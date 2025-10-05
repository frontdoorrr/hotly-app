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


# FCM and Notification Test Fixtures
@pytest.fixture
def mock_fcm_service():
    """Mock FCM service for testing."""
    from unittest.mock import Mock

    mock_service = Mock()

    # Default successful responses
    mock_service.register_device_token.return_value = {
        "success": True,
        "message": "Device token registered successfully",
        "device_id": "test_device_123",
        "is_new": True,
    }

    mock_service.send_push_notification.return_value = Mock(
        success=True, success_count=1, failure_count=0, failed_tokens=[]
    )

    mock_service.get_notification_stats.return_value = {
        "period_days": 7,
        "total_notifications_sent": 10,
        "total_success_count": 9,
        "total_failure_count": 1,
        "success_rate": 0.9,
        "by_notification_type": {"general": {"count": 10, "success": 9, "failures": 1}},
        "generated_at": datetime.utcnow().isoformat(),
    }

    return mock_service


@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    from unittest.mock import Mock

    mock_service = Mock()

    # Default user preferences
    mock_preferences = Mock()
    mock_preferences.user_id = "test_user_123"
    mock_preferences.push_notifications_enabled = True
    mock_preferences.promotional_notifications = False
    mock_preferences.quiet_hours_enabled = False

    mock_service.get_user_preferences.return_value = mock_preferences
    mock_service.update_user_preferences.return_value = mock_preferences

    mock_service.can_send_notification.return_value = {
        "can_send": True,
        "reason": "allowed",
    }

    return mock_service


@pytest.fixture
def mock_notification_template_service():
    """Mock notification template service for testing."""
    from unittest.mock import Mock

    mock_service = Mock()

    # Default template
    mock_template = Mock()
    mock_template.id = "template_123"
    mock_template.name = "test_template"
    mock_template.title_template = "Hello {user_name}!"
    mock_template.body_template = "Welcome to {app_name}, {user_name}!"
    mock_template.required_variables = ["user_name", "app_name"]
    mock_template.default_data = {"app_name": "HotlyApp"}

    mock_service.get_template_by_name.return_value = mock_template
    mock_service.render_template.return_value = {
        "title": "Hello Test User!",
        "body": "Welcome to HotlyApp, Test User!",
        "notification_type": "onboarding",
        "category": "welcome",
        "priority": "normal",
        "data": {"user_name": "Test User", "app_name": "HotlyApp"},
    }

    return mock_service


@pytest.fixture
def sample_push_notification_request():
    """Sample push notification request data."""
    return {
        "title": "Test Notification",
        "body": "This is a test notification body",
        "user_ids": ["user1", "user2"],
        "data": {"test_key": "test_value"},
        "notification_type": "general",
        "priority": "normal",
    }


@pytest.fixture
def sample_device_token():
    """Sample FCM device token."""
    return "sample_fcm_token_abcdef123456789"


@pytest.fixture
def sample_device_info():
    """Sample device information."""
    return {
        "platform": "ios",
        "model": "iPhone 13",
        "version": "15.6",
        "app_version": "1.0.0",
        "timezone": "Asia/Seoul",
    }


@pytest.fixture
def sample_notification_template_data():
    """Sample notification template creation data."""
    return {
        "name": "test_welcome_template",
        "description": "Welcome notification template for testing",
        "title_template": "환영합니다, {user_name}님!",
        "body_template": "{app_name}에 오신 것을 환영합니다. {feature}을 사용해보세요!",
        "notification_type": "onboarding",
        "category": "welcome",
        "priority": "normal",
        "required_variables": ["user_name", "app_name", "feature"],
        "optional_variables": ["user_email"],
        "default_data": {"app_name": "핫플리", "feature": "맛집 추천"},
    }


@pytest.fixture
def sample_templated_notification_request():
    """Sample templated notification request."""
    return {
        "template_name": "welcome_template",
        "user_ids": ["test_user_123"],
        "variables": {
            "user_name": "김철수",
            "app_name": "핫플리",
            "feature": "개인화 추천",
        },
        "additional_data": {"source": "onboarding_flow", "campaign_id": "welcome_2024"},
    }


@pytest.fixture
def sample_user_notification_preferences():
    """Sample user notification preferences."""
    return {
        "push_notifications_enabled": True,
        "email_notifications_enabled": False,
        "onboarding_notifications": True,
        "place_recommendations": True,
        "course_recommendations": True,
        "social_activity_notifications": False,
        "reminder_notifications": True,
        "promotional_notifications": False,
        "system_update_notifications": True,
        "quiet_hours_enabled": True,
        "quiet_hours_start": 22,
        "quiet_hours_end": 7,
        "max_daily_notifications": 15,
        "max_weekly_notifications": 80,
        "preferred_language": "ko",
        "timezone": "Asia/Seoul",
    }
