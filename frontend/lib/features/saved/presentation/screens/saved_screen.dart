import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
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
          title: Text(context.l10n.place_savedPlaces),
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
                  context.l10n.auth_loginRequired,
                  style: AppTextStyles.h3,
                ),
                const SizedBox(height: 8),
                Text(
                  context.l10n.place_loginToSavePlaces,
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
                  child: Text(context.l10n.auth_loginButton),
                ),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.place_savedPlaces),
        automaticallyImplyLeading: false,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              ref.read(savedPlacesProvider.notifier).refresh();
            },
            tooltip: context.l10n.common_refresh,
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
              context.l10n.error_occurred,
              style: AppTextStyles.h3.copyWith(
                color: AppColors.error,
              ),
            ),
            const SizedBox(height: AppTheme.space2),
            Text(
              state.errorMessage ?? context.l10n.place_cannotLoadPlaces,
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
              child: Text(context.l10n.common_retry),
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
            context.l10n.place_noFilterResults,
            style: AppTextStyles.h3.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTheme.space2),
          Text(
            context.l10n.place_tryOtherTags,
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: AppTheme.space4),
          OutlinedButton(
            onPressed: () {
              ref.read(savedPlacesProvider.notifier).clearTagFilters();
            },
            child: Text(context.l10n.place_clearFilters),
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
            context.l10n.place_noSavedPlaces,
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
          const SizedBox(height: AppTheme.space2),
          Text(
            context.l10n.place_savePlacePrompt,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: theme.colorScheme.outline,
            ),
          ),
        ],
      ),
    );
  }
}
