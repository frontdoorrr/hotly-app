// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'tag_statistics.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$TagInfoImpl _$$TagInfoImplFromJson(Map<String, dynamic> json) =>
    _$TagInfoImpl(
      tag: json['tag'] as String,
      count: (json['count'] as num).toInt(),
    );

Map<String, dynamic> _$$TagInfoImplToJson(_$TagInfoImpl instance) =>
    <String, dynamic>{
      'tag': instance.tag,
      'count': instance.count,
    };

_$TagStatisticsImpl _$$TagStatisticsImplFromJson(Map<String, dynamic> json) =>
    _$TagStatisticsImpl(
      totalUniqueTags: (json['totalUniqueTags'] as num).toInt(),
      totalTagUsage: (json['totalTagUsage'] as num).toInt(),
      mostUsedTags: (json['mostUsedTags'] as List<dynamic>)
          .map((e) => TagInfo.fromJson(e as Map<String, dynamic>))
          .toList(),
      tagCategories: (json['tagCategories'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, (e as List<dynamic>).map((e) => e as String).toList()),
      ),
      averageTagsPerPlace: (json['averageTagsPerPlace'] as num).toDouble(),
      placesCount: (json['placesCount'] as num).toInt(),
    );

Map<String, dynamic> _$$TagStatisticsImplToJson(_$TagStatisticsImpl instance) =>
    <String, dynamic>{
      'totalUniqueTags': instance.totalUniqueTags,
      'totalTagUsage': instance.totalTagUsage,
      'mostUsedTags': instance.mostUsedTags,
      'tagCategories': instance.tagCategories,
      'averageTagsPerPlace': instance.averageTagsPerPlace,
      'placesCount': instance.placesCount,
    };

_$TagClusterImpl _$$TagClusterImplFromJson(Map<String, dynamic> json) =>
    _$TagClusterImpl(
      clusters: (json['clusters'] as Map<String, dynamic>).map(
        (k, e) =>
            MapEntry(k, (e as List<dynamic>).map((e) => e as String).toList()),
      ),
    );

Map<String, dynamic> _$$TagClusterImplToJson(_$TagClusterImpl instance) =>
    <String, dynamic>{
      'clusters': instance.clusters,
    };
