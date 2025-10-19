# TRD: Firebase Authentication 기반 인증 시스템

## 1. 시스템 개요

### 1-1. 아키텍처 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter App   │    │  FastAPI Backend│    │Firebase/External│
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Firebase    │ │◄───┤ │ JWT         │ │◄───┤ │ Firebase    │ │
│ │ Auth SDK    │ │    │ │ Validator   │ │    │ │ Auth        │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Google      │ │    │ │ Firebase    │ │    │ │ Google      │ │
│ │ Sign-In SDK │ │───►│ │ Admin SDK   │ │───►│ │ OAuth       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Apple       │ │    │ │ Kakao       │ │    │ │ Apple       │ │
│ │ Sign-In SDK │ │    │ │ Custom Token│ │    │ │ Sign In     │ │
│ └─────────────┘ │    │ │ Generator   │ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ └─────────────┘ │    │ ┌─────────────┐ │
│ │ Kakao       │ │    │ ┌─────────────┐ │    │ │ Kakao       │ │
│ │ Flutter SDK │ │───►│ │ Rate Limiter│ │    │ │ OAuth API   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │                 │    │                 │
│ │ Auth State  │ │    │                 │    │                 │
│ │ Manager     │ │    │                 │    │                 │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1-2. 기술 스택
```yaml
Frontend:
  Framework: Flutter 3.x
  State Management: Riverpod
  Firebase: firebase_auth, firebase_core
  Social SDKs:
    - google_sign_in: ^6.0.0
    - sign_in_with_apple: ^5.0.0
    - kakao_flutter_sdk_user: ^1.9.0
  Logging: logger

Backend:
  Runtime: Python 3.11+
  Framework: FastAPI 0.104+
  Firebase: firebase-admin
  Async: asyncio
  Security: slowapi (Rate Limiting)

Authentication:
  Core: Firebase Authentication
  Token: JWT (Firebase ID Token)
  Social: Google, Apple, Kakao (Custom Token)
  Anonymous: Firebase Anonymous Auth

Security:
  Transport: HTTPS/TLS 1.3
  Storage: Flutter Secure Storage
  Token: Firebase ID Token (1시간 유효)
  Refresh: Firebase Refresh Token (영구)
```

---

## 2. Firebase 프로젝트 설정

### 2-1. Firebase Console 설정

#### 프로젝트 생성
```
1. Firebase Console (https://console.firebase.google.com) 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름: "hotly-app" (또는 원하는 이름)
4. Google Analytics 활성화 (선택사항)
5. 프로젝트 생성 완료
```

#### Authentication 활성화
```
Firebase Console > Authentication > Sign-in method

활성화할 제공업체:
├── ✅ Email/Password
│   └── 이메일 링크 로그인 비활성화 (비밀번호 로그인만 사용)
├── ✅ Google
│   └── 프로젝트 지원 이메일 설정
├── ✅ Apple
│   ├── Services ID 등록 (Apple Developer Console)
│   └── Private Key 업로드
└── ✅ Anonymous
    └── 게스트 모드용
```

#### 앱 등록
```
1. Android 앱 추가
   - 패키지 이름: com.example.hotly
   - google-services.json 다운로드
   - android/app/ 디렉토리에 배치

2. iOS 앱 추가
   - 번들 ID: com.example.hotly
   - GoogleService-Info.plist 다운로드
   - ios/Runner/ 디렉토리에 배치
```

### 2-2. Firebase Admin SDK 설정 (Backend)

```python
# backend/app/core/firebase_config.py
import firebase_admin
from firebase_admin import credentials, auth
from pydantic_settings import BaseSettings

class FirebaseSettings(BaseSettings):
    """Firebase 설정"""
    firebase_credentials_path: str = "path/to/serviceAccountKey.json"
    firebase_project_id: str

    class Config:
        env_file = ".env"

settings = FirebaseSettings()

# Firebase Admin SDK 초기화
cred = credentials.Certificate(settings.firebase_credentials_path)
firebase_app = firebase_admin.initialize_app(cred, {
    'projectId': settings.firebase_project_id,
})

def get_firebase_auth():
    """Firebase Auth 인스턴스 반환"""
    return auth
```

