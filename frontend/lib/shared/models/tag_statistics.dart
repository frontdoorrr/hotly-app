import 'package:freezed_annotation/freezed_annotation.dart';

part 'tag_statistics.freezed.dart';
part 'tag_statistics.g.dart';

/// Tag information with usage count
@freezed
class TagInfo with _$TagInfo {
  const factory TagInfo({
    required String tag,
    required int count,
  }) = _TagInfo;

  factory TagInfo.fromJson(Map<String, dynamic> json) =>
      _$TagInfoFromJson(json);
}

/// Tag statistics for user
@freezed
class TagStatistics with _$TagStatistics {
  const factory TagStatistics({
    required int totalUniqueTags,
    required int totalTagUsage,
    required List<TagInfo> mostUsedTags,
    required Map<String, List<String>> tagCategories,
    required double averageTagsPerPlace,
    required int placesCount,
  }) = _TagStatistics;

  factory TagStatistics.fromJson(Map<String, dynamic> json) =>
      _$TagStatisticsFromJson(json);

  factory TagStatistics.empty() => const TagStatistics(
        totalUniqueTags: 0,
        totalTagUsage: 0,
        mostUsedTags: [],
        tagCategories: {},
        averageTagsPerPlace: 0.0,
        placesCount: 0,
      );
}

/// Tag cluster response
@freezed
class TagCluster with _$TagCluster {
  const factory TagCluster({
    required Map<String, List<String>> clusters,
  }) = _TagCluster;

  factory TagCluster.fromJson(Map<String, dynamic> json) =>
      _$TagClusterFromJson(json);
}
