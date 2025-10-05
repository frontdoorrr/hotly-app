"""
사용자 데이터 스키마

인증된 사용자 로직 및 개인별 데이터 연동을 위한
Pydantic 스키마들을 정의합니다.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, EmailStr


# 사용자 프로필 스키마
class UserProfileBase(BaseModel):
    """사용자 프로필 기본 스키마"""
    display_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserProfileUpdate(UserProfileBase):
    """사용자 프로필 업데이트 스키마"""
    pass


class UserProfileResponse(UserProfileBase):
    """사용자 프로필 응답 스키마"""
    id: str
    firebase_uid: str
    email: Optional[EmailStr] = None
    is_active: bool
    is_email_verified: bool = False
    is_phone_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 개인 데이터 스키마
class UserPersonalDataBase(BaseModel):
    """사용자 개인 데이터 기본 스키마"""
    data_type: str = Field(..., description="데이터 타입 (예: preferences, payment_info)")
    data_content: Dict[str, Any] = Field(..., description="데이터 내용")


class UserPersonalDataCreate(UserPersonalDataBase):
    """사용자 개인 데이터 생성 스키마"""
    encrypt: bool = Field(False, description="암호화 여부")


class UserPersonalDataResponse(UserPersonalDataBase):
    """사용자 개인 데이터 응답 스키마"""
    id: str
    user_id: str
    is_encrypted: bool
    sensitivity_level: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 활동 로그 스키마
class UserActivityLogResponse(BaseModel):
    """사용자 활동 로그 응답 스키마"""
    id: str
    user_id: str
    activity_type: str
    activity_data: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# 사용자 설정 스키마
class UserSettingsBase(BaseModel):
    """사용자 설정 기본 스키마"""
    settings_type: str = Field(default="app_preferences", description="설정 타입")
    settings_data: Dict[str, Any] = Field(..., description="설정 데이터")


class UserSettingsUpdate(UserSettingsBase):
    """사용자 설정 업데이트 스키마"""
    pass


class UserSettingsResponse(UserSettingsBase):
    """사용자 설정 응답 스키마"""
    id: str
    user_id: str
    is_default: bool
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 프라이버시 설정 스키마
class UserPrivacySettingsBase(BaseModel):
    """사용자 프라이버시 설정 기본 스키마"""
    privacy_settings: Dict[str, Any] = Field(..., description="프라이버시 설정")


class UserPrivacySettingsUpdate(UserPrivacySettingsBase):
    """사용자 프라이버시 설정 업데이트 스키마"""
    pass


class UserPrivacySettingsResponse(UserPrivacySettingsBase):
    """사용자 프라이버시 설정 응답 스키마"""
    id: str
    user_id: str
    gdpr_compliance: bool
    consent_date: Optional[datetime] = None
    consent_version: str
    data_retention_days: int
    created_at: datetime
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


# 데이터 접근 제어 스키마
class UserDataAccessResponse(BaseModel):
    """사용자 데이터 접근 제어 응답 스키마"""
    id: str
    user_id: str
    resource_type: str
    permission_level: str
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


# 활동 로깅 요청 스키마
class ActivityLogRequest(BaseModel):
    """활동 로깅 요청 스키마"""
    activity_type: str = Field(..., description="활동 타입")
    activity_data: Dict[str, Any] = Field(..., description="활동 데이터")


# 데이터 삭제 요청 스키마
class DataDeletionRequest(BaseModel):
    """데이터 삭제 요청 스키마"""
    reason: str = Field(default="user_request", description="삭제 사유")
    immediate: bool = Field(default=False, description="즉시 삭제 여부")


# 일반적인 응답 스키마
class StandardResponse(BaseModel):
    """표준 응답 스키마"""
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None