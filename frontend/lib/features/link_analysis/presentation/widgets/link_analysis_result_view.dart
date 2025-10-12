import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/link_analysis_result.dart';
import '../providers/link_analysis_provider.dart';

/// Widget to display link analysis results
class LinkAnalysisResultView extends ConsumerWidget {
  final ScrollController scrollController;

  const LinkAnalysisResultView({
    super.key,
    required this.scrollController,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(linkAnalysisProvider);
    final result = state.result;

    if (result == null) {
      return const SizedBox.shrink();
    }

    return SingleChildScrollView(
      controller: scrollController,
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status indicator
          _buildStatusCard(result, state.isPolling),

          const SizedBox(height: 20),

          // Result content
          if (result.status == AnalysisStatus.completed)
            _buildResultContent(context, ref, result),

          // Error message
          if (result.status == AnalysisStatus.failed && result.error != null)
            _buildErrorCard(result.error!),
        ],
      ),
    );
  }

  Widget _buildStatusCard(LinkAnalysisResult result, bool isPolling) {
    IconData icon;
    Color color;
    String statusText;

    switch (result.status) {
      case AnalysisStatus.pending:
      case AnalysisStatus.inProgress:
        icon = Icons.hourglass_empty;
        color = AppColors.warning;
        statusText = '분석 중...';
        break;
      case AnalysisStatus.completed:
        icon = Icons.check_circle;
        color = AppColors.success;
        statusText = '분석 완료';
        break;
      case AnalysisStatus.failed:
        icon = Icons.error;
        color = AppColors.error;
        statusText = '분석 실패';
        break;
      case AnalysisStatus.cancelled:
        icon = Icons.cancel;
        color = Colors.grey;
        statusText = '분석 취소됨';
        break;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      statusText,
                      style: AppTextStyles.bodyLarge.copyWith(color: color),
                    ),
                    if (result.cached)
                      Text(
                        '캐시된 결과 (${result.processingTime.toStringAsFixed(2)}s)',
                        style: AppTextStyles.bodySmall.copyWith(
                          color: AppColors.textSecondary,
                        ),
                      ),
                  ],
                ),
              ),
              if (isPolling)
                const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
            ],
          ),
          if (result.progress != null && result.progress! > 0)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  LinearProgressIndicator(
                    value: result.progress,
                    backgroundColor: Colors.grey[200],
                    valueColor: AlwaysStoppedAnimation<Color>(color),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    '${(result.progress! * 100).toInt()}%',
                    style: AppTextStyles.bodySmall.copyWith(
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildResultContent(BuildContext context, WidgetRef ref, LinkAnalysisResult result) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Confidence score
        if (result.confidence > 0)
          _buildConfidenceCard(result.confidence),

        const SizedBox(height: 20),

        // Place information
        if (result.placeInfo != null) ...[
          Text('장소 정보', style: AppTextStyles.h3),
          const SizedBox(height: 12),
          _buildPlaceInfoCard(result.placeInfo!),
        ],

        const SizedBox(height: 20),

        // Content metadata
        if (result.contentMetadata != null) ...[
          Text('추출된 콘텐츠', style: AppTextStyles.h3),
          const SizedBox(height: 12),
          _buildContentMetadataCard(result.contentMetadata!),
        ],

        const SizedBox(height: 20),

        // Action buttons
        _buildActionButtons(context, ref, result),
      ],
    );
  }

  Widget _buildConfidenceCard(double confidence) {
    final percentage = (confidence * 100).toInt();
    Color color;

    if (confidence >= 0.8) {
      color = AppColors.success;
    } else if (confidence >= 0.5) {
      color = AppColors.warning;
    } else {
      color = AppColors.error;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(Icons.verified, color: color),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '신뢰도',
                  style: AppTextStyles.bodySmall.copyWith(
                    color: AppColors.textSecondary,
                  ),
                ),
                Text(
                  '$percentage%',
                  style: AppTextStyles.h3.copyWith(color: color),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPlaceInfoCard(PlaceInfo placeInfo) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              placeInfo.name,
              style: AppTextStyles.h3,
            ),
            if (placeInfo.category != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  placeInfo.category!,
                  style: AppTextStyles.bodySmall.copyWith(
                    color: AppColors.primary,
                  ),
                ),
              ),
            ],
            if (placeInfo.address != null) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.location_on,
                      size: 16, color: AppColors.textSecondary),
                  const SizedBox(width: 4),
                  Expanded(
                    child: Text(
                      placeInfo.address!,
                      style: AppTextStyles.body2.copyWith(
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ),
                ],
              ),
            ],
            if (placeInfo.description != null) ...[
              const SizedBox(height: 12),
              Text(
                placeInfo.description!,
                style: AppTextStyles.body2,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (placeInfo.tags != null && placeInfo.tags!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: placeInfo.tags!
                    .take(5)
                    .map(
                      (tag) => Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.grey[100],
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '#$tag',
                          style: AppTextStyles.bodySmall,
                        ),
                      ),
                    )
                    .toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildContentMetadataCard(ContentMetadata metadata) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (metadata.title != null) ...[
              Text(
                metadata.title!,
                style: AppTextStyles.bodyLarge,
              ),
              const SizedBox(height: 8),
            ],
            if (metadata.description != null) ...[
              Text(
                metadata.description!,
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.textSecondary,
                ),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 12),
            ],
            if (metadata.images.isNotEmpty) ...[
              SizedBox(
                height: 100,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: metadata.images.length,
                  itemBuilder: (context, index) {
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: CachedNetworkImage(
                          imageUrl: metadata.images[index],
                          width: 100,
                          height: 100,
                          fit: BoxFit.cover,
                          placeholder: (context, url) => Container(
                            color: Colors.grey[200],
                            child: const Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          errorWidget: (context, url, error) => Container(
                            color: Colors.grey[200],
                            child: const Icon(Icons.error),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context, WidgetRef ref, LinkAnalysisResult result) {
    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: () async {
              // Show loading indicator using root navigator
              showDialog(
                context: context,
                barrierDismissible: false,
                useRootNavigator: true,
                builder: (dialogContext) => const Center(
                  child: CircularProgressIndicator(),
                ),
              );

              // Save place
              final success = await ref.read(linkAnalysisProvider.notifier).savePlace();

              // Hide loading dialog using root navigator
              if (context.mounted) {
                Navigator.of(context, rootNavigator: true).pop();
              }

              if (success) {
                // Show success message and close bottom sheet
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: const Text('장소가 저장되었습니다'),
                      backgroundColor: AppColors.success,
                      duration: const Duration(seconds: 2),
                    ),
                  );
                  // Close bottom sheet
                  Navigator.of(context).pop();
                }
              } else {
                // Show error message
                if (context.mounted) {
                  final error = ref.read(linkAnalysisProvider).error ?? '저장 실패';
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(error),
                      backgroundColor: AppColors.error,
                      duration: const Duration(seconds: 3),
                    ),
                  );
                }
              }
            },
            icon: const Icon(Icons.bookmark_border),
            label: const Text('장소 저장'),
            style: OutlinedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              // TODO: Navigate to place detail
              Navigator.of(context).pop();
            },
            icon: const Icon(Icons.arrow_forward),
            label: const Text('상세 보기'),
            style: ElevatedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 12),
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildErrorCard(String error) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.red[50],
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.red[200]!),
      ),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: Colors.red[700]),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              error,
              style: AppTextStyles.body2.copyWith(
                color: Colors.red[700],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
