# TRD: Supabase Auth 기반 인증 시스템

## 1. 시스템 개요

### 1-1. 아키텍처 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   API Gateway   │    │  Auth Service   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Supabase    │ │◄───┤ │ JWT         │ │◄───┤ │ Supabase    │ │
│ │ Auth Client │ │    │ │ Validator   │ │    │ │ GoTrue      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Social      │ │    │ │ Rate Limit  │ │    │ │ User        │ │
│ │ Login SDKs  │ │    │ │ Middleware  │ │    │ │ Management  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Biometric   │ │    │ │ Session     │ │    │ │ Token       │ │
│ │ Auth        │ │    │ │ Management  │ │    │ │ Management  │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────┐    ┌─────────────────┐
│ External OAuth  │    │   Data Store    │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Google      │ │───►│ │ Supabase    │ │
│ │ OAuth       │ │    │ │ Auth Tables │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Apple       │ │    │ │ User        │ │
│ │ Sign In     │ │    │ │ Profiles    │ │
│ └─────────────┘ │    │ │ (PostgreSQL)│ │
│ ┌─────────────┐ │    │ └─────────────┘ │
│ │ Kakao       │ │    │ ┌─────────────┐ │
│ │ Login       │ │    │ │ Session     │ │
│ └─────────────┘ │    │ │ Store       │ │
└─────────────────┘    │ │ (Redis)     │ │
                       │ └─────────────┘ │
                       └─────────────────┘
```

### 1-2. 기술 스택
```yaml
Authentication:
  Core: Supabase Auth (GoTrue)
  Social: Google Sign-In, Apple Sign In, Kakao OAuth
  Biometric: React Native Biometrics, Android Biometric API

Backend:
  Runtime: Python 3.11+ (FastAPI)
  Framework: FastAPI
  Session Store: Redis Cluster
  Database: PostgreSQL (Supabase managed)

Security:
  Encryption: AES-256-GCM (local storage)
  Transport: TLS 1.3
  JWT: Supabase JWT with user_metadata/app_metadata
  Rate Limiting: slowapi + Redis
  RLS: PostgreSQL Row Level Security

Client:
  Web: @supabase/supabase-js
  Mobile: @supabase/supabase-flutter (if needed)
  State Management: React Context / Redux (auth state)
```

## 2. Supabase 설정 및 구성

### 2-1. Supabase 프로젝트 설정
```python
# app/core/supabase_config.py
from supabase import create_client, Client
from pydantic_settings import BaseSettings

class SupabaseSettings(BaseSettings):
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    jwt_secret: str

    # OAuth 설정
    google_client_id: str
    google_client_secret: str
    apple_client_id: str
    apple_client_secret: str

    # 인증 설정
    password_min_length: int = 8
    email_verification_required: bool = True
    session_duration_hours: int = 24
    refresh_token_duration_days: int = 30

    class Config:
        env_file = ".env"

settings = SupabaseSettings()

# Supabase 클라이언트 초기화
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

# 서비스 역할 클라이언트 (관리자 작업용)
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)
```

### 2-2. Supabase Auth 제공업체 설정
```sql
-- Supabase Dashboard에서 설정 또는 SQL로 구성

-- OAuth 제공업체 활성화
-- Google OAuth
INSERT INTO auth.providers (name, enabled)
VALUES ('google', true);

-- Apple OAuth
INSERT INTO auth.providers (name, enabled)
VALUES ('apple', true);

-- Anonymous 인증
INSERT INTO auth.providers (name, enabled)
VALUES ('anonymous', true);

-- 이메일 인증 설정
UPDATE auth.config
SET
  enable_signup = true,
  enable_anonymous_sign_ins = true,
  email_confirm_required = true,
  secure_password_change = true,
  password_min_length = 8;
```

### 2-3. PostgreSQL Row Level Security (RLS)
```sql
-- auth.users는 Supabase가 자동 관리
-- 추가 프로필 정보를 위한 테이블 생성

-- 사용자 프로필 테이블
CREATE TABLE public.user_profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  display_name TEXT NOT NULL CHECK (char_length(display_name) BETWEEN 2 AND 20),
  bio TEXT,
  photo_url TEXT,
  region TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 활성화
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- 사용자 프로필 정책: 자신의 프로필만 읽기/쓰기
CREATE POLICY "Users can view own profile"
  ON public.user_profiles
  FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON public.user_profiles
  FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON public.user_profiles
  FOR INSERT
  WITH CHECK (auth.uid() = id);

-- 게스트 데이터 테이블
CREATE TABLE public.guest_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id),
  data JSONB NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.guest_data ENABLE ROW LEVEL SECURITY;

-- 게스트 데이터 정책: 익명 사용자만 접근
CREATE POLICY "Anonymous users can manage own guest data"
  ON public.guest_data
  FOR ALL
  USING (
    auth.uid() = user_id
    AND auth.jwt()->>'is_anonymous' = 'true'
    AND expires_at > NOW()
  );

-- 관리자 테이블
CREATE TABLE public.admin_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  data JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.admin_data ENABLE ROW LEVEL SECURITY;

-- 관리자 정책: app_metadata에 admin 역할이 있는 사용자만
CREATE POLICY "Only admins can access admin data"
  ON public.admin_data
  FOR ALL
  USING (
    (auth.jwt()->>'role')::text = 'admin'
  );
```

### 2-4. User Metadata 관리
```python
# app/services/user_metadata_service.py
from typing import Dict, Any, Optional
from supabase import Client

