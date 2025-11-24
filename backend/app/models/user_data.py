"""
사용자 데이터 모델

인증된 사용자 로직 및 개인별 데이터 연동을 위한 데이터 모델들
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import re

from app.db.base_class import Base


class AuthenticatedUser(Base):
    """Firebase 인증된 사용자 데이터 모델"""
    __tablename__ = "authenticated_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    firebase_uid = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    
    # 상태 필드
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    def validate(self):
        """데이터 검증"""
        if self.email and not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
    
    def _is_valid_email(self, email: str) -> bool:
        """이메일 형식 검증"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class UserPersonalData(Base):
    """사용자 개인 데이터 모델"""
    __tablename__ = "user_personal_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), index=True, nullable=False)
    data_type = Column(String(100), nullable=False)
    data_content = Column(JSON, nullable=False)
    
    # 보안 필드
    is_encrypted = Column(Boolean, default=False)
    sensitivity_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserActivityLog(Base):
    """사용자 활동 로그 모델"""
    __tablename__ = "user_activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), index=True, nullable=False)
    activity_type = Column(String(100), nullable=False)
    activity_data = Column(JSON, nullable=False)
    
    # 추적 정보
    ip_address = Column(String(45), nullable=True)  # IPv6 지원
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # 프라이버시 설정
    requires_masking = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)


class UserDataAccess(Base):
    """사용자 데이터 접근 제어 모델"""
    __tablename__ = "user_data_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), index=True, nullable=False)
    resource_type = Column(String(100), nullable=False)
    permission_level = Column(String(50), nullable=False)  # READ, WRITE, READ_WRITE, ADMIN
    
    # 권한 부여 정보
    granted_by = Column(String(255), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # 상태
    is_active = Column(Boolean, default=True)
    
    def is_expired(self) -> bool:
        """접근 권한 만료 여부 확인"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class UserSettingsData(Base):
    """사용자 설정 데이터 모델 (JSON 기반)"""
    __tablename__ = "user_settings_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), index=True, nullable=False)
    settings_type = Column(String(100), nullable=False)
    settings_data = Column(JSON, nullable=False)
    
    # 설정 메타데이터
    is_default = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_default_settings() -> Dict[str, Any]:
        """기본 설정 반환"""
        return {
            "theme": "light",
            "language": "ko",
            "timezone": "Asia/Seoul",
            "notifications": {
                "push_enabled": True,
                "email_enabled": True,
                "quiet_hours": {
                    "enabled": False,
                    "start": "22:00",
                    "end": "07:00"
                }
            },
            "privacy": {
                "location_tracking": True,
                "analytics": True,
                "marketing": False
            }
        }


class UserPrivacySettings(Base):
    """사용자 프라이버시 설정 모델"""
    __tablename__ = "user_privacy_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    privacy_settings = Column(JSON, nullable=False)
    
    # GDPR 준수
    gdpr_compliance = Column(Boolean, default=True)
    consent_date = Column(DateTime, nullable=True)
    consent_version = Column(String(20), default="1.0")
    
    # 데이터 보존 설정
    data_retention_days = Column(Integer, default=365)
    auto_delete_enabled = Column(Boolean, default=False)
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def validate_gdpr_compliance(self) -> bool:
        """GDPR 준수 검증"""
        required_consents = [
            "data_collection_consent",
            "data_retention_days"
        ]
        
        if not self.privacy_settings:
            return False
            
        for consent in required_consents:
            if consent not in self.privacy_settings:
                return False
                
        # 데이터 수집 동의가 있어야 함
        if not self.privacy_settings.get("data_collection_consent", False):
            return False
            
        return True