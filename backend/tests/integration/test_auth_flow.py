"""인증 플로우 통합 테스트."""
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestAuthenticationFlow:
    """인증 플로우 통합 테스트."""

    @pytest.fixture
    def client(self):
        """테스트 클라이언트 fixture."""
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_completeAuthFlow_signUpToSignIn_success(self, client):
        """회원가입부터 로그인까지 전체 플로우 성공."""
        # Given: 새로운 사용자 회원가입 데이터
        sign_up_data = {
            "email": "integration@test.com",
            "password": "SecurePass123!",
            "display_name": "통합 테스트",
        }

        # Mock Supabase responses
        mock_user = Mock(
            id="user-integration-123",
            email="integration@test.com",
            user_metadata={"display_name": "통합 테스트"},
            app_metadata={},
            created_at="2025-01-03T00:00:00Z",
            email_confirmed_at="2025-01-03T00:00:00Z",
        )

        mock_session = Mock(
            access_token="mock-access-token",
            refresh_token="mock-refresh-token",
        )

        with patch("app.api.api_v1.endpoints.auth.auth_service.sign_up") as mock_signup:
            mock_signup.return_value = {
                "user": mock_user.__dict__,
                "session": mock_session.__dict__,
            }

            # When: 회원가입 API 호출
            signup_response = client.post("/api/v1/auth/signup", json=sign_up_data)

            # Then: 회원가입 성공
            assert signup_response.status_code == 201
            signup_data = signup_response.json()
            assert signup_data["success"] is True
            assert signup_data["is_new_user"] is True
            assert signup_data["access_token"] == "mock-access-token"

        # Given: 로그인 데이터
        sign_in_data = {
            "email": "integration@test.com",
            "password": "SecurePass123!",
        }

        with patch("app.api.api_v1.endpoints.auth.auth_service.sign_in") as mock_signin:
            mock_signin.return_value = {
                "user": mock_user.__dict__,
                "session": mock_session.__dict__,
            }

            # When: 로그인 API 호출
            signin_response = client.post("/api/v1/auth/signin", json=sign_in_data)

            # Then: 로그인 성공
            assert signin_response.status_code == 200
            signin_data = signin_response.json()
            assert signin_data["success"] is True
            assert signin_data["access_token"] == "mock-access-token"

    @pytest.mark.asyncio
    async def test_protectedEndpoint_withValidToken_success(self, client):
        """유효한 토큰으로 보호된 엔드포인트 접근 성공."""
        # Given: 유효한 액세스 토큰
        valid_token = "valid-jwt-token"

        mock_user = {
            "id": "user-123",
            "email": "test@example.com",
            "user_metadata": {"display_name": "테스트 사용자"},
            "app_metadata": {},
            "created_at": "2025-01-03T00:00:00Z",
            "email_confirmed_at": "2025-01-03T00:00:00Z",
        }

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.return_value = Mock(user=Mock(**mock_user))

            # When: 보호된 엔드포인트 접근
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {valid_token}"},
            )

            # Then: 사용자 정보 조회 성공
            assert response.status_code == 200
            user_data = response.json()
            assert user_data["id"] == "user-123"
            assert user_data["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_protectedEndpoint_withoutToken_unauthorized(self, client):
        """토큰 없이 보호된 엔드포인트 접근 시 401 에러."""
        # When: 토큰 없이 보호된 엔드포인트 접근
        response = client.get("/api/v1/auth/me")

        # Then: 401 Unauthorized 에러
        assert response.status_code == 403  # FastAPI HTTPBearer default

    @pytest.mark.asyncio
    async def test_protectedEndpoint_withInvalidToken_unauthorized(self, client):
        """유효하지 않은 토큰으로 보호된 엔드포인트 접근 시 401 에러."""
        # Given: 유효하지 않은 토큰
        invalid_token = "invalid-token"

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.side_effect = Exception("Invalid token")

            # When: 유효하지 않은 토큰으로 접근
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {invalid_token}"},
            )

            # Then: 401 Unauthorized 에러
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_oauthFlow_googleProvider_returnsAuthUrl(self, client):
        """Google OAuth 플로우 시작 시 인증 URL 반환."""
        # Given: Google OAuth 제공자
        provider = "google"

        with patch(
            "app.api.api_v1.endpoints.auth.auth_service.sign_in_with_oauth"
        ) as mock_oauth:
            mock_oauth.return_value = {
                "url": "https://accounts.google.com/oauth/authorize?..."
            }

            # When: OAuth 인증 시작
            response = client.post(f"/api/v1/auth/oauth/{provider}")

            # Then: OAuth URL 반환
            assert response.status_code == 200
            oauth_data = response.json()
            assert "url" in oauth_data
            assert "google.com" in oauth_data["url"]

    @pytest.mark.asyncio
    async def test_oauthFlow_unsupportedProvider_badRequest(self, client):
        """지원하지 않는 OAuth 제공자 사용 시 400 에러."""
        # Given: 지원하지 않는 OAuth 제공자
        provider = "facebook"

        # When: OAuth 인증 시도
        response = client.post(f"/api/v1/auth/oauth/{provider}")

        # Then: 400 Bad Request 에러
        assert response.status_code == 400
        error_data = response.json()
        assert "Unsupported OAuth provider" in error_data["detail"]

    @pytest.mark.asyncio
    async def test_tokenRefresh_validRefreshToken_returnsNewTokens(self, client):
        """유효한 리프레시 토큰으로 새 토큰 발급 성공."""
        # Given: 유효한 리프레시 토큰
        refresh_data = {
            "refresh_token": "valid-refresh-token",
            "device_id": "device-123",
        }

        mock_session = Mock(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
        )

        with patch(
            "app.api.api_v1.endpoints.auth.auth_service.refresh_session"
        ) as mock_refresh:
            mock_refresh.return_value = {"session": mock_session.__dict__}

            # When: 토큰 갱신 API 호출
            response = client.post("/api/v1/auth/refresh", json=refresh_data)

            # Then: 새 토큰 발급 성공
            assert response.status_code == 200
            token_data = response.json()
            assert token_data["success"] is True
            assert token_data["new_access_token"] == "new-access-token"
            assert token_data["new_refresh_token"] == "new-refresh-token"

    @pytest.mark.asyncio
    async def test_signOut_authenticatedUser_success(self, client):
        """인증된 사용자 로그아웃 성공."""
        # Given: 인증된 사용자
        valid_token = "valid-jwt-token"

        mock_user = {
            "id": "user-123",
            "email": "test@example.com",
            "user_metadata": {"display_name": "테스트 사용자"},
            "app_metadata": {},
            "created_at": "2025-01-03T00:00:00Z",
            "email_confirmed_at": "2025-01-03T00:00:00Z",
        }

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.return_value = Mock(user=Mock(**mock_user))

            with patch("app.api.api_v1.endpoints.auth.auth_service.sign_out"):
                # When: 로그아웃 API 호출
                response = client.post(
                    "/api/v1/auth/signout",
                    headers={"Authorization": f"Bearer {valid_token}"},
                )

                # Then: 로그아웃 성공
                assert response.status_code == 200
                logout_data = response.json()
                assert logout_data["success"] is True
                assert "signed out" in logout_data["message"].lower()

    @pytest.mark.asyncio
    async def test_profileUpdate_authenticatedUser_success(self, client):
        """인증된 사용자 프로필 업데이트 성공."""
        # Given: 인증된 사용자와 업데이트 데이터
        valid_token = "valid-jwt-token"
        profile_data = {
            "display_name": "업데이트된 이름",
            "preferred_language": "en",
        }

        mock_user = {
            "id": "user-123",
            "email": "test@example.com",
            "user_metadata": {"display_name": "테스트 사용자"},
            "app_metadata": {},
            "created_at": "2025-01-03T00:00:00Z",
            "email_confirmed_at": "2025-01-03T00:00:00Z",
        }

        updated_user = {
            **mock_user,
            "user_metadata": {
                "display_name": "업데이트된 이름",
                "preferred_language": "en",
            },
        }

        with patch("app.middleware.jwt_middleware.supabase_client") as mock_supabase:
            mock_supabase.auth.get_user.return_value = Mock(user=Mock(**mock_user))

            with patch(
                "app.api.api_v1.endpoints.auth.auth_service.update_user"
            ) as mock_update:
                mock_update.return_value = updated_user

                # When: 프로필 업데이트 API 호출
                response = client.put(
                    "/api/v1/auth/profile",
                    json=profile_data,
                    headers={"Authorization": f"Bearer {valid_token}"},
                )

                # Then: 프로필 업데이트 성공
                assert response.status_code == 200
                updated_data = response.json()
                assert updated_data["user_metadata"]["display_name"] == "업데이트된 이름"
