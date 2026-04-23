# ArchyAI App — UI Design System

Flutter 앱 기준으로 실제 구현된 디자인 시스템 현황입니다.

---

## 1. 기술 스택

- **프레임워크**: Flutter (Dart)
- **상태관리**: Riverpod
- **폰트**: Google Fonts — Noto Sans KR
- **Material**: Material 3 (`useMaterial3: true`)
- **테마 파일**: `frontend/lib/core/theme/`

---

## 2. Color Tokens — ArchyAI Dark Palette

> 파일: `app_colors.dart`  
> 앱은 **다크 테마 단일 기준**으로 운영됩니다.

### Brand — Teal
| 토큰 | 값 | 용도 |
|---|---|---|
| `teal400` / `primary` / `primary500` | `#1D9E75` | 브랜드 메인 (버튼, 강조, CTA) |
| `teal600` / `primary600` | `#0D7A57` | 버튼 hover / Secondary |
| `brandSubtle` / `primary50` / `primary100` | `#0A2318` | 연한 브랜드 배경 (칩, 뱃지 bg) |
| `primary900` | `#07150F` | 진한 브랜드 강조 |

### Semantic
| 토큰 | 값 | 용도 |
|---|---|---|
| `success` | `#38A169` | 성공 상태 |
| `warning` | `#D69E2E` | 경고 |
| `error` | `#E53E3E` | 에러 |
| `info` | `#3182CE` | 정보 |

### Dark Background Scale
| 토큰 | 값 | 용도 |
|---|---|---|
| `bgBase` / `gray900` | `#090C10` | 최하층 배경 (scaffold) |
| `bgElevated` / `gray50` | `#0D1118` | 살짝 올라온 배경 (input fill) |
| `surfaceDefault` / `gray700` | `#141620` | 카드 / 시트 / BottomNav 배경 |
| `borderSubtle` / `gray200` | `#1A2030` | 구분선 / 보더 |
| `gray100` | `#111620` | 내부 구분 배경 |
| `gray500` | `#5A7A72` | 비활성 아이콘 |

### Text
| 토큰 | 값 | 용도 |
|---|---|---|
| `textPrimary` | `#D4EEE8` | 기본 텍스트 |
| `textSecondary` | `#8AADA6` | 보조 텍스트 |
| `textTertiary` / `gray500` | `#5A7A72` | 비활성 / 힌트 텍스트 |

