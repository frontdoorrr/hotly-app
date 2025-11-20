"""
보안 유틸리티 및 JWT 토큰 관리

JWT 토큰 생성/검증, 패스워드 해싱 등 보안 관련 유틸리티를 제공합니다.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import logging

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# 패스워드 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 알고리즘
ALGORITHM = settings.JWT_ALGORITHM


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    JWT 액세스 토큰 생성

    Args:
        subject: 토큰 주체 (일반적으로 사용자 ID)
        expires_delta: 만료 시간 델타
        additional_claims: 추가 클레임

    Returns:
        JWT 액세스 토큰 문자열
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.ACCESS_TOKEN_EXPIRE_HOURS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT 리프레시 토큰 생성

    Args:
        subject: 토큰 주체 (일반적으로 사용자 ID)
        expires_delta: 만료 시간 델타

    Returns:
        JWT 리프레시 토큰 문자열
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰 문자열

    Returns:
        검증된 페이로드 또는 None (검증 실패 시)
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.debug("Token has expired")
        return None

    except JWTError as e:
        logger.debug(f"Invalid token: {e}")
        return None


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    액세스 토큰 전용 검증

    Args:
        token: JWT 액세스 토큰

    Returns:
        검증된 페이로드 또는 None
    """
    payload = verify_token(token)

    if payload and payload.get("type") == "access":
        return payload

    return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    리프레시 토큰 전용 검증

    Args:
        token: JWT 리프레시 토큰

    Returns:
        검증된 페이로드 또는 None
    """
    payload = verify_token(token)

    if payload and payload.get("type") == "refresh":
        return payload

    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    패스워드 검증

    Args:
        plain_password: 평문 패스워드
        hashed_password: 해싱된 패스워드

    Returns:
        검증 성공 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    패스워드 해싱

    Args:
        password: 평문 패스워드

    Returns:
        해싱된 패스워드
    """
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """
    패스워드 리셋 토큰 생성

    Args:
        email: 사용자 이메일

    Returns:
        패스워드 리셋용 JWT 토큰
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=1)

    to_encode = {
        "sub": email,
        "exp": expire,
        "type": "password_reset",
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    패스워드 리셋 토큰 검증

    Args:
        token: 패스워드 리셋 토큰

    Returns:
        이메일 주소 또는 None (검증 실패 시)
    """
    payload = verify_token(token)

    if payload and payload.get("type") == "password_reset":
        return payload.get("sub")

    return None
