import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/share_queue_item.dart';
import '../providers/share_queue_provider.dart';
import 'batch_processing_sheet.dart';

/// 홈 화면에 표시되는 공유 큐 배지 위젯
///
/// 대기 중인 링크가 있을 때 표시되며, 탭하면 분석 진행 바텀시트가 열립니다.
class ShareQueueBadge extends ConsumerWidget {
  const ShareQueueBadge({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueState = ref.watch(shareQueueProvider);
    final pendingCount = queueState.pendingCount;

    // 대기 중인 항목이 없으면 표시하지 않음
    if (pendingCount == 0 && !queueState.isProcessing) {
      return const SizedBox.shrink();
    }

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _showProcessingSheet(context, ref),
          borderRadius: BorderRadius.circular(12),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: queueState.isProcessing
                ? _buildProcessingContent(queueState)
                : _buildPendingContent(pendingCount, ref),
          ),
        ),
      ),
    );
  }

  Widget _buildPendingContent(int pendingCount, WidgetRef ref) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.white.withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.link,
            color: AppColors.white,
            size: 24,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '$pendingCount개 링크 분석 대기 중',
                style: AppTextStyles.labelLarge.copyWith(
                  color: AppColors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                '탭하여 분석을 시작하세요',
                style: AppTextStyles.bodySmall.copyWith(
                  color: AppColors.white.withOpacity(0.8),
                ),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.white,
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            '분석 시작',
            style: AppTextStyles.button.copyWith(
              color: AppColors.primary,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildProcessingContent(ShareQueueState state) {
    final totalToProcess = state.items
        .where(
          (item) =>
              item.status != ShareQueueStatus.saved &&
              item.status != ShareQueueStatus.ignored,
        )
        .length;

    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.white.withOpacity(0.2),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(AppColors.white),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '분석 중... (${state.processingIndex + 1}/$totalToProcess)',
                style: AppTextStyles.labelLarge.copyWith(
                  color: AppColors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(2),
                child: LinearProgressIndicator(
                  value: state.progress,
                  backgroundColor: AppColors.white.withOpacity(0.3),
                  valueColor: const AlwaysStoppedAnimation<Color>(AppColors.white),
                  minHeight: 4,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(width: 12),
        Text(
          '${(state.progress * 100).toInt()}%',
          style: AppTextStyles.labelLarge.copyWith(
            color: AppColors.white,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  void _showProcessingSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => const BatchProcessingSheet(),
    );

    // 분석 시작
    final notifier = ref.read(shareQueueProvider.notifier);
    if (!ref.read(shareQueueProvider).isProcessing) {
      notifier.processBatch();
    }
  }
}

/// 홈 화면용 소형 배지 (네비게이션 바 등에 표시)
class ShareQueueMiniBadge extends ConsumerWidget {
  final Widget child;

  const ShareQueueMiniBadge({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pendingCount = ref.watch(pendingQueueCountProvider);

    if (pendingCount == 0) {
      return child;
    }

    return Stack(
      clipBehavior: Clip.none,
      children: [
        child,
        Positioned(
          right: -4,
          top: -4,
          child: Container(
            padding: const EdgeInsets.all(4),
            decoration: const BoxDecoration(
              color: AppColors.primary,
              shape: BoxShape.circle,
            ),
            constraints: const BoxConstraints(
              minWidth: 18,
              minHeight: 18,
            ),
            child: Center(
              child: Text(
                pendingCount > 9 ? '9+' : pendingCount.toString(),
                style: AppTextStyles.bodySmall.copyWith(
                  color: AppColors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
