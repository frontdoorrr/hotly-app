import 'package:flutter/material.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/map_entities.dart';

/// Bottom sheet showing search result place information
class SearchResultInfo extends StatelessWidget {
  final PlaceSearchResult place;
  final VoidCallback onClose;
  final VoidCallback? onSave;

  const SearchResultInfo({
    super.key,
    required this.place,
    required this.onClose,
    this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

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
                  place.placeName,
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
                  place.address,
                  style: theme.textTheme.bodyMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),

          // 카테고리 (있는 경우)
          if (place.categoryName != null) ...[
            const SizedBox(height: AppTheme.space1),
            Row(
              children: [
                Icon(
                  Icons.category_outlined,
                  size: 16,
                  color: theme.colorScheme.secondary,
                ),
                const SizedBox(width: AppTheme.space1),
                Text(
                  place.categoryName!,
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.primary,
                  ),
                ),
              ],
            ),
          ],

          // 거리 (있는 경우)
          if (place.distance != null) ...[
            const SizedBox(height: AppTheme.space1),
            Row(
              children: [
                Icon(
                  Icons.near_me_outlined,
                  size: 16,
                  color: theme.colorScheme.secondary,
                ),
                const SizedBox(width: AppTheme.space1),
                Text(
                  '${(place.distance! / 1000).toStringAsFixed(1)} km',
                  style: theme.textTheme.bodyMedium,
                ),
              ],
            ),
          ],

          const SizedBox(height: AppTheme.space3),

          // 저장 버튼 (있는 경우)
          if (onSave != null)
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: onSave,
                icon: const Icon(Icons.bookmark_add_outlined),
                label: const Text('장소 저장'),
              ),
            ),
        ],
      ),
    );
  }
}
