# Hotly Flutter App

AI 기반 핫플레이스 아카이빙 모바일 앱 (Flutter)

## 시작하기

### 필수 요구사항

- Flutter SDK: 3.19.0+
- Dart SDK: 3.3.0+
- FVM (Flutter Version Management)
- Android Studio / Xcode

### 설치 및 실행

```bash
# 1. FVM으로 Flutter 버전 설정
fvm install 3.19.6
fvm use 3.19.6

# 2. 의존성 설치
fvm flutter pub get

# 3. 코드 생성 (Freezed, Riverpod 등)
fvm flutter pub run build_runner build --delete-conflicting-outputs

# 4. 환경 변수 설정
cp .env.dev .env

# 5. 앱 실행 (개발 모드)
fvm flutter run --dart-define=ENV=dev

# 6. 특정 기기에서 실행
fvm flutter devices
fvm flutter run -d <device_id>
```

## 프로젝트 구조

```
lib/
├── main.dart                    # 앱 진입점
├── app.dart                     # MaterialApp 설정
├── core/                        # 공통 인프라
│   ├── config/
│   ├── constants/
│   ├── di/
│   ├── error/
│   ├── network/
│   ├── router/
│   └── utils/
├── features/                    # 기능별 모듈 (Feature-First)
│   ├── auth/
│   ├── home/
│   ├── places/
│   ├── courses/
│   └── profile/
└── shared/                      # 공유 위젯 및 유틸
    ├── widgets/
    └── providers/
```

## 개발 명령어

### 테스트

```bash
# 모든 테스트 실행
fvm flutter test

# 커버리지 포함
fvm flutter test --coverage

# 위젯 테스트만
fvm flutter test test/widget/

# 통합 테스트
fvm flutter test integration_test/
```

### 코드 생성

```bash
# 코드 생성 (한 번)
fvm flutter pub run build_runner build --delete-conflicting-outputs

# Watch 모드 (자동 생성)
fvm flutter pub run build_runner watch --delete-conflicting-outputs
```

### 코드 품질

```bash
# Lint 검사
fvm flutter analyze

# 포맷팅
fvm flutter format lib/ test/

# 포맷 검사
fvm flutter format --set-exit-if-changed lib/ test/
```

### 빌드

#### 자동 빌드 스크립트 (권장)
```bash
# Android 빌드
./scripts/build-android.sh dev debug       # 개발 디버그
./scripts/build-android.sh staging release # 스테이징 릴리즈
./scripts/build-android.sh prod release    # 프로덕션 릴리즈

# iOS 빌드
./scripts/build-ios.sh dev debug           # 개발 디버그
./scripts/build-ios.sh staging release     # 스테이징 릴리즈
./scripts/build-ios.sh prod release        # 프로덕션 릴리즈
```

#### 수동 빌드 (Flutter 명령어)
```bash
# Android APK (개발)
fvm flutter build apk --dart-define=ENV=dev

# Android APK (프로덕션)
fvm flutter build apk --release --dart-define-from-file=.env.prod \
  --obfuscate --split-debug-info=build/symbols

# Android App Bundle (Play Store 제출용)
fvm flutter build appbundle --release --dart-define-from-file=.env.prod \
  --obfuscate --split-debug-info=build/symbols

# iOS (프로덕션)
fvm flutter build ipa --release --dart-define-from-file=.env.prod \
  --obfuscate --split-debug-info=build/symbols
```

#### 빌드 출력 위치
- **Android APK**: `build/app/outputs/apk/{flavor}/{buildType}/`
- **Android AAB**: `build/app/outputs/bundle/{flavor}Release/`
- **iOS IPA**: `build/ios/ipa/`

## 환경 변수

환경별 설정은 `.env.dev`, `.env.staging`, `.env.prod` 파일에서 관리합니다.

```bash
# 개발 환경
fvm flutter run --dart-define=ENV=dev

# 스테이징 환경
fvm flutter run --dart-define=ENV=staging

# 프로덕션 환경
fvm flutter run --dart-define=ENV=prod
```

## 아키텍처

- **Clean Architecture**: Domain, Data, Presentation 레이어 분리
- **Feature-First**: 기능별 디렉토리 구조
- **Riverpod**: 상태 관리
- **GetIt**: 의존성 주입 (서비스 레이어)
- **Freezed**: 불변 데이터 모델

자세한 내용은 [trd/frontend/01-flutter-tech-stack.md](../trd/frontend/01-flutter-tech-stack.md) 참고

