"""
Firebase Authentication 스키마 정의

이 모듈은 Firebase Auth 시스템의 요청/응답 스키마를 정의합니다.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator


class SocialProvider(str, Enum):
    """소셜 로그인 제공자"""
    GOOGLE = "google"
    APPLE = "apple"
    KAKAO = "kakao"
    ANONYMOUS = "anonymous"


class AuthError(str, Enum):
    """인증 에러 코드"""
    INVALID_TOKEN = "invalid_token"
    TOKEN_EXPIRED = "token_expired"
    INVALID_CREDENTIALS = "invalid_credentials"
    USER_NOT_FOUND = "user_not_found"
    USER_DISABLED = "user_disabled"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PROVIDER_ERROR = "provider_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class UserPermissions(BaseModel):
    """사용자 권한 설정"""
    can_create_courses: bool = Field(default=True, description="코스 생성 권한")
    can_share_content: bool = Field(default=True, description="콘텐츠 공유 권한")  
    can_view_content: bool = Field(default=True, description="콘텐츠 조회 권한")
    can_comment: bool = Field(default=True, description="댓글 작성 권한")
    can_rate_places: bool = Field(default=True, description="장소 평가 권한")
    data_retention_days: int = Field(default=365, description="데이터 보존 기간(일)")
    max_saved_places: int = Field(default=1000, description="최대 저장 가능 장소 수")
    max_courses_per_day: int = Field(default=10, description="일일 최대 코스 생성 수")


class UserProfile(BaseModel):
    """사용자 프로필 정보"""
    user_id: str = Field(..., description="Firebase 사용자 ID")
    email: Optional[EmailStr] = Field(None, description="이메일 주소")
    name: Optional[str] = Field(None, description="사용자 이름")
    profile_image_url: Optional[str] = Field(None, description="프로필 이미지 URL")
    provider: SocialProvider = Field(..., description="로그인 제공자")
    linked_providers: List[SocialProvider] = Field(default_factory=list, description="연결된 제공자 목록")
    is_anonymous: bool = Field(default=False, description="익명 사용자 여부")
    is_verified: bool = Field(default=False, description="이메일 인증 여부")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="계정 생성 시간")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 시간")
    permissions: UserPermissions = Field(default_factory=UserPermissions, description="사용자 권한")
    
    # 사용자 선호 설정
    preferred_language: str = Field(default="ko", description="선호 언어")
    timezone: str = Field(default="Asia/Seoul", description="시간대")
    
    # 개인화 정보
    location: Optional[Dict[str, float]] = Field(None, description="사용자 위치 (lat, lng)")
    interests: List[str] = Field(default_factory=list, description="관심사 태그")
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('유효한 이메일 주소가 아닙니다')
        return v


class SocialLoginRequest(BaseModel):
    """소셜 로그인 요청"""
    provider: SocialProvider = Field(..., description="소셜 로그인 제공자")
    id_token: Optional[str] = Field(None, description="ID 토큰 (Google, Apple)")
    access_token: Optional[str] = Field(None, description="액세스 토큰 (Kakao)")
    device_id: str = Field(..., description="디바이스 식별자")
    device_info: Optional[Dict[str, Any]] = Field(None, description="디바이스 정보")
    
    @validator('id_token', 'access_token')
    def validate_token_presence(cls, v, values):
        provider = values.get('provider')
        if provider in [SocialProvider.GOOGLE, SocialProvider.APPLE] and not values.get('id_token'):
            raise ValueError(f'{provider} 로그인에는 id_token이 필요합니다')
        if provider == SocialProvider.KAKAO and not values.get('access_token'):
            raise ValueError('Kakao 로그인에는 access_token이 필요합니다')
        return v


class LoginResponse(BaseModel):
    """로그인 응답"""
    success: bool = Field(..., description="로그인 성공 여부")
    user_profile: Optional[UserProfile] = Field(None, description="사용자 프로필")
    access_token: Optional[str] = Field(None, description="액세스 토큰")
    refresh_token: Optional[str] = Field(None, description="리프레시 토큰")
    expires_in: int = Field(default=3600, description="토큰 만료 시간(초)")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    
    # 추가 정보
    is_new_user: bool = Field(default=False, description="신규 사용자 여부")
    requires_onboarding: bool = Field(default=False, description="온보딩 필요 여부")
    session_id: Optional[str] = Field(None, description="세션 ID")
    
    # 에러 정보 (실패 시)
    error_code: Optional[AuthError] = Field(None, description="에러 코드")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class TokenValidationResult(BaseModel):
    """토큰 검증 결과"""
    is_valid: bool = Field(..., description="토큰 유효성")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    email: Optional[str] = Field(None, description="사용자 이메일")
    expires_at: Optional[datetime] = Field(None, description="토큰 만료 시간")
    issued_at: Optional[datetime] = Field(None, description="토큰 발급 시간")
    
    # 권한 정보
    permissions: Optional[UserPermissions] = Field(None, description="사용자 권한")
    
    # 에러 정보 (유효하지 않을 시)
    error_code: Optional[AuthError] = Field(None, description="에러 코드")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class TokenRefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="리프레시 토큰")
    device_id: str = Field(..., description="디바이스 식별자")


class TokenRefreshResponse(BaseModel):
    """토큰 갱신 응답"""
    success: bool = Field(..., description="갱신 성공 여부")
    new_access_token: Optional[str] = Field(None, description="새 액세스 토큰")
    new_refresh_token: Optional[str] = Field(None, description="새 리프레시 토큰")
    expires_in: int = Field(default=3600, description="토큰 만료 시간(초)")
    
    # 에러 정보 (실패 시)
    error_code: Optional[AuthError] = Field(None, description="에러 코드")
    error_message: Optional[str] = Field(None, description="에러 메시지")


class UserSession(BaseModel):
    """사용자 세션 정보"""
    session_id: str = Field(..., description="세션 ID")
    user_id: str = Field(..., description="사용자 ID")
    device_id: str = Field(..., description="디바이스 ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="세션 생성 시간")
    expires_at: datetime = Field(..., description="세션 만료 시간")
    last_activity_at: datetime = Field(default_factory=datetime.utcnow, description="마지막 활동 시간")
    is_active: bool = Field(default=True, description="세션 활성 상태")
    
    # 세션 메타데이터
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    location: Optional[Dict[str, Any]] = Field(None, description="접속 위치 정보")


class SecurityAlert(BaseModel):
    """보안 경고 정보"""
    alert_id: str = Field(..., description="경고 ID")
    user_id: str = Field(..., description="사용자 ID")
    alert_type: str = Field(..., description="경고 타입")
    risk_level: str = Field(..., description="위험 수준 (LOW/MEDIUM/HIGH)")
    is_suspicious: bool = Field(..., description="의심스러운 활동 여부")
    reason: str = Field(..., description="경고 사유")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="감지 시간")
    
    # 추가 정보
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    actions_taken: List[str] = Field(default_factory=list, description="취한 조치 목록")


class AnonymousUserRequest(BaseModel):
    """익명 사용자 생성 요청"""
    device_id: str = Field(..., description="디바이스 식별자")
    device_info: Optional[Dict[str, Any]] = Field(None, description="디바이스 정보")
    location: Optional[Dict[str, float]] = Field(None, description="위치 정보")


class UserUpgradeRequest(BaseModel):
    """사용자 계정 업그레이드 요청 (익명 → 인증)"""
    anonymous_user_id: str = Field(..., description="익명 사용자 ID")
    social_login: SocialLoginRequest = Field(..., description="소셜 로그인 정보")


class LogoutRequest(BaseModel):
    """로그아웃 요청"""
    user_id: str = Field(..., description="사용자 ID")
    device_id: Optional[str] = Field(None, description="특정 디바이스 로그아웃")
    all_devices: bool = Field(default=False, description="모든 디바이스에서 로그아웃")


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    success: bool = Field(..., description="로그아웃 성공 여부")
    message: str = Field(..., description="결과 메시지")
    sessions_terminated: int = Field(default=0, description="종료된 세션 수")


# Firebase 설정 관련 스키마
class FirebaseConfig(BaseModel):
    """Firebase 설정"""
    project_id: str = Field(..., description="Firebase 프로젝트 ID")
    api_key: str = Field(..., description="Firebase API 키")
    auth_domain: str = Field(..., description="Firebase 인증 도메인")
    
    # 소셜 로그인 설정
    google_client_id: Optional[str] = Field(None, description="Google 클라이언트 ID")
    apple_client_id: Optional[str] = Field(None, description="Apple 클라이언트 ID")
    kakao_client_id: Optional[str] = Field(None, description="Kakao 클라이언트 ID")
    
    # 보안 설정
    token_expiration_hours: int = Field(default=24, description="토큰 만료 시간(시간)")
    refresh_token_expiration_days: int = Field(default=30, description="리프레시 토큰 만료 시간(일)")
    
    # 레이트 리미팅 설정
    max_login_attempts_per_minute: int = Field(default=10, description="분당 최대 로그인 시도")
    max_token_refresh_per_hour: int = Field(default=60, description="시간당 최대 토큰 갱신")


class LoginAttempt(BaseModel):
    """로그인 시도 로그"""
    attempt_id: str = Field(..., description="시도 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    device_id: str = Field(..., description="디바이스 ID")
    provider: SocialProvider = Field(..., description="로그인 제공자")
    success: bool = Field(..., description="로그인 성공 여부")
    attempted_at: datetime = Field(default_factory=datetime.utcnow, description="시도 시간")
    
    # 추가 정보
    ip_address: Optional[str] = Field(None, description="IP 주소")
    user_agent: Optional[str] = Field(None, description="사용자 에이전트")
    country: Optional[str] = Field(None, description="국가")
    failure_reason: Optional[str] = Field(None, description="실패 사유")