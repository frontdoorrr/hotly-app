// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'archive_model.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ArchivedContentModel _$ArchivedContentModelFromJson(Map<String, dynamic> json) {
  return _ArchivedContentModel.fromJson(json);
}

/// @nodoc
mixin _$ArchivedContentModel {
  String get id => throw _privateConstructorUsedError;
  String get url => throw _privateConstructorUsedError;
  String get platform => throw _privateConstructorUsedError;
  @JsonKey(name: 'content_type')
  String get contentType => throw _privateConstructorUsedError;
  String? get title => throw _privateConstructorUsedError;
  String? get author => throw _privateConstructorUsedError;
  @JsonKey(name: 'published_at')
  String? get publishedAt => throw _privateConstructorUsedError;
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  String? get language => throw _privateConstructorUsedError;
  String? get summary => throw _privateConstructorUsedError;
  @JsonKey(name: 'keywords_main')
  List<String> get keywordsMain => throw _privateConstructorUsedError;
  @JsonKey(name: 'keywords_sub')
  List<String> get keywordsSub => throw _privateConstructorUsedError;
  @JsonKey(name: 'named_entities')
  List<String> get namedEntities => throw _privateConstructorUsedError;
  @JsonKey(name: 'topic_categories')
  List<String> get topicCategories => throw _privateConstructorUsedError;
  String? get sentiment => throw _privateConstructorUsedError;
  List<String> get todos => throw _privateConstructorUsedError;
  List<String> get insights => throw _privateConstructorUsedError;
  @JsonKey(name: 'type_specific_data')
  Map<String, dynamic>? get typeSpecificData =>
      throw _privateConstructorUsedError;
  @JsonKey(name: 'link_analyzer_id')
  String? get linkAnalyzerId => throw _privateConstructorUsedError;
  @JsonKey(name: 'archived_at')
  String get archivedAt => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ArchivedContentModelCopyWith<ArchivedContentModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchivedContentModelCopyWith<$Res> {
  factory $ArchivedContentModelCopyWith(ArchivedContentModel value,
          $Res Function(ArchivedContentModel) then) =
      _$ArchivedContentModelCopyWithImpl<$Res, ArchivedContentModel>;
  @useResult
  $Res call(
      {String id,
      String url,
      String platform,
      @JsonKey(name: 'content_type') String contentType,
      String? title,
      String? author,
      @JsonKey(name: 'published_at') String? publishedAt,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String? language,
      String? summary,
      @JsonKey(name: 'keywords_main') List<String> keywordsMain,
      @JsonKey(name: 'keywords_sub') List<String> keywordsSub,
      @JsonKey(name: 'named_entities') List<String> namedEntities,
      @JsonKey(name: 'topic_categories') List<String> topicCategories,
      String? sentiment,
      List<String> todos,
      List<String> insights,
      @JsonKey(name: 'type_specific_data')
      Map<String, dynamic>? typeSpecificData,
      @JsonKey(name: 'link_analyzer_id') String? linkAnalyzerId,
      @JsonKey(name: 'archived_at') String archivedAt});
}

/// @nodoc
class _$ArchivedContentModelCopyWithImpl<$Res,
        $Val extends ArchivedContentModel>
    implements $ArchivedContentModelCopyWith<$Res> {
  _$ArchivedContentModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? url = null,
    Object? platform = null,
    Object? contentType = null,
    Object? title = freezed,
    Object? author = freezed,
    Object? publishedAt = freezed,
    Object? thumbnailUrl = freezed,
    Object? language = freezed,
    Object? summary = freezed,
    Object? keywordsMain = null,
    Object? keywordsSub = null,
    Object? namedEntities = null,
    Object? topicCategories = null,
    Object? sentiment = freezed,
    Object? todos = null,
    Object? insights = null,
    Object? typeSpecificData = freezed,
    Object? linkAnalyzerId = freezed,
    Object? archivedAt = null,
  }) {
    return _then(_value.copyWith(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      url: null == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String,
      platform: null == platform
          ? _value.platform
          : platform // ignore: cast_nullable_to_non_nullable
              as String,
      contentType: null == contentType
          ? _value.contentType
          : contentType // ignore: cast_nullable_to_non_nullable
              as String,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      author: freezed == author
          ? _value.author
          : author // ignore: cast_nullable_to_non_nullable
              as String?,
      publishedAt: freezed == publishedAt
          ? _value.publishedAt
          : publishedAt // ignore: cast_nullable_to_non_nullable
              as String?,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      language: freezed == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String?,
      summary: freezed == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String?,
      keywordsMain: null == keywordsMain
          ? _value.keywordsMain
          : keywordsMain // ignore: cast_nullable_to_non_nullable
              as List<String>,
      keywordsSub: null == keywordsSub
          ? _value.keywordsSub
          : keywordsSub // ignore: cast_nullable_to_non_nullable
              as List<String>,
      namedEntities: null == namedEntities
          ? _value.namedEntities
          : namedEntities // ignore: cast_nullable_to_non_nullable
              as List<String>,
      topicCategories: null == topicCategories
          ? _value.topicCategories
          : topicCategories // ignore: cast_nullable_to_non_nullable
              as List<String>,
      sentiment: freezed == sentiment
          ? _value.sentiment
          : sentiment // ignore: cast_nullable_to_non_nullable
              as String?,
      todos: null == todos
          ? _value.todos
          : todos // ignore: cast_nullable_to_non_nullable
              as List<String>,
      insights: null == insights
          ? _value.insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
      typeSpecificData: freezed == typeSpecificData
          ? _value.typeSpecificData
          : typeSpecificData // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      linkAnalyzerId: freezed == linkAnalyzerId
          ? _value.linkAnalyzerId
          : linkAnalyzerId // ignore: cast_nullable_to_non_nullable
              as String?,
      archivedAt: null == archivedAt
          ? _value.archivedAt
          : archivedAt // ignore: cast_nullable_to_non_nullable
              as String,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ArchivedContentModelImplCopyWith<$Res>
    implements $ArchivedContentModelCopyWith<$Res> {
  factory _$$ArchivedContentModelImplCopyWith(_$ArchivedContentModelImpl value,
          $Res Function(_$ArchivedContentModelImpl) then) =
      __$$ArchivedContentModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String url,
      String platform,
      @JsonKey(name: 'content_type') String contentType,
      String? title,
      String? author,
      @JsonKey(name: 'published_at') String? publishedAt,
      @JsonKey(name: 'thumbnail_url') String? thumbnailUrl,
      String? language,
      String? summary,
      @JsonKey(name: 'keywords_main') List<String> keywordsMain,
      @JsonKey(name: 'keywords_sub') List<String> keywordsSub,
      @JsonKey(name: 'named_entities') List<String> namedEntities,
      @JsonKey(name: 'topic_categories') List<String> topicCategories,
      String? sentiment,
      List<String> todos,
      List<String> insights,
      @JsonKey(name: 'type_specific_data')
      Map<String, dynamic>? typeSpecificData,
      @JsonKey(name: 'link_analyzer_id') String? linkAnalyzerId,
      @JsonKey(name: 'archived_at') String archivedAt});
}

/// @nodoc
class __$$ArchivedContentModelImplCopyWithImpl<$Res>
    extends _$ArchivedContentModelCopyWithImpl<$Res, _$ArchivedContentModelImpl>
    implements _$$ArchivedContentModelImplCopyWith<$Res> {
  __$$ArchivedContentModelImplCopyWithImpl(_$ArchivedContentModelImpl _value,
      $Res Function(_$ArchivedContentModelImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? url = null,
    Object? platform = null,
    Object? contentType = null,
    Object? title = freezed,
    Object? author = freezed,
    Object? publishedAt = freezed,
    Object? thumbnailUrl = freezed,
    Object? language = freezed,
    Object? summary = freezed,
    Object? keywordsMain = null,
    Object? keywordsSub = null,
    Object? namedEntities = null,
    Object? topicCategories = null,
    Object? sentiment = freezed,
    Object? todos = null,
    Object? insights = null,
    Object? typeSpecificData = freezed,
    Object? linkAnalyzerId = freezed,
    Object? archivedAt = null,
  }) {
    return _then(_$ArchivedContentModelImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      url: null == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String,
      platform: null == platform
          ? _value.platform
          : platform // ignore: cast_nullable_to_non_nullable
              as String,
      contentType: null == contentType
          ? _value.contentType
          : contentType // ignore: cast_nullable_to_non_nullable
              as String,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      author: freezed == author
          ? _value.author
          : author // ignore: cast_nullable_to_non_nullable
              as String?,
      publishedAt: freezed == publishedAt
          ? _value.publishedAt
          : publishedAt // ignore: cast_nullable_to_non_nullable
              as String?,
      thumbnailUrl: freezed == thumbnailUrl
          ? _value.thumbnailUrl
          : thumbnailUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      language: freezed == language
          ? _value.language
          : language // ignore: cast_nullable_to_non_nullable
              as String?,
      summary: freezed == summary
          ? _value.summary
          : summary // ignore: cast_nullable_to_non_nullable
              as String?,
      keywordsMain: null == keywordsMain
          ? _value._keywordsMain
          : keywordsMain // ignore: cast_nullable_to_non_nullable
              as List<String>,
      keywordsSub: null == keywordsSub
          ? _value._keywordsSub
          : keywordsSub // ignore: cast_nullable_to_non_nullable
              as List<String>,
      namedEntities: null == namedEntities
          ? _value._namedEntities
          : namedEntities // ignore: cast_nullable_to_non_nullable
              as List<String>,
      topicCategories: null == topicCategories
          ? _value._topicCategories
          : topicCategories // ignore: cast_nullable_to_non_nullable
              as List<String>,
      sentiment: freezed == sentiment
          ? _value.sentiment
          : sentiment // ignore: cast_nullable_to_non_nullable
              as String?,
      todos: null == todos
          ? _value._todos
          : todos // ignore: cast_nullable_to_non_nullable
              as List<String>,
      insights: null == insights
          ? _value._insights
          : insights // ignore: cast_nullable_to_non_nullable
              as List<String>,
      typeSpecificData: freezed == typeSpecificData
          ? _value._typeSpecificData
          : typeSpecificData // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      linkAnalyzerId: freezed == linkAnalyzerId
          ? _value.linkAnalyzerId
          : linkAnalyzerId // ignore: cast_nullable_to_non_nullable
              as String?,
      archivedAt: null == archivedAt
          ? _value.archivedAt
          : archivedAt // ignore: cast_nullable_to_non_nullable
              as String,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ArchivedContentModelImpl implements _ArchivedContentModel {
  const _$ArchivedContentModelImpl(
      {required this.id,
      required this.url,
      required this.platform,
      @JsonKey(name: 'content_type') required this.contentType,
      this.title,
      this.author,
      @JsonKey(name: 'published_at') this.publishedAt,
      @JsonKey(name: 'thumbnail_url') this.thumbnailUrl,
      this.language,
      this.summary,
      @JsonKey(name: 'keywords_main')
      final List<String> keywordsMain = const [],
      @JsonKey(name: 'keywords_sub') final List<String> keywordsSub = const [],
      @JsonKey(name: 'named_entities')
      final List<String> namedEntities = const [],
      @JsonKey(name: 'topic_categories')
      final List<String> topicCategories = const [],
      this.sentiment,
      final List<String> todos = const [],
      final List<String> insights = const [],
      @JsonKey(name: 'type_specific_data')
      final Map<String, dynamic>? typeSpecificData,
      @JsonKey(name: 'link_analyzer_id') this.linkAnalyzerId,
      @JsonKey(name: 'archived_at') required this.archivedAt})
      : _keywordsMain = keywordsMain,
        _keywordsSub = keywordsSub,
        _namedEntities = namedEntities,
        _topicCategories = topicCategories,
        _todos = todos,
        _insights = insights,
        _typeSpecificData = typeSpecificData;

  factory _$ArchivedContentModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ArchivedContentModelImplFromJson(json);

  @override
  final String id;
  @override
  final String url;
  @override
  final String platform;
  @override
  @JsonKey(name: 'content_type')
  final String contentType;
  @override
  final String? title;
  @override
  final String? author;
  @override
  @JsonKey(name: 'published_at')
  final String? publishedAt;
  @override
  @JsonKey(name: 'thumbnail_url')
  final String? thumbnailUrl;
  @override
  final String? language;
  @override
  final String? summary;
  final List<String> _keywordsMain;
  @override
  @JsonKey(name: 'keywords_main')
  List<String> get keywordsMain {
    if (_keywordsMain is EqualUnmodifiableListView) return _keywordsMain;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keywordsMain);
  }

  final List<String> _keywordsSub;
  @override
  @JsonKey(name: 'keywords_sub')
  List<String> get keywordsSub {
    if (_keywordsSub is EqualUnmodifiableListView) return _keywordsSub;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keywordsSub);
  }

  final List<String> _namedEntities;
  @override
  @JsonKey(name: 'named_entities')
  List<String> get namedEntities {
    if (_namedEntities is EqualUnmodifiableListView) return _namedEntities;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_namedEntities);
  }

  final List<String> _topicCategories;
  @override
  @JsonKey(name: 'topic_categories')
  List<String> get topicCategories {
    if (_topicCategories is EqualUnmodifiableListView) return _topicCategories;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topicCategories);
  }

  @override
  final String? sentiment;
  final List<String> _todos;
  @override
  @JsonKey()
  List<String> get todos {
    if (_todos is EqualUnmodifiableListView) return _todos;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_todos);
  }

  final List<String> _insights;
  @override
  @JsonKey()
  List<String> get insights {
    if (_insights is EqualUnmodifiableListView) return _insights;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_insights);
  }

  final Map<String, dynamic>? _typeSpecificData;
  @override
  @JsonKey(name: 'type_specific_data')
  Map<String, dynamic>? get typeSpecificData {
    final value = _typeSpecificData;
    if (value == null) return null;
    if (_typeSpecificData is EqualUnmodifiableMapView) return _typeSpecificData;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  @override
  @JsonKey(name: 'link_analyzer_id')
  final String? linkAnalyzerId;
  @override
  @JsonKey(name: 'archived_at')
  final String archivedAt;

  @override
  String toString() {
    return 'ArchivedContentModel(id: $id, url: $url, platform: $platform, contentType: $contentType, title: $title, author: $author, publishedAt: $publishedAt, thumbnailUrl: $thumbnailUrl, language: $language, summary: $summary, keywordsMain: $keywordsMain, keywordsSub: $keywordsSub, namedEntities: $namedEntities, topicCategories: $topicCategories, sentiment: $sentiment, todos: $todos, insights: $insights, typeSpecificData: $typeSpecificData, linkAnalyzerId: $linkAnalyzerId, archivedAt: $archivedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchivedContentModelImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.url, url) || other.url == url) &&
            (identical(other.platform, platform) ||
                other.platform == platform) &&
            (identical(other.contentType, contentType) ||
                other.contentType == contentType) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.author, author) || other.author == author) &&
            (identical(other.publishedAt, publishedAt) ||
                other.publishedAt == publishedAt) &&
            (identical(other.thumbnailUrl, thumbnailUrl) ||
                other.thumbnailUrl == thumbnailUrl) &&
            (identical(other.language, language) ||
                other.language == language) &&
            (identical(other.summary, summary) || other.summary == summary) &&
            const DeepCollectionEquality()
                .equals(other._keywordsMain, _keywordsMain) &&
            const DeepCollectionEquality()
                .equals(other._keywordsSub, _keywordsSub) &&
            const DeepCollectionEquality()
                .equals(other._namedEntities, _namedEntities) &&
            const DeepCollectionEquality()
                .equals(other._topicCategories, _topicCategories) &&
            (identical(other.sentiment, sentiment) ||
                other.sentiment == sentiment) &&
            const DeepCollectionEquality().equals(other._todos, _todos) &&
            const DeepCollectionEquality().equals(other._insights, _insights) &&
            const DeepCollectionEquality()
                .equals(other._typeSpecificData, _typeSpecificData) &&
            (identical(other.linkAnalyzerId, linkAnalyzerId) ||
                other.linkAnalyzerId == linkAnalyzerId) &&
            (identical(other.archivedAt, archivedAt) ||
                other.archivedAt == archivedAt));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hashAll([
        runtimeType,
        id,
        url,
        platform,
        contentType,
        title,
        author,
        publishedAt,
        thumbnailUrl,
        language,
        summary,
        const DeepCollectionEquality().hash(_keywordsMain),
        const DeepCollectionEquality().hash(_keywordsSub),
        const DeepCollectionEquality().hash(_namedEntities),
        const DeepCollectionEquality().hash(_topicCategories),
        sentiment,
        const DeepCollectionEquality().hash(_todos),
        const DeepCollectionEquality().hash(_insights),
        const DeepCollectionEquality().hash(_typeSpecificData),
        linkAnalyzerId,
        archivedAt
      ]);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ArchivedContentModelImplCopyWith<_$ArchivedContentModelImpl>
      get copyWith =>
          __$$ArchivedContentModelImplCopyWithImpl<_$ArchivedContentModelImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ArchivedContentModelImplToJson(
      this,
    );
  }
}