#### Service Account Key 생성
```
1. Firebase Console > 프로젝트 설정 > 서비스 계정
2. "새 비공개 키 생성" 클릭
3. JSON 파일 다운로드
4. backend/credentials/serviceAccountKey.json에 저장
5. .gitignore에 추가하여 커밋 방지
```

---

## 3. Frontend 구현 (Flutter)

### 3-1. Firebase Auth Service 구현

```dart
// frontend/lib/core/auth/firebase_auth_service.dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart' as kakao;
import 'package:logger/logger.dart';

class FirebaseAuthService {
  final FirebaseAuth _firebaseAuth;
  final GoogleSignIn _googleSignIn;
  final Logger _logger;

  FirebaseAuthService({
    FirebaseAuth? firebaseAuth,
    GoogleSignIn? googleSignIn,
    Logger? logger,
  })  : _firebaseAuth = firebaseAuth ?? FirebaseAuth.instance,
        _googleSignIn = googleSignIn ?? GoogleSignIn(),
        _logger = logger ?? Logger();

  /// 현재 로그인된 사용자
  User? get currentUser => _firebaseAuth.currentUser;

  /// 인증 상태 스트림
  Stream<User?> get authStateChanges => _firebaseAuth.authStateChanges();

  /// ID Token 가져오기 (API 호출용)
  Future<String?> getIdToken({bool forceRefresh = false}) async {
    try {
      final user = currentUser;
      if (user == null) return null;
      return await user.getIdToken(forceRefresh);
    } catch (e) {
      _logger.e('Failed to get ID token', error: e);
      return null;
    }
  }

  /// Google Sign-In
  Future<UserCredential?> signInWithGoogle() async {
    try {
      // Google Sign-In 시작
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      // Google 인증 정보 가져오기
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Firebase 인증 정보 생성
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Firebase 로그인
      return await _firebaseAuth.signInWithCredential(credential);
    } catch (e) {
      _logger.e('Google Sign-In failed', error: e);
      rethrow;
    }
  }

  /// Apple Sign-In
  Future<UserCredential?> signInWithApple() async {
    try {
      // Apple Sign-In 시작
      final appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      // Firebase 인증 정보 생성
      final oAuthProvider = OAuthProvider('apple.com');
      final credential = oAuthProvider.credential(
        idToken: appleCredential.identityToken,
        accessToken: appleCredential.authorizationCode,
      );

      // Firebase 로그인
      return await _firebaseAuth.signInWithCredential(credential);
    } catch (e) {
      _logger.e('Apple Sign-In failed', error: e);
      rethrow;
    }
  }

  /// Kakao Sign-In with Custom Token
  Future<UserCredential?> signInWithKakao({
    required Future<String> Function(String kakaoAccessToken)
        getCustomTokenFromBackend,
  }) async {
    try {
      // 1. Kakao SDK로 로그인
      kakao.OAuthToken token;
      if (await kakao.isKakaoTalkInstalled()) {
        token = await kakao.UserApi.instance.loginWithKakaoTalk();
      } else {
        token = await kakao.UserApi.instance.loginWithKakaoAccount();
      }

      _logger.i('Kakao login successful');

      // 2. 백엔드에서 Firebase Custom Token 받기
      final customToken = await getCustomTokenFromBackend(token.accessToken);

      // 3. Firebase Custom Token으로 로그인
      return await _firebaseAuth.signInWithCustomToken(customToken);
    } catch (e) {
      _logger.e('Kakao Sign-In failed', error: e);
      rethrow;
    }
  }

  /// 익명 로그인 (게스트 모드)
  Future<UserCredential> signInAnonymously() async {
    try {
      return await _firebaseAuth.signInAnonymously();
    } catch (e) {
      _logger.e('Anonymous sign-in failed', error: e);
      rethrow;
    }
  }

  /// 익명 사용자를 Google 계정으로 업그레이드
  Future<UserCredential?> linkWithGoogle() async {
    try {
      final user = currentUser;
      if (user == null || !user.isAnonymous) {
        throw Exception('No anonymous user to link');
      }

      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // 익명 사용자와 Google 계정 연결
      return await user.linkWithCredential(credential);
    } catch (e) {
      _logger.e('Failed to link with Google', error: e);
      rethrow;
    }
  }

  /// 로그아웃
  Future<void> signOut() async {
    try {
      await _firebaseAuth.signOut();
      if (await _googleSignIn.isSignedIn()) {
        await _googleSignIn.signOut();
      }
      try {
        await kakao.UserApi.instance.logout();
      } catch (e) {
        // Kakao 로그아웃 실패는 무시 (로그인 안 된 경우)
      }
    } catch (e) {
      _logger.e('Sign out failed', error: e);
      rethrow;
    }
  }
}
```

