"""Archive endpoints — URL 분석 및 아카이빙."""

import json as _json
import logging
from typing import Any, List, Optional
from uuid import UUID

from pathlib import Path as FilePath

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import Text, cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.archived_content import ArchivedContent
from app.models.user_data import AuthenticatedUser
from app.crud.user import crud_user
from app.schemas.archive import (
    ArchiveDetail,
    ArchiveListItem,
    ArchiveListResponse,
    ArchiveRequest,
)
from app.services.places.place_extractor import PlaceExtractorService
from app.services.link_analyzer_client import (
    ContentExtractionError,
    LinkAnalyzerAuthError,
    LinkAnalyzerError,
    RateLimitError,
    UnsupportedPlatformError,
    link_analyzer_client,
)

logger = logging.getLogger(__name__)
router = APIRouter()
_place_extractor = PlaceExtractorService()

_ALLOWED_MEDIA_MIMES = frozenset({
    "image/jpeg", "image/png", "image/webp", "video/mp4",
})
_MAX_MEDIA_COUNT = 10
_MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024   # 50MB per file
_MAX_TOTAL_SIZE_BYTES = 100 * 1024 * 1024  # 100MB total
_FORCE_UPDATE_PROTECTED_ATTRS = frozenset({"id", "user_id", "created_at", "archived_at"})


# ------------------------------------------------------------------
# POST /archive — URL 분석 후 아카이빙
# ------------------------------------------------------------------

@router.post("", response_model=ArchiveDetail, status_code=status.HTTP_201_CREATED)
async def archive_url(
    body: ArchiveRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Any:
    user_id = _get_user_id(db, current_user)

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
        result = await link_analyzer_client.analyze(body.url, force=body.force, language=body.language)
        logger.info("[DEBUG] link-analyzer raw response: %s", result)
    except UnsupportedPlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ContentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
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
        if existing.content_type == "place":
            background_tasks.add_task(
                _place_extractor.extract_and_create,
                user_id=user_id,
                **_to_extraction_snapshot(existing),
            )
        return existing

    db.add(content)
    db.commit()
    db.refresh(content)
    if content.content_type == "place":
        background_tasks.add_task(
            _place_extractor.extract_and_create,
            user_id=user_id,
            **_to_extraction_snapshot(content),
        )
    return content


# ------------------------------------------------------------------
# POST /archive/instagram — Instagram 미디어 multipart 아카이빙
# ------------------------------------------------------------------

@router.post("/instagram", response_model=ArchiveDetail, status_code=status.HTTP_201_CREATED)
async def archive_instagram(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
    caption: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    media: List[UploadFile] = File(...),
    force: bool = Form(False),
    language: str = Form("ko"),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Any:
    user_id = _get_user_id(db, current_user)

    existing = (
        db.query(ArchivedContent)
        .filter(ArchivedContent.user_id == user_id, ArchivedContent.url == url)
        .first()
    )
    if existing and not force:
        return existing

    if len(media) > _MAX_MEDIA_COUNT:
        raise HTTPException(status_code=400, detail=f"미디어 파일은 최대 {_MAX_MEDIA_COUNT}개까지 허용합니다.")

    media_tuples: list[tuple[str, bytes, str]] = []
    total_size = 0
    for i, upload in enumerate(media):
        mime = upload.content_type or "application/octet-stream"
        if mime not in _ALLOWED_MEDIA_MIMES:
            raise HTTPException(status_code=415, detail=f"지원하지 않는 파일 형식입니다: {mime}")
        file_bytes = await upload.read()
        if len(file_bytes) > _MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="파일 크기가 50MB를 초과합니다.")
        total_size += len(file_bytes)
        if total_size > _MAX_TOTAL_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="전체 업로드 크기가 100MB를 초과합니다.")
        fname = FilePath(upload.filename or f"media_{i}.bin").name
        media_tuples.append((fname, file_bytes, mime))

    try:
        result = await link_analyzer_client.analyze_instagram(url, media_tuples, caption, author, language=language)
        logger.info("[DEBUG] link-analyzer instagram raw response: %s", result)
    except UnsupportedPlatformError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ContentExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    except LinkAnalyzerAuthError as exc:
        logger.error("link-analyzer instagram auth error: %s", exc)
        raise HTTPException(status_code=503, detail="분석 서비스 인증 오류입니다.")
    except LinkAnalyzerError as exc:
        logger.error("link-analyzer instagram error: %s", exc)
        raise HTTPException(status_code=503, detail="분석 서비스를 사용할 수 없습니다.")

    content = _build_model(result, user_id)

    if existing and force:
        for attr, val in content.__dict__.items():
            if attr.startswith("_") or attr in _FORCE_UPDATE_PROTECTED_ATTRS:
                continue
            setattr(existing, attr, val)
        db.commit()
        db.refresh(existing)
        if existing.content_type == "place":
            background_tasks.add_task(
                _place_extractor.extract_and_create,
                user_id=user_id,
                **_to_extraction_snapshot(existing),
            )
        return existing

    db.add(content)
    db.commit()
    db.refresh(content)
    if content.content_type == "place":
        background_tasks.add_task(
            _place_extractor.extract_and_create,
            user_id=user_id,
            **_to_extraction_snapshot(content),
        )
    return content


