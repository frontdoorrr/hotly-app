import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../../shared/models/place.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../providers/saved_places_provider.dart';
import '../widgets/tag_filter_chips.dart';

class SavedScreen extends ConsumerStatefulWidget {
  const SavedScreen({super.key});

  @override
  ConsumerState<SavedScreen> createState() => _SavedScreenState();
}

class _SavedScreenState extends ConsumerState<SavedScreen> {
  // Selected tags for filtering
  final Set<String> _selectedTags = {};

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final state = ref.watch(savedPlacesProvider);

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

    // Calculate tag statistics
    final tagStats = _calculateTagStatistics(state.places);

    // Filter places based on selected tags
    final filteredPlaces = _filterPlaces(state.places);

    return Column(
      children: [
        // Tag filter chips
        if (tagStats.isNotEmpty)
          TagFilterChips(
            availableTags: tagStats.keys.toList(),
            tagCounts: tagStats.values.toList(),
            selectedTags: _selectedTags,
            totalPlacesCount: state.places.length,
            onTagSelected: _handleTagSelected,
          ),

        // Places list
        Expanded(
          child: filteredPlaces.isEmpty
              ? _buildNoResultsState(context)
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

  /// Calculate tag statistics from places
  Map<String, int> _calculateTagStatistics(List<Place> places) {
    final tagCounts = <String, int>{};

    for (final place in places) {
      for (final tag in place.tags) {
        tagCounts[tag] = (tagCounts[tag] ?? 0) + 1;
      }
    }

    // Sort by count descending
    final sortedEntries = tagCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    return Map.fromEntries(sortedEntries);
  }

  /// Filter places based on selected tags
  List<Place> _filterPlaces(List<Place> places) {
    if (_selectedTags.isEmpty) {
      return places;
    }

    return places.where((place) {
      // Check if place has any of the selected tags
      return place.tags.any((tag) => _selectedTags.contains(tag));
    }).toList();
  }

  /// Handle tag selection
  void _handleTagSelected(String tag) {
    setState(() {
      if (tag.isEmpty) {
        // Clear all filters
        _selectedTags.clear();
      } else if (_selectedTags.contains(tag)) {
        // Deselect tag
        _selectedTags.remove(tag);
      } else {
        // Select tag
        _selectedTags.add(tag);
      }
    });
  }

  Widget _buildNoResultsState(BuildContext context) {
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
              setState(() {
                _selectedTags.clear();
              });
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
