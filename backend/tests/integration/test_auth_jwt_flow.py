"""
Firebase → JWT 인증 플로우 통합 테스트

전체 인증 흐름을 테스트합니다:
1. 소셜 로그인 → JWT 토큰 발급
2. JWT 토큰 검증
3. JWT 토큰 갱신
4. 레이트 리미팅 통합
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.api.api_v1.endpoints.auth import router
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
)
from app.services.auth.firebase_auth_service import FirebaseAuthService
from app.schemas.auth import SocialProvider


@pytest.fixture
def app():
    """테스트용 FastAPI 앱"""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/auth")
    return app


@pytest.fixture
def client(app):
    """동기 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def auth_service():
    """모의 Firebase Auth 서비스"""
    service = FirebaseAuthService(
        firebase_app=None,
        firebase_auth=MagicMock()
    )
    service.cache = AsyncMock()
    return service


class TestSocialLoginToJWTFlow:
    """소셜 로그인 → JWT 발급 플로우 테스트"""

    @pytest.mark.asyncio
    async def test_socialLogin_withGoogle_returnsJWTTokens(self, auth_service):
        """Google 소셜 로그인 시 JWT 토큰 반환"""
        # Google 인증 모의
        auth_service.firebase_auth.verify_id_token = MagicMock(
            return_value={
                "uid": "google_user_123",
                "email": "user@gmail.com",
                "name": "Test User",
                "picture": "https://example.com/photo.jpg",
                "email_verified": True,
            }
        )
        auth_service.cache.get = AsyncMock(return_value=None)
        auth_service.cache.set = AsyncMock()
        # Note: Rate limiting은 API 엔드포인트 레벨에서 처리됨

        from app.schemas.auth import SocialLoginRequest

        request = SocialLoginRequest(
            provider=SocialProvider.GOOGLE,
            id_token="valid_google_id_token",
            device_id="device_123"
        )

        result = await auth_service.login_with_social(request)

        assert result.success is True
        assert result.access_token is not None
        assert result.refresh_token is not None

        # JWT 토큰 검증
        payload = verify_access_token(result.access_token)
        assert payload is not None
        assert "sub" in payload

    @pytest.mark.asyncio
    async def test_socialLogin_withKakao_returnsJWTTokens(self, auth_service):
        """Kakao 소셜 로그인 시 JWT 토큰 반환"""
        auth_service.cache.get = AsyncMock(return_value=None)
        auth_service.cache.set = AsyncMock()
        # Rate limiting handled at endpoint level

        # Kakao API 호출 모의
        with patch("app.services.auth.firebase_auth_service.REQUESTS_AVAILABLE", False):
            from app.schemas.auth import SocialLoginRequest

            request = SocialLoginRequest(
                provider=SocialProvider.KAKAO,
                access_token="kakao_access_token",
                device_id="device_123"
            )

            result = await auth_service.login_with_social(request)

            assert result.success is True
            assert result.access_token is not None

            # JWT 검증
            payload = verify_access_token(result.access_token)
            assert payload is not None


