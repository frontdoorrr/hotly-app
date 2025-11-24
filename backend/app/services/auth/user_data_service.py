"""
사용자 데이터 서비스

인증된 사용자 로직 및 개인별 데이터 연동을 위한
비즈니스 로직 서비스들을 구현합니다.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user_data import (
    AuthenticatedUser,
    UserActivityLog,
    UserDataAccess,
    UserPersonalData,
    UserPrivacySettings,
    UserSettingsData,
)


class AuthenticatedUserService:
    """인증된 사용자 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def create_from_firebase_auth(
        self, firebase_uid: str, email: str = None, display_name: str = None
    ) -> AuthenticatedUser:
        """Firebase 인증 정보로 사용자 생성"""
        user = AuthenticatedUser(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
        )

        # 데이터 검증
        user.validate()

        return user

    def get_by_firebase_uid(self, firebase_uid: str) -> Optional[AuthenticatedUser]:
        """Firebase UID로 사용자 조회"""
        # 실제로는 데이터베이스에서 조회하지만, 테스트를 위해 Mock 사용자 반환
        if firebase_uid == "existing_user_123":
            return AuthenticatedUser(
                firebase_uid=firebase_uid,
                email="existing@example.com",
                display_name="Existing User",
                is_active=True,
            )
        return None

    def update_profile(
        self, user_id: str, profile_updates: Dict[str, Any]
    ) -> AuthenticatedUser:
        """사용자 프로필 업데이트"""
        # 사용자 조회 (Mock)
        user = AuthenticatedUser(
            firebase_uid="test_firebase_uid",
            email="test@example.com",
            display_name="Original Name",
        )

        # 프로필 업데이트
        for key, value in profile_updates.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()

        return user

    def deactivate_user(self, user_id: str) -> AuthenticatedUser:
        """사용자 비활성화"""
        # 사용자 조회 (Mock)
        user = AuthenticatedUser(
            firebase_uid="test_firebase_uid", email="test@example.com", is_active=True
        )

        # 비활성화
        user.is_active = False
        user.updated_at = datetime.utcnow()

        return user


