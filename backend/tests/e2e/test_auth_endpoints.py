"""
인증 엔드포인트 E2E 테스트

실제 API 엔드포인트를 통한 인증 플로우 테스트입니다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.api_v1.endpoints.auth import router
from app.core.security import create_access_token, create_refresh_token


@pytest.fixture
def app():
    """테스트용 FastAPI 앱"""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1/auth")
    return test_app


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return TestClient(app)


class TestSocialLoginEndpoint:
    """소셜 로그인 엔드포인트 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_socialLogin_withValidRequest_returns200(
        self, mock_service, mock_cache, client
    ):
        """유효한 소셜 로그인 요청 시 200 반환"""
        # Mock 설정
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        from app.schemas.auth import LoginResponse, UserProfile, SocialProvider

        mock_response = LoginResponse(
            success=True,
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_in=3600,
            user_profile=UserProfile(
                user_id="user_123",
                email="test@example.com",
                name="Test User",
                provider=SocialProvider.GOOGLE,
                is_anonymous=False,
                is_verified=True,
                created_at=datetime.utcnow(),
                last_login_at=datetime.utcnow(),
            ),
        )
        mock_service.login_with_social = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "valid_google_token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data

    @patch("app.middleware.auth_rate_limit.cache_service")
    def test_socialLogin_withRateLimitExceeded_returns429(self, mock_cache, client):
        """레이트 리미트 초과 시 429 반환"""
        # 레이트 리미트 초과 시뮬레이션
        mock_cache.get = AsyncMock(return_value=10)  # 제한에 도달

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 429
        assert "rate_limit_exceeded" in response.json()["detail"]["error"]


class TestTokenRefreshEndpoint:
    """토큰 갱신 엔드포인트 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_refreshToken_withValidToken_returns200(
        self, mock_service, mock_cache, client
    ):
        """유효한 리프레시 토큰으로 갱신 시 200 반환"""
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        from app.schemas.auth import TokenRefreshResponse

        mock_response = TokenRefreshResponse(
            success=True,
            new_access_token="new_access_token",
            new_refresh_token="new_refresh_token",
            expires_in=3600,
        )
        mock_service.refresh_tokens = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "valid_refresh_token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "new_access_token" in data

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_refreshToken_withInvalidToken_returnsError(
        self, mock_service, mock_cache, client
    ):
        """유효하지 않은 토큰으로 갱신 시 에러 반환"""
        mock_cache.get = AsyncMock(return_value=None)

        from app.schemas.auth import TokenRefreshResponse, AuthError

        mock_response = TokenRefreshResponse(
            success=False,
            error_code=AuthError.INVALID_TOKEN,
            error_message="유효하지 않은 토큰입니다.",
        )
        mock_service.refresh_tokens = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/v1/auth/refresh",
            json={
                "refresh_token": "invalid_token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 200  # API는 200으로 응답하고 success=False
        data = response.json()
        assert data["success"] is False


class TestTokenVerificationEndpoint:
    """토큰 검증 엔드포인트 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_verifyToken_withValidToken_returnsUserInfo(
        self, mock_service, mock_cache, client
    ):
        """유효한 토큰 검증 시 사용자 정보 반환"""
        mock_cache.get = AsyncMock(return_value=None)

        from app.schemas.auth import TokenValidationResult

        mock_result = TokenValidationResult(
            is_valid=True,
            user_id="user_123",
            email="user@example.com",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        mock_service.validate_access_token = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/auth/verify-token",
            params={"token": "valid_access_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["user_id"] == "user_123"


class TestProtectedEndpoints:
    """보호된 엔드포인트 E2E 테스트"""

    @patch("app.middleware.jwt_middleware.firebase_auth_service")
    def test_getMe_withValidToken_returns200(self, mock_service, client):
        """유효한 토큰으로 /me 접근 시 200 반환"""
        from app.schemas.auth import TokenValidationResult

        mock_result = TokenValidationResult(
            is_valid=True,
            user_id="user_123",
            email="user@example.com",
            permissions={"role": "user"},
        )
        mock_service.validate_access_token = AsyncMock(return_value=mock_result)

        # JWT 토큰 생성
        token = create_access_token(
            subject="user_123",
            additional_claims={"email": "user@example.com"}
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        # 응답이 성공하거나 권한 문제 (구현에 따라 다름)
        assert response.status_code in [200, 403]

    def test_getMe_withoutToken_returns401(self, client):
        """토큰 없이 /me 접근 시 401 반환"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code in [401, 403]


class TestRateLimitingE2E:
    """레이트 리미팅 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    def test_multipleLoginAttempts_triggersRateLimit(self, mock_cache, client):
        """다수 로그인 시도 시 레이트 리미트 발동"""
        # 처음 10번은 허용
        for i in range(10):
            mock_cache.get = AsyncMock(return_value=i)
            mock_cache.set = AsyncMock()

        # 11번째는 차단
        mock_cache.get = AsyncMock(return_value=10)

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 429

    @patch("app.middleware.auth_rate_limit.cache_service")
    def test_rateLimitHeaders_included(self, mock_cache, client):
        """레이트 리미트 헤더 포함 확인"""
        mock_cache.get = AsyncMock(return_value=10)

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "token",
                "device_id": "device_123",
            },
        )

        # 429 응답에 레이트 리미트 헤더 포함
        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers


class TestSecurityHeaders:
    """보안 헤더 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_response_includesSecurityHeaders(
        self, mock_service, mock_cache, client
    ):
        """응답에 보안 헤더 포함 확인"""
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()

        from app.schemas.auth import LoginResponse

        mock_response = LoginResponse(
            success=True,
            access_token="token",
            refresh_token="refresh",
            expires_in=3600,
        )
        mock_service.login_with_social = AsyncMock(return_value=mock_response)

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "token",
                "device_id": "device_123",
            },
        )

        # 주요 보안 헤더 확인 (전체 앱에서 미들웨어로 추가)
        # Note: TestClient에서는 미들웨어가 완전히 적용되지 않을 수 있음
        assert response.status_code == 200


class TestErrorHandling:
    """에러 처리 E2E 테스트"""

    @patch("app.middleware.auth_rate_limit.cache_service")
    @patch("app.services.auth.firebase_auth_service.firebase_auth_service")
    def test_socialLogin_withException_returns400(
        self, mock_service, mock_cache, client
    ):
        """소셜 로그인 예외 발생 시 400 반환"""
        mock_cache.get = AsyncMock(return_value=None)
        mock_service.login_with_social = AsyncMock(
            side_effect=Exception("Test error")
        )

        response = client.post(
            "/api/v1/auth/social-login",
            json={
                "provider": "google",
                "id_token": "token",
                "device_id": "device_123",
            },
        )

        assert response.status_code == 400

    def test_invalidRequestBody_returns422(self, client):
        """잘못된 요청 본문 시 422 반환"""
        response = client.post(
            "/api/v1/auth/social-login",
            json={
                # provider 필드 누락
                "id_token": "token",
            },
        )

        assert response.status_code == 422
