// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'archived_content.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$ArchivedContent {
  String get id => throw _privateConstructorUsedError;
  String get url => throw _privateConstructorUsedError;
  Platform get platform => throw _privateConstructorUsedError;
  String get contentType => throw _privateConstructorUsedError; // 메타데이터
  String? get title => throw _privateConstructorUsedError;
  String? get author => throw _privateConstructorUsedError;
  DateTime? get publishedAt => throw _privateConstructorUsedError;
  String? get thumbnailUrl => throw _privateConstructorUsedError;
  String? get language => throw _privateConstructorUsedError; // 분석 공통
  String? get summary => throw _privateConstructorUsedError;
  List<String> get keywordsMain => throw _privateConstructorUsedError;
  List<String> get keywordsSub => throw _privateConstructorUsedError;
  List<String> get namedEntities => throw _privateConstructorUsedError;
  List<String> get topicCategories => throw _privateConstructorUsedError;
  Sentiment? get sentiment => throw _privateConstructorUsedError;
  List<String> get todos => throw _privateConstructorUsedError;
  List<String> get insights =>
      throw _privateConstructorUsedError; // 타입별 추가 데이터 (content_type에 따라 구조 상이)
  Map<String, dynamic>? get typeSpecificData =>
      throw _privateConstructorUsedError; // 앱 메타
  String? get linkAnalyzerId => throw _privateConstructorUsedError;
  DateTime get archivedAt => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $ArchivedContentCopyWith<ArchivedContent> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchivedContentCopyWith<$Res> {
  factory $ArchivedContentCopyWith(
          ArchivedContent value, $Res Function(ArchivedContent) then) =
      _$ArchivedContentCopyWithImpl<$Res, ArchivedContent>;
  @useResult
  $Res call(
      {String id,
      String url,
      Platform platform,
      String contentType,
      String? title,
      String? author,
      DateTime? publishedAt,
      String? thumbnailUrl,
      String? language,
      String? summary,
      List<String> keywordsMain,
      List<String> keywordsSub,
      List<String> namedEntities,
      List<String> topicCategories,
      Sentiment? sentiment,
      List<String> todos,
      List<String> insights,
      Map<String, dynamic>? typeSpecificData,
      String? linkAnalyzerId,
      DateTime archivedAt});
}

/// @nodoc
class _$ArchivedContentCopyWithImpl<$Res, $Val extends ArchivedContent>
    implements $ArchivedContentCopyWith<$Res> {
  _$ArchivedContentCopyWithImpl(this._value, this._then);

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
              as Platform,
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
              as DateTime?,
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
              as Sentiment?,
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
              as DateTime,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ArchivedContentImplCopyWith<$Res>
    implements $ArchivedContentCopyWith<$Res> {
  factory _$$ArchivedContentImplCopyWith(_$ArchivedContentImpl value,
          $Res Function(_$ArchivedContentImpl) then) =
      __$$ArchivedContentImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String url,
      Platform platform,
      String contentType,
      String? title,
      String? author,
      DateTime? publishedAt,
      String? thumbnailUrl,
      String? language,
      String? summary,
      List<String> keywordsMain,
      List<String> keywordsSub,
      List<String> namedEntities,
      List<String> topicCategories,
      Sentiment? sentiment,
      List<String> todos,
      List<String> insights,
      Map<String, dynamic>? typeSpecificData,
      String? linkAnalyzerId,
      DateTime archivedAt});
}

/// @nodoc
class __$$ArchivedContentImplCopyWithImpl<$Res>
    extends _$ArchivedContentCopyWithImpl<$Res, _$ArchivedContentImpl>
    implements _$$ArchivedContentImplCopyWith<$Res> {
  __$$ArchivedContentImplCopyWithImpl(
      _$ArchivedContentImpl _value, $Res Function(_$ArchivedContentImpl) _then)
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
    return _then(_$ArchivedContentImpl(
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
              as Platform,
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
              as DateTime?,
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
              as Sentiment?,
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
              as DateTime,
    ));
  }
}

/// @nodoc

