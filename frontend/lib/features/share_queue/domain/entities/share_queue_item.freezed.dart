// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'share_queue_item.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

ShareQueueItem _$ShareQueueItemFromJson(Map<String, dynamic> json) {
  return _ShareQueueItem.fromJson(json);
}

/// @nodoc
mixin _$ShareQueueItem {
  /// 고유 ID (UUID)
  String get id => throw _privateConstructorUsedError;

  /// 원본 URL
  String get url => throw _privateConstructorUsedError;

  /// 페이지 제목 (선택)
  String? get title => throw _privateConstructorUsedError;

  /// 공유 시각
  DateTime get sharedAt => throw _privateConstructorUsedError;

  /// 현재 상태
  ShareQueueStatus get status => throw _privateConstructorUsedError;

  /// 분석 결과 (완료 시)
  ShareQueueAnalysisResult? get result => throw _privateConstructorUsedError;

  /// 에러 메시지 (실패 시)
  String? get errorMessage => throw _privateConstructorUsedError;

  /// 재시도 횟수
  int get retryCount => throw _privateConstructorUsedError;

  /// 플랫폼 (instagram, naver_blog, youtube)
  String? get platform => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ShareQueueItemCopyWith<ShareQueueItem> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ShareQueueItemCopyWith<$Res> {
  factory $ShareQueueItemCopyWith(
          ShareQueueItem value, $Res Function(ShareQueueItem) then) =
      _$ShareQueueItemCopyWithImpl<$Res, ShareQueueItem>;
  @useResult
  $Res call(
      {String id,
      String url,
      String? title,
      DateTime sharedAt,
      ShareQueueStatus status,
      ShareQueueAnalysisResult? result,
      String? errorMessage,
      int retryCount,
      String? platform});

  $ShareQueueAnalysisResultCopyWith<$Res>? get result;
}

/// @nodoc
class _$ShareQueueItemCopyWithImpl<$Res, $Val extends ShareQueueItem>
    implements $ShareQueueItemCopyWith<$Res> {
  _$ShareQueueItemCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? url = null,
    Object? title = freezed,
    Object? sharedAt = null,
    Object? status = null,
    Object? result = freezed,
    Object? errorMessage = freezed,
    Object? retryCount = null,
    Object? platform = freezed,
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
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      sharedAt: null == sharedAt
          ? _value.sharedAt
          : sharedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ShareQueueStatus,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as ShareQueueAnalysisResult?,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
      retryCount: null == retryCount
          ? _value.retryCount
          : retryCount // ignore: cast_nullable_to_non_nullable
              as int,
      platform: freezed == platform
          ? _value.platform
          : platform // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $ShareQueueAnalysisResultCopyWith<$Res>? get result {
    if (_value.result == null) {
      return null;
    }

    return $ShareQueueAnalysisResultCopyWith<$Res>(_value.result!, (value) {
      return _then(_value.copyWith(result: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ShareQueueItemImplCopyWith<$Res>
    implements $ShareQueueItemCopyWith<$Res> {
  factory _$$ShareQueueItemImplCopyWith(_$ShareQueueItemImpl value,
          $Res Function(_$ShareQueueItemImpl) then) =
      __$$ShareQueueItemImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String id,
      String url,
      String? title,
      DateTime sharedAt,
      ShareQueueStatus status,
      ShareQueueAnalysisResult? result,
      String? errorMessage,
      int retryCount,
      String? platform});

  @override
  $ShareQueueAnalysisResultCopyWith<$Res>? get result;
}

/// @nodoc
class __$$ShareQueueItemImplCopyWithImpl<$Res>
    extends _$ShareQueueItemCopyWithImpl<$Res, _$ShareQueueItemImpl>
    implements _$$ShareQueueItemImplCopyWith<$Res> {
  __$$ShareQueueItemImplCopyWithImpl(
      _$ShareQueueItemImpl _value, $Res Function(_$ShareQueueItemImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? id = null,
    Object? url = null,
    Object? title = freezed,
    Object? sharedAt = null,
    Object? status = null,
    Object? result = freezed,
    Object? errorMessage = freezed,
    Object? retryCount = null,
    Object? platform = freezed,
  }) {
    return _then(_$ShareQueueItemImpl(
      id: null == id
          ? _value.id
          : id // ignore: cast_nullable_to_non_nullable
              as String,
      url: null == url
          ? _value.url
          : url // ignore: cast_nullable_to_non_nullable
              as String,
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      sharedAt: null == sharedAt
          ? _value.sharedAt
          : sharedAt // ignore: cast_nullable_to_non_nullable
              as DateTime,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as ShareQueueStatus,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as ShareQueueAnalysisResult?,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
      retryCount: null == retryCount
          ? _value.retryCount
          : retryCount // ignore: cast_nullable_to_non_nullable
              as int,
      platform: freezed == platform
          ? _value.platform
          : platform // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ShareQueueItemImpl implements _ShareQueueItem {
  const _$ShareQueueItemImpl(
      {required this.id,
      required this.url,
      this.title,
      required this.sharedAt,
      this.status = ShareQueueStatus.pending,
      this.result,
      this.errorMessage,
      this.retryCount = 0,
      this.platform});

  factory _$ShareQueueItemImpl.fromJson(Map<String, dynamic> json) =>
      _$$ShareQueueItemImplFromJson(json);

  /// 고유 ID (UUID)
  @override
  final String id;

  /// 원본 URL
  @override
  final String url;

  /// 페이지 제목 (선택)
  @override
  final String? title;

  /// 공유 시각
  @override
  final DateTime sharedAt;

  /// 현재 상태
  @override
  @JsonKey()
  final ShareQueueStatus status;

  /// 분석 결과 (완료 시)
  @override
  final ShareQueueAnalysisResult? result;

  /// 에러 메시지 (실패 시)
  @override
  final String? errorMessage;

  /// 재시도 횟수
  @override
  @JsonKey()
  final int retryCount;

  /// 플랫폼 (instagram, naver_blog, youtube)
  @override
  final String? platform;

  @override
  String toString() {
    return 'ShareQueueItem(id: $id, url: $url, title: $title, sharedAt: $sharedAt, status: $status, result: $result, errorMessage: $errorMessage, retryCount: $retryCount, platform: $platform)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ShareQueueItemImpl &&
            (identical(other.id, id) || other.id == id) &&
            (identical(other.url, url) || other.url == url) &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.sharedAt, sharedAt) ||
                other.sharedAt == sharedAt) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.result, result) || other.result == result) &&
            (identical(other.errorMessage, errorMessage) ||
                other.errorMessage == errorMessage) &&
            (identical(other.retryCount, retryCount) ||
                other.retryCount == retryCount) &&
            (identical(other.platform, platform) ||
                other.platform == platform));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, id, url, title, sharedAt, status,
      result, errorMessage, retryCount, platform);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ShareQueueItemImplCopyWith<_$ShareQueueItemImpl> get copyWith =>
      __$$ShareQueueItemImplCopyWithImpl<_$ShareQueueItemImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ShareQueueItemImplToJson(
      this,
    );
  }
}

abstract class _ShareQueueItem implements ShareQueueItem {
  const factory _ShareQueueItem(
      {required final String id,
      required final String url,
      final String? title,
      required final DateTime sharedAt,
      final ShareQueueStatus status,
      final ShareQueueAnalysisResult? result,
      final String? errorMessage,
      final int retryCount,
      final String? platform}) = _$ShareQueueItemImpl;

  factory _ShareQueueItem.fromJson(Map<String, dynamic> json) =
      _$ShareQueueItemImpl.fromJson;

  @override

  /// 고유 ID (UUID)
  String get id;
  @override

  /// 원본 URL
  String get url;
  @override

  /// 페이지 제목 (선택)
  String? get title;
  @override

  /// 공유 시각
  DateTime get sharedAt;
  @override

  /// 현재 상태
  ShareQueueStatus get status;
  @override

  /// 분석 결과 (완료 시)
  ShareQueueAnalysisResult? get result;
  @override

  /// 에러 메시지 (실패 시)
  String? get errorMessage;
  @override

  /// 재시도 횟수
  int get retryCount;
  @override

  /// 플랫폼 (instagram, naver_blog, youtube)
  String? get platform;
  @override
  @JsonKey(ignore: true)
  _$$ShareQueueItemImplCopyWith<_$ShareQueueItemImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ShareQueueAnalysisResult _$ShareQueueAnalysisResultFromJson(
    Map<String, dynamic> json) {
  return _ShareQueueAnalysisResult.fromJson(json);
}

/// @nodoc
mixin _$ShareQueueAnalysisResult {
  /// 장소명
  String get placeName => throw _privateConstructorUsedError;

  /// 카테고리
  String get category => throw _privateConstructorUsedError;

  /// 주소
  String? get address => throw _privateConstructorUsedError;

  /// 이미지 URL
  String? get imageUrl => throw _privateConstructorUsedError;

  /// 신뢰도 점수 (0.0 ~ 1.0)
  double get confidence => throw _privateConstructorUsedError;

  /// 태그 목록
  List<String> get tags => throw _privateConstructorUsedError;

  /// 추출된 추가 정보
  Map<String, dynamic>? get extractedInfo => throw _privateConstructorUsedError;

  /// 원본 분석 ID (서버)
  String? get analysisId => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ShareQueueAnalysisResultCopyWith<ShareQueueAnalysisResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ShareQueueAnalysisResultCopyWith<$Res> {
  factory $ShareQueueAnalysisResultCopyWith(ShareQueueAnalysisResult value,
          $Res Function(ShareQueueAnalysisResult) then) =
      _$ShareQueueAnalysisResultCopyWithImpl<$Res, ShareQueueAnalysisResult>;
  @useResult
  $Res call(
      {String placeName,
      String category,
      String? address,
      String? imageUrl,
      double confidence,
      List<String> tags,
      Map<String, dynamic>? extractedInfo,
      String? analysisId});
}

/// @nodoc
class _$ShareQueueAnalysisResultCopyWithImpl<$Res,
        $Val extends ShareQueueAnalysisResult>
    implements $ShareQueueAnalysisResultCopyWith<$Res> {
  _$ShareQueueAnalysisResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeName = null,
    Object? category = null,
    Object? address = freezed,
    Object? imageUrl = freezed,
    Object? confidence = null,
    Object? tags = null,
    Object? extractedInfo = freezed,
    Object? analysisId = freezed,
  }) {
    return _then(_value.copyWith(
      placeName: null == placeName
          ? _value.placeName
          : placeName // ignore: cast_nullable_to_non_nullable
              as String,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      tags: null == tags
          ? _value.tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      extractedInfo: freezed == extractedInfo
          ? _value.extractedInfo
          : extractedInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      analysisId: freezed == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ShareQueueAnalysisResultImplCopyWith<$Res>
    implements $ShareQueueAnalysisResultCopyWith<$Res> {
  factory _$$ShareQueueAnalysisResultImplCopyWith(
          _$ShareQueueAnalysisResultImpl value,
          $Res Function(_$ShareQueueAnalysisResultImpl) then) =
      __$$ShareQueueAnalysisResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String placeName,
      String category,
      String? address,
      String? imageUrl,
      double confidence,
      List<String> tags,
      Map<String, dynamic>? extractedInfo,
      String? analysisId});
}

/// @nodoc
class __$$ShareQueueAnalysisResultImplCopyWithImpl<$Res>
    extends _$ShareQueueAnalysisResultCopyWithImpl<$Res,
        _$ShareQueueAnalysisResultImpl>
    implements _$$ShareQueueAnalysisResultImplCopyWith<$Res> {
  __$$ShareQueueAnalysisResultImplCopyWithImpl(
      _$ShareQueueAnalysisResultImpl _value,
      $Res Function(_$ShareQueueAnalysisResultImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeName = null,
    Object? category = null,
    Object? address = freezed,
    Object? imageUrl = freezed,
    Object? confidence = null,
    Object? tags = null,
    Object? extractedInfo = freezed,
    Object? analysisId = freezed,
  }) {
    return _then(_$ShareQueueAnalysisResultImpl(
      placeName: null == placeName
          ? _value.placeName
          : placeName // ignore: cast_nullable_to_non_nullable
              as String,
      category: null == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      imageUrl: freezed == imageUrl
          ? _value.imageUrl
          : imageUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      tags: null == tags
          ? _value._tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      extractedInfo: freezed == extractedInfo
          ? _value._extractedInfo
          : extractedInfo // ignore: cast_nullable_to_non_nullable
              as Map<String, dynamic>?,
      analysisId: freezed == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$ShareQueueAnalysisResultImpl implements _ShareQueueAnalysisResult {
  const _$ShareQueueAnalysisResultImpl(
      {required this.placeName,
      required this.category,
      this.address,
      this.imageUrl,
      this.confidence = 0.0,
      final List<String> tags = const [],
      final Map<String, dynamic>? extractedInfo,
      this.analysisId})
      : _tags = tags,
        _extractedInfo = extractedInfo;

  factory _$ShareQueueAnalysisResultImpl.fromJson(Map<String, dynamic> json) =>
      _$$ShareQueueAnalysisResultImplFromJson(json);

  /// 장소명
  @override
  final String placeName;

  /// 카테고리
  @override
  final String category;

  /// 주소
  @override
  final String? address;

  /// 이미지 URL
  @override
  final String? imageUrl;

  /// 신뢰도 점수 (0.0 ~ 1.0)
  @override
  @JsonKey()
  final double confidence;

  /// 태그 목록
  final List<String> _tags;

  /// 태그 목록
  @override
  @JsonKey()
  List<String> get tags {
    if (_tags is EqualUnmodifiableListView) return _tags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_tags);
  }

  /// 추출된 추가 정보
  final Map<String, dynamic>? _extractedInfo;

  /// 추출된 추가 정보
  @override
  Map<String, dynamic>? get extractedInfo {
    final value = _extractedInfo;
    if (value == null) return null;
    if (_extractedInfo is EqualUnmodifiableMapView) return _extractedInfo;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(value);
  }

  /// 원본 분석 ID (서버)
  @override
  final String? analysisId;

  @override
  String toString() {
    return 'ShareQueueAnalysisResult(placeName: $placeName, category: $category, address: $address, imageUrl: $imageUrl, confidence: $confidence, tags: $tags, extractedInfo: $extractedInfo, analysisId: $analysisId)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ShareQueueAnalysisResultImpl &&
            (identical(other.placeName, placeName) ||
                other.placeName == placeName) &&
            (identical(other.category, category) ||
                other.category == category) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.imageUrl, imageUrl) ||
                other.imageUrl == imageUrl) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            const DeepCollectionEquality().equals(other._tags, _tags) &&
            const DeepCollectionEquality()
                .equals(other._extractedInfo, _extractedInfo) &&
            (identical(other.analysisId, analysisId) ||
                other.analysisId == analysisId));
  }

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      placeName,
      category,
      address,
      imageUrl,
      confidence,
      const DeepCollectionEquality().hash(_tags),
      const DeepCollectionEquality().hash(_extractedInfo),
      analysisId);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ShareQueueAnalysisResultImplCopyWith<_$ShareQueueAnalysisResultImpl>
      get copyWith => __$$ShareQueueAnalysisResultImplCopyWithImpl<
          _$ShareQueueAnalysisResultImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ShareQueueAnalysisResultImplToJson(
      this,
    );
  }
}

abstract class _ShareQueueAnalysisResult implements ShareQueueAnalysisResult {
  const factory _ShareQueueAnalysisResult(
      {required final String placeName,
      required final String category,
      final String? address,
      final String? imageUrl,
      final double confidence,
      final List<String> tags,
      final Map<String, dynamic>? extractedInfo,
      final String? analysisId}) = _$ShareQueueAnalysisResultImpl;

  factory _ShareQueueAnalysisResult.fromJson(Map<String, dynamic> json) =
      _$ShareQueueAnalysisResultImpl.fromJson;

  @override

  /// 장소명
  String get placeName;
  @override

  /// 카테고리
  String get category;
  @override

  /// 주소
  String? get address;
  @override

  /// 이미지 URL
  String? get imageUrl;
  @override

  /// 신뢰도 점수 (0.0 ~ 1.0)
  double get confidence;
  @override

  /// 태그 목록
  List<String> get tags;
  @override

  /// 추출된 추가 정보
  Map<String, dynamic>? get extractedInfo;
  @override

  /// 원본 분석 ID (서버)
  String? get analysisId;
  @override
  @JsonKey(ignore: true)
  _$$ShareQueueAnalysisResultImplCopyWith<_$ShareQueueAnalysisResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ShareQueueState {
  /// 큐 항목 목록
  List<ShareQueueItem> get items => throw _privateConstructorUsedError;

  /// 처리 중 여부
  bool get isProcessing => throw _privateConstructorUsedError;

  /// 현재 처리 중인 인덱스
  int get processingIndex => throw _privateConstructorUsedError;

  /// 에러 메시지
  String? get error => throw _privateConstructorUsedError;

  /// 마지막 동기화 시각
  DateTime? get lastSyncAt => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $ShareQueueStateCopyWith<ShareQueueState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ShareQueueStateCopyWith<$Res> {
  factory $ShareQueueStateCopyWith(
          ShareQueueState value, $Res Function(ShareQueueState) then) =
      _$ShareQueueStateCopyWithImpl<$Res, ShareQueueState>;
  @useResult
  $Res call(
      {List<ShareQueueItem> items,
      bool isProcessing,
      int processingIndex,
      String? error,
      DateTime? lastSyncAt});
}

/// @nodoc
class _$ShareQueueStateCopyWithImpl<$Res, $Val extends ShareQueueState>
    implements $ShareQueueStateCopyWith<$Res> {
  _$ShareQueueStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? isProcessing = null,
    Object? processingIndex = null,
    Object? error = freezed,
    Object? lastSyncAt = freezed,
  }) {
    return _then(_value.copyWith(
      items: null == items
          ? _value.items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ShareQueueItem>,
      isProcessing: null == isProcessing
          ? _value.isProcessing
          : isProcessing // ignore: cast_nullable_to_non_nullable
              as bool,
      processingIndex: null == processingIndex
          ? _value.processingIndex
          : processingIndex // ignore: cast_nullable_to_non_nullable
              as int,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      lastSyncAt: freezed == lastSyncAt
          ? _value.lastSyncAt
          : lastSyncAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ShareQueueStateImplCopyWith<$Res>
    implements $ShareQueueStateCopyWith<$Res> {
  factory _$$ShareQueueStateImplCopyWith(_$ShareQueueStateImpl value,
          $Res Function(_$ShareQueueStateImpl) then) =
      __$$ShareQueueStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<ShareQueueItem> items,
      bool isProcessing,
      int processingIndex,
      String? error,
      DateTime? lastSyncAt});
}

/// @nodoc
class __$$ShareQueueStateImplCopyWithImpl<$Res>
    extends _$ShareQueueStateCopyWithImpl<$Res, _$ShareQueueStateImpl>
    implements _$$ShareQueueStateImplCopyWith<$Res> {
  __$$ShareQueueStateImplCopyWithImpl(
      _$ShareQueueStateImpl _value, $Res Function(_$ShareQueueStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? isProcessing = null,
    Object? processingIndex = null,
    Object? error = freezed,
    Object? lastSyncAt = freezed,
  }) {
    return _then(_$ShareQueueStateImpl(
      items: null == items
          ? _value._items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ShareQueueItem>,
      isProcessing: null == isProcessing
          ? _value.isProcessing
          : isProcessing // ignore: cast_nullable_to_non_nullable
              as bool,
      processingIndex: null == processingIndex
          ? _value.processingIndex
          : processingIndex // ignore: cast_nullable_to_non_nullable
              as int,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      lastSyncAt: freezed == lastSyncAt
          ? _value.lastSyncAt
          : lastSyncAt // ignore: cast_nullable_to_non_nullable
              as DateTime?,
    ));
  }
}

/// @nodoc

class _$ShareQueueStateImpl extends _ShareQueueState {
  const _$ShareQueueStateImpl(
      {final List<ShareQueueItem> items = const [],
      this.isProcessing = false,
      this.processingIndex = 0,
      this.error,
      this.lastSyncAt})
      : _items = items,
        super._();

  /// 큐 항목 목록
  final List<ShareQueueItem> _items;

  /// 큐 항목 목록
  @override
  @JsonKey()
  List<ShareQueueItem> get items {
    if (_items is EqualUnmodifiableListView) return _items;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_items);
  }

  /// 처리 중 여부
  @override
  @JsonKey()
  final bool isProcessing;

  /// 현재 처리 중인 인덱스
  @override
  @JsonKey()
  final int processingIndex;

  /// 에러 메시지
  @override
  final String? error;

  /// 마지막 동기화 시각
  @override
  final DateTime? lastSyncAt;

  @override
  String toString() {
    return 'ShareQueueState(items: $items, isProcessing: $isProcessing, processingIndex: $processingIndex, error: $error, lastSyncAt: $lastSyncAt)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ShareQueueStateImpl &&
            const DeepCollectionEquality().equals(other._items, _items) &&
            (identical(other.isProcessing, isProcessing) ||
                other.isProcessing == isProcessing) &&
            (identical(other.processingIndex, processingIndex) ||
                other.processingIndex == processingIndex) &&
            (identical(other.error, error) || other.error == error) &&
            (identical(other.lastSyncAt, lastSyncAt) ||
                other.lastSyncAt == lastSyncAt));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_items),
      isProcessing,
      processingIndex,
      error,
      lastSyncAt);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ShareQueueStateImplCopyWith<_$ShareQueueStateImpl> get copyWith =>
      __$$ShareQueueStateImplCopyWithImpl<_$ShareQueueStateImpl>(
          this, _$identity);
}

abstract class _ShareQueueState extends ShareQueueState {
  const factory _ShareQueueState(
      {final List<ShareQueueItem> items,
      final bool isProcessing,
      final int processingIndex,
      final String? error,
      final DateTime? lastSyncAt}) = _$ShareQueueStateImpl;
  const _ShareQueueState._() : super._();

  @override

  /// 큐 항목 목록
  List<ShareQueueItem> get items;
  @override

  /// 처리 중 여부
  bool get isProcessing;
  @override

  /// 현재 처리 중인 인덱스
  int get processingIndex;
  @override

  /// 에러 메시지
  String? get error;
  @override

  /// 마지막 동기화 시각
  DateTime? get lastSyncAt;
  @override
  @JsonKey(ignore: true)
  _$$ShareQueueStateImplCopyWith<_$ShareQueueStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
