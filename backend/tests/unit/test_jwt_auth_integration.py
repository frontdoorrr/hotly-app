"""
JWT 인증 통합 단위 테스트

0-3 보안 설정과 Firebase Auth 서비스의 JWT 통합을 테스트합니다.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    verify_token,
)
from app.services.auth.firebase_auth_service import FirebaseAuthService
from app.schemas.auth import (
    AuthError,
    SocialLoginRequest,
    SocialProvider,
    TokenRefreshRequest,
)


class TestJWTTokenGeneration:
    """JWT 토큰 생성 테스트"""

    def test_createAccessToken_withValidSubject_returnsJWTString(self):
        """유효한 subject로 액세스 토큰 생성 시 JWT 문자열 반환"""
        token = create_access_token(subject="user_123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        # JWT는 3개의 부분으로 구성 (header.payload.signature)
        assert len(token.split(".")) == 3

    def test_createAccessToken_withAdditionalClaims_includesClaimsInToken(self):
        """추가 클레임과 함께 토큰 생성 시 클레임 포함"""
        claims = {"role": "admin", "permissions": ["read", "write"]}
        token = create_access_token(subject="user_123", additional_claims=claims)

        # 토큰 검증으로 클레임 확인
        payload = verify_access_token(token)

        assert payload is not None
        assert payload.get("role") == "admin"
        assert payload.get("permissions") == ["read", "write"]

    def test_createRefreshToken_withValidSubject_returnsJWTString(self):
        """유효한 subject로 리프레시 토큰 생성"""
        token = create_refresh_token(subject="user_123")

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3


class TestJWTTokenVerification:
    """JWT 토큰 검증 테스트"""

    def test_verifyAccessToken_withValidToken_returnsPayload(self):
        """유효한 액세스 토큰 검증 시 페이로드 반환"""
        token = create_access_token(subject="user_123")
        payload = verify_access_token(token)

        assert payload is not None
        assert payload.get("sub") == "user_123"
        assert payload.get("type") == "access"

    def test_verifyAccessToken_withExpiredToken_returnsNone(self):
        """만료된 토큰 검증 시 None 반환"""
        token = create_access_token(
            subject="user_123",
            expires_delta=timedelta(seconds=-1)  # 이미 만료됨
        )
        payload = verify_access_token(token)

        assert payload is None

    def test_verifyAccessToken_withRefreshToken_returnsNone(self):
        """리프레시 토큰을 액세스 토큰으로 검증 시 None 반환"""
        refresh_token = create_refresh_token(subject="user_123")
        payload = verify_access_token(refresh_token)

        # 타입이 다르므로 None
        assert payload is None

    def test_verifyRefreshToken_withValidToken_returnsPayload(self):
        """유효한 리프레시 토큰 검증 시 페이로드 반환"""
        token = create_refresh_token(subject="user_123")
        payload = verify_refresh_token(token)

        assert payload is not None
        assert payload.get("sub") == "user_123"
        assert payload.get("type") == "refresh"

    def test_verifyRefreshToken_withAccessToken_returnsNone(self):
        """액세스 토큰을 리프레시 토큰으로 검증 시 None 반환"""
        access_token = create_access_token(subject="user_123")
        payload = verify_refresh_token(access_token)

        # 타입이 다르므로 None
        assert payload is None

    def test_verifyToken_withInvalidToken_returnsNone(self):
        """유효하지 않은 토큰 검증 시 None 반환"""
        payload = verify_token("invalid.token.here")

        assert payload is None

    def test_verifyToken_withTamperedToken_returnsNone(self):
        """변조된 토큰 검증 시 None 반환"""
        token = create_access_token(subject="user_123")
        # 토큰 변조
        tampered = token[:-5] + "xxxxx"
        payload = verify_token(tampered)

        assert payload is None


class TestFirebaseAuthServiceJWTIntegration:
    """FirebaseAuthService JWT 통합 테스트"""

    @pytest.fixture
    def auth_service(self):
        """테스트용 인증 서비스"""
        service = FirebaseAuthService(
            firebase_app=None,
            firebase_auth=MagicMock()
        )
        service.cache = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_generateTokens_createsValidJWTs(self, auth_service):
        """_generate_tokens가 유효한 JWT를 생성하는지 확인"""
        auth_service.cache.set = AsyncMock()

        access_token, refresh_token = await auth_service._generate_tokens("user_123")

        # 액세스 토큰 검증
        access_payload = verify_access_token(access_token)
        assert access_payload is not None
        assert access_payload.get("sub") == "user_123"

        # 리프레시 토큰 검증
        refresh_payload = verify_refresh_token(refresh_token)
        assert refresh_payload is not None
        assert refresh_payload.get("sub") == "user_123"

    @pytest.mark.asyncio
    async def test_validateAccessToken_withOurJWT_returnsValid(self, auth_service):
        """우리 JWT로 validate_access_token 호출 시 유효 결과 반환"""
        auth_service.cache.set = AsyncMock()
        auth_service.cache.get = AsyncMock(return_value=None)

        # 토큰 생성
        access_token, _ = await auth_service._generate_tokens("user_123")

        # 토큰 검증
        result = await auth_service.validate_access_token(access_token)

        assert result.is_valid is True
        assert result.user_id == "user_123"

    @pytest.mark.asyncio
    async def test_validateAccessToken_withEmptyToken_returnsInvalid(self, auth_service):
        """빈 토큰으로 검증 시 에러 반환"""
        result = await auth_service.validate_access_token("")

        assert result.is_valid is False
        assert result.error_code == AuthError.INVALID_TOKEN

    @pytest.mark.asyncio
    async def test_refreshTokens_withValidRefreshToken_returnsNewTokens(self, auth_service):
        """유효한 리프레시 토큰으로 새 토큰 발급"""
        auth_service.cache.set = AsyncMock()
        auth_service.cache.get = AsyncMock(return_value=None)
        # Note: Rate limiting handled at endpoint level

        # 리프레시 토큰 생성
        _, refresh_token = await auth_service._generate_tokens("user_123")

        # 토큰 갱신 요청
        request = TokenRefreshRequest(
            refresh_token=refresh_token,
            device_id="device_123"
        )

        result = await auth_service.refresh_tokens(request)

        assert result.success is True
        assert result.new_access_token is not None
        assert result.new_refresh_token is not None

        # 새 토큰 검증
        new_access_payload = verify_access_token(result.new_access_token)
        assert new_access_payload is not None
        assert new_access_payload.get("sub") == "user_123"

    @pytest.mark.asyncio
    async def test_refreshTokens_withInvalidToken_returnsError(self, auth_service):
        """유효하지 않은 리프레시 토큰으로 갱신 시 에러"""
        auth_service.cache.get = AsyncMock(return_value=None)

        request = TokenRefreshRequest(
            refresh_token="invalid.token.here",
            device_id="device_123"
        )

        result = await auth_service.refresh_tokens(request)

        assert result.success is False
        assert result.error_code == AuthError.INVALID_TOKEN

    # Note: Rate limit tests moved to TestAuthRateLimiting class
    # Service no longer handles rate limiting - it's at endpoint level


class TestAuthRateLimiting:
    """인증 레이트 리미팅 테스트"""

    @pytest.fixture
    def mock_request(self):
        """Mock Request 객체"""
        request = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request

    @pytest.mark.asyncio
    async def test_checkRateLimit_firstRequest_allowed(self, mock_request):
        """첫 번째 요청은 허용"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        with patch("app.middleware.auth_rate_limit.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=None)
            mock_cache.set = AsyncMock()

            result = await AuthRateLimiter.check_rate_limit(
                mock_request, "login"
            )

            assert result is True
            mock_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_checkRateLimit_withinLimit_allowed(self, mock_request):
        """제한 내 요청은 허용"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        with patch("app.middleware.auth_rate_limit.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=5)  # 10 미만
            mock_cache.set = AsyncMock()

            result = await AuthRateLimiter.check_rate_limit(
                mock_request, "login"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_checkRateLimit_exceedsLimit_raisesHTTPException(self, mock_request):
        """제한 초과 시 HTTPException 발생"""
        from app.middleware.auth_rate_limit import AuthRateLimiter
        from fastapi import HTTPException

        with patch("app.middleware.auth_rate_limit.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=10)  # 제한 도달

            with pytest.raises(HTTPException) as exc_info:
                await AuthRateLimiter.check_rate_limit(
                    mock_request, "login"
                )

            assert exc_info.value.status_code == 429
            assert "rate_limit_exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_checkRateLimit_refreshEndpoint_hasDifferentLimit(self, mock_request):
        """리프레시 엔드포인트는 다른 제한 적용"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        with patch("app.middleware.auth_rate_limit.cache_service") as mock_cache:
            mock_cache.get = AsyncMock(return_value=50)  # 60 미만
            mock_cache.set = AsyncMock()

            # 리프레시는 60/시간이므로 50은 허용
            result = await AuthRateLimiter.check_rate_limit(
                mock_request, "refresh"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_checkRateLimit_unknownOperation_allowed(self, mock_request):
        """알 수 없는 작업은 허용"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        result = await AuthRateLimiter.check_rate_limit(
            mock_request, "unknown_operation"
        )

        assert result is True

    def test_getClientIdentifier_withXForwardedFor_returnsFirstIP(self, mock_request):
        """X-Forwarded-For 헤더가 있으면 첫 번째 IP 반환"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        mock_request.headers = {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}

        identifier = AuthRateLimiter._get_client_identifier(mock_request)

        assert identifier == "1.2.3.4"

    def test_getClientIdentifier_withoutXForwardedFor_returnsClientHost(self, mock_request):
        """X-Forwarded-For가 없으면 클라이언트 IP 반환"""
        from app.middleware.auth_rate_limit import AuthRateLimiter

        mock_request.headers = {}
        mock_request.client.host = "192.168.1.1"

        identifier = AuthRateLimiter._get_client_identifier(mock_request)

        assert identifier == "192.168.1.1"
