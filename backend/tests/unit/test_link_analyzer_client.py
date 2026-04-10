"""Unit tests for LinkAnalyzerClient._handle_response error mapping."""

from unittest.mock import MagicMock

import pytest

from app.services.link_analyzer_client import (
    ContentExtractionError,
    LinkAnalyzerAuthError,
    LinkAnalyzerClient,
    LinkAnalyzerError,
    UnsupportedPlatformError,
)


def _make_response(status_code: int, body: dict | None = None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = str(body)
    resp.json.return_value = body or {}
    return resp


class TestHandleResponse:
    def setup_method(self):
        self.client = LinkAnalyzerClient.__new__(LinkAnalyzerClient)

    def test_200_returnsJsonBody(self):
        body = {"id": "abc", "url": "https://example.com", "platform": "youtube"}
        resp = _make_response(200, body)
        result = self.client._handle_response(resp)
        assert result == body

    def test_201_returnsJsonBody(self):
        body = {"id": "xyz"}
        resp = _make_response(201, body)
        assert self.client._handle_response(resp) == body

    def test_401_raisesLinkAnalyzerAuthError(self):
        resp = _make_response(401, {"detail": {"code": "UNAUTHORIZED", "message": "Invalid API key"}})
        with pytest.raises(LinkAnalyzerAuthError):
            self.client._handle_response(resp)

    def test_400_unsupportedPlatform_raisesUnsupportedPlatformError(self):
        resp = _make_response(400, {"detail": {"code": "UNSUPPORTED_PLATFORM", "message": "TikTok은 지원하지 않습니다"}})
        with pytest.raises(UnsupportedPlatformError):
            self.client._handle_response(resp)

    def test_500_extractionFailed_raisesContentExtractionError(self):
        resp = _make_response(500, {"detail": {"code": "EXTRACTION_FAILED", "message": "비공개 게시물"}})
        with pytest.raises(ContentExtractionError):
            self.client._handle_response(resp)

    def test_503_genericError_raisesLinkAnalyzerError(self):
        resp = _make_response(503, {"detail": {"code": "SERVICE_UNAVAILABLE", "message": "down"}})
        with pytest.raises(LinkAnalyzerError):
            self.client._handle_response(resp)

    def test_400_otherCode_raisesLinkAnalyzerError(self):
        resp = _make_response(400, {"detail": {"code": "INVALID_URL", "message": "잘못된 URL"}})
        with pytest.raises(LinkAnalyzerError):
            self.client._handle_response(resp)

    def test_responseBodyNotJson_raisesLinkAnalyzerError(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Server Error"
        resp.json.side_effect = Exception("not json")
        with pytest.raises(LinkAnalyzerError):
            self.client._handle_response(resp)


class TestBuildModel:
    """Test _build_model helper in archive endpoint."""

    def test_buildModel_fullData_mapsAllFields(self):
        from uuid import uuid4
        from app.api.api_v1.endpoints.archive import _build_model

        user_id = uuid4()
        data = {
            "id": str(uuid4()),
            "url": "https://www.youtube.com/watch?v=test",
            "platform": "youtube",
            "metadata": {
                "title": "서울 맛집 추천",
                "author": "푸드채널",
                "thumbnail_url": "https://img.example.com/thumb.jpg",
                "language": "ko",
            },
            "analysis": {
                "content_type": "place",
                "summary": "강남 맛집 5선",
                "keywords": {
                    "main": ["강남", "맛집"],
                    "sub": ["파스타", "브런치"],
                    "named_entities": ["논현동"],
                },
                "categories": {"topic": ["음식", "여행"]},
                "sentiment": "positive",
                "action_items": {
                    "todos": ["예약 필요"],
                    "insights": ["점심 피크 혼잡"],
                },
                "type_specific_data": {"address": "서울 강남구"},
            },
        }

        model = _build_model(data, user_id)

        assert model.user_id == user_id
        assert model.url == data["url"]
        assert model.platform == "youtube"
        assert model.content_type == "place"
        assert model.title == "서울 맛집 추천"
        assert model.summary == "강남 맛집 5선"
        assert model.keywords_main == ["강남", "맛집"]
        assert model.sentiment == "positive"
        assert model.type_specific_data == {"address": "서울 강남구"}

    def test_buildModel_missingOptionalFields_usesDefaults(self):
        from uuid import uuid4
        from app.api.api_v1.endpoints.archive import _build_model

        user_id = uuid4()
        data = {"url": "https://instagram.com/p/abc", "platform": "instagram"}

        model = _build_model(data, user_id)

        assert model.user_id == user_id
        assert model.content_type == "unknown"
        assert model.title is None
        assert model.summary is None