class _$ArchivedContentImpl implements _ArchivedContent {
  const _$ArchivedContentImpl(
      {required this.id,
      required this.url,
      required this.platform,
      required this.contentType,
      this.title,
      this.author,
      this.publishedAt,
      this.thumbnailUrl,
      this.language,
      this.summary,
      final List<String> keywordsMain = const [],
      final List<String> keywordsSub = const [],
      final List<String> namedEntities = const [],
      final List<String> topicCategories = const [],
      this.sentiment,
      final List<String> todos = const [],
      final List<String> insights = const [],
      final Map<String, dynamic>? typeSpecificData,
      this.linkAnalyzerId,
      required this.archivedAt})
      : _keywordsMain = keywordsMain,
        _keywordsSub = keywordsSub,
        _namedEntities = namedEntities,
        _topicCategories = topicCategories,
        _todos = todos,
        _insights = insights,
        _typeSpecificData = typeSpecificData;

  @override
  final String id;
  @override
  final String url;
  @override
  final Platform platform;
  @override
  final String contentType;
// 메타데이터
  @override
  final String? title;
  @override
  final String? author;
  @override
  final DateTime? publishedAt;
  @override
  final String? thumbnailUrl;
  @override
  final String? language;
// 분석 공통
  @override
  final String? summary;
  final List<String> _keywordsMain;
  @override
  @JsonKey()
  List<String> get keywordsMain {
    if (_keywordsMain is EqualUnmodifiableListView) return _keywordsMain;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keywordsMain);
  }

  final List<String> _keywordsSub;
  @override
  @JsonKey()
  List<String> get keywordsSub {
    if (_keywordsSub is EqualUnmodifiableListView) return _keywordsSub;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_keywordsSub);
  }

  final List<String> _namedEntities;
  @override
  @JsonKey()
  List<String> get namedEntities {
    if (_namedEntities is EqualUnmodifiableListView) return _namedEntities;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_namedEntities);
  }

  final List<String> _topicCategories;
  @override
  @JsonKey()
  List<String> get topicCategories {
    if (_topicCategories is EqualUnmodifiableListView) return _topicCategories;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_topicCategories);
  }

  @override
  final Sentiment? sentiment;
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

// 타입별 추가 데이터 (content_type에 따라 구조 상이)
  final Map<String, dynamic>? _typeSpecificData;
