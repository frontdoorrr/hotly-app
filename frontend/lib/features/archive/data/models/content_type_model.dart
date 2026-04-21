import '../../domain/entities/content_type_info.dart';

class ContentTypeInfoModel {
  final String key;
  final String label;
  final String? icon;
  final String? color;
  final int order;

  const ContentTypeInfoModel({
    required this.key,
    required this.label,
    this.icon,
    this.color,
    required this.order,
  });

  factory ContentTypeInfoModel.fromJson(Map<String, dynamic> json) {
    return ContentTypeInfoModel(
      key: json['key'] as String,
      label: json['label'] as String,
      icon: json['icon'] as String?,
      color: json['color'] as String?,
      order: json['order'] as int,
    );
  }

  ContentTypeInfo toEntity() => ContentTypeInfo(
        key: key,
        label: label,
        icon: icon,
        colorHex: color,
        order: order,
      );
}
