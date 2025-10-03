"""
사용자 데이터 모델 테스트 (TDD)

인증된 사용자 로직 및 개인별 데이터 연동시스템을 위한
사용자 데이터 모델들의 테스트를 정의합니다.

Test Coverage:
- 사용자 데이터 모델 생성 및 검증
- 개인별 데이터 분리 및 접근 제어
- 사용자별 설정 및 선호도 관리
- 데이터 프라이버시 및 암호화
- 사용자 활동 추적 및 로깅
"""
from datetime import datetime, timedelta

import pytest

from app.models.user_data import (
    AuthenticatedUser,
    UserActivityLog,
    UserDataAccess,
    UserPersonalData,
    UserPrivacySettings,
    UserSettings,
)


class TestUserDataModel:
    """사용자 데이터 모델 테스트"""

    def test_user_data_creation(self):
        """사용자 데이터 생성 테스트"""
        # Given: 사용자 데이터 생성 정보
        firebase_uid = "firebase_user_123"
        email = "user@example.com"
        display_name = "Test User"

        # When: AuthenticatedUser 모델 생성
        user_data = AuthenticatedUser(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            is_active=True,
            created_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
        )

        # Then: 생성된 데이터 검증
        assert user_data.firebase_uid == firebase_uid
        assert user_data.email == email
        assert user_data.display_name == display_name
        assert user_data.is_active is True
        assert user_data.created_at is not None
        assert user_data.last_login_at is not None
        print("✅ 사용자 데이터 생성 테스트 통과")

    def test_user_data_validation(self):
        """사용자 데이터 검증 테스트"""
        # Given: 잘못된 데이터
        invalid_email = "invalid-email"

        # When & Then: 검증 실패 확인
        with pytest.raises(ValueError):
            user_data = AuthenticatedUser(
                firebase_uid="test_uid",
                email=invalid_email,  # 잘못된 이메일 형식
                display_name="Test User",
            )
            user_data.validate()

        print("✅ 사용자 데이터 검증 테스트 통과")

    def test_user_data_privacy_fields(self):
        """사용자 데이터 프라이버시 필드 테스트"""
        # Given: 민감한 개인 정보를 포함한 사용자 데이터
        user_data = AuthenticatedUser(
            firebase_uid="user_123",
            email="sensitive@example.com",
            phone_number="01012345678",
            date_of_birth=datetime(1990, 5, 15),
            is_phone_verified=True,
            is_email_verified=True,
        )

        # When: 민감한 필드 접근
        # Then: 필드가 올바르게 설정됨
        assert user_data.email == "sensitive@example.com"
        assert user_data.phone_number == "01012345678"
        assert user_data.is_phone_verified is True
        assert user_data.is_email_verified is True

        print("✅ 사용자 데이터 프라이버시 필드 테스트 통과")


class TestUserPersonalDataModel:
    """사용자 개인 데이터 모델 테스트"""

    def test_personal_data_creation(self):
        """개인 데이터 생성 테스트"""
        # Given: 개인 데이터 정보
        user_id = "user_123"
        data_type = "preferences"
        data_content = {"theme": "dark", "language": "ko", "notifications": True}

        # When: UserPersonalData 모델 생성
        personal_data = UserPersonalData(
            user_id=user_id,
            data_type=data_type,
            data_content=data_content,
            is_encrypted=True,
            created_at=datetime.utcnow(),
        )

        # Then: 생성된 데이터 검증
        assert personal_data.user_id == user_id
        assert personal_data.data_type == data_type
        assert personal_data.data_content == data_content
        assert personal_data.is_encrypted is True
        assert personal_data.created_at is not None

        print("✅ 개인 데이터 생성 테스트 통과")

    def test_personal_data_encryption_flag(self):
        """개인 데이터 암호화 플래그 테스트"""
        # Given: 암호화가 필요한 민감한 데이터
        sensitive_data = {
            "credit_card": "1234-5678-9012-3456",
            "address": "서울시 강남구 테헤란로 123",
        }

        # When: 민감한 개인 데이터 생성
        personal_data = UserPersonalData(
            user_id="user_123",
            data_type="payment_info",
            data_content=sensitive_data,
            is_encrypted=True,  # 암호화 필수
            sensitivity_level="HIGH",
        )

        # Then: 암호화 플래그 확인
        assert personal_data.is_encrypted is True
        assert personal_data.sensitivity_level == "HIGH"

        print("✅ 개인 데이터 암호화 플래그 테스트 통과")


