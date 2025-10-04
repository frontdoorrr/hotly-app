"""Supabase 인증 서비스."""
from typing import Any, Dict, Optional

from supabase import Client

from app.schemas.auth import SignInRequest, SignUpRequest


class SupabaseAuthService:
    """Supabase 인증 서비스."""

    def __init__(self, supabase_client: Client):
        """
        Supabase 인증 서비스 초기화.

        Args:
            supabase_client: Supabase 클라이언트 인스턴스
        """
        self.supabase = supabase_client

    async def sign_up(self, sign_up_data: SignUpRequest) -> Dict[str, Any]:
        """
        회원가입.

        Args:
            sign_up_data: 회원가입 요청 데이터

        Returns:
            회원가입 결과 (사용자 정보 및 세션)

        Raises:
            Exception: 회원가입 실패 시
        """
        response = self.supabase.auth.sign_up(
            {
                "email": sign_up_data.email,
                "password": sign_up_data.password,
                "options": {"data": {"display_name": sign_up_data.display_name}},
            }
        )

        return {
            "user": response.user.__dict__ if response.user else None,
            "session": response.session.__dict__ if response.session else None,
        }

    async def sign_in(self, sign_in_data: SignInRequest) -> Dict[str, Any]:
        """
        로그인.

        Args:
            sign_in_data: 로그인 요청 데이터

        Returns:
            로그인 결과 (사용자 정보 및 세션)

        Raises:
            Exception: 로그인 실패 시
        """
        response = self.supabase.auth.sign_in_with_password(
            {"email": sign_in_data.email, "password": sign_in_data.password}
        )

        return {
            "user": response.user.__dict__ if response.user else None,
            "session": response.session.__dict__ if response.session else None,
        }

    async def sign_out(self) -> None:
        """
        로그아웃.

        Raises:
            Exception: 로그아웃 실패 시
        """
        self.supabase.auth.sign_out()

    async def refresh_session(self) -> Dict[str, Any]:
        """
        세션 갱신.

        Returns:
            갱신된 세션 정보

        Raises:
            Exception: 세션 갱신 실패 시
        """
        response = self.supabase.auth.refresh_session()

        return {"session": response.session.__dict__ if response.session else None}

    async def sign_in_with_oauth(self, provider: str) -> Dict[str, str]:
        """
        OAuth 로그인.

        Args:
            provider: OAuth 제공자 (google, apple, kakao)

        Returns:
            OAuth 인증 URL

        Raises:
            Exception: OAuth 로그인 실패 시
        """
        response = self.supabase.auth.sign_in_with_oauth({"provider": provider})

        return {"url": response.url if hasattr(response, "url") else str(response)}

    async def get_user(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        액세스 토큰으로 사용자 정보 조회.

        Args:
            access_token: 액세스 토큰

        Returns:
            사용자 정보 또는 None

        Raises:
            Exception: 사용자 조회 실패 시
        """
        try:
            response = self.supabase.auth.get_user(access_token)
            return response.user.__dict__ if response.user else None
        except Exception as e:
            raise Exception(f"사용자 조회 실패: {str(e)}")

    async def update_user(
        self,
        user_id: str,
        user_metadata: Optional[Dict[str, Any]] = None,
        app_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        사용자 메타데이터 업데이트.

        Args:
            user_id: 사용자 ID
            user_metadata: 사용자 메타데이터 (사용자가 수정 가능)
            app_metadata: 앱 메타데이터 (관리자만 수정 가능)

        Returns:
            업데이트된 사용자 정보

        Raises:
            Exception: 업데이트 실패 시
        """
        update_data = {}
        if user_metadata:
            update_data["user_metadata"] = user_metadata
        if app_metadata:
            update_data["app_metadata"] = app_metadata

        response = self.supabase.auth.admin.update_user_by_id(user_id, update_data)

        return response.user.__dict__ if response.user else None
