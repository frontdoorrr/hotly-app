// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'link_analysis_result.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$LinkAnalysisResult {
  String get analysisId => throw _privateConstructorUsedError;
  AnalysisStatus get status => throw _privateConstructorUsedError;
  PlaceInfo? get placeInfo => throw _privateConstructorUsedError;
  ContentMetadata? get contentMetadata => throw _privateConstructorUsedError;
  double get confidence => throw _privateConstructorUsedError;
  double get processingTime => throw _privateConstructorUsedError;
  bool get cached => throw _privateConstructorUsedError;
  double? get progress => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LinkAnalysisResultCopyWith<LinkAnalysisResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LinkAnalysisResultCopyWith<$Res> {
  factory $LinkAnalysisResultCopyWith(
          LinkAnalysisResult value, $Res Function(LinkAnalysisResult) then) =
      _$LinkAnalysisResultCopyWithImpl<$Res, LinkAnalysisResult>;
  @useResult
  $Res call(
      {String analysisId,
      AnalysisStatus status,
      PlaceInfo? placeInfo,
      ContentMetadata? contentMetadata,
      double confidence,
      double processingTime,
      bool cached,
      double? progress,
      String? error});

  $PlaceInfoCopyWith<$Res>? get placeInfo;
  $ContentMetadataCopyWith<$Res>? get contentMetadata;
}

