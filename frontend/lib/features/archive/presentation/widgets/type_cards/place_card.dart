import 'package:flutter/material.dart';
import '../../../../../core/l10n/l10n_extension.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../core/theme/app_text_styles.dart';
import '_shared.dart';

class PlaceCard extends StatelessWidget {
  final Map<String, dynamic> data;
  const PlaceCard({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final menus = (data['menu_items'] as List?)?.cast<Map<String, dynamic>>();
    final visitTips = (data['visit_tips'] as List?)?.cast<String>();

    return TypeInfoCard(
      children: [
        TypeInfoRow(icon: Icons.location_on, text: data['address'] as String?),
        TypeInfoRow(icon: Icons.access_time, text: data['operating_hours'] as String?),
        TypeInfoRow(icon: Icons.phone, text: data['phone'] as String?),
        TypeInfoRow(icon: Icons.payments_outlined, text: data['price_range'] as String?),
        if (data['reservation_required'] == true)
          TypeInfoRow(
            icon: Icons.bookmark_border,
            text: context.l10n.place_reservationRequired,
            color: Colors.orange,
          ),

        // 메뉴
        if (menus != null && menus.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(context.l10n.place_menu, style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          ...menus.take(4).map(
                (m) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(m['name']?.toString() ?? '', style: AppTextStyles.body2),
                      if (m['price'] != null)
                        Text(
                          '${_formatPrice(m['price'])}원',
                          style: AppTextStyles.body2
                              .copyWith(color: AppColors.textSecondary),
                        ),
                    ],
                  ),
                ),
              ),
        ],

        // 방문 팁
        if (visitTips != null && visitTips.isNotEmpty) ...[
          const SizedBox(height: 8),
          Text(context.l10n.place_visitTips, style: AppTextStyles.bodySmall.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: 4),
          ...visitTips.take(3).map(
                (tip) => Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('• ', style: TextStyle(color: AppColors.primary)),
                      Expanded(child: Text(tip, style: AppTextStyles.body2)),
                    ],
                  ),
                ),
              ),
        ],
      ],
    );
  }

  String _formatPrice(dynamic price) {
    if (price is int) {
      return price.toString().replaceAllMapped(
            RegExp(r'(\d)(?=(\d{3})+$)'),
            (m) => '${m[1]},',
          );
    }
    return price.toString();
  }
}
