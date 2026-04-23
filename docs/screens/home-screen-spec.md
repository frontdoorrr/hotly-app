# 홈 화면 상세 스펙 (Home Screen Specification)

## 문서 정보
- **화면명**: 홈 화면 (Home Screen)
- **라우트**: `/home` (기본 화면)
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **관련 문서**: `docs/user-flows.md`, `prd/02-place-management.md`

---

## 1. 화면 목적 및 사용자 가치

### 1.1 목적
- 사용자가 앱 실행 시 가장 먼저 보는 화면으로, 개인화된 추천과 빠른 액세스 제공
- 최근 활동 및 저장된 장소를 한눈에 확인
- 주요 기능으로 빠르게 이동 (링크 분석, 검색, 코스 생성)

### 1.2 사용자 가치
- **개인화**: AI 기반 추천 장소로 새로운 발견 (5초 이내)
- **빠른 액세스**: 3 클릭 이내 모든 주요 기능 도달
- **컨텍스트**: 최근 활동 타임라인으로 이어서 탐색

### 1.3 성공 지표
- 홈 화면 체류 시간: 평균 30초
- 추천 장소 클릭률: 20% 이상
- 빠른 액세스 버튼 사용률: 60% 이상

---

## 2. 와이어프레임

```
┌─────────────────────────────────────┐
│  ┌───────┐              🔔 👤      │ ← Top App Bar
│  │ HOTLY │         ArchyAI            │
│  └───────┘                          │
├─────────────────────────────────────┤
│                                     │
│  🔥 오늘의 추천 장소                │ ← Section Header
│  ┌─────────────────────────────┐   │
│  │ ┌────┐ 카페 A               │   │
│  │ │IMG │ 강남역 · ⭐ 4.5      │   │ ← Recommendation Card
│  │ └────┘ #데이트 #뷰맛집      │   │   (Horizontal Scroll)
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ ┌────┐ 맛집 B               │   │
│  │ │IMG │ 신사역 · ⭐ 4.8      │   │
│  │ └────┘ #분위기 #파스타      │   │
│  └─────────────────────────────┘   │
│          [더보기 →]                 │
│                                     │
│  빠른 액세스                        │ ← Quick Actions
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │ 🔗   │ │ 🔍   │ │ 🗺    │       │
│  │링크  │ │검색  │ │코스  │       │
│  │분석  │ │장소  │ │만들기│       │
│  └──────┘ └──────┘ └──────┘       │
│                                     │
│  최근 활동                          │ ← Recent Activity
│  ┌─────────────────────────────┐   │
│  │ 💾 장소 저장됨 - 카페 A     │   │
│  │    2시간 전                  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ 🗺️  코스 생성 - 강남 데이트 │   │
│  │    어제                      │   │
│  └─────────────────────────────┘   │
│                                     │
│  인기 장소                          │ ← Popular Places
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐     │
│  │IMG │ │IMG │ │IMG │ │IMG │     │   (Grid View)
│  │플레│ │플레│ │플레│ │플레│     │
│  │C   │ │D   │ │E   │ │F   │     │
│  └────┘ └────┘ └────┘ └────┘     │
│                                     │
└─────────────────────────────────────┘
│  [홈] [검색] [➕] [코스] [프로필]  │ ← Bottom Nav Bar
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리 구조

```dart
HomeScreen (StatelessWidget)
└─ Scaffold
   ├─ AppBar (TopAppBar)
   │  ├─ Leading: Logo
   │  ├─ Title: "ArchyAI"
   │  └─ Actions: [NotificationIcon, ProfileIcon]
   │
   ├─ Body: RefreshIndicator
   │  └─ CustomScrollView
   │     ├─ SliverAppBar (Collapsible)
   │     │
   │     ├─ SliverToBoxAdapter (추천 장소 섹션)
   │     │  └─ RecommendationSection
   │     │     ├─ SectionHeader
   │     │     │  ├─ Icon (🔥)
   │     │     │  └─ Text("오늘의 추천 장소")
   │     │     ├─ SizedBox(height: 200)
   │     │     │  └─ ListView.builder (horizontal: true)
   │     │     │     └─ PlaceCard (Recommendation variant)
   │     │     └─ TextButton("더보기")
   │     │
   │     ├─ SliverToBoxAdapter (빠른 액세스)
   │     │  └─ QuickActionsSection
   │     │     ├─ SectionHeader
   │     │     └─ Row
   │     │        ├─ QuickActionButton (링크 분석)
   │     │        ├─ QuickActionButton (검색)
   │     │        └─ QuickActionButton (코스 만들기)
   │     │
   │     ├─ SliverToBoxAdapter (최근 활동)
   │     │  └─ RecentActivitySection
   │     │     ├─ SectionHeader
   │     │     └─ ListView.builder
   │     │        └─ ActivityCard
   │     │
   │     └─ SliverGrid (인기 장소)
   │        └─ PlaceCard (Grid variant)
   │
   └─ BottomNavigationBar
      └─ CustomBottomNavBar (current: home)
