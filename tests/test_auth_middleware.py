"""
인증 미들웨어 테스트 (TDD)

Firebase 인증과 내부 사용자 데이터를 연동하는
인증 미들웨어의 테스트를 정의합니다.

Test Coverage:
- Firebase 토큰 검증
- 사용자 인증 상태 확인
- 인증된 사용자 정보 조회/생성
- 권한 기반 접근 제어
- 인증 실패 처리
- 세션 관리
"""
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import jwt
import pytest
from unittest.mock import Mock, AsyncMock


class TestFirebaseAuthMiddleware:
    """Firebase 인증 미들웨어 테스트"""
    
    def test_verify_valid_firebase_token(self):
        """유효한 Firebase 토큰 검증 테스트"""
        # Given: 유효한 Firebase 토큰
        valid_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
        expected_claims = {
            "uid": "firebase_user_123",
            "email": "user@example.com",
            "name": "Test User",
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp())
        }
        
        try:
            from app.middleware.auth_middleware import FirebaseAuthMiddleware
            middleware = FirebaseAuthMiddleware()
            
            # When: 토큰 검증
            claims = middleware.verify_firebase_token(valid_token)
            
            # Then: 클레임이 올바르게 반환됨
            assert claims is not None
            assert "uid" in claims
            assert "email" in claims
            
            print("✅ 유효한 Firebase 토큰 검증 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ FirebaseAuthMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_reject_invalid_firebase_token(self):
        """유효하지 않은 Firebase 토큰 거부 테스트"""
        # Given: 유효하지 않은 토큰
        invalid_token = "invalid.token.here"
        
        try:
            from app.middleware.auth_middleware import FirebaseAuthMiddleware
            middleware = FirebaseAuthMiddleware()
            
            # When & Then: 토큰 검증 실패
            with pytest.raises(HTTPException) as exc_info:
                middleware.verify_firebase_token(invalid_token)
            
            assert exc_info.value.status_code == 401
            
            print("✅ 유효하지 않은 Firebase 토큰 거부 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ FirebaseAuthMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_handle_expired_token(self):
        """만료된 토큰 처리 테스트"""
        # Given: 만료된 토큰
        expired_token = "expired.jwt.token"
        
        try:
            from app.middleware.auth_middleware import FirebaseAuthMiddleware
            middleware = FirebaseAuthMiddleware()
            
            # When & Then: 만료된 토큰 검증 실패
            with pytest.raises(HTTPException) as exc_info:
                middleware.verify_firebase_token(expired_token)
            
            assert exc_info.value.status_code == 401
            assert "expired" in str(exc_info.value.detail).lower()
            
            print("✅ 만료된 토큰 처리 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ FirebaseAuthMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestUserAuthenticationMiddleware:
    """사용자 인증 미들웨어 테스트"""
    
    def test_authenticate_existing_user(self):
        """기존 사용자 인증 테스트"""
        # Given: Firebase 토큰과 기존 사용자
        firebase_claims = {
            "uid": "existing_user_123",
            "email": "existing@example.com",
            "name": "Existing User"
        }
        
        try:
            from app.middleware.auth_middleware import UserAuthenticationMiddleware
            middleware = UserAuthenticationMiddleware()
            
            # When: 사용자 인증
            authenticated_user = middleware.authenticate_user(firebase_claims)
            
            # Then: 기존 사용자 반환
            assert authenticated_user is not None
            assert authenticated_user.firebase_uid == firebase_claims["uid"]
            assert authenticated_user.email == firebase_claims["email"]
            
            print("✅ 기존 사용자 인증 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserAuthenticationMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_create_new_user_on_first_login(self):
        """첫 로그인 시 새 사용자 생성 테스트"""
        # Given: Firebase 토큰과 새 사용자
        firebase_claims = {
            "uid": "new_user_456",
            "email": "newuser@example.com",
            "name": "New User"
        }
        
        try:
            from app.middleware.auth_middleware import UserAuthenticationMiddleware
            middleware = UserAuthenticationMiddleware()
            
            # When: 새 사용자 인증 (자동 생성)
            authenticated_user = middleware.authenticate_user(firebase_claims)
            
            # Then: 새 사용자 생성됨
            assert authenticated_user is not None
            assert authenticated_user.firebase_uid == firebase_claims["uid"]
            assert authenticated_user.email == firebase_claims["email"]
            assert authenticated_user.display_name == firebase_claims["name"]
            assert authenticated_user.is_active is True
            
            print("✅ 첫 로그인 시 새 사용자 생성 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserAuthenticationMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_update_last_login_timestamp(self):
        """마지막 로그인 시간 업데이트 테스트"""
        # Given: 인증된 사용자
        firebase_claims = {
            "uid": "user_123",
            "email": "user@example.com",
            "name": "Test User"
        }
        
        try:
            from app.middleware.auth_middleware import UserAuthenticationMiddleware
            middleware = UserAuthenticationMiddleware()
            
            # When: 사용자 인증
            before_auth = datetime.utcnow()
            authenticated_user = middleware.authenticate_user(firebase_claims)
            after_auth = datetime.utcnow()
            
            # Then: 마지막 로그인 시간 업데이트
            assert authenticated_user.last_login_at is not None
            assert before_auth <= authenticated_user.last_login_at <= after_auth
            
            print("✅ 마지막 로그인 시간 업데이트 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ UserAuthenticationMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestAuthorizationMiddleware:
    """권한 부여 미들웨어 테스트"""
    
    def test_check_user_access_permission(self):
        """사용자 접근 권한 확인 테스트"""
        # Given: 인증된 사용자와 리소스
        user_id = "user_123"
        resource_type = "places"
        required_permission = "READ"
        
        try:
            from app.middleware.auth_middleware import AuthorizationMiddleware
            middleware = AuthorizationMiddleware()
            
            # When: 접근 권한 확인
            has_access = middleware.check_access(
                user_id=user_id,
                resource_type=resource_type,
                required_permission=required_permission
            )
            
            # Then: 접근 권한 확인됨
            assert isinstance(has_access, bool)
            
            print("✅ 사용자 접근 권한 확인 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthorizationMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_deny_insufficient_permission(self):
        """권한 부족 시 접근 거부 테스트"""
        # Given: 권한이 부족한 사용자
        user_id = "limited_user_123"
        resource_type = "admin_panel"
        required_permission = "ADMIN"
        
        try:
            from app.middleware.auth_middleware import AuthorizationMiddleware
            middleware = AuthorizationMiddleware()
            
            # When: 권한 부족한 리소스 접근
            has_access = middleware.check_access(
                user_id=user_id,
                resource_type=resource_type,
                required_permission=required_permission
            )
            
            # Then: 접근 거부됨
            assert has_access is False
            
            print("✅ 권한 부족 시 접근 거부 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthorizationMiddleware 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestAuthenticationFlow:
    """인증 플로우 통합 테스트"""
    
    async def test_full_authentication_flow(self):
        """전체 인증 플로우 테스트"""
        # Given: HTTP 요청과 Authorization 헤더
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            "authorization": "Bearer valid.firebase.token"
        }
        
        try:
            from app.middleware.auth_middleware import AuthenticationFlow
            auth_flow = AuthenticationFlow()
            
            # When: 전체 인증 플로우 실행
            authenticated_user = await auth_flow.authenticate_request(mock_request)
            
            # Then: 인증된 사용자 반환
            assert authenticated_user is not None
            assert hasattr(authenticated_user, 'firebase_uid')
            assert hasattr(authenticated_user, 'email')
            
            print("✅ 전체 인증 플로우 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticationFlow 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    async def test_authentication_with_missing_token(self):
        """토큰 누락 시 인증 실패 테스트"""
        # Given: Authorization 헤더가 없는 요청
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        
        try:
            from app.middleware.auth_middleware import AuthenticationFlow
            auth_flow = AuthenticationFlow()
            
            # When & Then: 토큰 누락으로 인증 실패
            with pytest.raises(HTTPException) as exc_info:
                await auth_flow.authenticate_request(mock_request)
            
            assert exc_info.value.status_code == 401
            
            print("✅ 토큰 누락 시 인증 실패 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ AuthenticationFlow 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


class TestSessionManagement:
    """세션 관리 테스트"""
    
    def test_create_user_session(self):
        """사용자 세션 생성 테스트"""
        # Given: 인증된 사용자
        user_id = "user_123"
        session_data = {
            "ip_address": "192.168.1.100",
            "user_agent": "Mozilla/5.0...",
            "login_time": datetime.utcnow()
        }
        
        try:
            from app.middleware.auth_middleware import SessionManager
            session_manager = SessionManager()
            
            # When: 세션 생성
            session = session_manager.create_session(user_id, session_data)
            
            # Then: 세션 생성됨
            assert session is not None
            assert session["user_id"] == user_id
            assert session["session_id"] is not None
            assert session["created_at"] is not None
            
            print("✅ 사용자 세션 생성 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ SessionManager 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_validate_active_session(self):
        """활성 세션 검증 테스트"""
        # Given: 활성 세션 ID
        session_id = "active_session_123"
        
        try:
            from app.middleware.auth_middleware import SessionManager
            session_manager = SessionManager()
            
            # When: 세션 검증
            is_valid = session_manager.validate_session(session_id)
            
            # Then: 세션 유효성 확인
            assert isinstance(is_valid, bool)
            
            print("✅ 활성 세션 검증 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ SessionManager 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False
    
    def test_invalidate_user_session(self):
        """사용자 세션 무효화 테스트"""
        # Given: 무효화할 세션
        session_id = "session_to_invalidate_123"
        
        try:
            from app.middleware.auth_middleware import SessionManager
            session_manager = SessionManager()
            
            # When: 세션 무효화
            invalidated = session_manager.invalidate_session(session_id)
            
            # Then: 세션 무효화 확인
            assert invalidated is True
            
            print("✅ 사용자 세션 무효화 테스트 통과")
            return True
            
        except ImportError:
            print("⚠️ SessionManager 구현 필요")
            return False
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            return False


def main():
    """테스트 실행"""
    print("🧪 인증 미들웨어 테스트 시작")
    print("=" * 50)
    
    # 테스트 클래스 인스턴스 생성
    test_firebase = TestFirebaseAuthMiddleware()
    test_user_auth = TestUserAuthenticationMiddleware()
    test_authorization = TestAuthorizationMiddleware()
    test_auth_flow = TestAuthenticationFlow()
    test_session = TestSessionManagement()
    
    tests = [
        # Firebase 인증 미들웨어 테스트
        test_firebase.test_verify_valid_firebase_token,
        test_firebase.test_reject_invalid_firebase_token,
        test_firebase.test_handle_expired_token,
        
        # 사용자 인증 미들웨어 테스트
        test_user_auth.test_authenticate_existing_user,
        test_user_auth.test_create_new_user_on_first_login,
        test_user_auth.test_update_last_login_timestamp,
        
        # 권한 부여 미들웨어 테스트
        test_authorization.test_check_user_access_permission,
        test_authorization.test_deny_insufficient_permission,
        
        # 세션 관리 테스트
        test_session.test_create_user_session,
        test_session.test_validate_active_session,
        test_session.test_invalidate_user_session,
    ]
    
    # 비동기 테스트들 (별도 처리)
    async_tests = [
        test_auth_flow.test_full_authentication_flow,
        test_auth_flow.test_authentication_with_missing_token,
    ]
    
    passed = 0
    failed = 0
    
    # 일반 테스트 실행
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} 실패: {e}")
            failed += 1
    
    # 비동기 테스트는 구현 후 실행 예정
    for async_test in async_tests:
        print(f"⚠️ {async_test.__name__}: 비동기 테스트 - 구현 후 실행 예정")
        failed += 1
    
    print(f"\n📊 테스트 결과:")
    print(f"   ✅ 통과: {passed}")
    print(f"   ❌ 실패: {failed}")
    print(f"   📈 전체: {passed + failed}")
    
    if failed == 0:
        print("🎉 모든 테스트 통과!")
    else:
        print(f"⚠️ {failed}개 테스트 실패 - 미들웨어 구현 필요")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)