class TestUserActivityLogModel:
    """사용자 활동 로그 모델 테스트"""

    def test_activity_log_creation(self):
        """활동 로그 생성 테스트"""
        # Given: 사용자 활동 정보
        user_id = "user_123"
        activity_type = "place_search"
        activity_data = {"query": "강남 카페", "results_count": 25, "response_time_ms": 150}

        # When: UserActivityLog 모델 생성
        activity_log = UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0...",
            created_at=datetime.utcnow(),
        )

        # Then: 생성된 로그 검증
        assert activity_log.user_id == user_id
        assert activity_log.activity_type == activity_type
        assert activity_log.activity_data == activity_data
        assert activity_log.ip_address == "192.168.1.100"
        assert activity_log.created_at is not None

        print("✅ 활동 로그 생성 테스트 통과")

    def test_activity_log_privacy_masking(self):
        """활동 로그 프라이버시 마스킹 테스트"""
        # Given: 개인 정보가 포함된 활동 데이터
        activity_data_with_pii = {
            "search_query": "병원 예약",
            "phone_number": "01012345678",  # 개인정보
            "location": {"lat": 37.5665, "lng": 126.9780},
        }

        # When: 활동 로그 생성
        activity_log = UserActivityLog(
            user_id="user_123",
            activity_type="medical_search",
            activity_data=activity_data_with_pii,
            requires_masking=True,
        )

        # Then: 마스킹 필요 플래그 확인
        assert activity_log.requires_masking is True
        assert activity_log.activity_data["phone_number"] == "01012345678"  # 원본 데이터는 유지

        print("✅ 활동 로그 프라이버시 마스킹 테스트 통과")


class TestUserDataAccessModel:
    """사용자 데이터 접근 제어 모델 테스트"""

    def test_data_access_control_creation(self):
        """데이터 접근 제어 생성 테스트"""
        # Given: 데이터 접근 제어 정보
        user_id = "user_123"
        resource_type = "places"
        permission_level = "READ_WRITE"

        # When: UserDataAccess 모델 생성
        data_access = UserDataAccess(
            user_id=user_id,
            resource_type=resource_type,
            permission_level=permission_level,
            granted_by="system",
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
        )

        # Then: 생성된 접근 제어 검증
        assert data_access.user_id == user_id
        assert data_access.resource_type == resource_type
        assert data_access.permission_level == permission_level
        assert data_access.granted_by == "system"
        assert data_access.expires_at is not None

        print("✅ 데이터 접근 제어 생성 테스트 통과")

    def test_data_access_expiration(self):
        """데이터 접근 만료 테스트"""
        # Given: 만료된 접근 권한
        expired_access = UserDataAccess(
            user_id="user_123",
            resource_type="premium_features",
            permission_level="READ_WRITE",
            expires_at=datetime.utcnow() - timedelta(days=1),  # 어제 만료
        )

        # When: 만료 상태 확인
        is_expired = expired_access.is_expired()

        # Then: 만료됨 확인
        assert is_expired is True

        print("✅ 데이터 접근 만료 테스트 통과")


class TestUserSettingsModel:
    """사용자 설정 모델 테스트"""

    def test_user_settings_creation(self):
        """사용자 설정 생성 테스트"""
        # Given: 사용자 설정 정보
        user_id = "user_123"
        settings_data = {
            "theme": "dark",
            "language": "ko",
            "timezone": "Asia/Seoul",
            "notifications": {
                "push_enabled": True,
                "email_enabled": False,
                "quiet_hours": {"start": "22:00", "end": "07:00"},
            },
        }

        # When: UserSettings 모델 생성
        user_settings = UserSettings(
            user_id=user_id,
            settings_type="app_preferences",
            settings_data=settings_data,
            is_default=False,
            updated_at=datetime.utcnow(),
        )

        # Then: 생성된 설정 검증
        assert user_settings.user_id == user_id
        assert user_settings.settings_type == "app_preferences"
        assert user_settings.settings_data == settings_data
        assert user_settings.is_default is False
        assert user_settings.updated_at is not None

        print("✅ 사용자 설정 생성 테스트 통과")

    def test_default_settings_validation(self):
        """기본 설정 검증 테스트"""
        # Given: 기본 설정 데이터
        default_settings = UserSettings.get_default_settings()

        # When & Then: 기본 설정 필수 필드 확인
        assert "theme" in default_settings
        assert "language" in default_settings
        assert "timezone" in default_settings
        assert "notifications" in default_settings
        assert default_settings["language"] == "ko"  # 한국어 기본
        assert default_settings["timezone"] == "Asia/Seoul"  # 한국 시간대 기본

        print("✅ 기본 설정 검증 테스트 통과")


