"""HTTP client for the external link-analyzer service."""

import logging
from typing import Any, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkAnalyzerError(Exception):
    pass


class UnsupportedPlatformError(LinkAnalyzerError):
    pass


class ContentExtractionError(LinkAnalyzerError):
    pass


class LinkAnalyzerAuthError(LinkAnalyzerError):
    pass


class RateLimitError(LinkAnalyzerError):
    pass


class LinkAnalyzerClient:
    """Thin HTTP client wrapping the link-analyzer REST API."""

    def __init__(self) -> None:
        self._base_url = settings.LINK_ANALYZER_BASE_URL.rstrip("/")
        self._headers = {
            "X-API-Key": settings.LINK_ANALYZER_API_KEY or "",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(self, url: str, force: bool = False) -> dict[str, Any]:
        """Submit a URL for analysis and return the ContentResponse dict.

        Raises:
            UnsupportedPlatformError: URL 플랫폼 미지원
            ContentExtractionError:   콘텐츠 추출 실패 (비공개 등)
            LinkAnalyzerAuthError:    API 키 인증 실패
            LinkAnalyzerError:        기타 오류
        """
        payload = {"url": url, "force": force}
        async with httpx.AsyncClient(timeout=120) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/api/v1/analyze",
                    headers=self._headers,
                    json=payload,
                )
            except httpx.RequestError as exc:
                raise LinkAnalyzerError(f"link-analyzer 연결 실패: {exc}") from exc

        return self._handle_response(resp)

    async def analyze_instagram(
        self,
        url: str,
        media_files: list[tuple[str, bytes, str]],
        caption: Optional[str] = None,
        author: Optional[str] = None,
    ) -> dict[str, Any]:
        """Instagram 미디어 파일을 multipart로 link-analyzer에 전달한다.

        media_files: [(filename, bytes, mime_type), ...]
        """
        files = [("media", (name, data, mime)) for name, data, mime in media_files]
        data: dict[str, str] = {"url": url}
        if caption:
            data["caption"] = caption
        if author:
            data["author"] = author
        headers = {"X-API-Key": self._headers["X-API-Key"]}
        timeout = httpx.Timeout(
            connect=10.0,
            read=float(settings.LINK_ANALYZER_INSTAGRAM_TIMEOUT),
            write=60.0,
            pool=10.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/api/v1/analyze/instagram",
                    headers=headers,
                    data=data,
                    files=files,
                )
            except httpx.RequestError as exc:
                raise LinkAnalyzerError(f"link-analyzer 연결 실패: {exc}") from exc

        return self._handle_response(resp)

    async def get_content(self, content_id: str) -> dict[str, Any]:
        """Fetch a previously analyzed content by its link-analyzer ID."""
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{self._base_url}/api/v1/contents/{content_id}",
                    headers=self._headers,
                )
            except httpx.RequestError as exc:
                raise LinkAnalyzerError(f"link-analyzer 연결 실패: {exc}") from exc

        return self._handle_response(resp)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_response(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code in (200, 201):
            return resp.json()

        error_body: dict = {}
        try:
            error_body = resp.json()
        except Exception:
            pass

        detail = error_body.get("detail", {})
        if isinstance(detail, dict):
            code = detail.get("code", "")
            message = detail.get("message", resp.text)
        else:
            code = ""
            message = str(detail) if detail else resp.text

        if resp.status_code == 401:
            raise LinkAnalyzerAuthError(message)
        if resp.status_code == 429:
            raise RateLimitError(message)
        if resp.status_code == 400 and code == "UNSUPPORTED_PLATFORM":
            raise UnsupportedPlatformError(message)
        if resp.status_code == 400 and code == "FILE_TOO_LARGE":
            raise ContentExtractionError(message)
        if resp.status_code == 500 and code == "EXTRACTION_FAILED":
            raise ContentExtractionError(message)

        logger.error("link-analyzer error %s %s: %s", resp.status_code, code, message)
        raise LinkAnalyzerError(f"[{resp.status_code}] {code}: {message}")


link_analyzer_client = LinkAnalyzerClient()
