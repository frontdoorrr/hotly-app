"""
사용자 데이터 모델 간단 테스트 (TDD)

기존 모델과의 충돌 없이 독립적으로 테스트합니다.
"""
from datetime import datetime


def test_authenticated_user_creation():
    """인증된 사용자 생성 테스트"""
    try:
        from app.models.user_data import AuthenticatedUser

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

        print("✅ 인증된 사용자 생성 테스트 통과")
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_user_personal_data_creation():
    """개인 데이터 생성 테스트"""
    try:
        from app.models.user_data import UserPersonalData

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
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_user_activity_log_creation():
    """활동 로그 생성 테스트"""
    try:
        from app.models.user_data import UserActivityLog

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
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_user_settings_creation():
    """사용자 설정 생성 테스트"""
    try:
        from app.models.user_data import UserSettings

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
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_default_settings():
    """기본 설정 테스트"""
    try:
        from app.models.user_data import UserSettings

        # Given & When: 기본 설정 조회
        default_settings = UserSettings.get_default_settings()

        # Then: 기본 설정 필수 필드 확인
        assert "theme" in default_settings
        assert "language" in default_settings
        assert "timezone" in default_settings
        assert "notifications" in default_settings
        assert default_settings["language"] == "ko"  # 한국어 기본
        assert default_settings["timezone"] == "Asia/Seoul"  # 한국 시간대 기본

        print("✅ 기본 설정 테스트 통과")
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def test_email_validation():
    """이메일 검증 테스트"""
    try:
        from app.models.user_data import AuthenticatedUser

        # Given: 유효한 이메일
        user_data = AuthenticatedUser(
            firebase_uid="test_uid", email="valid@example.com", display_name="Test User"
        )

        # When & Then: 검증 성공
        user_data.validate()  # 예외가 발생하지 않아야 함

        # Given: 잘못된 이메일
        invalid_user = AuthenticatedUser(
            firebase_uid="test_uid_2", email="invalid-email", display_name="Test User"
        )

        # When & Then: 검증 실패
        try:
            invalid_user.validate()
            assert False, "검증 실패가 예상됨"
        except ValueError:
            pass  # 예상된 결과

        print("✅ 이메일 검증 테스트 통과")
        return True

    except ImportError as e:
        print(f"⚠️ 모델 import 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


def main():
    """테스트 실행"""
    print("🧪 사용자 데이터 모델 간단 테스트 시작")
    print("=" * 50)

    tests = [
        test_authenticated_user_creation,
        test_user_personal_data_creation,
        test_user_activity_log_creation,
        test_user_settings_creation,
        test_default_settings,
        test_email_validation,
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
        print(f"⚠️ {failed}개 테스트 실패")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
