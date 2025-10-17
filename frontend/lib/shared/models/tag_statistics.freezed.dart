// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'tag_statistics.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

TagInfo _$TagInfoFromJson(Map<String, dynamic> json) {
  return _TagInfo.fromJson(json);
}

/// @nodoc
mixin _$TagInfo {
  String get tag => throw _privateConstructorUsedError;
  int get count => throw _privateConstructorUsedError;

  /// Serializes this TagInfo to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of TagInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $TagInfoCopyWith<TagInfo> get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TagInfoCopyWith<$Res> {
  factory $TagInfoCopyWith(TagInfo value, $Res Function(TagInfo) then) =
      _$TagInfoCopyWithImpl<$Res, TagInfo>;
  @useResult
  $Res call({String tag, int count});
}

/// @nodoc
class _$TagInfoCopyWithImpl<$Res, $Val extends TagInfo>
    implements $TagInfoCopyWith<$Res> {
  _$TagInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of TagInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? tag = null,
    Object? count = null,
  }) {
    return _then(_value.copyWith(
      tag: null == tag
          ? _value.tag
          : tag // ignore: cast_nullable_to_non_nullable
              as String,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TagInfoImplCopyWith<$Res> implements $TagInfoCopyWith<$Res> {
  factory _$$TagInfoImplCopyWith(
          _$TagInfoImpl value, $Res Function(_$TagInfoImpl) then) =
      __$$TagInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({String tag, int count});
}

/// @nodoc
class __$$TagInfoImplCopyWithImpl<$Res>
    extends _$TagInfoCopyWithImpl<$Res, _$TagInfoImpl>
    implements _$$TagInfoImplCopyWith<$Res> {
  __$$TagInfoImplCopyWithImpl(
      _$TagInfoImpl _value, $Res Function(_$TagInfoImpl) _then)
      : super(_value, _then);

  /// Create a copy of TagInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? tag = null,
    Object? count = null,
  }) {
    return _then(_$TagInfoImpl(
      tag: null == tag
          ? _value.tag
          : tag // ignore: cast_nullable_to_non_nullable
              as String,
      count: null == count
          ? _value.count
          : count // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TagInfoImpl implements _TagInfo {
  const _$TagInfoImpl({required this.tag, required this.count});

  factory _$TagInfoImpl.fromJson(Map<String, dynamic> json) =>
      _$$TagInfoImplFromJson(json);

  @override
  final String tag;
  @override
  final int count;

  @override
  String toString() {
    return 'TagInfo(tag: $tag, count: $count)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TagInfoImpl &&
            (identical(other.tag, tag) || other.tag == tag) &&
            (identical(other.count, count) || other.count == count));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, tag, count);

  /// Create a copy of TagInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TagInfoImplCopyWith<_$TagInfoImpl> get copyWith =>
      __$$TagInfoImplCopyWithImpl<_$TagInfoImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TagInfoImplToJson(
      this,
    );
  }
}

abstract class _TagInfo implements TagInfo {
  const factory _TagInfo(
      {required final String tag, required final int count}) = _$TagInfoImpl;

  factory _TagInfo.fromJson(Map<String, dynamic> json) = _$TagInfoImpl.fromJson;

  @override
  String get tag;
  @override
  int get count;

  /// Create a copy of TagInfo
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TagInfoImplCopyWith<_$TagInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

TagStatistics _$TagStatisticsFromJson(Map<String, dynamic> json) {
  return _TagStatistics.fromJson(json);
}

/// @nodoc
mixin _$TagStatistics {
  int get totalUniqueTags => throw _privateConstructorUsedError;
  int get totalTagUsage => throw _privateConstructorUsedError;
  List<TagInfo> get mostUsedTags => throw _privateConstructorUsedError;
  Map<String, List<String>> get tagCategories =>
      throw _privateConstructorUsedError;
  double get averageTagsPerPlace => throw _privateConstructorUsedError;
  int get placesCount => throw _privateConstructorUsedError;

  /// Serializes this TagStatistics to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of TagStatistics
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $TagStatisticsCopyWith<TagStatistics> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TagStatisticsCopyWith<$Res> {
  factory $TagStatisticsCopyWith(
          TagStatistics value, $Res Function(TagStatistics) then) =
      _$TagStatisticsCopyWithImpl<$Res, TagStatistics>;
  @useResult
  $Res call(
      {int totalUniqueTags,
      int totalTagUsage,
      List<TagInfo> mostUsedTags,
      Map<String, List<String>> tagCategories,
      double averageTagsPerPlace,
      int placesCount});
}

/// @nodoc
class _$TagStatisticsCopyWithImpl<$Res, $Val extends TagStatistics>
    implements $TagStatisticsCopyWith<$Res> {
  _$TagStatisticsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of TagStatistics
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalUniqueTags = null,
    Object? totalTagUsage = null,
    Object? mostUsedTags = null,
    Object? tagCategories = null,
    Object? averageTagsPerPlace = null,
    Object? placesCount = null,
  }) {
    return _then(_value.copyWith(
      totalUniqueTags: null == totalUniqueTags
          ? _value.totalUniqueTags
          : totalUniqueTags // ignore: cast_nullable_to_non_nullable
              as int,
      totalTagUsage: null == totalTagUsage
          ? _value.totalTagUsage
          : totalTagUsage // ignore: cast_nullable_to_non_nullable
              as int,
      mostUsedTags: null == mostUsedTags
          ? _value.mostUsedTags
          : mostUsedTags // ignore: cast_nullable_to_non_nullable
              as List<TagInfo>,
      tagCategories: null == tagCategories
          ? _value.tagCategories
          : tagCategories // ignore: cast_nullable_to_non_nullable
              as Map<String, List<String>>,
      averageTagsPerPlace: null == averageTagsPerPlace
          ? _value.averageTagsPerPlace
          : averageTagsPerPlace // ignore: cast_nullable_to_non_nullable
              as double,
      placesCount: null == placesCount
          ? _value.placesCount
          : placesCount // ignore: cast_nullable_to_non_nullable
              as int,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TagStatisticsImplCopyWith<$Res>
    implements $TagStatisticsCopyWith<$Res> {
  factory _$$TagStatisticsImplCopyWith(
          _$TagStatisticsImpl value, $Res Function(_$TagStatisticsImpl) then) =
      __$$TagStatisticsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int totalUniqueTags,
      int totalTagUsage,
      List<TagInfo> mostUsedTags,
      Map<String, List<String>> tagCategories,
      double averageTagsPerPlace,
      int placesCount});
}

/// @nodoc
class __$$TagStatisticsImplCopyWithImpl<$Res>
    extends _$TagStatisticsCopyWithImpl<$Res, _$TagStatisticsImpl>
    implements _$$TagStatisticsImplCopyWith<$Res> {
  __$$TagStatisticsImplCopyWithImpl(
      _$TagStatisticsImpl _value, $Res Function(_$TagStatisticsImpl) _then)
      : super(_value, _then);

  /// Create a copy of TagStatistics
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? totalUniqueTags = null,
    Object? totalTagUsage = null,
    Object? mostUsedTags = null,
    Object? tagCategories = null,
    Object? averageTagsPerPlace = null,
    Object? placesCount = null,
  }) {
    return _then(_$TagStatisticsImpl(
      totalUniqueTags: null == totalUniqueTags
          ? _value.totalUniqueTags
          : totalUniqueTags // ignore: cast_nullable_to_non_nullable
              as int,
      totalTagUsage: null == totalTagUsage
          ? _value.totalTagUsage
          : totalTagUsage // ignore: cast_nullable_to_non_nullable
              as int,
      mostUsedTags: null == mostUsedTags
          ? _value._mostUsedTags
          : mostUsedTags // ignore: cast_nullable_to_non_nullable
              as List<TagInfo>,
      tagCategories: null == tagCategories
          ? _value._tagCategories
          : tagCategories // ignore: cast_nullable_to_non_nullable
              as Map<String, List<String>>,
      averageTagsPerPlace: null == averageTagsPerPlace
          ? _value.averageTagsPerPlace
          : averageTagsPerPlace // ignore: cast_nullable_to_non_nullable
              as double,
      placesCount: null == placesCount
          ? _value.placesCount
          : placesCount // ignore: cast_nullable_to_non_nullable
              as int,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TagStatisticsImpl implements _TagStatistics {
  const _$TagStatisticsImpl(
      {required this.totalUniqueTags,
      required this.totalTagUsage,
      required final List<TagInfo> mostUsedTags,
      required final Map<String, List<String>> tagCategories,
      required this.averageTagsPerPlace,
      required this.placesCount})
      : _mostUsedTags = mostUsedTags,
        _tagCategories = tagCategories;

  factory _$TagStatisticsImpl.fromJson(Map<String, dynamic> json) =>
      _$$TagStatisticsImplFromJson(json);

  @override
  final int totalUniqueTags;
  @override
  final int totalTagUsage;
  final List<TagInfo> _mostUsedTags;
  @override
  List<TagInfo> get mostUsedTags {
    if (_mostUsedTags is EqualUnmodifiableListView) return _mostUsedTags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_mostUsedTags);
  }

  final Map<String, List<String>> _tagCategories;
  @override
  Map<String, List<String>> get tagCategories {
    if (_tagCategories is EqualUnmodifiableMapView) return _tagCategories;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_tagCategories);
  }

  @override
  final double averageTagsPerPlace;
  @override
  final int placesCount;

  @override
  String toString() {
    return 'TagStatistics(totalUniqueTags: $totalUniqueTags, totalTagUsage: $totalTagUsage, mostUsedTags: $mostUsedTags, tagCategories: $tagCategories, averageTagsPerPlace: $averageTagsPerPlace, placesCount: $placesCount)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TagStatisticsImpl &&
            (identical(other.totalUniqueTags, totalUniqueTags) ||
                other.totalUniqueTags == totalUniqueTags) &&
            (identical(other.totalTagUsage, totalTagUsage) ||
                other.totalTagUsage == totalTagUsage) &&
            const DeepCollectionEquality()
                .equals(other._mostUsedTags, _mostUsedTags) &&
            const DeepCollectionEquality()
                .equals(other._tagCategories, _tagCategories) &&
            (identical(other.averageTagsPerPlace, averageTagsPerPlace) ||
                other.averageTagsPerPlace == averageTagsPerPlace) &&
            (identical(other.placesCount, placesCount) ||
                other.placesCount == placesCount));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      totalUniqueTags,
      totalTagUsage,
      const DeepCollectionEquality().hash(_mostUsedTags),
      const DeepCollectionEquality().hash(_tagCategories),
      averageTagsPerPlace,
      placesCount);

  /// Create a copy of TagStatistics
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TagStatisticsImplCopyWith<_$TagStatisticsImpl> get copyWith =>
      __$$TagStatisticsImplCopyWithImpl<_$TagStatisticsImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TagStatisticsImplToJson(
      this,
    );
  }
}

abstract class _TagStatistics implements TagStatistics {
  const factory _TagStatistics(
      {required final int totalUniqueTags,
      required final int totalTagUsage,
      required final List<TagInfo> mostUsedTags,
      required final Map<String, List<String>> tagCategories,
      required final double averageTagsPerPlace,
      required final int placesCount}) = _$TagStatisticsImpl;

  factory _TagStatistics.fromJson(Map<String, dynamic> json) =
      _$TagStatisticsImpl.fromJson;

  @override
  int get totalUniqueTags;
  @override
  int get totalTagUsage;
  @override
  List<TagInfo> get mostUsedTags;
  @override
  Map<String, List<String>> get tagCategories;
  @override
  double get averageTagsPerPlace;
  @override
  int get placesCount;

  /// Create a copy of TagStatistics
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TagStatisticsImplCopyWith<_$TagStatisticsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

TagCluster _$TagClusterFromJson(Map<String, dynamic> json) {
  return _TagCluster.fromJson(json);
}

/// @nodoc
mixin _$TagCluster {
  Map<String, List<String>> get clusters => throw _privateConstructorUsedError;

  /// Serializes this TagCluster to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of TagCluster
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $TagClusterCopyWith<TagCluster> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $TagClusterCopyWith<$Res> {
  factory $TagClusterCopyWith(
          TagCluster value, $Res Function(TagCluster) then) =
      _$TagClusterCopyWithImpl<$Res, TagCluster>;
  @useResult
  $Res call({Map<String, List<String>> clusters});
}

/// @nodoc
class _$TagClusterCopyWithImpl<$Res, $Val extends TagCluster>
    implements $TagClusterCopyWith<$Res> {
  _$TagClusterCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of TagCluster
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? clusters = null,
  }) {
    return _then(_value.copyWith(
      clusters: null == clusters
          ? _value.clusters
          : clusters // ignore: cast_nullable_to_non_nullable
              as Map<String, List<String>>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$TagClusterImplCopyWith<$Res>
    implements $TagClusterCopyWith<$Res> {
  factory _$$TagClusterImplCopyWith(
          _$TagClusterImpl value, $Res Function(_$TagClusterImpl) then) =
      __$$TagClusterImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({Map<String, List<String>> clusters});
}

/// @nodoc
class __$$TagClusterImplCopyWithImpl<$Res>
    extends _$TagClusterCopyWithImpl<$Res, _$TagClusterImpl>
    implements _$$TagClusterImplCopyWith<$Res> {
  __$$TagClusterImplCopyWithImpl(
      _$TagClusterImpl _value, $Res Function(_$TagClusterImpl) _then)
      : super(_value, _then);

  /// Create a copy of TagCluster
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? clusters = null,
  }) {
    return _then(_$TagClusterImpl(
      clusters: null == clusters
          ? _value._clusters
          : clusters // ignore: cast_nullable_to_non_nullable
              as Map<String, List<String>>,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$TagClusterImpl implements _TagCluster {
  const _$TagClusterImpl({required final Map<String, List<String>> clusters})
      : _clusters = clusters;

  factory _$TagClusterImpl.fromJson(Map<String, dynamic> json) =>
      _$$TagClusterImplFromJson(json);

  final Map<String, List<String>> _clusters;
  @override
  Map<String, List<String>> get clusters {
    if (_clusters is EqualUnmodifiableMapView) return _clusters;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableMapView(_clusters);
  }

  @override
  String toString() {
    return 'TagCluster(clusters: $clusters)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$TagClusterImpl &&
            const DeepCollectionEquality().equals(other._clusters, _clusters));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode =>
      Object.hash(runtimeType, const DeepCollectionEquality().hash(_clusters));

  /// Create a copy of TagCluster
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$TagClusterImplCopyWith<_$TagClusterImpl> get copyWith =>
      __$$TagClusterImplCopyWithImpl<_$TagClusterImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$TagClusterImplToJson(
      this,
    );
  }
}

abstract class _TagCluster implements TagCluster {
  const factory _TagCluster(
      {required final Map<String, List<String>> clusters}) = _$TagClusterImpl;

  factory _TagCluster.fromJson(Map<String, dynamic> json) =
      _$TagClusterImpl.fromJson;

  @override
  Map<String, List<String>> get clusters;

  /// Create a copy of TagCluster
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$TagClusterImplCopyWith<_$TagClusterImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
