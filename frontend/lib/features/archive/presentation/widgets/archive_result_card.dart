import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/archived_content.dart';
import 'content_type_badge.dart';
import 'type_cards/event_card.dart';
import 'type_cards/place_card.dart';
import 'type_cards/review_card.dart';
import 'type_cards/tips_card.dart';

/// content_type에 따라 적절한 카드를 렌더링하는 통합 결과 카드
class ArchiveResultCard extends StatelessWidget {
  final ArchivedContent content;
  final bool compact;

  const ArchiveResultCard({
    super.key,
    required this.content,
    this.compact = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 공통 헤더
        _buildHeader(context),

        const SizedBox(height: 12),

        // 요약
        if (content.summary != null && content.summary!.isNotEmpty)
          _buildSummary(),

        const SizedBox(height: 12),

        // 타입별 상세 카드
        _buildTypeCard(),

        // 키워드 (compact 아닐 때만)
        if (!compact && content.keywordsMain.isNotEmpty) ...[
          const SizedBox(height: 12),
          _buildKeywords(),
        ],

        // Todos/Insights (compact 아닐 때만)
        if (!compact && content.todos.isNotEmpty) ...[
          const SizedBox(height: 12),
          _buildTodos(),
        ],
      ],
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 썸네일
        if (content.thumbnailUrl != null)
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: CachedNetworkImage(
              imageUrl: content.thumbnailUrl!,
              width: 72,
              height: 72,
              fit: BoxFit.cover,
              errorWidget: (_, __, ___) => _platformIcon(),
            ),
          )
        else
          _platformIcon(),

        const SizedBox(width: 12),

        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // content_type 뱃지
              ContentTypeBadge(contentType: content.contentType),
              const SizedBox(height: 4),
              if (content.title != null)
                Text(
                  content.title!,
                  style: AppTextStyles.bodyLarge,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              if (content.author != null)
                Text(
                  content.author!,
                  style: AppTextStyles.bodySmall
                      .copyWith(color: AppColors.textSecondary),
                ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _platformIcon() {
    IconData icon;
    Color color;
    switch (content.platform) {
      case Platform.instagram:
        icon = Icons.camera_alt;
        color = Colors.purple;
        break;
      case Platform.naver_blog:
        icon = Icons.article;
        color = Colors.green;
        break;
      default:
        icon = Icons.play_circle;
        color = Colors.red;
    }
    return Container(
      width: 72,
      height: 72,
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: color, size: 32),
    );
  }

  Widget _buildSummary() {
    return Text(
      content.summary!,
      style: AppTextStyles.body2.copyWith(color: AppColors.textSecondary),
      maxLines: compact ? 2 : 4,
      overflow: TextOverflow.ellipsis,
    );
  }

  Widget _buildTypeCard() {
    final data = content.typeSpecificData;
    if (data == null) return const SizedBox.shrink();

    switch (content.contentType) {
      case 'place':
        return PlaceCard(data: data);
      case 'event':
        return EventCard(data: data);
      case 'tips':
        return TipsCard(data: data, compact: compact);
      case 'review':
        return ReviewCard(data: data);
      default:
        return const SizedBox.shrink();
    }
  }

  Widget _buildKeywords() {
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: content.keywordsMain
          .take(6)
          .map(
            (kw) => Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.08),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '#$kw',
                style: AppTextStyles.bodySmall
                    .copyWith(color: AppColors.primary),
              ),
            ),
          )
          .toList(),
    );
  }

  Widget _buildTodos() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('할 일', style: AppTextStyles.h4),
        const SizedBox(height: 8),
        ...content.todos.take(3).map(
              (todo) => Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.check_circle_outline,
                        size: 16, color: AppColors.primary),
                    const SizedBox(width: 6),
                    Expanded(
                        child: Text(todo, style: AppTextStyles.body2)),
                  ],
                ),
              ),
            ),
      ],
    );
  }
}

