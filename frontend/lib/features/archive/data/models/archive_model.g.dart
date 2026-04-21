// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'archive_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_$ArchivedContentModelImpl _$$ArchivedContentModelImplFromJson(
        Map<String, dynamic> json) =>
    _$ArchivedContentModelImpl(
      id: json['id'] as String,
      url: json['url'] as String,
      platform: json['platform'] as String,
      contentType: json['content_type'] as String,
      title: json['title'] as String?,
      author: json['author'] as String?,
      publishedAt: json['published_at'] as String?,
      thumbnailUrl: json['thumbnail_url'] as String?,
      language: json['language'] as String?,
      summary: json['summary'] as String?,
      keywordsMain: (json['keywords_main'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      keywordsSub: (json['keywords_sub'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      namedEntities: (json['named_entities'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      topicCategories: (json['topic_categories'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      sentiment: json['sentiment'] as String?,
      todos:
          (json['todos'] as List<dynamic>?)?.map((e) => e as String).toList() ??
              const [],
      insights: (json['insights'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          const [],
      typeSpecificData: const _TypeSpecificDataConverter()
          .fromJson(json['type_specific_data']),
      linkAnalyzerId: json['link_analyzer_id'] as String?,
      archivedAt: json['archived_at'] as String,
    );

Map<String, dynamic> _$$ArchivedContentModelImplToJson(
        _$ArchivedContentModelImpl instance) =>
    <String, dynamic>{
      'id': instance.id,
      'url': instance.url,
      'platform': instance.platform,
      'content_type': instance.contentType,
      'title': instance.title,
      'author': instance.author,
      'published_at': instance.publishedAt,
      'thumbnail_url': instance.thumbnailUrl,
      'language': instance.language,
      'summary': instance.summary,
      'keywords_main': instance.keywordsMain,
      'keywords_sub': instance.keywordsSub,
      'named_entities': instance.namedEntities,
      'topic_categories': instance.topicCategories,
      'sentiment': instance.sentiment,
      'todos': instance.todos,
      'insights': instance.insights,
      'type_specific_data':
          const _TypeSpecificDataConverter().toJson(instance.typeSpecificData),
      'link_analyzer_id': instance.linkAnalyzerId,
      'archived_at': instance.archivedAt,
    };

_$ArchiveListModelImpl _$$ArchiveListModelImplFromJson(
        Map<String, dynamic> json) =>
    _$ArchiveListModelImpl(
      items: (json['items'] as List<dynamic>)
          .map((e) => ArchivedContentModel.fromJson(e as Map<String, dynamic>))
          .toList(),
      total: (json['total'] as num).toInt(),
      page: (json['page'] as num).toInt(),
      pageSize: (json['page_size'] as num).toInt(),
    );

Map<String, dynamic> _$$ArchiveListModelImplToJson(
        _$ArchiveListModelImpl instance) =>
    <String, dynamic>{
      'items': instance.items,
      'total': instance.total,
      'page': instance.page,
      'page_size': instance.pageSize,
    };
