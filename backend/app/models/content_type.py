"""ContentType model — configurable archive content type definitions."""

from sqlalchemy import Boolean, Column, Integer, String

from app.db.base_class import Base


class ContentType(Base):
    __tablename__ = "content_types"  # type: ignore[assignment]

    key = Column(String(50), primary_key=True)
    label = Column(String(100), nullable=False)
    label_en = Column(String(100), nullable=True)
    icon = Column(String(100), nullable=True)
    color = Column(String(20), nullable=True)
    order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
