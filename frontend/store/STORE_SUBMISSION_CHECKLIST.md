# 스토어 제출 체크리스트

## 🎯 배포 전 최종 점검

### 공통 준비사항
- [ ] 앱 버전 확인 (`pubspec.yaml`: version 1.0.0+1)
- [ ] 프로덕션 환경 변수 설정 (`.env.prod`)
- [ ] Firebase 프로젝트 설정 완료 (Authentication, Messaging, Analytics)
- [ ] API 키 프로덕션 값으로 교체
- [ ] 디버그 로그 비활성화 확인
- [ ] 개인정보처리방침 URL 준비
- [ ] 이용약관 URL 준비

---

## 📱 Android (Google Play Store)

### 1. 계정 및 설정
- [ ] Google Play Console 개발자 계정 등록 ($25 일회성)
- [ ] Merchant 계정 설정 (인앱 결제 사용 시)

### 2. 빌드 파일
- [ ] Keystore 생성 및 안전하게 보관
- [ ] `key.properties` 설정
- [ ] `google-services.json` 프로덕션 파일 교체
- [ ] Release AAB 빌드 성공 (`./scripts/build-android.sh prod release`)
- [ ] APK 크기 확인 (권장: < 150MB)

### 3. 스토어 등록 정보

#### 앱 정보
- [ ] 앱 이름: **Hotly**
- [ ] 짧은 설명 (80자): "AI가 추천하는 핫플레이스! 데이트 코스부터 맛집까지, 나만의 장소 컬렉션"
- [ ] 전체 설명: `store/app-description-ko.md` 참고
- [ ] 카테고리: **라이프스타일** 또는 **여행 및 지역정보**
- [ ] 콘텐츠 등급: **만 3세 이상**

#### 그래픽 자료
**스크린샷 (필수)**
- [ ] Phone: 최소 2개, 최대 8개 (1080x1920 또는 1440x2560 권장)
  - [ ] 홈 화면 (장소 리스트)
  - [ ] 링크 분석 화면
  - [ ] 지도 화면
  - [ ] 코스 생성 화면
  - [ ] 장소 상세 화면
  - [ ] 프로필 화면

**아이콘 및 배너**
- [ ] 앱 아이콘: 512x512 PNG (이미 생성됨)
- [ ] 기능 그래픽: 1024x500 PNG (필수)
- [ ] Promo 비디오 (선택사항): YouTube 링크

#### 정책 문서
- [ ] 개인정보처리방침 URL: https://hotly.app/privacy
- [ ] 이용약관 URL: https://hotly.app/terms
- [ ] 연락처 이메일: support@hotly.app
- [ ] 웹사이트 URL: https://hotly.app

#### 가격 및 배포
- [ ] 가격: 무료
- [ ] 배포 국가: 대한민국 (추후 확대 가능)
- [ ] 콘텐츠 등급 설정 완료

### 4. 테스트
- [ ] 실제 기기에서 release 빌드 테스트
- [ ] ProGuard 난독화 확인
- [ ] 크래시 없음 확인
- [ ] 성능 테스트 (앱 시작 속도 < 3초)

---

## 🍎 iOS (Apple App Store)

### 1. 계정 및 설정
- [ ] Apple Developer Program 가입 ($99/년)
- [ ] App ID 생성: `com.hotly.hotly_app`
- [ ] Capabilities 활성화:
  - [ ] Push Notifications
  - [ ] Sign in with Apple
  - [ ] Associated Domains

### 2. 인증서 및 프로비저닝
- [ ] Distribution Certificate 생성
- [ ] App Store Provisioning Profile 생성
- [ ] Xcode에서 Signing 설정 완료

### 3. 빌드 파일
- [ ] `GoogleService-Info.plist` 프로덕션 파일 교체
- [ ] CocoaPods 설치 완료 (`pod install`)
- [ ] Release IPA 빌드 성공 (`./scripts/build-ios.sh prod release`)
- [ ] IPA 크기 확인 (권장: < 200MB)

### 4. App Store Connect 설정

#### 앱 정보
- [ ] 앱 이름: **Hotly**
- [ ] 부제목 (30자): "AI 핫플레이스 아카이빙"
- [ ] 카테고리: **라이프스타일**
- [ ] 콘텐츠 등급: **만 4+**

#### 설명
- [ ] 한국어 설명: `store/app-description-ko.md` 참고
- [ ] 프로모션 텍스트 (170자): "새로운 업데이트! AI 링크 분석으로 SNS 핫플을 한 번에 저장하세요."
- [ ] 키워드 (100자): "핫플,맛집,데이트,카페,여행,지도,코스,추천,SNS,인스타그램"

#### 스크린샷
**iPhone (필수)**
- [ ] 6.7" (iPhone 15 Pro Max): 1290x2796
  - [ ] 최소 3개, 최대 10개

**iPad (선택사항)**
- [ ] 12.9" (iPad Pro): 2048x2732

#### 앱 미리보기 (선택사항)
- [ ] 15-30초 비디오
- [ ] .mov 또는 .mp4 형식

#### 정책 및 정보
- [ ] 개인정보처리방침 URL: https://hotly.app/privacy
- [ ] 이용약관 URL (선택): https://hotly.app/terms
- [ ] 지원 URL: https://hotly.app/support
- [ ] 마케팅 URL: https://hotly.app
- [ ] 저작권: 2025 Hotly Inc.

