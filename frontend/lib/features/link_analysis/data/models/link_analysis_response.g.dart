// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'link_analysis_response.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$LinkAnalysisResponseImpl _$$LinkAnalysisResponseImplFromJson(
        Map<String, dynamic> json) =>
    _$LinkAnalysisResponseImpl(
      success: json['success'] as bool,
      analysisId: json['analysis_id'] as String,
      status: json['status'] as String,
      resultData: json['result'] == null
          ? null
          : AnalysisResultData.fromJson(json['result'] as Map<String, dynamic>),
      cached: json['cached'] as bool? ?? false,
      processingTime: (json['processing_time'] as num?)?.toDouble() ?? 0.0,
      progress: (json['progress'] as num?)?.toDouble(),
      error: json['error'] as String?,
    );

Map<String, dynamic> _$$LinkAnalysisResponseImplToJson(
        _$LinkAnalysisResponseImpl instance) =>
    <String, dynamic>{
      'success': instance.success,
      'analysis_id': instance.analysisId,
      'status': instance.status,
      'result': instance.resultData,
      'cached': instance.cached,
      'processing_time': instance.processingTime,
      'progress': instance.progress,
      'error': instance.error,
    };

_$AnalysisResultDataImpl _$$AnalysisResultDataImplFromJson(
        Map<String, dynamic> json) =>
    _$AnalysisResultDataImpl(
      placeInfo: json['place_info'] == null
          ? null
          : PlaceInfoModel.fromJson(json['place_info'] as Map<String, dynamic>),
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      analysisTime: (json['analysis_time'] as num?)?.toDouble() ?? 0.0,
      contentMetadata: json['content_metadata'] == null
          ? null
          : ContentMetadataModel.fromJson(
              json['content_metadata'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$AnalysisResultDataImplToJson(
        _$AnalysisResultDataImpl instance) =>
    <String, dynamic>{
      'place_info': instance.placeInfo,
      'confidence': instance.confidence,
      'analysis_time': instance.analysisTime,
      'content_metadata': instance.contentMetadata,
    };

_$PlaceInfoModelImpl _$$PlaceInfoModelImplFromJson(Map<String, dynamic> json) =>
    _$PlaceInfoModelImpl(
      name: json['name'] as String,
      address: json['address'] as String?,
      category: json['category'] as String?,
      tags:
          (json['tags'] as List<dynamic>?)?.map((e) => e as String).toList() ??
              const [],
      description: json['description'] as String?,
      rating: (json['rating'] as num?)?.toDouble(),
      coordinates: json['coordinates'] == null
          ? null
          : CoordinatesModel.fromJson(
              json['coordinates'] as Map<String, dynamic>),
    );

Map<String, dynamic> _$$PlaceInfoModelImplToJson(
        _$PlaceInfoModelImpl instance) =>
    <String, dynamic>{
      'name': instance.name,
      'address': instance.address,
      'category': instance.category,
      'tags': instance.tags,
      'description': instance.description,
      'rating': instance.rating,
      'coordinates': instance.coordinates,
    };

_$CoordinatesModelImpl _$$CoordinatesModelImplFromJson(
        Map<String, dynamic> json) =>
    _$CoordinatesModelImpl(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );

Map<String, dynamic> _$$CoordinatesModelImplToJson(
        _$CoordinatesModelImpl instance) =>
    <String, dynamic>{
      'latitude': instance.latitude,
      'longitude': instance.longitude,
    };

_$ContentMetadataModelImpl _$$ContentMetadataModelImplFromJson(
        Map<String, dynamic> json) =>
    _$ContentMetadataModelImpl(
      title: json['title'] as String?,
      description: json['description'] as String?,
      images: (json['images'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      hashtags: (json['hashtags'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      extractionTime: (json['extraction_time'] as num?)?.toDouble(),
    );

Map<String, dynamic> _$$ContentMetadataModelImplToJson(
        _$ContentMetadataModelImpl instance) =>
    <String, dynamic>{
      'title': instance.title,
      'description': instance.description,
      'images': instance.images,
      'hashtags': instance.hashtags,
      'extraction_time': instance.extractionTime,
    };
