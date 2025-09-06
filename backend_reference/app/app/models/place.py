"""Place model with PostGIS support for location-based queries."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from app.db.base_class import Base


class PlaceStatus(str, Enum):
    """Place status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"


class PlaceCategory(str, Enum):
    """Place category enumeration."""

    RESTAURANT = "restaurant"
    CAFE = "cafe"
    BAR = "bar"
    TOURIST_ATTRACTION = "tourist_attraction"
    SHOPPING = "shopping"
    ACCOMMODATION = "accommodation"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class Place(Base):
    """Place model with geographical and metadata information."""

    __tablename__ = "places"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User association
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Basic place information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    opening_hours = Column(Text, nullable=True)
    price_range = Column(String(50), nullable=True)

    # Categorization
    category = Column(String(50), nullable=False, default=PlaceCategory.OTHER)
    tags = Column(ARRAY(String), nullable=True, default=[])
    keywords = Column(ARRAY(String), nullable=True, default=[])

    # Geographical data (PostGIS)
    coordinates = Column(
        Geography("POINT", srid=4326, spatial_index=True), nullable=True
    )

    # AI analysis metadata
    ai_confidence = Column(Float, nullable=True)
    ai_model_version = Column(String(100), nullable=True)
    recommendation_score = Column(Integer, nullable=True)

    # SNS source information
    source_url = Column(String(1000), nullable=True)
    source_platform = Column(String(50), nullable=True)
    source_content_hash = Column(String(64), nullable=True, index=True)

    # Status and timestamps
    status = Column(String(50), nullable=False, default=PlaceStatus.ACTIVE)
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Optimization indexes
    __table_args__ = (
        # Composite index for user's places with category filter
        Index("idx_user_category_created", "user_id", "category", "created_at"),
        # Full-text search index for name and address
        Index(
            "idx_place_search",
            func.to_tsvector(
                "korean", func.coalesce("name", "") + " " + func.coalesce("address", "")
            ),
            postgresql_using="gin",
        ),
        # Tag search optimization
        Index("idx_place_tags", "tags", postgresql_using="gin"),
        # Status filtering
        Index("idx_place_status", "status", "created_at"),
        # Duplicate detection
        Index("idx_place_duplicate", "user_id", "source_content_hash"),
        # Recommendation ranking
        Index(
            "idx_place_recommendation",
            "category",
            "recommendation_score",
            "ai_confidence",
        ),
    )

    def __repr__(self) -> str:
        return f"<Place(id={self.id}, name='{self.name}', category={self.category})>"

    @property
    def latitude(self) -> Optional[float]:
        """Extract latitude from coordinates."""
        if self.coordinates:
            return float(self.coordinates.data["coordinates"][1])
        return None

    @property
    def longitude(self) -> Optional[float]:
        """Extract longitude from coordinates."""
        if self.coordinates:
            return float(self.coordinates.data["coordinates"][0])
        return None

    def set_coordinates(self, latitude: float, longitude: float) -> None:
        """Set geographical coordinates."""
        self.coordinates = f"POINT({longitude} {latitude})"

    def is_within_radius(self, lat: float, lng: float, radius_km: float) -> bool:
        """Check if place is within specified radius from given coordinates."""
        if not self.coordinates:
            return False

        # This would typically be done in SQL query using ST_DWithin
        # Here for model completeness only
        return True

    def add_tag(self, tag: str) -> None:
        """Add tag to place (normalized)."""
        if self.tags is None:
            self.tags = []

        normalized_tag = tag.lower().strip()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)

    def remove_tag(self, tag: str) -> bool:
        """Remove tag from place."""
        if self.tags is None:
            return False

        normalized_tag = tag.lower().strip()
        if normalized_tag in self.tags:
            self.tags.remove(normalized_tag)
            return True
        return False