### 3-2. Auth Repository 구현

```dart
// frontend/lib/features/auth/data/repositories/auth_repository_impl.dart
class AuthRepositoryFirebaseImpl implements AuthRepository {
  final FirebaseAuthService _firebaseAuthService;
  final Dio _dio;

  AuthRepositoryFirebaseImpl(this._firebaseAuthService, this._dio);

  @override
  Future<Either<ApiException, User>> signInWithGoogle() async {
    try {
      final userCredential = await _firebaseAuthService.signInWithGoogle();
      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(
          type: ApiExceptionType.server,
          message: 'Google 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }
      return Right(User.fromFirebase(userCredential.user!));
    } on FirebaseAuthException catch (e) {
      return Left(ApiException(
        type: ApiExceptionType.server,
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithKakao() async {
    try {
      final userCredential = await _firebaseAuthService.signInWithKakao(
        getCustomTokenFromBackend: _getFirebaseCustomTokenFromBackend,
      );
      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(
          type: ApiExceptionType.server,
          message: 'Kakao 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }
      return Right(User.fromFirebase(userCredential.user!));
    } catch (e) {
      return Left(ApiException(
        type: ApiExceptionType.server,
        message: 'Kakao 로그인 실패: $e',
        statusCode: 500,
      ));
    }
  }

  /// 카카오 토큰으로 Firebase Custom Token 받기
  Future<String> _getFirebaseCustomTokenFromBackend(
    String kakaoAccessToken,
  ) async {
    try {
      final response = await _dio.post(
        '/api/v1/auth/social-login',
        data: {
          'provider': 'kakao',
          'accessToken': kakaoAccessToken,
        },
      );
      final customToken = response.data['customToken'] as String?;
      if (customToken == null) {
        throw Exception('Custom token not found in response');
      }
      return customToken;
    } catch (e) {
      throw Exception('Failed to get custom token from backend: $e');
    }
  }

  /// Firebase Auth 에러 메시지 변환
  String _getFirebaseErrorMessage(FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
        return '사용자를 찾을 수 없습니다';
      case 'wrong-password':
        return '비밀번호가 올바르지 않습니다';
      case 'email-already-in-use':
        return '이미 사용 중인 이메일입니다';
      case 'invalid-email':
        return '유효하지 않은 이메일 형식입니다';
      case 'weak-password':
        return '비밀번호가 너무 약합니다 (최소 6자 이상)';
      default:
        return e.message ?? '알 수 없는 오류가 발생했습니다';
    }
  }
}
```

### 3-3. Auth Provider (Riverpod State Management)

