import 'package:freezed_annotation/freezed_annotation.dart';
import '../../domain/entities/archived_content.dart';

part 'archive_model.freezed.dart';
part 'archive_model.g.dart';

@freezed
class ArchivedContentModel with _$ArchivedContentModel {
  const factory ArchivedContentModel({
    required String id,
    required String url,
    required String platform,
    @JsonKey(name: 'content_type') required String contentType,
    String? title,
    String? author,
    @JsonKey(name: 'published_at') String? publishedAt,
    @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
    String? language,
    String? summary,
    @JsonKey(name: 'keywords_main') @Default([]) List<String> keywordsMain,
    @JsonKey(name: 'keywords_sub') @Default([]) List<String> keywordsSub,
    @JsonKey(name: 'named_entities') @Default([]) List<String> namedEntities,
    @JsonKey(name: 'topic_categories') @Default([]) List<String> topicCategories,
    String? sentiment,
    @Default([]) List<String> todos,
    @Default([]) List<String> insights,
    @JsonKey(name: 'type_specific_data') Map<String, dynamic>? typeSpecificData,
    @JsonKey(name: 'link_analyzer_id') String? linkAnalyzerId,
    @JsonKey(name: 'archived_at') required String archivedAt,
  }) = _ArchivedContentModel;

  factory ArchivedContentModel.fromJson(Map<String, dynamic> json) =>
      _$ArchivedContentModelFromJson(json);
}

@freezed
class ArchiveListModel with _$ArchiveListModel {
  const factory ArchiveListModel({
    required List<ArchivedContentModel> items,
    required int total,
    required int page,
    @JsonKey(name: 'page_size') required int pageSize,
  }) = _ArchiveListModel;

  factory ArchiveListModel.fromJson(Map<String, dynamic> json) =>
      _$ArchiveListModelFromJson(json);
}

// ------------------------------------------------------------------
// Model → Entity 변환
// ------------------------------------------------------------------

extension ArchivedContentModelX on ArchivedContentModel {
  ArchivedContent toEntity() {
    return ArchivedContent(
      id: id,
      url: url,
      platform: _parsePlatform(platform),
      contentType: _parseContentType(contentType),
      title: title,
      author: author,
      publishedAt: publishedAt != null ? DateTime.tryParse(publishedAt!) : null,
      thumbnailUrl: thumbnailUrl,
      language: language,
      summary: summary,
      keywordsMain: keywordsMain,
      keywordsSub: keywordsSub,
      namedEntities: namedEntities,
      topicCategories: topicCategories,
      sentiment: _parseSentiment(sentiment),
      todos: todos,
      insights: insights,
      typeSpecificData: typeSpecificData,
      linkAnalyzerId: linkAnalyzerId,
      archivedAt: DateTime.parse(archivedAt),
    );
  }
}

extension ArchiveListModelX on ArchiveListModel {
  ArchiveList toEntity() {
    return ArchiveList(
      items: items.map((e) => e.toEntity()).toList(),
      total: total,
      page: page,
      pageSize: pageSize,
    );
  }
}

ContentType _parseContentType(String value) {
  switch (value) {
    case 'place':
      return ContentType.place;
    case 'event':
      return ContentType.event;
    case 'tips':
      return ContentType.tips;
    case 'review':
      return ContentType.review;
    default:
      return ContentType.unknown;
  }
}

Platform _parsePlatform(String value) {
  switch (value) {
    case 'instagram':
      return Platform.instagram;
    case 'naver_blog':
      return Platform.naver_blog;
    default:
      return Platform.youtube;
  }
}

Sentiment? _parseSentiment(String? value) {
  switch (value) {
    case 'positive':
      return Sentiment.positive;
    case 'negative':
      return Sentiment.negative;
    case 'neutral':
      return Sentiment.neutral;
    default:
      return null;
  }
}
