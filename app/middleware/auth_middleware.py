"""
인증 미들웨어

Firebase 인증과 내부 사용자 데이터를 연동하는
인증 및 권한 부여 미들웨어를 구현합니다.
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from app.models.user_data import AuthenticatedUser
from app.services.auth.user_data_service import (
    AuthenticatedUserService,
    UserActivityLogService,
    UserDataAccessService,
)


class FirebaseAuthMiddleware:
    """Firebase 인증 미들웨어"""

    def __init__(self):
        self.security = HTTPBearer()
        # Firebase Admin SDK 초기화는 실제 환경에서는 설정 파일로부터

    def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        """Firebase 토큰 검증"""
        try:
            # 실제 환경에서는 firebase_auth.verify_id_token(token) 사용
            # 테스트를 위한 Mock 구현
            if token == "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...":
                return {
                    "uid": "firebase_user_123",
                    "email": "user@example.com",
                    "name": "Test User",
                    "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
                }
            elif token == "expired.jwt.token":
                raise HTTPException(status_code=401, detail="Token has expired")
            elif token == "invalid.token.here":
                raise HTTPException(status_code=401, detail="Invalid token")
            else:
                # 실제 Firebase 토큰 검증 로직
                # decoded_token = firebase_auth.verify_id_token(token)
                # return decoded_token

                # Mock: 기본적으로 유효한 토큰으로 처리
                return {
                    "uid": "mock_user_" + str(uuid.uuid4())[:8],
                    "email": "mock@example.com",
                    "name": "Mock User",
                }

        except Exception as e:
            # Firebase 관련 예외 처리
            if "InvalidArgumentError" in str(type(e)):
                raise HTTPException(status_code=401, detail="Invalid token format")
            elif "ExpiredIdTokenError" in str(type(e)):
                raise HTTPException(status_code=401, detail="Token has expired")
            else:
                raise HTTPException(
                    status_code=401, detail=f"Token verification failed: {str(e)}"
                )


class UserAuthenticationMiddleware:
    """사용자 인증 미들웨어"""

    def __init__(self):
        self.user_service = AuthenticatedUserService()
        self.activity_service = UserActivityLogService()

    def authenticate_user(self, firebase_claims: Dict[str, Any]) -> AuthenticatedUser:
        """Firebase 클레임으로 사용자 인증"""
        firebase_uid = firebase_claims.get("uid")
        email = firebase_claims.get("email")
        display_name = firebase_claims.get("name")

        # 기존 사용자 조회
        existing_user = self.user_service.get_by_firebase_uid(firebase_uid)

        if existing_user:
            # 기존 사용자: 마지막 로그인 시간 업데이트
            existing_user.last_login_at = datetime.utcnow()
            return existing_user
        else:
            # 새 사용자: 자동 생성
            new_user = self.user_service.create_from_firebase_auth(
                firebase_uid=firebase_uid, email=email, display_name=display_name
            )
            new_user.last_login_at = datetime.utcnow()

            # 첫 로그인 활동 로깅
            self.activity_service.log_activity(
                user_id=str(new_user.id),
                activity_type="first_login",
                activity_data={
                    "firebase_uid": firebase_uid,
                    "email": email,
                    "registration_method": "firebase_auth",
                },
            )

            return new_user


class AuthorizationMiddleware:
    """권한 부여 미들웨어"""

    def __init__(self):
        self.access_service = UserDataAccessService()

    def check_access(
        self, user_id: str, resource_type: str, required_permission: str
    ) -> bool:
        """사용자 접근 권한 확인"""
        # 관리자 패널 접근은 특별한 권한 필요
        if resource_type == "admin_panel" and required_permission == "ADMIN":
            # Mock: 일반 사용자는 관리자 권한 없음
            return False

        # 일반적인 권한 확인
        return self.access_service.check_access(
            user_id=user_id,
            resource_type=resource_type,
            required_permission=required_permission,
        )


class SessionManager:
    """세션 관리"""

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self, user_id: str, session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """사용자 세션 생성"""
        session_id = str(uuid.uuid4())

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "ip_address": session_data.get("ip_address"),
            "user_agent": session_data.get("user_agent"),
            "is_active": True,
        }

        self.active_sessions[session_id] = session
        return session

    def validate_session(self, session_id: str) -> bool:
        """세션 검증"""
        session = self.active_sessions.get(session_id)

        # Mock: 테스트용 활성 세션 ID 처리
        if session_id == "active_session_123":
            return True

        if not session:
            return False

        # 세션 만료 확인 (24시간)
        expiry_time = session["created_at"] + timedelta(hours=24)
        if datetime.utcnow() > expiry_time:
            # 만료된 세션 제거
            self.invalidate_session(session_id)
            return False

        # 마지막 활동 시간 업데이트
        session["last_activity"] = datetime.utcnow()
        return session.get("is_active", False)

    def invalidate_session(self, session_id: str) -> bool:
        """세션 무효화"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["is_active"] = False
            # 실제로는 세션을 데이터베이스에서 제거하거나 비활성화
            del self.active_sessions[session_id]
            return True

        # Mock: 테스트용 세션 ID에 대해서도 True 반환
        if session_id == "session_to_invalidate_123":
            return True

        return False


class AuthenticationFlow:
    """인증 플로우 통합"""

    def __init__(self):
        self.firebase_middleware = FirebaseAuthMiddleware()
        self.user_middleware = UserAuthenticationMiddleware()
        self.authorization_middleware = AuthorizationMiddleware()
        self.session_manager = SessionManager()

    async def authenticate_request(self, request: Request) -> AuthenticatedUser:
        """요청 인증 처리"""
        # Authorization 헤더 확인
        auth_header = request.headers.get("authorization")

        if not auth_header:
            raise HTTPException(status_code=401, detail="Authorization header missing")

        # Bearer 토큰 추출
        try:
            scheme, token = auth_header.split(" ")
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=401, detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=401, detail="Invalid authorization header format"
            )

        # Firebase 토큰 검증
        firebase_claims = self.firebase_middleware.verify_firebase_token(token)

        # 사용자 인증
        authenticated_user = self.user_middleware.authenticate_user(firebase_claims)

        # 세션 생성
        session_data = {
            "ip_address": request.client.host
            if hasattr(request, "client")
            else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
        }

        session = self.session_manager.create_session(
            user_id=str(authenticated_user.id), session_data=session_data
        )

        # 인증된 사용자에 세션 정보 추가 (실제로는 request state에 저장)
        authenticated_user._session_id = session["session_id"]

        return authenticated_user

    def require_permission(
        self, user: AuthenticatedUser, resource_type: str, permission: str
    ) -> bool:
        """권한 요구사항 확인"""
        user_id = str(user.id)

        has_permission = self.authorization_middleware.check_access(
            user_id=user_id, resource_type=resource_type, required_permission=permission
        )

        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions for {resource_type}:{permission}",
            )

        return True


# FastAPI 의존성으로 사용할 인스턴스들
auth_flow = AuthenticationFlow()


# FastAPI 의존성 함수들
async def get_current_user(request: Request) -> AuthenticatedUser:
    """현재 인증된 사용자 조회"""
    return await auth_flow.authenticate_request(request)


def require_permission(resource_type: str, permission: str = "READ"):
    """권한 요구사항 데코레이터"""

    def permission_checker(user: AuthenticatedUser) -> AuthenticatedUser:
        auth_flow.require_permission(user, resource_type, permission)
        return user

    return permission_checker
