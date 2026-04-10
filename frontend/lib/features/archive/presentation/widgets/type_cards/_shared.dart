// 타입 카드들이 공통으로 사용하는 위젯

import 'package:flutter/material.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/theme/app_text_styles.dart';

class TypeInfoCard extends StatelessWidget {
  final List<Widget> children;
  const TypeInfoCard({super.key, required this.children});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Colors.grey[200]!),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: children,
        ),
      ),
    );
  }
}

class TypeInfoRow extends StatelessWidget {
  final IconData icon;
  final String? text;
  final Color? color;

  const TypeInfoRow({super.key, required this.icon, this.text, this.color});

  @override
  Widget build(BuildContext context) {
    if (text == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 15, color: color ?? AppColors.textSecondary),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              text!,
              style: AppTextStyles.body2.copyWith(
                color: color ?? AppColors.textPrimary,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
