"""Authentication endpoints."""
import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)

from app.middleware.jwt_middleware import get_admin_user, get_current_active_user
from app.schemas.auth import (
    AnonymousUserRequest,
    LoginResponse,
    LogoutResponse,
    SignInRequest,
    SignUpRequest,
    SocialLoginRequest,
    SocialProvider,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserUpgradeRequest,
)
from app.services.auth.firebase_auth_service import firebase_auth_service

router = APIRouter()

# Use Firebase auth service
auth_service = firebase_auth_service


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def sign_up(sign_up_data: SignUpRequest) -> Dict[str, Any]:
    """
    회원가입 (Firebase 이메일/비밀번호).

    Note: Firebase에서는 이메일/비밀번호 회원가입이 Firebase Console에서 활성화되어야 합니다.
    현재는 소셜 로그인을 권장합니다.

    Args:
        sign_up_data: 회원가입 요청 데이터

    Returns:
        로그인 응답 (사용자 정보 및 토큰)

    Raises:
        HTTPException: 회원가입 실패 시
    """
    # Firebase는 클라이언트 SDK에서 직접 회원가입을 처리하는 것을 권장
    # 백엔드에서는 소셜 로그인 또는 토큰 검증만 수행
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Please use Firebase client SDK for email/password signup, or use social login endpoints",
    )


@router.post("/signin")
async def sign_in(sign_in_data: SignInRequest) -> Dict[str, Any]:
    """
    로그인 (Firebase 이메일/비밀번호).

    Note: Firebase에서는 클라이언트 SDK에서 직접 로그인을 처리하는 것을 권장합니다.
    백엔드로 전달받은 ID 토큰을 검증하려면 /verify-token 엔드포인트를 사용하세요.

    Args:
        sign_in_data: 로그인 요청 데이터

    Returns:
        로그인 응답 (사용자 정보 및 토큰)

    Raises:
        HTTPException: 로그인 실패 시
    """
    # Firebase는 클라이언트 SDK에서 직접 로그인을 처리하는 것을 권장
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Please use Firebase client SDK for email/password login, or use social login endpoints",
    )


@router.post("/signout", response_model=LogoutResponse)
async def sign_out(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> LogoutResponse:
    """
    로그아웃.

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        로그아웃 응답

    Raises:
        HTTPException: 로그아웃 실패 시
    """
    try:
        user_id = current_user.get("uid") or current_user.get("user_id")
        await auth_service.terminate_user_session(user_id)

        return LogoutResponse(
            success=True, message="Successfully signed out", sessions_terminated=1
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sign out failed: {str(e)}",
        )


@router.post("/social-login", response_model=LoginResponse)
async def social_login(login_request: SocialLoginRequest) -> LoginResponse:
    """
    소셜 로그인 (Google, Apple, Kakao).

    클라이언트에서 소셜 로그인 후 받은 ID 토큰 또는 액세스 토큰을 검증하고
    Firebase 커스텀 토큰을 생성합니다.

    Args:
        login_request: 소셜 로그인 요청 (provider, idToken/accessToken)

    Returns:
        로그인 응답 (사용자 정보 및 Firebase 토큰)

    Raises:
        HTTPException: 소셜 로그인 실패 시
    """
    try:
        result = await auth_service.login_with_social(login_request)
        return result
    except Exception as e:
        logger.error(f"Social login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Social login failed: {str(e)}",
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(refresh_data: TokenRefreshRequest) -> TokenRefreshResponse:
    """
    토큰 갱신.

    Firebase refresh token을 사용하여 새로운 ID 토큰을 발급받습니다.

    Args:
        refresh_data: 리프레시 토큰 요청 데이터

    Returns:
        새로운 액세스 토큰 및 리프레시 토큰

    Raises:
        HTTPException: 토큰 갱신 실패 시
    """
    try:
        result = await auth_service.refresh_tokens(refresh_data)
        return result
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.post("/verify-token")
async def verify_token(token: str) -> Dict[str, Any]:
    """
    Firebase ID 토큰 검증.

    클라이언트에서 Firebase Authentication으로 로그인한 후 받은 ID 토큰을 검증합니다.

    Args:
        token: Firebase ID 토큰

    Returns:
        토큰 검증 결과 및 사용자 정보

    Raises:
        HTTPException: 토큰 검증 실패 시
    """
    try:
        result = await auth_service.validate_access_token(token)
        return {
            "valid": result.is_valid,
            "user_id": result.user_id,
            "email": result.email,
            "permissions": result.permissions,
        }
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보 조회.

    Args:
        current_user: 현재 인증된 사용자 정보

    Returns:
        사용자 정보
    """
    return current_user


@router.post("/anonymous", response_model=LoginResponse)
async def create_anonymous_user(
    anonymous_data: AnonymousUserRequest,
) -> LoginResponse:
    """
    익명 사용자 생성 (게스트 모드).

    Firebase Anonymous Authentication을 사용하여 임시 사용자를 생성합니다.

    Args:
        anonymous_data: 익명 사용자 요청 데이터

    Returns:
        익명 사용자 로그인 응답

    Raises:
        HTTPException: 익명 사용자 생성 실패 시
    """
    try:
        result = await auth_service.create_anonymous_user(anonymous_data)
        return result
    except Exception as e:
        logger.error(f"Anonymous user creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Anonymous user creation failed: {str(e)}",
        )


@router.post("/upgrade", response_model=LoginResponse)
async def upgrade_anonymous_user(
    upgrade_data: UserUpgradeRequest,
) -> LoginResponse:
    """
    익명 사용자를 인증된 사용자로 업그레이드.

    게스트 모드로 사용하던 익명 사용자를 소셜 로그인으로 업그레이드합니다.
    기존 데이터는 유지됩니다.

    Args:
        upgrade_data: 사용자 업그레이드 요청 데이터

    Returns:
        업그레이드된 사용자 로그인 응답

    Raises:
        HTTPException: 업그레이드 실패 시
    """
    try:
        result = await auth_service.upgrade_anonymous_user(upgrade_data)
        return result
    except Exception as e:
        logger.error(f"User upgrade failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User upgrade failed: {str(e)}",
        )


@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    사용자 프로필 업데이트.

    Firebase Authentication의 사용자 메타데이터를 업데이트합니다.

    Args:
        profile_data: 업데이트할 프로필 데이터
        current_user: 현재 인증된 사용자 정보

    Returns:
        업데이트된 사용자 정보

    Raises:
        HTTPException: 업데이트 실패 시
    """
    try:
        # Firebase Auth에서는 클라이언트 SDK를 통한 프로필 업데이트를 권장
        # 백엔드에서는 커스텀 클레임만 업데이트
        user_id = current_user.get("uid") or current_user.get("user_id")

        # Note: Firebase Admin SDK를 사용하여 사용자 정보 업데이트
        # auth.update_user(uid, display_name=..., photo_url=...)
        # 현재는 클라이언트 SDK 사용을 권장

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Please use Firebase client SDK to update user profile (display name, photo, etc.)",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile update failed: {str(e)}",
        )


@router.get("/admin/users", response_model=Dict[str, Any])
async def list_all_users(
    admin_user: Dict[str, Any] = Depends(get_admin_user),
) -> Dict[str, Any]:
    """
    모든 사용자 목록 조회 (관리자 전용).

    Args:
        admin_user: 관리자 사용자 정보

    Returns:
        사용자 목록

    Raises:
        HTTPException: 조회 실패 시 또는 권한 없음
    """
    # TODO: Implement admin user list functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin user list not yet implemented",
    )
