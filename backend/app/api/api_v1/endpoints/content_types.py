"""Content types endpoint — returns active content type definitions."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.content_type import ContentType
from app.models.user_data import AuthenticatedUser
from app.schemas.content_type import ContentTypeResponse

router = APIRouter()


@router.get("", response_model=list[ContentTypeResponse])
async def get_content_types(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Any:
    """활성화된 콘텐츠 타입 목록을 order 순으로 반환합니다."""
    return (
        db.query(ContentType)
        .filter(ContentType.is_active == True)  # noqa: E712
        .order_by(ContentType.order)
        .all()
    )
