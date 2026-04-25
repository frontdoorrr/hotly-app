import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:shimmer/shimmer.dart';
import '../../../../core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../archive/domain/entities/archived_content.dart';
import '../../../archive/presentation/providers/archive_provider.dart';
import '../../../archive/presentation/widgets/archive_input_sheet.dart';
import '../../../archive/presentation/widgets/content_type_badge.dart';
import '../../../share_queue/presentation/widgets/share_queue_badge.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final recentAsync = ref.watch(recentArchiveProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Image.asset(
              'assets/images/logo/logo-icon-64.png',
              width: 28,
              height: 28,
              fit: BoxFit.contain,
            ),
            const SizedBox(width: 8),
            Text(context.l10n.appName),
          ],
        ),
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.refresh(recentArchiveProvider.future),
        child: CustomScrollView(
          slivers: [
            const SliverToBoxAdapter(child: ShareQueueBadge()),

            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 16, 8, 4),
                child: Row(
                  children: [
                    Text(context.l10n.home_recentArchives, style: theme.textTheme.titleLarge),
                    const Spacer(),
                    TextButton(
                      onPressed: () => context.go('/discover'),
                      child: Text(context.l10n.home_viewAll),
                    ),
                  ],
                ),
              ),
            ),

            recentAsync.when(
              loading: () => SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (_, __) => const Padding(
                      padding: EdgeInsets.only(bottom: 10),
                      child: RepaintBoundary(child: _HomeSkeletonTile()),
                    ),
                    childCount: 3,
                  ),
                ),
              ),
              error: (_, __) => SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(48),
                    child: Text(
                      context.l10n.home_loadFailed,
                      style: theme.textTheme.bodyMedium,
                    ),
                  ),
                ),
              ),
              data: (items) => items.isEmpty
                  ? SliverToBoxAdapter(
                      child: _EmptyState(
                        onAddTap: () => ArchiveInputSheet.show(context),
                      ),
                    )
                  : SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      sliver: SliverList(
                        delegate: SliverChildBuilderDelegate(
                          (context, index) {
                            if (index.isOdd) {
                              return const SizedBox(height: 10);
                            }
                            final itemIndex = index ~/ 2;
                            final item = items[itemIndex];
                            final delay = Duration(
                              milliseconds: (itemIndex * 50).clamp(0, 200),
                            );
                            return RepaintBoundary(
                              child: _RecentArchiveTile(
                                content: item,
                                onTap: () => context.push('/archive/${item.id}'),
                              )
                                  .animate(key: ValueKey(item.id))
                                  .fadeIn(
                                    duration: 250.ms,
                                    delay: delay,
                                    curve: Curves.easeOut,
                                  )
                                  .slideY(
                                    begin: 0.06,
                                    end: 0,
                                    duration: 250.ms,
                                    delay: delay,
                                  ),
                            );
                          },
                          childCount: items.length * 2 - 1,
                        ),
                      ),
                    ),
            ),

            const SliverToBoxAdapter(child: SizedBox(height: 80)),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => ArchiveInputSheet.show(context),
        icon: const Icon(Icons.add_link),
        label: Text(context.l10n.home_archivingFab),
      ),
    );
  }
}

class _RecentArchiveTile extends StatelessWidget {
  final ArchivedContent content;
  final VoidCallback onTap;

  const _RecentArchiveTile({required this.content, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      clipBehavior: Clip.hardEdge,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Thumbnail(content: content),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ContentTypeBadge(contentType: content.contentType),
                    const SizedBox(height: 4),
                    if (content.title != null)
                      Text(
                        content.title!,
                        style: AppTextStyles.bodyLarge,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    if (content.summary != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        content.summary!,
                        style: AppTextStyles.body2
                            .copyWith(color: AppColors.textSecondary),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ],
                    const SizedBox(height: 6),
                    Text(
                      _formatDate(content.archivedAt),
                      style: AppTextStyles.bodySmall
                          .copyWith(color: AppColors.textTertiary),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime dt) =>
      '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';
}

class _Thumbnail extends StatelessWidget {
  final ArchivedContent content;
  const _Thumbnail({required this.content});

  @override
  Widget build(BuildContext context) {
    if (content.thumbnailUrl != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: content.thumbnailUrl!,
          width: 60,
          height: 60,
          fit: BoxFit.cover,
          errorWidget: (_, __, ___) => _fallback(),
        ),
      );
    }
    return _fallback();
  }

  Widget _fallback() {
    final (icon, color) = switch (content.platform) {
      Platform.instagram => (Icons.camera_alt, Colors.purple),
      Platform.naver_blog => (Icons.article, Colors.green),
      _ => (Icons.play_circle, Colors.red),
    };
    return Container(
      width: 60,
      height: 60,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color),
    );
  }
}


class _HomeSkeletonTile extends StatelessWidget {
  const _HomeSkeletonTile();

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final baseColor = isDark ? Colors.grey[800]! : Colors.grey[200]!;
    final highlightColor = isDark ? Colors.grey[700]! : Colors.grey[100]!;
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: baseColor),
      ),
      child: Shimmer.fromColors(
        baseColor: baseColor,
        highlightColor: highlightColor,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: isDark ? Colors.grey[600]! : Colors.white,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 56,
                      height: 20,
                      decoration: BoxDecoration(
                        color: isDark ? Colors.grey[600]! : Colors.white,
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      height: 15,
                      decoration: BoxDecoration(
                        color: isDark ? Colors.grey[600]! : Colors.white,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 5),
                    Container(
                      height: 13,
                      decoration: BoxDecoration(
                        color: isDark ? Colors.grey[600]! : Colors.white,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      width: 80,
                      height: 11,
                      decoration: BoxDecoration(
                        color: isDark ? Colors.grey[600]! : Colors.white,
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final VoidCallback onAddTap;
  const _EmptyState({required this.onAddTap});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(48),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.bookmarks_outlined, size: 64, color: Colors.grey[300]),
            const SizedBox(height: 16),
            Text(
              context.l10n.home_noContent,
              style: AppTextStyles.body2
                  .copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 8),
            Text(
              context.l10n.home_addLinkPrompt,
              style: AppTextStyles.bodySmall
                  .copyWith(color: AppColors.textTertiary),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onAddTap,
              icon: const Icon(Icons.add_link),
              label: Text(context.l10n.home_addLink),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.primary,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
