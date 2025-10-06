import 'package:freezed_annotation/freezed_annotation.dart';

part 'link_analysis_result.freezed.dart';

/// Link Analysis Result Entity
@freezed
class LinkAnalysisResult with _$LinkAnalysisResult {
  const factory LinkAnalysisResult({
    required String analysisId,
    required AnalysisStatus status,
    PlaceInfo? placeInfo,
    ContentMetadata? contentMetadata,
    @Default(0.0) double confidence,
    @Default(0.0) double processingTime,
    @Default(false) bool cached,
    double? progress,
    String? error,
  }) = _LinkAnalysisResult;
}

/// Analysis Status
enum AnalysisStatus {
  pending,
  inProgress,
  completed,
  failed,
  cancelled,
}

/// Place Information extracted from link
@freezed
class PlaceInfo with _$PlaceInfo {
  const factory PlaceInfo({
    required String name,
    String? address,
    String? category,
    List<String>? tags,
    String? description,
    double? rating,
    Coordinates? coordinates,
  }) = _PlaceInfo;
}

/// Geographic Coordinates
@freezed
class Coordinates with _$Coordinates {
  const factory Coordinates({
    required double latitude,
    required double longitude,
  }) = _Coordinates;
}

/// Content Metadata from extracted URL
@freezed
class ContentMetadata with _$ContentMetadata {
  const factory ContentMetadata({
    String? title,
    String? description,
    @Default([]) List<String> images,
    @Default([]) List<String> hashtags,
    double? extractionTime,
  }) = _ContentMetadata;
}
