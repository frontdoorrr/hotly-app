#!/usr/bin/env python3
"""
Firebase Auth 수동 테스트

의존성 없이 직접 Firebase Auth 서비스를 테스트합니다.
"""
import asyncio
import sys
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# 프로젝트 경로 추가
sys.path.append('/Users/jeongmun/Documents/GitHub/hotly-app')


class MockRequests:
    """requests 모듈 목킹"""
    class Response:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json_data = json_data
            
        def json(self):
            return self._json_data
    
    @staticmethod
    def get(url, headers=None, timeout=None):
        # Kakao API 응답 목킹
        if 'kapi.kakao.com' in url:
            return MockRequests.Response(200, {
                'id': 12345678,
                'kakao_account': {
                    'email': 'user@kakao.com',
                    'profile': {
                        'nickname': '카카오유저',
                        'profile_image_url': 'http://k.kakaocdn.net/...'
                    }
                }
            })
        return MockRequests.Response(404)


# requests 모듈을 목 객체로 대체
sys.modules['requests'] = MockRequests()

try:
    from app.services.firebase_auth_service import FirebaseAuthService
    from app.schemas.auth import (
        SocialLoginRequest, 
        SocialProvider,
        TokenRefreshRequest,
        AnonymousUserRequest
    )
except ImportError as e:
    print(f"❌ Import 실패: {e}")
    sys.exit(1)


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        
    def assert_true(self, condition, message=""):
        if condition:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"❌ FAILED: {message}")
            return False
    
    def assert_equal(self, actual, expected, message=""):
        if actual == expected:
            self.passed += 1
            return True
        else:
            self.failed += 1
            print(f"❌ FAILED: {message} - Expected {expected}, got {actual}")
            return False
    
    def print_summary(self):
        total = self.passed + self.failed
        print(f"\n📊 테스트 결과:")
        print(f"   ✅ 통과: {self.passed}")
        print(f"   ❌ 실패: {self.failed}")
        print(f"   📈 전체: {total}")
        
        if self.failed == 0:
            print("🎉 모든 테스트 통과!")
        else:
            print(f"⚠️ {self.failed}개 테스트 실패")