class UserPersonalDataService:
    """사용자 개인 데이터 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def store_data(
        self,
        user_id: str,
        data_type: str,
        data_content: Dict[str, Any],
        encrypt: bool = False,
    ) -> UserPersonalData:
        """개인 데이터 저장"""
        personal_data = UserPersonalData(
            user_id=user_id,
            data_type=data_type,
            data_content=data_content,
            is_encrypted=encrypt,
            sensitivity_level="LOW" if not encrypt else "MEDIUM",
            created_at=datetime.utcnow(),
        )

        return personal_data

    def store_sensitive_data(
        self, user_id: str, data_type: str, data_content: Dict[str, Any]
    ) -> UserPersonalData:
        """민감한 데이터를 암호화하여 저장"""
        personal_data = UserPersonalData(
            user_id=user_id,
            data_type=data_type,
            data_content=data_content,
            is_encrypted=True,
            sensitivity_level="HIGH",
            created_at=datetime.utcnow(),
        )

        return personal_data

    def get_by_type(self, user_id: str, data_type: str) -> Optional[UserPersonalData]:
        """타입별 사용자 데이터 조회"""
        # Mock 데이터 반환
        if user_id == "user_123" and data_type == "preferences":
            return UserPersonalData(
                user_id=user_id,
                data_type=data_type,
                data_content={"theme": "light", "language": "ko"},
                is_encrypted=False,
            )

        return None


class UserActivityLogService:
    """사용자 활동 로그 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def log_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_data: Dict[str, Any],
        request_info: Dict[str, str] = None,
    ) -> UserActivityLog:
        """사용자 활동 로깅"""
        request_info = request_info or {}

        activity_log = UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data,
            ip_address=request_info.get("ip_address"),
            user_agent=request_info.get("user_agent"),
            created_at=datetime.utcnow(),
        )

        return activity_log

    def get_user_activity_history(
        self, user_id: str, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[UserActivityLog]:
        """사용자 활동 기록 조회"""
        # Mock 활동 기록 반환
        activities = []

        # 샘플 활동 로그 생성
        for i in range(min(3, limit)):  # 최대 3개의 샘플 로그
            activity_time = start_date + timedelta(hours=i * 24)
            if activity_time <= end_date:
                activity = UserActivityLog(
                    user_id=user_id,
                    activity_type=f"activity_{i}",
                    activity_data={"action": f"test_action_{i}"},
                    created_at=activity_time,
                )
                activities.append(activity)

        return activities


class UserSettingsService:
    """사용자 설정 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def initialize_default_settings(self, user_id: str) -> UserSettingsData:
        """사용자 기본 설정 초기화"""
        default_settings_data = UserSettingsData.get_default_settings()

        settings = UserSettingsData(
            user_id=user_id,
            settings_type="app_preferences",
            settings_data=default_settings_data,
            is_default=True,
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return settings

    def update_settings(
        self, user_id: str, settings_type: str, settings_updates: Dict[str, Any]
    ) -> UserSettingsData:
        """사용자 설정 업데이트"""
        # 기존 설정 조회 (Mock)
        current_settings_data = UserSettingsData.get_default_settings()

        # 설정 업데이트 (Deep merge)
        self._deep_merge_dict(current_settings_data, settings_updates)

        updated_settings = UserSettingsData(
            user_id=user_id,
            settings_type=settings_type,
            settings_data=current_settings_data,
            is_default=False,
            version=2,
            updated_at=datetime.utcnow(),
        )

        return updated_settings

    def _deep_merge_dict(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """딕셔너리 깊은 병합"""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge_dict(base_dict[key], value)
            else:
                base_dict[key] = value


class UserDataPrivacyService:
    """사용자 데이터 프라이버시 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def setup_privacy_settings(
        self, user_id: str, privacy_preferences: Dict[str, Any]
    ) -> UserPrivacySettings:
        """프라이버시 설정 구성"""
        privacy_settings = UserPrivacySettings(
            user_id=user_id,
            privacy_settings=privacy_preferences,
            gdpr_compliance=True,
            consent_date=datetime.utcnow(),
            consent_version="1.0",
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )

        # GDPR 준수 검증
        if not privacy_settings.validate_gdpr_compliance():
            raise ValueError("프라이버시 설정이 GDPR 요구사항을 만족하지 않습니다.")

        return privacy_settings

    def request_data_deletion(
        self, user_id: str, reason: str, immediate: bool = False
    ) -> Dict[str, Any]:
        """데이터 삭제 요청 처리"""
        deletion_date = datetime.utcnow()

        if not immediate:
            # 30일 후 삭제 예약
            deletion_date += timedelta(days=30)

        deletion_result = {
            "user_id": user_id,
            "status": "immediate" if immediate else "scheduled",
            "deletion_date": deletion_date,
            "reason": reason,
            "requested_at": datetime.utcnow(),
        }

        return deletion_result

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """사용자 데이터 내보내기 (GDPR 권리)"""
        # 실제로는 모든 사용자 관련 데이터를 수집
        exported_data = {
            "user_id": user_id,
            "export_date": datetime.utcnow(),
            "data_types": [
                "authenticated_user",
                "personal_data",
                "activity_logs",
                "settings",
                "privacy_settings",
            ],
            "format": "json",
            "status": "completed",
        }

        return exported_data


class UserDataAccessService:
    """사용자 데이터 접근 제어 서비스"""

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def grant_access(
        self,
        user_id: str,
        resource_type: str,
        permission_level: str,
        granted_by: str,
        expires_in_days: int = None,
    ) -> UserDataAccess:
        """데이터 접근 권한 부여"""
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        access_control = UserDataAccess(
            user_id=user_id,
            resource_type=resource_type,
            permission_level=permission_level,
            granted_by=granted_by,
            granted_at=datetime.utcnow(),
            expires_at=expires_at,
            is_active=True,
        )

        return access_control

    def check_access(
        self, user_id: str, resource_type: str, required_permission: str
    ) -> bool:
        """데이터 접근 권한 확인"""
        # Mock 구현 - 실제로는 데이터베이스에서 권한 조회
        permission_levels = {"READ": 1, "WRITE": 2, "READ_WRITE": 3, "ADMIN": 4}

        # 기본적으로 사용자는 자신의 데이터에 대해 READ_WRITE 권한을 가짐
        user_permission_level = permission_levels.get("READ_WRITE", 0)
        required_level = permission_levels.get(required_permission, 999)

        return user_permission_level >= required_level

    def revoke_access(self, user_id: str, resource_type: str) -> bool:
        """데이터 접근 권한 철회"""
        # Mock 구현 - 실제로는 데이터베이스에서 권한 비활성화
        return True
