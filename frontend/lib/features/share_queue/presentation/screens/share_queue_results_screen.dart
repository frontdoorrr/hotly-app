import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/share_queue_item.dart';
import '../providers/share_queue_provider.dart';

/// 분석 결과 확인 및 저장 화면
///
/// 분석된 장소 정보를 확인하고, 개별/일괄 저장할 수 있습니다.
class ShareQueueResultsScreen extends ConsumerStatefulWidget {
  const ShareQueueResultsScreen({super.key});

  @override
  ConsumerState<ShareQueueResultsScreen> createState() =>
      _ShareQueueResultsScreenState();
}

class _ShareQueueResultsScreenState
    extends ConsumerState<ShareQueueResultsScreen> {
  bool _showOnlyHighConfidence = false;
  final Set<String> _selectedIds = {};

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(shareQueueProvider);
    final completedItems = state.items
        .where((item) => item.status == ShareQueueStatus.completed)
        .toList();

    final displayItems = _showOnlyHighConfidence
        ? completedItems
            .where((item) => item.result?.confidence != null &&
                   item.result!.confidence >= 0.7)
            .toList()
        : completedItems;

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        backgroundColor: AppColors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close, color: AppColors.textPrimary),
          onPressed: () => context.pop(),
        ),
        title: Text(
          '분석 결과',
          style: AppTextStyles.h3.copyWith(
            color: AppColors.textPrimary,
          ),
        ),
        centerTitle: true,
        actions: [
          if (_selectedIds.isNotEmpty)
            TextButton(
              onPressed: () => setState(() => _selectedIds.clear()),
              child: Text(
                '선택 해제',
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.primary,
                ),
              ),
            ),
        ],
      ),
      body: Column(
        children: [
          // 헤더 및 필터
          _buildHeader(completedItems),

          // 결과 목록
          Expanded(
            child: displayItems.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: displayItems.length,
                    itemBuilder: (context, index) {
                      final item = displayItems[index];
                      return _buildResultCard(item);
                    },
                  ),
          ),

          // 하단 액션 바
          if (displayItems.isNotEmpty) _buildBottomActionBar(displayItems),
        ],
      ),
    );
  }

  Widget _buildHeader(List<ShareQueueItem> items) {
    final highConfidenceCount =
        items.where((item) => (item.result?.confidence ?? 0) >= 0.7).length;

    return Container(
      padding: const EdgeInsets.all(16),
      color: AppColors.white,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 요약 정보
          Row(
            children: [
              _buildSummaryChip(
                icon: Icons.check_circle,
                label: '${items.length}개 분석 완료',
                color: AppColors.success,
              ),
              const SizedBox(width: 8),
              _buildSummaryChip(
                icon: Icons.star,
                label: '신뢰도 높음 $highConfidenceCount개',
                color: AppColors.primary,
              ),
            ],
          ),
          const SizedBox(height: 12),

          // 필터 토글
          Row(
            children: [
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _showOnlyHighConfidence = false),
                  borderRadius: BorderRadius.circular(8),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: !_showOnlyHighConfidence
                          ? AppColors.primary
                          : AppColors.gray100,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Text(
                        '모두 보기',
                        style: AppTextStyles.button.copyWith(
                          color: !_showOnlyHighConfidence
                              ? AppColors.white
                              : AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: InkWell(
                  onTap: () => setState(() => _showOnlyHighConfidence = true),
                  borderRadius: BorderRadius.circular(8),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: _showOnlyHighConfidence
                          ? AppColors.primary
                          : AppColors.gray100,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Center(
                      child: Text(
                        '신뢰도 높은 것만',
                        style: AppTextStyles.button.copyWith(
                          color: _showOnlyHighConfidence
                              ? AppColors.white
                              : AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryChip({
    required IconData icon,
    required String label,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: AppTextStyles.bodySmall.copyWith(
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildResultCard(ShareQueueItem item) {
    final result = item.result;
    if (result == null) return const SizedBox.shrink();

    final isSelected = _selectedIds.contains(item.id);
    final confidence = result.confidence;
    final confidenceColor = _getConfidenceColor(confidence);

    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: AppColors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isSelected ? AppColors.primary : AppColors.gray100,
          width: isSelected ? 2 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: AppColors.black.withOpacity(0.04),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 이미지 (있는 경우)
          if (result.imageUrl != null)
            ClipRRect(
              borderRadius:
                  const BorderRadius.vertical(top: Radius.circular(16)),
              child: AspectRatio(
                aspectRatio: 16 / 9,
                child: CachedNetworkImage(
                  imageUrl: result.imageUrl!,
                  fit: BoxFit.cover,
                  placeholder: (context, url) => Container(
                    color: AppColors.gray100,
                    child: const Center(
                      child: CircularProgressIndicator(strokeWidth: 2),
                    ),
                  ),
                  errorWidget: (context, url, error) => Container(
                    color: AppColors.gray100,
                    child: const Icon(
                      Icons.image_not_supported,
                      color: AppColors.gray500,
                    ),
                  ),
                ),
              ),
            ),

          // 콘텐츠
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // 장소명 및 신뢰도
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            result.placeName,
                            style: AppTextStyles.labelLarge.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: AppColors.gray100,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  result.category,
                                  style: AppTextStyles.bodySmall.copyWith(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ),
                              const SizedBox(width: 8),
                              if (result.address != null)
                                Expanded(
                                  child: Text(
                                    result.address!,
                                    style: AppTextStyles.bodySmall.copyWith(
                                      color: AppColors.textSecondary,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    // 신뢰도 배지
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 6,
                      ),
                      decoration: BoxDecoration(
                        color: confidenceColor.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        children: [
                          Icon(
                            Icons.star,
                            size: 16,
                            color: confidenceColor,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${(confidence * 100).toInt()}%',
                            style: AppTextStyles.bodySmall.copyWith(
                              color: confidenceColor,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),

                // 태그
                if (result.tags.isNotEmpty)
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: result.tags.take(5).map((tag) {
                      return Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.primary.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '#$tag',
                          style: AppTextStyles.bodySmall.copyWith(
                            color: AppColors.primary,
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                const SizedBox(height: 16),

                // 액션 버튼
                Row(
                  children: [
                    // 선택 체크박스
                    InkWell(
                      onTap: () {
                        setState(() {
                          if (isSelected) {
                            _selectedIds.remove(item.id);
                          } else {
                            _selectedIds.add(item.id);
                          }
                        });
                      },
                      child: Container(
                        width: 24,
                        height: 24,
                        decoration: BoxDecoration(
                          color: isSelected
                              ? AppColors.primary
                              : AppColors.white,
                          border: Border.all(
                            color: isSelected
                                ? AppColors.primary
                                : AppColors.gray200,
                            width: 2,
                          ),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: isSelected
                            ? const Icon(
                                Icons.check,
                                size: 16,
                                color: AppColors.white,
                              )
                            : null,
                      ),
                    ),
                    const Spacer(),
                    // 무시 버튼
                    TextButton(
                      onPressed: () {
                        ref.read(shareQueueProvider.notifier).ignoreItem(item.id);
                      },
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.textSecondary,
                      ),
                      child: const Text('무시'),
                    ),
                    // 편집 버튼
                    TextButton(
                      onPressed: () {
                        // TODO: 편집 화면으로 이동
                      },
                      style: TextButton.styleFrom(
                        foregroundColor: AppColors.info,
                      ),
                      child: const Text('편집'),
                    ),
                    // 저장 버튼
                    ElevatedButton(
                      onPressed: () async {
                        final success = await ref
                            .read(shareQueueProvider.notifier)
                            .saveItem(item.id);
                        if (success && mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('${result.placeName} 저장됨'),
                              backgroundColor: AppColors.success,
                            ),
                          );
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8),
                        ),
                      ),
                      child: Text(
                        '저장',
                        style: AppTextStyles.button.copyWith(
                          color: AppColors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
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
            _showOnlyHighConfidence
                ? '신뢰도 높은 결과가 없습니다'
                : '분석된 결과가 없습니다',
            style: AppTextStyles.labelLarge.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActionBar(List<ShareQueueItem> displayItems) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        16,
        16,
        16,
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
          // 전체 선택/해제
          InkWell(
            onTap: () {
              setState(() {
                if (_selectedIds.length == displayItems.length) {
                  _selectedIds.clear();
                } else {
                  _selectedIds.clear();
                  _selectedIds.addAll(displayItems.map((e) => e.id));
                }
              });
            },
            child: Row(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: _selectedIds.length == displayItems.length
                        ? AppColors.primary
                        : AppColors.white,
                    border: Border.all(
                      color: _selectedIds.length == displayItems.length
                          ? AppColors.primary
                          : AppColors.gray200,
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: _selectedIds.length == displayItems.length
                      ? const Icon(
                          Icons.check,
                          size: 16,
                          color: AppColors.white,
                        )
                      : null,
                ),
                const SizedBox(width: 8),
                Text(
                  '전체 선택',
                  style: AppTextStyles.body2.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ),
          const Spacer(),
          // 선택 저장 버튼
          ElevatedButton(
            onPressed: _selectedIds.isEmpty
                ? null
                : () async {
                    final count = await ref
                        .read(shareQueueProvider.notifier)
                        .saveSelectedItems(_selectedIds.toList());
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('$count개 장소 저장됨'),
                          backgroundColor: AppColors.success,
                        ),
                      );
                      setState(() => _selectedIds.clear());
                    }
                  },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              disabledBackgroundColor: AppColors.gray200,
              padding: const EdgeInsets.symmetric(
                horizontal: 24,
                vertical: 12,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            child: Text(
              _selectedIds.isEmpty
                  ? '저장'
                  : '${_selectedIds.length}개 저장하기',
              style: AppTextStyles.button.copyWith(
                color: AppColors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return AppColors.success;
    if (confidence >= 0.7) return AppColors.warning;
    return AppColors.error;
  }
}
