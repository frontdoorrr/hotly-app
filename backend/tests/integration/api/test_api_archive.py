"""Integration tests for POST/GET/DELETE /api/v1/archive endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.archive import router
from app.db.deps import get_db
from app.middleware.jwt_middleware import get_current_active_user
from app.models.archived_content import ArchivedContent
from app.services.link_analyzer_client import (
    ContentExtractionError,
    LinkAnalyzerAuthError,
    UnsupportedPlatformError,
)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

USER_ID = uuid4()
AUTH_USER = {"uid": str(USER_ID), "email": "test@example.com"}

ANALYZER_RESPONSE = {
    "id": str(uuid4()),
    "url": "https://www.youtube.com/watch?v=test",
    "platform": "youtube",
    "metadata": {
        "title": "서울 맛집 BEST 5",
        "author": "푸드스타",
        "thumbnail_url": "https://img.example.com/thumb.jpg",
        "language": "ko",
    },
    "analysis": {
        "content_type": "place",
        "summary": "강남 맛집 5곳 소개",
        "keywords": {"main": ["강남", "맛집"], "sub": [], "named_entities": []},
        "categories": {"topic": ["음식"]},
        "sentiment": "positive",
        "action_items": {"todos": [], "insights": []},
        "type_specific_data": {"address": "서울 강남구 논현동"},
    },
}


def _make_db_content(user_id=USER_ID, url=ANALYZER_RESPONSE["url"]) -> ArchivedContent:
    content = ArchivedContent()
    content.id = uuid4()
    content.user_id = user_id
    content.url = url
    content.platform = "youtube"
    content.content_type = "place"
    content.title = "서울 맛집 BEST 5"
    content.summary = "강남 맛집 5곳 소개"
    content.keywords_main = ["강남", "맛집"]
    content.keywords_sub = []
    content.named_entities = []
    content.topic_categories = ["음식"]
    content.sentiment = "positive"
    content.todos = []
    content.insights = []
    content.type_specific_data = {"address": "서울 강남구 논현동"}
    content.link_analyzer_id = uuid4()
    content.archived_at = datetime.now(timezone.utc)
    return content


def _make_app(mock_db: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/archive")
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_active_user] = lambda: AUTH_USER
    return app


# ------------------------------------------------------------------
# POST /archive
# ------------------------------------------------------------------

class TestPostArchive:
    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_newUrl_analyzesAndReturns201(self, mock_client):
        mock_client.analyze = AsyncMock(return_value=ANALYZER_RESPONSE)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        saved = _make_db_content()
        db.refresh.side_effect = lambda obj: None

        def add_side_effect(obj):
            obj.id = saved.id
            obj.archived_at = saved.archived_at

        db.add.side_effect = add_side_effect

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": ANALYZER_RESPONSE["url"]})

        assert resp.status_code == 201
        assert resp.json()["content_type"] == "place"
        assert resp.json()["platform"] == "youtube"
        mock_client.analyze.assert_called_once_with(ANALYZER_RESPONSE["url"], force=False)

    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_duplicateUrl_forcefalse_returnsExisting200(self, mock_client):
        existing = _make_db_content()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": existing.url, "force": False})

        assert resp.status_code == 201  # FastAPI returns 201 (status_code of route)
        mock_client.analyze.assert_not_called()

    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_duplicateUrl_forceTrue_reanalyzesAndUpdates(self, mock_client):
        mock_client.analyze = AsyncMock(return_value=ANALYZER_RESPONSE)
        existing = _make_db_content()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = existing

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": existing.url, "force": True})

        assert resp.status_code == 201
        mock_client.analyze.assert_called_once_with(existing.url, force=True)
        db.commit.assert_called()

    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_unsupportedPlatform_returns400(self, mock_client):
        mock_client.analyze = AsyncMock(
            side_effect=UnsupportedPlatformError("TikTok은 지원하지 않습니다")
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": "https://tiktok.com/video/123"})

        assert resp.status_code == 400

    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_extractionFailed_returns422(self, mock_client):
        mock_client.analyze = AsyncMock(
            side_effect=ContentExtractionError("비공개 게시물입니다")
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": "https://www.instagram.com/p/private"})

        assert resp.status_code == 422

    @patch("app.api.api_v1.endpoints.archive.link_analyzer_client")
    def test_authError_returns503(self, mock_client):
        mock_client.analyze = AsyncMock(
            side_effect=LinkAnalyzerAuthError("Invalid API key")
        )
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(_make_app(db))
        resp = client.post("/archive", json={"url": "https://www.youtube.com/watch?v=test"})

        assert resp.status_code == 503


# ------------------------------------------------------------------
# GET /archive
# ------------------------------------------------------------------

class TestGetArchiveList:
    def test_listArchives_returnsItems(self):
        items = [_make_db_content(), _make_db_content()]
        db = MagicMock()
        q = db.query.return_value.filter.return_value
        q.count.return_value = 2
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = items

        client = TestClient(_make_app(db))
        resp = client.get("/archive")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_listArchives_contentTypeFilter_queriesWithFilter(self):
        db = MagicMock()
        q = db.query.return_value.filter.return_value
        q.filter.return_value = q
        q.count.return_value = 0
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        client = TestClient(_make_app(db))
        resp = client.get("/archive?content_type=place")

        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_listArchives_pagination(self):
        db = MagicMock()
        q = db.query.return_value.filter.return_value
        q.count.return_value = 50
        q.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        client = TestClient(_make_app(db))
        resp = client.get("/archive?page=2&page_size=10")

        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 2
        assert data["page_size"] == 10


# ------------------------------------------------------------------
# GET /archive/{id}
# ------------------------------------------------------------------

class TestGetArchiveDetail:
    def test_getArchive_ownedItem_returns200(self):
        item = _make_db_content()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = item

        client = TestClient(_make_app(db))
        resp = client.get(f"/archive/{item.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(item.id)

    def test_getArchive_notFound_returns404(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(_make_app(db))
        resp = client.get(f"/archive/{uuid4()}")

        assert resp.status_code == 404

    def test_getArchive_otherUserItem_returns403(self):
        other_user_item = _make_db_content(user_id=uuid4())  # different user
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = other_user_item

        client = TestClient(_make_app(db))
        resp = client.get(f"/archive/{other_user_item.id}")

        assert resp.status_code == 403


# ------------------------------------------------------------------
# DELETE /archive/{id}
# ------------------------------------------------------------------

class TestDeleteArchive:
    def test_deleteArchive_ownedItem_returns204(self):
        item = _make_db_content()
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = item

        client = TestClient(_make_app(db))
        resp = client.delete(f"/archive/{item.id}")

        assert resp.status_code == 204
        db.delete.assert_called_once_with(item)
        db.commit.assert_called_once()

    def test_deleteArchive_notFound_returns404(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        client = TestClient(_make_app(db))
        resp = client.delete(f"/archive/{uuid4()}")

        assert resp.status_code == 404

    def test_deleteArchive_otherUserItem_returns403(self):
        other_user_item = _make_db_content(user_id=uuid4())
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = other_user_item

        client = TestClient(_make_app(db))
        resp = client.delete(f"/archive/{other_user_item.id}")

        assert resp.status_code == 403
        db.delete.assert_not_called()
