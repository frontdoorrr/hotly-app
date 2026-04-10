"""Archive endpoints — URL 분석 및 아카이빙."""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.jwt_middleware import get_current_active_user
from app.models.archived_content import ArchivedContent
from app.schemas.archive import (
    ArchiveDetail,
    ArchiveListItem,
    ArchiveListResponse,
    ArchiveRequest,
)
from app.services.link_analyzer_client import (
    ContentExtractionError,
    LinkAnalyzerAuthError,
    LinkAnalyzerError,
    UnsupportedPlatformError,
    link_analyzer_client,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ------------------------------------------------------------------
# POST /archive — URL 분석 후 아카이빙
# ------------------------------------------------------------------

@router.post("", response_model=ArchiveDetail, status_code=status.HTTP_201_CREATED)
async def archive_url(
    body: ArchiveRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Any:
    user_id = UUID(current_user["uid"])

    # 동일 URL 이미 아카이빙된 경우 처리
    existing = (
        db.query(ArchivedContent)
        .filter(ArchivedContent.user_id == user_id, ArchivedContent.url == body.url)
        .first()
    )
    if existing and not body.force:
        return existing

    # link-analyzer 호출
    try:
        result = await link_analyzer_client.analyze(body.url, force=body.force)
    except UnsupportedPlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ContentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LinkAnalyzerAuthError as exc:
        logger.error("link-analyzer auth error: %s", exc)
        raise HTTPException(status_code=503, detail="분석 서비스 인증 오류입니다.")
    except LinkAnalyzerError as exc:
        logger.error("link-analyzer error: %s", exc)
        raise HTTPException(status_code=503, detail="분석 서비스를 사용할 수 없습니다.")

    content = _build_model(result, user_id)

    if existing and body.force:
        # 기존 레코드 업데이트
        for attr, val in content.__dict__.items():
            if attr.startswith("_"):
                continue
            setattr(existing, attr, val)
        db.commit()
        db.refresh(existing)
        return existing

    db.add(content)
    db.commit()
    db.refresh(content)
    return content


# ------------------------------------------------------------------
# GET /archive — 목록 조회
# ------------------------------------------------------------------

@router.get("", response_model=ArchiveListResponse)
def list_archives(
    content_type: Optional[str] = Query(None, description="place | event | tips | review | unknown"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Any:
    user_id = UUID(current_user["uid"])

    q = db.query(ArchivedContent).filter(ArchivedContent.user_id == user_id)
    if content_type:
        q = q.filter(ArchivedContent.content_type == content_type)

    total = q.count()
    items = (
        q.order_by(ArchivedContent.archived_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ArchiveListResponse(
        items=[ArchiveListItem.from_orm(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ------------------------------------------------------------------
# GET /archive/{id} — 상세 조회
# ------------------------------------------------------------------

@router.get("/{archive_id}", response_model=ArchiveDetail)
def get_archive(
    archive_id: UUID,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Any:
    user_id = UUID(current_user["uid"])
    item = _get_owned_or_404(db, archive_id, user_id)
    return item


# ------------------------------------------------------------------
# DELETE /archive/{id} — 삭제
# ------------------------------------------------------------------

@router.delete("/{archive_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_archive(
    archive_id: UUID,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> None:
    user_id = UUID(current_user["uid"])
    item = _get_owned_or_404(db, archive_id, user_id)
    db.delete(item)
    db.commit()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _get_owned_or_404(db: Session, archive_id: UUID, user_id: UUID) -> ArchivedContent:
    item = db.query(ArchivedContent).filter(ArchivedContent.id == archive_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="아카이브를 찾을 수 없습니다.")
    if item.user_id != user_id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    return item


def _build_model(data: dict, user_id: UUID) -> ArchivedContent:
    """link-analyzer ContentResponse → ArchivedContent 모델 변환."""
    meta = data.get("metadata") or {}
    analysis = data.get("analysis") or {}
    keywords = analysis.get("keywords") or {}
    categories = analysis.get("categories") or {}
    action_items = analysis.get("action_items") or {}

    return ArchivedContent(
        user_id=user_id,
        url=data.get("url", ""),
        platform=data.get("platform", ""),
        content_type=analysis.get("content_type", "unknown"),
        title=meta.get("title"),
        author=meta.get("author"),
        published_at=meta.get("published_at"),
        thumbnail_url=meta.get("thumbnail_url"),
        language=meta.get("language"),
        summary=analysis.get("summary"),
        keywords_main=keywords.get("main"),
        keywords_sub=keywords.get("sub"),
        named_entities=keywords.get("named_entities"),
        topic_categories=categories.get("topic"),
        sentiment=analysis.get("sentiment"),
        todos=action_items.get("todos"),
        insights=action_items.get("insights"),
        type_specific_data=analysis.get("type_specific_data"),
        link_analyzer_id=data.get("id"),
    )
