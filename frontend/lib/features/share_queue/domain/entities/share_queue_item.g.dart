// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'share_queue_item.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ShareQueueItemImpl _$$ShareQueueItemImplFromJson(Map<String, dynamic> json) =>
    _$ShareQueueItemImpl(
      id: json['id'] as String,
      url: json['url'] as String,
      title: json['title'] as String?,
      sharedAt: DateTime.parse(json['sharedAt'] as String),
      status: $enumDecodeNullable(_$ShareQueueStatusEnumMap, json['status']) ??
          ShareQueueStatus.pending,
      result: json['result'] == null
          ? null
          : ShareQueueAnalysisResult.fromJson(
              json['result'] as Map<String, dynamic>),
      errorMessage: json['errorMessage'] as String?,
      retryCount: (json['retryCount'] as num?)?.toInt() ?? 0,
      platform: json['platform'] as String?,
    );

Map<String, dynamic> _$$ShareQueueItemImplToJson(
        _$ShareQueueItemImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'url': instance.url,
      'title': instance.title,
      'sharedAt': instance.sharedAt.toIso8601String(),
      'status': _$ShareQueueStatusEnumMap[instance.status]!,
      'result': instance.result,
      'errorMessage': instance.errorMessage,
      'retryCount': instance.retryCount,
      'platform': instance.platform,
    };

const _$ShareQueueStatusEnumMap = {
  ShareQueueStatus.pending: 'pending',
  ShareQueueStatus.analyzing: 'analyzing',
  ShareQueueStatus.completed: 'completed',
  ShareQueueStatus.saved: 'saved',
  ShareQueueStatus.failed: 'failed',
  ShareQueueStatus.ignored: 'ignored',
};

_$ShareQueueAnalysisResultImpl _$$ShareQueueAnalysisResultImplFromJson(
        Map<String, dynamic> json) =>
    _$ShareQueueAnalysisResultImpl(
      placeName: json['placeName'] as String,
      category: json['category'] as String,
      address: json['address'] as String?,
      imageUrl: json['imageUrl'] as String?,
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      tags:
          (json['tags'] as List<dynamic>?)?.map((e) => e as String).toList() ??
              const [],
      extractedInfo: json['extractedInfo'] as Map<String, dynamic>?,
      analysisId: json['analysisId'] as String?,
    );

Map<String, dynamic> _$$ShareQueueAnalysisResultImplToJson(
        _$ShareQueueAnalysisResultImpl instance) =>
    <String, dynamic>{
      'placeName': instance.placeName,
      'category': instance.category,
      'address': instance.address,
      'imageUrl': instance.imageUrl,
      'confidence': instance.confidence,
      'tags': instance.tags,
      'extractedInfo': instance.extractedInfo,
      'analysisId': instance.analysisId,
    };