# ------------------------------------------------------------------
# GET /archive — 목록 조회
# ------------------------------------------------------------------

@router.get("", response_model=ArchiveListResponse)
def list_archives(
    content_type: Optional[str] = Query(None, description="place | event | tips | review | unknown"),
    keyword: Optional[str] = Query(None, description="keywords_main 포함 여부로 필터"),
    topic: Optional[str] = Query(None, description="topic_categories 포함 여부로 필터"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Any:
    user_id = _get_user_id(db, current_user)

    q = db.query(ArchivedContent).filter(ArchivedContent.user_id == user_id)
    if content_type:
        q = q.filter(ArchivedContent.content_type == content_type)
    if keyword:
        q = q.filter(ArchivedContent.keywords_main.op("@>")(cast([keyword], ARRAY(Text))))
    if topic:
        q = q.filter(ArchivedContent.topic_categories.op("@>")(cast([topic], ARRAY(Text))))

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
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Any:
    user_id = _get_user_id(db, current_user)
    item = _get_owned_or_404(db, archive_id, user_id)
    return item


# ------------------------------------------------------------------
# DELETE /archive/{id} — 삭제
# ------------------------------------------------------------------

@router.delete("/{archive_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_archive(
    archive_id: UUID,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    user_id = _get_user_id(db, current_user)
    item = _get_owned_or_404(db, archive_id, user_id)
    db.delete(item)
    db.commit()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _to_extraction_snapshot(content: ArchivedContent) -> dict:
    """ORM 객체에서 PlaceExtractorService에 필요한 필드를 세션-독립 dict로 복사한다."""
    import copy
    return {
        "content_type": content.content_type,
        "title": content.title,
        "url": content.url,
        "platform": content.platform,
        "keywords_main": list(content.keywords_main) if content.keywords_main else None,
        "named_entities": list(content.named_entities) if content.named_entities else None,
        "type_specific_data": copy.deepcopy(content.type_specific_data)
        if content.type_specific_data
        else None,
    }


def _normalize_type_specific_data(data) -> dict | None:
    """type_specific_data 내부의 JSON 인코딩된 문자열을 재귀적으로 파싱한다.

    link-analyzer가 중첩 필드(venue 등)를 JSON 문자열로 내보내는 경우를 방어한다.
    """
    if data is None:
        return None
    if isinstance(data, str):
        try:
            data = _json.loads(data)
        except (_json.JSONDecodeError, ValueError):
            return None
    if not isinstance(data, dict):
        return data
    result: dict = {}
    for k, v in data.items():
        if isinstance(v, str):
            try:
                parsed = _json.loads(v)
                result[k] = parsed if isinstance(parsed, (dict, list)) else v
            except (_json.JSONDecodeError, ValueError):
                result[k] = v
        elif isinstance(v, dict):
            result[k] = _normalize_type_specific_data(v)
        else:
            result[k] = v
    return result


def _get_user_id(db: Session, current_user: AuthenticatedUser) -> UUID:
    """firebase_uid로 DB User를 조회하거나 생성해 UUID 반환."""
    user = crud_user.get_or_create_by_firebase_uid(
        db,
        firebase_uid=current_user.firebase_uid,
        email=current_user.email or "",
    )
    return user.id


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

    type_specific_data = _normalize_type_specific_data(analysis.get("type_specific_data"))

    return ArchivedContent(
        user_id=user_id,
        url=data.get("url", ""),
        platform=data.get("platform", ""),
        content_type=analysis.get("content_type") or "unknown",
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
        type_specific_data=type_specific_data,
        link_analyzer_id=data.get("id"),
    )
