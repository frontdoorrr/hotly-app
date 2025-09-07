"""User device model for FCM token management."""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class UserDevice(Base):
    """User device model for FCM token management."""

    __tablename__ = "user_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String, nullable=False, index=True)

    # FCM token information
    fcm_token = Column(Text, nullable=False, unique=True, index=True)

    # Device information
    device_info = Column(
        JSON, nullable=False, default=dict
    )  # platform, model, version, etc.

    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_active = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    unregistered_at = Column(DateTime, nullable=True)

    # Notification preferences
    push_enabled = Column(Boolean, default=True, nullable=False)
    quiet_hours_start = Column(Integer, nullable=True)  # Hour of day (0-23)
    quiet_hours_end = Column(Integer, nullable=True)  # Hour of day (0-23)

    def __repr__(self) -> str:
        return f"<UserDevice(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

    @property
    def device_platform(self) -> Optional[str]:
        """Get device platform from device info."""
        return self.device_info.get("platform") if self.device_info else None

    @property
    def device_model(self) -> Optional[str]:
        """Get device model from device info."""
        return self.device_info.get("model") if self.device_info else None

    @property
    def is_ios(self) -> bool:
        """Check if device is iOS."""
        return self.device_platform == "ios"

    @property
    def is_android(self) -> bool:
        """Check if device is Android."""
        return self.device_platform == "android"

    def is_in_quiet_hours(self, current_hour: int) -> bool:
        """Check if current time is in user's quiet hours."""
        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        if start < end:
            # Normal range (e.g., 22-6)
            return start <= current_hour < end
        else:
            # Overnight range (e.g., 22-6)
            return current_hour >= start or current_hour < end

    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active = datetime.utcnow()
