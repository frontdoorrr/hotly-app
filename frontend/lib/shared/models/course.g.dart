// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'course.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$CourseImpl _$$CourseImplFromJson(Map<String, dynamic> json) => _$CourseImpl(
      id: json['id'] as String,
      title: json['title'] as String,
      type: $enumDecode(_$CourseTypeEnumMap, json['type']),
      places: (json['places'] as List<dynamic>)
          .map((e) => CoursePlace.fromJson(e as Map<String, dynamic>))
          .toList(),
      description: json['description'] as String?,
      thumbnailUrl: json['thumbnailUrl'] as String?,
      totalDuration: json['totalDuration'] == null
          ? Duration.zero
          : Duration(microseconds: (json['totalDuration'] as num).toInt()),
      likeCount: (json['likeCount'] as num?)?.toInt() ?? 0,
      shareCount: (json['shareCount'] as num?)?.toInt() ?? 0,
      isPublic: json['isPublic'] as bool? ?? false,
      createdAt: json['createdAt'] == null
          ? null
          : DateTime.parse(json['createdAt'] as String),
      updatedAt: json['updatedAt'] == null
          ? null
          : DateTime.parse(json['updatedAt'] as String),
    );

Map<String, dynamic> _$$CourseImplToJson(_$CourseImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'title': instance.title,
      'type': _$CourseTypeEnumMap[instance.type]!,
      'places': instance.places,
      'description': instance.description,
      'thumbnailUrl': instance.thumbnailUrl,
      'totalDuration': instance.totalDuration.inMicroseconds,
      'likeCount': instance.likeCount,
      'shareCount': instance.shareCount,
      'isPublic': instance.isPublic,
      'createdAt': instance.createdAt?.toIso8601String(),
      'updatedAt': instance.updatedAt?.toIso8601String(),
    };

const _$CourseTypeEnumMap = {
  CourseType.date: 'date',
  CourseType.travel: 'travel',
  CourseType.foodTour: 'food_tour',
  CourseType.other: 'other',
};
