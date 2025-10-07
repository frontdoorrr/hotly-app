# Firebase Authentication 마이그레이션 가이드

## 개요

Hotly 앱의 인증 시스템이 Supabase Auth에서 Firebase Authentication으로 마이그레이션되었습니다.

## 주요 변경사항

### 1. 인증 공급자 변경
- **이전**: Supabase Authentication
- **현재**: Firebase Authentication
- **이유**: 프론트엔드(Flutter)와 백엔드 기술 스택 통일, AWS RDS 호환성

### 2. 아키텍처 변경

#### 인증 플로우
```
클라이언트 (Flutter)
  ↓ Firebase SDK로 소셜 로그인 (Google/Apple/Kakao)
  ↓ ID Token 발급받음
  ↓
백엔드 (FastAPI)
  ↓ POST /api/v1/auth/social-login
  ↓ Firebase Admin SDK로 ID Token 검증
  ↓ 커스텀 클레임 설정 (role, permissions 등)
  ↓ 세션 생성 및 관리
  ↓
응답: LoginResponse
  - user_profile
  - access_token (Firebase ID Token)
  - refresh_token
  - is_new_user
```

### 3. API 엔드포인트 변경

#### 새로운 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/auth/social-login` | POST | 소셜 로그인 (Google/Apple/Kakao) |
| `/api/v1/auth/verify-token` | POST | Firebase ID 토큰 검증 |
| `/api/v1/auth/refresh` | POST | 토큰 갱신 |
| `/api/v1/auth/anonymous` | POST | 익명 사용자 생성 (게스트 모드) |
| `/api/v1/auth/upgrade` | POST | 익명 → 인증 사용자 업그레이드 |
| `/api/v1/auth/signout` | POST | 로그아웃 |
| `/api/v1/auth/me` | GET | 현재 사용자 정보 조회 |

#### 제거된 엔드포인트
- `/api/v1/auth/signup` - Firebase 클라이언트 SDK에서 처리
- `/api/v1/auth/signin` - Firebase 클라이언트 SDK에서 처리
- `/api/v1/auth/oauth/{provider}` - `/social-login`으로 통합

## 설정 방법

### 1. Firebase 프로젝트 설정

1. [Firebase Console](https://console.firebase.google.com/)에서 프로젝트 생성
2. Authentication 활성화
3. 소셜 로그인 공급자 설정:
   - Google
   - Apple
   - Kakao (커스텀 OAuth 공급자)

### 2. 서비스 계정 키 다운로드

1. Firebase Console → 프로젝트 설정 → 서비스 계정
2. "새 비공개 키 생성" 클릭
3. JSON 파일 다운로드 후 안전한 위치에 저장

### 3. 환경 변수 설정

`.env` 파일에 다음 값 설정:

```bash
# Firebase Authentication
FIREBASE_PROJECT_ID="your-project-id"
FIREBASE_API_KEY="your-api-key"
FIREBASE_AUTH_DOMAIN="your-project.firebaseapp.com"
FIREBASE_CREDENTIALS_PATH="path/to/service-account-key.json"

# OAuth 공급자
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
APPLE_CLIENT_ID="com.your.app.identifier"
KAKAO_CLIENT_ID="your-kakao-app-key"

# Auth Rate Limiting
MAX_LOGIN_ATTEMPTS_PER_MINUTE=10
MAX_TOKEN_REFRESH_PER_HOUR=60
```

### 4. 의존성 확인

`pyproject.toml`에 Firebase Admin SDK가 포함되어 있는지 확인:

```toml
[tool.poetry.dependencies]
firebase-admin = "^6.4.0"
```

설치:
```bash
cd backend
poetry install
```

## 클라이언트 통합 가이드 (Flutter)

### 1. Firebase SDK 설정

`pubspec.yaml`:
```yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_auth: ^4.15.0
  google_sign_in: ^6.1.6
  sign_in_with_apple: ^5.0.0
```

### 2. 소셜 로그인 구현 예시

#### Google 로그인
```dart
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';

Future<User?> signInWithGoogle() async {
  // Google Sign In
  final GoogleSignInAccount? googleUser = await GoogleSignIn().signIn();
  final GoogleSignInAuthentication? googleAuth =
      await googleUser?.authentication;

  // Firebase 인증
  final credential = GoogleAuthProvider.credential(
    accessToken: googleAuth?.accessToken,
    idToken: googleAuth?.idToken,
  );

  final userCredential =
      await FirebaseAuth.instance.signInWithCredential(credential);

  // ID Token 가져오기
  final idToken = await userCredential.user?.getIdToken();

  // 백엔드에 전송
  final response = await http.post(
    Uri.parse('$baseUrl/api/v1/auth/social-login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'provider': 'google',
      'idToken': idToken,
    }),
  );

  return userCredential.user;
}
```

#### Kakao 로그인
```dart
import 'package:kakao_flutter_sdk/kakao_flutter_sdk.dart';

Future<User?> signInWithKakao() async {
  try {
    // Kakao 로그인
    OAuthToken token = await UserApi.instance.loginWithKakaoAccount();

    // 백엔드에서 Kakao 토큰 검증 후 Firebase 커스텀 토큰 발급
    final response = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/social-login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'provider': 'kakao',
        'accessToken': token.accessToken,
      }),
    );

    final data = jsonDecode(response.body);
    final customToken = data['customToken'];

    // Firebase에 커스텀 토큰으로 로그인
    final userCredential = await FirebaseAuth.instance
        .signInWithCustomToken(customToken);

    return userCredential.user;
  } catch (error) {
    print('Kakao login failed: $error');
    return null;
  }
}
```

### 3. 인증 상태 관리

```dart
import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // 현재 사용자 스트림
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  // 현재 사용자
  User? get currentUser => _auth.currentUser;

  // ID Token 가져오기 (API 호출 시 사용)
  Future<String?> getIdToken() async {
    return await _auth.currentUser?.getIdToken();
  }

  // 로그아웃
  Future<void> signOut() async {
    // 백엔드에 로그아웃 요청
    await http.post(
      Uri.parse('$baseUrl/api/v1/auth/signout'),
      headers: {
        'Authorization': 'Bearer ${await getIdToken()}',
      },
    );

    // Firebase 로그아웃
    await _auth.signOut();
  }
}
```

### 4. API 호출 시 인증 헤더 추가

```dart
Future<Response> authenticatedRequest(String endpoint) async {
  final idToken = await AuthService().getIdToken();

  return await http.get(
    Uri.parse('$baseUrl$endpoint'),
    headers: {
      'Authorization': 'Bearer $idToken',
      'Content-Type': 'application/json',
    },
  );
}
```

## 보안 고려사항

### 1. Firebase 규칙 설정

Firestore Security Rules 예시:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 인증된 사용자만 자신의 데이터 접근 가능
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // 관리자만 접근 가능
    match /admin/{document=**} {
      allow read, write: if request.auth.token.role == 'admin';
    }
  }
}
```

### 2. Custom Claims 설정

백엔드에서 사용자 역할 설정:
```python
from firebase_admin import auth

