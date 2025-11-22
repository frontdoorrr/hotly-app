"""
인증 엔드포인트 전용 레이트 리미팅

인증 관련 엔드포인트에 대해 엄격한 레이트 리미팅을 적용합니다.
브루트포스 공격 및 남용을 방지합니다.
"""
import time
import logging
from typing import Optional
from functools import wraps

from fastapi import HTTPException, Request, status
from starlette.responses import JSONResponse

from app.core.config import settings
from app.utils.cache import cache_service

logger = logging.getLogger(__name__)


class AuthRateLimiter:
    """인증 엔드포인트 전용 레이트 리미터"""

    # 엔드포인트별 레이트 리미트 설정
    RATE_LIMITS = {
        "login": {
            "requests": 10,
            "window": 60,  # 1분
            "message": "로그인 시도 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        },
        "refresh": {
            "requests": 60,
            "window": 3600,  # 1시간
            "message": "토큰 갱신 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        },
        "verify": {
            "requests": 30,
            "window": 60,  # 1분
            "message": "토큰 검증 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        },
        "signup": {
            "requests": 5,
            "window": 3600,  # 1시간
            "message": "회원가입 시도 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        },
        "password_reset": {
            "requests": 3,
            "window": 3600,  # 1시간
            "message": "비밀번호 재설정 시도 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
        },
    }

    @classmethod
    async def check_rate_limit(
        cls,
        request: Request,
        operation: str,
        identifier: Optional[str] = None,
    ) -> bool:
        """
        레이트 리미트 확인

        Args:
            request: FastAPI 요청 객체
            operation: 작업 유형 (login, refresh, verify 등)
            identifier: 클라이언트 식별자 (없으면 IP 사용)

        Returns:
            허용 여부

        Raises:
            HTTPException: 레이트 리미트 초과 시
        """
        if operation not in cls.RATE_LIMITS:
            return True

        config = cls.RATE_LIMITS[operation]

        # 클라이언트 식별
        if not identifier:
            identifier = cls._get_client_identifier(request)

        # 레이트 리미트 키
        rate_key = f"auth_rate:{operation}:{identifier}"

        try:
            current_time = int(time.time())
            window_key = current_time // config["window"]
            cache_key = f"{rate_key}:{window_key}"

            # 현재 카운트 조회
            count = await cache_service.get(cache_key)
            if count is None:
                count = 0

            if count >= config["requests"]:
                # 리셋까지 남은 시간 계산
                reset_time = config["window"] - (current_time % config["window"])

                logger.warning(
                    f"Auth rate limit exceeded: {operation} for {identifier}"
                )

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": config["message"],
                        "retry_after": reset_time,
                    },
                    headers={
                        "Retry-After": str(reset_time),
                        "X-RateLimit-Limit": str(config["requests"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_time),
                    },
                )

            # 카운트 증가
            ttl = config["window"] - (current_time % config["window"])
            await cache_service.set(cache_key, count + 1, ttl=max(ttl, 1))

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Auth rate limit check failed: {e}")
            # 에러 시에는 허용 (가용성 우선)
            return True

    @staticmethod
    def _get_client_identifier(request: Request) -> str:
        """클라이언트 식별자 추출"""
        # X-Forwarded-For 헤더 (프록시 뒤에 있는 경우)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # 직접 연결된 클라이언트 IP
        if request.client:
            return request.client.host

        return "unknown"


def auth_rate_limit(operation: str):
    """
    인증 레이트 리미팅 데코레이터

    사용 예:
        @router.post("/login")
        @auth_rate_limit("login")
        async def login(request: Request, ...):
            ...

    Args:
        operation: 작업 유형 (login, refresh, verify 등)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Request 객체 찾기
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                request = kwargs.get("request")

            if request:
                await AuthRateLimiter.check_rate_limit(request, operation)

            return await func(*args, **kwargs)
        return wrapper
    return decorator


# FastAPI Depends로 사용할 수 있는 함수들
async def check_login_rate_limit(request: Request):
    """로그인 레이트 리미트 체크 (Depends용)"""
    await AuthRateLimiter.check_rate_limit(request, "login")


async def check_refresh_rate_limit(request: Request):
    """토큰 갱신 레이트 리미트 체크 (Depends용)"""
    await AuthRateLimiter.check_rate_limit(request, "refresh")


async def check_verify_rate_limit(request: Request):
    """토큰 검증 레이트 리미트 체크 (Depends용)"""
    await AuthRateLimiter.check_rate_limit(request, "verify")


async def check_signup_rate_limit(request: Request):
    """회원가입 레이트 리미트 체크 (Depends용)"""
    await AuthRateLimiter.check_rate_limit(request, "signup")


async def check_password_reset_rate_limit(request: Request):
    """비밀번호 재설정 레이트 리미트 체크 (Depends용)"""
    await AuthRateLimiter.check_rate_limit(request, "password_reset")
