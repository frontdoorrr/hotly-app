import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/models/place.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';

/// Bottom sheet showing selected place information
class PlaceMarkerInfo extends ConsumerWidget {
  final String placeId;
  final VoidCallback onClose;

  const PlaceMarkerInfo({
    super.key,
    required this.placeId,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final savedState = ref.watch(savedPlacesProvider);

    // placeId로 Place 객체 찾기
    try {
      final place = savedState.places.firstWhere(
        (p) => p.id == placeId,
      );

      return _buildInfo(context, theme, place);
    } catch (e) {
      // 장소를 찾을 수 없는 경우
      debugPrint('⚠️ Place not found: $placeId');
      return const SizedBox.shrink();
    }
  }

  Widget _buildInfo(BuildContext context, ThemeData theme, Place place) {

    return Container(
      padding: const EdgeInsets.all(AppTheme.space4),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(AppTheme.radiusXl),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더: 장소명 + 닫기 버튼
          Row(
            children: [
              Expanded(
                child: Text(
                  place.name,
                  style: theme.textTheme.titleLarge,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: onClose,
                tooltip: '닫기',
              ),
            ],
          ),

          const SizedBox(height: AppTheme.space2),

          // 주소
          if (place.address != null)
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(
                  Icons.place_outlined,
                  size: 16,
                  color: theme.colorScheme.secondary,
                ),
                const SizedBox(width: AppTheme.space1),
                Expanded(
                  child: Text(
                    place.address!,
                    style: theme.textTheme.bodyMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),

          const SizedBox(height: AppTheme.space1),

          // 카테고리
          Row(
            children: [
              Icon(
                Icons.category_outlined,
                size: 16,
                color: theme.colorScheme.secondary,
              ),
              const SizedBox(width: AppTheme.space1),
              Text(
                place.category,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: theme.colorScheme.primary,
                ),
              ),
            ],
          ),

          // 평점 (있는 경우)
          if (place.rating > 0) ...[
            const SizedBox(height: AppTheme.space1),
            Row(
              children: [
                const Icon(
                  Icons.star,
                  size: 16,
                  color: Colors.amber,
                ),
                const SizedBox(width: AppTheme.space1),
                Text(
                  place.rating.toStringAsFixed(1),
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ],

          const SizedBox(height: AppTheme.space3),

          // 상세보기 버튼
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                // PlaceDetailScreen으로 이동
                context.push('/place/${place.id}');
              },
              child: const Text('상세보기'),
            ),
          ),
        ],
      ),
    );
  }
}
