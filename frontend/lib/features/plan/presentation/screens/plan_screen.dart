import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:hotly_app/core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../../archive/domain/entities/archived_content.dart';
import '../providers/plan_provider.dart';

class PlanScreen extends ConsumerWidget {
  const PlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(context.l10n.nav_plan),
          automaticallyImplyLeading: false,
          bottom: TabBar(
            tabs: [
              Tab(text: context.l10n.plan_tabEvents),
              Tab(text: context.l10n.plan_tabPlaces),
            ],
          ),
        ),
        body: TabBarView(
          children: [
            _EventTab(ref: ref),
            _PlaceTab(ref: ref),
          ],
        ),
      ),
    );
  }
}

// ------------------------------------------------------------------
// 이벤트 탭
// ------------------------------------------------------------------

class _EventTab extends ConsumerWidget {
  const _EventTab({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(planEventProvider);

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, __) => Center(child: Text(context.l10n.plan_loadFailed)),
      data: (items) => items.isEmpty
          ? _EmptyPlan(
              icon: Icons.event_outlined,
              message: context.l10n.plan_noEvents,
            )
          : RefreshIndicator(
              onRefresh: () => ref.refresh(planEventProvider.future),
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, index) => _EventTile(
                  content: items[index],
                  onTap: () => context.push('/archive/${items[index].id}'),
                ),
              ),
            ),
    );
  }
}

// ------------------------------------------------------------------
// 가볼 곳 탭
// ------------------------------------------------------------------

class _PlaceTab extends ConsumerWidget {
  const _PlaceTab({required this.ref});
  final WidgetRef ref;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(planPlaceProvider);

    return async.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (_, __) => Center(child: Text(context.l10n.plan_loadFailed)),
      data: (items) => items.isEmpty
          ? _EmptyPlan(
              icon: Icons.place_outlined,
              message: context.l10n.plan_noPlaces,
            )
          : RefreshIndicator(
              onRefresh: () => ref.refresh(planPlaceProvider.future),
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemBuilder: (context, index) => _PlanTile(
                  content: items[index],
                  onTap: () => context.push('/archive/${items[index].id}'),
                ),
              ),
            ),
    );
  }
}

// ------------------------------------------------------------------
// 이벤트 타일 (D-day 뱃지 포함)
// ------------------------------------------------------------------

class _EventTile extends StatelessWidget {
  final ArchivedContent content;
  final VoidCallback onTap;

  const _EventTile({required this.content, required this.onTap});

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
                    const SizedBox(height: 8),
                    _EventDateRow(content: content),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _DDayBadge(content: content),
            ],
          ),
        ),
      ),
    );
  }
}

class _EventDateRow extends StatelessWidget {
  final ArchivedContent content;
  const _EventDateRow({required this.content});

  @override
  Widget build(BuildContext context) {
    final startDate = content.typeSpecificData?['start_date'] as String?;
    final endDate = content.typeSpecificData?['end_date'] as String?;
    final time = content.typeSpecificData?['time'] as String?;

    if (startDate == null && time == null) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (startDate != null)
          Row(
            children: [
              const Icon(Icons.calendar_today, size: 12, color: Colors.grey),
              const SizedBox(width: 4),
              Text(
                endDate != null ? '$startDate ~ $endDate' : startDate,
                style: AppTextStyles.bodySmall
                    .copyWith(color: AppColors.textTertiary),
              ),
            ],
          ),
        if (time != null) ...[
          const SizedBox(height: 2),
          Row(
            children: [
              const Icon(Icons.access_time, size: 12, color: Colors.grey),
              const SizedBox(width: 4),
              Text(
                time,
                style: AppTextStyles.bodySmall
                    .copyWith(color: AppColors.textTertiary),
              ),
            ],
          ),
        ],
      ],
    );
  }
}

class _DDayBadge extends StatelessWidget {
  final ArchivedContent content;
  const _DDayBadge({required this.content});

  @override
  Widget build(BuildContext context) {
    final startDate = content.typeSpecificData?['start_date'] as String?;
    if (startDate == null) return const SizedBox.shrink();

    String label;
    Color color;

    try {
      final diff = DateTime.parse(startDate)
          .difference(DateTime.now())
          .inDays;
      if (diff > 0) {
        label = 'D-$diff';
        color = Colors.deepPurple;
      } else if (diff == 0) {
        label = context.l10n.plan_today;
        color = Colors.red;
      } else {
        label = context.l10n.plan_ended;
        color = Colors.grey;
      }
    } catch (_) {
      return const SizedBox.shrink();
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

// ------------------------------------------------------------------
// 장소 타일 (기본)
// ------------------------------------------------------------------

class _PlanTile extends StatelessWidget {
  final ArchivedContent content;
  final VoidCallback onTap;

  const _PlanTile({required this.content, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final address =
        content.typeSpecificData?['address'] as String?;

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
                    if (content.title != null)
                      Text(
                        content.title!,
                        style: AppTextStyles.bodyLarge,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    if (address != null) ...[
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          const Icon(Icons.place, size: 12,
                              color: Colors.orange),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              address,
                              style: AppTextStyles.bodySmall
                                  .copyWith(color: AppColors.textSecondary),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ],
                      ),
                    ] else if (content.summary != null) ...[
                      const SizedBox(height: 4),
                      Text(
                        content.summary!,
                        style: AppTextStyles.body2
                            .copyWith(color: AppColors.textSecondary),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
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
}

// ------------------------------------------------------------------
// 공통 위젯
// ------------------------------------------------------------------

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

class _EmptyPlan extends StatelessWidget {
  final IconData icon;
  final String message;

  const _EmptyPlan({
    required this.icon,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text(
            message,
            style:
                AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }
}
