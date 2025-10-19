# Firebase Authentication 환경 설정 가이드

이 문서는 **hotly-app** 프로젝트의 Firebase Authentication 설정을 처음부터 끝까지 안내합니다.

---

## 1. Firebase 프로젝트 생성

### 1-1. Firebase Console 접속
1. https://console.firebase.google.com 접속
2. Google 계정으로 로그인
3. "프로젝트 추가" 버튼 클릭

### 1-2. 프로젝트 설정
```
1. 프로젝트 이름: hotly-app (또는 원하는 이름)
2. 프로젝트 ID: hotly-app-xxxxx (자동 생성)
3. Google Analytics: 활성화 권장 (선택사항)
4. Analytics 계정: 기본 계정 또는 신규 생성
5. "프로젝트 만들기" 클릭
```

### 1-3. 프로젝트 생성 완료
- 프로젝트 생성까지 약 1-2분 소요
- "계속" 버튼 클릭하여 Firebase Console 진입

---

## 2. Firebase Authentication 활성화

### 2-1. Authentication 시작하기
```
Firebase Console > 빌드 > Authentication
→ "시작하기" 버튼 클릭
```

### 2-2. 로그인 제공업체 활성화

#### Google 로그인
```
1. Sign-in method 탭 선택
2. "Google" 클릭
3. 사용 설정 토글 ON
4. 프로젝트 지원 이메일: your-email@example.com
5. "저장" 클릭
```

#### Apple 로그인 (iOS 필수)
```
1. "Apple" 클릭
2. 사용 설정 토글 ON
3. Apple Developer Console 설정 필요:

   a) Apple Developer Console (https://developer.apple.com) 접속
   b) Certificates, Identifiers & Profiles > Identifiers
   c) "+" 버튼 클릭 → Services IDs 선택
   d) Description: Hotly App Sign In
   e) Identifier: com.example.hotly.signin
   f) "Configure" 버튼 클릭
      - Sign In with Apple 체크
      - Primary App ID: com.example.hotly 선택
      - Domains and Subdomains: hotly-app.firebaseapp.com
      - Return URLs: https://hotly-app.firebaseapp.com/__/auth/handler
   g) "Save" → "Continue" → "Register"

   h) Keys 메뉴로 이동
   i) "+" 버튼 클릭
   j) Key Name: Hotly App Sign In with Apple Key
   k) Sign In with Apple 체크 → Configure
   l) Primary App ID 선택 → Save
   m) Continue → Register
   n) Download 클릭하여 .p8 파일 다운로드
   o) Key ID 복사 (나중에 사용)

4. Firebase로 돌아와서:
   - Services ID: com.example.hotly.signin
   - Apple 팀 ID: Apple Developer Console에서 확인 (우측 상단)
   - Key ID: 위에서 복사한 Key ID
   - Private Key: .p8 파일 내용 복사하여 붙여넣기

5. "저장" 클릭
```

#### Email/Password 로그인 (선택사항)
```
1. "이메일/비밀번호" 클릭
2. 이메일/비밀번호 사용 설정 토글 ON
3. 이메일 링크(비밀번호가 없는 로그인)는 비활성화 유지
4. "저장" 클릭
```

#### Anonymous 로그인 (게스트 모드)
```
1. "익명" 클릭
2. 사용 설정 토글 ON
3. "저장" 클릭
```

---

## 3. Android 앱 등록

### 3-1. Android 앱 추가
```
Firebase Console > 프로젝트 설정 (⚙️) > 일반 탭
→ "앱 추가" > Android 아이콘 클릭
```

### 3-2. Android 패키지 정보 입력
```
1. Android 패키지 이름: com.example.hotly
   (flutter/android/app/build.gradle의 applicationId)

2. 앱 닉네임 (선택사항): Hotly Android

3. 디버그 서명 인증서 SHA-1 (Google 로그인 시 필수):

   맥/리눅스:
   keytool -list -v -keystore ~/.android/debug.keystore \
     -alias androiddebugkey -storepass android -keypass android

   윈도우:
   keytool -list -v -keystore %USERPROFILE%\.android\debug.keystore ^
     -alias androiddebugkey -storepass android -keypass android

   SHA-1 값을 복사하여 입력

4. "앱 등록" 클릭
```