/// @nodoc
class _$LinkAnalysisResultCopyWithImpl<$Res, $Val extends LinkAnalysisResult>
    implements $LinkAnalysisResultCopyWith<$Res> {
  _$LinkAnalysisResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? analysisId = null,
    Object? status = null,
    Object? placeInfo = freezed,
    Object? contentMetadata = freezed,
    Object? confidence = null,
    Object? processingTime = null,
    Object? cached = null,
    Object? progress = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      analysisId: null == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AnalysisStatus,
      placeInfo: freezed == placeInfo
          ? _value.placeInfo
          : placeInfo // ignore: cast_nullable_to_non_nullable
              as PlaceInfo?,
      contentMetadata: freezed == contentMetadata
          ? _value.contentMetadata
          : contentMetadata // ignore: cast_nullable_to_non_nullable
              as ContentMetadata?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      processingTime: null == processingTime
          ? _value.processingTime
          : processingTime // ignore: cast_nullable_to_non_nullable
              as double,
      cached: null == cached
          ? _value.cached
          : cached // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as double?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $PlaceInfoCopyWith<$Res>? get placeInfo {
    if (_value.placeInfo == null) {
      return null;
    }

    return $PlaceInfoCopyWith<$Res>(_value.placeInfo!, (value) {
      return _then(_value.copyWith(placeInfo: value) as $Val);
    });
  }

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $ContentMetadataCopyWith<$Res>? get contentMetadata {
    if (_value.contentMetadata == null) {
      return null;
    }

    return $ContentMetadataCopyWith<$Res>(_value.contentMetadata!, (value) {
      return _then(_value.copyWith(contentMetadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$LinkAnalysisResultImplCopyWith<$Res>
    implements $LinkAnalysisResultCopyWith<$Res> {
  factory _$$LinkAnalysisResultImplCopyWith(_$LinkAnalysisResultImpl value,
          $Res Function(_$LinkAnalysisResultImpl) then) =
      __$$LinkAnalysisResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String analysisId,
      AnalysisStatus status,
      PlaceInfo? placeInfo,
      ContentMetadata? contentMetadata,
      double confidence,
      double processingTime,
      bool cached,
      double? progress,
      String? error});

  @override
  $PlaceInfoCopyWith<$Res>? get placeInfo;
  @override
  $ContentMetadataCopyWith<$Res>? get contentMetadata;
}

/// @nodoc
class __$$LinkAnalysisResultImplCopyWithImpl<$Res>
    extends _$LinkAnalysisResultCopyWithImpl<$Res, _$LinkAnalysisResultImpl>
    implements _$$LinkAnalysisResultImplCopyWith<$Res> {
  __$$LinkAnalysisResultImplCopyWithImpl(_$LinkAnalysisResultImpl _value,
      $Res Function(_$LinkAnalysisResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? analysisId = null,
    Object? status = null,
    Object? placeInfo = freezed,
    Object? contentMetadata = freezed,
    Object? confidence = null,
    Object? processingTime = null,
    Object? cached = null,
    Object? progress = freezed,
    Object? error = freezed,
  }) {
    return _then(_$LinkAnalysisResultImpl(
      analysisId: null == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as AnalysisStatus,
      placeInfo: freezed == placeInfo
          ? _value.placeInfo
          : placeInfo // ignore: cast_nullable_to_non_nullable
              as PlaceInfo?,
      contentMetadata: freezed == contentMetadata
          ? _value.contentMetadata
          : contentMetadata // ignore: cast_nullable_to_non_nullable
              as ContentMetadata?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      processingTime: null == processingTime
          ? _value.processingTime
          : processingTime // ignore: cast_nullable_to_non_nullable
              as double,
      cached: null == cached
          ? _value.cached
          : cached // ignore: cast_nullable_to_non_nullable
              as bool,
      progress: freezed == progress
          ? _value.progress
          : progress // ignore: cast_nullable_to_non_nullable
              as double?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$LinkAnalysisResultImpl implements _LinkAnalysisResult {
  const _$LinkAnalysisResultImpl(
      {required this.analysisId,
      required this.status,
      this.placeInfo,
      this.contentMetadata,
      this.confidence = 0.0,
      this.processingTime = 0.0,
      this.cached = false,
      this.progress,
      this.error});

  @override
  final String analysisId;
  @override
  final AnalysisStatus status;
  @override
  final PlaceInfo? placeInfo;
  @override
  final ContentMetadata? contentMetadata;
  @override
  @JsonKey()
  final double confidence;
  @override
  @JsonKey()
  final double processingTime;
  @override
  @JsonKey()
  final bool cached;
  @override
  final double? progress;
  @override
  final String? error;

  @override
  String toString() {
    return 'LinkAnalysisResult(analysisId: $analysisId, status: $status, placeInfo: $placeInfo, contentMetadata: $contentMetadata, confidence: $confidence, processingTime: $processingTime, cached: $cached, progress: $progress, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LinkAnalysisResultImpl &&
            (identical(other.analysisId, analysisId) ||
                other.analysisId == analysisId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.placeInfo, placeInfo) ||
                other.placeInfo == placeInfo) &&
            (identical(other.contentMetadata, contentMetadata) ||
                other.contentMetadata == contentMetadata) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.processingTime, processingTime) ||
                other.processingTime == processingTime) &&
            (identical(other.cached, cached) || other.cached == cached) &&
            (identical(other.progress, progress) ||
                other.progress == progress) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(runtimeType, analysisId, status, placeInfo,
      contentMetadata, confidence, processingTime, cached, progress, error);

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LinkAnalysisResultImplCopyWith<_$LinkAnalysisResultImpl> get copyWith =>
      __$$LinkAnalysisResultImplCopyWithImpl<_$LinkAnalysisResultImpl>(
          this, _$identity);
}

abstract class _LinkAnalysisResult implements LinkAnalysisResult {
  const factory _LinkAnalysisResult(
      {required final String analysisId,
      required final AnalysisStatus status,
      final PlaceInfo? placeInfo,
      final ContentMetadata? contentMetadata,
      final double confidence,
      final double processingTime,
      final bool cached,
      final double? progress,
      final String? error}) = _$LinkAnalysisResultImpl;

  @override
  String get analysisId;
  @override
  AnalysisStatus get status;
  @override
  PlaceInfo? get placeInfo;
  @override
  ContentMetadata? get contentMetadata;
  @override
  double get confidence;
  @override
  double get processingTime;
  @override
  bool get cached;
  @override
  double? get progress;
  @override
  String? get error;

  /// Create a copy of LinkAnalysisResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LinkAnalysisResultImplCopyWith<_$LinkAnalysisResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$PlaceInfo {
  String get name => throw _privateConstructorUsedError;
  String? get address => throw _privateConstructorUsedError;
  String? get category => throw _privateConstructorUsedError;
  List<String>? get tags => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  double? get rating => throw _privateConstructorUsedError;
  Coordinates? get coordinates => throw _privateConstructorUsedError;

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PlaceInfoCopyWith<PlaceInfo> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlaceInfoCopyWith<$Res> {
  factory $PlaceInfoCopyWith(PlaceInfo value, $Res Function(PlaceInfo) then) =
      _$PlaceInfoCopyWithImpl<$Res, PlaceInfo>;
  @useResult
  $Res call(
      {String name,
      String? address,
      String? category,
      List<String>? tags,
      String? description,
      double? rating,
      Coordinates? coordinates});

  $CoordinatesCopyWith<$Res>? get coordinates;
}

/// @nodoc
class _$PlaceInfoCopyWithImpl<$Res, $Val extends PlaceInfo>
    implements $PlaceInfoCopyWith<$Res> {
  _$PlaceInfoCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? address = freezed,
    Object? category = freezed,
    Object? tags = freezed,
    Object? description = freezed,
    Object? rating = freezed,
    Object? coordinates = freezed,
  }) {
    return _then(_value.copyWith(
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      category: freezed == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String?,
      tags: freezed == tags
          ? _value.tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      rating: freezed == rating
          ? _value.rating
          : rating // ignore: cast_nullable_to_non_nullable
              as double?,
      coordinates: freezed == coordinates
          ? _value.coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as Coordinates?,
    ) as $Val);
  }

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $CoordinatesCopyWith<$Res>? get coordinates {
    if (_value.coordinates == null) {
      return null;
    }

    return $CoordinatesCopyWith<$Res>(_value.coordinates!, (value) {
      return _then(_value.copyWith(coordinates: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PlaceInfoImplCopyWith<$Res>
    implements $PlaceInfoCopyWith<$Res> {
  factory _$$PlaceInfoImplCopyWith(
          _$PlaceInfoImpl value, $Res Function(_$PlaceInfoImpl) then) =
      __$$PlaceInfoImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String name,
      String? address,
      String? category,
      List<String>? tags,
      String? description,
      double? rating,
      Coordinates? coordinates});

  @override
  $CoordinatesCopyWith<$Res>? get coordinates;
}

/// @nodoc
class __$$PlaceInfoImplCopyWithImpl<$Res>
    extends _$PlaceInfoCopyWithImpl<$Res, _$PlaceInfoImpl>
    implements _$$PlaceInfoImplCopyWith<$Res> {
  __$$PlaceInfoImplCopyWithImpl(
      _$PlaceInfoImpl _value, $Res Function(_$PlaceInfoImpl) _then)
      : super(_value, _then);

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? address = freezed,
    Object? category = freezed,
    Object? tags = freezed,
    Object? description = freezed,
    Object? rating = freezed,
    Object? coordinates = freezed,
  }) {
    return _then(_$PlaceInfoImpl(
      name: null == name
          ? _value.name
          : name // ignore: cast_nullable_to_non_nullable
              as String,
      address: freezed == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String?,
      category: freezed == category
          ? _value.category
          : category // ignore: cast_nullable_to_non_nullable
              as String?,
      tags: freezed == tags
          ? _value._tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      rating: freezed == rating
          ? _value.rating
          : rating // ignore: cast_nullable_to_non_nullable
              as double?,
      coordinates: freezed == coordinates
          ? _value.coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as Coordinates?,
    ));
  }
}

/// @nodoc

class _$PlaceInfoImpl implements _PlaceInfo {
  const _$PlaceInfoImpl(
      {required this.name,
      this.address,
      this.category,
      final List<String>? tags,
      this.description,
      this.rating,
      this.coordinates})
      : _tags = tags;

  @override
  final String name;
  @override
  final String? address;
  @override
  final String? category;
  final List<String>? _tags;
  @override
  List<String>? get tags {
    final value = _tags;
    if (value == null) return null;
    if (_tags is EqualUnmodifiableListView) return _tags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(value);
  }

  @override
  final String? description;
  @override
  final double? rating;
  @override
  final Coordinates? coordinates;

  @override
  String toString() {
    return 'PlaceInfo(name: $name, address: $address, category: $category, tags: $tags, description: $description, rating: $rating, coordinates: $coordinates)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlaceInfoImpl &&
            (identical(other.name, name) || other.name == name) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.category, category) ||
                other.category == category) &&
            const DeepCollectionEquality().equals(other._tags, _tags) &&
            (identical(other.description, description) ||
                other.description == description) &&
            (identical(other.rating, rating) || other.rating == rating) &&
            (identical(other.coordinates, coordinates) ||
                other.coordinates == coordinates));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      name,
      address,
      category,
      const DeepCollectionEquality().hash(_tags),
      description,
      rating,
      coordinates);

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PlaceInfoImplCopyWith<_$PlaceInfoImpl> get copyWith =>
      __$$PlaceInfoImplCopyWithImpl<_$PlaceInfoImpl>(this, _$identity);
}

abstract class _PlaceInfo implements PlaceInfo {
  const factory _PlaceInfo(
      {required final String name,
      final String? address,
      final String? category,
      final List<String>? tags,
      final String? description,
      final double? rating,
      final Coordinates? coordinates}) = _$PlaceInfoImpl;

  @override
  String get name;
  @override
  String? get address;
  @override
  String? get category;
  @override
  List<String>? get tags;
  @override
  String? get description;
  @override
  double? get rating;
  @override
  Coordinates? get coordinates;

  /// Create a copy of PlaceInfo
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PlaceInfoImplCopyWith<_$PlaceInfoImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$Coordinates {
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;

  /// Create a copy of Coordinates
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CoordinatesCopyWith<Coordinates> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CoordinatesCopyWith<$Res> {
  factory $CoordinatesCopyWith(
          Coordinates value, $Res Function(Coordinates) then) =
      _$CoordinatesCopyWithImpl<$Res, Coordinates>;
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class _$CoordinatesCopyWithImpl<$Res, $Val extends Coordinates>
    implements $CoordinatesCopyWith<$Res> {
  _$CoordinatesCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of Coordinates
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
  }) {
    return _then(_value.copyWith(
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CoordinatesImplCopyWith<$Res>
    implements $CoordinatesCopyWith<$Res> {
  factory _$$CoordinatesImplCopyWith(
          _$CoordinatesImpl value, $Res Function(_$CoordinatesImpl) then) =
      __$$CoordinatesImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class __$$CoordinatesImplCopyWithImpl<$Res>
    extends _$CoordinatesCopyWithImpl<$Res, _$CoordinatesImpl>
    implements _$$CoordinatesImplCopyWith<$Res> {
  __$$CoordinatesImplCopyWithImpl(
      _$CoordinatesImpl _value, $Res Function(_$CoordinatesImpl) _then)
      : super(_value, _then);

  /// Create a copy of Coordinates
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
  }) {
    return _then(_$CoordinatesImpl(
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc

class _$CoordinatesImpl implements _Coordinates {
  const _$CoordinatesImpl({required this.latitude, required this.longitude});

  @override
  final double latitude;
  @override
  final double longitude;

  @override
  String toString() {
    return 'Coordinates(latitude: $latitude, longitude: $longitude)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CoordinatesImpl &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude));
  }

  @override
  int get hashCode => Object.hash(runtimeType, latitude, longitude);

  /// Create a copy of Coordinates
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CoordinatesImplCopyWith<_$CoordinatesImpl> get copyWith =>
      __$$CoordinatesImplCopyWithImpl<_$CoordinatesImpl>(this, _$identity);
}

abstract class _Coordinates implements Coordinates {
  const factory _Coordinates(
      {required final double latitude,
      required final double longitude}) = _$CoordinatesImpl;

  @override
  double get latitude;
  @override
  double get longitude;

  /// Create a copy of Coordinates
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CoordinatesImplCopyWith<_$CoordinatesImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ContentMetadata {
  String? get title => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  List<String> get images => throw _privateConstructorUsedError;
  List<String> get hashtags => throw _privateConstructorUsedError;
  double? get extractionTime => throw _privateConstructorUsedError;

  /// Create a copy of ContentMetadata
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ContentMetadataCopyWith<ContentMetadata> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ContentMetadataCopyWith<$Res> {
  factory $ContentMetadataCopyWith(
          ContentMetadata value, $Res Function(ContentMetadata) then) =
      _$ContentMetadataCopyWithImpl<$Res, ContentMetadata>;
  @useResult
  $Res call(
      {String? title,
      String? description,
      List<String> images,
      List<String> hashtags,
      double? extractionTime});
}

/// @nodoc
class _$ContentMetadataCopyWithImpl<$Res, $Val extends ContentMetadata>
    implements $ContentMetadataCopyWith<$Res> {
  _$ContentMetadataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ContentMetadata
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? title = freezed,
    Object? description = freezed,
    Object? images = null,
    Object? hashtags = null,
    Object? extractionTime = freezed,
  }) {
    return _then(_value.copyWith(
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value.images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
      hashtags: null == hashtags
          ? _value.hashtags
          : hashtags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      extractionTime: freezed == extractionTime
          ? _value.extractionTime
          : extractionTime // ignore: cast_nullable_to_non_nullable
              as double?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ContentMetadataImplCopyWith<$Res>
    implements $ContentMetadataCopyWith<$Res> {
  factory _$$ContentMetadataImplCopyWith(_$ContentMetadataImpl value,
          $Res Function(_$ContentMetadataImpl) then) =
      __$$ContentMetadataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? title,
      String? description,
      List<String> images,
      List<String> hashtags,
      double? extractionTime});
}

/// @nodoc
class __$$ContentMetadataImplCopyWithImpl<$Res>
    extends _$ContentMetadataCopyWithImpl<$Res, _$ContentMetadataImpl>
    implements _$$ContentMetadataImplCopyWith<$Res> {
  __$$ContentMetadataImplCopyWithImpl(
      _$ContentMetadataImpl _value, $Res Function(_$ContentMetadataImpl) _then)
      : super(_value, _then);

  /// Create a copy of ContentMetadata
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? title = freezed,
    Object? description = freezed,
    Object? images = null,
    Object? hashtags = null,
    Object? extractionTime = freezed,
  }) {
    return _then(_$ContentMetadataImpl(
      title: freezed == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String?,
      description: freezed == description
          ? _value.description
          : description // ignore: cast_nullable_to_non_nullable
              as String?,
      images: null == images
          ? _value._images
          : images // ignore: cast_nullable_to_non_nullable
              as List<String>,
      hashtags: null == hashtags
          ? _value._hashtags
          : hashtags // ignore: cast_nullable_to_non_nullable
              as List<String>,
      extractionTime: freezed == extractionTime
          ? _value.extractionTime
          : extractionTime // ignore: cast_nullable_to_non_nullable
              as double?,
    ));
  }
}

/// @nodoc

class _$ContentMetadataImpl implements _ContentMetadata {
  const _$ContentMetadataImpl(
      {this.title,
      this.description,
      final List<String> images = const [],
      final List<String> hashtags = const [],
      this.extractionTime})
      : _images = images,
        _hashtags = hashtags;

  @override
  final String? title;
  @override
  final String? description;
  final List<String> _images;
  @override
  @JsonKey()
  List<String> get images {
    if (_images is EqualUnmodifiableListView) return _images;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_images);
  }

  final List<String> _hashtags;
  @override
  @JsonKey()
  List<String> get hashtags {
    if (_hashtags is EqualUnmodifiableListView) return _hashtags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_hashtags);
  }

  @override
  final double? extractionTime;

  @override
  String toString() {
    return 'ContentMetadata(title: $title, description: $description, images: $images, hashtags: $hashtags, extractionTime: $extractionTime)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ContentMetadataImpl &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            const DeepCollectionEquality().equals(other._images, _images) &&
            const DeepCollectionEquality().equals(other._hashtags, _hashtags) &&
            (identical(other.extractionTime, extractionTime) ||
                other.extractionTime == extractionTime));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      title,
      description,
      const DeepCollectionEquality().hash(_images),
      const DeepCollectionEquality().hash(_hashtags),
      extractionTime);

  /// Create a copy of ContentMetadata
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ContentMetadataImplCopyWith<_$ContentMetadataImpl> get copyWith =>
      __$$ContentMetadataImplCopyWithImpl<_$ContentMetadataImpl>(
          this, _$identity);
}

abstract class _ContentMetadata implements ContentMetadata {
  const factory _ContentMetadata(
      {final String? title,
      final String? description,
      final List<String> images,
      final List<String> hashtags,
      final double? extractionTime}) = _$ContentMetadataImpl;

  @override
  String? get title;
  @override
  String? get description;
  @override
  List<String> get images;
  @override
  List<String> get hashtags;
  @override
  double? get extractionTime;

  /// Create a copy of ContentMetadata
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ContentMetadataImplCopyWith<_$ContentMetadataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