#### 앱 리뷰 정보
- [ ] 연락처 이름
- [ ] 연락처 전화번호
- [ ] 연락처 이메일
- [ ] 데모 계정 (필요 시):
  - [ ] 사용자명: demo@hotly.app
  - [ ] 비밀번호: Demo1234!

#### 버전 정보
- [ ] 버전 번호: 1.0.0
- [ ] 빌드 번호: 1
- [ ] 새로운 기능:
  ```
  첫 출시! 🎉

  ✨ 주요 기능
  • AI 기반 링크 분석
  • 카카오맵 연동
  • 데이트 코스 생성
  • 소셜 기능

  지금 다운로드하고 나만의 핫플 컬렉션을 시작하세요!
  ```

### 5. 빌드 업로드
- [ ] Transporter로 IPA 업로드 완료
- [ ] App Store Connect에서 빌드 선택
- [ ] TestFlight 내부 테스트 완료
- [ ] 크래시 없음 확인

### 6. Export Compliance
- [ ] 암호화 사용 여부: Yes (HTTPS 사용)
- [ ] Export Compliance 문서 제출 (필요 시)

---

## 🖼️ 그래픽 자료 제작 가이드

### 스크린샷 캡처
```bash
# iPhone 시뮬레이터 실행
flutter run --release

# 스크린샷 캡처: Cmd + S

# 권장 기기:
# - iPhone 15 Pro Max (6.7")
# - iPhone 15 Pro (6.1")
```

### 기능 그래픽 (Feature Graphic)
**크기**: 1024x500 PNG

**포함 요소**:
- Hotly 로고
- 주요 화면 스크린샷 2-3개
- 캐치프레이즈: "AI가 찾아주는 나만의 핫플레이스"
- 브랜드 컬러: #FF5722

**제작 도구**:
- Figma (무료)
- Canva (무료)
- Adobe Illustrator

---

## 📋 제출 전 최종 테스트

### 기능 테스트
- [ ] 회원가입 / 로그인
- [ ] 소셜 로그인 (Google, Apple)
- [ ] 링크 분석
- [ ] 장소 저장
- [ ] 지도 보기
- [ ] 코스 생성
- [ ] 공유 기능
- [ ] 푸시 알림
- [ ] 프로필 수정
- [ ] 설정 변경

### 성능 테스트
- [ ] 앱 시작 속도 < 3초
- [ ] 화면 전환 부드러움
- [ ] 메모리 사용량 정상
- [ ] 배터리 소모 정상
- [ ] 오프라인 모드 동작

### 보안 테스트
- [ ] HTTPS 통신만 사용
- [ ] 민감 정보 암호화 확인
- [ ] 로그에 민감 정보 노출 없음
- [ ] ProGuard/난독화 적용 확인

---

## 🚀 제출 단계

### Google Play Store
1. [ ] Play Console 접속
2. [ ] "앱 만들기" 클릭
3. [ ] 앱 정보 입력
4. [ ] AAB 파일 업로드
5. [ ] 스크린샷 및 그래픽 업로드
6. [ ] 콘텐츠 등급 설정
7. [ ] 가격 및 배포 설정
8. [ ] 개인정보처리방침 URL 입력
9. [ ] **"검토를 위해 제출"** 클릭
10. [ ] 검토 대기 (보통 1-3일)

### Apple App Store
1. [ ] App Store Connect 접속
2. [ ] "나의 앱" > "+" > "새로운 앱"
3. [ ] 앱 정보 입력
4. [ ] 스크린샷 및 미리보기 업로드
5. [ ] 빌드 선택
6. [ ] 앱 리뷰 정보 입력
7. [ ] 개인정보처리방침 URL 입력
8. [ ] **"심사 제출"** 클릭
9. [ ] 심사 대기 (보통 1-2일)

---

## 📊 제출 후 모니터링

### 출시 후 1주일
- [ ] 크래시 리포트 확인 (Firebase Crashlytics)
- [ ] 사용자 피드백 모니터링
- [ ] 앱 스토어 리뷰 응답
- [ ] 성능 지표 확인 (Firebase Analytics)

### 출시 후 1개월
- [ ] 버그 수정 업데이트 준비
- [ ] 사용자 요청 기능 검토
- [ ] A/B 테스트 계획

---

## 🎉 출시 완료 후

### 마케팅
- [ ] 소셜 미디어 공지 (Instagram, Facebook)
- [ ] 블로그 포스트 작성
- [ ] 보도자료 배포
- [ ] 앱 스토어 최적화 (ASO)

### 유지보수
- [ ] 주간 크래시 리포트 검토
- [ ] 월간 성능 리포트 작성
- [ ] 분기별 기능 업데이트

---

## 📞 문의 및 지원

**Google Play Console 지원**
- https://support.google.com/googleplay/android-developer

**App Store Connect 지원**
- https://developer.apple.com/support/app-store-connect/

**Hotly 내부 지원**
- 개발팀: dev@hotly.app
- 디자인팀: design@hotly.app

---

**마지막 업데이트**: 2025년 1월 1일
