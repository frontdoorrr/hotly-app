# Logo & Brand Asset Guide

ArchyAI(hotly-app) 로고 자산의 종류, 사이즈, 용도, 적용 방법을 정리한 문서입니다.

## 1. 로고 종류

`frontend/assets/images/logo/` 하위에 3종의 로고가 SVG 원본 + 사전 렌더링된 PNG로 보관되어 있습니다.

| 종류 | 원본 SVG | 구성 | 용도 |
|---|---|---|---|
| **Icon** | `logo-icon.svg` | 심볼 단독 (정방형) | 앱 아이콘, 파비콘, 작은 영역 |
| **Compact** | `logo-compact.svg` | 심볼 + 짧은 브랜드 마크 (정방형) | 스플래시, 카드형 UI |
| **Wordmark** | `logo-wordmark.svg` | 심볼 + 풀 워드마크 (가로형) | 인앱 헤더, 랜딩 페이지, 문서 |

### 사전 렌더링된 PNG 사이즈

```
logo-icon-{16,32,48,64,128,180,192,256,512,1024}.png   # 정방형
logo-compact-{64,128,256,512,1024}.png                  # 정방형
logo-wordmark-{240x60,480x120,720x180,1200x300}.png    # 가로 4:1
```

> SVG 원본 수정 후 PNG를 다시 만들 때는 아래 명령 사용:
> ```bash
> brew install librsvg
> cd frontend/assets/images/logo
> rsvg-convert -w 1024 -h 1024 logo-icon.svg -o logo-icon-1024.png
> ```

## 2. 용도별 매핑

### 모바일 앱 아이콘 (iOS / Android)
- **소스**: `logo-icon-1024.png`
- **빌드 입력**: `assets/images/logo/app_icon.png`, `app_icon_foreground.png`
- **설정 파일**: `frontend/flutter_launcher_icons.yaml`
- **생성 명령**:
  ```bash
  cd frontend
  dart run flutter_launcher_icons
  ```
- **결과**:
  - Android: `android/app/src/main/res/mipmap-*/ic_launcher.png`
  - iOS: `ios/Runner/Assets.xcassets/AppIcon.appiconset/`

### 스플래시 스크린
- **소스**: `logo-compact-1024.png` (심볼 + 짧은 브랜드 마크)
- **빌드 입력**: `assets/images/logo/splash_logo.png`, `splash_logo_dark.png`
- **설정 파일**: `frontend/pubspec.yaml`의 `flutter_native_splash` 섹션 또는 `flutter_native_splash.yaml`
- **생성 명령**:
  ```bash
  cd frontend
  dart run flutter_native_splash:create
  ```

### 웹 파비콘 / PWA
- **루트 파비콘**: `frontend/web/favicon.png` ← `logo-icon-32.png`
- **PWA 아이콘**:
  - `frontend/web/icons/Icon-192.png` ← `logo-icon-192.png`
  - `frontend/web/icons/Icon-512.png` ← `logo-icon-512.png`
  - `frontend/web/icons/Icon-maskable-192.png` ← `logo-icon-192.png`
  - `frontend/web/icons/Icon-maskable-512.png` ← `logo-icon-512.png`
- **Apple Touch Icon (180×180)**: 필요 시 `logo-icon-180.png`을 `web/icons/` 또는 `web/`에 두고 `index.html`의 `<link rel="apple-touch-icon">`로 연결

### 인앱 헤더 / AppBar
- **소스**: `logo-wordmark-240x60.png`(또는 480x120 @2x)
- **권장 코드**:
  ```dart
  AppBar(
    title: Image.asset(
      'assets/images/logo/logo-wordmark-480x120.png',
      height: 28,
      fit: BoxFit.contain,
    ),
  )
  ```
- 다크모드에서 색이 안 맞으면 워드마크 다크 변형(추가 시) 또는 `ColorFiltered` 사용

## 3. 브랜드 컬러

| 토큰 | HEX | 용도 |
|---|---|---|
| Primary | `#FF5722` | 메인 액션, 강조 |
| Primary Dark | `#D84315` | hover/pressed, 다크모드 강조 |
| Accent | `#FFC107` | 보조 강조 |
| BG Light | `#FFFFFF` | 라이트 배경, 스플래시 배경 |
| BG Dark | `#1A1A1A` | 다크 배경 |

코드 토큰은 `frontend/lib/core/theme/`의 색상 정의와 일치시킵니다.

## 4. 디자인 가드레일

- **클리어스페이스**: 워드마크 좌우/상하 최소 여백 = 심볼 높이의 25%
- **최소 사용 크기**:
  - Icon: 16px (1x), 32px 이상 권장
  - Wordmark: 가로 120px 이상
- **금지 사항**:
  - 비례 왜곡(가로/세로 한쪽만 늘리기)
  - 임의 색상 변경 (브랜드 팔레트 외)
  - 그림자/외곽선 등 효과 추가
- **배경 대비**: 충분한 대비가 안 나오는 배경 위에는 단색 박스(흰색/검정)를 깔고 배치

## 5. 자산 변경 시 체크리스트

로고 디자인을 변경했을 때 동기화해야 할 항목:

- [ ] `logo-icon.svg`, `logo-compact.svg`, `logo-wordmark.svg` 원본 갱신
- [ ] PNG 사이즈 일괄 재생성 (rsvg-convert 또는 `generate_icons.sh`)
- [ ] `app_icon.png`, `app_icon_foreground.png`, `splash_logo.png` 교체
- [ ] `dart run flutter_launcher_icons`
- [ ] `dart run flutter_native_splash:create`
- [ ] `web/favicon.png`, `web/icons/Icon-{192,512}.png` 교체
- [ ] iOS 시뮬레이터/실기기에서 아이콘 캐시 초기화 (`flutter clean` 후 재빌드)
- [ ] Android: 일부 런처는 캐시되므로 앱 제거 후 재설치하여 검증

## 6. 참고

- 원본 SVG는 디자인 소스 오브 트루스(SoT)입니다. PNG는 빌드 산출물로 취급하되, 사이즈별 사전 렌더링본은 커밋합니다 (외부 도구 의존을 줄이기 위함).
- `frontend/assets/images/logo/README.md`는 초기 가이드(플레이스홀더 생성용)이며, 본 문서가 최신 SoT입니다.