// 타입별 추가 데이터 (content_type에 따라 구조 상이)
  @override
  Map<String, dynamic>? get typeSpecificData {
    final value = _typeSpecificData;
    if (value == null) return null;
    if (_typeSpecificData is EqualUnmodifiableMapView) return _typeSpecificData;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

// 앱 메타
  @override
  final String? linkAnalyzerId;
  @override
  final DateTime archivedAt;

  @override
  String toString() {
    return 'ArchivedContent(id: $id, url: $url, platform: $platform, contentType: $contentType, title: $title, author: $author, publishedAt: $publishedAt, thumbnailUrl: $thumbnailUrl, language: $language, summary: $summary, keywordsMain: $keywordsMain, keywordsSub: $keywordsSub, namedEntities: $namedEntities, topicCategories: $topicCategories, sentiment: $sentiment, todos: $todos, insights: $insights, typeSpecificData: $typeSpecificData, linkAnalyzerId: $linkAnalyzerId, archivedAt: $archivedAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchivedContentImpl &&
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
  _$$ArchivedContentImplCopyWith<_$ArchivedContentImpl> get copyWith =>
      __$$ArchivedContentImplCopyWithImpl<_$ArchivedContentImpl>(
          this, _$identity);
}

abstract class _ArchivedContent implements ArchivedContent {
  const factory _ArchivedContent(
      {required final String id,
      required final String url,
      required final Platform platform,
      required final String contentType,
      final String? title,
      final String? author,
      final DateTime? publishedAt,
      final String? thumbnailUrl,
      final String? language,
      final String? summary,
      final List<String> keywordsMain,
      final List<String> keywordsSub,
      final List<String> namedEntities,
      final List<String> topicCategories,
      final Sentiment? sentiment,
      final List<String> todos,
      final List<String> insights,
      final Map<String, dynamic>? typeSpecificData,
      final String? linkAnalyzerId,
      required final DateTime archivedAt}) = _$ArchivedContentImpl;

  @override
  String get id;
  @override
  String get url;
  @override
  Platform get platform;
  @override
  String get contentType;
  @override // 메타데이터
  String? get title;
  @override
  String? get author;
  @override
  DateTime? get publishedAt;
  @override
  String? get thumbnailUrl;
  @override
  String? get language;
  @override // 분석 공통
  String? get summary;
  @override
  List<String> get keywordsMain;
  @override
  List<String> get keywordsSub;
  @override
  List<String> get namedEntities;
  @override
  List<String> get topicCategories;
  @override
  Sentiment? get sentiment;
  @override
  List<String> get todos;
  @override
  List<String> get insights;
  @override // 타입별 추가 데이터 (content_type에 따라 구조 상이)
  Map<String, dynamic>? get typeSpecificData;
  @override // 앱 메타
  String? get linkAnalyzerId;
  @override
  DateTime get archivedAt;
  @override
  @JsonKey(ignore: true)
  _$$ArchivedContentImplCopyWith<_$ArchivedContentImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ArchiveList {
  List<ArchivedContent> get items => throw _privateConstructorUsedError;
  int get total => throw _privateConstructorUsedError;
  int get page => throw _privateConstructorUsedError;
  int get pageSize => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $ArchiveListCopyWith<ArchiveList> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchiveListCopyWith<$Res> {
  factory $ArchiveListCopyWith(
          ArchiveList value, $Res Function(ArchiveList) then) =
      _$ArchiveListCopyWithImpl<$Res, ArchiveList>;
  @useResult
  $Res call({List<ArchivedContent> items, int total, int page, int pageSize});
}

/// @nodoc
class _$ArchiveListCopyWithImpl<$Res, $Val extends ArchiveList>
    implements $ArchiveListCopyWith<$Res> {
  _$ArchiveListCopyWithImpl(this._value, this._then);

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
              as List<ArchivedContent>,
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
abstract class _$$ArchiveListImplCopyWith<$Res>
    implements $ArchiveListCopyWith<$Res> {
  factory _$$ArchiveListImplCopyWith(
          _$ArchiveListImpl value, $Res Function(_$ArchiveListImpl) then) =
      __$$ArchiveListImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({List<ArchivedContent> items, int total, int page, int pageSize});
}

/// @nodoc
class __$$ArchiveListImplCopyWithImpl<$Res>
    extends _$ArchiveListCopyWithImpl<$Res, _$ArchiveListImpl>
    implements _$$ArchiveListImplCopyWith<$Res> {
  __$$ArchiveListImplCopyWithImpl(
      _$ArchiveListImpl _value, $Res Function(_$ArchiveListImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? total = null,
    Object? page = null,
    Object? pageSize = null,
  }) {
    return _then(_$ArchiveListImpl(
      items: null == items
          ? _value._items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ArchivedContent>,
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

class _$ArchiveListImpl implements _ArchiveList {
  const _$ArchiveListImpl(
      {required final List<ArchivedContent> items,
      required this.total,
      required this.page,
      required this.pageSize})
      : _items = items;

  final List<ArchivedContent> _items;
  @override
  List<ArchivedContent> get items {
    if (_items is EqualUnmodifiableListView) return _items;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_items);
  }

  @override
  final int total;
  @override
  final int page;
  @override
  final int pageSize;

  @override
  String toString() {
    return 'ArchiveList(items: $items, total: $total, page: $page, pageSize: $pageSize)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchiveListImpl &&
            const DeepCollectionEquality().equals(other._items, _items) &&
            (identical(other.total, total) || other.total == total) &&
            (identical(other.page, page) || other.page == page) &&
            (identical(other.pageSize, pageSize) ||
                other.pageSize == pageSize));
  }

  @override
  int get hashCode => Object.hash(runtimeType,
      const DeepCollectionEquality().hash(_items), total, page, pageSize);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ArchiveListImplCopyWith<_$ArchiveListImpl> get copyWith =>
      __$$ArchiveListImplCopyWithImpl<_$ArchiveListImpl>(this, _$identity);
}

abstract class _ArchiveList implements ArchiveList {
  const factory _ArchiveList(
      {required final List<ArchivedContent> items,
      required final int total,
      required final int page,
      required final int pageSize}) = _$ArchiveListImpl;

  @override
  List<ArchivedContent> get items;
  @override
  int get total;
  @override
  int get page;
  @override
  int get pageSize;
  @override
  @JsonKey(ignore: true)
  _$$ArchiveListImplCopyWith<_$ArchiveListImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
