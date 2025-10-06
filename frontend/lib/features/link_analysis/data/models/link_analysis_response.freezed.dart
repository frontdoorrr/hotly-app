// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'link_analysis_response.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

LinkAnalysisResponse _$LinkAnalysisResponseFromJson(Map<String, dynamic> json) {
  return _LinkAnalysisResponse.fromJson(json);
}

/// @nodoc
mixin _$LinkAnalysisResponse {
  bool get success => throw _privateConstructorUsedError;
  @JsonKey(name: 'analysis_id')
  String get analysisId => throw _privateConstructorUsedError;
  String get status => throw _privateConstructorUsedError;
  @JsonKey(name: 'result')
  AnalysisResultData? get resultData => throw _privateConstructorUsedError;
  bool get cached => throw _privateConstructorUsedError;
  @JsonKey(name: 'processing_time')
  double get processingTime => throw _privateConstructorUsedError;
  double? get progress => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  /// Serializes this LinkAnalysisResponse to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $LinkAnalysisResponseCopyWith<LinkAnalysisResponse> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LinkAnalysisResponseCopyWith<$Res> {
  factory $LinkAnalysisResponseCopyWith(LinkAnalysisResponse value,
          $Res Function(LinkAnalysisResponse) then) =
      _$LinkAnalysisResponseCopyWithImpl<$Res, LinkAnalysisResponse>;
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'analysis_id') String analysisId,
      String status,
      @JsonKey(name: 'result') AnalysisResultData? resultData,
      bool cached,
      @JsonKey(name: 'processing_time') double processingTime,
      double? progress,
      String? error});

  $AnalysisResultDataCopyWith<$Res>? get resultData;
}

