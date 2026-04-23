"""Schemas for content type feature."""

from pydantic import BaseModel


class ContentTypeResponse(BaseModel):
    key: str
    label: str
    label_en: str | None
    icon: str | None
    color: str | None
    order: int

    class Config:
        orm_mode = True