```dart
// frontend/lib/features/auth/presentation/providers/auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

enum AuthStatus { initial, authenticated, unauthenticated }

@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    User? user,
    @Default(AuthStatus.initial) AuthStatus status,
    @Default(false) bool isLoading,
    ApiException? error,
  }) = _AuthState;
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;
  StreamSubscription<User?>? _authSubscription;

  AuthNotifier(this._repository) : super(const AuthState()) {
    _checkInitialAuth();
    _listenToAuthChanges();
  }

  Future<void> _checkInitialAuth() async {
    final currentUser = _repository.currentUser;
    state = state.copyWith(
      user: currentUser,
      status: currentUser != null
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated,
    );
  }

  void _listenToAuthChanges() {
    _authSubscription = _repository.authStateChanges.listen((user) {
      state = state.copyWith(
        user: user,
        status: user != null
            ? AuthStatus.authenticated
            : AuthStatus.unauthenticated,
      );
    });
  }

  Future<void> signInWithGoogle() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.signInWithGoogle();

    result.fold(
      (error) => state = state.copyWith(isLoading: false, error: error),
      (_) => state = state.copyWith(isLoading: false),
    );
  }

  Future<void> signInWithKakao() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.signInWithKakao();

    result.fold(
      (error) => state = state.copyWith(isLoading: false, error: error),
      (user) => state = state.copyWith(
        isLoading: false,
        user: user,
        status: AuthStatus.authenticated,
      ),
    );
  }

  @override
  void dispose() {
    _authSubscription?.cancel();
    super.dispose();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});
```

---

## 4. Backend 구현 (FastAPI + Firebase Admin SDK)

### 4-1. Firebase Auth Service (Backend)

```python
# backend/app/services/auth/firebase_auth_service.py
from typing import Dict, Any, Optional
from firebase_admin import auth
from app.schemas.auth import SocialLoginRequest, LoginResponse
import httpx
import logging

logger = logging.getLogger(__name__)

class FirebaseAuthService:
    """Firebase Authentication 서비스"""

    def __init__(self):
        self.kakao_api_url = "https://kapi.kakao.com/v2/user/me"

    async def login_with_social(
        self,
        login_request: SocialLoginRequest
    ) -> LoginResponse:
        """
        소셜 로그인 처리 (Google, Apple, Kakao)

        Args:
            login_request: provider, accessToken or idToken

        Returns:
            LoginResponse with customToken (Firebase), user info
        """
        provider = login_request.provider

        if provider == "kakao":
            return await self._handle_kakao_login(login_request)
        elif provider == "google":
            return await self._handle_google_login(login_request)
        elif provider == "apple":
            return await self._handle_apple_login(login_request)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _handle_kakao_login(
        self,
        login_request: SocialLoginRequest
    ) -> LoginResponse:
        """
        Kakao 로그인 처리

        1. Kakao Access Token으로 사용자 정보 조회
        2. Firebase Custom Token 생성
        3. Firebase UID 반환
        """
        try:
            # 1. Kakao API로 사용자 정보 조회
            kakao_user = await self._get_kakao_user_info(
                login_request.access_token
            )

            # 2. Kakao ID로 Firebase UID 생성 (고유 식별자)
            kakao_id = kakao_user.get("id")
            firebase_uid = f"kakao_{kakao_id}"

            # 3. Firebase에 사용자 존재 여부 확인
            try:
                user = auth.get_user(firebase_uid)
                logger.info(f"Existing Firebase user: {firebase_uid}")
            except auth.UserNotFoundError:
                # 신규 사용자 생성
                user = auth.create_user(
                    uid=firebase_uid,
                    display_name=kakao_user.get("properties", {}).get("nickname"),
                    photo_url=kakao_user.get("properties", {}).get("profile_image"),
                )
                logger.info(f"Created new Firebase user: {firebase_uid}")

            # 4. Firebase Custom Token 생성
            custom_token = auth.create_custom_token(firebase_uid)

            return LoginResponse(
                customToken=custom_token.decode("utf-8"),
                user={
                    "uid": firebase_uid,
                    "displayName": user.display_name,
                    "photoURL": user.photo_url,
                    "provider": "kakao",
                },
                message="Kakao login successful",
            )

        except Exception as e:
            logger.error(f"Kakao login failed: {e}")
            raise Exception(f"Kakao login failed: {str(e)}")

    async def _get_kakao_user_info(self, access_token: str) -> Dict[str, Any]:
        """Kakao API로 사용자 정보 조회"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.kakao_api_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get Kakao user info: {e}")
            raise Exception(f"Failed to get Kakao user info: {str(e)}")

    async def validate_access_token(
        self,
        token: str
    ) -> TokenValidationResult:
        """
        Firebase ID Token 검증

        Args:
            token: Firebase ID Token

        Returns:
            TokenValidationResult with user info
        """
        try:
            # Firebase ID Token 검증
            decoded_token = auth.verify_id_token(token)

            return TokenValidationResult(
                valid=True,
                uid=decoded_token.get("uid"),
                email=decoded_token.get("email"),
                provider=decoded_token.get("firebase", {}).get("sign_in_provider"),
                user=decoded_token,
            )
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            raise Exception(f"Invalid token: {str(e)}")

    async def create_anonymous_user(
        self,
        anonymous_data: AnonymousUserRequest
    ) -> LoginResponse:
        """익명 사용자 생성 (게스트 모드)"""
        try:
            # Firebase Anonymous User 생성
            user = auth.create_user()
            custom_token = auth.create_custom_token(user.uid)

            return LoginResponse(
                customToken=custom_token.decode("utf-8"),
                user={
                    "uid": user.uid,
                    "isAnonymous": True,
                },
                message="Anonymous user created",
            )
        except Exception as e:
            logger.error(f"Anonymous user creation failed: {e}")
            raise Exception(f"Anonymous user creation failed: {str(e)}")

# Singleton instance
firebase_auth_service = FirebaseAuthService()
```

