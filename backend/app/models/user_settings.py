"""User settings model for notification and privacy preferences."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class UserSettings(Base):
    """User settings for notifications and privacy."""

    __tablename__ = "user_settings"  # type: ignore[assignment]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Notification settings
    push_enabled = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)

    # Notification preferences by type
    marketing_notifications = Column(Boolean, default=True)
    recommendation_notifications = Column(Boolean, default=True)
    social_notifications = Column(Boolean, default=True)

    # Privacy settings
    profile_visibility = Column(String(20), default="public")  # public, friends, private
    activity_visibility = Column(Boolean, default=True)
    show_saved_places = Column(Boolean, default=True)
    allow_friend_requests = Column(Boolean, default=True)

    # App settings
    language = Column(String(10), default="ko")
    theme = Column(String(20), default="system")  # light, dark, system

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id})>"
