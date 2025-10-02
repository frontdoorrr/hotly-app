"""JWT 검증 미들웨어."""
from typing import Any, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.supabase_config import settings, supabase_client

security = HTTPBearer()


async def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    JWT 토큰 검증.

    Args:
        token: JWT 토큰

    Returns:
        JWT 페이로드

    Raises:
        HTTPException: 토큰이 유효하지 않을 경우
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_signature": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보 조회.

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
        # Supabase에서 사용자 정보 조회
        response = supabase_client.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        # 사용자 정보를 딕셔너리로 변환
        user_dict = {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata or {},
            "app_metadata": response.user.app_metadata or {},
            "created_at": response.user.created_at,
            "email_confirmed_at": response.user.email_confirmed_at,
        }

        return user_dict

    except HTTPException:
        raise
    except Exception as e:
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
    # 사용자 상태 확인 (필요시 추가 검증)
    if current_user.get("app_metadata", {}).get("disabled"):
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
    user_role = current_user.get("app_metadata", {}).get("role")

    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    return current_user