### 4-2. Auth Endpoints

```python
# backend/app/api/api_v1/endpoints/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import (
    SocialLoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenValidationResult,
)
from app.services.auth.firebase_auth_service import firebase_auth_service

router = APIRouter()

@router.post("/social-login", response_model=LoginResponse)
async def social_login(login_request: SocialLoginRequest) -> LoginResponse:
    """
    소셜 로그인 (Google, Apple, Kakao)

    클라이언트에서 소셜 로그인 후 받은 토큰을 검증하고
    Firebase Custom Token을 생성합니다.
    """
    try:
        result = await firebase_auth_service.login_with_social(login_request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Social login failed: {str(e)}",
        )

@router.post("/verify-token", response_model=TokenValidationResult)
async def verify_token(token: str) -> TokenValidationResult:
    """Firebase ID Token 검증"""
    try:
        result = await firebase_auth_service.validate_access_token(token)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )

@router.post("/anonymous", response_model=LoginResponse)
async def create_anonymous_user(
    anonymous_data: AnonymousUserRequest,
) -> LoginResponse:
    """익명 사용자 생성 (게스트 모드)"""
    try:
        result = await firebase_auth_service.create_anonymous_user(anonymous_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Anonymous user creation failed: {str(e)}",
        )
```

### 4-3. JWT Middleware (Token 검증)

```python
# backend/app/middleware/jwt_middleware.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from typing import Dict, Any

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자 정보 반환

    Firebase ID Token을 검증하고 사용자 정보를 반환합니다.
    """
    try:
        token = credentials.credentials

        # Firebase ID Token 검증
        decoded_token = auth.verify_id_token(token)

        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified"),
            "provider": decoded_token.get("firebase", {}).get("sign_in_provider"),
            "custom_claims": decoded_token.get("custom_claims", {}),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """활성 사용자 확인"""
    # 추가 검증 로직 (필요시)
    return current_user

async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """관리자 권한 확인"""
    custom_claims = current_user.get("custom_claims", {})
    if custom_claims.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
```

---

## 5. 카카오 로그인 Custom Token 방식 상세

### 5-1. 전체 플로우