/// @nodoc
class _$LinkAnalysisResponseCopyWithImpl<$Res,
        $Val extends LinkAnalysisResponse>
    implements $LinkAnalysisResponseCopyWith<$Res> {
  _$LinkAnalysisResponseCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? analysisId = null,
    Object? status = null,
    Object? resultData = freezed,
    Object? cached = null,
    Object? processingTime = null,
    Object? progress = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      analysisId: null == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      resultData: freezed == resultData
          ? _value.resultData
          : resultData // ignore: cast_nullable_to_non_nullable
              as AnalysisResultData?,
      cached: null == cached
          ? _value.cached
          : cached // ignore: cast_nullable_to_non_nullable
              as bool,
      processingTime: null == processingTime
          ? _value.processingTime
          : processingTime // ignore: cast_nullable_to_non_nullable
              as double,
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

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $AnalysisResultDataCopyWith<$Res>? get resultData {
    if (_value.resultData == null) {
      return null;
    }

    return $AnalysisResultDataCopyWith<$Res>(_value.resultData!, (value) {
      return _then(_value.copyWith(resultData: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$LinkAnalysisResponseImplCopyWith<$Res>
    implements $LinkAnalysisResponseCopyWith<$Res> {
  factory _$$LinkAnalysisResponseImplCopyWith(_$LinkAnalysisResponseImpl value,
          $Res Function(_$LinkAnalysisResponseImpl) then) =
      __$$LinkAnalysisResponseImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool success,
      @JsonKey(name: 'analysis_id') String analysisId,
      String status,
      @JsonKey(name: 'result') AnalysisResultData? resultData,
      bool cached,
      @JsonKey(name: 'processing_time') double processingTime,
      double? progress,
      String? error});

  @override
  $AnalysisResultDataCopyWith<$Res>? get resultData;
}

/// @nodoc
class __$$LinkAnalysisResponseImplCopyWithImpl<$Res>
    extends _$LinkAnalysisResponseCopyWithImpl<$Res, _$LinkAnalysisResponseImpl>
    implements _$$LinkAnalysisResponseImplCopyWith<$Res> {
  __$$LinkAnalysisResponseImplCopyWithImpl(_$LinkAnalysisResponseImpl _value,
      $Res Function(_$LinkAnalysisResponseImpl) _then)
      : super(_value, _then);

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? success = null,
    Object? analysisId = null,
    Object? status = null,
    Object? resultData = freezed,
    Object? cached = null,
    Object? processingTime = null,
    Object? progress = freezed,
    Object? error = freezed,
  }) {
    return _then(_$LinkAnalysisResponseImpl(
      success: null == success
          ? _value.success
          : success // ignore: cast_nullable_to_non_nullable
              as bool,
      analysisId: null == analysisId
          ? _value.analysisId
          : analysisId // ignore: cast_nullable_to_non_nullable
              as String,
      status: null == status
          ? _value.status
          : status // ignore: cast_nullable_to_non_nullable
              as String,
      resultData: freezed == resultData
          ? _value.resultData
          : resultData // ignore: cast_nullable_to_non_nullable
              as AnalysisResultData?,
      cached: null == cached
          ? _value.cached
          : cached // ignore: cast_nullable_to_non_nullable
              as bool,
      processingTime: null == processingTime
          ? _value.processingTime
          : processingTime // ignore: cast_nullable_to_non_nullable
              as double,
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
@JsonSerializable()
class _$LinkAnalysisResponseImpl implements _LinkAnalysisResponse {
  const _$LinkAnalysisResponseImpl(
      {required this.success,
      @JsonKey(name: 'analysis_id') required this.analysisId,
      required this.status,
      @JsonKey(name: 'result') this.resultData,
      this.cached = false,
      @JsonKey(name: 'processing_time') this.processingTime = 0.0,
      this.progress,
      this.error});

  factory _$LinkAnalysisResponseImpl.fromJson(Map<String, dynamic> json) =>
      _$$LinkAnalysisResponseImplFromJson(json);

  @override
  final bool success;
  @override
  @JsonKey(name: 'analysis_id')
  final String analysisId;
  @override
  final String status;
  @override
  @JsonKey(name: 'result')
  final AnalysisResultData? resultData;
  @override
  @JsonKey()
  final bool cached;
  @override
  @JsonKey(name: 'processing_time')
  final double processingTime;
  @override
  final double? progress;
  @override
  final String? error;

  @override
  String toString() {
    return 'LinkAnalysisResponse(success: $success, analysisId: $analysisId, status: $status, resultData: $resultData, cached: $cached, processingTime: $processingTime, progress: $progress, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LinkAnalysisResponseImpl &&
            (identical(other.success, success) || other.success == success) &&
            (identical(other.analysisId, analysisId) ||
                other.analysisId == analysisId) &&
            (identical(other.status, status) || other.status == status) &&
            (identical(other.resultData, resultData) ||
                other.resultData == resultData) &&
            (identical(other.cached, cached) || other.cached == cached) &&
            (identical(other.processingTime, processingTime) ||
                other.processingTime == processingTime) &&
            (identical(other.progress, progress) ||
                other.progress == progress) &&
            (identical(other.error, error) || other.error == error));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, success, analysisId, status,
      resultData, cached, processingTime, progress, error);

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$LinkAnalysisResponseImplCopyWith<_$LinkAnalysisResponseImpl>
      get copyWith =>
          __$$LinkAnalysisResponseImplCopyWithImpl<_$LinkAnalysisResponseImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$LinkAnalysisResponseImplToJson(
      this,
    );
  }
}

abstract class _LinkAnalysisResponse implements LinkAnalysisResponse {
  const factory _LinkAnalysisResponse(
      {required final bool success,
      @JsonKey(name: 'analysis_id') required final String analysisId,
      required final String status,
      @JsonKey(name: 'result') final AnalysisResultData? resultData,
      final bool cached,
      @JsonKey(name: 'processing_time') final double processingTime,
      final double? progress,
      final String? error}) = _$LinkAnalysisResponseImpl;

  factory _LinkAnalysisResponse.fromJson(Map<String, dynamic> json) =
      _$LinkAnalysisResponseImpl.fromJson;

  @override
  bool get success;
  @override
  @JsonKey(name: 'analysis_id')
  String get analysisId;
  @override
  String get status;
  @override
  @JsonKey(name: 'result')
  AnalysisResultData? get resultData;
  @override
  bool get cached;
  @override
  @JsonKey(name: 'processing_time')
  double get processingTime;
  @override
  double? get progress;
  @override
  String? get error;

  /// Create a copy of LinkAnalysisResponse
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$LinkAnalysisResponseImplCopyWith<_$LinkAnalysisResponseImpl>
      get copyWith => throw _privateConstructorUsedError;
}

AnalysisResultData _$AnalysisResultDataFromJson(Map<String, dynamic> json) {
  return _AnalysisResultData.fromJson(json);
}

/// @nodoc
mixin _$AnalysisResultData {
  @JsonKey(name: 'place_info')
  PlaceInfoModel? get placeInfo => throw _privateConstructorUsedError;
  double get confidence => throw _privateConstructorUsedError;
  @JsonKey(name: 'analysis_time')
  double get analysisTime => throw _privateConstructorUsedError;
  @JsonKey(name: 'content_metadata')
  ContentMetadataModel? get contentMetadata =>
      throw _privateConstructorUsedError;

  /// Serializes this AnalysisResultData to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AnalysisResultDataCopyWith<AnalysisResultData> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AnalysisResultDataCopyWith<$Res> {
  factory $AnalysisResultDataCopyWith(
          AnalysisResultData value, $Res Function(AnalysisResultData) then) =
      _$AnalysisResultDataCopyWithImpl<$Res, AnalysisResultData>;
  @useResult
  $Res call(
      {@JsonKey(name: 'place_info') PlaceInfoModel? placeInfo,
      double confidence,
      @JsonKey(name: 'analysis_time') double analysisTime,
      @JsonKey(name: 'content_metadata')
      ContentMetadataModel? contentMetadata});

  $PlaceInfoModelCopyWith<$Res>? get placeInfo;
  $ContentMetadataModelCopyWith<$Res>? get contentMetadata;
}

/// @nodoc
class _$AnalysisResultDataCopyWithImpl<$Res, $Val extends AnalysisResultData>
    implements $AnalysisResultDataCopyWith<$Res> {
  _$AnalysisResultDataCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeInfo = freezed,
    Object? confidence = null,
    Object? analysisTime = null,
    Object? contentMetadata = freezed,
  }) {
    return _then(_value.copyWith(
      placeInfo: freezed == placeInfo
          ? _value.placeInfo
          : placeInfo // ignore: cast_nullable_to_non_nullable
              as PlaceInfoModel?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      analysisTime: null == analysisTime
          ? _value.analysisTime
          : analysisTime // ignore: cast_nullable_to_non_nullable
              as double,
      contentMetadata: freezed == contentMetadata
          ? _value.contentMetadata
          : contentMetadata // ignore: cast_nullable_to_non_nullable
              as ContentMetadataModel?,
    ) as $Val);
  }

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $PlaceInfoModelCopyWith<$Res>? get placeInfo {
    if (_value.placeInfo == null) {
      return null;
    }

    return $PlaceInfoModelCopyWith<$Res>(_value.placeInfo!, (value) {
      return _then(_value.copyWith(placeInfo: value) as $Val);
    });
  }

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $ContentMetadataModelCopyWith<$Res>? get contentMetadata {
    if (_value.contentMetadata == null) {
      return null;
    }

    return $ContentMetadataModelCopyWith<$Res>(_value.contentMetadata!,
        (value) {
      return _then(_value.copyWith(contentMetadata: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$AnalysisResultDataImplCopyWith<$Res>
    implements $AnalysisResultDataCopyWith<$Res> {
  factory _$$AnalysisResultDataImplCopyWith(_$AnalysisResultDataImpl value,
          $Res Function(_$AnalysisResultDataImpl) then) =
      __$$AnalysisResultDataImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'place_info') PlaceInfoModel? placeInfo,
      double confidence,
      @JsonKey(name: 'analysis_time') double analysisTime,
      @JsonKey(name: 'content_metadata')
      ContentMetadataModel? contentMetadata});

  @override
  $PlaceInfoModelCopyWith<$Res>? get placeInfo;
  @override
  $ContentMetadataModelCopyWith<$Res>? get contentMetadata;
}

/// @nodoc
class __$$AnalysisResultDataImplCopyWithImpl<$Res>
    extends _$AnalysisResultDataCopyWithImpl<$Res, _$AnalysisResultDataImpl>
    implements _$$AnalysisResultDataImplCopyWith<$Res> {
  __$$AnalysisResultDataImplCopyWithImpl(_$AnalysisResultDataImpl _value,
      $Res Function(_$AnalysisResultDataImpl) _then)
      : super(_value, _then);

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeInfo = freezed,
    Object? confidence = null,
    Object? analysisTime = null,
    Object? contentMetadata = freezed,
  }) {
    return _then(_$AnalysisResultDataImpl(
      placeInfo: freezed == placeInfo
          ? _value.placeInfo
          : placeInfo // ignore: cast_nullable_to_non_nullable
              as PlaceInfoModel?,
      confidence: null == confidence
          ? _value.confidence
          : confidence // ignore: cast_nullable_to_non_nullable
              as double,
      analysisTime: null == analysisTime
          ? _value.analysisTime
          : analysisTime // ignore: cast_nullable_to_non_nullable
              as double,
      contentMetadata: freezed == contentMetadata
          ? _value.contentMetadata
          : contentMetadata // ignore: cast_nullable_to_non_nullable
              as ContentMetadataModel?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$AnalysisResultDataImpl implements _AnalysisResultData {
  const _$AnalysisResultDataImpl(
      {@JsonKey(name: 'place_info') this.placeInfo,
      this.confidence = 0.0,
      @JsonKey(name: 'analysis_time') this.analysisTime = 0.0,
      @JsonKey(name: 'content_metadata') this.contentMetadata});

  factory _$AnalysisResultDataImpl.fromJson(Map<String, dynamic> json) =>
      _$$AnalysisResultDataImplFromJson(json);

  @override
  @JsonKey(name: 'place_info')
  final PlaceInfoModel? placeInfo;
  @override
  @JsonKey()
  final double confidence;
  @override
  @JsonKey(name: 'analysis_time')
  final double analysisTime;
  @override
  @JsonKey(name: 'content_metadata')
  final ContentMetadataModel? contentMetadata;

  @override
  String toString() {
    return 'AnalysisResultData(placeInfo: $placeInfo, confidence: $confidence, analysisTime: $analysisTime, contentMetadata: $contentMetadata)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AnalysisResultDataImpl &&
            (identical(other.placeInfo, placeInfo) ||
                other.placeInfo == placeInfo) &&
            (identical(other.confidence, confidence) ||
                other.confidence == confidence) &&
            (identical(other.analysisTime, analysisTime) ||
                other.analysisTime == analysisTime) &&
            (identical(other.contentMetadata, contentMetadata) ||
                other.contentMetadata == contentMetadata));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType, placeInfo, confidence, analysisTime, contentMetadata);

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AnalysisResultDataImplCopyWith<_$AnalysisResultDataImpl> get copyWith =>
      __$$AnalysisResultDataImplCopyWithImpl<_$AnalysisResultDataImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AnalysisResultDataImplToJson(
      this,
    );
  }
}

abstract class _AnalysisResultData implements AnalysisResultData {
  const factory _AnalysisResultData(
      {@JsonKey(name: 'place_info') final PlaceInfoModel? placeInfo,
      final double confidence,
      @JsonKey(name: 'analysis_time') final double analysisTime,
      @JsonKey(name: 'content_metadata')
      final ContentMetadataModel? contentMetadata}) = _$AnalysisResultDataImpl;

  factory _AnalysisResultData.fromJson(Map<String, dynamic> json) =
      _$AnalysisResultDataImpl.fromJson;

  @override
  @JsonKey(name: 'place_info')
  PlaceInfoModel? get placeInfo;
  @override
  double get confidence;
  @override
  @JsonKey(name: 'analysis_time')
  double get analysisTime;
  @override
  @JsonKey(name: 'content_metadata')
  ContentMetadataModel? get contentMetadata;

  /// Create a copy of AnalysisResultData
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AnalysisResultDataImplCopyWith<_$AnalysisResultDataImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

PlaceInfoModel _$PlaceInfoModelFromJson(Map<String, dynamic> json) {
  return _PlaceInfoModel.fromJson(json);
}

/// @nodoc
mixin _$PlaceInfoModel {
  String get name => throw _privateConstructorUsedError;
  String? get address => throw _privateConstructorUsedError;
  String? get category => throw _privateConstructorUsedError;
  List<String> get tags => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  double? get rating => throw _privateConstructorUsedError;
  CoordinatesModel? get coordinates => throw _privateConstructorUsedError;

  /// Serializes this PlaceInfoModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PlaceInfoModelCopyWith<PlaceInfoModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlaceInfoModelCopyWith<$Res> {
  factory $PlaceInfoModelCopyWith(
          PlaceInfoModel value, $Res Function(PlaceInfoModel) then) =
      _$PlaceInfoModelCopyWithImpl<$Res, PlaceInfoModel>;
  @useResult
  $Res call(
      {String name,
      String? address,
      String? category,
      List<String> tags,
      String? description,
      double? rating,
      CoordinatesModel? coordinates});

  $CoordinatesModelCopyWith<$Res>? get coordinates;
}

/// @nodoc
class _$PlaceInfoModelCopyWithImpl<$Res, $Val extends PlaceInfoModel>
    implements $PlaceInfoModelCopyWith<$Res> {
  _$PlaceInfoModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? address = freezed,
    Object? category = freezed,
    Object? tags = null,
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
      tags: null == tags
          ? _value.tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
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
              as CoordinatesModel?,
    ) as $Val);
  }

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $CoordinatesModelCopyWith<$Res>? get coordinates {
    if (_value.coordinates == null) {
      return null;
    }

    return $CoordinatesModelCopyWith<$Res>(_value.coordinates!, (value) {
      return _then(_value.copyWith(coordinates: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PlaceInfoModelImplCopyWith<$Res>
    implements $PlaceInfoModelCopyWith<$Res> {
  factory _$$PlaceInfoModelImplCopyWith(_$PlaceInfoModelImpl value,
          $Res Function(_$PlaceInfoModelImpl) then) =
      __$$PlaceInfoModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String name,
      String? address,
      String? category,
      List<String> tags,
      String? description,
      double? rating,
      CoordinatesModel? coordinates});

  @override
  $CoordinatesModelCopyWith<$Res>? get coordinates;
}

/// @nodoc
class __$$PlaceInfoModelImplCopyWithImpl<$Res>
    extends _$PlaceInfoModelCopyWithImpl<$Res, _$PlaceInfoModelImpl>
    implements _$$PlaceInfoModelImplCopyWith<$Res> {
  __$$PlaceInfoModelImplCopyWithImpl(
      _$PlaceInfoModelImpl _value, $Res Function(_$PlaceInfoModelImpl) _then)
      : super(_value, _then);

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? name = null,
    Object? address = freezed,
    Object? category = freezed,
    Object? tags = null,
    Object? description = freezed,
    Object? rating = freezed,
    Object? coordinates = freezed,
  }) {
    return _then(_$PlaceInfoModelImpl(
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
      tags: null == tags
          ? _value._tags
          : tags // ignore: cast_nullable_to_non_nullable
              as List<String>,
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
              as CoordinatesModel?,
    ));
  }
}

/// @nodoc
@JsonSerializable()
class _$PlaceInfoModelImpl implements _PlaceInfoModel {
  const _$PlaceInfoModelImpl(
      {required this.name,
      this.address,
      this.category,
      final List<String> tags = const [],
      this.description,
      this.rating,
      this.coordinates})
      : _tags = tags;

  factory _$PlaceInfoModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$PlaceInfoModelImplFromJson(json);

  @override
  final String name;
  @override
  final String? address;
  @override
  final String? category;
  final List<String> _tags;
  @override
  @JsonKey()
  List<String> get tags {
    if (_tags is EqualUnmodifiableListView) return _tags;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_tags);
  }

  @override
  final String? description;
  @override
  final double? rating;
  @override
  final CoordinatesModel? coordinates;

  @override
  String toString() {
    return 'PlaceInfoModel(name: $name, address: $address, category: $category, tags: $tags, description: $description, rating: $rating, coordinates: $coordinates)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlaceInfoModelImpl &&
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

  @JsonKey(includeFromJson: false, includeToJson: false)
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

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PlaceInfoModelImplCopyWith<_$PlaceInfoModelImpl> get copyWith =>
      __$$PlaceInfoModelImplCopyWithImpl<_$PlaceInfoModelImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PlaceInfoModelImplToJson(
      this,
    );
  }
}

abstract class _PlaceInfoModel implements PlaceInfoModel {
  const factory _PlaceInfoModel(
      {required final String name,
      final String? address,
      final String? category,
      final List<String> tags,
      final String? description,
      final double? rating,
      final CoordinatesModel? coordinates}) = _$PlaceInfoModelImpl;

  factory _PlaceInfoModel.fromJson(Map<String, dynamic> json) =
      _$PlaceInfoModelImpl.fromJson;

  @override
  String get name;
  @override
  String? get address;
  @override
  String? get category;
  @override
  List<String> get tags;
  @override
  String? get description;
  @override
  double? get rating;
  @override
  CoordinatesModel? get coordinates;

  /// Create a copy of PlaceInfoModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PlaceInfoModelImplCopyWith<_$PlaceInfoModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

CoordinatesModel _$CoordinatesModelFromJson(Map<String, dynamic> json) {
  return _CoordinatesModel.fromJson(json);
}

/// @nodoc
mixin _$CoordinatesModel {
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;

  /// Serializes this CoordinatesModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of CoordinatesModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CoordinatesModelCopyWith<CoordinatesModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CoordinatesModelCopyWith<$Res> {
  factory $CoordinatesModelCopyWith(
          CoordinatesModel value, $Res Function(CoordinatesModel) then) =
      _$CoordinatesModelCopyWithImpl<$Res, CoordinatesModel>;
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class _$CoordinatesModelCopyWithImpl<$Res, $Val extends CoordinatesModel>
    implements $CoordinatesModelCopyWith<$Res> {
  _$CoordinatesModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CoordinatesModel
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
abstract class _$$CoordinatesModelImplCopyWith<$Res>
    implements $CoordinatesModelCopyWith<$Res> {
  factory _$$CoordinatesModelImplCopyWith(_$CoordinatesModelImpl value,
          $Res Function(_$CoordinatesModelImpl) then) =
      __$$CoordinatesModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class __$$CoordinatesModelImplCopyWithImpl<$Res>
    extends _$CoordinatesModelCopyWithImpl<$Res, _$CoordinatesModelImpl>
    implements _$$CoordinatesModelImplCopyWith<$Res> {
  __$$CoordinatesModelImplCopyWithImpl(_$CoordinatesModelImpl _value,
      $Res Function(_$CoordinatesModelImpl) _then)
      : super(_value, _then);

  /// Create a copy of CoordinatesModel
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
  }) {
    return _then(_$CoordinatesModelImpl(
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
@JsonSerializable()
class _$CoordinatesModelImpl implements _CoordinatesModel {
  const _$CoordinatesModelImpl(
      {required this.latitude, required this.longitude});

  factory _$CoordinatesModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$CoordinatesModelImplFromJson(json);

  @override
  final double latitude;
  @override
  final double longitude;

  @override
  String toString() {
    return 'CoordinatesModel(latitude: $latitude, longitude: $longitude)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CoordinatesModelImpl &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(runtimeType, latitude, longitude);

  /// Create a copy of CoordinatesModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CoordinatesModelImplCopyWith<_$CoordinatesModelImpl> get copyWith =>
      __$$CoordinatesModelImplCopyWithImpl<_$CoordinatesModelImpl>(
          this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$CoordinatesModelImplToJson(
      this,
    );
  }
}

abstract class _CoordinatesModel implements CoordinatesModel {
  const factory _CoordinatesModel(
      {required final double latitude,
      required final double longitude}) = _$CoordinatesModelImpl;

  factory _CoordinatesModel.fromJson(Map<String, dynamic> json) =
      _$CoordinatesModelImpl.fromJson;

  @override
  double get latitude;
  @override
  double get longitude;

  /// Create a copy of CoordinatesModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CoordinatesModelImplCopyWith<_$CoordinatesModelImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

ContentMetadataModel _$ContentMetadataModelFromJson(Map<String, dynamic> json) {
  return _ContentMetadataModel.fromJson(json);
}

/// @nodoc
mixin _$ContentMetadataModel {
  String? get title => throw _privateConstructorUsedError;
  String? get description => throw _privateConstructorUsedError;
  List<String> get images => throw _privateConstructorUsedError;
  List<String> get hashtags => throw _privateConstructorUsedError;
  @JsonKey(name: 'extraction_time')
  double? get extractionTime => throw _privateConstructorUsedError;

  /// Serializes this ContentMetadataModel to a JSON map.
  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;

  /// Create a copy of ContentMetadataModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ContentMetadataModelCopyWith<ContentMetadataModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ContentMetadataModelCopyWith<$Res> {
  factory $ContentMetadataModelCopyWith(ContentMetadataModel value,
          $Res Function(ContentMetadataModel) then) =
      _$ContentMetadataModelCopyWithImpl<$Res, ContentMetadataModel>;
  @useResult
  $Res call(
      {String? title,
      String? description,
      List<String> images,
      List<String> hashtags,
      @JsonKey(name: 'extraction_time') double? extractionTime});
}

/// @nodoc
class _$ContentMetadataModelCopyWithImpl<$Res,
        $Val extends ContentMetadataModel>
    implements $ContentMetadataModelCopyWith<$Res> {
  _$ContentMetadataModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ContentMetadataModel
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
abstract class _$$ContentMetadataModelImplCopyWith<$Res>
    implements $ContentMetadataModelCopyWith<$Res> {
  factory _$$ContentMetadataModelImplCopyWith(_$ContentMetadataModelImpl value,
          $Res Function(_$ContentMetadataModelImpl) then) =
      __$$ContentMetadataModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String? title,
      String? description,
      List<String> images,
      List<String> hashtags,
      @JsonKey(name: 'extraction_time') double? extractionTime});
}

/// @nodoc
class __$$ContentMetadataModelImplCopyWithImpl<$Res>
    extends _$ContentMetadataModelCopyWithImpl<$Res, _$ContentMetadataModelImpl>
    implements _$$ContentMetadataModelImplCopyWith<$Res> {
  __$$ContentMetadataModelImplCopyWithImpl(_$ContentMetadataModelImpl _value,
      $Res Function(_$ContentMetadataModelImpl) _then)
      : super(_value, _then);

  /// Create a copy of ContentMetadataModel
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
    return _then(_$ContentMetadataModelImpl(
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
@JsonSerializable()
class _$ContentMetadataModelImpl implements _ContentMetadataModel {
  const _$ContentMetadataModelImpl(
      {this.title,
      this.description,
      final List<String> images = const [],
      final List<String> hashtags = const [],
      @JsonKey(name: 'extraction_time') this.extractionTime})
      : _images = images,
        _hashtags = hashtags;

  factory _$ContentMetadataModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ContentMetadataModelImplFromJson(json);

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
  @JsonKey(name: 'extraction_time')
  final double? extractionTime;

  @override
  String toString() {
    return 'ContentMetadataModel(title: $title, description: $description, images: $images, hashtags: $hashtags, extractionTime: $extractionTime)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ContentMetadataModelImpl &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.description, description) ||
                other.description == description) &&
            const DeepCollectionEquality().equals(other._images, _images) &&
            const DeepCollectionEquality().equals(other._hashtags, _hashtags) &&
            (identical(other.extractionTime, extractionTime) ||
                other.extractionTime == extractionTime));
  }

  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  int get hashCode => Object.hash(
      runtimeType,
      title,
      description,
      const DeepCollectionEquality().hash(_images),
      const DeepCollectionEquality().hash(_hashtags),
      extractionTime);

  /// Create a copy of ContentMetadataModel
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ContentMetadataModelImplCopyWith<_$ContentMetadataModelImpl>
      get copyWith =>
          __$$ContentMetadataModelImplCopyWithImpl<_$ContentMetadataModelImpl>(
              this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ContentMetadataModelImplToJson(
      this,
    );
  }
}

abstract class _ContentMetadataModel implements ContentMetadataModel {
  const factory _ContentMetadataModel(
          {final String? title,
          final String? description,
          final List<String> images,
          final List<String> hashtags,
          @JsonKey(name: 'extraction_time') final double? extractionTime}) =
      _$ContentMetadataModelImpl;

  factory _ContentMetadataModel.fromJson(Map<String, dynamic> json) =
      _$ContentMetadataModelImpl.fromJson;

  @override
  String? get title;
  @override
  String? get description;
  @override
  List<String> get images;
  @override
  List<String> get hashtags;
  @override
  @JsonKey(name: 'extraction_time')
  double? get extractionTime;

  /// Create a copy of ContentMetadataModel
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ContentMetadataModelImplCopyWith<_$ContentMetadataModelImpl>
      get copyWith => throw _privateConstructorUsedError;
}
