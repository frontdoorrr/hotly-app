"""JWT 검증 미들웨어."""
import logging
from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.services.auth.firebase_auth_service import firebase_auth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Firebase ID 토큰 검증.

    Args:
        token: Firebase ID 토큰

    Returns:
        검증된 사용자 정보

    Raises:
        HTTPException: 토큰이 유효하지 않을 경우
    """
    try:
        validation_result = await firebase_auth_service.validate_access_token(token)

        if not validation_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "uid": validation_result.user_id,
            "email": validation_result.email,
            "permissions": validation_result.permissions,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보 조회 (Firebase Authentication).

    Args:
        credentials: HTTP Authorization 헤더의 Bearer 토큰

    Returns:
        사용자 정보

    Raises:
        HTTPException: 인증 실패 시
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    token = credentials.credentials

    try:
        # Firebase ID 토큰 검증
        user_info = await verify_firebase_token(token)
        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    현재 활성 사용자 조회 (비활성화된 사용자 차단).

    Args:
        current_user: 현재 사용자 정보

    Returns:
        활성 사용자 정보

    Raises:
        HTTPException: 사용자가 비활성화된 경우
    """
    # Firebase에서 사용자 상태 확인 (custom claims 사용)
    permissions = current_user.get("permissions", {})
    if permissions.get("disabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    return current_user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    관리자 사용자 조회 (관리자 권한 필요).

    Args:
        current_user: 현재 사용자 정보

    Returns:
        관리자 사용자 정보

    Raises:
        HTTPException: 관리자 권한이 없는 경우
    """
    # Firebase custom claims에서 role 확인
    permissions = current_user.get("permissions", {})
    user_role = permissions.get("role")

    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user
