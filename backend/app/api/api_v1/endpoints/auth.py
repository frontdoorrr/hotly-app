"""Authentication endpoints."""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.supabase_config import supabase_client
from app.middleware.jwt_middleware import get_admin_user, get_current_active_user
from app.schemas.auth import (
    AnonymousUserRequest,
    LoginResponse,
    LogoutResponse,
    SignInRequest,
    SignUpRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserUpgradeRequest,
)
from app.services.auth.supabase_auth_service import SupabaseAuthService

router = APIRouter()

# Initialize auth service
auth_service = SupabaseAuthService(supabase_client)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def sign_up(sign_up_data: SignUpRequest) -> Dict[str, Any]:
    """
    회원가입.

    Args:
        sign_up_data: 회원가입 요청 데이터

    Returns:
        로그인 응답 (사용자 정보 및 토큰)

    Raises:
        HTTPException: 회원가입 실패 시
    """
    try:
        result = await auth_service.sign_up(sign_up_data)

        return {
            "success": True,
            "user_profile": result.get("user"),
            "access_token": result.get("session", {}).get("access_token"),
            "refresh_token": result.get("session", {}).get("refresh_token"),
            "is_new_user": True,
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sign up failed: {str(e)}",
        )


@router.post("/signin")
async def sign_in(sign_in_data: SignInRequest) -> Dict[str, Any]:
    """
    로그인.

    Args:
        sign_in_data: 로그인 요청 데이터

    Returns:
        로그인 응답 (사용자 정보 및 토큰)

    Raises:
        HTTPException: 로그인 실패 시
    """
    try:
        result = await auth_service.sign_in(sign_in_data)

        return {
            "success": True,
            "user_profile": result.get("user"),
            "access_token": result.get("session", {}).get("access_token"),
            "refresh_token": result.get("session", {}).get("refresh_token"),
            "is_new_user": False,
            "expires_in": 3600,
            "token_type": "Bearer",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sign in failed: {str(e)}",
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
        await auth_service.sign_out()

        return LogoutResponse(
            success=True, message="Successfully signed out", sessions_terminated=1
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sign out failed: {str(e)}",
        )


@router.post("/oauth/{provider}", response_model=Dict[str, str])
async def oauth_sign_in(provider: str) -> Dict[str, str]:
    """
    OAuth 소셜 로그인.

    Args:
        provider: OAuth 제공자 (google, apple, kakao)

    Returns:
        OAuth 인증 URL

    Raises:
        HTTPException: OAuth 로그인 실패 시
    """
    if provider not in ["google", "apple", "kakao"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    try:
        result = await auth_service.sign_in_with_oauth(provider)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth sign in failed: {str(e)}",
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(refresh_data: TokenRefreshRequest) -> TokenRefreshResponse:
    """
    토큰 갱신.

    Args:
        refresh_data: 리프레시 토큰 요청 데이터

    Returns:
        새로운 액세스 토큰 및 리프레시 토큰

    Raises:
        HTTPException: 토큰 갱신 실패 시
    """
    try:
        result = await auth_service.refresh_session()

        return TokenRefreshResponse(
            success=True,
            new_access_token=result.get("session", {}).get("access_token"),
            new_refresh_token=result.get("session", {}).get("refresh_token"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}",
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
    익명 사용자 생성.

    Args:
        anonymous_data: 익명 사용자 요청 데이터

    Returns:
        익명 사용자 로그인 응답

    Raises:
        HTTPException: 익명 사용자 생성 실패 시
    """
    # TODO: Implement anonymous user creation logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Anonymous user creation not yet implemented",
    )


@router.post("/upgrade", response_model=LoginResponse)
async def upgrade_anonymous_user(
    upgrade_data: UserUpgradeRequest,
) -> LoginResponse:
    """
    익명 사용자를 인증된 사용자로 업그레이드.

    Args:
        upgrade_data: 사용자 업그레이드 요청 데이터

    Returns:
        업그레이드된 사용자 로그인 응답

    Raises:
        HTTPException: 업그레이드 실패 시
    """
    # TODO: Implement anonymous to authenticated user upgrade logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="User upgrade not yet implemented",
    )


@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    사용자 프로필 업데이트.

    Args:
        profile_data: 업데이트할 프로필 데이터
        current_user: 현재 인증된 사용자 정보

    Returns:
        업데이트된 사용자 정보

    Raises:
        HTTPException: 업데이트 실패 시
    """
    try:
        result = await auth_service.update_user(
            user_id=current_user["id"], user_metadata=profile_data
        )
        return result
    except Exception as e:
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
