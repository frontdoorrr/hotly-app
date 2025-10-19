import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/theme/app_theme.dart';
import '../../../../core/theme/app_text_styles.dart';

/// Horizontal scrollable tag filter chips
class TagFilterChips extends StatefulWidget {
  final List<String> availableTags;
  final List<int> tagCounts;
  final Set<String> selectedTags;
  final int totalPlacesCount;
  final ValueChanged<String> onTagSelected;
  final int initialDisplayCount; // Number of tags to show initially
  final int incrementCount; // Number of tags to add when "더보기" is clicked

  const TagFilterChips({
    super.key,
    required this.availableTags,
    required this.tagCounts,
    required this.selectedTags,
    required this.totalPlacesCount,
    required this.onTagSelected,
    this.initialDisplayCount = 5,
    this.incrementCount = 5,
  });

  @override
  State<TagFilterChips> createState() => _TagFilterChipsState();
}

class _TagFilterChipsState extends State<TagFilterChips> {
  late int _displayCount;

  @override
  void initState() {
    super.initState();
    _displayCount = widget.initialDisplayCount;
  }

  @override
  Widget build(BuildContext context) {
    // Calculate how many tags to display
    final actualDisplayCount = _displayCount.clamp(0, widget.availableTags.length);
    final displayTags = widget.availableTags.take(actualDisplayCount).toList();
    final displayCounts = widget.tagCounts.take(actualDisplayCount).toList();

    final hasMoreTags = actualDisplayCount < widget.availableTags.length;
    final remainingCount = widget.availableTags.length - actualDisplayCount;

    // Calculate total items (tags + "전체" + "더보기" button if needed)
    final itemCount = displayTags.length + 1 + (hasMoreTags ? 1 : 0);

    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: AppTheme.space4),
        itemCount: itemCount,
        separatorBuilder: (_, __) => const SizedBox(width: AppTheme.space2),
        itemBuilder: (context, index) {
          // First chip is always "전체" (All)
          if (index == 0) {
            return _buildChip(
              context,
              label: '전체',
              count: widget.totalPlacesCount,
              isSelected: widget.selectedTags.isEmpty,
              onTap: () {
                // Clear all filters
                if (widget.selectedTags.isNotEmpty) {
                  widget.onTagSelected('');
                }
              },
            );
          }

          // Last chip is "더보기" button if there are more tags
          if (hasMoreTags && index == itemCount - 1) {
            return _buildMoreButton(context, remainingCount);
          }

          // Other chips are tag filters
          final tagIndex = index - 1;
          final tag = displayTags[tagIndex];
          final count = displayCounts[tagIndex];
          final isSelected = widget.selectedTags.contains(tag);

          return _buildChip(
            context,
            label: tag,
            count: count,
            isSelected: isSelected,
            onTap: () => widget.onTagSelected(tag),
          );
        },
      ),
    );
  }

  Widget _buildMoreButton(BuildContext context, int remainingCount) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          setState(() {
            // Add incrementCount more tags, or show all if less than incrementCount remain
            _displayCount = (_displayCount + widget.incrementCount)
                .clamp(0, widget.availableTags.length);
          });
        },
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 8,
          ),
          decoration: BoxDecoration(
            color: AppColors.background,
            border: Border.all(
              color: AppColors.border,
              width: 1,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '더보기',
                style: AppTextStyles.label1.copyWith(
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                '+$remainingCount',
                style: AppTextStyles.label2.copyWith(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 2),
              Icon(
                Icons.keyboard_arrow_down,
                size: 16,
                color: AppColors.textSecondary,
              ),
            ],
          ),
        ),
      ),
    );
  }


  Widget _buildChip(
    BuildContext context, {
    required String label,
    required int count,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    final emoji = _getEmojiForTag(label);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 8,
          ),
          decoration: BoxDecoration(
            color: isSelected
                ? AppColors.primary.withOpacity(0.1)
                : AppColors.background,
            border: Border.all(
              color: isSelected ? AppColors.primary : AppColors.border,
              width: isSelected ? 2 : 1,
            ),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (emoji != null) ...[
                Text(
                  emoji,
                  style: const TextStyle(fontSize: 16),
                ),
                const SizedBox(width: 4),
              ],
              Text(
                label,
                style: AppTextStyles.label1.copyWith(
                  color: isSelected
                      ? AppColors.primary
                      : AppColors.textPrimary,
                  fontWeight: isSelected
                      ? FontWeight.w600
                      : FontWeight.normal,
                ),
              ),
              const SizedBox(width: 4),
              Text(
                '$count',
                style: AppTextStyles.label2.copyWith(
                  color: isSelected
                      ? AppColors.primary
                      : AppColors.textSecondary,
                  fontWeight: isSelected
                      ? FontWeight.w600
                      : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String? _getEmojiForTag(String tag) {
    final lowerTag = tag.toLowerCase();

    // Food & Drink
    if (lowerTag.contains('맛집') || lowerTag.contains('레스토랑')) return '🍽️';
    if (lowerTag.contains('카페')) return '☕';
    if (lowerTag.contains('디저트') || lowerTag.contains('케이크')) return '🍰';
    if (lowerTag.contains('한식')) return '🍚';
    if (lowerTag.contains('일식') || lowerTag.contains('초밥')) return '🍣';
    if (lowerTag.contains('중식')) return '🥟';
    if (lowerTag.contains('양식')) return '🍝';
    if (lowerTag.contains('브런치')) return '🥞';
    if (lowerTag.contains('술집') || lowerTag.contains('바')) return '🍺';

    // Date & Romance
    if (lowerTag.contains('데이트') || lowerTag.contains('로맨틱')) return '🌹';
    if (lowerTag.contains('기념일') || lowerTag.contains('특별한날')) return '🎉';

    // Activities
    if (lowerTag.contains('액티비티') || lowerTag.contains('활동')) return '🎯';
    if (lowerTag.contains('영화')) return '🎬';
    if (lowerTag.contains('전시') || lowerTag.contains('갤러리')) return '🎨';
    if (lowerTag.contains('공연') || lowerTag.contains('콘서트')) return '🎭';
    if (lowerTag.contains('스포츠') || lowerTag.contains('운동')) return '⚽';
    if (lowerTag.contains('산책') || lowerTag.contains('공원')) return '🌳';

    // Travel & Places
    if (lowerTag.contains('여행')) return '✈️';
    if (lowerTag.contains('해변') || lowerTag.contains('바다')) return '🏖️';
    if (lowerTag.contains('산') || lowerTag.contains('등산')) return '⛰️';
    if (lowerTag.contains('도시')) return '🏙️';

    // Shopping & Services
    if (lowerTag.contains('쇼핑')) return '🛍️';
    if (lowerTag.contains('뷰티') || lowerTag.contains('미용')) return '💄';

    // Atmosphere
    if (lowerTag.contains('힙한') || lowerTag.contains('트렌디')) return '✨';
    if (lowerTag.contains('조용한') || lowerTag.contains('차분')) return '🤫';
    if (lowerTag.contains('북적') || lowerTag.contains('활기')) return '🎊';
    if (lowerTag.contains('감성')) return '🌙';
    if (lowerTag.contains('뷰맛집') || lowerTag.contains('전망')) return '🌆';

    // Special features
    if (lowerTag.contains('반려동물') || lowerTag.contains('펫')) return '🐾';
    if (lowerTag.contains('주차')) return '🅿️';
    if (lowerTag.contains('와이파이') || lowerTag.contains('wifi')) return '📶';
    if (lowerTag.contains('24시간')) return '🌙';

    return null;
  }
}
