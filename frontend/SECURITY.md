# Security Guidelines for Hotly App

## 코드 난독화 (Obfuscation)

### Flutter 빌드 시 자동 적용
```bash
# Android & iOS 릴리즈 빌드 시 자동으로 난독화 적용
flutter build apk --release --obfuscate --split-debug-info=build/symbols
flutter build ipa --release --obfuscate --split-debug-info=build/symbols
```

### ProGuard (Android)
- `android/app/proguard-rules.pro`에 난독화 규칙 정의
- Release 빌드 시 자동 적용 (`isMinifyEnabled = true`)
- 주요 규칙:
  - Flutter/Dart 코드 보호
  - Firebase SDK keep
  - JSON 직렬화 클래스 keep

### Symbol Files
- 난독화된 코드의 디버깅을 위해 symbol 파일 보관
- 위치: `build/symbols/`
- **중요**: 각 릴리즈 버전의 symbol 파일을 백업!

---

## 환경 변수 보안

### 절대 Git에 커밋 금지
```bash
# .gitignore에 포함된 파일들
.env.dev
.env.prod
.env.staging
*.jks
*.p12
key.properties
google-services.json
GoogleService-Info.plist
```

### 안전한 저장 방법
1. **로컬 개발**: `.env.dev` 파일 사용 (gitignore)
2. **CI/CD**: GitHub Secrets, GitLab CI Variables
3. **프로덕션**: 환경 변수는 빌드 시점에 주입

---

## 데이터 보안

### 1. Secure Storage
```dart
// flutter_secure_storage 사용
final storage = FlutterSecureStorage();

// 토큰, 비밀번호 등 민감 정보 저장
await storage.write(key: 'access_token', value: token);

// 일반 설정은 SharedPreferences 사용
final prefs = await SharedPreferences.getInstance();
await prefs.setBool('dark_mode', true);
```

### 2. API 통신
- **HTTPS만 사용** (network_security_config.xml 참조)
- Certificate Pinning (선택사항)
- 요청/응답 암호화

### 3. 로컬 데이터베이스
```dart
// SQLite 암호화 (sqflite_sqlcipher)
final database = await openDatabase(
  path,
  password: 'user-specific-key',
);
```

---

## 인증 및 권한

### 1. Firebase Auth
- Multi-factor Authentication (MFA) 활성화 권장
- 익명 로그인 비활성화 (프로덕션)

### 3. 권한 최소화
```xml
<!-- 필요한 권한만 요청 -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

---

## 코드 보안

### 1. 하드코딩 금지
```dart
// ❌ 나쁜 예
const apiKey = 'AIzaSyABC123...';

// ✅ 좋은 예
final apiKey = dotenv.env['KAKAO_MAP_API_KEY']!;
```

### 2. 민감 로그 제거
```dart
// Release 빌드에서 로그 비활성화
if (kReleaseMode) {
  debugPrint = (String? message, {int? wrapWidth}) {};
}

// 또는 조건부 로깅
void log(String message) {
  if (kDebugMode) {
    print(message);
  }
}
```

### 3. SQL Injection 방지
```dart
// ✅ Parameterized queries 사용
await db.query(
  'users',
  where: 'id = ?',
  whereArgs: [userId],
);
```

---

## 네트워크 보안

### Android Network Security Config
```xml
<!-- android/app/src/main/res/xml/network_security_config.xml -->
<network-security-config>
  <!-- Production: HTTPS only -->
  <base-config cleartextTrafficPermitted="false">
    <trust-anchors>
      <certificates src="system" />
    </trust-anchors>
  </base-config>
</network-security-config>
```

### iOS App Transport Security
```xml
<!-- ios/Runner/Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsArbitraryLoads</key>
  <false/>
</dict>
```

---

## 취약점 스캔

### Dart/Flutter Packages
```bash
# 취약한 패키지 확인
flutter pub outdated
flutter pub upgrade --major-versions

# 의존성 트리 확인
flutter pub deps
```

### Android
```bash
# Gradle dependency check
cd android
./gradlew dependencyCheckAnalyze
```

### iOS
```bash
# CocoaPods 보안 업데이트
cd ios
pod outdated
pod update
```

---

## OWASP Mobile Top 10 대응

### M1: Improper Platform Usage
- ✅ iOS/Android 권한 시스템 올바르게 사용
- ✅ Platform channel 보안 검증

### M2: Insecure Data Storage
- ✅ FlutterSecureStorage로 민감 데이터 암호화
- ✅ 로그에 민감 정보 출력 금지

### M3: Insecure Communication
- ✅ HTTPS only
- ✅ Certificate pinning (선택)

### M4: Insecure Authentication
- ✅ Firebase Auth + Custom Claims
- ✅ JWT 토큰 만료 관리

### M5: Insufficient Cryptography
- ✅ Flutter 내장 암호화 사용
- ✅ 하드코딩된 키 사용 금지

### M6: Insecure Authorization
- ✅ 백엔드에서 권한 검증
- ✅ 클라이언트 측 검증은 UX용

### M7: Client Code Quality
- ✅ Dart analyzer 활성화
- ✅ 정적 분석 도구 사용

### M8: Code Tampering
- ✅ 코드 난독화 (`--obfuscate`)
- ✅ Jailbreak/Root 탐지 (선택)

### M9: Reverse Engineering
- ✅ ProGuard/R8 난독화
- ✅ Native code obfuscation

### M10: Extraneous Functionality
- ✅ Debug 코드 프로덕션 제거
- ✅ 테스트 계정 비활성화

---

## 정기 보안 점검

### 월간
- [ ] 의존성 취약점 스캔
- [ ] Firebase 보안 설정 확인
- [ ] API 키 로테이션

### 분기별
- [ ] 코드 보안 감사
- [ ] 권한 최소화 검토
- [ ] 로그 검토 (민감 정보 노출 확인)

### 연간
- [ ] 침투 테스트 (Penetration Testing)
- [ ] 보안 감사 (Security Audit)
- [ ] 개인정보처리방침 업데이트

---

## 사고 대응 (Incident Response)

### 보안 사고 발견 시
1. **즉시 조치**
   - 영향받는 API 키 즉시 폐기
   - 사용자에게 비밀번호 재설정 요청

2. **조사**
   - Firebase Crashlytics 로그 확인
   - Firebase Analytics 로그 분석

3. **패치**
   - 취약점 수정
   - 긴급 앱 업데이트 배포

4. **사후 관리**
   - 사고 보고서 작성
   - 재발 방지 대책 수립

---

## 참고 자료

- [OWASP Mobile Security](https://owasp.org/www-project-mobile-top-10/)
- [Flutter Security Best Practices](https://docs.flutter.dev/security)
- [Android Security Guide](https://developer.android.com/topic/security/best-practices)
- [iOS Security Guide](https://support.apple.com/guide/security/welcome/web)
