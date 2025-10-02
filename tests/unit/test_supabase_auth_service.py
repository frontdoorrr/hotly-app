"""Supabase 인증 서비스 단위 테스트 (TDD)."""
from unittest.mock import Mock

import pytest

from app.schemas.auth import SignInRequest, SignUpRequest
from app.services.supabase_auth_service import SupabaseAuthService


class TestSupabaseAuthService:
    """Supabase 인증 서비스 테스트."""

    @pytest.fixture
    def mock_supabase_client(self):
        """모의 Supabase 클라이언트."""
        return Mock()

    @pytest.fixture
    def auth_service(self, mock_supabase_client):
        """인증 서비스 인스턴스."""
        return SupabaseAuthService(mock_supabase_client)

    @pytest.mark.asyncio
    async def test_signUp_validCredentials_createsUser(
        self, auth_service, mock_supabase_client
    ):
        """유효한 자격 증명으로 회원가입 시 사용자가 생성됨."""
        # Given
        sign_up_data = SignUpRequest(
            email="test@example.com", password="SecurePass123", display_name="테스트 사용자"
        )

        expected_response = {
            "user": {
                "id": "user-123",
                "email": "test@example.com",
                "user_metadata": {"display_name": "테스트 사용자"},
            },
            "session": {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh-token",
            },
        }

        mock_supabase_client.auth.sign_up.return_value = Mock(**expected_response)

        # When
        result = await auth_service.sign_up(sign_up_data)

        # Then
        assert result["user"]["id"] == "user-123"
        assert result["user"]["email"] == sign_up_data.email
        mock_supabase_client.auth.sign_up.assert_called_once()

    @pytest.mark.asyncio
    async def test_signIn_validCredentials_returnsSession(
        self, auth_service, mock_supabase_client
    ):
        """유효한 자격 증명으로 로그인 시 세션 반환."""
        # Given
        sign_in_data = SignInRequest(email="test@example.com", password="SecurePass123")

        expected_response = {
            "user": {"id": "user-123", "email": "test@example.com"},
            "session": {
                "access_token": "mock-token",
                "refresh_token": "mock-refresh-token",
            },
        }

        mock_supabase_client.auth.sign_in_with_password.return_value = Mock(
            **expected_response
        )

        # When
        result = await auth_service.sign_in(sign_in_data)

        # Then
        assert result["session"]["access_token"] == "mock-token"
        assert result["user"]["email"] == sign_in_data.email
        mock_supabase_client.auth.sign_in_with_password.assert_called_once_with(
            {"email": sign_in_data.email, "password": sign_in_data.password}
        )

    @pytest.mark.asyncio
    async def test_signIn_invalidPassword_raisesAuthError(
        self, auth_service, mock_supabase_client
    ):
        """잘못된 비밀번호로 로그인 시 인증 오류 발생."""
        # Given
        sign_in_data = SignInRequest(email="test@example.com", password="WrongPassword")

        mock_supabase_client.auth.sign_in_with_password.side_effect = Exception(
            "Invalid login credentials"
        )

        # When & Then
        with pytest.raises(Exception) as exc_info:
            await auth_service.sign_in(sign_in_data)

        assert "Invalid login credentials" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_signOut_validSession_revokesToken(
        self, auth_service, mock_supabase_client
    ):
        """유효한 세션으로 로그아웃 시 토큰 무효화."""
        # Given
        mock_supabase_client.auth.sign_out.return_value = None

        # When
        await auth_service.sign_out()

        # Then
        mock_supabase_client.auth.sign_out.assert_called_once()

    @pytest.mark.asyncio
    async def test_refreshSession_validRefreshToken_returnsNewSession(
        self, auth_service, mock_supabase_client
    ):
        """유효한 리프레시 토큰으로 세션 갱신 시 새 세션 반환."""
        # Given
        expected_response = {
            "session": {
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
            }
        }

        mock_supabase_client.auth.refresh_session.return_value = Mock(
            **expected_response
        )

        # When
        result = await auth_service.refresh_session()

        # Then
        assert result["session"]["access_token"] == "new-access-token"
        mock_supabase_client.auth.refresh_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_signInWithOAuth_googleProvider_returnsAuthUrl(
        self, auth_service, mock_supabase_client
    ):
        """Google OAuth 로그인 시 인증 URL 반환."""
        # Given
        provider = "google"
        expected_response = {"url": "https://accounts.google.com/o/oauth2/v2/auth?..."}

        mock_supabase_client.auth.sign_in_with_oauth.return_value = Mock(
            **expected_response
        )

        # When
        result = await auth_service.sign_in_with_oauth(provider)

        # Then
        assert "url" in result
        assert "google" in result["url"]
        mock_supabase_client.auth.sign_in_with_oauth.assert_called_once_with(
            {"provider": provider}
        )
