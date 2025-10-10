import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/link_analysis_result.dart';

part 'link_analysis_response.freezed.dart';
part 'link_analysis_response.g.dart';

/// API Response Model for Link Analysis
@freezed
class LinkAnalysisResponse with _$LinkAnalysisResponse {
  const factory LinkAnalysisResponse({
    required bool success,
    @JsonKey(name: 'analysisId') required String analysisId,
    required String status,
    @JsonKey(name: 'result') AnalysisResultData? resultData,
    @Default(false) bool cached,
    @JsonKey(name: 'processingTime') @Default(0.0) double processingTime,
    double? progress,
    String? error,
  }) = _LinkAnalysisResponse;

  factory LinkAnalysisResponse.fromJson(Map<String, dynamic> json) =>
      _$LinkAnalysisResponseFromJson(json);
}

/// Analysis Result Data from API
@freezed
class AnalysisResultData with _$AnalysisResultData {
  const factory AnalysisResultData({
    @JsonKey(name: 'placeInfo') PlaceInfoModel? placeInfo,
    @Default(0.0) double confidence,
    @JsonKey(name: 'analysisTime') @Default(0.0) double analysisTime,
    @JsonKey(name: 'contentMetadata') ContentMetadataModel? contentMetadata,
  }) = _AnalysisResultData;

  factory AnalysisResultData.fromJson(Map<String, dynamic> json) =>
      _$AnalysisResultDataFromJson(json);
}

/// Place Info Model from API
@freezed
class PlaceInfoModel with _$PlaceInfoModel {
  const factory PlaceInfoModel({
    required String name,
    String? address,
    String? category,
    @Default([]) List<String> tags,
    String? description,
    double? rating,
    CoordinatesModel? coordinates,
  }) = _PlaceInfoModel;

  factory PlaceInfoModel.fromJson(Map<String, dynamic> json) =>
      _$PlaceInfoModelFromJson(json);
}

/// Coordinates Model from API
@freezed
class CoordinatesModel with _$CoordinatesModel {
  const factory CoordinatesModel({
    required double latitude,
    required double longitude,
  }) = _CoordinatesModel;

  factory CoordinatesModel.fromJson(Map<String, dynamic> json) =>
      _$CoordinatesModelFromJson(json);
}

/// Content Metadata Model from API
@freezed
class ContentMetadataModel with _$ContentMetadataModel {
  const factory ContentMetadataModel({
    String? title,
    String? description,
    @Default([]) List<String> images,
    @Default([]) List<String> hashtags,
    @JsonKey(name: 'extractionTime') double? extractionTime,
  }) = _ContentMetadataModel;

  factory ContentMetadataModel.fromJson(Map<String, dynamic> json) =>
      _$ContentMetadataModelFromJson(json);
}

/// Extension to convert API models to domain entities
extension LinkAnalysisResponseX on LinkAnalysisResponse {
  LinkAnalysisResult toEntity() {
    return LinkAnalysisResult(
      analysisId: analysisId,
      status: _mapStatus(status),
      placeInfo: resultData?.placeInfo?.toEntity(),
      contentMetadata: resultData?.contentMetadata?.toEntity(),
      confidence: resultData?.confidence ?? 0.0,
      processingTime: processingTime,
      cached: cached,
      progress: progress,
      error: error,
    );
  }

  AnalysisStatus _mapStatus(String status) {
    switch (status.toLowerCase()) {
      case 'pending':
        return AnalysisStatus.pending;
      case 'in_progress':
        return AnalysisStatus.inProgress;
      case 'completed':
        return AnalysisStatus.completed;
      case 'failed':
        return AnalysisStatus.failed;
      case 'cancelled':
        return AnalysisStatus.cancelled;
      default:
        return AnalysisStatus.pending;
    }
  }
}

extension PlaceInfoModelX on PlaceInfoModel {
  PlaceInfo toEntity() {
    return PlaceInfo(
      name: name,
      address: address,
      category: category,
      tags: tags,
      description: description,
      rating: rating,
      coordinates: coordinates?.toEntity(),
    );
  }
}

extension CoordinatesModelX on CoordinatesModel {
  Coordinates toEntity() {
    return Coordinates(
      latitude: latitude,
      longitude: longitude,
    );
  }
}

extension ContentMetadataModelX on ContentMetadataModel {
  ContentMetadata toEntity() {
    return ContentMetadata(
      title: title,
      description: description,
      images: images,
      hashtags: hashtags,
      extractionTime: extractionTime,
    );
  }
}
