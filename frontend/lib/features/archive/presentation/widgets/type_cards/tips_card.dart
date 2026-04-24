import 'dart:convert';

import 'package:flutter/material.dart';
import '../../../../../core/l10n/l10n_extension.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/theme/app_text_styles.dart';
import '_shared.dart';

class TipsCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final bool compact;
  const TipsCard({super.key, required this.data, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final tips = _parseTipList(data['tip_list']);
    final materials = _parseStringList(data['materials']);
    final cautions = _parseStringList(data['cautions']);
    final difficulty = data['difficulty']?.toString();

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
                text: data['estimated_time'] as String?,
              ),
            if (data['sub_field'] != null) ...[
              const SizedBox(width: 8),
              _InfoChip(icon: Icons.category_outlined, text: data['sub_field'] as String?),
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
                          (tip['description'] ?? tip['text'] ?? '').toString(),
                          style: AppTextStyles.body2,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          if (compact && tips.length > 3)
            Text(
              context.l10n.tips_moreItems(tips.length - 3),
              style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary),
            ),
        ],

        // 준비물
        if (materials != null && materials.isNotEmpty && !compact) ...[
          const SizedBox(height: 8),
          Text(context.l10n.tips_materials, style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
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
          Text(context.l10n.tips_cautions, style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
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
    final l10n = context.l10n;
    final (label, color) = switch (difficulty) {
      'easy' => (l10n.tips_easy, Colors.green),
      'hard' => (l10n.tips_hard, Colors.red),
      _ => (l10n.tips_medium, Colors.orange),
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

/// tip_list 원소가 Map이 아니라 String으로 오는 경우까지 허용하도록 방어 처리.
List<Map<String, dynamic>>? _parseTipList(Object? raw) {
  final list = _asList(raw);
  if (list == null) return null;
  final out = <Map<String, dynamic>>[];
  var stepCounter = 1;
  for (final item in list) {
    final map = _asMap(item);
    if (map != null) {
      if (map['step'] == null) {
        map['step'] = stepCounter;
      }
      out.add(map);
    } else if (item is String && item.isNotEmpty) {
      out.add({'step': stepCounter, 'description': item});
    } else {
      continue;
    }
    stepCounter++;
  }
  return out;
}

List<String>? _parseStringList(Object? raw) {
  final list = _asList(raw);
  if (list == null) return null;
  return list
      .where((e) => e != null)
      .map((e) => e.toString())
      .where((s) => s.isNotEmpty)
      .toList();
}

List<dynamic>? _asList(Object? raw) {
  if (raw == null) return null;
  if (raw is List) return raw;
  if (raw is String) {
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) return decoded;
    } catch (_) {}
  }
  return null;
}

Map<String, dynamic>? _asMap(Object? raw) {
  if (raw == null) return null;
  if (raw is Map<String, dynamic>) return Map<String, dynamic>.from(raw);
  if (raw is Map) return raw.map((k, v) => MapEntry(k.toString(), v));
  if (raw is String) {
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) return Map<String, dynamic>.from(decoded);
      if (decoded is Map) return decoded.map((k, v) => MapEntry(k.toString(), v));
    } catch (_) {}
  }
  return null;
}