class UserMetadataService:
    """Supabase의 user_metadata와 app_metadata 관리"""

    def __init__(self, supabase_admin: Client):
        self.supabase_admin = supabase_admin

    async def set_user_metadata(
        self,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """사용자 메타데이터 설정 (사용자가 수정 가능)"""
        try:
            self.supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"user_metadata": metadata}
            )
        except Exception as e:
            raise Exception(f"Failed to set user metadata: {str(e)}")

    async def set_app_metadata(
        self,
        user_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """앱 메타데이터 설정 (관리자만 수정 가능)"""
        try:
            self.supabase_admin.auth.admin.update_user_by_id(
                user_id,
                {"app_metadata": metadata}
            )
        except Exception as e:
            raise Exception(f"Failed to set app metadata: {str(e)}")

    async def set_user_role(self, user_id: str, role: str) -> None:
        """사용자 역할 설정 (JWT에 포함됨)"""
        await self.set_app_metadata(user_id, {"role": role})

    async def update_last_active(self, user_id: str) -> None:
        """마지막 활성 시간 업데이트"""
        await self.set_app_metadata(
            user_id,
            {"last_active": datetime.utcnow().isoformat()}
        )
```

## 3. 인증 서비스 구현

### 3-1. Supabase Auth 초기화
```python
# app/services/auth_service.py
from supabase import Client, create_client
from typing import Optional, Callable, List
from datetime import datetime
import asyncio

class SupabaseAuthService:
    """Supabase 인증 서비스"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.current_session = None
        self.auth_state_listeners: List[Callable] = []

        # 인증 상태 변경 리스너 설정
        self.setup_auth_state_listener()

    def setup_auth_state_listener(self) -> None:
        """인증 상태 변경 리스너 설정"""
        def on_auth_state_change(event, session):
            self.current_session = session

            if session and session.user:
                # 토큰 새로고침 및 메타데이터 업데이트
                asyncio.create_task(self.update_last_active(session.user.id))

            # 모든 리스너에게 상태 변경 알림
            for listener in self.auth_state_listeners:
                listener(session)

        self.supabase.auth.on_auth_state_change(on_auth_state_change)

    async def refresh_session(self) -> Optional[dict]:
        """세션 새로고침"""
        try:
            response = self.supabase.auth.refresh_session()
            if response.session:
                self.current_session = response.session
                return response.session
            return None
        except Exception as e:
            raise Exception(f"Session refresh failed: {str(e)}")

    def get_access_token(self) -> Optional[str]:
        """현재 액세스 토큰 반환"""
        if self.current_session:
            return self.current_session.access_token
        return None

    def on_auth_state_change(self, listener: Callable) -> Callable:
        """인증 상태 변경 리스너 추가"""
        self.auth_state_listeners.append(listener)
        # 즉시 현재 상태 전달
        listener(self.current_session)

        # 언서브스크라이브 함수 반환
        def unsubscribe():
            self.auth_state_listeners.remove(listener)
        return unsubscribe

    async def get_current_user(self) -> Optional[dict]:
        """현재 로그인한 사용자 정보 반환"""
        try:
            user = self.supabase.auth.get_user()
            return user.user if user else None
        except:
            return None

    async def update_last_active(self, user_id: str) -> None:
        """마지막 활동 시간 업데이트"""
        try:
            self.supabase.auth.admin.update_user_by_id(
                user_id,
                {"app_metadata": {"last_active": datetime.utcnow().isoformat()}}
            )
        except Exception as e:
            print(f"Failed to update last active: {str(e)}")
```

### 3-2. 이메일/비밀번호 인증
```typescript
// email-auth.ts
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  sendEmailVerification,
  sendPasswordResetEmail,
  updateProfile
} from 'firebase/auth';

interface SignUpData {
  email: string;
  password: string;
  displayName: string;
  acceptedTerms: boolean;
}

interface SignInData {
  email: string;
  password: string;
  rememberMe: boolean;
}

class EmailAuthService {
  constructor(private authService: FirebaseAuthService) {}

  async signUp(data: SignUpData): Promise<UserCredential> {
    this.validateSignUpData(data);

    try {
      // 1. Firebase Auth 계정 생성
      const userCredential = await createUserWithEmailAndPassword(
        this.authService.auth,
        data.email,
        data.password
      );

      // 2. 사용자 프로필 업데이트
      await updateProfile(userCredential.user, {
        displayName: data.displayName
      });

      // 3. 이메일 인증 발송
      await this.sendVerificationEmail(userCredential.user);

      // 4. 사용자 프로필 생성
      await this.createUserProfile(userCredential.user, data);

      // 5. 가입 이벤트 로깅
      await this.logAuthEvent('signup', userCredential.user.uid, {
        provider: 'email',
        email: data.email
      });

      return userCredential;
    } catch (error) {
      this.handleAuthError(error);
      throw error;
    }
  }

  async signIn(data: SignInData): Promise<UserCredential> {
    try {
      const userCredential = await signInWithEmailAndPassword(
        this.authService.auth,
        data.email,
        data.password
      );

      // Remember me 설정
      if (data.rememberMe) {
        await this.setPersistence(true);
      }

      // 로그인 이벤트 로깅
      await this.logAuthEvent('signin', userCredential.user.uid, {
        provider: 'email',
        remember_me: data.rememberMe
      });

      return userCredential;
    } catch (error) {
      this.handleAuthError(error);
      throw error;
    }
  }

  async sendVerificationEmail(user: User): Promise<void> {
    try {
      await sendEmailVerification(user, {
        url: 'https://hotly.app/verify-email',
        handleCodeInApp: true
      });
    } catch (error) {
      console.error('Failed to send verification email:', error);
      throw new Error('이메일 인증 메일 발송에 실패했습니다.');
    }
  }

  async resetPassword(email: string): Promise<void> {
    try {
      await sendPasswordResetEmail(this.authService.auth, email, {
        url: 'https://hotly.app/reset-password'
      });
    } catch (error) {
      console.error('Password reset failed:', error);
      throw new Error('비밀번호 재설정 메일 발송에 실패했습니다.');
    }
  }

  private validateSignUpData(data: SignUpData): void {
    if (!data.acceptedTerms) {
      throw new Error('이용약관에 동의해야 합니다.');
    }

    if (!this.isValidEmail(data.email)) {
      throw new Error('올바른 이메일 주소를 입력해주세요.');
    }

    if (!this.isValidPassword(data.password)) {
      throw new Error('비밀번호는 8자 이상, 영문과 숫자를 포함해야 합니다.');
    }

    if (data.displayName.length < 2 || data.displayName.length > 20) {
      throw new Error('닉네임은 2-20자 사이로 입력해주세요.');
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private isValidPassword(password: string): boolean {
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /\d/.test(password);
    const minLength = password.length >= 8;

    return hasLetter && hasNumber && minLength;
  }
}
```

### 3-3. 소셜 로그인 구현
```typescript
// social-auth.ts
import {
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  OAuthProvider
} from 'firebase/auth';

interface SocialProvider {
  id: string;
  name: string;
  provider: AuthProvider;
  scopes?: string[];
}

class SocialAuthService {
  private providers: Map<string, SocialProvider> = new Map();

  constructor(private authService: FirebaseAuthService) {
    this.initializeProviders();
  }

  private initializeProviders(): void {
    // Google 프로바이더
    const googleProvider = new GoogleAuthProvider();
    googleProvider.addScope('email');
    googleProvider.addScope('profile');
    googleProvider.setCustomParameters({
      prompt: 'select_account'
    });

    this.providers.set('google', {
      id: 'google',
      name: 'Google',
      provider: googleProvider,
      scopes: ['email', 'profile']
    });

    // Apple 프로바이더 (웹용)
    const appleProvider = new OAuthProvider('apple.com');
    appleProvider.addScope('email');
    appleProvider.addScope('name');
    appleProvider.setCustomParameters({
      locale: 'ko'
    });

    this.providers.set('apple', {
      id: 'apple',
      name: 'Apple',
      provider: appleProvider,
      scopes: ['email', 'name']
    });

    // 카카오는 Custom Auth Token으로 구현
    this.setupKakaoProvider();
  }

  async signInWithProvider(providerId: string): Promise<UserCredential> {
    const providerConfig = this.providers.get(providerId);
    if (!providerConfig) {
      throw new Error(`Unsupported provider: ${providerId}`);
    }

    try {
      let userCredential: UserCredential;

      if (this.isMobile()) {
        // 모바일에서는 리다이렉트 방식 사용
        userCredential = await signInWithRedirect(
          this.authService.auth,
          providerConfig.provider
        );
      } else {
        // 웹에서는 팝업 방식 사용
        userCredential = await signInWithPopup(
          this.authService.auth,
          providerConfig.provider
        );
      }

      // 프로필 정보 보완
      await this.processSocialUserProfile(userCredential, providerId);

      // 소셜 로그인 이벤트 로깅
      await this.logAuthEvent('social_signin', userCredential.user.uid, {
        provider: providerId,
        is_new_user: userCredential.additionalUserInfo?.isNewUser
      });

      return userCredential;
    } catch (error) {
      this.handleSocialAuthError(error, providerId);
      throw error;
    }
  }

  private async setupKakaoProvider(): Promise<void> {
    // 카카오 로그인은 Custom Auth Token 방식으로 구현
    // 1. 카카오 SDK로 로그인 → 액세스 토큰 획득
    // 2. 백엔드에서 토큰 검증 → Firebase Custom Token 생성
    // 3. Custom Token으로 Firebase 로그인
  }

  async signInWithKakao(): Promise<UserCredential> {
    try {
      // 1. 카카오 SDK 로그인
      const kakaoToken = await this.kakaoLogin();

      // 2. 백엔드로 토큰 전송하여 Firebase Custom Token 획득
      const customToken = await this.exchangeKakaoToken(kakaoToken);

      // 3. Custom Token으로 Firebase 로그인
      const userCredential = await signInWithCustomToken(
        this.authService.auth,
        customToken
      );

      return userCredential;
    } catch (error) {
      console.error('Kakao login failed:', error);
      throw new Error('카카오 로그인에 실패했습니다.');
    }
  }

  private async kakaoLogin(): Promise<string> {
    // React Native의 경우 @react-native-kakao/user 사용
    // 웹의 경우 Kakao JavaScript SDK 사용
    if (Platform.OS === 'ios' || Platform.OS === 'android') {
      return await this.kakaoNativeLogin();
    } else {
      return await this.kakaoWebLogin();
    }
  }

  private async exchangeKakaoToken(accessToken: string): Promise<string> {
    const response = await fetch('/api/auth/kakao/exchange', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ access_token: accessToken })
    });

    if (!response.ok) {
      throw new Error('Failed to exchange Kakao token');
    }

    const { firebase_token } = await response.json();
    return firebase_token;
  }

  private async processSocialUserProfile(
    userCredential: UserCredential,
    providerId: string
  ): Promise<void> {
    const user = userCredential.user;
    const profile = userCredential.additionalUserInfo?.profile as any;

    // 프로바이더별 프로필 정보 매핑
    let displayName = user.displayName;
    let photoURL = user.photoURL;

    switch (providerId) {
      case 'google':
        displayName = profile?.name || user.displayName;
        photoURL = profile?.picture || user.photoURL;
        break;
      case 'apple':
        // Apple은 첫 로그인 시에만 이름 제공
        if (profile?.name) {
          displayName = `${profile.name.firstName} ${profile.name.lastName}`;
        }
        break;
      case 'kakao':
        displayName = profile?.nickname;
        photoURL = profile?.profile_image_url;
        break;
    }

    // 프로필 업데이트
    if (displayName !== user.displayName || photoURL !== user.photoURL) {
      await updateProfile(user, { displayName, photoURL });
    }

    // 사용자 프로필 DB 생성/업데이트
    await this.createOrUpdateUserProfile(user, {
      provider: providerId,
      socialProfile: profile
    });
  }
}
```

## 4. 게스트 모드 구현

### 4-1. 익명 인증 관리
```typescript
// guest-auth.ts
import { signInAnonymously, linkWithCredential } from 'firebase/auth';

interface GuestData {
  places: Place[];
  courses: Course[];
  preferences: UserPreferences;
  created_at: number;
  expires_at: number;
}

class GuestAuthService {
  private readonly GUEST_DATA_TTL = 24 * 60 * 60 * 1000; // 24시간

  constructor(private authService: FirebaseAuthService) {}

  async signInAsGuest(): Promise<UserCredential> {
    try {
      const userCredential = await signInAnonymously(this.authService.auth);

      // 게스트 데이터 컨테이너 생성
      await this.initializeGuestData(userCredential.user.uid);

      // 게스트 로그인 이벤트
      await this.logAuthEvent('guest_signin', userCredential.user.uid, {
        expires_at: Date.now() + this.GUEST_DATA_TTL
      });

      return userCredential;
    } catch (error) {
      console.error('Guest sign in failed:', error);
      throw new Error('게스트 로그인에 실패했습니다.');
    }
  }

  async convertGuestToUser(credential: AuthCredential): Promise<UserCredential> {
    const currentUser = this.authService.getCurrentUser();

    if (!currentUser || !currentUser.isAnonymous) {
      throw new Error('게스트 계정이 아닙니다.');
    }

    try {
      // 1. 게스트 데이터 백업
      const guestData = await this.getGuestData(currentUser.uid);

      // 2. 익명 계정을 실제 계정으로 연결
      const userCredential = await linkWithCredential(currentUser, credential);

      // 3. 게스트 데이터를 사용자 계정으로 이전
      await this.migrateGuestData(userCredential.user.uid, guestData);

      // 4. 사용자 프로필 생성
      await this.createUserProfileFromGuest(userCredential.user, guestData);

      // 5. 게스트 데이터 정리
      await this.cleanupGuestData(currentUser.uid);

      // 계정 연결 이벤트 로깅
      await this.logAuthEvent('guest_conversion', userCredential.user.uid, {
        guest_data_items: Object.keys(guestData).length,
        conversion_method: credential.providerId
      });

      return userCredential;
    } catch (error) {
      console.error('Guest conversion failed:', error);
      throw new Error('계정 연결에 실패했습니다.');
    }
  }

  private async initializeGuestData(guestUid: string): Promise<void> {
    const guestData: GuestData = {
      places: [],
      courses: [],
      preferences: this.getDefaultPreferences(),
      created_at: Date.now(),
      expires_at: Date.now() + this.GUEST_DATA_TTL
    };

    await this.saveGuestData(guestUid, guestData);
  }

  private async getGuestData(guestUid: string): Promise<GuestData> {
    const doc = await firestore()
      .collection('guest_data')
      .doc(guestUid)
      .get();

    if (!doc.exists) {
      throw new Error('게스트 데이터가 존재하지 않습니다.');
    }

    return doc.data() as GuestData;
  }

  private async saveGuestData(guestUid: string, data: GuestData): Promise<void> {
    await firestore()
      .collection('guest_data')
      .doc(guestUid)
      .set(data, { merge: true });
  }

  private async migrateGuestData(userUid: string, guestData: GuestData): Promise<void> {
    const batch = firestore().batch();

    // 장소 데이터 이전
    guestData.places.forEach((place, index) => {
      const placeRef = firestore()
        .collection('users')
        .doc(userUid)
        .collection('places')
        .doc();

      batch.set(placeRef, {
        ...place,
        migrated_from_guest: true,
        migrated_at: new Date()
      });
    });

    // 코스 데이터 이전
    guestData.courses.forEach((course, index) => {
      const courseRef = firestore()
        .collection('users')
        .doc(userUid)
        .collection('courses')
        .doc();

      batch.set(courseRef, {
        ...course,
        migrated_from_guest: true,
        migrated_at: new Date()
      });
    });

    await batch.commit();
  }

  async cleanupExpiredGuestData(): Promise<void> {
    const expiredThreshold = Date.now();

    const expiredGuests = await firestore()
      .collection('guest_data')
      .where('expires_at', '<=', expiredThreshold)
      .get();

    const batch = firestore().batch();
    expiredGuests.docs.forEach(doc => {
      batch.delete(doc.ref);
    });

    await batch.commit();
    console.log(`Cleaned up ${expiredGuests.docs.length} expired guest accounts`);
  }
}
```

## 5. 생체 인증 구현

### 5-1. 생체 인증 서비스
```typescript
// biometric-auth.ts
import ReactNativeBiometrics from 'react-native-biometrics';

interface BiometricConfig {
  title: string;
  subtitle: string;
  description: string;
  fallbackLabel: string;
  negativeLabel: string;
}

enum BiometricType {
  FINGERPRINT = 'Fingerprint',
  FACE_ID = 'FaceID',
  IRIS = 'Iris',
  NONE = 'None'
}

class BiometricAuthService {
  private rnBiometrics: ReactNativeBiometrics;
  private isAvailable: boolean = false;
  private biometricType: BiometricType = BiometricType.NONE;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics();
    this.initializeBiometrics();
  }

  private async initializeBiometrics(): Promise<void> {
    try {
      const { available, biometryType } = await this.rnBiometrics.isSensorAvailable();

      this.isAvailable = available;

      switch (biometryType) {
        case ReactNativeBiometrics.TouchID:
        case ReactNativeBiometrics.Fingerprint:
          this.biometricType = BiometricType.FINGERPRINT;
          break;
        case ReactNativeBiometrics.FaceID:
          this.biometricType = BiometricType.FACE_ID;
          break;
        default:
          this.biometricType = BiometricType.NONE;
      }
    } catch (error) {
      console.error('Biometric initialization failed:', error);
      this.isAvailable = false;
    }
  }

  async isBiometricAvailable(): Promise<boolean> {
    return this.isAvailable;
  }

  getBiometricType(): BiometricType {
    return this.biometricType;
  }

  async enableBiometricAuth(userId: string): Promise<boolean> {
    if (!this.isAvailable) {
      throw new Error('생체인증을 사용할 수 없습니다.');
    }

    try {
      // 1. 키 쌍 생성
      const { keysExist } = await this.rnBiometrics.biometricKeysExist();

      if (!keysExist) {
        const { publicKey } = await this.rnBiometrics.createKeys();
        // 공개 키를 서버에 저장 (선택사항)
        await this.storeBiometricPublicKey(userId, publicKey);
      }

      // 2. 생체인증 테스트
      const config = this.getBiometricConfig();
      const { success } = await this.rnBiometrics.createSignature({
        promptMessage: '생체인증을 설정하시겠습니까?',
        payload: `enable_biometric_${userId}_${Date.now()}`
      });

      if (success) {
        // 3. 생체인증 활성화 상태 저장
        await this.saveBiometricPreference(userId, true);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Enable biometric auth failed:', error);
      throw new Error('생체인증 설정에 실패했습니다.');
    }
  }

  async authenticateWithBiometric(userId: string): Promise<boolean> {
    if (!this.isAvailable) {
      return false;
    }

    const isEnabled = await this.isBiometricEnabled(userId);
    if (!isEnabled) {
      return false;
    }

    try {
      const config = this.getBiometricConfig();
      const payload = `auth_${userId}_${Date.now()}`;

      const { success, signature } = await this.rnBiometrics.createSignature({
        promptMessage: config.title,
        payload
      });

      if (success && signature) {
        // 서명 검증 (선택사항)
        const isValid = await this.verifyBiometricSignature(userId, payload, signature);
        return isValid;
      }

      return false;
    } catch (error) {
      console.error('Biometric authentication failed:', error);
      return false;
    }
  }

  async disableBiometricAuth(userId: string): Promise<void> {
    try {
      // 1. 키 삭제
      await this.rnBiometrics.deleteKeys();

      // 2. 설정 비활성화
      await this.saveBiometricPreference(userId, false);

      // 3. 서버에서 공개 키 삭제
      await this.deleteBiometricPublicKey(userId);
    } catch (error) {
      console.error('Disable biometric auth failed:', error);
      throw new Error('생체인증 해제에 실패했습니다.');
    }
  }

  private getBiometricConfig(): BiometricConfig {
    const baseConfig: BiometricConfig = {
      fallbackLabel: '비밀번호 사용',
      negativeLabel: '취소',
      title: 'Hotly 인증',
      subtitle: '',
      description: ''
    };

    switch (this.biometricType) {
      case BiometricType.FINGERPRINT:
        return {
          ...baseConfig,
          subtitle: '지문으로 로그인',
          description: '등록된 지문을 인식해주세요'
        };
      case BiometricType.FACE_ID:
        return {
          ...baseConfig,
          subtitle: 'Face ID로 로그인',
          description: '얼굴을 인식해주세요'
        };
      default:
        return {
          ...baseConfig,
          subtitle: '생체인증으로 로그인',
          description: '등록된 생체정보를 인식해주세요'
        };
    }
  }

  private async saveBiometricPreference(userId: string, enabled: boolean): Promise<void> {
    const key = `biometric_enabled_${userId}`;
    await SecureStore.setItemAsync(key, enabled.toString());
  }

  private async isBiometricEnabled(userId: string): Promise<boolean> {
    const key = `biometric_enabled_${userId}`;
    const value = await SecureStore.getItemAsync(key);
    return value === 'true';
  }
}
```

### 5-2. PIN/패턴 인증
```typescript
// pin-auth.ts
interface PinConfig {
  length: number; // 4 또는 6
  attempts: number;
  lockoutDuration: number; // ms
}

class PinAuthService {
  private readonly config: PinConfig = {
    length: 6,
    attempts: 5,
    lockoutDuration: 5 * 60 * 1000 // 5분
  };

  async setPinCode(userId: string, pinCode: string): Promise<void> {
    this.validatePinCode(pinCode);

    try {
      // PIN을 해시화하여 저장
      const hashedPin = await this.hashPin(pinCode);
      const key = `pin_${userId}`;

      await SecureStore.setItemAsync(key, hashedPin);

      // PIN 설정 완료 표시
      await SecureStore.setItemAsync(`pin_enabled_${userId}`, 'true');

      // 실패 횟수 초기화
      await this.resetFailedAttempts(userId);

    } catch (error) {
      console.error('PIN setup failed:', error);
      throw new Error('PIN 설정에 실패했습니다.');
    }
  }

  async verifyPinCode(userId: string, pinCode: string): Promise<boolean> {
    // 잠금 상태 확인
    const isLocked = await this.isAccountLocked(userId);
    if (isLocked) {
      throw new Error('계정이 잠겼습니다. 잠시 후 다시 시도해주세요.');
    }

    try {
      const key = `pin_${userId}`;
      const storedHash = await SecureStore.getItemAsync(key);

      if (!storedHash) {
        throw new Error('PIN이 설정되지 않았습니다.');
      }

      const isValid = await this.verifyPin(pinCode, storedHash);

      if (isValid) {
        await this.resetFailedAttempts(userId);
        return true;
      } else {
        await this.incrementFailedAttempts(userId);
        return false;
      }
    } catch (error) {
      console.error('PIN verification failed:', error);
      await this.incrementFailedAttempts(userId);
      return false;
    }
  }

  async removePinCode(userId: string): Promise<void> {
    try {
      await SecureStore.deleteItemAsync(`pin_${userId}`);
      await SecureStore.deleteItemAsync(`pin_enabled_${userId}`);
      await SecureStore.deleteItemAsync(`pin_attempts_${userId}`);
      await SecureStore.deleteItemAsync(`pin_lockout_${userId}`);
    } catch (error) {
      console.error('PIN removal failed:', error);
      throw new Error('PIN 제거에 실패했습니다.');
    }
  }

  private validatePinCode(pinCode: string): void {
    if (pinCode.length !== this.config.length) {
      throw new Error(`PIN은 ${this.config.length}자리여야 합니다.`);
    }

    if (!/^\d+$/.test(pinCode)) {
      throw new Error('PIN은 숫자만 사용할 수 있습니다.');
    }

    // 연속된 숫자 체크 (예: 123456, 654321)
    if (this.isSequentialPin(pinCode)) {
      throw new Error('연속된 숫자는 사용할 수 없습니다.');
    }

    // 반복된 숫자 체크 (예: 111111, 000000)
    if (this.isRepeatingPin(pinCode)) {
      throw new Error('동일한 숫자 반복은 사용할 수 없습니다.');
    }
  }

  private async hashPin(pinCode: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(pinCode + 'hotly_salt');
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private async verifyPin(pinCode: string, hashedPin: string): Promise<boolean> {
    const hashToCheck = await this.hashPin(pinCode);
    return hashToCheck === hashedPin;
  }

  private async incrementFailedAttempts(userId: string): Promise<void> {
    const key = `pin_attempts_${userId}`;
    const currentAttempts = parseInt(await SecureStore.getItemAsync(key) || '0');
    const newAttempts = currentAttempts + 1;

    await SecureStore.setItemAsync(key, newAttempts.toString());

    if (newAttempts >= this.config.attempts) {
      const lockoutUntil = Date.now() + this.config.lockoutDuration;
      await SecureStore.setItemAsync(`pin_lockout_${userId}`, lockoutUntil.toString());
    }
  }

  private async resetFailedAttempts(userId: string): Promise<void> {
    await SecureStore.deleteItemAsync(`pin_attempts_${userId}`);
    await SecureStore.deleteItemAsync(`pin_lockout_${userId}`);
  }

  private async isAccountLocked(userId: string): Promise<boolean> {
    const lockoutKey = `pin_lockout_${userId}`;
    const lockoutUntil = await SecureStore.getItemAsync(lockoutKey);

    if (!lockoutUntil) return false;

    const lockoutTime = parseInt(lockoutUntil);
    if (Date.now() > lockoutTime) {
      await SecureStore.deleteItemAsync(lockoutKey);
      return false;
    }

    return true;
  }
}
```

## 6. 세션 및 토큰 관리

### 6-1. JWT 토큰 검증
```typescript
// jwt-validator.ts
import { auth } from 'firebase-admin';
import { DecodedIdToken } from 'firebase-admin/auth';

interface TokenValidationResult {
  valid: boolean;
  user?: DecodedIdToken;
  error?: string;
}

class JWTValidator {
  async validateFirebaseToken(token: string): Promise<TokenValidationResult> {
    try {
      // Firebase ID 토큰 검증
      const decodedToken = await auth().verifyIdToken(token, true);

      // 추가 검증
      if (!this.isTokenValid(decodedToken)) {
        return { valid: false, error: 'Invalid token claims' };
      }

      return { valid: true, user: decodedToken };
    } catch (error) {
      console.error('Token validation failed:', error);

      if (error.code === 'auth/id-token-expired') {
        return { valid: false, error: 'Token expired' };
      }

      if (error.code === 'auth/id-token-revoked') {
        return { valid: false, error: 'Token revoked' };
      }

      return { valid: false, error: 'Invalid token' };
    }
  }

  private isTokenValid(token: DecodedIdToken): boolean {
    // 토큰 만료 시간 확인
    if (token.exp < Math.floor(Date.now() / 1000)) {
      return false;
    }

    // 발급 시간이 너무 오래된 경우
    const maxAge = 24 * 60 * 60; // 24시간
    if (token.iat < Math.floor(Date.now() / 1000) - maxAge) {
      return false;
    }

    // 필수 클레임 확인
    if (!token.uid || !token.iss || !token.aud) {
      return false;
    }

    return true;
  }

  // Express 미들웨어
  createAuthMiddleware() {
    return async (req: Request, res: Response, next: NextFunction) => {
      const authHeader = req.headers.authorization;

      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing or invalid authorization header' });
      }

      const token = authHeader.substring(7);
      const result = await this.validateFirebaseToken(token);

      if (!result.valid) {
        return res.status(401).json({ error: result.error });
      }

      // 사용자 정보를 request 객체에 추가
      (req as any).user = result.user;
      next();
    };
  }
}
```

### 6-2. 세션 관리
```typescript
// session-manager.ts
interface UserSession {
  userId: string;
  deviceId: string;
  deviceInfo: {
    platform: string;
    version: string;
    model?: string;
  };
  createdAt: Date;
  lastActiveAt: Date;
  ipAddress: string;
  userAgent: string;
  isActive: boolean;
}

class SessionManager {
  private redis: Redis;
  private readonly SESSION_TTL = 30 * 24 * 60 * 60; // 30일

  constructor(redisClient: Redis) {
    this.redis = redisClient;
  }

  async createSession(userId: string, deviceInfo: any, req: Request): Promise<string> {
    const sessionId = this.generateSessionId();

    const session: UserSession = {
      userId,
      deviceId: deviceInfo.deviceId,
      deviceInfo: {
        platform: deviceInfo.platform,
        version: deviceInfo.version,
        model: deviceInfo.model
      },
      createdAt: new Date(),
      lastActiveAt: new Date(),
      ipAddress: this.getClientIP(req),
      userAgent: req.get('User-Agent') || '',
      isActive: true
    };

    // Redis에 세션 저장
    const sessionKey = `session:${sessionId}`;
    await this.redis.setex(
      sessionKey,
      this.SESSION_TTL,
      JSON.stringify(session)
    );

    // 사용자의 활성 세션 목록에 추가
    const userSessionsKey = `user_sessions:${userId}`;
    await this.redis.sadd(userSessionsKey, sessionId);
    await this.redis.expire(userSessionsKey, this.SESSION_TTL);

    return sessionId;
  }

  async getSession(sessionId: string): Promise<UserSession | null> {
    const sessionKey = `session:${sessionId}`;
    const sessionData = await this.redis.get(sessionKey);

    if (!sessionData) {
      return null;
    }

    return JSON.parse(sessionData) as UserSession;
  }

  async updateLastActive(sessionId: string): Promise<void> {
    const session = await this.getSession(sessionId);
    if (!session) return;

    session.lastActiveAt = new Date();

    const sessionKey = `session:${sessionId}`;
    await this.redis.setex(
      sessionKey,
      this.SESSION_TTL,
      JSON.stringify(session)
    );
  }

  async getUserActiveSessions(userId: string): Promise<UserSession[]> {
    const userSessionsKey = `user_sessions:${userId}`;
    const sessionIds = await this.redis.smembers(userSessionsKey);

    const sessions: UserSession[] = [];

    for (const sessionId of sessionIds) {
      const session = await this.getSession(sessionId);
      if (session && session.isActive) {
        sessions.push(session);
      }
    }

    return sessions;
  }

  async revokeSession(sessionId: string): Promise<void> {
    const session = await this.getSession(sessionId);
    if (!session) return;

    // 세션 비활성화
    session.isActive = false;
    const sessionKey = `session:${sessionId}`;
    await this.redis.setex(
      sessionKey,
      this.SESSION_TTL,
      JSON.stringify(session)
    );

    // 사용자 세션 목록에서 제거
    const userSessionsKey = `user_sessions:${session.userId}`;
    await this.redis.srem(userSessionsKey, sessionId);
  }

  async revokeAllUserSessions(userId: string): Promise<void> {
    const sessions = await this.getUserActiveSessions(userId);

    for (const session of sessions) {
      await this.revokeSession(this.getSessionIdFromSession(session));
    }

    // 사용자 세션 목록 초기화
    const userSessionsKey = `user_sessions:${userId}`;
    await this.redis.del(userSessionsKey);
  }

  async cleanupExpiredSessions(): Promise<void> {
    // 만료된 세션들을 정리하는 배치 작업
    const pattern = 'session:*';
    const keys = await this.redis.keys(pattern);

    for (const key of keys) {
      const ttl = await this.redis.ttl(key);
      if (ttl === -2) { // 키가 만료됨
        const sessionId = key.replace('session:', '');
        console.log(`Cleaning up expired session: ${sessionId}`);
      }
    }
  }

  private generateSessionId(): string {
    return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getClientIP(req: Request): string {
    return (req.headers['x-forwarded-for'] as string)?.split(',')[0] ||
           req.connection.remoteAddress ||
           req.socket.remoteAddress ||
           'unknown';
  }
}
```

## 7. 보안 강화

### 7-1. Rate Limiting
```typescript
// rate-limiter.ts
import rateLimit from 'express-rate-limit';
import { RedisStore } from 'rate-limit-redis';

class AuthRateLimiter {
  private redis: Redis;

  constructor(redisClient: Redis) {
    this.redis = redisClient;
  }

  // 일반 로그인 시도 제한
  getLoginLimiter() {
    return rateLimit({
      store: new RedisStore({
        client: this.redis,
        prefix: 'login_limit:'
      }),
      windowMs: 15 * 60 * 1000, // 15분
      max: 5, // 최대 5회 시도
      message: {
        error: 'Too many login attempts',
        message: '로그인 시도 횟수를 초과했습니다. 15분 후 다시 시도해주세요.'
      },
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: (req) => {
        // IP + 이메일 조합으로 키 생성
        const email = req.body.email || 'unknown';
        const ip = req.ip || 'unknown';
        return `${ip}:${email}`;
      },
      onLimitReached: (req, res) => {
        console.warn(`Login rate limit exceeded:`, {
          ip: req.ip,
          email: req.body.email,
          userAgent: req.get('User-Agent')
        });
      }
    });
  }

  // 비밀번호 재설정 제한
  getPasswordResetLimiter() {
    return rateLimit({
      store: new RedisStore({
        client: this.redis,
        prefix: 'password_reset:'
      }),
      windowMs: 60 * 60 * 1000, // 1시간
      max: 3, // 최대 3회
      message: {
        error: 'Too many password reset attempts',
        message: '비밀번호 재설정 요청이 너무 많습니다. 1시간 후 다시 시도해주세요.'
      },
      keyGenerator: (req) => req.body.email || req.ip
    });
  }

  // 계정 생성 제한
  getSignupLimiter() {
    return rateLimit({
      store: new RedisStore({
        client: this.redis,
        prefix: 'signup_limit:'
      }),
      windowMs: 24 * 60 * 60 * 1000, // 24시간
      max: 3, // IP당 최대 3개 계정 생성
      message: {
        error: 'Too many signup attempts',
        message: '계정 생성 제한에 도달했습니다. 24시간 후 다시 시도해주세요.'
      },
      keyGenerator: (req) => req.ip
    });
  }
}
```

### 7-2. 이상 행동 탐지
```typescript
// anomaly-detector.ts
interface LoginAttempt {
  userId?: string;
  email?: string;
  ip: string;
  userAgent: string;
  location?: {
    country: string;
    city: string;
  };
  success: boolean;
  timestamp: Date;
}

interface AnomalyAlert {
  type: 'suspicious_location' | 'multiple_failures' | 'new_device' | 'brute_force';
  severity: 'low' | 'medium' | 'high';
  userId?: string;
  details: any;
  timestamp: Date;
}

class AnomalyDetector {
  private redis: Redis;

  constructor(redisClient: Redis) {
    this.redis = redisClient;
  }

  async analyzeLoginAttempt(attempt: LoginAttempt): Promise<AnomalyAlert[]> {
    const alerts: AnomalyAlert[] = [];

    // 1. 지리적 이상 감지
    if (attempt.userId) {
      const locationAlert = await this.checkSuspiciousLocation(attempt);
      if (locationAlert) alerts.push(locationAlert);
    }

    // 2. 연속 실패 감지
    const failureAlert = await this.checkMultipleFailures(attempt);
    if (failureAlert) alerts.push(failureAlert);

    // 3. 새로운 기기 감지
    if (attempt.success && attempt.userId) {
      const deviceAlert = await this.checkNewDevice(attempt);
      if (deviceAlert) alerts.push(deviceAlert);
    }

    // 4. 브루트포스 공격 감지
    const bruteForceAlert = await this.checkBruteForce(attempt);
    if (bruteForceAlert) alerts.push(bruteForceAlert);

    // 알림 발송
    for (const alert of alerts) {
      await this.sendSecurityAlert(alert);
    }

    return alerts;
  }

  private async checkSuspiciousLocation(attempt: LoginAttempt): Promise<AnomalyAlert | null> {
    if (!attempt.location || !attempt.userId) return null;

    const key = `user_locations:${attempt.userId}`;
    const recentLocations = await this.redis.lrange(key, 0, 9); // 최근 10개 위치

    // 기존 위치들과 비교
    const isSuspicious = !recentLocations.some(loc => {
      const location = JSON.parse(loc);
      return location.country === attempt.location!.country;
    });

    if (isSuspicious && recentLocations.length > 0) {
      return {
        type: 'suspicious_location',
        severity: 'high',
        userId: attempt.userId,
        details: {
          newLocation: attempt.location,
          previousLocations: recentLocations.slice(0, 3)
        },
        timestamp: new Date()
      };
    }

    // 위치 정보 저장
    await this.redis.lpush(key, JSON.stringify({
      country: attempt.location.country,
      city: attempt.location.city,
      timestamp: attempt.timestamp
    }));
    await this.redis.ltrim(key, 0, 9); // 최신 10개만 유지
    await this.redis.expire(key, 30 * 24 * 60 * 60); // 30일 보관

    return null;
  }

  private async checkMultipleFailures(attempt: LoginAttempt): Promise<AnomalyAlert | null> {
    if (attempt.success) return null;

    const key = `failed_attempts:${attempt.email || attempt.ip}`;
    const failCount = await this.redis.incr(key);
    await this.redis.expire(key, 60 * 60); // 1시간 TTL

    if (failCount >= 5) {
      return {
        type: 'multiple_failures',
        severity: 'medium',
        details: {
          attempts: failCount,
          email: attempt.email,
          ip: attempt.ip,
          userAgent: attempt.userAgent
        },
        timestamp: new Date()
      };
    }

    return null;
  }

  private async checkNewDevice(attempt: LoginAttempt): Promise<AnomalyAlert | null> {
    const key = `user_devices:${attempt.userId}`;
    const deviceFingerprint = this.generateDeviceFingerprint(attempt);

    const isKnownDevice = await this.redis.sismember(key, deviceFingerprint);

    if (!isKnownDevice) {
      // 새로운 기기 등록
      await this.redis.sadd(key, deviceFingerprint);
      await this.redis.expire(key, 90 * 24 * 60 * 60); // 90일 보관

      return {
        type: 'new_device',
        severity: 'low',
        userId: attempt.userId,
        details: {
          deviceInfo: {
            userAgent: attempt.userAgent,
            ip: attempt.ip,
            location: attempt.location
          }
        },
        timestamp: new Date()
      };
    }

    return null;
  }

  private async checkBruteForce(attempt: LoginAttempt): Promise<AnomalyAlert | null> {
    const key = `brute_force:${attempt.ip}`;
    const attempts = await this.redis.incr(key);
    await this.redis.expire(key, 60 * 60); // 1시간 TTL

    if (attempts >= 20) { // 1시간에 20회 이상
      return {
        type: 'brute_force',
        severity: 'high',
        details: {
          ip: attempt.ip,
          attempts,
          userAgent: attempt.userAgent
        },
        timestamp: new Date()
      };
    }

    return null;
  }

  private generateDeviceFingerprint(attempt: LoginAttempt): string {
    const crypto = require('crypto');
    const fingerprint = `${attempt.userAgent}|${attempt.ip}`;
    return crypto.createHash('sha256').update(fingerprint).digest('hex');
  }

  private async sendSecurityAlert(alert: AnomalyAlert): Promise<void> {
    // 보안 알림 발송 로직
    console.warn('Security Alert:', alert);

    if (alert.severity === 'high') {
      // 즉시 알림 (이메일, Slack 등)
      await this.sendImmediateAlert(alert);
    }

    // 보안 로그 저장
    await this.logSecurityEvent(alert);
  }
}
```

## 8. 모니터링 및 분석

### 8-1. 인증 메트릭 수집
```typescript
// auth-analytics.ts
interface AuthMetrics {
  totalSignups: number;
  totalLogins: number;
  socialLoginRatio: number;
  guestConversionRate: number;
  failedLoginRate: number;
  averageSessionDuration: number;
}

class AuthAnalytics {
  private postgresql: Pool;
  private redis: Redis;

  constructor(pgPool: Pool, redisClient: Redis) {
    this.postgresql = pgPool;
    this.redis = redisClient;
  }

  async recordAuthEvent(event: AuthEvent): Promise<void> {
    // 실시간 메트릭 업데이트
    await this.updateRealtimeMetrics(event);

    // 상세 로그 저장
    await this.saveAuthLog(event);
  }

  private async updateRealtimeMetrics(event: AuthEvent): Promise<void> {
    const today = new Date().toISOString().split('T')[0];
    const key = `auth_metrics:${today}`;

    switch (event.type) {
      case 'signup':
        await this.redis.hincrby(key, 'total_signups', 1);
        await this.redis.hincrby(key, `signups_${event.provider}`, 1);
        break;
      case 'signin':
        await this.redis.hincrby(key, 'total_logins', 1);
        await this.redis.hincrby(key, `logins_${event.provider}`, 1);
        break;
      case 'signin_failed':
        await this.redis.hincrby(key, 'failed_logins', 1);
        break;
      case 'guest_conversion':
        await this.redis.hincrby(key, 'guest_conversions', 1);
        break;
    }

    await this.redis.expire(key, 30 * 24 * 60 * 60); // 30일 보관
  }

  async getAuthMetrics(period: 'day' | 'week' | 'month'): Promise<AuthMetrics> {
    const endDate = new Date();
    const startDate = new Date();

    switch (period) {
      case 'day':
        startDate.setDate(endDate.getDate() - 1);
        break;
      case 'week':
        startDate.setDate(endDate.getDate() - 7);
        break;
      case 'month':
        startDate.setMonth(endDate.getMonth() - 1);
        break;
    }

    const query = `
      SELECT
        COUNT(CASE WHEN type = 'signup' THEN 1 END) as total_signups,
        COUNT(CASE WHEN type = 'signin' THEN 1 END) as total_logins,
        COUNT(CASE WHEN type = 'signin' AND provider != 'email' THEN 1 END) as social_logins,
        COUNT(CASE WHEN type = 'guest_conversion' THEN 1 END) as guest_conversions,
        COUNT(CASE WHEN type = 'signin_failed' THEN 1 END) as failed_logins,
        CASE
          WHEN COUNT(CASE WHEN type = 'signin' THEN 1 END) > 0
          THEN (COUNT(CASE WHEN type = 'signin' AND provider != 'email' THEN 1 END)::float / COUNT(CASE WHEN type = 'signin' THEN 1 END) * 100)
          ELSE 0
        END as social_login_ratio,
        CASE
          WHEN (COUNT(CASE WHEN type = 'signin' THEN 1 END) + COUNT(CASE WHEN type = 'signin_failed' THEN 1 END)) > 0
          THEN (COUNT(CASE WHEN type = 'signin_failed' THEN 1 END)::float / (COUNT(CASE WHEN type = 'signin' THEN 1 END) + COUNT(CASE WHEN type = 'signin_failed' THEN 1 END)) * 100)
          ELSE 0
        END as failed_login_rate
      FROM auth_logs
      WHERE timestamp >= $1 AND timestamp <= $2
    `;

    const result = await this.postgresql.query(query, [startDate, endDate]);

    return result[0] || this.getDefaultMetrics();
  }

  async getTopFailureReasons(): Promise<{ reason: string; count: number }[]> {
    const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

    const query = `
      SELECT error_code as reason, COUNT(*) as count
      FROM auth_logs
      WHERE type = 'signin_failed' AND timestamp >= $1
      GROUP BY error_code
      ORDER BY count DESC
      LIMIT 10
    `;

    const result = await this.postgresql.query(query, [oneWeekAgo]);
    return result.rows;
  }

  async generateAuthReport(period: 'daily' | 'weekly' | 'monthly'): Promise<AuthReport> {
    const metrics = await this.getAuthMetrics(period);
    const failureReasons = await this.getTopFailureReasons();
    const conversionFunnel = await this.getConversionFunnel();

    return {
      period,
      generatedAt: new Date(),
      metrics,
      failureReasons,
      conversionFunnel,
      recommendations: this.generateRecommendations(metrics)
    };
  }

  private generateRecommendations(metrics: AuthMetrics): string[] {
    const recommendations: string[] = [];

    if (metrics.failedLoginRate > 10) {
      recommendations.push('로그인 실패율이 높습니다. UX 개선을 고려하세요.');
    }

    if (metrics.socialLoginRatio < 60) {
      recommendations.push('소셜 로그인 사용률을 높이기 위한 UI 개선이 필요합니다.');
    }

    if (metrics.guestConversionRate < 20) {
      recommendations.push('게스트 사용자의 회원 전환율 개선이 필요합니다.');
    }

    return recommendations;
  }
}
```

## 9. 에러 처리 및 복구

### 9-1. 에러 분류 및 처리
```typescript
// auth-error-handler.ts
enum AuthErrorType {
  NETWORK_ERROR = 'network_error',
  INVALID_CREDENTIALS = 'invalid_credentials',
  ACCOUNT_DISABLED = 'account_disabled',
  TOO_MANY_REQUESTS = 'too_many_requests',
  TOKEN_EXPIRED = 'token_expired',
  PROVIDER_ERROR = 'provider_error',
  UNKNOWN_ERROR = 'unknown_error'
}

interface AuthError {
  type: AuthErrorType;
  code: string;
  message: string;
  userMessage: string;
  retryable: boolean;
  suggestions?: string[];
}

class AuthErrorHandler {
  private errorMap: Map<string, AuthError> = new Map();

  constructor() {
    this.initializeErrorMap();
  }

  private initializeErrorMap(): void {
    // Firebase Auth 에러 매핑
    this.errorMap.set('auth/user-not-found', {
      type: AuthErrorType.INVALID_CREDENTIALS,
      code: 'auth/user-not-found',
      message: 'User not found',
      userMessage: '등록되지 않은 이메일입니다.',
      retryable: false,
      suggestions: ['이메일 주소를 확인해주세요', '회원가입하기']
    });

    this.errorMap.set('auth/wrong-password', {
      type: AuthErrorType.INVALID_CREDENTIALS,
      code: 'auth/wrong-password',
      message: 'Wrong password',
      userMessage: '비밀번호가 일치하지 않습니다.',
      retryable: false,
      suggestions: ['비밀번호를 확인해주세요', '비밀번호 찾기']
    });

    this.errorMap.set('auth/too-many-requests', {
      type: AuthErrorType.TOO_MANY_REQUESTS,
      code: 'auth/too-many-requests',
      message: 'Too many failed login attempts',
      userMessage: '로그인 시도 횟수를 초과했습니다.',
      retryable: true,
      suggestions: ['잠시 후 다시 시도해주세요', '비밀번호 재설정하기']
    });

    this.errorMap.set('auth/network-request-failed', {
      type: AuthErrorType.NETWORK_ERROR,
      code: 'auth/network-request-failed',
      message: 'Network error',
      userMessage: '네트워크 연결을 확인해주세요.',
      retryable: true,
      suggestions: ['인터넷 연결을 확인해주세요', '다시 시도하기']
    });
  }

  handleAuthError(error: any): AuthError {
    const mappedError = this.errorMap.get(error.code);

    if (mappedError) {
      return mappedError;
    }

    // 매핑되지 않은 에러는 일반적인 에러로 처리
    return {
      type: AuthErrorType.UNKNOWN_ERROR,
      code: error.code || 'unknown',
      message: error.message || 'Unknown error',
      userMessage: '로그인 중 오류가 발생했습니다.',
      retryable: true,
      suggestions: ['다시 시도해주세요', '문제가 지속되면 고객센터에 문의하세요']
    };
  }

  async logError(error: AuthError, context: any): Promise<void> {
    const errorLog = {
      type: error.type,
      code: error.code,
      message: error.message,
      context,
      timestamp: new Date(),
      userId: context.userId || null,
      ip: context.ip || null,
      userAgent: context.userAgent || null
    };

    // 에러 로그 저장
    await this.saveErrorLog(errorLog);

    // 심각한 에러의 경우 알림 발송
    if (this.isCriticalError(error)) {
      await this.sendCriticalErrorAlert(errorLog);
    }
  }

  private isCriticalError(error: AuthError): boolean {
    return error.type === AuthErrorType.ACCOUNT_DISABLED ||
           error.type === AuthErrorType.PROVIDER_ERROR;
  }

  async retryWithBackoff<T>(
    operation: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;

        const authError = this.handleAuthError(error);
        if (!authError.retryable || attempt === maxRetries) {
          throw error;
        }

        // 지수 백오프
        const delay = baseDelay * Math.pow(2, attempt);
        await this.sleep(delay);
      }
    }

    throw lastError!;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## 10. 테스트 전략

### 10-1. 단위 테스트
```typescript
// auth-service.test.ts
describe('AuthService', () => {
  let authService: FirebaseAuthService;
  let mockAuth: jest.Mocked<Auth>;

  beforeEach(() => {
    mockAuth = createMockAuth();
    authService = new FirebaseAuthService(mockAuth);
  });

  describe('Email Authentication', () => {
    it('should create user with valid email and password', async () => {
      const signUpData = {
        email: 'test@example.com',
        password: 'password123',
        displayName: 'Test User',
        acceptedTerms: true
      };

      const mockUserCredential = createMockUserCredential();
      mockAuth.createUserWithEmailAndPassword.mockResolvedValue(mockUserCredential);

      const result = await authService.signUp(signUpData);

      expect(result.user.email).toBe(signUpData.email);
      expect(mockAuth.createUserWithEmailAndPassword).toHaveBeenCalledWith(
        signUpData.email,
        signUpData.password
      );
    });

    it('should reject weak passwords', async () => {
      const signUpData = {
        email: 'test@example.com',
        password: '123', // 너무 짧음
        displayName: 'Test User',
        acceptedTerms: true
      };

      await expect(authService.signUp(signUpData)).rejects.toThrow(
        '비밀번호는 8자 이상, 영문과 숫자를 포함해야 합니다.'
      );
    });

    it('should handle login with correct credentials', async () => {
      const loginData = {
        email: 'test@example.com',
        password: 'password123',
        rememberMe: true
      };

      const mockUserCredential = createMockUserCredential();
      mockAuth.signInWithEmailAndPassword.mockResolvedValue(mockUserCredential);

      const result = await authService.signIn(loginData);

      expect(result.user.email).toBe(loginData.email);
    });
  });

  describe('Social Authentication', () => {
    it('should handle Google sign in', async () => {
      const mockUserCredential = createMockUserCredential({
        providerId: 'google.com'
      });

      mockAuth.signInWithPopup.mockResolvedValue(mockUserCredential);

      const result = await authService.signInWithProvider('google');

      expect(result.user.providerId).toBe('google.com');
    });

    it('should handle social auth errors gracefully', async () => {
      const error = new Error('popup_closed_by_user');
      error.code = 'auth/popup-closed-by-user';

      mockAuth.signInWithPopup.mockRejectedValue(error);

      await expect(authService.signInWithProvider('google')).rejects.toThrow();
    });
  });

  describe('Guest Mode', () => {
    it('should create anonymous user', async () => {
      const mockUserCredential = createMockUserCredential({
        isAnonymous: true
      });

      mockAuth.signInAnonymously.mockResolvedValue(mockUserCredential);

      const result = await authService.signInAsGuest();

      expect(result.user.isAnonymous).toBe(true);
    });

    it('should convert guest to regular user', async () => {
      const mockGuestUser = createMockUser({ isAnonymous: true });
      const mockCredential = createMockCredential();
      const mockUserCredential = createMockUserCredential({
        isAnonymous: false
      });

      mockAuth.linkWithCredential.mockResolvedValue(mockUserCredential);

      const result = await authService.convertGuestToUser(
        mockGuestUser,
        mockCredential
      );

      expect(result.user.isAnonymous).toBe(false);
    });
  });
});
```

### 10-2. 통합 테스트
```typescript
// auth-integration.test.ts
describe('Authentication Integration', () => {
  let testServer: TestServer;
  let authService: AuthService;
  let testUser: TestUser;

  beforeAll(async () => {
    testServer = await createTestServer();
    authService = testServer.get(AuthService);
  });

  beforeEach(async () => {
    testUser = await createTestUser();
  });

  afterEach(async () => {
    await cleanupTestUser(testUser);
  });

  describe('Complete Authentication Flow', () => {
    it('should complete full signup and login flow', async () => {
      // 1. 회원가입
      const signupResult = await authService.signUp({
        email: testUser.email,
        password: testUser.password,
        displayName: testUser.displayName,
        acceptedTerms: true
      });

      expect(signupResult.user.email).toBe(testUser.email);

      // 2. 이메일 인증
      const verificationToken = await getEmailVerificationToken(testUser.email);
      await authService.verifyEmail(verificationToken);

      // 3. 로그인
      const loginResult = await authService.signIn({
        email: testUser.email,
        password: testUser.password,
        rememberMe: false
      });

      expect(loginResult.user.emailVerified).toBe(true);
    });

    it('should maintain session across app restarts', async () => {
      // 로그인
      await authService.signIn({
        email: testUser.email,
        password: testUser.password,
        rememberMe: true
      });

      // 앱 재시작 시뮬레이션
      const newAuthService = testServer.get(AuthService);
      await newAuthService.initialize();

      // 자동 로그인 확인
      const currentUser = newAuthService.getCurrentUser();
      expect(currentUser).not.toBeNull();
      expect(currentUser?.email).toBe(testUser.email);
    });

    it('should handle guest to user conversion', async () => {
      // 게스트 로그인
      const guestResult = await authService.signInAsGuest();
      expect(guestResult.user.isAnonymous).toBe(true);

      // 게스트 데이터 생성
      await authService.saveGuestData(guestResult.user.uid, {
        places: [createTestPlace()],
        courses: [createTestCourse()]
      });

      // 정규 계정으로 전환
      const conversionResult = await authService.convertGuestToUser({
        email: testUser.email,
        password: testUser.password,
        displayName: testUser.displayName
      });

      expect(conversionResult.user.isAnonymous).toBe(false);
      expect(conversionResult.user.email).toBe(testUser.email);

      // 데이터 이전 확인
      const userData = await authService.getUserData(conversionResult.user.uid);
      expect(userData.places).toHaveLength(1);
      expect(userData.courses).toHaveLength(1);
    });
  });

  describe('Security and Rate Limiting', () => {
    it('should block excessive login attempts', async () => {
      const attempts = Array(6).fill(null).map(() =>
        authService.signIn({
          email: testUser.email,
          password: 'wrongpassword',
          rememberMe: false
        }).catch(() => {}) // 실패 무시
      );

      await Promise.all(attempts);

      // 7번째 시도는 rate limit에 걸려야 함
      await expect(authService.signIn({
        email: testUser.email,
        password: testUser.password, // 올바른 비밀번호라도
        rememberMe: false
      })).rejects.toThrow(/rate limit/i);
    });

    it('should detect suspicious login patterns', async () => {
      const anomalyDetector = testServer.get(AnomalyDetector);

      // 다른 지역에서 로그인 시도 시뮬레이션
      const normalLogin = {
        userId: testUser.id,
        ip: '192.168.1.1',
        location: { country: 'KR', city: 'Seoul' }
      };

      const suspiciousLogin = {
        userId: testUser.id,
        ip: '203.0.113.1',
        location: { country: 'US', city: 'New York' }
      };

      await anomalyDetector.analyzeLoginAttempt(normalLogin);
      const alerts = await anomalyDetector.analyzeLoginAttempt(suspiciousLogin);

      expect(alerts).toContainEqual(
        expect.objectContaining({
          type: 'suspicious_location',
          severity: 'high'
        })
      );
    });
  });
});
```

## Firebase → Supabase 전환 요약

### 주요 변경 사항

#### 1. 인증 시스템
- **Firebase Authentication** → **Supabase Auth (GoTrue)**
- **Firebase Admin SDK** → **Supabase Python Client**
- **Custom Claims** → **user_metadata / app_metadata**

#### 2. 데이터베이스
- **Firestore** → **PostgreSQL** (이미 프로젝트에서 사용 중)
- **Firestore Security Rules** → **Row Level Security (RLS)**
- **Firebase Realtime Database** → **Supabase Realtime** (필요시)

#### 3. 인증 제공업체
| 제공업체 | Firebase | Supabase |
|---------|----------|----------|
| Google | ✅ OAuth 2.0 | ✅ OAuth 2.0 |
| Apple | ✅ Sign in with Apple | ✅ Sign in with Apple |
| Kakao | 🔄 Custom Token | ✅ OAuth 연동 |
| Email | ✅ 기본 제공 | ✅ 기본 제공 |
| Anonymous | ✅ 익명 인증 | ✅ Anonymous 사용자 |

#### 4. API 변경
```python
# Firebase (기존)
from firebase_admin import auth
user = auth.get_user(uid)
custom_claims = user.custom_claims

# Supabase (신규)
from supabase import create_client
supabase = create_client(url, key)
user = supabase.auth.admin.get_user_by_id(user_id)
app_metadata = user.user.app_metadata
```

#### 5. 보안 정책
```sql
-- Firebase Security Rules (기존)
match /users/{userId} {
  allow read, write: if request.auth.uid == userId;
}

-- PostgreSQL RLS (신규)
CREATE POLICY "Users can access own data"
  ON public.users
  FOR ALL
  USING (auth.uid() = id);
```

### 마이그레이션 체크리스트

- [x] Supabase 프로젝트 생성
- [x] PostgreSQL 스키마 설계 (RLS 포함)
- [x] OAuth 제공업체 설정 (Google, Apple, Kakao)
- [x] 인증 서비스 FastAPI 통합
- [ ] 기존 사용자 데이터 마이그레이션
- [ ] 세션 관리 시스템 구축
- [ ] 테스트 및 배포

이제 Supabase Auth 기반 인증 시스템의 TRD 작성이 완료되었습니다.