### 3-3. google-services.json 다운로드
```
1. google-services.json 파일 다운로드
2. 파일을 flutter/android/app/ 디렉토리에 복사
3. "다음" 클릭
```

### 3-4. Firebase SDK 추가 (자동 완료됨)
```
Flutter 프로젝트는 이미 Firebase SDK가 설정되어 있습니다.
pubspec.yaml에 다음 패키지들이 있는지 확인:

dependencies:
  firebase_core: ^2.24.0
  firebase_auth: ^4.15.0
  google_sign_in: ^6.1.5

"다음" → "계속 콘솔로 이동" 클릭
```

---

## 4. iOS 앱 등록

### 4-1. iOS 앱 추가
```
Firebase Console > 프로젝트 설정 (⚙️) > 일반 탭
→ "앱 추가" > iOS 아이콘 클릭
```

### 4-2. iOS 번들 ID 입력
```
1. iOS 번들 ID: com.example.hotly
   (flutter/ios/Runner.xcodeproj/project.pbxproj의 PRODUCT_BUNDLE_IDENTIFIER)

2. 앱 닉네임 (선택사항): Hotly iOS

3. App Store ID (선택사항): 나중에 추가 가능

4. "앱 등록" 클릭
```

### 4-3. GoogleService-Info.plist 다운로드
```
1. GoogleService-Info.plist 파일 다운로드
2. Xcode에서 flutter/ios/Runner.xcworkspace 열기
3. Runner 폴더에서 우클릭 → "Add Files to Runner..."
4. GoogleService-Info.plist 선택
5. ✅ "Copy items if needed" 체크
6. ✅ "Create groups" 선택
7. Target: Runner 선택
8. "Add" 클릭

"다음" → "계속 콘솔로 이동" 클릭
```

---

## 5. Backend (FastAPI) 설정

### 5-1. Firebase Admin SDK Service Account Key 생성
```
1. Firebase Console > 프로젝트 설정 (⚙️) > 서비스 계정 탭
2. "새 비공개 키 생성" 버튼 클릭
3. "키 생성" 확인 클릭
4. JSON 파일 자동 다운로드 (serviceAccountKey.json)
```

### 5-2. Service Account Key 배치
```bash
# Backend 디렉토리로 이동
cd backend

# credentials 디렉토리 생성 (없는 경우)
mkdir -p credentials

# 다운로드한 JSON 파일을 credentials/ 디렉토리로 이동
mv ~/Downloads/hotly-app-xxxxx-firebase-adminsdk-xxxxx.json \
   credentials/serviceAccountKey.json

# .gitignore에 credentials/ 추가 확인
echo "credentials/" >> .gitignore
```

### 5-3. Backend 환경 변수 설정
```bash
# backend/.env 파일 생성/수정
cat > .env <<EOF
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=credentials/serviceAccountKey.json
FIREBASE_PROJECT_ID=hotly-app-xxxxx

# API Configuration
API_BASE_URL=http://localhost:8000/api/v1

# Kakao (이미 설정된 값 유지)
KAKAO_NATIVE_APP_KEY=78ff40eb343af6b500a92c15fcd786db
KAKAO_JAVASCRIPT_APP_KEY=eb676c17a94bf63780199e12d1381007
EOF
```

---

## 6. Frontend (Flutter) 설정

### 6-1. Firebase 초기화 코드 확인
```dart
// frontend/lib/main.dart
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart'; // FlutterFire CLI로 생성

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase 초기화
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  runApp(MyApp());
}
```

### 6-2. FlutterFire CLI로 firebase_options.dart 생성
```bash
# Flutter 프로젝트 디렉토리로 이동
cd frontend

# FlutterFire CLI 설치 (한 번만)
dart pub global activate flutterfire_cli

# Firebase 프로젝트와 연결
flutterfire configure

# 프롬프트에 따라 진행:
# 1. Firebase 프로젝트 선택: hotly-app-xxxxx
# 2. 플랫폼 선택: android, ios
# 3. 파일 생성 확인

# 생성된 파일 확인
# ✅ lib/firebase_options.dart
```

