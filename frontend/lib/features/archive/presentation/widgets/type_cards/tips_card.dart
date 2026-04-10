import 'package:flutter/material.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/theme/app_text_styles.dart';
import '_shared.dart';

class TipsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final bool compact;
  const TipsCard({super.key, required this.data, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final tips = (data['tip_list'] as List?)?.cast<Map<String, dynamic>>();
    final materials = (data['materials'] as List?)?.cast<String>();
    final cautions = (data['cautions'] as List?)?.cast<String>();
    final difficulty = data['difficulty'] as String?;

    return TypeInfoCard(
      children: [
        // 난이도 + 소요시간
        Row(
          children: [
            if (difficulty != null)
              _DifficultyBadge(difficulty: difficulty),
            if (difficulty != null && data['estimated_time'] != null)
              const SizedBox(width: 8),
            if (data['estimated_time'] != null)
              _InfoChip(
                icon: Icons.timer_outlined,
                text: data['estimated_time'],
              ),
            if (data['sub_field'] != null) ...[
              const SizedBox(width: 8),
              _InfoChip(icon: Icons.category_outlined, text: data['sub_field']),
            ],
          ],
        ),

        // 단계별 팁
        if (tips != null && tips.isNotEmpty) ...[
          const SizedBox(height: 12),
          ...tips.take(compact ? 3 : tips.length).map(
                (tip) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 22,
                        height: 22,
                        decoration: const BoxDecoration(
                          color: AppColors.primary,
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            '${tip['step']}',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          tip['description']?.toString() ?? '',
                          style: AppTextStyles.body2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          if (compact && tips.length > 3)
            Text(
              '외 ${tips.length - 3}개 더',
              style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary),
            ),
        ],

        // 준비물
        if (materials != null && materials.isNotEmpty && !compact) ...[
          const SizedBox(height: 8),
          Text('준비물', style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: materials
                .map(
                  (m) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.grey[100],
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(m, style: AppTextStyles.bodySmall),
                  ),
                )
                .toList(),
          ),
        ],

        // 주의사항
        if (cautions != null && cautions.isNotEmpty && !compact) ...[
          const SizedBox(height: 8),
          Text('주의사항', style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          ...cautions.map(
            (c) => Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.warning_amber, size: 14, color: Colors.orange),
                const SizedBox(width: 4),
                Expanded(child: Text(c, style: AppTextStyles.body2)),
              ],
            ),
          ),
        ],
      ],
    );
  }
}

class _DifficultyBadge extends StatelessWidget {
  final String difficulty;
  const _DifficultyBadge({required this.difficulty});

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (difficulty) {
      'easy' => ('쉬움', Colors.green),
      'hard' => ('어려움', Colors.red),
      _ => ('보통', Colors.orange),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(color: color, fontSize: 12, fontWeight: FontWeight.w600),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String? text;
  const _InfoChip({required this.icon, this.text});

  @override
  Widget build(BuildContext context) {
    if (text == null) return const SizedBox.shrink();
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: AppColors.textSecondary),
        const SizedBox(width: 3),
        Text(text!, style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
      ],
    );
  }
}
