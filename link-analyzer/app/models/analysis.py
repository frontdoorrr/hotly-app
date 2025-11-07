"""SQLAlchemy models for analysis results."""

from sqlalchemy import Column, String, DateTime, JSON, Float, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class AnalysisResult(Base):
    """
    Analysis result storage model.

    Stores complete analysis results for caching and retrieval.
    """

    __tablename__ = "analysis_results"

    # Primary key
    id = Column(String(255), primary_key=True, index=True)  # URL hash or unique ID

    # Source information
    url = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    content_type = Column(String(50), nullable=False)

    # Platform metadata
    title = Column(Text)
    description = Column(Text)
    hashtags = Column(JSON, default=list)  # List[str]

    # Analysis results (JSON columns)
    video_analysis = Column(JSON, nullable=True)  # VideoAnalysis schema
    image_analysis = Column(JSON, nullable=True)  # ImageAnalysis schema
    classification = Column(JSON, nullable=True)  # ClassificationResult schema

    # Confidence and quality metrics
    confidence_score = Column(Float, default=0.0)

    # Additional metadata
    metadata = Column(JSON, default=dict)

    # Timestamps
    analyzed_at = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_platform_created', 'platform', 'created_at'),
        Index('idx_url_hash', 'url', postgresql_using='hash'),
    )

    def __repr__(self):
        return f"<AnalysisResult(id='{self.id}', platform='{self.platform}', url='{self.url[:50]}...')>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'url': self.url,
            'platform': self.platform,
            'content_type': self.content_type,
            'title': self.title,
            'description': self.description,
            'hashtags': self.hashtags,
            'video_analysis': self.video_analysis,
            'image_analysis': self.image_analysis,
            'classification': self.classification,
            'confidence_score': self.confidence_score,
            'metadata': self.metadata,
            'analyzed_at': self.analyzed_at.isoformat() if self.analyzed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
