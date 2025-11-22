import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/models/place.dart';
import '../../../auth/presentation/providers/auth_provider.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../providers/saved_places_provider.dart';
import '../widgets/tag_filter_chips.dart';

class SavedScreen extends ConsumerWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final authState = ref.watch(authProvider);
    final state = ref.watch(savedPlacesProvider);

    // 로그인 안 됨
    if (authState.status != AuthStatus.authenticated) {
      return Scaffold(
        appBar: AppBar(
          title: const Text('저장한 장소'),
          automaticallyImplyLeading: false,
        ),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(
                  Icons.bookmark_border,
                  size: 80,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(height: 24),
                Text(
                  '로그인이 필요합니다',
                  style: AppTextStyles.h3,
                ),
                const SizedBox(height: 8),
                Text(
                  '로그인하고 마음에 드는 장소를 저장해보세요',
                  style: AppTextStyles.body2.copyWith(
                    color: AppColors.textSecondary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: () {
                    context.push('/login');
                  },
                  child: const Text('로그인하기'),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('저장한 장소'),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(savedPlacesProvider.notifier).refresh();
            },
            tooltip: '새로고침',
          ),
        ],
      ),
      body: _buildBody(context, state, ref),
    );
  }

  Widget _buildBody(BuildContext context, SavedPlacesState state, WidgetRef ref) {
    final notifier = ref.read(savedPlacesProvider.notifier);
    if (state.isLoading) {
      return const Center(
        child: CircularProgressIndicator(),
      );
    }

    if (state.hasError) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 80,
              color: AppColors.error,
            ),
            const SizedBox(height: AppTheme.space4),
            Text(
              '오류가 발생했습니다',
              style: AppTextStyles.h3.copyWith(
                color: AppColors.error,
              ),
            ),
            const SizedBox(height: AppTheme.space2),
            Text(
              state.errorMessage ?? '장소를 불러올 수 없습니다',
              style: AppTextStyles.body2.copyWith(
                color: AppColors.textSecondary,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppTheme.space4),
            ElevatedButton(
              onPressed: () {
                ref.read(savedPlacesProvider.notifier).refresh();
              },
              child: const Text('다시 시도'),
            ),
          ],
        ),
      );
    }

    if (state.places.isEmpty) {
      return _buildEmptyState(context);
    }

    // Calculate tag statistics and filtered places from provider
    final tagStats = notifier.tagStatistics;
    final filteredPlaces = notifier.filteredPlaces;

    return Column(
      children: [
        // Tag filter chips
        if (tagStats.isNotEmpty)
          TagFilterChips(
            availableTags: tagStats.keys.toList(),
            tagCounts: tagStats.values.toList(),
            selectedTags: state.selectedTags,
            totalPlacesCount: state.places.length,
            onTagSelected: (tag) {
              if (tag.isEmpty) {
                notifier.clearTagFilters();
              } else {
                notifier.toggleTag(tag);
              }
            },
          ),

        // Places list
        Expanded(
          child: filteredPlaces.isEmpty
              ? _buildNoResultsState(context, ref)
              : RefreshIndicator(
                  onRefresh: () async {
                    await ref.read(savedPlacesProvider.notifier).refresh();
                  },
                  child: ListView.builder(
                    padding: const EdgeInsets.all(AppTheme.space4),
                    itemCount: filteredPlaces.length,
                    itemBuilder: (context, index) {
                      final place = filteredPlaces[index];
                      return Padding(
                        padding: const EdgeInsets.only(bottom: AppTheme.space3),
                        child: PlaceCard(
                          place: place,
                          onTap: () {
                            // TODO: Navigate to place detail
                          },
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }

  Widget _buildNoResultsState(BuildContext context, WidgetRef ref) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.search_off,
            size: 80,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: AppTheme.space4),
          Text(
            '필터 조건에 맞는 장소가 없습니다',
            style: AppTextStyles.h3.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTheme.space2),
          Text(
            '다른 태그를 선택해보세요',
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTheme.space4),
          OutlinedButton(
            onPressed: () {
              ref.read(savedPlacesProvider.notifier).clearTagFilters();
            },
            child: const Text('필터 초기화'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.bookmark_border,
            size: 80,
            color: theme.colorScheme.outline,
          ),
          const SizedBox(height: AppTheme.space4),
          Text(
            '저장한 장소가 없습니다',
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: AppTheme.space2),
          Text(
            '마음에 드는 장소를 저장해보세요',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }
}
