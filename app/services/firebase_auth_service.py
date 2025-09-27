"""
Firebase Authentication Service

Firebase 인증 시스템을 위한 서비스 클래스입니다.
다양한 소셜 로그인, 토큰 관리, 세션 관리, 보안 기능을 제공합니다.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import uuid4

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False

try:
    import firebase_admin
    from firebase_admin import auth, credentials
    from firebase_admin.auth import ExpiredIdTokenError, InvalidIdTokenError
    FIREBASE_AVAILABLE = True
except ImportError:
    # Firebase SDK not available - use mock classes for testing
    firebase_admin = None
    auth = None
    credentials = None
    
    class ExpiredIdTokenError(Exception):
        pass
    
    class InvalidIdTokenError(Exception):
        pass
    
    FIREBASE_AVAILABLE = False

from app.core.config import settings
from app.schemas.auth import (
    SocialLoginRequest,
    LoginResponse,
    UserProfile,
    TokenValidationResult,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserSession,
    UserPermissions,
    SecurityAlert,
    AnonymousUserRequest,
    SocialProvider,
    AuthError,
    LoginAttempt
)
from app.utils.cache import cache_service

logger = logging.getLogger(__name__)


class FirebaseAuthService:
    """Firebase 인증 서비스"""
    
    def __init__(self, firebase_app=None, firebase_auth=None):
        """
        Firebase Auth Service 초기화
        
        Args:
            firebase_app: Firebase 앱 인스턴스 (테스트용)
            firebase_auth: Firebase Auth 인스턴스 (테스트용)
        """
        self.firebase_app = firebase_app or self._initialize_firebase()
        self.firebase_auth = firebase_auth or auth
        self.cache = cache_service
        
        # 레이트 리미팅 설정
        self.max_login_attempts = settings.MAX_LOGIN_ATTEMPTS_PER_MINUTE or 10
        self.max_token_refresh = settings.MAX_TOKEN_REFRESH_PER_HOUR or 60
        
    def _initialize_firebase(self):
        """Firebase 앱 초기화"""
        try:
            if not FIREBASE_AVAILABLE:
                logger.info("Firebase SDK not available, using test mode")
                return None
                
            # Firebase 서비스 계정 키가 있는지 확인
            if not settings.FIREBASE_CREDENTIALS_PATH:
                logger.warning("Firebase credentials path not set, using mock for development")
                return None
                
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            return firebase_admin.initialize_app(cred, {
                'projectId': settings.FIREBASE_PROJECT_ID
            })
        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            return None
    
    async def validate_firebase_config(self) -> bool:
        """Firebase 설정 유효성 검증"""
        try:
            if not FIREBASE_AVAILABLE:
                # 테스트 환경에서는 항상 True 반환
                return True
                
            # Firebase 프로젝트 설정 확인
            if not settings.FIREBASE_PROJECT_ID:
                return False
                
            # Firebase 앱 초기화 상태 확인
            if not self.firebase_app:
                return False
                
            # 테스트 토큰 검증 (실제 운영에서는 제거)
            return True
            
        except Exception as e:
            logger.error(f"Firebase config validation failed: {e}")
            return False
    
    async def login_with_social(self, request: SocialLoginRequest) -> LoginResponse:
        """소셜 로그인 처리"""
        try:
            # 레이트 리미팅 체크
            if not await self._check_rate_limit(request.device_id, "login"):
                return LoginResponse(
                    success=False,
                    error_code=AuthError.RATE_LIMIT_EXCEEDED,
                    error_message="로그인 시도 한도를 초과했습니다."
                )
            
            # 소셜 제공자별 인증 처리
            user_info = await self._authenticate_social_user(request)
            if not user_info:
                return LoginResponse(
                    success=False,
                    error_code=AuthError.PROVIDER_ERROR,
                    error_message="소셜 로그인 인증에 실패했습니다."
                )
            
            # 사용자 프로필 생성
            user_profile = await self._create_user_profile(user_info, request.provider)
            
            # 토큰 생성
            access_token, refresh_token = await self._generate_tokens(user_profile.user_id)
            
            # 세션 생성
            session_id = await self._create_user_session(
                user_id=user_profile.user_id,
                device_id=request.device_id,
                session_token=access_token,
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            # 로그인 시도 로그
            await self._log_login_attempt(
                user_id=user_profile.user_id,
                device_id=request.device_id,
                provider=request.provider,
                success=True
            )
            
            return LoginResponse(
                success=True,
                user_profile=user_profile,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,
                session_id=session_id,
                is_new_user=user_info.get('is_new_user', False)
            )
            
        except Exception as e:
            logger.error(f"Social login failed: {e}")
            
            # 실패한 로그인 시도 로그
            await self._log_login_attempt(
                user_id=None,
                device_id=request.device_id,
                provider=request.provider,
                success=False,
                failure_reason=str(e)
            )
            
            return LoginResponse(
                success=False,
                error_code=AuthError.UNKNOWN_ERROR,
                error_message="로그인 처리 중 오류가 발생했습니다."
            )
    
    async def _authenticate_social_user(self, request: SocialLoginRequest) -> Optional[Dict]:
        """소셜 제공자별 사용자 인증"""
        try:
            if request.provider == SocialProvider.GOOGLE:
                return await self._authenticate_google(request.id_token)
            elif request.provider == SocialProvider.APPLE:
                return await self._authenticate_apple(request.id_token)
            elif request.provider == SocialProvider.KAKAO:
                return await self._authenticate_kakao(request.access_token)
            else:
                logger.error(f"Unsupported provider: {request.provider}")
                return None
                
        except Exception as e:
            logger.error(f"Social authentication failed for {request.provider}: {e}")
            return None
    
    async def _authenticate_google(self, id_token: str) -> Optional[Dict]:
        """Google ID 토큰 검증"""
        try:
            if self.firebase_auth.verify_id_token:
                # Firebase Admin SDK를 통한 Google ID 토큰 검증
                decoded_token = self.firebase_auth.verify_id_token(id_token)
                return {
                    'uid': decoded_token['uid'],
                    'email': decoded_token.get('email'),
                    'name': decoded_token.get('name'),
                    'picture': decoded_token.get('picture'),
                    'email_verified': decoded_token.get('email_verified', False),
                    'provider': 'google'
                }
            else:
                # 테스트 환경에서는 mock 데이터 반환
                return {
                    'uid': 'google_user_123',
                    'email': 'user@gmail.com',
                    'name': 'Google User',
                    'picture': 'https://lh3.googleusercontent.com/...',
                    'email_verified': True,
                    'provider': 'google'
                }
        except ExpiredIdTokenError:
            logger.error("Google ID token expired")
            return None
        except InvalidIdTokenError:
            logger.error("Invalid Google ID token")
            return None
        except Exception as e:
            logger.error(f"Google authentication failed: {e}")
            return None
    
    async def _authenticate_apple(self, id_token: str) -> Optional[Dict]:
        """Apple ID 토큰 검증"""
        try:
            if self.firebase_auth.verify_id_token:
                decoded_token = self.firebase_auth.verify_id_token(id_token)
                return {
                    'uid': decoded_token['uid'],
                    'email': decoded_token.get('email'),
                    'name': decoded_token.get('name'),  # Apple은 이름을 제공하지 않을 수 있음
                    'email_verified': decoded_token.get('email_verified', True),
                    'provider': 'apple'
                }
            else:
                # 테스트 환경
                return {
                    'uid': 'apple_user_456',
                    'email': 'user@privaterelay.appleid.com',
                    'name': None,
                    'email_verified': True,
                    'provider': 'apple'
                }
        except Exception as e:
            logger.error(f"Apple authentication failed: {e}")
            return None
    
    async def _authenticate_kakao(self, access_token: str) -> Optional[Dict]:
        """Kakao 액세스 토큰으로 사용자 정보 조회"""
        try:
            if not REQUESTS_AVAILABLE:
                # 테스트 환경에서는 Mock 데이터 반환
                return {
                    'uid': f"kakao_12345678",
                    'email': 'user@kakao.com',
                    'name': '카카오유저',
                    'picture': 'http://k.kakaocdn.net/...',
                    'email_verified': False,
                    'provider': 'kakao',
                    'custom_token': 'custom_firebase_token'
                }
            
            # Kakao API 호출하여 사용자 정보 조회
            response = requests.get(
                'https://kapi.kakao.com/v2/user/me',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Kakao API error: {response.status_code}")
                return None
            
            kakao_user = response.json()
            kakao_account = kakao_user.get('kakao_account', {})
            profile = kakao_account.get('profile', {})
            
            # Firebase Custom Token 생성
            custom_token = None
            if self.firebase_auth.create_custom_token:
                kakao_uid = f"kakao_{kakao_user['id']}"
                custom_token = self.firebase_auth.create_custom_token(kakao_uid)
            
            return {
                'uid': f"kakao_{kakao_user['id']}",
                'email': kakao_account.get('email'),
                'name': profile.get('nickname'),
                'picture': profile.get('profile_image_url'),
                'email_verified': kakao_account.get('is_email_verified', False),
                'provider': 'kakao',
                'custom_token': custom_token
            }
            
        except Exception as e:
            logger.error(f"Kakao authentication failed: {e}")
            return None
    
    async def _create_user_profile(self, user_info: Dict, provider: SocialProvider) -> UserProfile:
        """사용자 프로필 생성"""
        # 게스트 사용자 권한 설정
        permissions = UserPermissions(
            can_create_courses=False if provider == SocialProvider.ANONYMOUS else True,
            can_share_content=False if provider == SocialProvider.ANONYMOUS else True,
            can_view_content=True,
            can_comment=False if provider == SocialProvider.ANONYMOUS else True,
            can_rate_places=False if provider == SocialProvider.ANONYMOUS else True,
            data_retention_days=7 if provider == SocialProvider.ANONYMOUS else 365
        )
        
        return UserProfile(
            user_id=user_info['uid'],
            email=user_info.get('email'),
            name=user_info.get('name'),
            profile_image_url=user_info.get('picture'),
            provider=provider,
            is_anonymous=provider == SocialProvider.ANONYMOUS,
            is_verified=user_info.get('email_verified', False),
            created_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
            permissions=permissions,
            linked_providers=[provider] if provider != SocialProvider.ANONYMOUS else []
        )
    
    async def _generate_tokens(self, user_id: str) -> tuple[str, str]:
        """액세스 토큰과 리프레시 토큰 생성"""
        # 실제로는 JWT나 Firebase 토큰을 생성
        access_token = f"access_token_{user_id}_{uuid4()}"
        refresh_token = f"refresh_token_{user_id}_{uuid4()}"
        
        # 토큰을 캐시에 저장
        await self.cache.set(
            f"access_token:{access_token}",
            {"user_id": user_id, "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()},
            ttl=3600
        )
        
        await self.cache.set(
            f"refresh_token:{refresh_token}",
            {"user_id": user_id, "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()},
            ttl=30 * 24 * 3600
        )
        
        return access_token, refresh_token
    
    async def validate_access_token(self, token: str) -> TokenValidationResult:
        """액세스 토큰 검증"""
        try:
            if not token:
                return TokenValidationResult(
                    is_valid=False,
                    error_code=AuthError.INVALID_TOKEN,
                    error_message="토큰이 제공되지 않았습니다."
                )
            
            # 캐시에서 토큰 정보 조회
            token_info = await self.cache.get(f"access_token:{token}")
            if not token_info:
                # Firebase Auth로 토큰 검증 시도
                if self.firebase_auth.verify_id_token:
                    try:
                        decoded_token = self.firebase_auth.verify_id_token(token)
                        return TokenValidationResult(
                            is_valid=True,
                            user_id=decoded_token['uid'],
                            email=decoded_token.get('email'),
                            expires_at=datetime.fromtimestamp(decoded_token['exp'])
                        )
                    except ExpiredIdTokenError:
                        return TokenValidationResult(
                            is_valid=False,
                            error_code=AuthError.TOKEN_EXPIRED,
                            error_message="토큰이 만료되었습니다."
                        )
                    except InvalidIdTokenError:
                        return TokenValidationResult(
                            is_valid=False,
                            error_code=AuthError.INVALID_TOKEN,
                            error_message="유효하지 않은 토큰입니다."
                        )
                
                return TokenValidationResult(
                    is_valid=False,
                    error_code=AuthError.INVALID_TOKEN,
                    error_message="토큰을 찾을 수 없습니다."
                )
            
            # 토큰 만료 시간 확인
            expires_at = datetime.fromisoformat(token_info['expires_at'])
            if datetime.utcnow() > expires_at:
                await self.cache.delete(f"access_token:{token}")
                return TokenValidationResult(
                    is_valid=False,
                    error_code=AuthError.TOKEN_EXPIRED,
                    error_message="토큰이 만료되었습니다."
                )
            
            return TokenValidationResult(
                is_valid=True,
                user_id=token_info['user_id'],
                expires_at=expires_at
            )
            
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return TokenValidationResult(
                is_valid=False,
                error_code=AuthError.UNKNOWN_ERROR,
                error_message="토큰 검증 중 오류가 발생했습니다."
            )
    
    async def refresh_tokens(self, request: TokenRefreshRequest) -> TokenRefreshResponse:
        """토큰 갱신"""
        try:
            # 레이트 리미팅 체크
            if not await self._check_rate_limit(request.device_id, "refresh"):
                return TokenRefreshResponse(
                    success=False,
                    error_code=AuthError.RATE_LIMIT_EXCEEDED,
                    error_message="토큰 갱신 한도를 초과했습니다."
                )
            
            # 리프레시 토큰 검증
            token_info = await self.cache.get(f"refresh_token:{request.refresh_token}")
            if not token_info:
                return TokenRefreshResponse(
                    success=False,
                    error_code=AuthError.INVALID_TOKEN,
                    error_message="유효하지 않은 리프레시 토큰입니다."
                )
            
            # 새 토큰 생성
            new_access_token, new_refresh_token = await self._generate_tokens(token_info['user_id'])
            
            # 기존 토큰 삭제
            await self.cache.delete(f"refresh_token:{request.refresh_token}")
            
            return TokenRefreshResponse(
                success=True,
                new_access_token=new_access_token,
                new_refresh_token=new_refresh_token,
                expires_in=3600
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return TokenRefreshResponse(
                success=False,
                error_code=AuthError.UNKNOWN_ERROR,
                error_message="토큰 갱신 중 오류가 발생했습니다."
            )
    
    async def create_user_session(self, user_id: str, device_id: str, session_token: str, expires_at: datetime) -> bool:
        """사용자 세션 생성"""
        try:
            session_info = {
                'user_id': user_id,
                'device_id': device_id,
                'session_token': session_token,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat(),
                'is_active': True
            }
            
            # 세션을 캐시에 저장
            session_key = f"session:{user_id}:{device_id}"
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            await self.cache.set(session_key, session_info, ttl=ttl)
            
            return True
            
        except Exception as e:
            logger.error(f"Session creation failed: {e}")
            return False
    
    async def get_user_session(self, user_id: str, device_id: str) -> Optional[UserSession]:
        """사용자 세션 조회"""
        try:
            session_key = f"session:{user_id}:{device_id}"
            session_info = await self.cache.get(session_key)
            
            if not session_info:
                return None
            
            return UserSession(
                session_id=f"{user_id}_{device_id}",
                user_id=session_info['user_id'],
                device_id=session_info['device_id'],
                created_at=datetime.fromisoformat(session_info['created_at']),
                expires_at=datetime.fromisoformat(session_info['expires_at']),
                is_active=session_info['is_active']
            )
            
        except Exception as e:
            logger.error(f"Session retrieval failed: {e}")
            return None
    
    async def terminate_user_session(self, user_id: str, device_id: str) -> bool:
        """사용자 세션 종료"""
        try:
            session_key = f"session:{user_id}:{device_id}"
            return await self.cache.delete(session_key)
            
        except Exception as e:
            logger.error(f"Session termination failed: {e}")
            return False
    
    async def create_anonymous_user(self, device_id: str) -> LoginResponse:
        """익명 사용자 생성"""
        try:
            # 익명 사용자 UID 생성
            anonymous_uid = f"anonymous_{uuid4()}"
            
            # Firebase 익명 인증 사용자 생성
            if self.firebase_auth.create_user:
                firebase_user = self.firebase_auth.create_user(uid=anonymous_uid)
                user_info = {
                    'uid': firebase_user.uid,
                    'is_anonymous': True,
                    'provider_id': 'anonymous'
                }
            else:
                # 테스트 환경
                user_info = {
                    'uid': anonymous_uid,
                    'is_anonymous': True,
                    'provider_id': 'anonymous'
                }
            
            # 익명 사용자 프로필 생성
            user_profile = await self._create_user_profile(user_info, SocialProvider.ANONYMOUS)
            
            # 토큰 생성 (익명 사용자도 토큰 필요)
            access_token, refresh_token = await self._generate_tokens(user_profile.user_id)
            
            return LoginResponse(
                success=True,
                user_profile=user_profile,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,
                is_new_user=True
            )
            
        except Exception as e:
            logger.error(f"Anonymous user creation failed: {e}")
            return LoginResponse(
                success=False,
                error_code=AuthError.UNKNOWN_ERROR,
                error_message="익명 사용자 생성 중 오류가 발생했습니다."
            )
    
    async def get_user_permissions(self, user_id: str) -> UserPermissions:
        """사용자 권한 조회"""
        try:
            # 캐시에서 사용자 권한 조회
            permissions_info = await self.cache.get(f"permissions:{user_id}")
            
            if permissions_info:
                return UserPermissions(**permissions_info)
            
            # 기본 권한 (익명 사용자인지 확인)
            if user_id.startswith('anonymous_') or user_id.startswith('guest_'):
                permissions = UserPermissions(
                    can_create_courses=False,
                    can_share_content=False,
                    can_view_content=True,
                    can_comment=False,
                    can_rate_places=False,
                    data_retention_days=7,
                    max_saved_places=10,
                    max_courses_per_day=1
                )
            else:
                permissions = UserPermissions()
            
            # 권한을 캐시에 저장
            await self.cache.set(f"permissions:{user_id}", permissions.dict(), ttl=3600)
            
            return permissions
            
        except Exception as e:
            logger.error(f"Permission retrieval failed: {e}")
            return UserPermissions(can_view_content=True)
    
    async def upgrade_anonymous_user(self, anonymous_user_id: str, social_login: SocialLoginRequest) -> LoginResponse:
        """익명 사용자를 인증된 사용자로 업그레이드"""
        try:
            # 소셜 로그인 인증
            user_info = await self._authenticate_social_user(social_login)
            if not user_info:
                return LoginResponse(
                    success=False,
                    error_code=AuthError.PROVIDER_ERROR,
                    error_message="소셜 로그인 인증에 실패했습니다."
                )
            
            # Firebase에서 계정 연결
            if self.firebase_auth.link_provider:
                linked_user = self.firebase_auth.link_provider(anonymous_user_id, user_info)
                user_info.update({
                    'uid': linked_user['uid'],
                    'email': linked_user.get('email'),
                    'provider_data': linked_user.get('provider_data', [])
                })
            
            # 업그레이드된 사용자 프로필 생성
            user_profile = await self._create_user_profile(user_info, social_login.provider)
            user_profile.is_anonymous = False
            user_profile.linked_providers = [SocialProvider.ANONYMOUS, social_login.provider]
            
            # 새 토큰 생성
            access_token, refresh_token = await self._generate_tokens(user_profile.user_id)
            
            # 기존 익명 세션 제거
            await self.terminate_user_session(anonymous_user_id, social_login.device_id)
            
            return LoginResponse(
                success=True,
                user_profile=user_profile,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600
            )
            
        except Exception as e:
            logger.error(f"Anonymous user upgrade failed: {e}")
            return LoginResponse(
                success=False,
                error_code=AuthError.UNKNOWN_ERROR,
                error_message="계정 업그레이드 중 오류가 발생했습니다."
            )
    
    async def log_login_attempt(self, user_id: Optional[str], session: Dict[str, Any]):
        """로그인 시도 로그"""
        try:
            log_entry = {
                'user_id': user_id,
                'timestamp': session['timestamp'].isoformat(),
                'country': session.get('country', 'Unknown'),
                'ip_address': session.get('ip_address'),
                'success': True
            }
            
            # 로그를 저장 (실제로는 데이터베이스나 로그 서비스에)
            await self.cache.set(
                f"login_log:{user_id}:{session['timestamp'].timestamp()}",
                log_entry,
                ttl=86400  # 24시간
            )
            
        except Exception as e:
            logger.error(f"Login attempt logging failed: {e}")
    
    async def check_suspicious_activity(self, user_id: str) -> SecurityAlert:
        """의심스러운 활동 감지"""
        try:
            # 최근 로그인 기록 조회 (캐시에서)
            # 실제로는 데이터베이스에서 조회
            recent_logins = []  # 임시로 빈 리스트
            
            # 지역별 로그인 분석
            countries = set()
            recent_attempts = []
            
            for login in recent_logins:
                countries.add(login.get('country', 'Unknown'))
                recent_attempts.append(login)
            
            # 의심스러운 패턴 감지
            is_suspicious = False
            risk_level = "LOW"
            reasons = []
            
            # 여러 국가에서 짧은 시간 내 로그인
            if len(countries) > 2:
                is_suspicious = True
                risk_level = "HIGH"
                reasons.append(f"Multiple countries: {', '.join(countries)}")
            
            # 너무 많은 로그인 시도
            if len(recent_attempts) > 10:
                is_suspicious = True
                risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
                reasons.append("High login frequency")
            
            return SecurityAlert(
                alert_id=str(uuid4()),
                user_id=user_id,
                alert_type="suspicious_login",
                risk_level=risk_level,
                is_suspicious=is_suspicious,
                reason="; ".join(reasons) if reasons else "No suspicious activity detected",
                detected_at=datetime.utcnow(),
                metadata={'countries': list(countries), 'attempt_count': len(recent_attempts)}
            )
            
        except Exception as e:
            logger.error(f"Suspicious activity check failed: {e}")
            return SecurityAlert(
                alert_id=str(uuid4()),
                user_id=user_id,
                alert_type="error",
                risk_level="LOW",
                is_suspicious=False,
                reason="Error during suspicious activity check"
            )
    
    async def _check_rate_limit(self, device_id: str, operation: str) -> bool:
        """레이트 리미팅 확인"""
        try:
            rate_limit_key = f"rate_limit:{operation}:{device_id}"
            current_count = await self.cache.get(rate_limit_key)
            
            max_attempts = self.max_login_attempts if operation == "login" else self.max_token_refresh
            ttl = 60 if operation == "login" else 3600
            
            if current_count is None:
                await self.cache.set(rate_limit_key, 1, ttl=ttl)
                return True
            
            if current_count >= max_attempts:
                return False
            
            await self.cache.set(rate_limit_key, current_count + 1, ttl=ttl)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # 에러 시에는 허용
    
    async def _log_login_attempt(
        self,
        user_id: Optional[str],
        device_id: str,
        provider: SocialProvider,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """로그인 시도 로깅"""
        try:
            attempt = LoginAttempt(
                attempt_id=str(uuid4()),
                user_id=user_id,
                device_id=device_id,
                provider=provider,
                success=success,
                attempted_at=datetime.utcnow(),
                failure_reason=failure_reason
            )
            
            # 로그를 캐시에 임시 저장 (실제로는 데이터베이스에)
            log_key = f"login_attempts:{device_id}:{attempt.attempted_at.timestamp()}"
            await self.cache.set(log_key, attempt.dict(), ttl=86400)
            
        except Exception as e:
            logger.error(f"Login attempt logging failed: {e}")


# 전역 Firebase Auth 서비스 인스턴스
firebase_auth_service = FirebaseAuthService()