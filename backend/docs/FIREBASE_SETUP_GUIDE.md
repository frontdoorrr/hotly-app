# Firebase 설정 가이드

## 개요

이 문서는 Hotly 앱에서 Firebase Authentication을 사용하기 위한 설정 방법을 안내합니다.

## 1. Firebase 프로젝트 생성

1. [Firebase Console](https://console.firebase.google.com/) 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력: `hotly-app-{environment}` (예: `hotly-app-dev`, `hotly-app-prod`)
4. Google Analytics 설정 (선택사항)
5. 프로젝트 생성 완료

## 2. iOS 앱 설정

### 2.1 iOS 앱 추가

1. Firebase Console > 프로젝트 설정 > "iOS 앱 추가" 클릭
2. iOS 번들 ID 입력: `com.hotly.hotly_app`
3. 앱 닉네임: `Hotly iOS`
4. App Store ID: (배포 후 입력)

### 2.2 GoogleService-Info.plist 다운로드

1. Firebase Console에서 `GoogleService-Info.plist` 다운로드
2. 파일을 다음 위치에 저장:
   ```
   frontend/ios/Runner/GoogleService-Info.plist
   ```
3. ✅ 파일이 이미 존재하는지 확인: **완료**

### 2.3 Xcode 프로젝트 설정

1. Xcode에서 `frontend/ios/Runner.xcworkspace` 열기
2. Runner 프로젝트 선택 > Signing & Capabilities
3. Bundle Identifier 확인: `com.hotly.hotly_app`

## 3. Android 앱 설정

### 3.1 Android 앱 추가

1. Firebase Console > 프로젝트 설정 > "Android 앱 추가" 클릭
2. Android 패키지 이름 입력: `com.hotly.hotly_app`
3. 앱 닉네임: `Hotly Android`
4. 디버그 서명 인증서 SHA-1 (선택사항):
   ```bash
   cd frontend/android
   keytool -list -v -keystore app/debug.keystore -alias androiddebugkey -storepass android -keypass android
   ```

### 3.2 google-services.json 다운로드

1. Firebase Console에서 `google-services.json` 다운로드
2. **🚨 중요**: 파일을 다음 위치에 저장:
   ```
   frontend/android/app/google-services.json
   ```
3. ❌ **현재 상태**: 파일이 누락되어 있습니다

### 3.3 Android 설정 확인

파일 위치를 확인하세요:
```
frontend/android/app/google-services.json  ← 이 파일 필요!
```

build.gradle에 플러그인이 이미 추가되어 있습니다:
```kotlin
// frontend/android/app/build.gradle.kts
plugins {
    id("com.google.gms.google-services")  // ✅ 이미 설정됨
}
```

## 4. Firebase Authentication 활성화

### 4.1 소셜 로그인 공급자 활성화

1. Firebase Console > Authentication > Sign-in method
2. 다음 공급자 활성화:

#### Google Sign-In
- ✅ "Google" 활성화
- 프로젝트 지원 이메일 설정
- 웹 클라이언트 ID는 자동 생성됨

#### Apple Sign-In
- ✅ "Apple" 활성화
- iOS Bundle ID: `com.hotly.hotly_app`
- Service ID: Firebase에서 자동 생성
- Team ID: Apple Developer 계정에서 확인

#### Kakao Sign-In (Custom OAuth)
Kakao는 Custom OAuth Provider로 설정:
1. [Kakao Developers](https://developers.kakao.com/) 에서 앱 생성
2. REST API 키 복사
3. Backend에서 Kakao 토큰 검증 후 Firebase Custom Token 발급

### 4.2 익명 인증 활성화 (선택사항)

게스트 모드 기능을 사용하려면:
1. Firebase Console > Authentication > Sign-in method
2. "익명" 활성화

## 5. Backend 설정

### 5.1 서비스 계정 키 생성

1. Firebase Console > 프로젝트 설정 > 서비스 계정
2. "새 비공개 키 생성" 클릭
3. JSON 파일 다운로드
4. **🚨 중요**: 파일을 안전한 위치에 저장 (절대 Git에 커밋하지 말 것)

### 5.2 환경 변수 설정

`backend/.env` 파일 생성 (`.env.example` 참고):

```bash
# Firebase Authentication Configuration
FIREBASE_PROJECT_ID="your-firebase-project-id"
FIREBASE_API_KEY="your-firebase-api-key"
FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
FIREBASE_CREDENTIALS_PATH="path/to/service-account-key.json"

# OAuth Providers
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
APPLE_CLIENT_ID="com.hotly.hotly_app"
KAKAO_CLIENT_ID="your-kakao-app-key"

# Auth Rate Limiting
MAX_LOGIN_ATTEMPTS_PER_MINUTE=10
MAX_TOKEN_REFRESH_PER_HOUR=60
```

### 5.3 서비스 계정 키 파일 위치

다음 중 하나의 방법으로 서비스 계정 키 설정:

**방법 1: 파일 경로 (개발 환경 권장)**
```bash
FIREBASE_CREDENTIALS_PATH="./config/firebase-service-account.json"
```

**방법 2: JSON 문자열 (프로덕션/클라우드 환경 권장)**
```bash
FIREBASE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'
```

## 6. Frontend 설정

### 6.1 환경 변수 설정

`.env.dev`, `.env.staging`, `.env.prod` 파일 생성:

```bash
# ===== Firebase Configuration =====
FIREBASE_PROJECT_ID=hotly-app-dev

# ===== Kakao Configuration =====
KAKAO_NATIVE_APP_KEY=your_kakao_native_app_key
KAKAO_MAP_APP_KEY=your_kakao_map_app_key

# ===== Social Login Configuration =====
GOOGLE_CLIENT_ID_IOS=your-google-client-id-ios.apps.googleusercontent.com
GOOGLE_CLIENT_ID_ANDROID=your-google-client-id-android.apps.googleusercontent.com
APPLE_CLIENT_ID=com.hotly.hotly_app
```

### 6.2 Firebase SDK 초기화

이미 구현되어 있습니다:
- `frontend/lib/firebase_options.dart`: ✅ FlutterFire CLI로 생성됨
- `frontend/lib/core/auth/firebase_auth_service.dart`: ✅ 인증 서비스 구현 완료

## 7. 빌드 및 실행

### 7.1 iOS 빌드

```bash
cd frontend
flutter clean
flutter pub get
cd ios
pod install
cd ..
flutter run -d ios
```

### 7.2 Android 빌드

**🚨 주의**: `google-services.json` 파일이 있어야 빌드 가능!

```bash
cd frontend
flutter clean
flutter pub get
flutter run -d android
```

빌드 오류 발생 시:
```
File google-services.json is missing. The Google Services Plugin cannot function without it.
```
→ 위 3.2 단계 참조하여 파일 추가

## 8. 테스트

### 8.1 로그인 테스트

1. 앱 실행
2. Google/Apple/Kakao 로그인 버튼 클릭
3. 소셜 로그인 인증 진행
4. Firebase Console > Authentication > Users에서 사용자 확인

### 8.2 토큰 확인

```dart
final authService = FirebaseAuthService();
final token = await authService.getIdToken();
print('ID Token: $token');
```

## 9. 보안 체크리스트

- [ ] `google-services.json`이 `.gitignore`에 포함되었는지 확인
- [ ] `GoogleService-Info.plist`가 `.gitignore`에 포함되었는지 확인
- [ ] Firebase 서비스 계정 키가 Git에 커밋되지 않았는지 확인
- [ ] 환경 변수 파일 (`.env`)이 `.gitignore`에 포함되었는지 확인
- [ ] Firebase Console에서 승인된 도메인 설정
- [ ] Firebase Security Rules 설정 (Firestore 사용 시)
- [ ] API 키 제한 설정 (Firebase Console > 프로젝트 설정 > 일반)

## 10. 프로덕션 배포

### 10.1 별도 Firebase 프로젝트 생성

개발/스테이징/프로덕션 환경별로 별도 Firebase 프로젝트 생성 권장:
- `hotly-app-dev`
- `hotly-app-staging`
- `hotly-app-prod`

### 10.2 환경별 설정 파일

```
frontend/
  .env.dev         → hotly-app-dev
  .env.staging     → hotly-app-staging
  .env.prod        → hotly-app-prod
```

### 10.3 Flutter 빌드 플레이버

```bash
# Development
flutter build apk --flavor dev --dart-define-from-file=.env.dev

# Production
flutter build apk --flavor prod --dart-define-from-file=.env.prod
```

## 트러블슈팅

### 문제: "Firebase credentials not found"

**원인**: 서비스 계정 키 파일 경로가 잘못되었거나 파일이 없음

**해결**:
1. `FIREBASE_CREDENTIALS_PATH` 환경 변수 확인
2. 파일 존재 여부 확인
3. 파일 권한 확인 (읽기 권한 필요)

### 문제: "google-services.json is missing"

**원인**: Android 빌드 시 `google-services.json` 파일 누락

**해결**:
1. Firebase Console에서 파일 다운로드
2. `frontend/android/app/google-services.json`에 저장
3. `flutter clean && flutter pub get`
4. 재빌드

### 문제: "Token verification failed"

**원인**: ID 토큰이 만료되었거나 프로젝트 ID가 일치하지 않음

**해결**:
1. Firebase 프로젝트 ID 확인
2. ID 토큰 만료 시간 확인 (기본 1시간)
3. 토큰 갱신:
   ```dart
   final newToken = await authService.refreshIdToken();
   ```

## 참고 자료

- [Firebase 공식 문서](https://firebase.google.com/docs)
- [FlutterFire 문서](https://firebase.flutter.dev/)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [Hotly App Firebase 마이그레이션 가이드](./FIREBASE_MIGRATION.md)

## 지원

문제가 발생하면:
1. Firebase Console의 Authentication 로그 확인
2. 백엔드 로그 확인 (`LOG_LEVEL=DEBUG`)
3. Flutter 앱 디버그 콘솔 확인
4. 개발팀에 문의
