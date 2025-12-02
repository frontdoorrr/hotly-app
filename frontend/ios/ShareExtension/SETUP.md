# iOS Share Extension 설정 가이드

## 1. Xcode에서 Share Extension Target 추가

1. Xcode에서 `Runner.xcworkspace` 열기
2. File > New > Target 선택
3. iOS > Share Extension 선택
4. 설정:
   - Product Name: `ShareExtension`
   - Language: Swift
   - Bundle Identifier: `com.hotly.hotly-app.ShareExtension`
   - Embed In Application: Runner

## 2. 파일 추가

이미 생성된 파일들을 Target에 추가:
- `ShareViewController.swift`
- `Info.plist`
- `MainInterface.storyboard`
- `ShareExtension.entitlements`

## 3. App Groups 설정

### Apple Developer Console
1. Certificates, Identifiers & Profiles 접속
2. Identifiers > App Groups 생성
3. `group.com.hotly.app.sharequeue` 그룹 생성

### Xcode - Main App (Runner)
1. Runner Target > Signing & Capabilities
2. + Capability > App Groups
3. ✅ `group.com.hotly.app.sharequeue` 체크

### Xcode - Share Extension
1. ShareExtension Target > Signing & Capabilities
2. + Capability > App Groups
3. ✅ `group.com.hotly.app.sharequeue` 체크

## 4. Build Settings

### ShareExtension Target
1. Build Settings > Skip Install: Yes
2. Build Settings > Code Signing Entitlements: `ShareExtension/ShareExtension.entitlements`

## 5. Podfile 수정

```ruby
target 'ShareExtension' do
  use_frameworks!
  # Share Extension은 최소한의 의존성만 필요
end
```

## 6. 빌드 및 테스트

1. ShareExtension scheme 선택
2. 실행하면 iOS Simulator에서 앱 선택 화면 표시
3. Instagram/Safari 등에서 공유 테스트

## 트러블슈팅

### App Groups 데이터 공유 안됨
- 두 Target 모두 같은 Team ID로 서명 필요
- App Groups identifier가 정확히 일치하는지 확인

### Share Extension이 표시되지 않음
- Info.plist의 NSExtensionActivationRule 확인
- 지원하는 URL 타입 확인

### 메모리 제한
- Share Extension 메모리 제한: 약 30MB
- 큰 이미지나 많은 데이터 처리 시 주의

## 버전 동기화

Main App과 Share Extension의 버전을 동기화:
- `Runner/Info.plist`
- `ShareExtension/Info.plist`

둘 다 같은 `CFBundleShortVersionString`과 `CFBundleVersion` 사용