abstract class _ArchivedContentModel implements ArchivedContentModel {
  const factory _ArchivedContentModel(
          {required final String id,
          required final String url,
          required final String platform,
          @JsonKey(name: 'content_type') required final String contentType,
          final String? title,
          final String? author,
          @JsonKey(name: 'published_at') final String? publishedAt,
          @JsonKey(name: 'thumbnail_url') final String? thumbnailUrl,
          final String? language,
          final String? summary,
          @JsonKey(name: 'keywords_main') final List<String> keywordsMain,
          @JsonKey(name: 'keywords_sub') final List<String> keywordsSub,
          @JsonKey(name: 'named_entities') final List<String> namedEntities,
          @JsonKey(name: 'topic_categories') final List<String> topicCategories,
          final String? sentiment,
          final List<String> todos,
          final List<String> insights,
          @JsonKey(name: 'type_specific_data')
          final Map<String, dynamic>? typeSpecificData,
          @JsonKey(name: 'link_analyzer_id') final String? linkAnalyzerId,
          @JsonKey(name: 'archived_at') required final String archivedAt}) =
      _$ArchivedContentModelImpl;

  factory _ArchivedContentModel.fromJson(Map<String, dynamic> json) =
      _$ArchivedContentModelImpl.fromJson;

  @override
  String get id;
  @override
  String get url;
  @override
  String get platform;
  @override
  @JsonKey(name: 'content_type')
  String get contentType;
  @override
  String? get title;
  @override
  String? get author;
  @override
  @JsonKey(name: 'published_at')
  String? get publishedAt;
  @override
  @JsonKey(name: 'thumbnail_url')
  String? get thumbnailUrl;
  @override
  String? get language;
  @override
  String? get summary;
  @override
  @JsonKey(name: 'keywords_main')
  List<String> get keywordsMain;
  @override
  @JsonKey(name: 'keywords_sub')
  List<String> get keywordsSub;
  @override
  @JsonKey(name: 'named_entities')
  List<String> get namedEntities;
  @override
  @JsonKey(name: 'topic_categories')
  List<String> get topicCategories;
  @override
  String? get sentiment;
  @override
  List<String> get todos;
  @override
  List<String> get insights;
  @override
  @JsonKey(name: 'type_specific_data')
  Map<String, dynamic>? get typeSpecificData;
  @override
  @JsonKey(name: 'link_analyzer_id')
  String? get linkAnalyzerId;
  @override
  @JsonKey(name: 'archived_at')
  String get archivedAt;
  @override
  @JsonKey(ignore: true)
  _$$ArchivedContentModelImplCopyWith<_$ArchivedContentModelImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ArchiveListModel _$ArchiveListModelFromJson(Map<String, dynamic> json) {
  return _ArchiveListModel.fromJson(json);
}

/// @nodoc
mixin _$ArchiveListModel {
  List<ArchivedContentModel> get items => throw _privateConstructorUsedError;
  int get total => throw _privateConstructorUsedError;
  int get page => throw _privateConstructorUsedError;
  @JsonKey(name: 'page_size')
  int get pageSize => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ArchiveListModelCopyWith<ArchiveListModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchiveListModelCopyWith<$Res> {
  factory $ArchiveListModelCopyWith(
          ArchiveListModel value, $Res Function(ArchiveListModel) then) =
      _$ArchiveListModelCopyWithImpl<$Res, ArchiveListModel>;
  @useResult
  $Res call(
      {List<ArchivedContentModel> items,
      int total,
      int page,
      @JsonKey(name: 'page_size') int pageSize});
}

/// @nodoc
class _$ArchiveListModelCopyWithImpl<$Res, $Val extends ArchiveListModel>
    implements $ArchiveListModelCopyWith<$Res> {
  _$ArchiveListModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? total = null,
    Object? page = null,
    Object? pageSize = null,
  }) {
    return _then(_value.copyWith(
      items: null == items
          ? _value.items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ArchivedContentModel>,
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      page: null == page
          ? _value.page
          : page // ignore: cast_nullable_to_non_nullable
              as int,
      pageSize: null == pageSize
          ? _value.pageSize
          : pageSize // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ArchiveListModelImplCopyWith<$Res>
    implements $ArchiveListModelCopyWith<$Res> {
  factory _$$ArchiveListModelImplCopyWith(_$ArchiveListModelImpl value,
          $Res Function(_$ArchiveListModelImpl) then) =
      __$$ArchiveListModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<ArchivedContentModel> items,
      int total,
      int page,
      @JsonKey(name: 'page_size') int pageSize});
}

/// @nodoc
class __$$ArchiveListModelImplCopyWithImpl<$Res>
    extends _$ArchiveListModelCopyWithImpl<$Res, _$ArchiveListModelImpl>
    implements _$$ArchiveListModelImplCopyWith<$Res> {
  __$$ArchiveListModelImplCopyWithImpl(_$ArchiveListModelImpl _value,
      $Res Function(_$ArchiveListModelImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? total = null,
    Object? page = null,
    Object? pageSize = null,
  }) {
    return _then(_$ArchiveListModelImpl(
      items: null == items
          ? _value._items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ArchivedContentModel>,
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      page: null == page
          ? _value.page
          : page // ignore: cast_nullable_to_non_nullable
              as int,
      pageSize: null == pageSize
          ? _value.pageSize
          : pageSize // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ArchiveListModelImpl implements _ArchiveListModel {
  const _$ArchiveListModelImpl(
      {required final List<ArchivedContentModel> items,
      required this.total,
      required this.page,
      @JsonKey(name: 'page_size') required this.pageSize})
      : _items = items;

  factory _$ArchiveListModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ArchiveListModelImplFromJson(json);

  final List<ArchivedContentModel> _items;
  @override
  List<ArchivedContentModel> get items {
    if (_items is EqualUnmodifiableListView) return _items;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_items);
  }

  @override
  final int total;
  @override
  final int page;
  @override
  @JsonKey(name: 'page_size')
  final int pageSize;

  @override
  String toString() {
    return 'ArchiveListModel(items: $items, total: $total, page: $page, pageSize: $pageSize)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchiveListModelImpl &&
            const DeepCollectionEquality().equals(other._items, _items) &&
            (identical(other.total, total) || other.total == total) &&
            (identical(other.page, page) || other.page == page) &&
            (identical(other.pageSize, pageSize) ||
                other.pageSize == pageSize));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType,
      const DeepCollectionEquality().hash(_items), total, page, pageSize);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ArchiveListModelImplCopyWith<_$ArchiveListModelImpl> get copyWith =>
      __$$ArchiveListModelImplCopyWithImpl<_$ArchiveListModelImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ArchiveListModelImplToJson(
      this,
    );
  }
}

abstract class _ArchiveListModel implements ArchiveListModel {
  const factory _ArchiveListModel(
          {required final List<ArchivedContentModel> items,
          required final int total,
          required final int page,
          @JsonKey(name: 'page_size') required final int pageSize}) =
      _$ArchiveListModelImpl;

  factory _ArchiveListModel.fromJson(Map<String, dynamic> json) =
      _$ArchiveListModelImpl.fromJson;

  @override
  List<ArchivedContentModel> get items;
  @override
  int get total;
  @override
  int get page;
  @override
  @JsonKey(name: 'page_size')
  int get pageSize;
  @override
  @JsonKey(ignore: true)
  _$$ArchiveListModelImplCopyWith<_$ArchiveListModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
