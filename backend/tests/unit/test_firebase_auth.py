"""
Firebase Authentication 시스템 테스트 (TDD)

Test Coverage:
- Firebase Auth 설정 및 초기화
- 다양한 소셜 로그인 (Google, Apple, Kakao)
- 사용자 인증 토큰 검증
- 사용자 세션 관리 및 갱신
- 보안 토큰 생성 및 검증
- 익명 사용자 및 게스트 모드
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.auth import (
    AuthError,
    SocialLoginRequest,
    SocialProvider,
    TokenRefreshRequest,
)
from app.services.auth.firebase_auth_service import FirebaseAuthService


class TestFirebaseAuthSetup:
    """Firebase Auth 설정 및 초기화 테스트"""

    @pytest.fixture
    async def auth_service(self):
        """Firebase Auth 서비스 fixture"""
        mock_firebase_app = MagicMock()
        mock_firebase_auth = AsyncMock()

        service = FirebaseAuthService(
            firebase_app=mock_firebase_app, firebase_auth=mock_firebase_auth
        )
        return service

    async def test_firebase_auth_initialization(self, auth_service):
        """Firebase Auth 서비스 초기화 테스트"""
        # Given: Firebase Auth 서비스
        # When: 서비스 초기화 확인
        # Then: 서비스가 올바르게 초기화됨
        assert auth_service.firebase_app is not None
        assert auth_service.firebase_auth is not None
        print("✅ Firebase Auth 서비스 초기화 테스트 통과")

    async def test_firebase_config_validation(self, auth_service):
        """Firebase 설정 검증 테스트"""
        # Given: Firebase 설정
        # When: 설정 유효성 검사
        config_valid = await auth_service.validate_firebase_config()

        # Then: 설정이 유효함
        assert config_valid is True
        print("✅ Firebase 설정 검증 테스트 통과")


class TestSocialLoginIntegration:
    """소셜 로그인 통합 테스트"""

    async def test_google_login_flow(self, auth_service):
        """Google 로그인 플로우 테스트"""
        # Given: Google ID 토큰
        google_id_token = "mock_google_id_token"

        login_request = SocialLoginRequest(
            provider=SocialProvider.GOOGLE,
            id_token=google_id_token,
            device_id="test_device_123",
        )

        # Mock Firebase response
        mock_user_info = {
            "uid": "google_user_123",
            "email": "user@gmail.com",
            "name": "김철수",
            "picture": "https://lh3.googleusercontent.com/...",
            "email_verified": True,
        }

        auth_service.firebase_auth.verify_id_token.return_value = mock_user_info

        # When: Google 로그인 수행
        login_result = await auth_service.login_with_social(login_request)

        # Then: 로그인 결과 검증
        assert login_result.success is True
        assert login_result.user_profile.email == "user@gmail.com"
        assert login_result.user_profile.provider == SocialProvider.GOOGLE
        assert login_result.access_token is not None
        assert login_result.refresh_token is not None

        print("✅ Google 로그인 플로우 테스트 통과")

    async def test_apple_login_flow(self, auth_service):
        """Apple 로그인 플로우 테스트"""
        # Given: Apple ID 토큰
        apple_id_token = "mock_apple_id_token"

        login_request = SocialLoginRequest(
            provider=SocialProvider.APPLE,
            id_token=apple_id_token,
            device_id="test_device_456",
        )

        # Mock Firebase response
        mock_user_info = {
            "uid": "apple_user_456",
            "email": "user@privaterelay.appleid.com",
            "name": None,  # Apple은 이름을 제공하지 않을 수 있음
            "email_verified": True,
        }

        auth_service.firebase_auth.verify_id_token.return_value = mock_user_info

        # When: Apple 로그인 수행
        login_result = await auth_service.login_with_social(login_request)

        # Then: 로그인 결과 검증
        assert login_result.success is True
        assert login_result.user_profile.provider == SocialProvider.APPLE
        assert "privaterelay.appleid.com" in login_result.user_profile.email
        assert login_result.access_token is not None

        print("✅ Apple 로그인 플로우 테스트 통과")

    async def test_kakao_login_flow(self, auth_service):
        """Kakao 로그인 플로우 테스트"""
        # Given: Kakao Access 토큰
        kakao_access_token = "mock_kakao_access_token"

        login_request = SocialLoginRequest(
            provider=SocialProvider.KAKAO,
            access_token=kakao_access_token,
            device_id="test_device_789",
        )

        # Mock Kakao API response
        mock_kakao_user = {
            "id": 12345678,
            "kakao_account": {
                "email": "user@kakao.com",
                "profile": {
                    "nickname": "카카오유저",
                    "profile_image_url": "http://k.kakaocdn.net/...",
                },
            },
        }

        # Mock Firebase custom token
        mock_custom_token = "custom_firebase_token"
        auth_service.firebase_auth.create_custom_token.return_value = mock_custom_token

        with patch("app.services.firebase_auth_service.requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_kakao_user
            mock_get.return_value.status_code = 200

            # When: Kakao 로그인 수행
            login_result = await auth_service.login_with_social(login_request)

            # Then: 로그인 결과 검증
            assert login_result.success is True
            assert login_result.user_profile.provider == SocialProvider.KAKAO
            assert login_result.user_profile.name == "카카오유저"
            assert login_result.access_token is not None

        print("✅ Kakao 로그인 플로우 테스트 통과")


class TestTokenValidationAndSession:
    """토큰 검증 및 세션 관리 테스트"""

    async def test_access_token_validation(self, auth_service):
        """액세스 토큰 검증 테스트"""
        # Given: 유효한 액세스 토큰
        valid_token = "valid_access_token_123"

        # Mock Firebase token verification
        mock_decoded_token = {
            "uid": "user_123",
            "email": "user@example.com",
            "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
        }

        auth_service.firebase_auth.verify_id_token.return_value = mock_decoded_token

        # When: 토큰 검증 수행
        validation_result = await auth_service.validate_access_token(valid_token)

        # Then: 검증 결과 확인
        assert validation_result.is_valid is True
        assert validation_result.user_id == "user_123"
        assert validation_result.email == "user@example.com"
        assert validation_result.expires_at is not None

        print("✅ 액세스 토큰 검증 테스트 통과")

    async def test_expired_token_handling(self, auth_service):
        """만료된 토큰 처리 테스트"""
        # Given: 만료된 토큰
        expired_token = "expired_token_456"

        # Mock Firebase token verification failure
        from firebase_admin.auth import ExpiredIdTokenError

        auth_service.firebase_auth.verify_id_token.side_effect = ExpiredIdTokenError(
            "Token expired"
        )

        # When: 만료된 토큰 검증
        validation_result = await auth_service.validate_access_token(expired_token)

        # Then: 만료 처리 확인
        assert validation_result.is_valid is False
        assert validation_result.error_code == AuthError.TOKEN_EXPIRED
        assert validation_result.user_id is None

        print("✅ 만료된 토큰 처리 테스트 통과")

    async def test_token_refresh_flow(self, auth_service):
        """토큰 갱신 플로우 테스트"""
        # Given: 리프레시 토큰
        refresh_token = "valid_refresh_token"

        refresh_request = TokenRefreshRequest(
            refresh_token=refresh_token, device_id="test_device_123"
        )

        # Mock Firebase token refresh
        mock_new_tokens = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }

        auth_service.firebase_auth.refresh.return_value = mock_new_tokens

        # When: 토큰 갱신 수행
        refresh_result = await auth_service.refresh_tokens(refresh_request)

        # Then: 갱신 결과 확인
        assert refresh_result.success is True
        assert refresh_result.new_access_token == "new_access_token"
        assert refresh_result.new_refresh_token == "new_refresh_token"
        assert refresh_result.expires_in == 3600

        print("✅ 토큰 갱신 플로우 테스트 통과")

    async def test_session_management(self, auth_service):
        """사용자 세션 관리 테스트"""
        # Given: 활성 사용자 세션
        user_id = "user_123"
        device_id = "device_456"
        session_token = "session_token_789"

        # When: 세션 생성
        session_created = await auth_service.create_user_session(
            user_id=user_id,
            device_id=device_id,
            session_token=session_token,
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )

        # Then: 세션 생성 확인
        assert session_created is True

        # When: 세션 조회
        session_info = await auth_service.get_user_session(user_id, device_id)

        # Then: 세션 정보 확인
        assert session_info is not None
        assert session_info.user_id == user_id
        assert session_info.device_id == device_id
        assert session_info.is_active is True

        # When: 세션 종료
        session_terminated = await auth_service.terminate_user_session(
            user_id, device_id
        )

        # Then: 세션 종료 확인
        assert session_terminated is True

        print("✅ 사용자 세션 관리 테스트 통과")


class TestAnonymousAndGuestMode:
    """익명 사용자 및 게스트 모드 테스트"""

    async def test_anonymous_user_creation(self, auth_service):
        """익명 사용자 생성 테스트"""
        # Given: 익명 사용자 요청
        device_id = "anonymous_device_123"

        # Mock Firebase anonymous auth
        mock_anonymous_user = {
            "uid": "anon_user_123",
            "is_anonymous": True,
            "provider_id": "anonymous",
        }

        auth_service.firebase_auth.create_user.return_value = mock_anonymous_user

        # When: 익명 사용자 생성
        anonymous_result = await auth_service.create_anonymous_user(device_id)

        # Then: 익명 사용자 생성 확인
        assert anonymous_result.success is True
        assert anonymous_result.user_profile.is_anonymous is True
        assert anonymous_result.user_profile.user_id == "anon_user_123"
        assert anonymous_result.access_token is not None

        print("✅ 익명 사용자 생성 테스트 통과")

    async def test_guest_mode_limitations(self, auth_service):
        """게스트 모드 제한사항 테스트"""
        # Given: 게스트 사용자
        guest_user_id = "guest_123"

        # When: 게스트 권한 확인
        permissions = await auth_service.get_user_permissions(guest_user_id)

        # Then: 제한된 권한 확인
        assert permissions.can_create_courses is False
        assert permissions.can_share_content is False
        assert permissions.can_view_content is True  # 읽기는 가능
        assert permissions.data_retention_days == 7  # 7일 제한

        print("✅ 게스트 모드 제한사항 테스트 통과")

    async def test_anonymous_to_authenticated_upgrade(self, auth_service):
        """익명 사용자에서 인증 사용자로 업그레이드 테스트"""
        # Given: 익명 사용자
        anonymous_user_id = "anon_user_123"

        # 소셜 로그인 정보
        social_login = SocialLoginRequest(
            provider=SocialProvider.GOOGLE,
            id_token="google_token_for_upgrade",
            device_id="device_123",
        )

        # Mock Firebase linking
        mock_linked_user = {
            "uid": "linked_user_123",
            "email": "upgraded@gmail.com",
            "provider_data": [
                {"provider_id": "anonymous"},
                {"provider_id": "google.com"},
            ],
        }

        auth_service.firebase_auth.link_provider.return_value = mock_linked_user

        # When: 계정 업그레이드
        upgrade_result = await auth_service.upgrade_anonymous_user(
            anonymous_user_id, social_login
        )

        # Then: 업그레이드 결과 확인
        assert upgrade_result.success is True
        assert upgrade_result.user_profile.is_anonymous is False
        assert upgrade_result.user_profile.email == "upgraded@gmail.com"
        assert len(upgrade_result.user_profile.linked_providers) == 2

        print("✅ 익명 사용자 인증 업그레이드 테스트 통과")


class TestSecurityAndErrorHandling:
    """보안 및 에러 처리 테스트"""

    async def test_invalid_token_security(self, auth_service):
        """잘못된 토큰 보안 테스트"""
        # Given: 잘못된 토큰들
        invalid_tokens = [
            "malformed_token",
            "fake.jwt.token",
            None,
            "",
            "expired_token_123",
        ]

        for invalid_token in invalid_tokens:
            # When: 잘못된 토큰 검증
            validation_result = await auth_service.validate_access_token(invalid_token)

            # Then: 토큰이 거부됨
            assert validation_result.is_valid is False
            assert validation_result.user_id is None

        print("✅ 잘못된 토큰 보안 테스트 통과")

    async def test_rate_limiting_protection(self, auth_service):
        """레이트 리미팅 보호 테스트"""
        # Given: 동일 IP에서 연속 로그인 시도
        device_id = "suspicious_device"
        login_request = SocialLoginRequest(
            provider=SocialProvider.GOOGLE, id_token="test_token", device_id=device_id
        )

        # When: 연속 로그인 시도 (20회)
        successful_attempts = 0
        rate_limited_attempts = 0

        for i in range(20):
            try:
                result = await auth_service.login_with_social(login_request)
                if result.success:
                    successful_attempts += 1
            except AuthError as e:
                if e.error_code == AuthError.RATE_LIMIT_EXCEEDED:
                    rate_limited_attempts += 1

        # Then: 레이트 리미팅 적용됨
        assert rate_limited_attempts > 0  # 일부 요청이 차단됨
        assert successful_attempts < 20  # 모든 요청이 성공하지는 않음

        print("✅ 레이트 리미팅 보호 테스트 통과")

    async def test_suspicious_activity_detection(self, auth_service):
        """의심스러운 활동 감지 테스트"""
        # Given: 의심스러운 로그인 패턴
        user_id = "user_123"

        # 다른 국가에서의 연속 로그인 시도
        suspicious_sessions = [
            {"country": "KR", "timestamp": datetime.utcnow()},
            {"country": "US", "timestamp": datetime.utcnow() + timedelta(minutes=1)},
            {"country": "CN", "timestamp": datetime.utcnow() + timedelta(minutes=2)},
        ]

        # When: 의심스러운 활동 감지
        for session in suspicious_sessions:
            await auth_service.log_login_attempt(user_id, session)

        security_alert = await auth_service.check_suspicious_activity(user_id)

        # Then: 보안 경고 생성
        assert security_alert.is_suspicious is True
        assert security_alert.risk_level == "HIGH"
        assert "Multiple countries" in security_alert.reason

        print("✅ 의심스러운 활동 감지 테스트 통과")


if __name__ == "__main__":
    # 간단한 테스트 실행기
    async def run_tests():
        test_setup = TestFirebaseAuthSetup()
        test_social = TestSocialLoginIntegration()
        test_token = TestTokenValidationAndSession()
        test_anonymous = TestAnonymousAndGuestMode()
        TestSecurityAndErrorHandling()

        # Mock 서비스 생성
        mock_firebase_app = MagicMock()
        mock_firebase_auth = AsyncMock()

        auth_service = FirebaseAuthService(
            firebase_app=mock_firebase_app, firebase_auth=mock_firebase_auth
        )

        print("🧪 Firebase Authentication 테스트 시작...")

        try:
            await test_setup.test_firebase_auth_initialization(auth_service)
            await test_social.test_google_login_flow(auth_service)
            await test_token.test_access_token_validation(auth_service)
            await test_anonymous.test_anonymous_user_creation(auth_service)

            print("🎉 모든 Firebase Authentication 테스트 통과!")

        except ImportError as e:
            print(f"⚠️ 테스트 실행을 위해 서비스 구현이 필요합니다: {e}")
            print("Firebase Auth 서비스 구현 후 다시 실행해주세요.")

    if __name__ == "__main__":
        asyncio.run(run_tests())
