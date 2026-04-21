import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
            Icon(Icons.local_fire_department, color: theme.colorScheme.primary),
            const SizedBox(width: 8),
            const Text('Hotly'),
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
                    Text('최근 아카이빙', style: theme.textTheme.titleLarge),
                    const Spacer(),
                    TextButton(
                      onPressed: () => context.go('/discover'),
                      child: const Text('전체 보기 →'),
                    ),
                  ],
                ),
              ),
            ),

            recentAsync.when(
              loading: () => const SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: EdgeInsets.all(48),
                    child: CircularProgressIndicator(),
                  ),
                ),
              ),
              error: (_, __) => SliverToBoxAdapter(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(48),
                    child: Text(
                      '불러오기 실패',
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
                            final item = items[index ~/ 2];
                            return _RecentArchiveTile(
                              content: item,
                              onTap: () => context.push('/archive/${item.id}'),
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
        label: const Text('링크 아카이빙'),
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
              '아직 아카이빙한 콘텐츠가 없어요',
              style: AppTextStyles.body2
                  .copyWith(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 8),
            Text(
              '아래 버튼으로 링크를 추가해보세요',
              style: AppTextStyles.bodySmall
                  .copyWith(color: AppColors.textTertiary),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: onAddTap,
              icon: const Icon(Icons.add_link),
              label: const Text('링크 추가하기'),
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
