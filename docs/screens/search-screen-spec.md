# 검색 화면 상세 스펙 (Search Screen Specification)

## 문서 정보
- **화면명**: 검색 화면 (Search Screen)
- **라우트**: `/search`
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **관련 문서**: `docs/user-flows.md`, `prd/08-search-filter.md`

---

## 1. 화면 목적 및 사용자 가치

### 1.1 목적
- 키워드, 카테고리, 위치 기반 장소 검색
- 고급 필터로 정확한 결과 제공
- 리스트/지도 뷰 전환으로 다양한 탐색 방식 지원

### 1.2 사용자 가치
- **빠른 검색**: 실시간 자동완성으로 1초 이내 결과 표시
- **정확한 필터링**: 카테고리, 거리, 평점 등 다중 조건 필터
- **시각적 탐색**: 지도 뷰로 주변 장소 한눈에 파악

### 1.3 성공 지표
- 검색 완료율: 80% 이상
- 필터 사용률: 40% 이상
- 검색 결과 클릭률: 60% 이상

---

## 2. 와이어프레임

```
┌─────────────────────────────────────┐
│  ← 검색                    🎚️ [뷰] │ ← Search Header
├─────────────────────────────────────┤
│  🔍 장소, 주소, 태그 검색          │ ← Search Bar
│     [X]                             │
├─────────────────────────────────────┤
│  최근 검색어                        │ ← Recent Searches
│  • 강남 카페           [X]          │   (검색 전)
│  • 신사 맛집           [X]          │
│                                     │
│  인기 검색어                        │
│  #데이트 #뷰맛집 #브런치            │
│                                     │
│  카테고리                           │
│  [카페] [맛집] [관광] [데이트]      │
├─────────────────────────────────────┤
│                                     │
│  ─── 검색 결과 (132개) ───         │ ← Results Header
│  정렬: [추천순 ▼]        [리스트▼] │   (검색 후)
│  필터: [카테고리(1)] [거리] [초기화]│
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ┌────┐ 카페 A               │   │
│  │ │IMG │ ⭐ 4.5 · 500m       │   │ ← Place Card
│  │ └────┘ #데이트 #조용한      │   │   (List Item)
│  │         💾 ❤️               │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ ┌────┐ 맛집 B               │   │
│  │ │IMG │ ⭐ 4.8 · 1.2km      │   │
│  │ └────┘ #분위기 #파스타      │   │
│  │         💾 ❤️               │   │
│  └─────────────────────────────┘   │
│                                     │
│  ━━━━━ 로딩 중 ━━━━━              │ ← Infinite Scroll
│                                     │
└─────────────────────────────────────┘
│  [홈] [검색] [➕] [코스] [프로필]  │ ← Bottom Nav
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리 구조

```dart
SearchScreen (StatefulWidget)
└─ Scaffold
   ├─ AppBar
   │  ├─ Leading: BackButton
   │  ├─ Title: SearchBar
   │  └─ Actions: [FilterButton, ViewToggleButton]
   │
   ├─ Body: Column
   │  ├─ SearchBar (Expanded)
   │  │  ├─ TextField (검색 입력)
   │  │  ├─ ClearButton (X)
   │  │  └─ AutocompleteOverlay
   │  │
   │  └─ Expanded
   │     └─ Consumer (검색 상태에 따라 분기)
   │        │
   │        ├─ SearchSuggestionsView (검색 전)
   │        │  ├─ RecentSearchesSection
   │        │  ├─ PopularSearchesSection
   │        │  └─ CategoryChipsSection
   │        │
   │        └─ SearchResultsView (검색 후)
   │           ├─ ResultsHeader
   │           │  ├─ SortDropdown
   │           │  └─ ViewToggle (List/Map)
   │           ├─ ActiveFiltersChips
   │           └─ ConditionalView
   │              ├─ PlaceListView (리스트 모드)
   │              │  └─ PaginatedListView
   │              │     └─ PlaceCard (List variant)
   │              └─ PlaceMapView (지도 모드)
   │                 ├─ GoogleMap / KakaoMap
   │                 └─ BottomSheet (선택된 장소)
   │
   └─ BottomNavigationBar
```

---

## 4. 핵심 컴포넌트 상세

### 4.1 SearchBar

```dart
// lib/features/search/presentation/widgets/search_bar_widget.dart
class SearchBarWidget extends ConsumerStatefulWidget {
  const SearchBarWidget({Key? key}) : super(key: key);

