"""Supabase 클라이언트 설정 및 초기화."""
from typing import Optional

from pydantic import BaseSettings
from supabase import Client, create_client


class SupabaseSettings(BaseSettings):
    """Supabase 연결 설정."""

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    jwt_secret: str = ""

    # OAuth 설정
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    apple_client_id: Optional[str] = None
    apple_client_secret: Optional[str] = None

    # 인증 설정
    password_min_length: int = 8
    email_verification_required: bool = True
    session_duration_hours: int = 24
    refresh_token_duration_days: int = 30

    class Config:
        """Pydantic 설정."""

        env_file = ".env"
        case_sensitive = False


# 설정 인스턴스 생성
settings = SupabaseSettings()

# Supabase 클라이언트 (클라이언트 측 - 제한된 권한)
# 테스트 환경에서는 더미 값 사용
if settings.supabase_url and settings.supabase_anon_key:
    supabase_client: Client = create_client(
        settings.supabase_url, settings.supabase_anon_key
    )
else:
    # 테스트/개발 환경용 더미 클라이언트
    supabase_client: Client = create_client(
        "https://dummy.supabase.co", "dummy-anon-key"
    )

# Supabase 관리자 클라이언트 (서버 측 - 전체 권한)
if settings.supabase_url and settings.supabase_service_role_key:
    supabase_admin: Client = create_client(
        settings.supabase_url, settings.supabase_service_role_key
    )
else:
    # 테스트/개발 환경용 더미 클라이언트
    supabase_admin: Client = create_client(
        "https://dummy.supabase.co", "dummy-service-role-key"
    )