### 6-3. Frontend 환경 변수 업데이트
```bash
# frontend/.env.dev 파일 수정
cat > .env.dev <<EOF
# Firebase Configuration
# Firebase 설정은 firebase_options.dart에 자동 생성됨

# API Configuration
API_BASE_URL=http://localhost:8000/api/v1

# Kakao Configuration
KAKAO_NATIVE_APP_KEY=78ff40eb343af6b500a92c15fcd786db
KAKAO_JAVASCRIPT_APP_KEY=eb676c17a94bf63780199e12d1381007
KAKAO_MAP_APP_KEY=78ff40eb343af6b500a92c15fcd786db
EOF
```

---

## 7. Kakao 로그인 설정

### 7-1. Kakao Developers Console 설정
```
1. https://developers.kakao.com 접속
2. 내 애플리케이션 > 애플리케이션 추가하기
3. 앱 이름: Hotly
4. 사업자명: (선택사항)
5. "저장" 클릭

6. 앱 키 확인 (이미 .env.dev에 설정된 값과 동일한지 확인):
   - Native 앱 키: 78ff40eb343af6b500a92c15fcd786db
   - JavaScript 키: eb676c17a94bf63780199e12d1381007

7. 플랫폼 설정:
   a) Android 플랫폼 등록
      - 패키지명: com.example.hotly
      - 마켓 URL: (선택사항)
      - 키 해시: 디버그 키 해시 등록
        (keytool -exportcert -alias androiddebugkey \
         -keystore ~/.android/debug.keystore | \
         openssl sha1 -binary | openssl base64)

   b) iOS 플랫폼 등록
      - 번들 ID: com.example.hotly
      - 팀 ID: Apple Developer Console에서 확인

8. 카카오 로그인 활성화:
   - 제품 설정 > 카카오 로그인
   - 활성화 설정 ON
   - Redirect URI: com.example.hotly://oauth
   - "저장" 클릭
```

### 7-2. Flutter Kakao SDK 설정 확인
```dart
// frontend/lib/main.dart
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Kakao SDK 초기화
  KakaoSdk.init(
    nativeAppKey: '78ff40eb343af6b500a92c15fcd786db',
    javaScriptAppKey: 'eb676c17a94bf63780199e12d1381007',
  );

  // Firebase 초기화
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  runApp(MyApp());
}
```

---

## 8. 설정 확인 및 테스트

### 8-1. Backend 테스트
```bash
# Backend 디렉토리로 이동
cd backend

# 가상환경 활성화
poetry shell

# Backend 서버 실행
uvicorn app.main:app --reload

# 다른 터미널에서 테스트
curl http://localhost:8000/api/v1/health

# 로그 확인
# ✅ Firebase Admin SDK initialized successfully
```

### 8-2. Frontend 테스트
```bash
# Flutter 프로젝트 디렉토리로 이동
cd frontend

# 의존성 설치
flutter pub get

# 앱 실행 (Android)
flutter run

# 또는 iOS
flutter run -d ios

# 로그 확인:
# ✅ Firebase initialized successfully
# ✅ Kakao SDK initialized
```

### 8-3. Firebase Console에서 확인
```
1. Authentication > Users 탭
   - 처음에는 사용자 0명

2. 앱에서 로그인 테스트:
   - Google 로그인 시도
   - Kakao 로그인 시도
   - 익명 로그인 시도

3. Users 탭 새로고침:
   - 로그인 성공 시 사용자 목록에 표시
   - UID, 이메일, 가입 시간 등 확인
```

---

## 9. 프로덕션 배포 준비

### 9-1. Android 릴리즈 빌드 SHA-1 등록
```bash
# 릴리즈 keystore 생성 (없는 경우)
keytool -genkey -v -keystore ~/upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload

# 릴리즈 SHA-1 확인
keytool -list -v -keystore ~/upload-keystore.jks \
  -alias upload

# Firebase Console에 SHA-1 추가
# 프로젝트 설정 > Android 앱 > SHA 인증서 지문 추가
```

### 9-2. iOS App Store 준비
```
1. Apple Developer Console:
   - App ID 등록 확인
   - Provisioning Profile 생성
   - Sign In with Apple Capability 추가

2. Firebase Console:
   - iOS 앱 설정 > App Store ID 입력
```

