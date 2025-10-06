import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../shared/models/place.dart';

/// Place Card - 장소 카드 위젯
/// 추천, 근처, 인기 장소 등에서 재사용
class PlaceCard extends StatelessWidget {
  final Place place;
  final VoidCallback onTap;
  final bool isHorizontal;

  const PlaceCard({
    super.key,
    required this.place,
    required this.onTap,
    this.isHorizontal = true,
  });

  @override
  Widget build(BuildContext context) {
    if (isHorizontal) {
      return _buildHorizontalCard(context);
    } else {
      return _buildVerticalCard(context);
    }
  }

  Widget _buildHorizontalCard(BuildContext context) {
    final theme = Theme.of(context);

    // TODO(human): Add Semantics widget here for accessibility
    // Wrap Card with Semantics and provide meaningful label
    // Example: Semantics(label: "...", button: true, excludeSemantics: true, child: Card(...))

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Container(
          width: 280,
          padding: const EdgeInsets.all(AppTheme.space3),
          child: Row(
            children: [
              // 이미지
              ClipRRect(
                borderRadius: BorderRadius.circular(AppTheme.radiusLg),
                child: place.imageUrl != null
                    ? CachedNetworkImage(
                        imageUrl: place.imageUrl!,
                        width: 80,
                        height: 80,
                        fit: BoxFit.cover,
                        placeholder: (context, url) => Container(
                          color: theme.colorScheme.surfaceContainerHighest,
                          child: const Center(
                            child: CircularProgressIndicator(),
                          ),
                        ),
                        errorWidget: (context, url, error) => Container(
                          color: theme.colorScheme.surfaceContainerHighest,
                          child: const Icon(Icons.place),
                        ),
                      )
                    : Container(
                        width: 80,
                        height: 80,
                        color: theme.colorScheme.surfaceContainerHighest,
                        child: const Icon(Icons.place),
                      ),
              ),
              const SizedBox(width: AppTheme.space3),

              // 정보
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      place.name,
                      style: theme.textTheme.titleMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: AppTheme.space1),
                    Row(
                      children: [
                        Text(
                          place.address,
                          style: theme.textTheme.bodySmall,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(width: AppTheme.space2),
                        if (place.rating > 0) ...[
                          const Icon(Icons.star, size: 14, color: Colors.amber),
                          const SizedBox(width: 2),
                          Text(
                            place.rating.toStringAsFixed(1),
                            style: theme.textTheme.bodySmall,
                          ),
                        ],
                      ],
                    ),
                    if (place.tags.isNotEmpty) ...[
                      const SizedBox(height: AppTheme.space1),
                      Wrap(
                        spacing: AppTheme.space1,
                        children: place.tags
                            .take(2)
                            .map((tag) => Text(
                                  '#$tag',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: theme.colorScheme.primary,
                                  ),
                                ))
                            .toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildVerticalCard(BuildContext context) {
    final theme = Theme.of(context);

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 이미지
            AspectRatio(
              aspectRatio: 1,
              child: place.imageUrl != null
                  ? CachedNetworkImage(
                      imageUrl: place.imageUrl!,
                      fit: BoxFit.cover,
                      placeholder: (context, url) => Container(
                        color: theme.colorScheme.surfaceContainerHighest,
                        child: const Center(
                          child: CircularProgressIndicator(),
                        ),
                      ),
                      errorWidget: (context, url, error) => Container(
                        color: theme.colorScheme.surfaceContainerHighest,
                        child: const Icon(Icons.place, size: 48),
                      ),
                    )
                  : Container(
                      color: theme.colorScheme.surfaceContainerHighest,
                      child: const Icon(Icons.place, size: 48),
                    ),
            ),

            // 정보
            Padding(
              padding: const EdgeInsets.all(AppTheme.space2),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    place.name,
                    style: theme.textTheme.titleSmall,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: AppTheme.space1),
                  if (place.rating > 0)
                    Row(
                      children: [
                        const Icon(Icons.star, size: 12, color: Colors.amber),
                        const SizedBox(width: 2),
                        Text(
                          place.rating.toStringAsFixed(1),
                          style: theme.textTheme.bodySmall,
                        ),
                      ],
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
