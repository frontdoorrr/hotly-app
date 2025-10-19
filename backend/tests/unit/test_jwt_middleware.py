"""JWT 검증 미들웨어 단위 테스트 (TDD) - Firebase Auth."""
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from app.middleware.jwt_middleware import get_current_user, verify_firebase_token
from app.schemas.auth import TokenValidationResult


class TestJWTMiddleware:
    """JWT 검증 미들웨어 테스트 (Firebase Auth)."""

    @pytest.mark.asyncio
    async def test_getCurrentUser_validToken_returnsUser(self):
        """유효한 Firebase ID 토큰으로 현재 사용자 조회 시 사용자 정보 반환."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "valid-firebase-id-token"

        expected_validation = TokenValidationResult(
            is_valid=True,
            user_id="user-123",
            email="test@example.com",
            permissions=None,
        )

        with patch(
            "app.middleware.jwt_middleware.firebase_auth_service.validate_access_token"
        ) as mock_validate:
            mock_validate.return_value = expected_validation

            # When
            result = await get_current_user(mock_credentials)

            # Then
            assert result["uid"] == "user-123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_getCurrentUser_invalidToken_raisesUnauthorized(self):
        """유효하지 않은 Firebase ID 토큰으로 조회 시 401 에러 발생."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid-token"

        with patch(
            "app.middleware.jwt_middleware.firebase_auth_service.validate_access_token"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Invalid token")

            # When & Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_getCurrentUser_expiredToken_raisesUnauthorized(self):
        """만료된 Firebase ID 토큰으로 조회 시 401 에러 발생."""
        # Given
        mock_credentials = Mock()
        mock_credentials.credentials = "expired-token"

        expected_validation = TokenValidationResult(
            is_valid=False, user_id=None, email=None
        )

        with patch(
            "app.middleware.jwt_middleware.firebase_auth_service.validate_access_token"
        ) as mock_validate:
            mock_validate.return_value = expected_validation

            # When & Then
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verifyFirebaseToken_validToken_returnsPayload(self):
        """유효한 Firebase ID 토큰 검증 시 사용자 정보 반환."""
        # Given
        token = "valid-firebase-id-token"
        expected_validation = TokenValidationResult(
            is_valid=True,
            user_id="user-123",
            email="test@example.com",
            permissions=None,
        )

        with patch(
            "app.middleware.jwt_middleware.firebase_auth_service.validate_access_token"
        ) as mock_validate:
            mock_validate.return_value = expected_validation

            # When
            result = await verify_firebase_token(token)

            # Then
            assert result["uid"] == "user-123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_getCurrentUser_noAuthHeader_raisesUnauthorized(self):
        """인증 헤더 없이 요청 시 401 에러 발생."""
        # Given
        mock_credentials = None

        # When & Then
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_credentials)

        assert exc_info.value.status_code == 401