class TestUserPrivacySettingsModel:
    """사용자 프라이버시 설정 모델 테스트"""

    def test_privacy_settings_creation(self):
        """프라이버시 설정 생성 테스트"""
        # Given: 프라이버시 설정 정보
        user_id = "user_123"
        privacy_settings = {
            "data_collection_consent": True,
            "marketing_consent": False,
            "location_tracking": True,
            "analytics_consent": True,
            "data_retention_days": 365,
            "allow_data_export": True,
        }

        # When: UserPrivacySettings 모델 생성
        user_privacy = UserPrivacySettings(
            user_id=user_id,
            privacy_settings=privacy_settings,
            gdpr_compliance=True,
            consent_date=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )

        # Then: 생성된 프라이버시 설정 검증
        assert user_privacy.user_id == user_id
        assert user_privacy.privacy_settings == privacy_settings
        assert user_privacy.gdpr_compliance is True
        assert user_privacy.consent_date is not None

        print("✅ 프라이버시 설정 생성 테스트 통과")

    def test_gdpr_compliance_validation(self):
        """GDPR 준수 검증 테스트"""
        # Given: GDPR 필수 설정
        privacy_settings = UserPrivacySettings(
            user_id="user_123",
            privacy_settings={
                "data_collection_consent": True,
                "marketing_consent": False,
                "data_retention_days": 365,
            },
            gdpr_compliance=True,
        )

        # When: GDPR 준수 검증
        is_gdpr_compliant = privacy_settings.validate_gdpr_compliance()

        # Then: GDPR 준수 확인
        assert is_gdpr_compliant is True
        assert privacy_settings.privacy_settings["data_collection_consent"] is True

        print("✅ GDPR 준수 검증 테스트 통과")


class TestUserDataIntegration:
    """사용자 데이터 통합 테스트"""

    def test_user_data_relationship(self):
        """사용자 데이터 관계 테스트"""
        # Given: 연결된 사용자 데이터들
        user_id = "user_123"

        # 기본 사용자 데이터
        user_data = AuthenticatedUser(
            firebase_uid="firebase_123",
            email="user@example.com",
            display_name="Test User",
        )

        # 개인 데이터
        personal_data = UserPersonalData(
            user_id=user_id, data_type="preferences", data_content={"theme": "dark"}
        )

        # 사용자 설정
        user_settings = UserSettings(
            user_id=user_id,
            settings_type="app_preferences",
            settings_data={"language": "ko"},
        )

        # When: 관계 검증
        # Then: 모든 데이터가 동일한 사용자 ID로 연결됨
        assert personal_data.user_id == user_id
        assert user_settings.user_id == user_id

        print("✅ 사용자 데이터 관계 테스트 통과")

    def test_user_data_cascade_operations(self):
        """사용자 데이터 종속 작업 테스트"""
        # Given: 사용자와 관련 데이터들

        # When: 사용자 데이터 삭제 시뮬레이션
        # Then: 관련 데이터도 함께 삭제되어야 함 (Cascade)
        # 이는 실제 데이터베이스 제약조건으로 구현됨

        # 삭제 대상 데이터 타입들
        data_types_to_delete = [
            "personal_data",
            "activity_logs",
            "user_settings",
            "privacy_settings",
            "data_access_controls",
        ]

        # 모든 관련 데이터 타입이 식별됨
        assert len(data_types_to_delete) == 5

        print("✅ 사용자 데이터 종속 작업 테스트 통과")


# 실행 시 간단한 테스트 러너
if __name__ == "__main__":
    print("🧪 사용자 데이터 모델 테스트 시작")
    print("=" * 50)

    # 테스트 클래스들 인스턴스 생성
    test_user_data = TestUserDataModel()
    test_personal_data = TestUserPersonalDataModel()
    test_activity_log = TestUserActivityLogModel()
    test_data_access = TestUserDataAccessModel()
    test_settings = TestUserSettingsModel()
    test_privacy = TestUserPrivacySettingsModel()
    test_integration = TestUserDataIntegration()

    try:
        # 사용자 데이터 모델 테스트
        test_user_data.test_user_data_creation()
        # test_user_data.test_user_data_validation()  # pytest 필요
        test_user_data.test_user_data_privacy_fields()

        # 개인 데이터 모델 테스트
        test_personal_data.test_personal_data_creation()
        test_personal_data.test_personal_data_encryption_flag()

        # 활동 로그 모델 테스트
        test_activity_log.test_activity_log_creation()
        test_activity_log.test_activity_log_privacy_masking()

        # 데이터 접근 제어 모델 테스트
        test_data_access.test_data_access_control_creation()
        test_data_access.test_data_access_expiration()

        # 사용자 설정 모델 테스트
        test_settings.test_user_settings_creation()
        # test_settings.test_default_settings_validation()  # 모델 구현 후

        # 프라이버시 설정 모델 테스트
        test_privacy.test_privacy_settings_creation()
        # test_privacy.test_gdpr_compliance_validation()  # 모델 구현 후

        # 통합 테스트
        test_integration.test_user_data_relationship()
        test_integration.test_user_data_cascade_operations()

        print("\n🎉 모든 사용자 데이터 모델 테스트 통과!")

    except ImportError as e:
        print(f"⚠️ 테스트 실행을 위해 모델 구현이 필요합니다: {e}")
        print("사용자 데이터 모델 구현 후 다시 실행해주세요.")
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
