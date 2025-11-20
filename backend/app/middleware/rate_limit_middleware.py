"""
전역 API 레이트 리미팅 미들웨어

Redis 기반 Sliding Window 알고리즘을 사용하여
API 요청 속도를 제한합니다.
"""
import time
import logging
from typing import Callable, Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """전역 API 레이트 리미팅 미들웨어"""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_limit: int = 10,
    ):
        """
        레이트 리미팅 미들웨어 초기화

        Args:
            app: FastAPI 애플리케이션
            requests_per_minute: 분당 최대 요청 수
            burst_limit: 버스트 허용량 (현재 미사용, 향후 확장용)
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.window_size = 60  # 1분

        # 인메모리 캐시 (Redis 연결 실패 시 폴백)
        self._memory_cache: dict = {}

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """요청 처리 및 레이트 리미팅 적용"""

        # 클라이언트 식별자
        client_id = self._get_client_id(request)

        # 화이트리스트 경로 확인
        if self._is_whitelisted(request.url.path):
            return await call_next(request)

        # 레이트 리미트 확인
        is_allowed, remaining, reset_time = await self._check_rate_limit(client_id)

        if not is_allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": reset_time,
                },
            )
        else:
            response = await call_next(request)

        # 레이트 리미트 정보 헤더 추가
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_id(self, request: Request) -> str:
        """
        클라이언트 식별자 추출

        인증된 사용자는 토큰 기반, 미인증 사용자는 IP 기반으로 식별
        """
        # Authorization 헤더에서 사용자 식별
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # 토큰의 마지막 16자를 식별자로 사용 (전체 토큰 노출 방지)
            token = auth_header[7:]
            if len(token) > 16:
                return f"user:{token[-16:]}"

        # X-Forwarded-For 헤더 (프록시/로드밸런서 뒤에 있는 경우)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # 첫 번째 IP가 실제 클라이언트 IP
            client_ip = forwarded.split(",")[0].strip()
            return f"ip:{client_ip}"

        # 직접 연결된 클라이언트 IP
        if request.client:
            return f"ip:{request.client.host}"

        return "ip:unknown"

    def _is_whitelisted(self, path: str) -> bool:
        """화이트리스트 경로 확인"""
        whitelist = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            f"{settings.API_V1_STR}/health",
        ]
        return any(path.startswith(p) or path == p for p in whitelist)

    async def _check_rate_limit(
        self,
        client_id: str,
    ) -> Tuple[bool, int, int]:
        """
        레이트 리미트 확인 (Sliding Window Counter)

        Returns:
            Tuple[bool, int, int]: (허용 여부, 남은 요청 수, 리셋까지 초)
        """
        current_time = int(time.time())
        window_key = current_time // self.window_size
        cache_key = f"rate_limit:{client_id}:{window_key}"

        try:
            # Redis 캐시 사용 시도
            from app.utils.cache import cache_service

            count = await cache_service.get(cache_key)
            if count is None:
                count = 0

            if count >= self.requests_per_minute:
                reset_time = self.window_size - (current_time % self.window_size)
                return False, 0, reset_time

            # 카운트 증가
            new_count = count + 1
            ttl = self.window_size - (current_time % self.window_size)
            await cache_service.set(cache_key, new_count, ttl=max(ttl, 1))

            remaining = self.requests_per_minute - new_count
            reset_time = self.window_size - (current_time % self.window_size)

            return True, remaining, reset_time

        except Exception as e:
            logger.warning(f"Redis rate limit check failed, using memory cache: {e}")
            return await self._check_rate_limit_memory(client_id, current_time)

    async def _check_rate_limit_memory(
        self,
        client_id: str,
        current_time: int,
    ) -> Tuple[bool, int, int]:
        """메모리 기반 레이트 리미트 (Redis 폴백)"""
        window_key = current_time // self.window_size
        cache_key = f"{client_id}:{window_key}"

        # 오래된 캐시 정리
        self._cleanup_memory_cache(current_time)

        count = self._memory_cache.get(cache_key, 0)

        if count >= self.requests_per_minute:
            reset_time = self.window_size - (current_time % self.window_size)
            return False, 0, reset_time

        self._memory_cache[cache_key] = count + 1

        remaining = self.requests_per_minute - count - 1
        reset_time = self.window_size - (current_time % self.window_size)

        return True, remaining, reset_time

    def _cleanup_memory_cache(self, current_time: int):
        """오래된 메모리 캐시 엔트리 정리"""
        current_window = current_time // self.window_size

        # 이전 윈도우의 키들 삭제
        keys_to_delete = [
            key for key in self._memory_cache.keys()
            if int(key.split(":")[-1]) < current_window - 1
        ]

        for key in keys_to_delete:
            del self._memory_cache[key]
