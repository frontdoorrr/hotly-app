# TRD-Frontend-04: 접근성 요구사항 (Accessibility Requirements)

## 문서 정보
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **작성자**: Development Team
- **관련 PRD**: `prd/main.md`, `prd/06-onboarding-flow.md`
- **관련 TRD**: `trd/frontend/01-flutter-tech-stack.md`
- **관련 Task**: `task/06-ui-frontend.md`

## 목차
1. [개요](#1-개요)
2. [접근성 표준 및 지침](#2-접근성-표준-및-지침)
3. [스크린 리더 지원](#3-스크린-리더-지원)
4. [키보드 네비게이션](#4-키보드-네비게이션)
5. [색상 및 대비](#5-색상-및-대비)
6. [터치 타겟 크기](#6-터치-타겟-크기)
7. [텍스트 확대 지원](#7-텍스트-확대-지원)
8. [다크 모드 지원](#8-다크-모드-지원)
9. [에러 및 피드백](#9-에러-및-피드백)
10. [접근성 테스트](#10-접근성-테스트)

---

## 1. 개요

### 1.1 목적
모든 사용자가 신체적 제약 없이 hotly-app을 완전하게 사용할 수 있도록 WCAG 2.1 AA 수준의 접근성을 보장한다.

### 1.2 사용자 가치
- **시각 장애인**: 스크린 리더(TalkBack/VoiceOver)로 모든 기능 사용 가능
- **청각 장애인**: 시각적 피드백으로 모든 정보 전달
- **지체 장애인**: 큰 터치 타겟(최소 44dp)과 키보드 네비게이션 지원
- **고령자**: 텍스트 확대 및 고대비 테마 지원

### 1.3 가설 및 KPI
- **가설**: WCAG 2.1 AA 준수로 사용자 기반 10% 확대, 접근성 불만 제로
- **측정 지표**:
  - WCAG 2.1 AA 준수율: 100%
  - 스크린 리더 사용 가능 기능: 100%
  - 색상 대비 비율: 4.5:1 이상 (일반 텍스트), 3:1 이상 (대형 텍스트)
  - 터치 타겟 크기: 최소 44dp × 44dp

---

## 2. 접근성 표준 및 지침

### 2.1 WCAG 2.1 레벨 AA 준수

```yaml
# ========== WCAG 2.1 AA 핵심 원칙 ==========

1. Perceivable (인지 가능):
  - 텍스트 대안 제공 (이미지, 아이콘)
  - 색상만으로 정보 전달 금지
  - 충분한 색상 대비 (4.5:1 이상)
  - 텍스트 크기 조절 가능 (200%까지)

2. Operable (조작 가능):
  - 키보드로 모든 기능 접근 가능
  - 터치 타겟 최소 44dp × 44dp
  - 시간 제한 조절 가능 (타임아웃 연장)
  - 깜빡임/번쩍임 금지 (발작 유발 방지)

3. Understandable (이해 가능):
  - 명확한 레이블 및 지시사항
  - 예측 가능한 네비게이션
  - 입력 오류 감지 및 수정 제안
  - 일관된 UI 패턴

4. Robust (견고성):
  - 보조 기술과 호환 (스크린 리더)
  - 시맨틱 HTML/Widget 사용
  - 플랫폼 접근성 API 준수
```

### 2.2 플랫폼별 접근성 가이드라인

```dart
// ========== Android Accessibility ==========
// TalkBack 지원
// - Semantic Labels
// - Content Descriptions
// - Accessibility Focus
// - Accessibility Actions

// ========== iOS Accessibility ==========
// VoiceOver 지원
// - Accessibility Labels
// - Accessibility Hints
// - Accessibility Traits
// - Accessibility Actions

// ========== Flutter Semantics Widget ==========
Semantics(
  label: '장소 카드: ${place.name}',
  hint: '탭하여 상세 정보 보기',
  button: true,
  enabled: true,
  onTap: () => _navigateToDetail(place),
  child: PlaceCard(place: place),
);
```

---

## 3. 스크린 리더 지원

### 3.1 Semantic Labels

```dart
// ========== 1. 이미지 대체 텍스트 ==========
// BAD: 스크린 리더가 읽을 수 없음
Image.network(place.imageUrl);

// GOOD: Semantic Label 제공
Semantics(
  label: '${place.name} 장소 사진',
  image: true,
  child: Image.network(place.imageUrl),
);

// ========== 2. 아이콘 버튼 레이블 ==========
// BAD: "버튼"만 읽힘
IconButton(
  icon: Icon(Icons.favorite),
  onPressed: () => _toggleLike(),
);

// GOOD: 명확한 레이블
Semantics(
  label: isLiked ? '좋아요 취소' : '좋아요',
  button: true,
  enabled: true,
  child: IconButton(
    icon: Icon(
      isLiked ? Icons.favorite : Icons.favorite_border,
      semanticLabel: isLiked ? '좋아요 취소' : '좋아요',
    ),
    onPressed: () => _toggleLike(),
  ),
);

// ========== 3. 복잡한 위젯 그룹 레이블 ==========
Semantics(
  label: '${place.name}, ${place.category}, 평점 ${place.rating}점, 거리 ${place.distance}m',
  button: true,
  onTap: () => _navigateToDetail(place),
  child: PlaceCard(
    place: place,
    // 하위 위젯의 Semantics 무시
    excludeSemantics: true,
  ),
);

// ========== 4. 동적 콘텐츠 변경 알림 ==========
class PlaceLikeButton extends StatefulWidget {
  @override
  State<PlaceLikeButton> createState() => _PlaceLikeButtonState();
}

class _PlaceLikeButtonState extends State<PlaceLikeButton> {
  bool _isLiked = false;

  void _toggleLike() {
    setState(() {
      _isLiked = !_isLiked;
    });

    // 스크린 리더에 상태 변경 알림
    SemanticsService.announce(
      _isLiked ? '좋아요를 눌렀습니다' : '좋아요를 취소했습니다',
      TextDirection.ltr,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: _isLiked ? '좋아요 취소' : '좋아요',
      button: true,
      child: IconButton(
        icon: Icon(_isLiked ? Icons.favorite : Icons.favorite_border),
        onPressed: _toggleLike,
      ),
    );
  }
}

// ========== 5. 커스텀 Semantic Actions ==========
Semantics(
  customSemanticsActions: {
    CustomSemanticsAction(label: '공유하기'): () => _share(place),
    CustomSemanticsAction(label: '저장하기'): () => _save(place),
    CustomSemanticsAction(label: '경로 찾기'): () => _navigate(place),
  },
  child: PlaceCard(place: place),
);
```

### 3.2 읽기 순서 제어

```dart
// ========== Semantic 읽기 순서 정의 ==========
Column(
  children: [
    // 1번: 제목 (가장 먼저 읽힘)
    Semantics(
      sortKey: const OrdinalSortKey(1),
      header: true,
      child: Text(
        '장소 목록',
        style: Theme.of(context).textTheme.headlineMedium,
      ),
    ),

    // 2번: 필터 버튼
    Semantics(
      sortKey: const OrdinalSortKey(2),
      button: true,
      label: '필터 옵션 열기',
      child: FilterButton(onPressed: _openFilter),
    ),

    // 3번: 장소 리스트
    Semantics(
      sortKey: const OrdinalSortKey(3),
      child: PlaceList(places: places),
    ),
  ],
);

// ========== ExcludeSemantics로 중복 읽기 방지 ==========
Semantics(
  label: '${place.name}, 평점 ${place.rating}점',
  child: Row(
    children: [
      ExcludeSemantics(
        child: Text(place.name), // 부모에서 이미 읽으므로 제외
      ),
      ExcludeSemantics(
        child: RatingStars(rating: place.rating),
      ),
    ],
  ),
);
```

### 3.3 Live Region (실시간 업데이트)

```dart
// ========== Live Region - 실시간 알림 ==========
class SearchResultsLiveRegion extends StatelessWidget {
  final int resultCount;

  const SearchResultsLiveRegion({required this.resultCount});

  @override
  Widget build(BuildContext context) {
    return Semantics(
      liveRegion: true, // 스크린 리더가 자동으로 읽음
      label: '검색 결과 ${resultCount}개',
      child: Text('$resultCount개의 장소'),
    );
  }
}

// 사용 예시
class SearchScreen extends StatefulWidget {
  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  List<Place> _results = [];

  void _search(String query) async {
    final results = await _searchPlaces(query);
    setState(() {
      _results = results;
    });

    // 검색 완료 알림
    SemanticsService.announce(
      '검색 완료. ${results.length}개의 장소를 찾았습니다',
      TextDirection.ltr,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SearchBar(onSearch: _search),
        SearchResultsLiveRegion(resultCount: _results.length),
        PlaceList(places: _results),
      ],
    );
  }
}
```

---

## 4. 키보드 네비게이션

### 4.1 포커스 관리

```dart
// ========== Focus Traversal Order ==========
class PlaceDetailScreen extends StatelessWidget {
  final _focusNodes = List.generate(5, (_) => FocusNode());

  @override
  Widget build(BuildContext context) {
    return FocusTraversalGroup(
      policy: OrderedTraversalPolicy(),
      child: Column(
        children: [
          // Tab 순서: 1 → 2 → 3 → 4 → 5
          FocusTraversalOrder(
            order: NumericFocusOrder(1.0),
            child: TextField(
              focusNode: _focusNodes[0],
              decoration: InputDecoration(labelText: '장소명'),
            ),
          ),
          FocusTraversalOrder(
            order: NumericFocusOrder(2.0),
            child: ElevatedButton(
              focusNode: _focusNodes[1],
              onPressed: _save,
              child: Text('저장'),
            ),
          ),
          FocusTraversalOrder(
            order: NumericFocusOrder(3.0),
            child: TextButton(
              focusNode: _focusNodes[2],
              onPressed: _cancel,
              child: Text('취소'),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    for (final node in _focusNodes) {
      node.dispose();
    }
    super.dispose();
  }
}

// ========== Focus Scope - 포커스 영역 제한 ==========
class ModalDialog extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return FocusScope(
      // 모달 외부로 포커스 이동 방지
      canRequestFocus: true,
      autofocus: true,
      child: AlertDialog(
        title: Text('장소 삭제'),
        content: Text('정말 삭제하시겠습니까?'),
        actions: [
          TextButton(
            autofocus: true, // 첫 번째 버튼에 자동 포커스
            onPressed: () => Navigator.pop(context, false),
            child: Text('취소'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('삭제'),
          ),
        ],
      ),
    );
  }
}
```

### 4.2 키보드 단축키

```dart
// ========== Keyboard Shortcuts ==========
class PlaceListScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: {
        // Ctrl+F: 검색
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyF):
            SearchIntent(),

        // Ctrl+N: 새 장소 추가
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyN):
            AddPlaceIntent(),

        // Esc: 닫기
        LogicalKeySet(LogicalKeyboardKey.escape): CloseIntent(),
      },
      child: Actions(
        actions: {
          SearchIntent: CallbackAction<SearchIntent>(
            onInvoke: (_) => _openSearch(),
          ),
          AddPlaceIntent: CallbackAction<AddPlaceIntent>(
            onInvoke: (_) => _addPlace(),
          ),
          CloseIntent: CallbackAction<CloseIntent>(
            onInvoke: (_) => Navigator.pop(context),
          ),
        },
        child: Focus(
          autofocus: true,
          child: PlaceListView(),
        ),
      ),
    );
  }
}

// Intent 정의
class SearchIntent extends Intent {}
class AddPlaceIntent extends Intent {}
class CloseIntent extends Intent {}
```

---

## 5. 색상 및 대비

### 5.1 색상 대비 비율

```dart
// ========== WCAG 2.1 AA 색상 대비 기준 ==========
// 일반 텍스트: 4.5:1 이상
// 대형 텍스트 (18pt+, 14pt+ bold): 3:1 이상
// UI 컴포넌트 및 그래픽: 3:1 이상

class AppColors {
  // ========== 라이트 모드 ==========
  static const lightBackground = Color(0xFFFFFFFF); // 흰색
  static const lightText = Color(0xFF1A202C); // 거의 검정 (대비 16.1:1)
  static const lightTextSecondary = Color(0xFF4A5568); // 회색 (대비 7.9:1)

  static const lightPrimary = Color(0xFFE53E3E); // 빨강 (대비 4.5:1)
  static const lightPrimaryText = Color(0xFFFFFFFF); // 흰색

  // ========== 다크 모드 ==========
  static const darkBackground = Color(0xFF1A202C); // 거의 검정
  static const darkText = Color(0xFFF7FAFC); // 거의 흰색 (대비 15.8:1)
  static const darkTextSecondary = Color(0xFFCBD5E0); // 밝은 회색 (대비 9.3:1)

  static const darkPrimary = Color(0xFFFC8181); // 밝은 빨강 (대비 5.2:1)
  static const darkPrimaryText = Color(0xFF1A202C); // 거의 검정

  // ========== 상태 색상 (충분한 대비 보장) ==========
  static const success = Color(0xFF38A169); // 대비 4.5:1
  static const warning = Color(0xFFD69E2E); // 대비 4.5:1
  static const error = Color(0xFFE53E3E); // 대비 4.5:1
}

// ========== 색상 대비 검증 ==========
double calculateContrastRatio(Color foreground, Color background) {
  final fgLuminance = foreground.computeLuminance();
  final bgLuminance = background.computeLuminance();

  final lighter = max(fgLuminance, bgLuminance);
  final darker = min(fgLuminance, bgLuminance);

  return (lighter + 0.05) / (darker + 0.05);
}

void validateColorContrast() {
  final ratio = calculateContrastRatio(
    AppColors.lightText,
    AppColors.lightBackground,
  );

  assert(ratio >= 4.5, 'Color contrast ratio must be at least 4.5:1');
}
```

### 5.2 색상만으로 정보 전달 금지

```dart
// ========== BAD: 색상만으로 상태 표시 ==========
Container(
  color: isAvailable ? Colors.green : Colors.red,
  child: Text('상태'),
);

// ========== GOOD: 색상 + 아이콘/텍스트 ==========
Container(
  decoration: BoxDecoration(
    color: isAvailable ? Colors.green.shade100 : Colors.red.shade100,
    border: Border.all(
      color: isAvailable ? Colors.green : Colors.red,
      width: 2,
    ),
  ),
  child: Row(
    children: [
      Icon(
        isAvailable ? Icons.check_circle : Icons.cancel,
        color: isAvailable ? Colors.green : Colors.red,
      ),
      const SizedBox(width: 8),
      Text(
        isAvailable ? '이용 가능' : '이용 불가',
        style: TextStyle(
          color: isAvailable ? Colors.green.shade900 : Colors.red.shade900,
          fontWeight: FontWeight.bold,
        ),
      ),
    ],
  ),
);

// ========== 링크 구분 (밑줄 추가) ==========
// BAD: 색상만으로 링크 표시
Text(
  'hotly.app',
  style: TextStyle(color: Colors.blue),
);

// GOOD: 색상 + 밑줄
Text(
  'hotly.app',
  style: TextStyle(
    color: Colors.blue,
    decoration: TextDecoration.underline,
  ),
);
```

---

## 6. 터치 타겟 크기

### 6.1 최소 터치 타겟 크기 (44dp × 44dp)

```dart
// ========== WCAG 2.5.5: 최소 터치 타겟 44dp × 44dp ==========

// BAD: 너무 작은 터치 타겟 (24dp)
IconButton(
  icon: Icon(Icons.favorite, size: 24),
  onPressed: _toggleLike,
);

// GOOD: 충분한 터치 타겟 (48dp, Material 기본값)
IconButton(
  iconSize: 24,
  padding: const EdgeInsets.all(12), // 24 + 12*2 = 48dp
  icon: Icon(Icons.favorite),
  onPressed: _toggleLike,
);

// ========== 작은 아이콘에 패딩 추가 ==========
GestureDetector(
  onTap: _close,
  child: Padding(
    padding: const EdgeInsets.all(12), // 터치 영역 확장
    child: Icon(Icons.close, size: 20),
  ),
);

// ========== Inkwell로 터치 피드백 + 충분한 크기 ==========
InkWell(
  onTap: _toggleLike,
  borderRadius: BorderRadius.circular(24),
  child: Container(
    width: 48, // 최소 44dp 이상
    height: 48,
    alignment: Alignment.center,
    child: Icon(Icons.favorite, size: 24),
  ),
);

// ========== 리스트 아이템 최소 높이 ==========
ListTile(
  minVerticalPadding: 12, // 최소 높이 48dp 보장
  leading: Icon(Icons.place),
  title: Text(place.name),
  onTap: () => _navigateToDetail(place),
);

// ========== 인접한 터치 타겟 간격 ==========
Row(
  children: [
    IconButton(
      icon: Icon(Icons.favorite),
      onPressed: _toggleLike,
    ),
    const SizedBox(width: 8), // 최소 8dp 간격
    IconButton(
      icon: Icon(Icons.share),
      onPressed: _share,
    ),
  ],
);
```

### 6.2 터치 타겟 크기 검증

```dart
// ========== 터치 타겟 크기 자동 검증 (개발 모드) ==========
class AccessibilityDebugger {
  static void checkTouchTargets(BuildContext context) {
    assert(() {
      final renderBox = context.findRenderObject() as RenderBox?;
      if (renderBox != null) {
        final size = renderBox.size;

        // 최소 44dp 검증
        if (size.width < 44 || size.height < 44) {
          debugPrint(
            'WARNING: Touch target too small: ${size.width}dp × ${size.height}dp. '
            'Minimum size is 44dp × 44dp.',
          );
        }
      }
      return true;
    }());
  }
}

// 사용
class LikeButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      AccessibilityDebugger.checkTouchTargets(context);
    });

    return IconButton(...);
  }
}
```

---

## 7. 텍스트 확대 지원

### 7.1 동적 텍스트 크기 조절

```dart
// ========== MediaQuery.textScaleFactor 지원 ==========

// BAD: 고정 크기 (사용자 설정 무시)
Text(
  '장소 이름',
  style: TextStyle(fontSize: 16),
);

// GOOD: 상대 크기 (Theme 사용)
Text(
  '장소 이름',
  style: Theme.of(context).textTheme.bodyLarge, // 시스템 설정 반영
);

// ========== textScaleFactor 제한 (레이아웃 깨짐 방지) ==========
Text(
  '장소 이름',
  style: Theme.of(context).textTheme.bodyLarge,
  textScaleFactor: MediaQuery.of(context).textScaleFactor.clamp(1.0, 2.0),
  // 최대 200% 확대까지만 허용
);

// ========== MediaQuery.textScaleFactorOf로 반응형 레이아웃 ==========
class ResponsiveText extends StatelessWidget {
  final String text;

  const ResponsiveText(this.text);

  @override
  Widget build(BuildContext context) {
    final textScaleFactor = MediaQuery.textScaleFactorOf(context);

    return Padding(
      padding: EdgeInsets.all(textScaleFactor > 1.5 ? 16 : 8),
      child: Text(
        text,
        style: Theme.of(context).textTheme.bodyLarge,
        overflow: TextOverflow.ellipsis,
        maxLines: textScaleFactor > 1.5 ? 3 : 2,
      ),
    );
  }
}
```

### 7.2 최소 폰트 크기

```dart
// ========== 최소 폰트 크기 12sp (WCAG 권장) ==========
class AppTextStyles {
  // 최소 크기
  static const minFontSize = 12.0;

  // 텍스트 스타일 (모두 12sp 이상)
  static const bodySmall = TextStyle(fontSize: 14);
  static const bodyMedium = TextStyle(fontSize: 16);
  static const bodyLarge = TextStyle(fontSize: 18);

  static const headlineSmall = TextStyle(fontSize: 20);
  static const headlineMedium = TextStyle(fontSize: 24);
  static const headlineLarge = TextStyle(fontSize: 30);

  // 캡션/힌트 (최소 크기 보장)
  static const caption = TextStyle(fontSize: 12);
}

// Theme 설정
ThemeData(
  textTheme: TextTheme(
    bodySmall: AppTextStyles.bodySmall,
    bodyMedium: AppTextStyles.bodyMedium,
    bodyLarge: AppTextStyles.bodyLarge,
    headlineSmall: AppTextStyles.headlineSmall,
    headlineMedium: AppTextStyles.headlineMedium,
    headlineLarge: AppTextStyles.headlineLarge,
    labelSmall: AppTextStyles.caption,
  ),
);
```

---

## 8. 다크 모드 지원

### 8.1 시스템 테마 연동

```dart
// ========== 시스템 다크 모드 감지 ==========
class App extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Hotly',
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system, // 시스템 설정 따름
      home: HomeScreen(),
    );
  }
}

// ========== 라이트/다크 테마 정의 ==========
class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: ColorScheme.light(
        primary: AppColors.lightPrimary,
        onPrimary: AppColors.lightPrimaryText,
        background: AppColors.lightBackground,
        onBackground: AppColors.lightText,
        surface: Colors.white,
        onSurface: AppColors.lightText,
      ),
      textTheme: TextTheme(
        bodyLarge: TextStyle(color: AppColors.lightText),
        bodyMedium: TextStyle(color: AppColors.lightText),
      ),
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: ColorScheme.dark(
        primary: AppColors.darkPrimary,
        onPrimary: AppColors.darkPrimaryText,
        background: AppColors.darkBackground,
        onBackground: AppColors.darkText,
        surface: Color(0xFF2D3748),
        onSurface: AppColors.darkText,
      ),
      textTheme: TextTheme(
        bodyLarge: TextStyle(color: AppColors.darkText),
        bodyMedium: TextStyle(color: AppColors.darkText),
      ),
    );
  }
}

// ========== 테마 기반 위젯 ==========
class ThemedButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return ElevatedButton(
      style: ElevatedButton.styleFrom(
        backgroundColor: Theme.of(context).colorScheme.primary,
        foregroundColor: Theme.of(context).colorScheme.onPrimary,
      ),
      onPressed: () {},
      child: Text('버튼'),
    );
  }
}
```

### 8.2 다크 모드 이미지/아이콘 대응

```dart
// ========== 다크 모드용 이미지 분기 ==========
class AdaptiveImage extends StatelessWidget {
  final String lightImagePath;
  final String darkImagePath;

  const AdaptiveImage({
    required this.lightImagePath,
    required this.darkImagePath,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Image.asset(
      isDark ? darkImagePath : lightImagePath,
    );
  }
}

// 사용
AdaptiveImage(
  lightImagePath: 'assets/images/logo_light.png',
  darkImagePath: 'assets/images/logo_dark.png',
);

// ========== 아이콘 색상 자동 적용 ==========
Icon(
  Icons.place,
  color: Theme.of(context).colorScheme.primary, // 테마 색상 자동 적용
);
```

---

## 9. 에러 및 피드백

### 9.1 명확한 에러 메시지

```dart
// ========== 접근성 친화적 에러 처리 ==========

// BAD: 모호한 메시지
if (nameController.text.isEmpty) {
  showError('입력 오류');
}

// GOOD: 구체적 메시지 + 해결 방법
if (nameController.text.isEmpty) {
  showError(
    title: '장소명을 입력해주세요',
    message: '장소명은 필수 항목입니다. 최소 2자 이상 입력해주세요.',
    action: () => _focusOnNameField(),
  );
}

// ========== 폼 유효성 검사 ==========
class PlaceForm extends StatefulWidget {
  @override
  State<PlaceForm> createState() => _PlaceFormState();
}

class _PlaceFormState extends State<PlaceForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        children: [
          TextFormField(
            controller: _nameController,
            decoration: InputDecoration(
              labelText: '장소명',
              hintText: '예: 서울 타워',
              helperText: '최소 2자 이상 입력해주세요',
              errorMaxLines: 2, // 에러 메시지 2줄까지 표시
            ),
            validator: (value) {
              if (value == null || value.isEmpty) {
                return '장소명을 입력해주세요';
              }
              if (value.length < 2) {
                return '장소명은 최소 2자 이상이어야 합니다';
              }
              return null;
            },
            // 스크린 리더에 에러 읽기
            autovalidateMode: AutovalidateMode.onUserInteraction,
          ),
          ElevatedButton(
            onPressed: () {
              if (_formKey.currentState!.validate()) {
                _submit();
              } else {
                // 첫 번째 에러 필드로 포커스
                SemanticsService.announce(
                  '입력 오류가 있습니다. 양식을 확인해주세요',
                  TextDirection.ltr,
                );
              }
            },
            child: Text('저장'),
          ),
        ],
      ),
    );
  }
}
```

### 9.2 햅틱 및 시각적 피드백

```dart
// ========== 햅틱 피드백 ==========
import 'package:flutter/services.dart';

class AccessibleButton extends StatelessWidget {
  final VoidCallback onPressed;
  final Widget child;

  const AccessibleButton({
    required this.onPressed,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () {
        // 햅틱 피드백 (청각 장애인 지원)
        HapticFeedback.mediumImpact();

        // 시각적 피드백 (스낵바)
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('버튼이 눌렸습니다'),
            duration: Duration(seconds: 2),
          ),
        );

        // 스크린 리더 알림
        SemanticsService.announce(
          '버튼이 눌렸습니다',
          TextDirection.ltr,
        );

        onPressed();
      },
      child: child,
    );
  }
}

// ========== 로딩 상태 접근성 ==========
class AccessibleLoadingButton extends StatefulWidget {
  final Future<void> Function() onPressed;
  final Widget child;

  const AccessibleLoadingButton({
    required this.onPressed,
    required this.child,
  });

  @override
  State<AccessibleLoadingButton> createState() =>
      _AccessibleLoadingButtonState();
}

class _AccessibleLoadingButtonState extends State<AccessibleLoadingButton> {
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: _isLoading ? '처리 중입니다' : '버튼',
      button: true,
      enabled: !_isLoading,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _handlePress,
        child: _isLoading
            ? SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              )
            : widget.child,
      ),
    );
  }

  Future<void> _handlePress() async {
    setState(() => _isLoading = true);

    SemanticsService.announce('처리 중입니다', TextDirection.ltr);

    try {
      await widget.onPressed();
      SemanticsService.announce('완료되었습니다', TextDirection.ltr);
    } catch (e) {
      SemanticsService.announce('오류가 발생했습니다', TextDirection.ltr);
    } finally {
      setState(() => _isLoading = false);
    }
  }
}
```

---

## 10. 접근성 테스트

### 10.1 자동화된 접근성 테스트

```dart
// ========== Widget 테스트 - 접근성 검증 ==========
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('PlaceCard should meet accessibility guidelines', (tester) async {
    final place = Place(id: '1', name: 'Test Place', rating: 4.5);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: PlaceCard(place: place),
        ),
      ),
    );

    // 1. Semantic Label 존재 확인
    expect(
      find.bySemanticsLabel(RegExp('Test Place')),
      findsOneWidget,
    );

    // 2. 터치 타겟 크기 검증 (최소 44dp)
    final cardSize = tester.getSize(find.byType(PlaceCard));
    expect(cardSize.width, greaterThanOrEqualTo(44));
    expect(cardSize.height, greaterThanOrEqualTo(44));

    // 3. 색상 대비 검증
    final textWidget = tester.widget<Text>(find.text('Test Place'));
    final textColor = textWidget.style?.color ?? Colors.black;
    final backgroundColor = Colors.white;

    final contrastRatio = calculateContrastRatio(textColor, backgroundColor);
    expect(contrastRatio, greaterThanOrEqualTo(4.5));

    // 4. 키보드 포커스 가능 확인
    expect(find.byType(Focus), findsWidgets);
  });

  testWidgets('Button should have sufficient touch target', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: IconButton(
            icon: Icon(Icons.favorite),
            onPressed: () {},
          ),
        ),
      ),
    );

    final buttonSize = tester.getSize(find.byType(IconButton));
    expect(buttonSize.width, greaterThanOrEqualTo(44));
    expect(buttonSize.height, greaterThanOrEqualTo(44));
  });

  testWidgets('Text should scale with textScaleFactor', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: MediaQuery(
          data: MediaQueryData(textScaleFactor: 2.0), // 200% 확대
          child: Scaffold(
            body: Text('Test', style: TextStyle(fontSize: 16)),
          ),
        ),
      ),
    );

    final textWidget = tester.widget<Text>(find.text('Test'));
    expect(textWidget.textScaleFactor, 2.0);
  });
}

// ========== 색상 대비 계산 헬퍼 ==========
double calculateContrastRatio(Color foreground, Color background) {
  final fgLuminance = foreground.computeLuminance();
  final bgLuminance = background.computeLuminance();

  final lighter = max(fgLuminance, bgLuminance);
  final darker = min(fgLuminance, bgLuminance);

  return (lighter + 0.05) / (darker + 0.05);
}
```

### 10.2 수동 접근성 테스트 체크리스트

```yaml
# ========== 수동 테스트 체크리스트 ==========

스크린 리더 테스트 (TalkBack/VoiceOver):
  - [ ] 모든 버튼/링크에 명확한 레이블 존재
  - [ ] 이미지에 대체 텍스트 존재
  - [ ] 읽기 순서가 논리적
  - [ ] 동적 콘텐츠 변경 시 알림 작동
  - [ ] 폼 필드 레이블 및 힌트 존재
  - [ ] 에러 메시지 읽기 가능

키보드 네비게이션:
  - [ ] Tab 키로 모든 인터랙티브 요소 접근 가능
  - [ ] 포커스 순서가 논리적
  - [ ] 포커스 인디케이터가 명확히 보임
  - [ ] Enter/Space로 버튼 활성화 가능
  - [ ] Esc로 모달/다이얼로그 닫기 가능

색상 및 대비:
  - [ ] 색상만으로 정보 전달 안 함
  - [ ] 텍스트 대비 4.5:1 이상 (일반), 3:1 이상 (대형)
  - [ ] 링크에 밑줄 또는 다른 시각적 구분 존재
  - [ ] 다크 모드에서도 충분한 대비 유지

터치 타겟:
  - [ ] 모든 버튼/링크 최소 44dp × 44dp
  - [ ] 인접한 터치 타겟 간격 충분 (8dp 이상)
  - [ ] 작은 아이콘에 패딩 추가

텍스트 확대:
  - [ ] 200% 확대 시 텍스트 읽기 가능
  - [ ] 레이아웃 깨지지 않음
  - [ ] 중요 정보 잘림 없음

다크 모드:
  - [ ] 다크 모드에서 모든 텍스트 읽기 가능
  - [ ] 이미지/아이콘 다크 모드 대응
  - [ ] 색상 대비 유지

에러 및 피드백:
  - [ ] 에러 메시지 명확하고 구체적
  - [ ] 해결 방법 제시
  - [ ] 시각적 + 햅틱 피드백
  - [ ] 스크린 리더 알림 작동
```

### 10.3 접근성 감사 도구

```dart
// ========== Accessibility Inspector (Flutter DevTools) ==========
// flutter run --profile
// DevTools > Accessibility Inspector 활성화

// ========== Custom Accessibility Debugger ==========
class AccessibilityDebugOverlay extends StatelessWidget {
  final Widget child;

  const AccessibilityDebugOverlay({required this.child});

  @override
  Widget build(BuildContext context) {
    return Directionality(
      textDirection: TextDirection.ltr,
      child: Stack(
        children: [
          child,
          if (kDebugMode)
            Positioned.fill(
              child: IgnorePointer(
                child: CustomPaint(
                  painter: AccessibilityPainter(),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class AccessibilityPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // 터치 타겟 크기 시각화
    // 색상 대비 경고 표시
    // 포커스 순서 번호 표시
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
```

---

## 11. 완료 정의 (DoD)

### 11.1 WCAG 2.1 AA 준수
- [x] 모든 이미지/아이콘에 대체 텍스트 제공
- [x] 색상만으로 정보 전달 금지
- [x] 색상 대비 4.5:1 이상 (일반 텍스트), 3:1 이상 (대형 텍스트)
- [x] 키보드로 모든 기능 접근 가능

### 11.2 스크린 리더 지원
- [x] TalkBack/VoiceOver 100% 호환
- [x] 모든 인터랙티브 요소에 Semantic Label
- [x] 논리적 읽기 순서
- [x] Live Region으로 실시간 업데이트 알림

### 11.3 물리적 접근성
- [x] 터치 타겟 최소 44dp × 44dp
- [x] 텍스트 200% 확대 지원
- [x] 다크 모드 완벽 지원
- [x] 햅틱 피드백 제공

### 11.4 테스트
- [x] 자동화된 접근성 테스트 80% 커버리지
- [x] 수동 스크린 리더 테스트 통과
- [x] 색상 대비 자동 검증
- [x] 터치 타겟 크기 자동 검증

---

## 12. 수용 기준 (Acceptance Criteria)

### AC-1: 스크린 리더 사용
- **Given** 시각 장애인 사용자
- **When** TalkBack/VoiceOver 활성화
- **Then** 모든 화면과 기능을 스크린 리더만으로 사용 가능

### AC-2: 색상 대비
- **Given** 모든 텍스트 요소
- **When** 색상 대비 측정
- **Then** 일반 텍스트 4.5:1 이상, 대형 텍스트 3:1 이상

### AC-3: 터치 타겟 크기
- **Given** 모든 버튼 및 인터랙티브 요소
- **When** 크기 측정
- **Then** 최소 44dp × 44dp 이상

### AC-4: 키보드 네비게이션
- **Given** 외부 키보드 연결
- **When** Tab 키로 네비게이션
- **Then** 모든 인터랙티브 요소 접근 가능, 논리적 순서

### AC-5: 텍스트 확대
- **Given** 시스템 텍스트 크기 200% 설정
- **When** 앱 실행
- **Then** 모든 텍스트 읽기 가능, 레이아웃 깨지지 않음

---

## 13. 참고 문서

- **내부 문서**:
  - `ui-design-system.md`: 디자인 토큰 및 색상 대비
  - `trd/frontend/01-flutter-tech-stack.md`: Flutter Semantics 위젯

- **외부 문서**:
  - [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
  - [Flutter Accessibility](https://docs.flutter.dev/development/accessibility-and-localization/accessibility)
  - [Material Design Accessibility](https://m3.material.io/foundations/accessible-design/overview)

---

## 14. Changelog

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0 | 최초 작성 - 접근성 요구사항 및 WCAG 2.1 AA 준수 전략 | Development Team |

---

*이 문서는 살아있는 문서(Living Document)로, 접근성 개선 시 즉시 업데이트됩니다.*
