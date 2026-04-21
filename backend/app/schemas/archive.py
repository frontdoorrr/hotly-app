"""Schemas for the archive feature."""

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


ContentType = str  # DB-managed via content_types table
Platform = Literal["youtube", "instagram", "naver_blog"]
Sentiment = Literal["positive", "neutral", "negative"]


# ------------------------------------------------------------------
# Request
# ------------------------------------------------------------------

class ArchiveRequest(BaseModel):
    url: str
    force: bool = False


# ------------------------------------------------------------------
# Response — list item (compact)
# ------------------------------------------------------------------

class ArchiveListItem(BaseModel):
    id: UUID
    url: str
    platform: Platform
    content_type: ContentType
    title: Optional[str]
    author: Optional[str]
    thumbnail_url: Optional[str]
    summary: Optional[str]
    sentiment: Optional[Sentiment]
    archived_at: datetime

    class Config:
        orm_mode = True


# ------------------------------------------------------------------
# Response — detail (full)
# ------------------------------------------------------------------

class ArchiveDetail(BaseModel):
    id: UUID
    url: str
    platform: Platform
    content_type: ContentType

    # metadata
    title: Optional[str]
    author: Optional[str]
    published_at: Optional[datetime]
    thumbnail_url: Optional[str]
    language: Optional[str]

    # analysis
    summary: Optional[str]
    keywords_main: Optional[list[str]]
    keywords_sub: Optional[list[str]]
    named_entities: Optional[list[str]]
    topic_categories: Optional[list[str]]
    sentiment: Optional[Sentiment]
    todos: Optional[list[str]]
    insights: Optional[list[str]]

    # type-specific
    type_specific_data: Optional[Any]

    # app meta
    link_analyzer_id: Optional[UUID]
    archived_at: datetime

    class Config:
        orm_mode = True


# ------------------------------------------------------------------
# Response — paginated list
# ------------------------------------------------------------------

class ArchiveListResponse(BaseModel):
    items: list[ArchiveListItem]
    total: int
    page: int
    page_size: int
