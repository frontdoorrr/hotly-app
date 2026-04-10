import 'package:freezed_annotation/freezed_annotation.dart';

part 'archived_content.freezed.dart';

enum ContentType { place, event, tips, review, unknown }

enum Platform { youtube, instagram, naver_blog }

enum Sentiment { positive, neutral, negative }

/// 아카이빙된 콘텐츠 엔티티
@freezed
class ArchivedContent with _$ArchivedContent {
  const factory ArchivedContent({
    required String id,
    required String url,
    required Platform platform,
    required ContentType contentType,

    // 메타데이터
    String? title,
    String? author,
    DateTime? publishedAt,
    String? thumbnailUrl,
    String? language,

    // 분석 공통
    String? summary,
    @Default([]) List<String> keywordsMain,
    @Default([]) List<String> keywordsSub,
    @Default([]) List<String> namedEntities,
    @Default([]) List<String> topicCategories,
    Sentiment? sentiment,
    @Default([]) List<String> todos,
    @Default([]) List<String> insights,

    // 타입별 추가 데이터 (content_type에 따라 구조 상이)
    Map<String, dynamic>? typeSpecificData,

    // 앱 메타
    String? linkAnalyzerId,
    required DateTime archivedAt,
  }) = _ArchivedContent;
}

/// 목록 조회 결과
@freezed
class ArchiveList with _$ArchiveList {
  const factory ArchiveList({
    required List<ArchivedContent> items,
    required int total,
    required int page,
    required int pageSize,
  }) = _ArchiveList;
}
