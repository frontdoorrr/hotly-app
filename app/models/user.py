from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .item import Item  # noqa: F401
    from .notification import UserNotificationSettings  # noqa: F401
    from .notification_analytics import UserNotificationPattern  # noqa: F401


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    items = relationship("Item", back_populates="owner")
    notification_settings = relationship(
        "UserNotificationSettings", back_populates="user", uselist=False
    )
    notification_pattern = relationship(
        "UserNotificationPattern", back_populates="user", uselist=False
    )