```
[Flutter App]
    ↓
1. 카카오 SDK 로그인
   - 카카오톡 앱 or 웹 로그인
    ↓
2. 카카오 액세스 토큰 획득
   - OAuthToken.accessToken
    ↓
3. 백엔드 API 호출
   POST /api/v1/auth/social-login
   {
     "provider": "kakao",
     "accessToken": "kakao_access_token"
   }
    ↓
[Backend]
    ↓
4. Kakao API 호출
   GET https://kapi.kakao.com/v2/user/me
   Headers: { Authorization: Bearer kakao_access_token }
    ↓
5. Kakao 사용자 정보 조회
   { id: 12345678, properties: { nickname: "홍길동" } }
    ↓
6. Firebase UID 생성
   uid = "kakao_12345678"
    ↓
7. Firebase 사용자 생성/조회
   - 기존 사용자: auth.get_user(uid)
   - 신규 사용자: auth.create_user(uid, ...)
    ↓
8. Firebase Custom Token 생성
   custom_token = auth.create_custom_token(uid)
    ↓
9. 클라이언트에 응답
   { customToken: "eyJhbGciOiJSUzI1NiIsIn..." }
    ↓
[Flutter App]
    ↓
10. Firebase Custom Token 로그인
    await FirebaseAuth.instance.signInWithCustomToken(customToken)
    ↓
11. Firebase 로그인 완료
    - Firebase UID 발급
    - ID Token 자동 생성
    - authStateChanges 이벤트 발생
```

### 5-2. Kakao 사용자 정보 매핑

```python
# Kakao API Response
{
  "id": 12345678,  # Kakao 고유 ID
  "properties": {
    "nickname": "홍길동",
    "profile_image": "http://k.kakaocdn.net/...",
    "thumbnail_image": "http://k.kakaocdn.net/..."
  },
  "kakao_account": {
    "email": "user@example.com",
    "email_verified": true
  }
}

# Firebase User Mapping
{
  "uid": "kakao_12345678",  # "kakao_" prefix
  "displayName": "홍길동",
  "photoURL": "http://k.kakaocdn.net/...",
  "providerId": "kakao",  # Custom Claims에 저장
}
```

### 5-3. 에러 처리

```python
async def _handle_kakao_login_with_error_handling(
    self,
    login_request: SocialLoginRequest
) -> LoginResponse:
    """에러 처리가 포함된 Kakao 로그인"""
    try:
        # Kakao API 호출
        kakao_user = await self._get_kakao_user_info(
            login_request.access_token
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Invalid Kakao access token",
            )
        elif e.response.status_code == 400:
            raise HTTPException(
                status_code=400,
                detail="Kakao API request failed",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Kakao API error: {e}",
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {e}",
        )

    # Firebase Custom Token 생성
    try:
        firebase_uid = f"kakao_{kakao_user['id']}"
        custom_token = auth.create_custom_token(firebase_uid)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Firebase token creation failed: {e}",
        )

    return LoginResponse(
        customToken=custom_token.decode("utf-8"),
        user={"uid": firebase_uid},
    )
```

---

## 6. 보안 구현

### 6-1. Rate Limiting

```python
# backend/app/middleware/rate_limiter.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

# 로그인 엔드포인트에 적용
@router.post("/social-login")
@limiter.limit("5/minute")  # 분당 5회 제한
async def social_login(
    request: Request,
    login_request: SocialLoginRequest
) -> LoginResponse:
    # ... 로그인 로직
    pass
```

### 6-2. Custom Claims (역할 관리)

```python
# 관리자 역할 부여
auth.set_custom_user_claims(user_uid, {"role": "admin"})

# 사용자 역할 확인
decoded_token = auth.verify_id_token(id_token)
if decoded_token.get("role") == "admin":
    # 관리자 권한 작업
    pass
```