class TestTokenValidationFlow:
    """토큰 검증 플로우 테스트"""

    @pytest.mark.asyncio
    async def test_validateToken_withOurJWT_returnsUserInfo(self, auth_service):
        """우리 JWT 검증 시 사용자 정보 반환"""
        auth_service.cache.get = AsyncMock(return_value=None)

        # JWT 토큰 생성
        token = create_access_token(
            subject="user_123",
            additional_claims={"email": "user@example.com"}
        )

        result = await auth_service.validate_access_token(token)

        assert result.is_valid is True
        assert result.user_id == "user_123"
        assert result.email == "user@example.com"

    @pytest.mark.asyncio
    async def test_validateToken_withExpiredJWT_returnsInvalid(self, auth_service):
        """만료된 JWT 검증 시 무효 반환"""
        auth_service.cache.get = AsyncMock(return_value=None)

        # 만료된 토큰 생성
        token = create_access_token(
            subject="user_123",
            expires_delta=timedelta(seconds=-1)
        )

        result = await auth_service.validate_access_token(token)

        assert result.is_valid is False

    @pytest.mark.asyncio
    async def test_validateToken_fallsBackToFirebase(self, auth_service):
        """우리 JWT가 아닌 경우 Firebase로 폴백"""
        auth_service.cache.get = AsyncMock(return_value=None)

        # Firebase 토큰 검증 모의
        auth_service.firebase_auth.verify_id_token = MagicMock(
            return_value={
                "uid": "firebase_user_456",
                "email": "firebase@example.com",
                "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            }
        )

        # Firebase 토큰으로 검증 (JWT 형식이지만 우리 키로 서명되지 않음)
        result = await auth_service.validate_access_token("firebase.id.token")

        assert result.is_valid is True
        assert result.user_id == "firebase_user_456"


class TestTokenRefreshFlow:
    """토큰 갱신 플로우 테스트"""

    @pytest.mark.asyncio
    async def test_refreshToken_withValidJWT_returnsNewTokens(self, auth_service):
        """유효한 JWT 리프레시 토큰으로 새 토큰 발급"""
        auth_service.cache.get = AsyncMock(return_value=None)
        auth_service.cache.set = AsyncMock()
        # Rate limiting handled at endpoint level

        # 리프레시 토큰 생성
        refresh_token = create_refresh_token(subject="user_123")

        from app.schemas.auth import TokenRefreshRequest

        request = TokenRefreshRequest(
            refresh_token=refresh_token,
            device_id="device_123"
        )

        result = await auth_service.refresh_tokens(request)

        assert result.success is True
        assert result.new_access_token is not None
        assert result.new_refresh_token is not None

        # 새 액세스 토큰 검증
        payload = verify_access_token(result.new_access_token)
        assert payload is not None
        assert payload.get("sub") == "user_123"

    @pytest.mark.asyncio
    async def test_refreshToken_withLegacyToken_stillWorks(self, auth_service):
        """레거시 캐시 기반 토큰도 여전히 작동"""
        # 레거시 토큰 캐시 데이터
        legacy_token_data = {
            "user_id": "legacy_user_789",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        auth_service.cache.get = AsyncMock(return_value=legacy_token_data)
        auth_service.cache.set = AsyncMock()
        auth_service.cache.delete = AsyncMock()
        # Rate limiting handled at endpoint level

        from app.schemas.auth import TokenRefreshRequest

        request = TokenRefreshRequest(
            refresh_token="legacy_refresh_token_format",
            device_id="device_123"
        )

        result = await auth_service.refresh_tokens(request)

        assert result.success is True
        assert result.new_access_token is not None


class TestCompleteAuthFlow:
    """전체 인증 플로우 테스트"""

    @pytest.mark.asyncio
    async def test_completeFlow_login_validate_refresh(self, auth_service):
        """로그인 → 검증 → 갱신 전체 플로우"""
        auth_service.cache.get = AsyncMock(return_value=None)
        auth_service.cache.set = AsyncMock()
        # Rate limiting handled at endpoint level

        # 1. 소셜 로그인 (Mock)
        with patch("app.services.auth.firebase_auth_service.REQUESTS_AVAILABLE", False):
            from app.schemas.auth import SocialLoginRequest, TokenRefreshRequest

            login_request = SocialLoginRequest(
                provider=SocialProvider.KAKAO,
                access_token="kakao_token",
                device_id="device_123"
            )

            login_result = await auth_service.login_with_social(login_request)
            assert login_result.success is True

            # 2. 액세스 토큰 검증
            validate_result = await auth_service.validate_access_token(
                login_result.access_token
            )
            assert validate_result.is_valid is True

            # 3. 토큰 갱신
            refresh_request = TokenRefreshRequest(
                refresh_token=login_result.refresh_token,
                device_id="device_123"
            )

            refresh_result = await auth_service.refresh_tokens(refresh_request)
            assert refresh_result.success is True

            # 4. 새 토큰 검증
            new_validate_result = await auth_service.validate_access_token(
                refresh_result.new_access_token
            )
            assert new_validate_result.is_valid is True


class TestRateLimitingIntegration:
    """레이트 리미팅 통합 테스트"""

    @pytest.mark.asyncio
    async def test_authRateLimiter_exceedsLimit_raisesHTTPException(self):
        """AuthRateLimiter 레이트 리미트 초과 시 HTTPException 발생"""
        from app.middleware.auth_rate_limit import AuthRateLimiter
        from fastapi import HTTPException
        from unittest.mock import MagicMock

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        with patch("app.middleware.auth_rate_limit.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=10)  # 제한 도달

            with pytest.raises(HTTPException) as exc_info:
                await AuthRateLimiter.check_rate_limit(mock_request, "login")

            assert exc_info.value.status_code == 429
            assert "rate_limit_exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_multipleEndpoints_haveDifferentLimits(self):
        """각 엔드포인트는 다른 레이트 리미트 적용"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        # 로그인: 10/분
        assert AuthRateLimiter.RATE_LIMITS["login"]["requests"] == 10
        assert AuthRateLimiter.RATE_LIMITS["login"]["window"] == 60

        # 갱신: 60/시간
        assert AuthRateLimiter.RATE_LIMITS["refresh"]["requests"] == 60
        assert AuthRateLimiter.RATE_LIMITS["refresh"]["window"] == 3600

        # 검증: 30/분
        assert AuthRateLimiter.RATE_LIMITS["verify"]["requests"] == 30
        assert AuthRateLimiter.RATE_LIMITS["verify"]["window"] == 60


class TestBackwardCompatibility:
    """하위 호환성 테스트"""

    @pytest.mark.asyncio
    async def test_legacyTokenFormat_stillAccepted(self, auth_service):
        """레거시 토큰 형식도 여전히 허용"""
        # 레거시 캐시 토큰
        legacy_data = {
            "user_id": "old_user_123",
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        }
        auth_service.cache.get = AsyncMock(return_value=legacy_data)

        result = await auth_service.validate_access_token("old_format_token")

        assert result.is_valid is True
        assert result.user_id == "old_user_123"

    @pytest.mark.asyncio
    async def test_firebaseToken_stillAccepted(self, auth_service):
        """Firebase ID 토큰도 여전히 허용"""
        auth_service.cache.get = AsyncMock(return_value=None)
        auth_service.firebase_auth.verify_id_token = MagicMock(
            return_value={
                "uid": "firebase_user",
                "email": "user@firebase.com",
                "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
            }
        )

        result = await auth_service.validate_access_token("firebase.token.here")

        assert result.is_valid is True
        assert result.user_id == "firebase_user"