```

---

## 4. 컴포넌트 상세 정의

### 4.1 TopAppBar

```dart
// lib/shared/widgets/app_bar/top_app_bar.dart
class TopAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final bool showLogo;
  final List<Widget>? actions;

  const TopAppBar({
    Key? key,
    required this.title,
    this.showLogo = false,
    this.actions,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: Theme.of(context).colorScheme.surface,
      elevation: 0,
      leading: showLogo
          ? Padding(
              padding: const EdgeInsets.all(8.0),
              child: Image.asset('assets/images/logo/app_logo.png'),
            )
          : null,
      title: Text(
        title,
        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
      ),
      actions: actions,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(56);
}

// 사용 예시
TopAppBar(
  title: 'ArchyAI',
  showLogo: true,
  actions: [
    IconButton(
      icon: Icon(Icons.notifications_outlined),
      onPressed: () => context.go('/notifications'),
    ),
    IconButton(
      icon: Icon(Icons.person_outline),
      onPressed: () => context.go('/profile'),
    ),
  ],
)
```

### 4.2 RecommendationSection

```dart
// lib/features/home/presentation/widgets/recommendation_section.dart
class RecommendationSection extends ConsumerWidget {
  const RecommendationSection({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recommendations = ref.watch(recommendationsProvider);

    return recommendations.when(
      loading: () => _buildSkeletonLoader(),
      error: (error, stack) => _buildErrorView(error),
      data: (places) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionHeader(
            icon: Icons.local_fire_department,
            title: '오늘의 추천 장소',
            subtitle: '${places.length}개의 새로운 장소',
          ),
          const SizedBox(height: 16),
          SizedBox(
            height: 200,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: places.length,
              itemBuilder: (context, index) {
                return Padding(
                  padding: const EdgeInsets.only(right: 12),
                  child: PlaceCard(
                    place: places[index],
                    variant: PlaceCardVariant.recommendation,
                    onTap: () => _navigateToDetail(context, places[index]),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextButton.icon(
              onPressed: () => context.go('/places/recommended'),
              icon: const Icon(Icons.arrow_forward),
              label: const Text('더보기'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSkeletonLoader() {
    return Shimmer.fromColors(
      baseColor: Colors.grey[300]!,
      highlightColor: Colors.grey[100]!,
      child: SizedBox(
        height: 200,
        child: ListView.builder(
          scrollDirection: Axis.horizontal,
          itemCount: 3,
          itemBuilder: (context, index) => Container(
            width: 280,
            margin: const EdgeInsets.only(right: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildErrorView(Object error) {
    return Center(
      child: Text('추천 장소를 불러올 수 없습니다: $error'),
    );
  }

  void _navigateToDetail(BuildContext context, Place place) {
    context.push('/places/${place.id}');
  }
}
```

### 4.3 PlaceCard (Recommendation Variant)

```dart
// lib/shared/widgets/cards/place_card.dart
enum PlaceCardVariant {
  recommendation, // 가로 카드 (280x200)
  list,          // 리스트 아이템
  grid,          // 그리드 아이템
}

class PlaceCard extends StatelessWidget {
  final Place place;
  final PlaceCardVariant variant;
  final VoidCallback? onTap;

  const PlaceCard({
    Key? key,
    required this.place,
    this.variant = PlaceCardVariant.list,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    switch (variant) {
      case PlaceCardVariant.recommendation:
        return _buildRecommendationCard(context);
      case PlaceCardVariant.list:
        return _buildListCard(context);
      case PlaceCardVariant.grid:
        return _buildGridCard(context);
    }
  }

  Widget _buildRecommendationCard(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 280,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Stack(
            children: [
              // 배경 이미지
              CachedNetworkImage(
                imageUrl: place.imageUrl ?? '',
                height: 200,
                width: 280,
                fit: BoxFit.cover,
                placeholder: (context, url) => Container(
                  color: Colors.grey[200],
                  child: const Center(child: CircularProgressIndicator()),
                ),
                errorWidget: (context, url, error) => Container(
                  color: Colors.grey[300],
                  child: const Icon(Icons.place, size: 48),
                ),
              ),

              // 그라데이션 오버레이
              Positioned.fill(
                child: Container(
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.transparent,
                        Colors.black.withOpacity(0.7),
                      ],
                    ),
                  ),
                ),
              ),

              // 정보 오버레이
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        place.name,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(
                            Icons.location_on,
                            color: Colors.white70,
                            size: 14,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            place.address?.split(' ').take(2).join(' ') ?? '',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 12,
                            ),
                          ),
                          const Spacer(),
                          const Icon(
                            Icons.star,
                            color: Colors.amber,
                            size: 14,
                          ),
                          const SizedBox(width: 2),
                          Text(
                            place.rating?.toStringAsFixed(1) ?? '-',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 4,
                        children: place.tags.take(2).map((tag) {
                          return Chip(
                            label: Text(
                              '#$tag',
                              style: const TextStyle(fontSize: 10),
                            ),
                            backgroundColor: Colors.white.withOpacity(0.3),
                            labelStyle: const TextStyle(color: Colors.white),
                            visualDensity: VisualDensity.compact,
                            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
              ),

              // 좋아요 버튼
              Positioned(
                top: 8,
                right: 8,
                child: LikeButton(
                  placeId: place.id,
                  isLiked: place.isLiked,
                  size: 32,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildListCard(BuildContext context) {
    // 리스트 변형 구현
    return const SizedBox.shrink();
  }

  Widget _buildGridCard(BuildContext context) {
    // 그리드 변형 구현
    return const SizedBox.shrink();
  }
}
```

### 4.4 QuickActionsSection

```dart
// lib/features/home/presentation/widgets/quick_actions_section.dart
class QuickActionsSection extends StatelessWidget {
  const QuickActionsSection({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(
          title: '빠른 액세스',
        ),
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              QuickActionButton(
                icon: Icons.link,
                label: '링크 분석',
                onPressed: () => context.go('/link-analysis'),
              ),
              QuickActionButton(
                icon: Icons.search,
                label: '검색',
                onPressed: () => context.go('/search'),
              ),
              QuickActionButton(
                icon: Icons.map_outlined,
                label: '코스 만들기',
                onPressed: () => context.go('/courses/create'),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const QuickActionButton({
    Key? key,
    required this.icon,
    required this.label,
    required this.onPressed,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onPressed,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 100,
        padding: const EdgeInsets.symmetric(vertical: 16),
        child: Column(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Icon(
                icon,
                size: 28,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## 5. 상태 관리 (Riverpod)

### 5.1 Providers

```dart
// lib/features/home/presentation/providers/home_providers.dart

// 추천 장소 Provider
final recommendationsProvider = FutureProvider.autoDispose<List<Place>>((ref) async {
  final repository = ref.read(placeRepositoryProvider);
  final result = await repository.getRecommendedPlaces();

  return result.when(
    success: (places) => places,
    failure: (error) => throw Exception(error),
  );
});

// 최근 활동 Provider
final recentActivitiesProvider = FutureProvider.autoDispose<List<Activity>>((ref) async {
  final repository = ref.read(activityRepositoryProvider);
  final result = await repository.getRecentActivities(limit: 5);

  return result.when(
    success: (activities) => activities,
    failure: (error) => throw Exception(error),
  );
});

// 인기 장소 Provider
final popularPlacesProvider = FutureProvider.autoDispose<List<Place>>((ref) async {
  final repository = ref.read(placeRepositoryProvider);
  final result = await repository.getPopularPlaces(limit: 8);

  return result.when(
    success: (places) => places,
    failure: (error) => throw Exception(error),
  );
});

// 홈 화면 State Notifier
final homeStateProvider = StateNotifierProvider<HomeNotifier, HomeState>((ref) {
  return HomeNotifier(
    ref.read(placeRepositoryProvider),
    ref.read(activityRepositoryProvider),
  );
});

class HomeNotifier extends StateNotifier<HomeState> {
  final PlaceRepository _placeRepository;
  final ActivityRepository _activityRepository;

  HomeNotifier(this._placeRepository, this._activityRepository)
      : super(const HomeState.initial());

  Future<void> refreshAll() async {
    state = const HomeState.loading();

    try {
      final results = await Future.wait([
        _placeRepository.getRecommendedPlaces(),
        _activityRepository.getRecentActivities(limit: 5),
        _placeRepository.getPopularPlaces(limit: 8),
      ]);

      // 성공 처리
      state = HomeState.loaded(
        recommendations: (results[0] as Success<List<Place>>).data,
        recentActivities: (results[1] as Success<List<Activity>>).data,
        popularPlaces: (results[2] as Success<List<Place>>).data,
      );
    } catch (e) {
      state = HomeState.error(e.toString());
    }
  }
}

// Home State
@freezed
class HomeState with _$HomeState {
  const factory HomeState.initial() = Initial;
  const factory HomeState.loading() = Loading;
  const factory HomeState.loaded({
    required List<Place> recommendations,
    required List<Activity> recentActivities,
    required List<Place> popularPlaces,
  }) = Loaded;
  const factory HomeState.error(String message) = Error;
}
```

---

## 6. API 연동

### 6.1 엔드포인트

```dart
// 추천 장소 조회
GET /api/v1/places/recommended?limit=10

// 최근 활동 조회
GET /api/v1/activities/recent?limit=5

// 인기 장소 조회
GET /api/v1/places/popular?limit=8
```

### 6.2 Repository Implementation

```dart
// lib/features/places/data/repositories/place_repository_impl.dart
class PlaceRepositoryImpl implements PlaceRepository {
  final PlaceRemoteDataSource _remoteDataSource;
  final PlaceLocalDataSource _localDataSource;

  @override
  Future<Result<List<Place>>> getRecommendedPlaces({int limit = 10}) async {
    try {
      // 1. 로컬 캐시 확인
      final cached = await _localDataSource.getCachedRecommendations();
      if (cached.isNotEmpty) {
        // 백그라운드 갱신
        unawaited(_refreshRecommendationsInBackground(limit));
        return Result.success(cached.map((dto) => dto.toEntity()).toList());
      }

      // 2. API 호출
      final placeDTOs = await _remoteDataSource.getRecommendedPlaces(limit: limit);
      final places = placeDTOs.map((dto) => dto.toEntity()).toList();

      // 3. 캐시 저장
      await _localDataSource.cacheRecommendations(placeDTOs);

      return Result.success(places);
    } catch (e) {
      return Result.failure('추천 장소를 불러올 수 없습니다: $e');
    }
  }

  Future<void> _refreshRecommendationsInBackground(int limit) async {
    try {
      final placeDTOs = await _remoteDataSource.getRecommendedPlaces(limit: limit);
      await _localDataSource.cacheRecommendations(placeDTOs);
    } catch (e) {
      logger.w('Background refresh failed: $e');
    }
  }
}
```

---

## 7. 엣지 케이스 처리

### 7.1 로딩 상태
```dart
// Shimmer 스켈레톤 로더
recommendations.when(
  loading: () => ShimmerPlaceCardList(count: 3),
  // ...
)
```

### 7.2 에러 상태
```dart
recommendations.when(
  error: (error, stack) => ErrorView(
    message: '추천 장소를 불러올 수 없습니다',
    onRetry: () => ref.refresh(recommendationsProvider),
  ),
  // ...
)
```

### 7.3 빈 상태
```dart
if (places.isEmpty) {
  return EmptyStateView(
    icon: Icons.explore_outlined,
    title: '아직 추천할 장소가 없어요',
    message: '장소를 저장하거나 검색하여 시작해보세요',
    action: ElevatedButton(
      onPressed: () => context.go('/search'),
      child: const Text('장소 검색하기'),
    ),
  );
}
```

### 7.4 Pull-to-Refresh
```dart
RefreshIndicator(
  onRefresh: () async {
    await ref.refresh(recommendationsProvider.future);
    await ref.refresh(recentActivitiesProvider.future);
    await ref.refresh(popularPlacesProvider.future);
  },
  child: CustomScrollView(...),
)
```

---

## 8. 성능 최적화

### 8.1 이미지 최적화
```dart
CachedNetworkImage(
  imageUrl: place.imageUrl,
  memCacheWidth: 400,  // 메모리 캐시 크기 제한
  memCacheHeight: 300,
  maxWidthDiskCache: 800,
  maxHeightDiskCache: 600,
)
```

### 8.2 리스트 최적화
```dart
ListView.builder(
  // Lazy loading
  itemCount: places.length,
  itemBuilder: (context, index) {
    return RepaintBoundary(
      child: PlaceCard(place: places[index]),
    );
  },
)
```

### 8.3 Provider 최적화
```dart
// autoDispose로 메모리 누수 방지
final recommendationsProvider = FutureProvider.autoDispose<List<Place>>(...);

// select로 불필요한 리빌드 방지
final placeCount = ref.watch(
  recommendationsProvider.select((state) => state.value?.length ?? 0),
);
```

---

## 9. 접근성

### 9.1 Semantic Labels
```dart
Semantics(
  label: '${place.name}, ${place.category}, 평점 ${place.rating}점',
  button: true,
  onTap: () => _navigateToDetail(place),
  child: PlaceCard(place: place),
)
```

### 9.2 터치 타겟 크기
```dart
// 모든 버튼 최소 44dp × 44dp
IconButton(
  iconSize: 24,
  padding: const EdgeInsets.all(12), // 총 48dp
  icon: Icon(Icons.favorite),
  onPressed: _toggleLike,
)
```

---

## 10. 테스트

### 10.1 Widget Test
```dart
// test/features/home/presentation/screens/home_screen_test.dart
void main() {
  testWidgets('HomeScreen should display recommendations', (tester) async {
    // Arrange
    final mockPlaces = [
      Place(id: '1', name: 'Test Place', ...),
    ];

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          recommendationsProvider.overrideWith(
            (ref) => AsyncValue.data(mockPlaces),
          ),
        ],
        child: MaterialApp(home: HomeScreen()),
      ),
    );

    // Act
    await tester.pumpAndSettle();

    // Assert
    expect(find.text('Test Place'), findsOneWidget);
    expect(find.byType(PlaceCard), findsOneWidget);
  });

  testWidgets('HomeScreen should show error when API fails', (tester) async {
    // Arrange
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          recommendationsProvider.overrideWith(
            (ref) => AsyncValue.error('Network error', StackTrace.empty),
          ),
        ],
        child: MaterialApp(home: HomeScreen()),
      ),
    );

    // Act
    await tester.pumpAndSettle();

    // Assert
    expect(find.text('추천 장소를 불러올 수 없습니다'), findsOneWidget);
  });
}
```

---

## 11. 완료 정의 (DoD)

- [ ] 모든 위젯 구현 및 테스트 통과 (커버리지 80% 이상)
- [ ] API 연동 완료 (추천, 최근 활동, 인기 장소)
- [ ] 로딩/에러/빈 상태 처리
- [ ] Pull-to-Refresh 동작
- [ ] 접근성 검증 (Semantic Labels, 터치 타겟 크기)
- [ ] 성능 테스트 (60fps 유지, 화면 로딩 3초 이내)

---

## 12. 수용 기준

- **Given** 사용자가 앱 실행
- **When** 홈 화면 표시
- **Then** 3초 이내 추천 장소 표시, Pull-to-Refresh 가능

- **Given** 추천 장소 카드 탭
- **When** 장소 상세 화면 이동
- **Then** 0.3초 이내 화면 전환, Hero 애니메이션 적용

- **Given** 빠른 액세스 버튼 탭
- **When** 해당 기능 화면 이동
- **Then** 즉시 화면 전환 (< 0.1초)

---

*이 문서는 실제 구현 시 참고할 수 있도록 작성되었으며, 코드 예시는 즉시 사용 가능합니다.*