async def test_firebase_auth():
    """Firebase Auth 서비스 테스트"""
    runner = TestRunner()
    
    print("🧪 Firebase Authentication 테스트 시작")
    print("=" * 50)
    
    # Mock 서비스 설정
    mock_firebase_app = MagicMock()
    mock_firebase_auth = AsyncMock()
    
    # Mock cache service
    mock_cache = AsyncMock()
    mock_cache.get.return_value = None
    mock_cache.set.return_value = True
    mock_cache.delete.return_value = True
    
    # FirebaseAuthService 생성
    auth_service = FirebaseAuthService(
        firebase_app=mock_firebase_app,
        firebase_auth=mock_firebase_auth
    )
    auth_service.cache = mock_cache
    
    print("\n1️⃣ 서비스 초기화 테스트")
    runner.assert_true(
        auth_service.firebase_app is not None,
        "Firebase app 초기화"
    )
    runner.assert_true(
        auth_service.firebase_auth is not None,
        "Firebase auth 초기화"
    )
    print("   ✅ 서비스 초기화 테스트 통과")
    
    print("\n2️⃣ Firebase 설정 검증 테스트")
    config_valid = await auth_service.validate_firebase_config()
    runner.assert_true(config_valid, "Firebase 설정 유효성")
    print("   ✅ 설정 검증 테스트 통과")
    
    print("\n3️⃣ Google 로그인 테스트")
    google_request = SocialLoginRequest(
        provider=SocialProvider.GOOGLE,
        id_token="mock_google_id_token",
        device_id="test_device_123"
    )
    
    # Mock Firebase Google 응답
    mock_firebase_auth.verify_id_token.return_value = {
        'uid': 'google_user_123',
        'email': 'user@gmail.com',
        'name': '김철수',
        'picture': 'https://lh3.googleusercontent.com/...',
        'email_verified': True
    }
    
    google_result = await auth_service.login_with_social(google_request)
    
    runner.assert_true(google_result.success, "Google 로그인 성공")
    runner.assert_equal(
        google_result.user_profile.email, 
        'user@gmail.com', 
        "Google 사용자 이메일"
    )
    runner.assert_equal(
        google_result.user_profile.provider, 
        SocialProvider.GOOGLE,
        "Google 제공자 확인"
    )
    runner.assert_true(
        google_result.access_token is not None,
        "액세스 토큰 생성"
    )
    print("   ✅ Google 로그인 테스트 통과")
    
    print("\n4️⃣ Apple 로그인 테스트")
    apple_request = SocialLoginRequest(
        provider=SocialProvider.APPLE,
        id_token="mock_apple_id_token",
        device_id="test_device_456"
    )
    
    # Mock Firebase Apple 응답
    mock_firebase_auth.verify_id_token.return_value = {
        'uid': 'apple_user_456',
        'email': 'user@privaterelay.appleid.com',
        'name': None,
        'email_verified': True
    }
    
    apple_result = await auth_service.login_with_social(apple_request)
    
    runner.assert_true(apple_result.success, "Apple 로그인 성공")
    runner.assert_equal(
        apple_result.user_profile.provider, 
        SocialProvider.APPLE,
        "Apple 제공자 확인"
    )
    runner.assert_true(
        'privaterelay.appleid.com' in apple_result.user_profile.email,
        "Apple 이메일 형식"
    )
    print("   ✅ Apple 로그인 테스트 통과")
    
    print("\n5️⃣ Kakao 로그인 테스트")
    kakao_request = SocialLoginRequest(
        provider=SocialProvider.KAKAO,
        access_token="mock_kakao_access_token",
        device_id="test_device_789"
    )
    
    # Mock Firebase custom token
    mock_firebase_auth.create_custom_token.return_value = "custom_firebase_token"
    
    kakao_result = await auth_service.login_with_social(kakao_request)
    
    runner.assert_true(kakao_result.success, "Kakao 로그인 성공")
    runner.assert_equal(
        kakao_result.user_profile.provider,
        SocialProvider.KAKAO,
        "Kakao 제공자 확인"
    )
    runner.assert_equal(
        kakao_result.user_profile.name,
        '카카오유저',
        "Kakao 사용자 이름"
    )
    print("   ✅ Kakao 로그인 테스트 통과")
    
    print("\n6️⃣ 토큰 검증 테스트")
    # 이전 Google 로그인에서 생성된 토큰 사용
    access_token = google_result.access_token
    
    # 토큰 정보를 캐시에 설정
    from datetime import timedelta
    mock_cache.get.return_value = {
        'user_id': 'google_user_123',
        'expires_at': (datetime.utcnow().replace(microsecond=0) + 
                      timedelta(hours=1)).isoformat()
    }
    
    token_result = await auth_service.validate_access_token(access_token)
    
    runner.assert_true(token_result.is_valid, "토큰 유효성")
    runner.assert_equal(
        token_result.user_id,
        'google_user_123',
        "토큰에서 사용자 ID 추출"
    )
    print("   ✅ 토큰 검증 테스트 통과")
    
    print("\n7️⃣ 만료된 토큰 처리 테스트")
    # ExpiredIdTokenError 모킹
    class MockExpiredIdTokenError(Exception):
        pass
    
    # Firebase auth에서 만료 에러 발생
    mock_firebase_auth.verify_id_token.side_effect = MockExpiredIdTokenError("Token expired")
    mock_cache.get.return_value = None
    
    expired_result = await auth_service.validate_access_token("expired_token")
    
    runner.assert_true(not expired_result.is_valid, "만료된 토큰 거부")
    print("   ✅ 만료된 토큰 처리 테스트 통과")
    
    # 사이드 이펙트 초기화
    mock_firebase_auth.verify_id_token.side_effect = None
    
    print("\n8️⃣ 토큰 갱신 테스트")
    refresh_request = TokenRefreshRequest(
        refresh_token="valid_refresh_token",
        device_id="test_device_123"
    )
    
    # Mock refresh token 정보
    mock_cache.get.return_value = {
        'user_id': 'google_user_123',
        'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    refresh_result = await auth_service.refresh_tokens(refresh_request)
    
    runner.assert_true(refresh_result.success, "토큰 갱신 성공")
    runner.assert_true(
        refresh_result.new_access_token is not None,
        "새 액세스 토큰 생성"
    )
    runner.assert_true(
        refresh_result.new_refresh_token is not None,
        "새 리프레시 토큰 생성"
    )
    print("   ✅ 토큰 갱신 테스트 통과")
    
    print("\n9️⃣ 세션 관리 테스트")
    user_id = "user_123"
    device_id = "device_456"
    session_token = "session_token_789"
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # 세션 생성
    session_created = await auth_service.create_user_session(
        user_id=user_id,
        device_id=device_id,
        session_token=session_token,
        expires_at=expires_at
    )
    
    runner.assert_true(session_created, "세션 생성")
    
    # 세션 조회
    mock_cache.get.return_value = {
        'user_id': user_id,
        'device_id': device_id,
        'session_token': session_token,
        'created_at': datetime.utcnow().isoformat(),
        'expires_at': expires_at.isoformat(),
        'is_active': True
    }
    
    session_info = await auth_service.get_user_session(user_id, device_id)
    
    runner.assert_true(session_info is not None, "세션 조회")
    runner.assert_equal(session_info.user_id, user_id, "세션 사용자 ID")
    runner.assert_equal(session_info.device_id, device_id, "세션 디바이스 ID")
    runner.assert_true(session_info.is_active, "세션 활성 상태")
    
    # 세션 종료
    session_terminated = await auth_service.terminate_user_session(user_id, device_id)
    runner.assert_true(session_terminated, "세션 종료")
    
    print("   ✅ 세션 관리 테스트 통과")
    
    print("\n🔟 익명 사용자 생성 테스트")
    device_id = "anonymous_device_123"
    
    # Mock Firebase 익명 사용자 생성
    mock_firebase_auth.create_user.return_value = MagicMock(uid='anon_user_123')
    
    anonymous_result = await auth_service.create_anonymous_user(device_id)
    
    runner.assert_true(anonymous_result.success, "익명 사용자 생성 성공")
    runner.assert_true(
        anonymous_result.user_profile.is_anonymous,
        "익명 사용자 플래그"
    )
    runner.assert_true(
        'anon_user_123' in anonymous_result.user_profile.user_id,
        "익명 사용자 ID"
    )
    print("   ✅ 익명 사용자 생성 테스트 통과")
    
    print("\n1️⃣1️⃣ 사용자 권한 테스트")
    guest_user_id = "guest_123"
    
    permissions = await auth_service.get_user_permissions(guest_user_id)
    
    runner.assert_true(not permissions.can_create_courses, "게스트 코스 생성 제한")
    runner.assert_true(not permissions.can_share_content, "게스트 공유 제한")
    runner.assert_true(permissions.can_view_content, "게스트 조회 허용")
    runner.assert_equal(permissions.data_retention_days, 7, "게스트 데이터 보존 기간")
    
    print("   ✅ 사용자 권한 테스트 통과")
    
    print("\n1️⃣2️⃣ 의심스러운 활동 감지 테스트")
    user_id = "user_123"
    
    security_alert = await auth_service.check_suspicious_activity(user_id)
    
    runner.assert_true(security_alert is not None, "보안 경고 생성")
    runner.assert_true(hasattr(security_alert, 'is_suspicious'), "의심 활동 플래그")
    runner.assert_true(hasattr(security_alert, 'risk_level'), "위험 수준")
    
    print("   ✅ 의심스러운 활동 감지 테스트 통과")
    
    runner.print_summary()
    return runner.failed == 0


def main():
    """메인 실행 함수"""
    print("🚀 Firebase Authentication 테스트 시작")
    print("Firebase 서비스의 모든 핵심 기능을 테스트합니다.")
    
    # 비동기 테스트 실행
    success = asyncio.run(test_firebase_auth())
    
    if success:
        print("\n🎉 모든 Firebase Auth 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 구현을 확인해주세요.")
        return 1


if __name__ == "__main__":
    exit(main())