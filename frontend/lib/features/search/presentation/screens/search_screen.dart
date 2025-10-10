import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../providers/search_provider.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _searchController.addListener(_onSearchChanged);
  }

  void _onSearchChanged() {
    ref.read(searchProvider.notifier).updateSearchQuery(_searchController.text);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  void _performSearch() {
    _searchFocusNode.unfocus();
    ref.read(searchProvider.notifier).search();
  }

  @override
  Widget build(BuildContext context) {
    final searchState = ref.watch(searchProvider);
    final showSuggestions = _searchFocusNode.hasFocus &&
        (searchState.autocompleteSuggestions.isNotEmpty ||
            searchState.searchHistory.isNotEmpty);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        title: TextField(
          controller: _searchController,
          focusNode: _searchFocusNode,
          decoration: InputDecoration(
            hintText: '장소, 태그, 지역 검색...',
            hintStyle: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
            prefixIcon: const Icon(Icons.search),
            suffixIcon: searchState.searchQuery.isNotEmpty
                ? IconButton(
                    icon: const Icon(Icons.clear),
                    onPressed: () {
                      _searchController.clear();
                      ref.read(searchProvider.notifier).clearSearchResults();
                    },
                  )
                : null,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            filled: true,
            fillColor: AppColors.surface,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16),
          ),
          style: AppTextStyles.body1,
          textInputAction: TextInputAction.search,
          onSubmitted: (_) => _performSearch(),
        ),
        backgroundColor: AppColors.background,
        elevation: 0,
      ),
      body: Stack(
        children: [
          // Main content
          _buildMainContent(searchState),

          // Autocomplete suggestions overlay
          if (showSuggestions)
            Positioned(
              top: 0,
              left: 0,
              right: 0,
              child: _buildSuggestionsOverlay(searchState),
            ),
        ],
      ),
    );
  }

  Widget _buildMainContent(SearchState state) {
    if (state.isSearching) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (state.error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.error_outline,
              size: 64,
              color: AppColors.error,
            ),
            const SizedBox(height: 16),
            Text(
              '검색 중 오류가 발생했습니다',
              style: AppTextStyles.h4,
            ),
            const SizedBox(height: 8),
            Text(
              state.error!.message,
              style: AppTextStyles.body2.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => ref.read(searchProvider.notifier).search(),
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (state.searchResults.isNotEmpty) {
      return _buildSearchResults(state);
    }

    if (state.searchQuery.isNotEmpty && !state.isSearching) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.search_off,
              size: 64,
              color: AppColors.textSecondary,
            ),
            const SizedBox(height: 16),
            Text(
              '검색 결과가 없습니다',
              style: AppTextStyles.h4,
            ),
            const SizedBox(height: 8),
            Text(
              '다른 키워드로 검색해보세요',
              style: AppTextStyles.body2.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
      );
    }

    return _buildEmptyState(state);
  }

  Widget _buildEmptyState(SearchState state) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (state.searchHistory.isNotEmpty) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '최근 검색어',
                  style: AppTextStyles.h4,
                ),
                TextButton(
                  onPressed: () {
                    ref.read(searchProvider.notifier).clearSearchHistory();
                  },
                  child: Text(
                    '전체 삭제',
                    style: AppTextStyles.label2.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: state.searchHistory.take(10).map((query) {
                return ActionChip(
                  label: Text(query),
                  onPressed: () {
                    _searchController.text = query;
                    _performSearch();
                  },
                  avatar: const Icon(Icons.history, size: 18),
                );
              }).toList(),
            ),
            const SizedBox(height: 32),
          ],
          Text(
            '인기 검색어',
            style: AppTextStyles.h4,
          ),
          const SizedBox(height: 12),
          _buildPopularSearches(),
        ],
      ),
    );
  }

  Widget _buildPopularSearches() {
    final popularSearches = [
      '강남 맛집',
      '홍대 카페',
      '한강 뷰',
      '데이트 코스',
      '인스타 감성',
      '브런치',
    ];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: popularSearches.map((query) {
        return ActionChip(
          label: Text(query),
          onPressed: () {
            _searchController.text = query;
            _performSearch();
          },
          avatar: const Icon(Icons.trending_up, size: 18),
        );
      }).toList(),
    );
  }

  Widget _buildSuggestionsOverlay(SearchState state) {
    return Material(
      elevation: 4,
      borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
      child: Container(
        constraints: const BoxConstraints(maxHeight: 300),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: const BorderRadius.vertical(bottom: Radius.circular(12)),
        ),
        child: ListView(
          shrinkWrap: true,
          padding: EdgeInsets.zero,
          children: [
            if (state.autocompleteSuggestions.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  '자동완성',
                  style: AppTextStyles.label2.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
              ...state.autocompleteSuggestions.map((suggestion) {
                return ListTile(
                  leading: const Icon(Icons.search, size: 20),
                  title: Text(suggestion),
                  onTap: () {
                    ref.read(searchProvider.notifier).selectSuggestion(suggestion);
                    _searchController.text = suggestion;
                    _searchFocusNode.unfocus();
                  },
                );
              }),
            ],
            if (state.searchQuery.isEmpty && state.searchHistory.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.all(12),
                child: Text(
                  '최근 검색어',
                  style: AppTextStyles.label2.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ),
              ...state.searchHistory.take(5).map((query) {
                return ListTile(
                  leading: const Icon(Icons.history, size: 20),
                  title: Text(query),
                  onTap: () {
                    _searchController.text = query;
                    _performSearch();
                  },
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildSearchResults(SearchState state) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: state.searchResults.length,
      itemBuilder: (context, index) {
        final place = state.searchResults[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: PlaceCard(
            place: place,
            onTap: () {
              context.push('/places/${place.id}');
            },
          ),
        );
      },
    );
  }
}