  @override
  ConsumerState<SearchBarWidget> createState() => _SearchBarWidgetState();
}

class _SearchBarWidgetState extends ConsumerState<SearchBarWidget> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  Timer? _debounceTimer;

  @override
  void initState() {
    super.initState();
    _controller.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    // Debounce: 300ms 대기 후 검색
    _debounceTimer?.cancel();
    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      final query = _controller.text.trim();
      if (query.isNotEmpty) {
        ref.read(searchQueryProvider.notifier).state = query;
        ref.read(searchNotifierProvider.notifier).search(query);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final suggestions = ref.watch(searchSuggestionsProvider);

    return Column(
      children: [
        Container(
          height: 56,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: TextField(
            controller: _controller,
            focusNode: _focusNode,
            autofocus: true,
            decoration: InputDecoration(
              hintText: '장소, 주소, 태그 검색',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _controller.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _controller.clear();
                        ref.read(searchQueryProvider.notifier).state = '';
                        ref.read(searchNotifierProvider.notifier).clear();
                      },
                    )
                  : null,
              filled: true,
              fillColor: Theme.of(context).colorScheme.surfaceVariant,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 12,
              ),
            ),
            textInputAction: TextInputAction.search,
            onSubmitted: (value) {
              if (value.trim().isNotEmpty) {
                ref.read(searchNotifierProvider.notifier).search(value.trim());
              }
            },
          ),
        ),

        // 자동완성 Suggestions
        if (_focusNode.hasFocus && _controller.text.length >= 2)
          suggestions.when(
            loading: () => const LinearProgressIndicator(),
            error: (_, __) => const SizedBox.shrink(),
            data: (suggestions) {
              if (suggestions.isEmpty) return const SizedBox.shrink();

              return Container(
                constraints: const BoxConstraints(maxHeight: 200),
                child: ListView.builder(
                  shrinkWrap: true,
                  itemCount: suggestions.length,
                  itemBuilder: (context, index) {
                    final suggestion = suggestions[index];
                    return ListTile(
                      leading: const Icon(Icons.search, size: 20),
                      title: Text(suggestion),
                      onTap: () {
                        _controller.text = suggestion;
                        _focusNode.unfocus();
                        ref.read(searchNotifierProvider.notifier).search(suggestion);
                      },
                    );
                  },
                ),
              );
            },
          ),
      ],
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    _debounceTimer?.cancel();
    super.dispose();
  }
}
```

### 4.2 SearchSuggestionsView (검색 전)

```dart
// lib/features/search/presentation/widgets/search_suggestions_view.dart
class SearchSuggestionsView extends ConsumerWidget {
  const SearchSuggestionsView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // 최근 검색어
        RecentSearchesSection(
          onSearchTap: (query) {
            ref.read(searchNotifierProvider.notifier).search(query);
          },
          onDeleteTap: (query) {
            ref.read(searchHistoryProvider.notifier).removeSearch(query);
          },
        ),

        const SizedBox(height: 24),

        // 인기 검색어
        PopularSearchesSection(
          onTagTap: (tag) {
            ref.read(searchNotifierProvider.notifier).searchByTag(tag);
          },
        ),

        const SizedBox(height: 24),

        // 카테고리
        CategoryChipsSection(
          onCategoryTap: (category) {
            ref.read(searchNotifierProvider.notifier).searchByCategory(category);
          },
        ),
      ],
    );
  }
}

class RecentSearchesSection extends ConsumerWidget {
  final Function(String) onSearchTap;
  final Function(String) onDeleteTap;

  const RecentSearchesSection({
    Key? key,
    required this.onSearchTap,
    required this.onDeleteTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recentSearches = ref.watch(searchHistoryProvider);

    if (recentSearches.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '최근 검색어',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 12),
        ...recentSearches.take(5).map((query) {
          return ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.history, size: 20),
            title: Text(query),
            trailing: IconButton(
              icon: const Icon(Icons.close, size: 18),
              onPressed: () => onDeleteTap(query),
              padding: const EdgeInsets.all(8),
              constraints: const BoxConstraints(
                minWidth: 32,
                minHeight: 32,
              ),
            ),
            onTap: () => onSearchTap(query),
          );
        }).toList(),
      ],
    );
  }
}

class PopularSearchesSection extends StatelessWidget {
  final Function(String) onTagTap;