## 주요 패키지

### 상태 관리
- `flutter_riverpod`: Provider 기반 상태 관리
- `get_it`: 서비스 의존성 주입

### 네트워킹
- `dio`: HTTP 클라이언트
- `dio_smart_retry`: 자동 재시도
- `connectivity_plus`: 네트워크 상태 감지

### 로컬 스토리지
- `sqflite`: SQLite 데이터베이스
- `hive`: Key-Value 저장소
- `flutter_secure_storage`: 보안 저장소 (토큰)

### Firebase
- `firebase_auth`: 인증
- `firebase_messaging`: FCM 푸시 알림
- `firebase_analytics`: 사용자 분석
- `firebase_crashlytics`: 크래시 리포팅

### UI/UX
- `flutter_animate`: 애니메이션
- `cached_network_image`: 이미지 캐싱
- `shimmer`: 로딩 스켈레톤
- `go_router`: 라우팅

## 코딩 컨벤션

`rules.md`와 `analysis_options.yaml`을 준수합니다.

- 파일/디렉토리: `snake_case`
- 클래스/Enum: `PascalCase`
- 메서드/변수: `lowerCamelCase`
- 상수: `lowerCamelCase const`

## 테스트 전략

- **TDD (Test-Driven Development)**: Red-Green-Refactor
- **테스트 커버리지**: 80% 이상
- **단위 테스트**: `test/unit/`
- **위젯 테스트**: `test/widget/`
- **통합 테스트**: `integration_test/`

## 배포 (Deployment)

### 사전 준비
앱 배포 전 필수 설정을 완료해야 합니다:

1. **Firebase 설정**
   ```bash
   # Android: google-services.json 다운로드
   # iOS: GoogleService-Info.plist 다운로드
   # Firebase Console에서 각 플랫폼 앱 등록 후 다운로드
   ```

2. **환경 변수 설정**
   ```bash
   cp .env.example .env.prod
   # .env.prod 파일을 실제 프로덕션 값으로 수정
   ```

3. **Android Keystore 생성** (첫 배포 시)
   ```bash
   keytool -genkey -v -keystore ~/hotly-release-key.jks \
     -keyalg RSA -keysize 2048 -validity 10000 \
     -alias hotly-release

   # android/key.properties 파일 생성
   ```

4. **iOS Certificates** (Apple Developer Program 필요, $99/년)
   - Xcode에서 Signing & Capabilities 설정
   - Provisioning Profile 생성

### 앱 아이콘 & 스플래시 생성
```bash
# 1. assets/images/logo/ 디렉토리에 이미지 준비
#    - app_icon.png (1024x1024)
#    - splash_logo.png (1242x1242)

# 2. 아이콘 자동 생성
flutter pub run flutter_launcher_icons

# 3. 스플래시 스크린 생성
flutter pub run flutter_native_splash:create
```

### 스토어 제출
자세한 배포 가이드는 아래 문서를 참고하세요:
- **[배포 가이드](DEPLOYMENT.md)**: 전체 배포 프로세스
- **[스토어 제출 체크리스트](store/STORE_SUBMISSION_CHECKLIST.md)**: 제출 전 확인사항
- **[보안 가이드](SECURITY.md)**: 보안 설정 및 Best Practices

## CI/CD

GitHub Actions를 통한 자동화:
- Lint 및 포맷 검사
- 테스트 실행
- 빌드 검증
- 배포 (Firebase App Distribution / TestFlight)

## 문서

### 기술 문서
- [기술 스택](../trd/frontend/01-flutter-tech-stack.md)
- [데이터 플로우](../trd/frontend/02-data-flow-state-management.md)
- [성능 최적화](../trd/frontend/03-performance-optimization.md)
- [접근성](../trd/frontend/04-accessibility.md)
- [사용자 플로우](../docs/user-flows.md)
- [API 연동 가이드](../docs/api-integration-guide.md)

### 배포 문서
- **[배포 가이드](DEPLOYMENT.md)** - 전체 배포 프로세스
- **[보안 가이드](SECURITY.md)** - 보안 설정 및 체크리스트
- **[스토어 제출 체크리스트](store/STORE_SUBMISSION_CHECKLIST.md)** - 제출 전 확인사항
- [앱 설명](store/app-description-ko.md) - 앱 스토어 설명문
- [개인정보처리방침](store/privacy-policy.md)
- [이용약관](store/terms-of-service.md)

## 라이선스

Proprietary - All rights reserved