### 6-3. Firebase Security Rules (Firestore)

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 사용자는 자신의 데이터만 접근
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // 게스트는 자신의 임시 데이터만 접근
    match /guest_data/{guestId} {
      allow read, write: if request.auth != null &&
                           request.auth.uid == guestId &&
                           request.auth.token.firebase.sign_in_provider == 'anonymous';
    }

    // 관리자만 접근 가능
    match /admin_data/{document=**} {
      allow read, write: if request.auth != null &&
                           request.auth.token.role == 'admin';
    }
  }
}
```

---

## 7. 테스트 전략

### 7-1. Frontend Unit Tests

```dart
// test/features/auth/firebase_auth_service_test.dart
void main() {
  group('FirebaseAuthService', () {
    late FirebaseAuthService authService;
    late MockFirebaseAuth mockFirebaseAuth;
    late MockGoogleSignIn mockGoogleSignIn;

    setUp(() {
      mockFirebaseAuth = MockFirebaseAuth();
      mockGoogleSignIn = MockGoogleSignIn();
      authService = FirebaseAuthService(
        firebaseAuth: mockFirebaseAuth,
        googleSignIn: mockGoogleSignIn,
      );
    });

    test('Google Sign-In success', () async {
      // Given
      final mockGoogleUser = MockGoogleSignInAccount();
      final mockGoogleAuth = MockGoogleSignInAuthentication();

      when(mockGoogleSignIn.signIn())
          .thenAnswer((_) async => mockGoogleUser);
      when(mockGoogleUser.authentication)
          .thenAnswer((_) async => mockGoogleAuth);
      when(mockGoogleAuth.accessToken).thenReturn('access_token');
      when(mockGoogleAuth.idToken).thenReturn('id_token');

      // When
      final result = await authService.signInWithGoogle();

      // Then
      expect(result, isNotNull);
      verify(mockFirebaseAuth.signInWithCredential(any)).called(1);
    });
  });
}
```

### 7-2. Backend Integration Tests

```python
# tests/integration/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_kakao_login(client: AsyncClient):
    """Kakao 로그인 통합 테스트"""
    # Given
    kakao_access_token = "mock_kakao_token"

    # When
    response = await client.post(
        "/api/v1/auth/social-login",
        json={
            "provider": "kakao",
            "accessToken": kakao_access_token,
        },
    )

    # Then
    assert response.status_code == 200
    data = response.json()
    assert "customToken" in data
    assert data["user"]["provider"] == "kakao"

@pytest.mark.asyncio
async def test_token_validation(client: AsyncClient):
    """Firebase ID Token 검증 테스트"""
    # Given
    valid_token = "mock_firebase_id_token"

    # When
    response = await client.post(
        "/api/v1/auth/verify-token",
        params={"token": valid_token},
    )

    # Then
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "uid" in data
```

---

## 8. 환경 설정 및 배포

### 8-1. 환경 변수 설정

```bash
# backend/.env
FIREBASE_CREDENTIALS_PATH=credentials/serviceAccountKey.json
FIREBASE_PROJECT_ID=hotly-app-12345

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=5

# Kakao
KAKAO_REST_API_KEY=your_kakao_rest_api_key
```

```dart
// frontend/.env.dev
# Firebase Configuration
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=hotly-app.firebaseapp.com
FIREBASE_PROJECT_ID=hotly-app-12345
FIREBASE_APP_ID=1:1234567890:android:abcdef

# API
API_BASE_URL=http://localhost:8000/api/v1

# Kakao
KAKAO_NATIVE_APP_KEY=78ff40eb343af6b500a92c15fcd786db
```

### 8-2. Firebase 배포 체크리스트

```
✅ Firebase 프로젝트 생성
✅ Authentication 제공업체 활성화 (Google, Apple, Anonymous)
✅ Android/iOS 앱 등록
✅ google-services.json / GoogleService-Info.plist 배치
✅ Service Account Key 생성 및 다운로드
✅ Firestore Security Rules 설정
✅ 백엔드 환경 변수 설정
✅ 프론트엔드 Firebase 설정 파일 배치
✅ Kakao 앱 키 발급 및 설정
```

---

## 9. 모니터링 및 로깅

### 9-1. Firebase Console 모니터링

```
Firebase Console > Authentication
├── Users: 총 사용자 수, 활성 사용자
├── Sign-in methods: 제공업체별 사용 통계
├── Templates: 이메일 템플릿 설정
└── Settings: 프로젝트 설정