  const PopularSearchesSection({
    Key? key,
    required this.onTagTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final popularTags = ['데이트', '뷰맛집', '브런치', '조용한', '디저트'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '인기 검색어',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: popularTags.map((tag) {
            return ActionChip(
              label: Text('#$tag'),
              onPressed: () => onTagTap(tag),
            );
          }).toList(),
        ),
      ],
    );
  }
}

class CategoryChipsSection extends StatelessWidget {
  final Function(String) onCategoryTap;

  const CategoryChipsSection({
    Key? key,
    required this.onCategoryTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final categories = [
      {'icon': Icons.local_cafe, 'label': '카페', 'value': 'cafe'},
      {'icon': Icons.restaurant, 'label': '맛집', 'value': 'restaurant'},
      {'icon': Icons.attractions, 'label': '관광', 'value': 'tourism'},
      {'icon': Icons.favorite, 'label': '데이트', 'value': 'date'},
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '카테고리',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 4,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1,
          ),
          itemCount: categories.length,
          itemBuilder: (context, index) {
            final category = categories[index];
            return InkWell(
              onTap: () => onCategoryTap(category['value'] as String),
              borderRadius: BorderRadius.circular(12),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    category['icon'] as IconData,
                    size: 32,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    category['label'] as String,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            );
          },
        ),
      ],
    );
  }
}
```

### 4.3 SearchResultsView (검색 후)

```dart
// lib/features/search/presentation/widgets/search_results_view.dart
class SearchResultsView extends ConsumerWidget {
  const SearchResultsView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchState = ref.watch(searchNotifierProvider);
    final viewMode = ref.watch(searchViewModeProvider);

    return Column(
      children: [
        // Results Header
        ResultsHeader(),

        // Active Filters
        if (searchState.hasActiveFilters)
          ActiveFiltersChips(),

        // Results List or Map
        Expanded(
          child: viewMode == SearchViewMode.list
              ? PlaceListView()
              : PlaceMapView(),
        ),
      ],
    );
  }
}

class ResultsHeader extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchState = ref.watch(searchNotifierProvider);
    final sortOption = ref.watch(searchSortOptionProvider);
    final viewMode = ref.watch(searchViewModeProvider);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: Theme.of(context).dividerColor,
            width: 1,
          ),
        ),
      ),
      child: Row(
        children: [
          Text(
            '검색 결과 (${searchState.totalCount}개)',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
          ),
          const Spacer(),

          // Sort Dropdown
          DropdownButton<SortOption>(
            value: sortOption,
            underline: const SizedBox.shrink(),
            items: SortOption.values.map((option) {
              return DropdownMenuItem(
                value: option,
                child: Text(option.label),
              );
            }).toList(),
            onChanged: (option) {
              if (option != null) {
                ref.read(searchSortOptionProvider.notifier).state = option;
                ref.read(searchNotifierProvider.notifier).sort(option);
              }
            },
          ),

          const SizedBox(width: 8),

          // View Toggle
          SegmentedButton<SearchViewMode>(
            segments: const [
              ButtonSegment(
                value: SearchViewMode.list,
                icon: Icon(Icons.list, size: 18),
              ),
              ButtonSegment(
                value: SearchViewMode.map,
                icon: Icon(Icons.map, size: 18),
              ),
            ],
            selected: {viewMode},
            onSelectionChanged: (Set<SearchViewMode> newSelection) {
              ref.read(searchViewModeProvider.notifier).state =
                  newSelection.first;
            },
            style: ButtonStyle(
              visualDensity: VisualDensity.compact,
            ),
          ),
        ],
      ),
    );
  }
}

class PlaceListView extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchState = ref.watch(searchNotifierProvider);

    return searchState.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error) => ErrorView(
        message: error,
        onRetry: () => ref.read(searchNotifierProvider.notifier).retry(),
      ),
      data: (results) {
        if (results.isEmpty) {
          return EmptyStateView(
            icon: Icons.search_off,
            title: '검색 결과가 없습니다',
            message: '다른 키워드로 검색해보세요',
          );
        }

        return PaginatedListView<Place>(
          items: results.places,
          hasMore: results.hasMore,
          onLoadMore: () {
            ref.read(searchNotifierProvider.notifier).loadMore();
          },
          itemBuilder: (context, place) {
            return PlaceCard(
              place: place,
              variant: PlaceCardVariant.list,
              onTap: () => context.push('/places/${place.id}'),
            );
          },
        );
      },
    );
  }
}
```

### 4.4 FilterBottomSheet

```dart
// lib/features/search/presentation/widgets/filter_bottom_sheet.dart
class FilterBottomSheet extends ConsumerStatefulWidget {
  const FilterBottomSheet({Key? key}) : super(key: key);

