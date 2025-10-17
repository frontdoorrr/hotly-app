"""UserTag model for efficient tag statistics and management."""

import uuid
from datetime import datetime
from typing import Dict

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base_class import Base


class UserTag(Base):
    """User tag statistics model for optimized tag queries."""

    __tablename__ = "user_tags"  # type: ignore[assignment]

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User association
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Tag information
    tag = Column(String(50), nullable=False)

    # Usage statistics
    usage_count = Column(Integer, nullable=False, default=1)
    last_used = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Category distribution (e.g., {"cafe": 5, "restaurant": 3})
    category_distribution = Column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint("user_id", "tag", name="uq_user_tags_user_tag"),
    )

    def __repr__(self) -> str:
        return f"<UserTag(user_id={self.user_id}, tag='{self.tag}', usage_count={self.usage_count})>"

    def increment_usage(self, category: str | None = None) -> None:
        """Increment tag usage count and update last_used timestamp."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()

        # Update category distribution
        if category and self.category_distribution is not None:
            dist = dict(self.category_distribution)  # Make a mutable copy
            dist[category] = dist.get(category, 0) + 1
            self.category_distribution = dist

    def get_top_category(self) -> str | None:
        """Get the category where this tag is most frequently used."""
        if not self.category_distribution:
            return None

        return max(self.category_distribution.items(), key=lambda x: x[1])[0]

    def get_category_percentage(self, category: str) -> float:
        """Get the percentage of usage in a specific category."""
        if not self.category_distribution or self.usage_count == 0:
            return 0.0

        category_count = self.category_distribution.get(category, 0)
        return (category_count / self.usage_count) * 100

    def to_dict(self) -> Dict:
        """Convert model to dictionary for API responses."""
        return {
            "tag": self.tag,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "category_distribution": self.category_distribution or {},
            "top_category": self.get_top_category(),
        }
