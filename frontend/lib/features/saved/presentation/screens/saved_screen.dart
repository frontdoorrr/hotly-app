import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../home/presentation/widgets/place_card.dart';
import '../providers/saved_places_provider.dart';

class SavedScreen extends ConsumerWidget {
  const SavedScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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

    return RefreshIndicator(
      onRefresh: () async {
        await ref.read(savedPlacesProvider.notifier).refresh();
      },
      child: ListView.builder(
        padding: const EdgeInsets.all(AppTheme.space4),
        itemCount: state.places.length,
        itemBuilder: (context, index) {
          final place = state.places[index];
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
