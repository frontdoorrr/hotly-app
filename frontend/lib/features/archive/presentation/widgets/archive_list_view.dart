import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/archived_content.dart';
import '../../domain/entities/content_type_info.dart';
import '../providers/archive_provider.dart';
import 'archive_input_sheet.dart';
import 'content_type_badge.dart';

/// 아카이브 목록 + 타입 필터 탭
class ArchiveListView extends ConsumerStatefulWidget {
  const ArchiveListView({super.key});

  @override
  ConsumerState<ArchiveListView> createState() => _ArchiveListViewState();
}

class _ArchiveListViewState extends ConsumerState<ArchiveListView> {
  final _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(archiveListProvider.notifier).load(refresh: true);
    });
    _scrollController.addListener(_onScroll);
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    final state = ref.read(archiveListProvider);
    if (_scrollController.position.pixels >=
            _scrollController.position.maxScrollExtent - 200 &&
        !state.isLoading &&
        state.hasMore) {
      ref.read(archiveListProvider.notifier).load();
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(archiveListProvider);

    return Scaffold(
      body: Column(
        children: [
          // 타입 필터 탭
          _TypeFilterBar(
            selected: state.selectedType,
            onSelect: (type) =>
                ref.read(archiveListProvider.notifier).filterByType(type),
            contentTypes: ref.watch(contentTypesProvider).valueOrNull ?? [],
            filterAllLabel: context.l10n.archiveList_filterAll,
          ),

          // 목록
          Expanded(
            child: state.isLoading && state.items.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : state.items.isEmpty
                    ? _EmptyView(
                        onAddTap: () => ArchiveInputSheet.show(context),
                      )
                    : RefreshIndicator(
                        onRefresh: () => ref
                            .read(archiveListProvider.notifier)
                            .load(refresh: true),
                        child: ListView.separated(
                          controller: _scrollController,
                          padding: const EdgeInsets.all(16),
                          itemCount:
                              state.items.length + (state.hasMore ? 1 : 0),
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            if (index == state.items.length) {
                              return const Center(
                                child: Padding(
                                  padding: EdgeInsets.all(16),
                                  child: CircularProgressIndicator(),
                                ),
                              );
                            }
                            final item = state.items[index];
                            return _ArchiveListTile(
                              content: item,
                              onTap: () => context.push('/archive/${item.id}'),
                              onDelete: () => ref
                                  .read(archiveListProvider.notifier)
                                  .delete(item.id),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => ArchiveInputSheet.show(context),
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }
}

// ------------------------------------------------------------------
// 타입 필터 탭바
// ------------------------------------------------------------------

class _TypeFilterBar extends StatelessWidget {
  final String? selected;
  final ValueChanged<String?> onSelect;
  final List<ContentTypeInfo> contentTypes;
  final String filterAllLabel;

  const _TypeFilterBar({
    required this.selected,
    required this.onSelect,
    required this.contentTypes,
    required this.filterAllLabel,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          // 전체 탭
          Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(filterAllLabel),
              selected: selected == null,
              onSelected: (_) => onSelect(null),
              selectedColor: AppColors.primary.withOpacity(0.15),
              checkmarkColor: AppColors.primary,
              labelStyle: TextStyle(
                color: selected == null ? AppColors.primary : AppColors.textSecondary,
                fontWeight: selected == null ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
          ),
          // DB에서 가져온 타입 탭
          ...contentTypes.map((type) {
            final isSelected = selected == type.key;
            final locale = Localizations.localeOf(context).languageCode;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: FilterChip(
                label: Text(type.localizedLabel(locale)),
                selected: isSelected,
                onSelected: (_) => onSelect(type.key),
                selectedColor: AppColors.primary.withOpacity(0.15),
                checkmarkColor: AppColors.primary,
                labelStyle: TextStyle(
                  color: isSelected ? AppColors.primary : AppColors.textSecondary,
                  fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}

// ------------------------------------------------------------------
// 목록 아이템
// ------------------------------------------------------------------

class _ArchiveListTile extends StatelessWidget {
  final ArchivedContent content;
  final VoidCallback onTap;
  final VoidCallback onDelete;

  const _ArchiveListTile({
    required this.content,
    required this.onTap,
    required this.onDelete,
  });

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
            // 썸네일 or 아이콘
            _thumbnail(),
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

            // 삭제 버튼
            IconButton(
              icon: const Icon(Icons.more_vert, size: 18),
              onPressed: () => _showDeleteDialog(context),
              padding: EdgeInsets.zero,
              constraints: const BoxConstraints(),
            ),
          ],
        ),
      ),
      ),
    );
  }

  Widget _thumbnail() {
    if (content.thumbnailUrl != null) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: CachedNetworkImage(
          imageUrl: content.thumbnailUrl!,
          width: 60,
          height: 60,
          fit: BoxFit.cover,
          errorWidget: (_, __, ___) => _platformFallback(),
        ),
      );
    }
    return _platformFallback();
  }

  Widget _platformFallback() {
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

  String _formatDate(DateTime dt) {
    return '${dt.year}.${dt.month.toString().padLeft(2, '0')}.${dt.day.toString().padLeft(2, '0')}';
  }

  Future<void> _showDeleteDialog(BuildContext context) async {
    final l10n = context.l10n;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(l10n.archiveList_deleteTitle),
        content: Text(l10n.archiveList_deleteBody),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(l10n.common_cancel)),
          TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child:
                  Text(l10n.archive_delete, style: const TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (confirmed == true) onDelete();
  }
}

// ------------------------------------------------------------------
// 빈 상태
// ------------------------------------------------------------------

class _EmptyView extends StatelessWidget {
  final VoidCallback onAddTap;
  const _EmptyView({required this.onAddTap});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.bookmarks_outlined, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            context.l10n.archiveList_noContent,
            style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: onAddTap,
            icon: const Icon(Icons.add),
            label: Text(context.l10n.archiveList_addLink),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ],
      ),
    );
  }
}

