"""
사용자 데이터 서비스 테스트 (TDD)

인증된 사용자 로직 및 개인별 데이터 연동을 위한
사용자 데이터 서비스들의 테스트를 정의합니다.

Test Coverage:
- Firebase UID로 사용자 생성/조회/업데이트
- 사용자 개인 데이터 CRUD 작업
- 사용자 활동 로깅 서비스
- 사용자 설정 관리 서비스
- 데이터 접근 제어 서비스
- GDPR 준수 및 데이터 삭제 서비스
"""
from datetime import datetime, timedelta
from uuid import uuid4
import pytest


class TestAuthenticatedUserService:
    """인증된 사용자 서비스 테스트"""
    
    def test_create_user_from_firebase_auth(self):
        """Firebase 인증 정보로 사용자 생성 테스트"""
        # Given: Firebase 인증 정보
        firebase_uid = "firebase_user_123"
        email = "newuser@example.com"
        display_name = "New User"
        
        # When: 서비스를 통해 사용자 생성
        try:
            from app.services.user_data_service import AuthenticatedUserService
            service = AuthenticatedUserService()
            
            user = service.create_from_firebase_auth(
                firebase_uid=firebase_uid,
                email=email,
                display_name=display_name
            )
            
            # Then: 사용자가 올바르게 생성됨
            assert user.firebase_uid == firebase_uid
            assert user.email == email
            assert user.display_name == display_name
            assert user.is_active is True
            assert user.created_at is not None
            
            print("✅ Firebase 인증으로 사용자 생성 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticatedUserService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_get_user_by_firebase_uid(self):
        """Firebase UID로 사용자 조회 테스트"""
        # Given: 존재하는 Firebase UID
        firebase_uid = "existing_user_123"
        
        try:
            from app.services.user_data_service import AuthenticatedUserService
            service = AuthenticatedUserService()
            
            # When: Firebase UID로 사용자 조회
            user = service.get_by_firebase_uid(firebase_uid)
            
            # Then: 사용자를 찾거나 None 반환
            if user:
                assert user.firebase_uid == firebase_uid
                assert user.is_active is True
            
            print("✅ Firebase UID로 사용자 조회 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticatedUserService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_update_user_profile(self):
        """사용자 프로필 업데이트 테스트"""
        # Given: 업데이트할 사용자 정보
        user_id = "user_123"
        profile_updates = {
            "display_name": "Updated Name",
            "phone_number": "01087654321",
            "is_phone_verified": True
        }
        
        try:
            from app.services.user_data_service import AuthenticatedUserService
            service = AuthenticatedUserService()
            
            # When: 프로필 업데이트
            updated_user = service.update_profile(user_id, profile_updates)
            
            # Then: 업데이트된 정보 확인
            assert updated_user.display_name == profile_updates["display_name"]
            assert updated_user.phone_number == profile_updates["phone_number"]
            assert updated_user.is_phone_verified == profile_updates["is_phone_verified"]
            assert updated_user.updated_at is not None
            
            print("✅ 사용자 프로필 업데이트 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticatedUserService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_deactivate_user(self):
        """사용자 비활성화 테스트"""
        # Given: 활성화된 사용자
        user_id = "active_user_123"
        
        try:
            from app.services.user_data_service import AuthenticatedUserService
            service = AuthenticatedUserService()
            
            # When: 사용자 비활성화
            deactivated_user = service.deactivate_user(user_id)
            
            # Then: 비활성화 상태 확인
            assert deactivated_user.is_active is False
            assert deactivated_user.updated_at is not None
            
            print("✅ 사용자 비활성화 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticatedUserService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestUserPersonalDataService:
    """사용자 개인 데이터 서비스 테스트"""
    
    def test_store_personal_data(self):
        """개인 데이터 저장 테스트"""
        # Given: 저장할 개인 데이터
        user_id = "user_123"
        data_type = "preferences"
        data_content = {
            "theme": "dark",
            "language": "ko",
            "notifications": True
        }
        
        try:
            from app.services.user_data_service import UserPersonalDataService
            service = UserPersonalDataService()
            
            # When: 개인 데이터 저장
            stored_data = service.store_data(
                user_id=user_id,
                data_type=data_type,
                data_content=data_content,
                encrypt=False
            )
            
            # Then: 저장된 데이터 검증
            assert stored_data.user_id == user_id
            assert stored_data.data_type == data_type
            assert stored_data.data_content == data_content
            assert stored_data.is_encrypted is False
            
            print("✅ 개인 데이터 저장 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserPersonalDataService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_store_sensitive_data_with_encryption(self):
        """민감한 데이터 암호화 저장 테스트"""
        # Given: 민감한 개인 데이터
        user_id = "user_123"
        sensitive_data = {
            "payment_method": "credit_card",
            "card_last_four": "1234",
            "billing_address": "서울시 강남구"
        }
        
        try:
            from app.services.user_data_service import UserPersonalDataService
            service = UserPersonalDataService()
            
            # When: 민감한 데이터를 암호화하여 저장
            stored_data = service.store_sensitive_data(
                user_id=user_id,
                data_type="payment_info",
                data_content=sensitive_data
            )
            
            # Then: 암호화 저장 확인
            assert stored_data.user_id == user_id
            assert stored_data.is_encrypted is True
            assert stored_data.sensitivity_level == "HIGH"
            
            print("✅ 민감한 데이터 암호화 저장 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserPersonalDataService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_get_user_data_by_type(self):
        """타입별 사용자 데이터 조회 테스트"""
        # Given: 사용자 ID와 데이터 타입
        user_id = "user_123"
        data_type = "preferences"
        
        try:
            from app.services.user_data_service import UserPersonalDataService
            service = UserPersonalDataService()
            
            # When: 타입별 데이터 조회
            user_data = service.get_by_type(user_id, data_type)
            
            # Then: 데이터 조회 확인
            if user_data:
                assert user_data.user_id == user_id
                assert user_data.data_type == data_type
            
            print("✅ 타입별 사용자 데이터 조회 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserPersonalDataService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestUserActivityLogService:
    """사용자 활동 로그 서비스 테스트"""
    
    def test_log_user_activity(self):
        """사용자 활동 로깅 테스트"""
        # Given: 사용자 활동 정보
        user_id = "user_123"
        activity_type = "place_search"
        activity_data = {
            "query": "강남 맛집",
            "results_count": 15,
            "response_time_ms": 120
        }
        request_info = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        }
        
        try:
            from app.services.user_data_service import UserActivityLogService
            service = UserActivityLogService()
            
            # When: 활동 로깅
            activity_log = service.log_activity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data,
                request_info=request_info
            )
            
            # Then: 로그 저장 확인
            assert activity_log.user_id == user_id
            assert activity_log.activity_type == activity_type
            assert activity_log.activity_data == activity_data
            assert activity_log.ip_address == request_info["ip_address"]
            
            print("✅ 사용자 활동 로깅 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserActivityLogService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_get_user_activity_history(self):
        """사용자 활동 기록 조회 테스트"""
        # Given: 조회할 사용자 ID와 기간
        user_id = "user_123"
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
        
        try:
            from app.services.user_data_service import UserActivityLogService
            service = UserActivityLogService()
            
            # When: 활동 기록 조회
            activity_history = service.get_user_activity_history(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=50
            )
            
            # Then: 기록 조회 확인
            assert isinstance(activity_history, list)
            for activity in activity_history:
                assert activity.user_id == user_id
                assert start_date <= activity.created_at <= end_date
            
            print("✅ 사용자 활동 기록 조회 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserActivityLogService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestUserSettingsService:
    """사용자 설정 서비스 테스트"""
    
    def test_initialize_default_settings(self):
        """사용자 기본 설정 초기화 테스트"""
        # Given: 새 사용자 ID
        user_id = "new_user_123"
        
        try:
            from app.services.user_data_service import UserSettingsService
            service = UserSettingsService()
            
            # When: 기본 설정 초기화
            settings = service.initialize_default_settings(user_id)
            
            # Then: 기본 설정 생성 확인
            assert settings.user_id == user_id
            assert settings.is_default is True
            assert "language" in settings.settings_data
            assert settings.settings_data["language"] == "ko"
            
            print("✅ 사용자 기본 설정 초기화 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserSettingsService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_update_user_settings(self):
        """사용자 설정 업데이트 테스트"""
        # Given: 업데이트할 설정
        user_id = "user_123"
        settings_updates = {
            "theme": "dark",
            "notifications": {
                "push_enabled": False,
                "email_enabled": True
            }
        }
        
        try:
            from app.services.user_data_service import UserSettingsService
            service = UserSettingsService()
            
            # When: 설정 업데이트
            updated_settings = service.update_settings(
                user_id=user_id,
                settings_type="app_preferences", 
                settings_updates=settings_updates
            )
            
            # Then: 업데이트 확인
            assert updated_settings.user_id == user_id
            assert updated_settings.settings_data["theme"] == "dark"
            assert updated_settings.settings_data["notifications"]["push_enabled"] is False
            
            print("✅ 사용자 설정 업데이트 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserSettingsService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestUserDataPrivacyService:
    """사용자 데이터 프라이버시 서비스 테스트"""
    
    def test_setup_privacy_settings(self):
        """프라이버시 설정 구성 테스트"""
        # Given: 새 사용자의 프라이버시 설정
        user_id = "user_123"
        privacy_preferences = {
            "data_collection_consent": True,
            "marketing_consent": False,
            "location_tracking": True,
            "analytics_consent": True,
            "data_retention_days": 365  # GDPR 필수 필드 추가
        }
        
        try:
            from app.services.user_data_service import UserDataPrivacyService
            service = UserDataPrivacyService()
            
            # When: 프라이버시 설정 구성
            privacy_settings = service.setup_privacy_settings(
                user_id=user_id,
                privacy_preferences=privacy_preferences
            )
            
            # Then: 설정 구성 확인
            assert privacy_settings.user_id == user_id
            assert privacy_settings.gdpr_compliance is True
            assert privacy_settings.consent_date is not None
            
            print("✅ 프라이버시 설정 구성 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserDataPrivacyService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_request_data_deletion(self):
        """데이터 삭제 요청 테스트"""
        # Given: 데이터 삭제를 요청하는 사용자
        user_id = "user_to_delete_123"
        deletion_reason = "user_request"
        
        try:
            from app.services.user_data_service import UserDataPrivacyService
            service = UserDataPrivacyService()
            
            # When: 데이터 삭제 요청
            deletion_result = service.request_data_deletion(
                user_id=user_id,
                reason=deletion_reason,
                immediate=False  # 30일 후 삭제
            )
            
            # Then: 삭제 요청 처리 확인
            assert deletion_result["user_id"] == user_id
            assert deletion_result["status"] == "scheduled"
            assert deletion_result["deletion_date"] is not None
            
            print("✅ 데이터 삭제 요청 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserDataPrivacyService 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


def main():
    """테스트 실행"""
    print("🧪 사용자 데이터 서비스 테스트 시작")
    print("=" * 50)
    
    # 테스트 클래스 인스턴스 생성
    test_user_service = TestAuthenticatedUserService()
    test_personal_data_service = TestUserPersonalDataService()
    test_activity_service = TestUserActivityLogService()
    test_settings_service = TestUserSettingsService()
    test_privacy_service = TestUserDataPrivacyService()
    
    tests = [
        # 인증된 사용자 서비스 테스트
        test_user_service.test_create_user_from_firebase_auth,
        test_user_service.test_get_user_by_firebase_uid,
        test_user_service.test_update_user_profile,
        test_user_service.test_deactivate_user,
        
        # 개인 데이터 서비스 테스트
        test_personal_data_service.test_store_personal_data,
        test_personal_data_service.test_store_sensitive_data_with_encryption,
        test_personal_data_service.test_get_user_data_by_type,
        
        # 활동 로그 서비스 테스트
        test_activity_service.test_log_user_activity,
        test_activity_service.test_get_user_activity_history,
        
        # 설정 서비스 테스트
        test_settings_service.test_initialize_default_settings,
        test_settings_service.test_update_user_settings,
        
        # 프라이버시 서비스 테스트
        test_privacy_service.test_setup_privacy_settings,
        test_privacy_service.test_request_data_deletion,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {e}")
            failed += 1
    
    print(f"\n📊 테스트 결과:")
    print(f"   ✅ 통과: {passed}")
    print(f"   ❌ 실패: {failed}")
    print(f"   📈 전체: {passed + failed}")
    
    if failed == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️ {failed}개 테스트 실패 - 서비스 구현 필요")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)