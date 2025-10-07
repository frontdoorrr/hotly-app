# Logo Assets

이 디렉토리는 앱의 아이콘과 스플래시 이미지를 포함합니다.

## 필요한 이미지 파일

### 1. 앱 아이콘
- **app_icon.png** (1024x1024px, PNG with transparency)
  - 앱의 메인 아이콘
  - Android와 iOS 모든 크기로 자동 생성됨
  - 투명 배경 권장

- **app_icon_foreground.png** (1024x1024px, PNG with transparency)
  - Android Adaptive Icon의 전경 레이어
  - 중앙 432x432px 영역에 중요 콘텐츠 배치 (safe zone)
  - 투명 배경 필수

### 2. 스플래시 스크린
- **splash_logo.png** (1242x1242px 권장, PNG with transparency)
  - Light mode 스플래시 로고
  - 중앙에 배치될 로고 이미지

- **splash_logo_dark.png** (1242x1242px 권장, PNG with transparency)
  - Dark mode 스플래시 로고 (선택사항)

## 디자인 가이드라인

### 앱 아이콘
- **크기**: 1024x1024px (최소)
- **포맷**: PNG, 투명 배경
- **컬러**: Hotly 브랜드 컬러 사용 (#FF5722 주황-빨강)
- **스타일**: 심플하고 인식하기 쉬운 디자인
- **텍스트**: 최소화 (로고만 권장)

### Adaptive Icon (Android)
- **Background**: 단색 #FF5722 (설정됨)
- **Foreground**: 중앙 432x432px safe zone 내에 로고 배치
- **여백**: 전체 1024x1024px 캔버스 사용, 가장자리 여백 고려

### 스플래시 로고
- **크기**: 1242x1242px (3x 해상도 기준)
- **위치**: 화면 중앙에 배치
- **배경**: 투명 (배경색은 설정 파일에서 지정)
- **크기 조절**: 화면 너비의 50% 이하 권장

## 생성 방법

### 온라인 도구 사용
1. **Figma** 또는 **Canva**에서 디자인
2. Export as PNG @ 1024x1024px

### AI 생성 (권장)
1. DALL-E, Midjourney 등 AI 이미지 생성 도구 사용
2. 프롬프트 예시:
   ```
   "Modern minimalist app icon for dating hot place app,
   fire emoji combined with location pin,
   orange-red gradient, flat design, 1024x1024"
   ```

### 임시 플레이스홀더
현재 개발 단계에서는 아래 명령으로 플레이스홀더 생성:
```bash
cd frontend
# 1024x1024 빨간 사각형 생성 (ImageMagick 필요)
convert -size 1024x1024 xc:#FF5722 assets/images/logo/app_icon.png
convert -size 1024x1024 xc:#FF5722 assets/images/logo/app_icon_foreground.png
convert -size 1242x1242 xc:#FF5722 assets/images/logo/splash_logo.png
convert -size 1242x1242 xc:#D84315 assets/images/logo/splash_logo_dark.png
```

## 아이콘 생성 실행

이미지 준비 후 아래 명령 실행:

```bash
cd frontend

# 앱 아이콘 생성
flutter pub run flutter_launcher_icons

# 스플래시 스크린 생성
flutter pub run flutter_native_splash:create

# 또는 한 번에
flutter pub run flutter_launcher_icons && flutter pub run flutter_native_splash:create
```

## 확인 방법

생성 후 확인할 파일들:

### Android
- `android/app/src/main/res/mipmap-*/ic_launcher.png`
- `android/app/src/main/res/drawable/launch_background.xml`

### iOS
- `ios/Runner/Assets.xcassets/AppIcon.appiconset/`
- `ios/Runner/Assets.xcassets/LaunchImage.imageset/`

## 브랜드 컬러

- **Primary**: `#FF5722` (Deep Orange)
- **Primary Dark**: `#D84315` (Darker Orange-Red)
- **Accent**: `#FFC107` (Amber)
- **Background Light**: `#FFFFFF`
- **Background Dark**: `#1A1A1A`
