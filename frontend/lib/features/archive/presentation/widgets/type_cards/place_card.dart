import 'dart:convert';

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
    final menus = _parseMenus(data['menu_items']);
    final visitTips = _parseStringList(data['visit_tips']);

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
                          context.l10n.place_priceWon(_formatPrice(m['price'])),
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

/// menu_items가 List<Map>이 아니라 List<String>이나 JSON 문자열 등으로
/// 오는 경우를 모두 방어적으로 Map 리스트로 변환한다.
List<Map<String, dynamic>>? _parseMenus(Object? raw) {
  final list = _asList(raw);
  if (list == null) return null;
  final out = <Map<String, dynamic>>[];
  for (final item in list) {
    final map = _asMap(item);
    if (map != null) {
      out.add(map);
    } else if (item is String && item.isNotEmpty) {
      out.add({'name': item});
    }
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
  if (raw is Map<String, dynamic>) return raw;
  if (raw is Map) return raw.map((k, v) => MapEntry(k.toString(), v));
  if (raw is String) {
    try {
      final decoded = jsonDecode(raw);
      if (decoded is Map<String, dynamic>) return decoded;
      if (decoded is Map) return decoded.map((k, v) => MapEntry(k.toString(), v));
    } catch (_) {}
  }
  return null;
}
