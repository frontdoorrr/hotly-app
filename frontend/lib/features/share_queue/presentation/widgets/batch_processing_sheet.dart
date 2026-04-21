import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/share_queue_item.dart';
import '../providers/share_queue_provider.dart';

/// 일괄 분석 진행 바텀시트
///
/// 분석 진행 상황을 실시간으로 표시하고,
/// 완료 시 결과 화면으로 이동합니다.
class BatchProcessingSheet extends ConsumerStatefulWidget {
  const BatchProcessingSheet({super.key});

  @override
  ConsumerState<BatchProcessingSheet> createState() =>
      _BatchProcessingSheetState();
}

class _BatchProcessingSheetState extends ConsumerState<BatchProcessingSheet> {
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(shareQueueProvider);
    final totalCount = state.items
        .where(
          (item) =>
              item.status != ShareQueueStatus.saved &&
              item.status != ShareQueueStatus.ignored,
        )
        .length;

    return Container(
      height: MediaQuery.of(context).size.height * 0.75,
      decoration: const BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        children: [
          // 핸들 바
          Container(
            margin: const EdgeInsets.only(top: 12, bottom: 8),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.gray200,
              borderRadius: BorderRadius.circular(2),
            ),
          ),

          // 헤더
          Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                _buildHeader(state, totalCount),
                const SizedBox(height: 16),
                _buildProgressBar(state),
              ],
            ),
          ),

          // 항목 목록 (saved/ignored 제외)
          Expanded(
            child: Builder(
              builder: (context) {
                final displayItems = state.items
                    .where((item) =>
                        item.status != ShareQueueStatus.saved &&
                        item.status != ShareQueueStatus.ignored)
                    .toList();
                return displayItems.isEmpty
                    ? _buildEmptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.symmetric(horizontal: 20),
                        itemCount: displayItems.length,
                        itemBuilder: (context, index) {
                          return ShareQueueItemTile(item: displayItems[index]);
                        },
                      );
              },
            ),
          ),

          // 하단 버튼
          _buildBottomActions(context, state),
        ],
      ),
    );
  }

  Widget _buildHeader(ShareQueueState state, int totalCount) {
    final String title;
    final IconData icon;
    final Color iconColor;

    if (state.isProcessing) {
      title = '📦 링크 분석 중 (${state.processingIndex + 1}/$totalCount)';
      icon = Icons.sync;
      iconColor = AppColors.info;
    } else if (state.completedCount == totalCount && totalCount > 0) {
      title = '✨ ${state.completedCount}개 장소 분석 완료';
      icon = Icons.check_circle;
      iconColor = AppColors.success;
    } else if (state.pendingCount > 0) {
      title = '🔗 ${state.pendingCount}개 링크 대기 중';
      icon = Icons.schedule;
      iconColor = AppColors.warning;
    } else {
      title = '📋 분석 결과';
      icon = Icons.list_alt;
      iconColor = AppColors.gray500;
    }

    return Row(
      children: [
        Icon(icon, color: iconColor, size: 28),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            title,
            style: AppTextStyles.h3.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
        if (state.failedCount > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.error.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              '${state.failedCount}개 실패',
              style: AppTextStyles.bodySmall.copyWith(
                color: AppColors.error,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildProgressBar(ShareQueueState state) {
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: state.isProcessing ? state.progress : 1.0,
            backgroundColor: AppColors.gray100,
            valueColor: AlwaysStoppedAnimation<Color>(
              state.isProcessing ? AppColors.primary : AppColors.success,
            ),
            minHeight: 8,
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              state.isProcessing
                  ? '${(state.progress * 100).toInt()}% 완료'
                  : '분석 완료',
              style: AppTextStyles.body2.copyWith(
                color: AppColors.textSecondary,
              ),
            ),
            if (state.isProcessing)
              Text(
                '약 ${_estimateRemainingTime(state)}',
                style: AppTextStyles.bodySmall.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
          ],
        ),
      ],
    );
  }

  String _estimateRemainingTime(ShareQueueState state) {
    final remaining = state.processableItems.length - state.processingIndex;
    final seconds = remaining * 25; // 평균 25초 예상
    if (seconds < 60) return '${seconds}초 남음';
    return '${(seconds / 60).ceil()}분 남음';
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.inbox_outlined,
            size: 64,
            color: AppColors.gray200,
          ),
          const SizedBox(height: 16),
          Text(
            '공유된 링크가 없습니다',
            style: AppTextStyles.labelLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Instagram, 네이버 블로그, YouTube에서\n링크를 공유해보세요',
            style: AppTextStyles.body2.copyWith(
              color: AppColors.textSecondary,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActions(BuildContext context, ShareQueueState state) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        20,
        16,
        20,
        16 + MediaQuery.of(context).padding.bottom,
      ),
      decoration: BoxDecoration(
        color: AppColors.white,
        boxShadow: [
          BoxShadow(
            color: AppColors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Row(
        children: [
          // 백그라운드 버튼
          Expanded(
            child: OutlinedButton(
              onPressed: () => Navigator.pop(context),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                side: const BorderSide(color: AppColors.gray200),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                state.isProcessing ? '백그라운드로' : '닫기',
                style: AppTextStyles.button.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
            ),
          ),
          const SizedBox(width: 12),
          // 메인 액션 버튼
          Expanded(
            flex: 2,
            child: ElevatedButton(
              onPressed: state.isProcessing
                  ? () {
                      ref.read(shareQueueProvider.notifier).cancelProcessing();
                    }
                  : state.completedCount > 0
                      ? () {
                          Navigator.pop(context);
                          context.push('/share-queue/results');
                        }
                      : state.failedCount > 0
                          ? () {
                              ref.read(shareQueueProvider.notifier).retryFailed();
                            }
                          : null,
              style: ElevatedButton.styleFrom(
                backgroundColor: state.isProcessing
                    ? AppColors.error
                    : AppColors.primary,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                state.isProcessing
                    ? '분석 취소'
                    : state.completedCount > 0
                        ? '결과 확인하기'
                        : state.failedCount > 0
                            ? '재시도'
                            : '완료',
                style: AppTextStyles.button.copyWith(
                  color: AppColors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

/// 큐 항목 타일 위젯
class ShareQueueItemTile extends StatelessWidget {
  final ShareQueueItem item;

  const ShareQueueItemTile({
    super.key,
    required this.item,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _getBackgroundColor(),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: _getBorderColor(),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          _buildStatusIcon(),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.result?.placeName ?? item.title ?? _getDisplayUrl(),
                  style: AppTextStyles.labelMedium.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                _buildSubtitle(),
              ],
            ),
          ),
          if (item.status == ShareQueueStatus.completed && item.result != null)
            _buildConfidenceBadge(),
        ],
      ),
    );
  }

  Color _getBackgroundColor() {
    switch (item.status) {
      case ShareQueueStatus.completed:
        return AppColors.success.withOpacity(0.05);
      case ShareQueueStatus.failed:
        return AppColors.error.withOpacity(0.05);
      case ShareQueueStatus.analyzing:
        return AppColors.info.withOpacity(0.05);
      default:
        return AppColors.gray50;
    }
  }

  Color _getBorderColor() {
    switch (item.status) {
      case ShareQueueStatus.completed:
        return AppColors.success.withOpacity(0.2);
      case ShareQueueStatus.failed:
        return AppColors.error.withOpacity(0.2);
      case ShareQueueStatus.analyzing:
        return AppColors.info.withOpacity(0.2);
      default:
        return AppColors.gray100;
    }
  }

  Widget _buildStatusIcon() {
    switch (item.status) {
      case ShareQueueStatus.pending:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.gray100,
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.schedule,
            color: AppColors.gray500,
            size: 18,
          ),
        );
      case ShareQueueStatus.analyzing:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.info.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Center(
            child: SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(AppColors.info),
              ),
            ),
          ),
        );
      case ShareQueueStatus.completed:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.success.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.check_circle,
            color: AppColors.success,
            size: 18,
          ),
        );
      case ShareQueueStatus.failed:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.error.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.error,
            color: AppColors.error,
            size: 18,
          ),
        );
      case ShareQueueStatus.saved:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.primary.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.bookmark,
            color: AppColors.primary,
            size: 18,
          ),
        );
      case ShareQueueStatus.ignored:
        return Container(
          width: 32,
          height: 32,
          decoration: BoxDecoration(
            color: AppColors.gray100,
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Icon(
            Icons.visibility_off,
            color: AppColors.gray500,
            size: 18,
          ),
        );
    }
  }

  Widget _buildSubtitle() {
    String text;
    Color color;

    switch (item.status) {
      case ShareQueueStatus.pending:
        text = '대기 중';
        color = AppColors.textSecondary;
        break;
      case ShareQueueStatus.analyzing:
        text = '분석 중...';
        color = AppColors.info;
        break;
      case ShareQueueStatus.completed:
        text = item.result?.category ?? '분석 완료';
        color = AppColors.success;
        break;
      case ShareQueueStatus.failed:
        text = item.errorMessage ?? '분석 실패';
        color = AppColors.error;
        break;
      case ShareQueueStatus.saved:
        text = '저장됨';
        color = AppColors.primary;
        break;
      case ShareQueueStatus.ignored:
        text = '무시됨';
        color = AppColors.textSecondary;
        break;
    }

    return Text(
      text,
      style: AppTextStyles.bodySmall.copyWith(
        color: color,
      ),
      maxLines: 1,
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildConfidenceBadge() {
    final confidence = item.result!.confidence;
    final color = _getConfidenceColor(confidence);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '${(confidence * 100).toInt()}%',
        style: AppTextStyles.bodySmall.copyWith(
          color: color,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return AppColors.success;
    if (confidence >= 0.7) return AppColors.warning;
    return AppColors.error;
  }

  String _getDisplayUrl() {
    try {
      final uri = Uri.parse(item.url);
      return uri.host;
    } catch (_) {
      return item.url;
    }
  }
}
