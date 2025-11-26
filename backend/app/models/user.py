from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .item import Item  # noqa: F401
    from .notification_analytics import UserNotificationPattern  # noqa: F401


class User(Base):
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(128), unique=True, index=True, nullable=True)

    # Basic info
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile fields
    nickname = Column(String(50), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    # Soft delete
    deleted_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship("Item", back_populates="owner")
    # notification_settings and notification_pattern relationships removed due to model conflicts
    # notification_pattern = relationship(
    #     "UserNotificationPattern", back_populates="user", uselist=False
    # )