### 9-3. Firebase 프로덕션 환경 분리
```
1. Firebase Console에서 새 프로젝트 생성:
   - 프로젝트 이름: hotly-app-prod

2. 위의 모든 설정 반복

3. Frontend 환경 분리:
   - .env.dev (개발)
   - .env.prod (프로덕션)
   - flutterfire configure --project=hotly-app-prod

4. Backend 환경 분리:
   - .env.dev
   - .env.prod
   - 각각 다른 Service Account Key 사용
```

---

## 10. 보안 체크리스트

### 10-1. 파일 보안
```bash
# ✅ .gitignore 확인
cat .gitignore

# 다음 항목들이 포함되어 있어야 함:
# *.env
# credentials/
# serviceAccountKey.json
# google-services.json
# GoogleService-Info.plist

# ✅ 실수로 커밋된 민감 정보 제거
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch credentials/serviceAccountKey.json' \
  --prune-empty --tag-name-filter cat -- --all
```

### 10-2. Firebase Security Rules 설정
```javascript
// Firebase Console > Firestore > Rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 기본 규칙: 인증된 사용자만 자신의 데이터 접근
    match /users/{userId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == userId;
    }

    // 게스트 데이터
    match /guest_data/{guestId} {
      allow read, write: if request.auth != null
                         && request.auth.uid == guestId;
    }
  }
}
```

### 10-3. API Key 제한 (선택사항)
```
Firebase Console > 프로젝트 설정 > 서비스 계정
→ Google Cloud Console 열기

APIs & Services > Credentials
→ API 키 제한 설정:
  - Android: 패키지 이름 + SHA-1 제한
  - iOS: 번들 ID 제한
  - Web: HTTP 리퍼러 제한
```

---

## 11. 트러블슈팅

### 문제 1: Google Sign-In이 Android에서 작동하지 않음
```
원인: SHA-1 인증서가 Firebase에 등록되지 않음

해결:
1. SHA-1 확인:
   keytool -list -v -keystore ~/.android/debug.keystore \
     -alias androiddebugkey -storepass android -keypass android

2. Firebase Console > 프로젝트 설정 > Android 앱 > SHA 인증서 지문 추가

3. google-services.json 재다운로드 및 교체

4. 앱 재빌드
```

### 문제 2: iOS에서 Google Sign-In 실패
```
원인: URL Scheme 설정 누락

해결:
1. Xcode에서 ios/Runner.xcworkspace 열기
2. Runner > Info.plist
3. URL Types 확인:
   <key>CFBundleURLTypes</key>
   <array>
     <dict>
       <key>CFBundleURLSchemes</key>
       <array>
         <string>com.googleusercontent.apps.YOUR_CLIENT_ID</string>
       </array>
     </dict>
   </array>

4. YOUR_CLIENT_ID는 GoogleService-Info.plist의 REVERSED_CLIENT_ID 값
```

### 문제 3: Kakao 로그인 실패
```
원인: Kakao SDK 초기화 오류 또는 앱 키 불일치

해결:
1. Kakao Developers Console에서 앱 키 확인
2. .env.dev 파일의 KAKAO_NATIVE_APP_KEY 일치 확인
3. 플랫폼 설정 (Android/iOS) 확인
4. Redirect URI 확인: com.example.hotly://oauth
```

### 문제 4: Firebase Admin SDK 오류
```
원인: Service Account Key 경로 오류

해결:
1. credentials/serviceAccountKey.json 파일 존재 확인
2. .env 파일의 FIREBASE_CREDENTIALS_PATH 경로 확인
3. JSON 파일 형식 확인 (유효한 JSON인지)
4. 파일 권한 확인: chmod 600 credentials/serviceAccountKey.json
```

---

## 12. 다음 단계

설정 완료 후:
1. ✅ Authentication 기능 테스트
2. ✅ 각 로그인 방식 (Google, Apple, Kakao, Anonymous) 검증
3. ✅ Backend API 연동 테스트
4. ✅ 프로덕션 환경 준비
5. ✅ 보안 규칙 설정
6. ✅ 모니터링 및 로깅 설정

## 참고 문서
- Firebase Authentication: https://firebase.google.com/docs/auth
- FlutterFire: https://firebase.flutter.dev/
- Kakao Login: https://developers.kakao.com/docs/latest/ko/kakaologin/common
- Apple Sign In: https://developer.apple.com/sign-in-with-apple/

---

**작성일**: 2025-01-XX
**작성자**: Claude
**버전**: 1.0 (Firebase 기반)
