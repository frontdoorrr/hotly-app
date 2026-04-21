"""ArchivedContent model — user-archived results from link-analyzer."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from app.db.base_class import Base


class ArchivedContent(Base):
    __tablename__ = "archived_contents"  # type: ignore[assignment]

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    url = Column(Text, nullable=False)

    platform = Column(
        Enum("youtube", "instagram", "naver_blog", name="platform_type"),
        nullable=False,
    )
    content_type = Column(String(50), nullable=False)

    # --- 콘텐츠 메타데이터 ---
    title = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)

    # --- 분석 공통 필드 ---
    summary = Column(Text, nullable=True)
    keywords_main = Column(ARRAY(Text), nullable=True)
    keywords_sub = Column(ARRAY(Text), nullable=True)
    named_entities = Column(ARRAY(Text), nullable=True)
    topic_categories = Column(ARRAY(Text), nullable=True)
    sentiment = Column(
        Enum("positive", "neutral", "negative", name="sentiment_type"),
        nullable=True,
    )
    todos = Column(ARRAY(Text), nullable=True)
    insights = Column(ARRAY(Text), nullable=True)

    # --- 타입별 추가 데이터 ---
    type_specific_data = Column(JSONB, nullable=True)

    # --- 앱 메타 ---
    link_analyzer_id = Column(UUID(as_uuid=True), nullable=True)
    archived_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