Firebase Console > Analytics (선택사항)
├── Events: 로그인 이벤트 추적
├── User properties: 사용자 속성
└── Audiences: 사용자 세그먼트
```

### 9-2. Backend 로깅

```python
# backend/app/services/auth/firebase_auth_service.py
import logging
import structlog

logger = structlog.get_logger(__name__)

async def login_with_social(self, login_request: SocialLoginRequest):
    logger.info(
        "social_login_attempt",
        provider=login_request.provider,
        timestamp=datetime.utcnow().isoformat(),
    )

    try:
        result = await self._handle_social_login(login_request)

        logger.info(
            "social_login_success",
            provider=login_request.provider,
            uid=result.user["uid"],
        )

        return result
    except Exception as e:
        logger.error(
            "social_login_failed",
            provider=login_request.provider,
            error=str(e),
        )
        raise
```

---

## 10. 트러블슈팅

### 10-1. 일반적인 이슈

**이슈 1: Kakao Custom Token 로그인 실패**
```
증상: Firebase signInWithCustomToken 실패
원인: Custom Token 형식 오류 또는 만료
해결:
1. Custom Token이 바이트 문자열인지 확인
2. decode("utf-8")로 문자열 변환
3. Firebase Admin SDK 초기화 확인
```

**이슈 2: Google Sign-In SHA-1 에러**
```
증상: Android에서 Google Sign-In 실패
원인: SHA-1 인증서 미등록
해결:
1. keytool -list -v -keystore debug.keystore
2. SHA-1 복사
3. Firebase Console > 프로젝트 설정 > SHA 인증서 추가
```

**이슈 3: Apple Sign-In 설정 오류**
```
증상: iOS에서 Apple Sign-In 실패
원인: Services ID 또는 Key 설정 오류
해결:
1. Apple Developer Console에서 Services ID 생성
2. Return URLs 설정
3. Firebase Console에 Private Key 업로드
```

### 10-2. 디버깅 가이드

```dart
// Frontend 디버깅
FirebaseAuth.instance.setSettings(
  appVerificationDisabledForTesting: true, // 테스트용
);

// 로그 활성화
Logger.level = Level.debug;

// 상세 로그 출력
_logger.d('Auth state changed', user?.uid);
```

```python
# Backend 디버깅
import logging
logging.basicConfig(level=logging.DEBUG)

# Firebase Admin SDK 디버깅
firebase_admin.initialize_app(cred, options={
    'debug': True,
})
```

---

## 11. 성능 최적화

### 11-1. Token Caching

```dart
// ID Token 캐싱 (Flutter)
String? _cachedIdToken;
DateTime? _tokenExpiryTime;

Future<String?> getIdToken() async {
  if (_cachedIdToken != null &&
      _tokenExpiryTime != null &&
      DateTime.now().isBefore(_tokenExpiryTime!)) {
    return _cachedIdToken;
  }

  // 토큰 갱신
  final token = await FirebaseAuth.instance.currentUser?.getIdToken(true);
  _cachedIdToken = token;
  _tokenExpiryTime = DateTime.now().add(Duration(minutes: 55)); // 5분 여유

  return token;
}
```

### 11-2. 병렬 요청 최적화

```python
# 병렬 Kakao API 호출
import asyncio

async def batch_validate_kakao_tokens(tokens: List[str]):
    tasks = [_get_kakao_user_info(token) for token in tokens]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## Changelog
- 2025-01-XX: 초기 문서 작성 - Firebase 기반 (작성자: Claude)
- 2025-01-XX: Firebase Authentication 기반으로 완전 재작성 (작성자: Claude)
  - 실제 구현 코드 기반 TRD 작성
  - Flutter + Firebase Auth SDK 구현 상세
  - FastAPI + Firebase Admin SDK 구현 상세
  - 카카오 Custom Token 방식 상세 설명
  - 보안, 테스트, 배포 가이드 포함
