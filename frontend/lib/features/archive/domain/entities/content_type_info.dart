/// 콘텐츠 타입 메타 정보 (DB에서 관리)
class ContentTypeInfo {
  final String key;
  final String label;
  final String? labelEn;
  final String? icon;
  final String? colorHex;
  final int order;

  const ContentTypeInfo({
    required this.key,
    required this.label,
    this.labelEn,
    this.icon,
    this.colorHex,
    required this.order,
  });

  String localizedLabel(String languageCode) =>
      languageCode == 'en' ? (labelEn ?? label) : label;
}