### Alias 요약
| 토큰 | 실제 값 |
|---|---|
| `background` / `backgroundDark` | `bgBase` (#090C10) |
| `backgroundLight` | `bgElevated` (#0D1118) |
| `surface` / `cardLight` / `cardDark` | `surfaceDefault` (#141620) |
| `border` / `borderLight` / `borderDark` | `borderSubtle` (#1A2030) |

---

## 3. Typography

> 파일: `app_text_styles.dart`  
> 폰트 스택: `'Google Sans'` (primary) → `'Noto Sans KR'` (fallback) → `sans-serif`  
> `app_theme.dart`에서 `fontFamily: 'Google Sans'`로 전역 적용, Google Fonts notoSansKr로 폴백

### 폰트 사이즈
| 상수 | 값 |
|---|---|
| `fontSizeXs` | 12px |
| `fontSizeSm` | 14px |
| `fontSizeBase` | 16px |
| `fontSizeLg` | 18px |
| `fontSizeXl` | 20px |
| `fontSize2xl` | 24px |
| `fontSize3xl` | 30px |

### 폰트 웨이트 (실제 적용값)
| 상수 | 값 | 의미 |
|---|---|---|
| `fontWeightNormal` | w500 | Medium |
| `fontWeightMedium` | w600 | SemiBold |
| `fontWeightSemibold` | w700 | Bold |
| `fontWeightBold` | w800 | ExtraBold |

### 텍스트 스타일
| 스타일 | 사이즈 | 웨이트 | line-height | 용도 |
|---|---|---|---|---|
| `h1` | 30px | w800 | 1.3 | 페이지 타이틀 |
| `h2` | 24px | w800 | 1.3 | 섹션 타이틀 |
| `h3` | 20px | w700 | 1.4 | 서브 타이틀 |
| `h4` | 18px | w700 | 1.4 | 카드 제목 |
| `bodyLarge` / `body1` | 16px | w500 | 1.5 | 본문 |
| `bodyMedium` / `body2` | 14px | w500 | 1.5 | 보조 본문 |
| `bodySmall` | 12px | w500 | 1.5 | 캡션 |
| `labelLarge` / `label1` | 16px | w600 | 1.2 | 버튼, 레이블 |
| `labelMedium` / `label2` | 14px | w600 | 1.2 | 소형 레이블 |
| `labelSmall` / `label3` | 12px | w600 | 1.2 | 뱃지, 태그 |
| `button` | 16px | w700 | 1.0 | 버튼 전용 |

### Material TextTheme 매핑
| Material 역할 | 매핑 |
|---|---|
| `displayLarge` | `h1` |
| `displayMedium` | `h2` |
| `displaySmall` | `h3` |
| `headlineMedium` | `h4` |
| `titleLarge` | `h3` (섹션 제목) |
| `bodyLarge/Medium/Small` | 각각 대응 |
| `labelLarge/Medium/Small` | 각각 대응 |

---

## 4. Spacing System

> 파일: `app_theme.dart`

| 상수 | 값 |
|---|---|
| `space0` | 0 |
| `space1` | 4px |
| `space2` | 8px |
| `space3` | 12px |
| `space4` | 16px |
| `space5` | 20px |
| `space6` | 24px |
| `space8` | 32px |
| `space10` | 40px |
| `space12` | 48px |
| `space16` | 64px |

---

## 5. Border Radius

> 파일: `app_theme.dart`

| 상수 | 값 |
|---|---|
| `radiusNone` | 0 |
| `radiusSm` | 2px |
| `radiusBase` | 4px |
| `radiusMd` | 6px |
| `radiusLg` | 8px |
| `radiusXl` | 12px |
| `radius2xl` | 16px |
| `radiusFull` | 9999px |

---

## 6. 테마 컴포넌트 기본값

> 파일: `app_theme.dart`  
> **lightTheme / darkTheme 통일 — 다크 테마 단일 운영**  
> `AppTheme.lightTheme == AppTheme.darkTheme == _base`

### AppBar
- elevation: 0
- 배경: `bgBase` (#090C10)
- 텍스트: `textPrimary` (#D4EEE8)
- 타이틀: Google Sans / Noto Sans KR 18px / w600
- systemOverlayStyle: light

### Card
- elevation: **0** (변경)
- border: **0.5px solid `borderSubtle`** (#1A2030) (추가)
- radius: `radiusLg` (8px)
- 배경: `surfaceDefault` (#141620)

### ElevatedButton
- 배경: `teal400` (#1D9E75)
- 텍스트: `white`
- 패딩: 24px 가로 / 16px 세로
- radius: `radiusLg` (8px)
- elevation: 0

### OutlinedButton
- 색상: `teal400`
- border: 1.5px solid `teal400`
- radius: `radiusLg`

### TextButton (ghost)
- 색상: `teal400`
- 패딩: 16px 가로 / 12px 세로

### Input
- 배경: `bgElevated` (#0D1118)
- border: 1px solid `borderSubtle` → 포커스 시 2px `teal400`
- hint 색: `textTertiary`
- radius: `radiusLg` (8px)
- 패딩: 16px 가로 / 12px 세로

### BottomNavigationBar
- 배경: `surfaceDefault` (#141620)
- 선택: `teal400` (#1D9E75)
- 비선택: `textTertiary` (#5A7A72)
- type: fixed / elevation: 0

### Divider
- 색: `borderSubtle` (#1A2030) / thickness: 0.5

---

## 7. 구현된 Atom 컴포넌트

> 파일: `frontend/lib/shared/widgets/atoms/`

### AppButton (`app_button.dart`)
```dart
AppButton(
  text: '장소 저장',
  variant: ButtonVariant.primary,  // primary | secondary | outline | ghost
  size: ButtonSize.md,             // sm | md | lg
  isLoading: false,
  isDisabled: false,
  icon: const Icon(Icons.save),
  width: double.infinity,
  onPressed: () {},
)
```

**사이즈 스펙:**
| Size | Height | 가로 패딩 | 폰트 |
|---|---|---|---|
| sm | 36px | 16px | 14px |
| md | 44px | 24px | 16px |
| lg | 52px | 32px | 18px |

### AppInput (`app_input.dart`)
```dart
AppInput(
  label: '장소명',
  placeholder: '장소를 입력하세요',
  isRequired: true,
  leftIcon: const Icon(Icons.search),   // prefixIcon alias
  rightIcon: const Icon(Icons.clear),   // suffixIcon alias
  onChanged: (v) {},
  validator: (v) => v!.isEmpty ? '필수' : null,
  controller: _controller,
)
```

---

## 8. 구현된 공용 위젯

> 파일: `frontend/lib/core/widgets/`

### `error_view.dart` — 상태 표시 3종 세트

#### ErrorView
```dart
ErrorView(message: '오류 메시지', icon: Icons.error_outline, onRetry: () {})

// 팩토리 생성자
ErrorView.network(onRetry: () {})   // 네트워크 오류
ErrorView.server(onRetry: () {})    // 서버 오류
ErrorView.notFound()                // 데이터 없음
```

#### EmptyView
```dart
EmptyView(
  message: '저장된 장소가 없습니다',
  subtitle: '마음에 드는 장소를 저장해보세요',
  icon: Icons.place_outlined,
  onAction: () {},
  actionLabel: '장소 찾아보기',
)

// 팩토리 생성자
EmptyView.search(query: '검색어')
EmptyView.places(onAddPlace: () {})
EmptyView.courses(onCreateCourse: () {})
```

#### LoadingView
```dart
LoadingView(message: '불러오는 중...')  // message 생략 가능
```

### `PaginatedListView<T>` (`paginated_list_view.dart`)
```dart
PaginatedListView<Place>(
  fetchData: (page) async => await repo.getPlaces(page),
  itemBuilder: (context, place) => PlaceCard(place: place),
  pageSize: 20,
  separator: const Divider(),
  emptyWidget: EmptyView.places(),
  errorWidget: ErrorView.server(),
)
```
- `infinite_scroll_pagination` 패키지 기반
- 1-based page key 사용

---

## 9. 피처별 구현 위젯 현황

### Archive
- `ArchiveInputSheet` — SNS URL 입력 바텀시트 (DraggableScrollableSheet)
- `ArchiveListView` — 아카이브 목록
- `ArchiveResultCard` — 분석 결과 카드
- `type_cards/` — place / event / tips / review 타입별 카드

### Map
- `MapSearchBar` — 지도 검색바
- `PlaceMarkerInfo` — 마커 정보 팝업
- `SearchResultInfo` — 검색 결과 정보 카드

### Home
- `PlaceCard` — 장소 카드

### Course
- `CoursePlaceCard` — 코스 내 장소 카드
- `RouteInfoCard` — 경로 정보 카드

### Saved
- `TagFilterChips` — 가로 스크롤 태그 필터 칩 (전체/개별 태그, 더보기, 카운트, 이모지 자동 매핑)

### Share Queue
- `BatchProcessingSheet` — 일괄 처리 바텀시트
- `ShareQueueBadge` — 큐 배지 (대기 상태 / 진행 상태 LinearProgressIndicator 포함)
- `ShareQueueMiniBadge` — 아이콘 위에 올라가는 소형 숫자 배지 (9+ 처리)

---

## 10. 앱 구조 (Feature-Based)

```
lib/
├── core/
│   ├── theme/          # 디자인 토큰 (colors, text, theme)
│   ├── network/        # DioClient, ApiEndpoints
│   ├── router/         # GoRouter 설정
│   └── widgets/        # 공용 코어 위젯
├── shared/
│   ├── models/         # User, Place, Course, Tag 등 공유 모델
│   └── widgets/
│       └── atoms/      # AppButton, AppInput
└── features/
    ├── auth/           # 로그인, 회원가입
    ├── home/           # 홈 화면
    ├── map/            # 지도 (Kakao Maps SDK)
    ├── search/         # 검색
    ├── place/          # 장소 상세
    ├── course/         # 코스
    ├── archive/        # SNS 링크 아카이빙
    ├── saved/          # 저장한 장소
    ├── profile/        # 프로필
    ├── share_queue/    # 공유 큐
    └── onboarding/     # 온보딩
```

---

## 11. 미구현 / 계획 항목

- Skeleton Loader 컴포넌트
- Toast / Snackbar 공용 래퍼
- 다크 모드 완전 적용 (테마 정의는 있으나 일부 위젯 미대응)
- 공용 Avatar 컴포넌트

---

*최종 업데이트: 2026-04-19*  
*기준: Flutter 앱 실제 구현 코드 — ArchyAI Dark Theme 적용*