  @override
  ConsumerState<FilterBottomSheet> createState() => _FilterBottomSheetState();
}

class _FilterBottomSheetState extends ConsumerState<FilterBottomSheet> {
  late SearchFilter _currentFilter;

  @override
  void initState() {
    super.initState();
    _currentFilter = ref.read(searchFilterProvider);
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.9,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surface,
            borderRadius: const BorderRadius.vertical(
              top: Radius.circular(20),
            ),
          ),
          child: Column(
            children: [
              // Handle
              Container(
                margin: const EdgeInsets.symmetric(vertical: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    Text(
                      '필터',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _currentFilter = SearchFilter.initial();
                        });
                      },
                      child: const Text('초기화'),
                    ),
                  ],
                ),
              ),

              const Divider(),

              // Filter Options
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  children: [
                    // 카테고리 필터
                    _buildFilterSection(
                      title: '카테고리',
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: PlaceCategory.values.map((category) {
                          final isSelected = _currentFilter.categories
                              .contains(category);
                          return FilterChip(
                            label: Text(category.label),
                            selected: isSelected,
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _currentFilter = _currentFilter.copyWith(
                                    categories: [
                                      ..._currentFilter.categories,
                                      category,
                                    ],
                                  );
                                } else {
                                  _currentFilter = _currentFilter.copyWith(
                                    categories: _currentFilter.categories
                                        .where((c) => c != category)
                                        .toList(),
                                  );
                                }
                              });
                            },
                          );
                        }).toList(),
                      ),
                    ),

                    const SizedBox(height: 24),

                    // 거리 필터
                    _buildFilterSection(
                      title: '거리',
                      child: Column(
                        children: [
                          Slider(
                            value: _currentFilter.maxDistance ?? 5000,
                            min: 500,
                            max: 10000,
                            divisions: 19,
                            label: '${(_currentFilter.maxDistance ?? 5000) ~/ 1000}km',
                            onChanged: (value) {
                              setState(() {
                                _currentFilter = _currentFilter.copyWith(
                                  maxDistance: value,
                                );
                              });
                            },
                          ),
                          Text(
                            '${(_currentFilter.maxDistance ?? 5000) ~/ 1000}km 이내',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ],
                      ),
                    ),

                    const SizedBox(height: 24),

                    // 평점 필터
                    _buildFilterSection(
                      title: '평점',
                      child: Column(
                        children: [
                          RadioListTile<double?>(
                            title: const Text('전체'),
                            value: null,
                            groupValue: _currentFilter.minRating,
                            onChanged: (value) {
                              setState(() {
                                _currentFilter = _currentFilter.copyWith(
                                  minRating: value,
                                );
                              });
                            },
                          ),
                          RadioListTile<double?>(
                            title: const Text('⭐ 4.0 이상'),
                            value: 4.0,
                            groupValue: _currentFilter.minRating,
                            onChanged: (value) {
                              setState(() {
                                _currentFilter = _currentFilter.copyWith(
                                  minRating: value,
                                );
                              });
                            },
                          ),
                          RadioListTile<double?>(
                            title: const Text('⭐ 4.5 이상'),
                            value: 4.5,
                            groupValue: _currentFilter.minRating,
                            onChanged: (value) {
                              setState(() {
                                _currentFilter = _currentFilter.copyWith(
                                  minRating: value,
                                );
                              });
                            },
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // Action Buttons
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  border: Border(
                    top: BorderSide(
                      color: Theme.of(context).dividerColor,
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('취소'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      flex: 2,
                      child: ElevatedButton(
                        onPressed: () {
                          ref.read(searchFilterProvider.notifier).state =
                              _currentFilter;
                          ref.read(searchNotifierProvider.notifier)
                              .applyFilter(_currentFilter);
                          Navigator.pop(context);
                        },
                        child: const Text('적용'),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildFilterSection({
    required String title,
    required Widget child,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
        ),
        const SizedBox(height: 12),
        child,
      ],
    );
  }
}
```

---

## 5. 상태 관리

```dart
// lib/features/search/presentation/providers/search_providers.dart

// 검색 쿼리
final searchQueryProvider = StateProvider<String>((ref) => '');

// 검색 히스토리
final searchHistoryProvider = StateNotifierProvider<SearchHistoryNotifier, List<String>>((ref) {
  return SearchHistoryNotifier();
});

// 검색 자동완성
final searchSuggestionsProvider = FutureProvider.autoDispose<List<String>>((ref) async {
  final query = ref.watch(searchQueryProvider);
  if (query.length < 2) return [];

  final repository = ref.read(placeRepositoryProvider);
  final result = await repository.getSearchSuggestions(query);

  return result.when(
    success: (suggestions) => suggestions,
    failure: (_) => [],
  );
});

// 검색 결과
final searchNotifierProvider = StateNotifierProvider<SearchNotifier, AsyncValue<SearchResults>>((ref) {
  return SearchNotifier(ref.read(placeRepositoryProvider));
});

// 필터
final searchFilterProvider = StateProvider<SearchFilter>((ref) => SearchFilter.initial());

// 정렬 옵션
final searchSortOptionProvider = StateProvider<SortOption>((ref) => SortOption.recommended);

// 뷰 모드
final searchViewModeProvider = StateProvider<SearchViewMode>((ref) => SearchViewMode.list);

// SearchNotifier
class SearchNotifier extends StateNotifier<AsyncValue<SearchResults>> {
  final PlaceRepository _repository;
  int _currentPage = 1;
  String _currentQuery = '';
  SearchFilter _currentFilter = SearchFilter.initial();

  SearchNotifier(this._repository) : super(const AsyncValue.loading());

  Future<void> search(String query) async {
    _currentQuery = query;
    _currentPage = 1;
    state = const AsyncValue.loading();

    final result = await _repository.searchPlaces(
      query: query,
      filter: _currentFilter,
      page: 1,
    );

    state = result.when(
      success: (results) => AsyncValue.data(results),
      failure: (error) => AsyncValue.error(error, StackTrace.current),
    );
  }

  Future<void> loadMore() async {
    if (state.value == null || !state.value!.hasMore) return;

    _currentPage++;
    final result = await _repository.searchPlaces(
      query: _currentQuery,
      filter: _currentFilter,
      page: _currentPage,
    );

    result.when(
      success: (newResults) {
        state = AsyncValue.data(
          state.value!.copyWith(
            places: [...state.value!.places, ...newResults.places],
            hasMore: newResults.hasMore,
          ),
        );
      },
      failure: (_) {
        _currentPage--; // 실패 시 페이지 롤백
      },
    );
  }

  Future<void> applyFilter(SearchFilter filter) async {
    _currentFilter = filter;
    await search(_currentQuery);
  }

  void clear() {
    state = const AsyncValue.loading();
    _currentQuery = '';
    _currentPage = 1;
  }
}

// Models
enum SortOption {
  recommended('추천순'),
  distance('거리순'),
  rating('평점순'),
  latest('최신순');

  final String label;
  const SortOption(this.label);
}

enum SearchViewMode { list, map }

@freezed
class SearchFilter with _$SearchFilter {
  const factory SearchFilter({
    @Default([]) List<PlaceCategory> categories,
    double? maxDistance,
    double? minRating,
    @Default([]) List<String> tags,
  }) = _SearchFilter;

  factory SearchFilter.initial() => const SearchFilter();
}

@freezed
class SearchResults with _$SearchResults {
  const factory SearchResults({
    required List<Place> places,
    required int totalCount,
    required bool hasMore,
  }) = _SearchResults;
}
```

---

## 6. 완료 정의 (DoD)

- [ ] 검색 기능 구현 (실시간 자동완성 포함)
- [ ] 필터 기능 구현 (카테고리, 거리, 평점)
- [ ] 리스트/지도 뷰 전환
- [ ] 무한 스크롤 페이지네이션
- [ ] 검색 히스토리 저장/삭제
- [ ] 접근성 검증
- [ ] 테스트 커버리지 80% 이상

---

## 7. 수용 기준

- **Given** 사용자가 검색어 입력
- **When** 2글자 이상 입력
- **Then** 300ms 대기 후 자동완성 표시, 1초 이내 검색 결과

- **Given** 필터 적용
- **When** 필터 옵션 선택 후 적용
- **Then** 필터링된 결과 즉시 표시

---

*다음: 장소 상세 화면 작성 중...*