# 관리자 역할 부여
auth.set_custom_user_claims(uid, {'role': 'admin'})

# 권한 부여
auth.set_custom_user_claims(uid, {
    'role': 'user',
    'subscriptionLevel': 'premium'
})
```

### 3. Rate Limiting

Firebase Auth는 자동으로 rate limiting을 제공하지만, 추가 보호를 위해 백엔드에서도 구현:

```python
# app/core/config.py에 설정됨
MAX_LOGIN_ATTEMPTS_PER_MINUTE = 10
MAX_TOKEN_REFRESH_PER_HOUR = 60
```

## 마이그레이션 체크리스트

- [ ] Firebase 프로젝트 생성 및 설정
- [ ] 서비스 계정 키 다운로드 및 안전한 저장
- [ ] 환경 변수 설정 (`.env` 파일)
- [ ] 소셜 로그인 공급자 설정 (Google, Apple, Kakao)
- [ ] Flutter 앱에 Firebase SDK 통합
- [ ] 소셜 로그인 UI 구현
- [ ] 인증 상태 관리 구현
- [ ] API 호출 시 인증 헤더 추가
- [ ] 기존 사용자 데이터 마이그레이션 (필요시)
- [ ] 테스트 (단위 테스트, 통합 테스트, E2E 테스트)
- [ ] Firebase Security Rules 설정
- [ ] Custom Claims 설정 로직 구현
- [ ] 프로덕션 배포

## 트러블슈팅

### 문제: "Firebase credentials not found"

**해결방법**:
1. `FIREBASE_CREDENTIALS_PATH` 환경 변수가 올바른 경로를 가리키는지 확인
2. 서비스 계정 키 파일이 존재하는지 확인
3. 파일 권한 확인 (읽기 권한 필요)

### 문제: "Token verification failed"

**해결방법**:
1. Firebase 프로젝트 ID가 일치하는지 확인
2. ID 토큰이 만료되지 않았는지 확인 (1시간 유효)
3. 클라이언트와 서버의 Firebase 프로젝트가 동일한지 확인

### 문제: "Social login not working"

**해결방법**:
1. Firebase Console에서 해당 로그인 공급자가 활성화되어 있는지 확인
2. OAuth 클라이언트 ID가 올바른지 확인
3. 앱의 SHA-1/SHA-256 지문이 Firebase에 등록되어 있는지 확인 (Android)
4. Bundle ID가 Firebase에 등록되어 있는지 확인 (iOS)

## 참고 자료

- [Firebase Authentication 문서](https://firebase.google.com/docs/auth)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
- [FlutterFire 문서](https://firebase.flutter.dev/)
- [Google Sign-In for Flutter](https://pub.dev/packages/google_sign_in)
- [Sign in with Apple for Flutter](https://pub.dev/packages/sign_in_with_apple)
- [Kakao Flutter SDK](https://pub.dev/packages/kakao_flutter_sdk)

## 지원

문제가 발생하면 다음을 확인하세요:
1. Firebase Console의 Authentication 로그
2. 백엔드 로그 (`LOG_LEVEL=DEBUG` 설정)
3. Flutter 앱의 디버그 콘솔

추가 도움이 필요하면 개발팀에 문의하세요.
