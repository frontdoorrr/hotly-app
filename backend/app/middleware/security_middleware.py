"""
보안 헤더 및 요청 검증 미들웨어

OWASP 보안 헤더 권장사항을 적용하고
요청 크기 및 Content-Type을 검증합니다.
"""
import logging
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    보안 헤더 추가 미들웨어

    OWASP 보안 헤더 권장사항을 모든 응답에 적용합니다.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """요청 처리 및 보안 헤더 추가"""
        response = await call_next(request)

        # XSS 방지
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Clickjacking 방지
        response.headers["X-Frame-Options"] = "DENY"

        # HTTPS 강제 (프로덕션)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Content Security Policy
        csp = getattr(settings, "CONTENT_SECURITY_POLICY", "default-src 'self'")
        response.headers["Content-Security-Policy"] = csp

        # Referrer 정책
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 권한 정책 (Permissions Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(self), "
            "microphone=(), "
            "camera=(), "
            "payment=()"
        )

        # 캐시 제어 (민감한 데이터)
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # 서버 정보 숨기기
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    요청 검증 미들웨어

    요청 크기 제한 및 Content-Type 검증을 수행합니다.
    """

    def __init__(
        self,
        app,
        max_request_size_mb: int = 10,
    ):
        """
        요청 검증 미들웨어 초기화

        Args:
            app: FastAPI 애플리케이션
            max_request_size_mb: 최대 요청 크기 (MB)
        """
        super().__init__(app)
        self.max_request_size = max_request_size_mb * 1024 * 1024

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """요청 검증 및 처리"""

        # 요청 크기 제한
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(
                        f"Request too large: {size} bytes from {request.client.host}"
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request entity too large",
                            "max_size_mb": self.max_request_size // (1024 * 1024),
                        },
                    )
            except ValueError:
                pass

        # Content-Type 검증 (POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            # 파일 업로드나 빈 요청이 아닌 경우에만 검증
            if content_length and int(content_length) > 0:
                content_type = request.headers.get("content-type", "")

                allowed_types = [
                    "application/json",
                    "multipart/form-data",
                    "application/x-www-form-urlencoded",
                    "text/plain",  # 일부 테스트 도구 지원
                ]

                if not any(ct in content_type for ct in allowed_types):
                    logger.warning(
                        f"Unsupported content type: {content_type} "
                        f"from {request.client.host}"
                    )
                    return JSONResponse(
                        status_code=415,
                        content={
                            "detail": "Unsupported media type",
                            "supported_types": [
                                "application/json",
                                "multipart/form-data",
                            ],
                        },
                    )

        # Host 헤더 검증 (Host Header Injection 방지)
        host = request.headers.get("host", "")
        allowed_hosts = getattr(settings, "ALLOWED_HOSTS", ["*"])

        if "*" not in allowed_hosts and host:
            # 포트 번호 제거 후 비교
            host_without_port = host.split(":")[0]
            if host_without_port not in allowed_hosts:
                logger.warning(f"Invalid host header: {host}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid host header"},
                )

        return await call_next(request)


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """
    SQL 인젝션 방지 미들웨어

    쿼리 파라미터와 경로에서 의심스러운 SQL 패턴을 감지합니다.
    Note: 이것은 추가적인 방어층으로, 주요 방어는 ORM에서 수행됩니다.
    """

    # 의심스러운 SQL 패턴
    SUSPICIOUS_PATTERNS = [
        "' OR '",
        "' OR 1=1",
        "'; DROP",
        "UNION SELECT",
        "UNION ALL SELECT",
        "--",
        "/*",
        "*/",
        "xp_",
        "sp_",
    ]

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """SQL 인젝션 패턴 검사"""

        # URL 경로 검사
        path = request.url.path.upper()

        # 쿼리 파라미터 검사
        query_string = str(request.query_params).upper()

        combined = path + query_string

        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern.upper() in combined:
                logger.warning(
                    f"Potential SQL injection detected: {pattern} "
                    f"from {request.client.host} - Path: {request.url.path}"
                )
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request"},
                )

        return await call_next(request)
