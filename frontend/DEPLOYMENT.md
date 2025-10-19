# Hotly App Deployment Guide

## 목차
1. [사전 준비](#사전-준비)
2. [환경 설정](#환경-설정)
3. [Android 배포](#android-배포)
4. [iOS 배포](#ios-배포)
5. [문제 해결](#문제-해결)

---

## 사전 준비

### 필수 계정 및 도구

#### Firebase
1. [Firebase Console](https://console.firebase.google.com)에서 프로젝트 생성
2. Android 앱 등록: `com.hotly.hotly_app`
3. iOS 앱 등록: `com.hotly.hotly_app`
4. `google-services.json` 다운로드 → `android/app/` 위치
5. `GoogleService-Info.plist` 다운로드 → `ios/Runner/` 위치

#### Kakao Developers
1. [Kakao Developers](https://developers.kakao.com)에서 애플리케이션 생성
2. 플랫폼 설정:
   - Android: 패키지명 `com.hotly.hotly_app`, 키 해시 등록
   - iOS: Bundle ID `com.hotly.hotly_app` 등록
3. API 키 발급:
   - JavaScript 키 (웹뷰용)
   - Native App 키 (네이티브용)

#### Google Cloud Platform (선택사항)
1. [Google Cloud Console](https://console.cloud.google.com)
2. OAuth 2.0 클라이언트 ID 생성:
   - Android 클라이언트 ID
   - iOS 클라이언트 ID

---

## 환경 설정

### 1. 환경 변수 파일 생성

#### Development (`.env.dev`)
```bash
cp .env.example .env.dev
# Edit .env.dev with your development credentials
```

#### Staging (`.env.staging`)
```bash
# Staging environment with test data
ENVIRONMENT=staging
API_BASE_URL=https://staging-api.hotly.app/api/v1
# Firebase configuration (use staging project)
# ... other staging configs
```

#### Production (`.env.prod`)
```bash
# Production environment - SECURE THESE VALUES!
ENVIRONMENT=production
API_BASE_URL=https://api.hotly.app/api/v1
# Firebase configuration (use production project)
ENABLE_DEBUG_LOGGING=false
# ... other production configs
```

### 2. 버전 관리

`pubspec.yaml`에서 버전 업데이트:
```yaml
version: 1.0.0+1  # [MAJOR.MINOR.PATCH]+[BUILD_NUMBER]
```

---

## Android 배포

### 1. Keystore 생성 (첫 배포 시)

```bash
keytool -genkey -v -keystore ~/hotly-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias hotly-release

# keystore password와 key password를 안전하게 보관!
```

### 2. Keystore 설정

`android/key.properties` 파일 생성:
```properties
storePassword=YOUR_KEYSTORE_PASSWORD
keyPassword=YOUR_KEY_PASSWORD
keyAlias=hotly-release
storeFile=/Users/your-username/hotly-release-key.jks
```

⚠️ **주의**: `key.properties`는 `.gitignore`에 포함되어야 합니다!

`android/app/build.gradle.kts` 수정:
```kotlin
// Load keystore properties
val keystorePropertiesFile = rootProject.file("key.properties")
val keystoreProperties = Properties()
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(FileInputStream(keystorePropertiesFile))
}

android {
    signingConfigs {
        create("release") {
            storeFile = file(keystoreProperties["storeFile"] ?: "debug.keystore")
            storePassword = keystoreProperties["storePassword"] as? String ?: "android"
            keyAlias = keystoreProperties["keyAlias"] as? String ?: "androiddebugkey"
            keyPassword = keystoreProperties["keyPassword"] as? String ?: "android"
        }
    }
}
```

### 3. 빌드 실행

#### Debug APK
```bash
./scripts/build-android.sh dev debug
```

#### Release AAB (Play Store 제출용)
```bash
./scripts/build-android.sh prod release
```

출력 파일:
- AAB: `build/app/outputs/bundle/prodRelease/app-prod-release.aab`
- APK: `build/app/outputs/apk/prod/release/app-prod-release.apk`

### 4. Google Play Console 제출

1. [Google Play Console](https://play.google.com/console) 접속
2. "앱 만들기" → 앱 정보 입력
3. 프로덕션 → 새 출시 만들기
4. AAB 파일 업로드 (`app-prod-release.aab`)
5. 출시 노트 작성
6. 검토 제출

#### 필수 자료
- 스크린샷 (최소 2개, 권장 8개)
  - Phone: 16:9 or 9:16 ratio
  - Tablet: 1920x1080 or 1080x1920
- 아이콘: 512x512 PNG
- 기능 그래픽: 1024x500 PNG
- 개인정보처리방침 URL
- 앱 설명 (짧은 설명, 전체 설명)

---

## iOS 배포

### 1. Apple Developer 계정 설정

#### Apple Developer Program 가입
1. [Apple Developer](https://developer.apple.com) 가입 (연간 $99)
2. Certificates, Identifiers & Profiles 설정

#### App ID 생성
1. Identifiers → App IDs → "+" 버튼
2. Bundle ID: `com.hotly.hotly_app`
3. Capabilities 활성화:
   - Push Notifications
   - Sign in with Apple
   - Associated Domains

#### Certificates 생성
1. Certificates → "+" 버튼
2. **Development**: iOS App Development
3. **Distribution**: iOS Distribution (App Store)

#### Provisioning Profiles 생성
1. Profiles → "+" 버튼
2. **Development**: iOS App Development
3. **Distribution**: App Store

### 2. Xcode 설정

```bash
# Xcode 프로젝트 열기
open ios/Runner.xcworkspace
```

Xcode에서:
1. **Signing & Capabilities** 탭
2. Team 선택 (Apple Developer 계정)
3. Automatically manage signing 체크 (또는 수동 설정)
4. Bundle Identifier 확인: `com.hotly.hotly_app`

### 3. 빌드 실행

#### Debug (Simulator/Device)
```bash
./scripts/build-ios.sh dev debug
```

#### Release (App Store 제출용)
```bash
./scripts/build-ios.sh prod release
```

출력 파일:
- Archive: `build/ios/archive/Runner.xcarchive`
- IPA: `build/ios/ipa/hotly_app.ipa`

### 4. App Store Connect 제출

#### Transporter 사용 (권장)
1. Mac App Store에서 "Transporter" 앱 다운로드
2. IPA 파일 드래그 앤 드롭
3. "전달" 버튼 클릭

#### 명령줄 사용
```bash
xcrun altool --upload-app --type ios \
  --file build/ios/ipa/hotly_app.ipa \
  --username YOUR_APPLE_ID \
  --password YOUR_APP_SPECIFIC_PASSWORD
```

**App-Specific Password 생성**:
1. [appleid.apple.com](https://appleid.apple.com) → 로그인
2. 보안 → 앱 암호 → "+" 생성
3. 생성된 암호 저장

#### App Store Connect에서 앱 설정
1. [App Store Connect](https://appstoreconnect.apple.com) 접속
2. "나의 앱" → "+" → "새로운 앱"
3. 앱 정보 입력:
   - 이름: Hotly
   - 기본 언어: 한국어
   - Bundle ID: com.hotly.hotly_app
   - SKU: com.hotly.hotly_app

4. 앱 버전 정보 입력:
   - 스크린샷 (iPhone, iPad 각각)
   - 앱 미리보기 비디오 (선택사항)
   - 설명, 키워드, 지원 URL
   - 개인정보처리방침 URL

5. 빌드 선택 및 제출

---

## 배포 체크리스트

### 공통
- [ ] 환경 변수 파일 설정 완료 (`.env.prod`)
- [ ] Firebase 프로젝트 설정 완료 (Authentication, Messaging, Analytics)
- [ ] Kakao API 키 발급 완료
- [ ] 버전 번호 업데이트 (`pubspec.yaml`)
- [ ] 개인정보처리방침 페이지 작성
- [ ] 이용약관 페이지 작성

### Android
- [ ] Keystore 생성 및 안전하게 보관
- [ ] `google-services.json` 파일 위치 확인
- [ ] ProGuard 규칙 테스트
- [ ] 릴리즈 빌드 테스트 (실제 기기)
- [ ] APK/AAB 크기 확인 (< 150MB 권장)
- [ ] Google Play Console 개발자 계정 등록
- [ ] 스크린샷 및 그래픽 자료 준비
- [ ] 앱 설명 및 키워드 작성

### iOS
- [ ] Apple Developer Program 가입 ($99/year)
- [ ] App ID 생성
- [ ] Certificates 생성 (Development, Distribution)
- [ ] Provisioning Profiles 생성
- [ ] `GoogleService-Info.plist` 파일 위치 확인
- [ ] Xcode 서명 설정 완료
- [ ] 릴리즈 빌드 테스트 (실제 기기)
- [ ] IPA 크기 확인 (< 200MB 권장)
- [ ] App Store Connect 앱 등록
- [ ] 스크린샷 및 앱 미리보기 준비
- [ ] 앱 설명 및 키워드 작성 (한국어, 영어)

---

## 문제 해결

### Android

#### "google-services.json not found"
```bash
# Firebase Console에서 다운로드
# android/app/google-services.json 위치에 저장
```

#### ProGuard로 인한 크래시
```bash
# proguard-rules.pro에 keep 규칙 추가
-keep class com.your.package.** { *; }

# 또는 일시적으로 비활성화 (디버깅용)
# build.gradle.kts: isMinifyEnabled = false
```

#### MultiDex 에러
```bash
# build.gradle.kts에서 이미 활성화됨
defaultConfig {
    multiDexEnabled = true
}
```

### iOS

#### "Code signing failed"
```bash
# Xcode에서:
# 1. Clean Build Folder (Cmd+Shift+K)
# 2. Signing & Capabilities에서 Team 재선택
# 3. Provisioning Profile 재생성
```

#### CocoaPods 에러
```bash
cd ios
pod deintegrate
pod install --repo-update
cd ..
flutter clean
flutter pub get
```

#### "Unable to install Runner.app"
```bash
# 기기에서 기존 앱 삭제
# 다시 빌드 및 설치
flutter clean
flutter run --release
```

---

## 보안 주의사항

### 절대 Git에 커밋하지 말 것
- `key.properties` (Android keystore 정보)
- `*.jks` (Android keystore 파일)
- `*.p12` (iOS certificate)
- `.env.prod` (프로덕션 환경 변수)
- `google-services.json` (실제 Firebase 설정)
- `GoogleService-Info.plist` (실제 Firebase 설정)

### 권장 사항
- 환경 변수는 CI/CD 시스템의 Secrets에 저장
- Keystore와 Certificate는 안전한 비밀번호 관리 도구에 보관
- 프로덕션 API 키는 정기적으로 교체
- 앱 업데이트 시 보안 패치 확인

---

## 자동화 (CI/CD)

### GitHub Actions 예제

`.github/workflows/deploy-android.yml`:
```yaml
name: Deploy Android

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-java@v3
        with:
          distribution: 'zulu'
          java-version: '11'
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.19.0'

      - name: Decode google-services.json
        env:
          GOOGLE_SERVICES: ${{ secrets.GOOGLE_SERVICES_JSON }}
        run: echo $GOOGLE_SERVICES | base64 -d > android/app/google-services.json

      - name: Build AAB
        run: ./scripts/build-android.sh prod release

      - name: Upload to Play Store
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_SERVICE_ACCOUNT }}
          packageName: com.hotly.hotly_app
          releaseFiles: build/app/outputs/bundle/prodRelease/app-prod-release.aab
          track: production
```

---

## 버전 관리 전략

### Semantic Versioning
- **MAJOR**: 호환되지 않는 API 변경
- **MINOR**: 하위 호환 가능한 기능 추가
- **PATCH**: 하위 호환 가능한 버그 수정

### Build Number
- 각 배포마다 증가
- Android: `versionCode`
- iOS: `CFBundleVersion`

예시:
- `1.0.0+1` → 첫 릴리즈
- `1.0.1+2` → 버그 수정
- `1.1.0+3` → 새 기능 추가
- `2.0.0+4` → 대규모 변경

---

## 참고 링크

- [Flutter Deployment](https://docs.flutter.dev/deployment)
- [Google Play Console](https://play.google.com/console)
- [App Store Connect](https://appstoreconnect.apple.com)
- [Firebase Console](https://console.firebase.google.com)
- [Firebase Setup Guide](../docs/firebase-setup-guide.md)
