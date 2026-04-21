import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_text_styles.dart';
import '../../domain/entities/content_type_info.dart';
import '../providers/archive_provider.dart';

/// contentType 문자열에 대한 정적 폴백 맵 (API 로딩 전/실패 시)
const _fallbackLabels = {
  'place': '장소',
  'event': '이벤트',
  'tips': '팁',
  'review': '리뷰',
};

const _fallbackIcons = {
  'place': Icons.place,
  'event': Icons.event,
  'tips': Icons.lightbulb,
  'review': Icons.star,
};

const _fallbackColors = {
  'place': Colors.orange,
  'event': Colors.purple,
  'tips': Colors.amber,
  'review': Colors.blue,
};

/// contentTypesProvider에서 타입 정보를 읽어 배지를 렌더링합니다.
/// API 로딩 전/실패 시 폴백 맵을 사용합니다.
class ContentTypeBadge extends ConsumerWidget {
  final String contentType;

  const ContentTypeBadge({super.key, required this.contentType});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final typesAsync = ref.watch(contentTypesProvider);
    final info = typesAsync.valueOrNull
        ?.where((t) => t.key == contentType)
        .firstOrNull;

    final label = info?.label ?? _fallbackLabels[contentType] ?? contentType;
    final icon = _resolveIcon(info);
    final color = _resolveColor(info);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: AppTextStyles.bodySmall.copyWith(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  IconData _resolveIcon(ContentTypeInfo? info) {
    if (info?.icon != null) {
      return _iconFromName(info!.icon!) ?? _fallbackIcons[contentType] ?? Icons.article;
    }
    return _fallbackIcons[contentType] ?? Icons.article;
  }

  Color _resolveColor(ContentTypeInfo? info) {
    if (info?.colorHex != null) {
      try {
        final hex = info!.colorHex!.replaceFirst('#', '');
        return Color(int.parse(hex, radix: 16) + 0xFF000000);
      } catch (_) {}
    }
    return _fallbackColors[contentType] ?? Colors.grey;
  }

  static IconData? _iconFromName(String name) {
    const map = {
      'place': Icons.place,
      'event': Icons.event,
      'lightbulb': Icons.lightbulb,
      'star': Icons.star,
      'article': Icons.article,
    };
    return map[name];
  }
}
