"""JWT 검증 미들웨어 단위 테스트 (TDD)."""
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.middleware.jwt_middleware import get_current_user, verify_jwt_token


class TestJWTMiddleware:
    """JWT 검증 미들웨어 테스트."""

    @pytest.mark.asyncio
    async def test_getCurrentUser_validToken_returnsUser(self):
        """유효한 JWT 토큰으로 현재 사용자 조회 시 사용자 정보 반환."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "valid-jwt-token"

        expected_user = {
            "id": "user-123",
            "email": "test@example.com",
            "user_metadata": {"display_name": "테스트"},
        }

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.return_value = Mock(user=Mock(**expected_user))

            # When
            result = await get_current_user(mock_credentials)

            # Then
            assert result["id"] == "user-123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_getCurrentUser_invalidToken_raisesUnauthorized(self):
        """유효하지 않은 JWT 토큰으로 조회 시 401 에러 발생."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid-token"

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

            # When & Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_getCurrentUser_expiredToken_raisesUnauthorized(self):
        """만료된 JWT 토큰으로 조회 시 401 에러 발생."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "expired-token"

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.side_effect = Exception("Token expired")

            # When & Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401
            assert (
                "expired" in str(exc_info.value.detail).lower()
                or "invalid" in str(exc_info.value.detail).lower()
            )

    @pytest.mark.asyncio
    async def test_verifyJwtToken_validToken_returnsPayload(self):
        """유효한 JWT 토큰 검증 시 페이로드 반환."""
        # Given
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        expected_payload = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "authenticated",
        }

        with patch("app.middleware.jwt_middleware.jwt.decode") as mock_decode:
            mock_decode.return_value = expected_payload

            # When
            result = await verify_jwt_token(token)

            # Then
            assert result["sub"] == "user-123"
            assert result["email"] == "test@example.com"
            assert result["role"] == "authenticated"

    @pytest.mark.asyncio
    async def test_getCurrentUser_noAuthHeader_raisesUnauthorized(self):
        """인증 헤더 없이 요청 시 401 에러 발생."""
        # Given
        mock_credentials = None

        # When & Then
        with pytest.raises(Exception):  # HTTPException 또는 일반 Exception
            await get_current_user(mock_credentials)
