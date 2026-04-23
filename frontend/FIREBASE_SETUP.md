# Firebase Authentication 설정 가이드 (Flutter)

## 개요

ArchyAI 앱은 Firebase Authentication을 사용하여 소셜 로그인을 처리합니다.

### 지원하는 인증 방법
- 🔵 Google Sign-In
- 🍎 Apple Sign-In
- 💬 Kakao Sign-In
- 👤 익명 로그인 (게스트 모드)

---

## 1. Firebase 프로젝트 설정

### 1.1 Firebase 프로젝트 생성

1. [Firebase Console](https://console.firebase.google.com/) 접속
2. "프로젝트 추가" 클릭
3. 프로젝트 이름 입력: `hotly-app`
4. Google Analytics 활성화 (선택사항)
5. 프로젝트 생성 완료

### 1.2 Android 앱 추가

1. Firebase Console > 프로젝트 설정 > 일반
2. "Android 앱 추가" 클릭
3. **Android 패키지 이름**: `com.hotly.hotly_app`
4. **앱 닉네임**: ArchyAI Android (선택사항)
5. **SHA-1 인증서** (중요!):
   ```bash
   # Debug keystore SHA-1 가져오기
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android

   # Release keystore SHA-1 가져오기 (프로덕션)
   keytool -list -v -keystore /path/to/release.keystore -alias your-key-alias
   ```
6. `google-services.json` 다운로드
7. 파일을 `android/app/` 폴더에 복사

### 1.3 iOS 앱 추가

1. Firebase Console > 프로젝트 설정 > 일반
2. "iOS 앱 추가" 클릭
3. **iOS 번들 ID**: `com.hotly.hotly_app`
4. **앱 닉네임**: ArchyAI iOS (선택사항)
5. `GoogleService-Info.plist` 다운로드

6. **Xcode에서 plist 파일 추가 (중요!)**

   **방법 1: 터미널에서 Xcode 열기 (권장)**
   ```bash
   cd /Users/jeongmun/Documents/GitHub/hotly-app/frontend
   open ios/Runner.xcworkspace
   ```

   **방법 2: Finder에서 열기**
   - `frontend/ios/Runner.xcworkspace` 파일을 더블클릭
   - ⚠️ 주의: `.xcodeproj`가 아닌 `.xcworkspace` 파일을 열어야 합니다!

   **Xcode에서 파일 추가하기:**

   a. 왼쪽 Project Navigator에서 **Runner** 폴더 찾기 (파란색 아이콘)

   b. **Runner** 폴더 우클릭 → **Add Files to "Runner"** 선택

   c. 다운로드한 `GoogleService-Info.plist` 파일 선택

   d. 파일 추가 옵션 대화상자에서:
      - ✅ **"Copy items if needed"** 체크 (필수!)
      - ✅ **"Create groups"** 선택
      - ✅ **Target: Runner** 체크 (필수!)
      - ❌ "Create folder references" 선택 안 함

   e. **Add** 버튼 클릭

   f. 확인: Project Navigator에서 Runner 폴더 아래에 `GoogleService-Info.plist` 파일이 보여야 함

   g. 파일 클릭하여 오른쪽 패널에서 **Target Membership**에 Runner가 체크되어 있는지 확인

7. **파일 위치 확인**
   ```bash
   # 터미널에서 파일이 제대로 복사되었는지 확인
   ls -la ios/Runner/GoogleService-Info.plist
   ```

   파일이 존재해야 합니다. 없다면 Xcode에서 "Copy items if needed"를 체크했는지 확인하세요.

---

## 2. Firebase Authentication 활성화

### 2.1 로그인 방법 활성화

Firebase Console > Authentication > Sign-in method에서 다음 활성화:

#### Google
1. "Google" 클릭 > "사용 설정"
2. 프로젝트 지원 이메일 선택
3. 저장

#### Apple
1. "Apple" 클릭 > "사용 설정"
2. **Services ID** (선택사항): `com.hotly.hotly_app.signin`
3. 저장

#### 익명
1. "익명" 클릭 > "사용 설정"
2. 저장

---

## 3. Kakao 로그인 설정

### 3.1 Kakao Developers 설정

1. [Kakao Developers](https://developers.kakao.com/) 접속
2. 내 애플리케이션 > 애플리케이션 추가
3. 앱 이름: `ArchyAI`
4. **앱 키 확인**:
   - 네이티브 앱 키: `.env` 파일의 `KAKAO_NATIVE_APP_KEY`
   - JavaScript 앱 키: `.env` 파일의 `KAKAO_JAVASCRIPT_APP_KEY`

### 3.2 플랫폼 설정

#### Android
1. 플랫폼 > Android 플랫폼 등록
2. **패키지명**: `com.hotly.hotly_app`
3. **키 해시** 등록:
   ```bash
   # Debug 키 해시
   keytool -exportcert -alias androiddebugkey -keystore ~/.android/debug.keystore | openssl sha1 -binary | openssl base64
   ```
4. 저장

#### iOS
1. 플랫폼 > iOS 플랫폼 등록
2. **번들 ID**: `com.hotly.hotly_app`
3. 저장

### 3.3 Redirect URI 설정

1. 카카오 로그인 > Redirect URI
2. 다음 URI 등록:
   - `kakao{NATIVE_APP_KEY}://oauth`
   - 예: `kakao123456789://oauth`

---

## 4. 환경 변수 설정

### 4.1 .env 파일 생성

```bash
cd frontend
cp .env.example .env.dev
```

### 4.2 .env.dev 파일 편집

```bash
# ===== Firebase Configuration =====
FIREBASE_PROJECT_ID=hotly-app-12345

# ===== Kakao Configuration =====
KAKAO_NATIVE_APP_KEY=abc123def456
KAKAO_JAVASCRIPT_APP_KEY=xyz789uvw012
KAKAO_MAP_APP_KEY=your_map_key

# ===== Social Login Configuration =====
GOOGLE_CLIENT_ID_IOS=123456789-abcdef.apps.googleusercontent.com
GOOGLE_CLIENT_ID_ANDROID=123456789-ghijkl.apps.googleusercontent.com
APPLE_CLIENT_ID=com.hotly.hotly_app

# ===== Backend API Configuration =====
API_BASE_URL=http://localhost:8000/api/v1
```

---

## 5. Android 추가 설정

### 5.1 build.gradle 확인

`android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        applicationId "com.hotly.hotly_app"
        minSdkVersion 21  // Firebase 최소 요구사항
        targetSdkVersion 34
    }
}

dependencies {
    // Firebase
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-auth'
    implementation 'com.google.firebase:firebase-messaging'

    // Kakao SDK
    implementation "com.kakao.sdk:v2-user:2.19.0"
}

apply plugin: 'com.google.gms.google-services'
```

### 5.2 AndroidManifest.xml 설정

`android/app/src/main/AndroidManifest.xml`:

```xml
<manifest>
    <application>
        <!-- Kakao App Key -->
        <meta-data
            android:name="com.kakao.sdk.AppKey"
            android:value="${KAKAO_NATIVE_APP_KEY}" />

        <!-- Kakao Login Redirect -->
        <activity
            android:name="com.kakao.sdk.auth.AuthCodeHandlerActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data
                    android:host="oauth"
                    android:scheme="kakao${KAKAO_NATIVE_APP_KEY}" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

---

## 6. iOS 추가 설정

### 6.1 Info.plist 설정

`ios/Runner/Info.plist`:

```xml
<dict>
    <!-- Kakao App Key -->
    <key>KAKAO_APP_KEY</key>
    <string>$(KAKAO_NATIVE_APP_KEY)</string>

    <!-- URL Schemes -->
    <key>CFBundleURLTypes</key>
    <array>
        <!-- Kakao Login -->
        <dict>
            <key>CFBundleTypeRole</key>
            <string>Editor</string>
            <key>CFBundleURLSchemes</key>
            <array>
                <string>kakao$(KAKAO_NATIVE_APP_KEY)</string>
            </array>
        </dict>
    </array>

    <!-- LSApplicationQueriesSchemes -->
    <key>LSApplicationQueriesSchemes</key>
    <array>
        <string>kakaokompassauth</string>
        <string>kakaolink</string>
        <string>kakaoplus</string>
        <string>kakaotalk</string>
    </array>
</dict>
```

### 6.2 Podfile 확인

`ios/Podfile`:

```ruby
platform :ios, '13.0'

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  # Firebase
  pod 'FirebaseAuth'
  pod 'FirebaseMessaging'

  # Google Sign-In
  pod 'GoogleSignIn'

  # Kakao SDK
  pod 'KakaoSDKUser'
  pod 'KakaoSDKAuth'
end

post_install do |installer|
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
    target.build_configurations.each do |config|
      config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '13.0'
    end
  end
end
```

설치:
```bash
cd ios
pod install
```

---

## 7. 코드 생성 및 빌드

### 7.1 의존성 설치

```bash
cd frontend
flutter pub get
```

### 7.2 코드 생성

Freezed, JSON Serializable 코드 생성:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

### 7.3 앱 실행

```bash
# Android
flutter run

# iOS
flutter run -d ios

# 특정 디바이스
flutter devices
flutter run -d <device-id>
```

---

## 8. 테스트

### 8.1 소셜 로그인 테스트

1. 앱 실행
2. 로그인 화면에서 "Google로 계속하기" 버튼 클릭
3. Google 계정 선택 및 권한 승인
4. 로그인 성공 확인

### 8.2 Firebase Console에서 확인

1. Firebase Console > Authentication > Users
2. 로그인한 사용자 목록 확인
3. UID, 이메일, 로그인 방법 확인

---

## 9. 트러블슈팅

### 문제: "MissingPluginException"

**원인**: Flutter 플러그인이 제대로 등록되지 않음

**해결**:
```bash
flutter clean
flutter pub get
cd ios && pod install && cd ..
flutter run
```

### 문제: "FirebaseApp not initialized"

**원인**: Firebase.initializeApp() 호출 누락

**해결**: `main.dart`에서 Firebase 초기화 확인
```dart
await Firebase.initializeApp();
```

### 문제: Kakao 로그인 실패 "Invalid App Key"

**원인**: Kakao App Key가 잘못되었거나 플랫폼 설정이 누락됨

**해결**:
1. `.env.dev` 파일의 `KAKAO_NATIVE_APP_KEY` 확인
2. Kakao Developers에서 플랫폼 설정 확인 (패키지명, 번들 ID, 키 해시)

### 문제: Google Sign-In 실패 "DEVELOPER_ERROR"

**원인**: SHA-1 인증서가 Firebase에 등록되지 않음

**해결**:
1. SHA-1 인증서 다시 확인
2. Firebase Console > 프로젝트 설정 > SHA 인증서 지문 추가
3. `google-services.json` 다시 다운로드

### 문제: Apple Sign-In 테스트 불가 (시뮬레이터)

**원인**: Apple Sign-In은 실제 기기에서만 작동

**해결**: 실제 iOS 기기로 테스트

---

## 10. 보안 체크리스트

- [ ] `google-services.json`과 `GoogleService-Info.plist`를 `.gitignore`에 추가
- [ ] `.env` 파일을 `.gitignore`에 추가
- [ ] Firebase Security Rules 설정
- [ ] API Key 제한 설정 (Firebase Console > 프로젝트 설정 > API 키)
- [ ] 프로덕션 키스토어 생성 및 안전하게 보관
- [ ] Release 빌드에서 DEBUG 로그 비활성화

---

## 참고 자료

- [Firebase Flutter Setup](https://firebase.flutter.dev/docs/overview)
- [FlutterFire Authentication](https://firebase.flutter.dev/docs/auth/overview)
- [Kakao Flutter SDK](https://developers.kakao.com/docs/latest/ko/flutter/getting-started)
- [Google Sign-In for Flutter](https://pub.dev/packages/google_sign_in)
- [Sign in with Apple for Flutter](https://pub.dev/packages/sign_in_with_apple)

---

## 지원

문제가 발생하면:
1. Firebase Console에서 로그 확인
2. Flutter 디버그 콘솔 확인
3. [GitHub Issues](https://github.com/your-org/hotly-app/issues)에 문의
