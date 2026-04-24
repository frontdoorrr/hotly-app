import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../../../core/l10n/l10n_extension.dart';
import '../../../../core/theme/app_theme.dart';
import '../../domain/entities/map_entities.dart';

/// Bottom sheet showing search result place information
class SearchResultInfo extends StatelessWidget {
  final PlaceSearchResult place;
  final VoidCallback onClose;
  final VoidCallback? onSave;

  const SearchResultInfo({
    super.key,
    required this.place,
    required this.onClose,
    this.onSave,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(AppTheme.space4),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(
          top: Radius.circular(AppTheme.radiusXl),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 헤더: 장소명 + 닫기 버튼
          Row(
            children: [
              Expanded(
                child: Text(
                  place.placeName,
                  style: theme.textTheme.titleLarge,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: onClose,
                tooltip: context.l10n.common_close,
              ),
            ],
          ),

          const SizedBox(height: AppTheme.space2),

          // 카테고리
          if (place.categoryName != null && place.categoryName!.isNotEmpty)
            _InfoRow(
              icon: Icons.category_outlined,
              text: place.categoryName!,
              emphasize: true,
            ),

          // 도로명 주소 (있으면 우선)
          if (place.roadAddress != null && place.roadAddress!.isNotEmpty)
            _InfoRow(
              icon: Icons.place_outlined,
              text: place.roadAddress!,
            ),

          // 지번 주소 (도로명과 다른 경우에만 추가로)
          if (place.address.isNotEmpty &&
              place.address != place.roadAddress)
            _InfoRow(
              icon: Icons.map_outlined,
              text: place.address,
            ),

          // 전화 (탭하면 전화 앱)
          if (place.phone != null && place.phone!.isNotEmpty)
            _InfoRow(
              icon: Icons.phone_outlined,
              text: place.phone!,
              onTap: () => _launchTel(context, place.phone!),
            ),

          // 거리
          if (place.distance != null)
            _InfoRow(
              icon: Icons.near_me_outlined,
              text: '${(place.distance! / 1000).toStringAsFixed(1)} km',
            ),

          const SizedBox(height: AppTheme.space3),

          // 액션 버튼들
          Row(
            children: [
              // 카카오맵에서 열기
              if (_kakaoMapUrl != null)
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => _launchUrl(context, _kakaoMapUrl!),
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: Text(
                      context.l10n.map_openInKakaoMap,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
              if (_kakaoMapUrl != null && onSave != null)
                const SizedBox(width: AppTheme.space2),
              // 저장
              if (onSave != null)
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: onSave,
                    icon: const Icon(Icons.bookmark_add_outlined, size: 16),
                    label: Text(
                      context.l10n.common_savePlaceButton,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  /// 카카오맵 URL — backend가 placeUrl을 주면 그걸 쓰고,
  /// 없으면 placeId 기반으로 대체 URL 구성.
  String? get _kakaoMapUrl {
    if (place.placeUrl != null && place.placeUrl!.isNotEmpty) {
      return place.placeUrl;
    }
    if (place.placeId.isNotEmpty) {
      return 'https://place.map.kakao.com/${place.placeId}';
    }
    return null;
  }

  Future<void> _launchUrl(BuildContext context, String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null || !await canLaunchUrl(uri)) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.map_cannotOpenExternal)),
        );
      }
      return;
    }
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Future<void> _launchTel(BuildContext context, String phone) async {
    final digits = phone.replaceAll(RegExp(r'[^0-9+]'), '');
    if (digits.isEmpty) return;
    final uri = Uri(scheme: 'tel', path: digits);
    if (!await canLaunchUrl(uri)) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(context.l10n.map_cannotOpenExternal)),
        );
      }
      return;
    }
    await launchUrl(uri);
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String text;
  final VoidCallback? onTap;
  final bool emphasize;

  const _InfoRow({
    required this.icon,
    required this.text,
    this.onTap,
    this.emphasize = false,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final textStyle = theme.textTheme.bodyMedium?.copyWith(
      color: emphasize
          ? theme.colorScheme.primary
          : (onTap != null ? theme.colorScheme.primary : null),
      decoration: onTap != null ? TextDecoration.underline : null,
    );

    final row = Padding(
      padding: const EdgeInsets.only(bottom: AppTheme.space1),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: theme.colorScheme.secondary),
          const SizedBox(width: AppTheme.space1),
          Expanded(
            child: Text(
              text,
              style: textStyle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );

    if (onTap == null) return row;
    return InkWell(onTap: onTap, child: row);
  }
}
