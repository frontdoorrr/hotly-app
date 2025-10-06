// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'map_entities.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$CoordinatePoint {
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;

  /// Create a copy of CoordinatePoint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CoordinatePointCopyWith<CoordinatePoint> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CoordinatePointCopyWith<$Res> {
  factory $CoordinatePointCopyWith(
          CoordinatePoint value, $Res Function(CoordinatePoint) then) =
      _$CoordinatePointCopyWithImpl<$Res, CoordinatePoint>;
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class _$CoordinatePointCopyWithImpl<$Res, $Val extends CoordinatePoint>
    implements $CoordinatePointCopyWith<$Res> {
  _$CoordinatePointCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CoordinatePoint
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
abstract class _$$CoordinatePointImplCopyWith<$Res>
    implements $CoordinatePointCopyWith<$Res> {
  factory _$$CoordinatePointImplCopyWith(_$CoordinatePointImpl value,
          $Res Function(_$CoordinatePointImpl) then) =
      __$$CoordinatePointImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double latitude, double longitude});
}

/// @nodoc
class __$$CoordinatePointImplCopyWithImpl<$Res>
    extends _$CoordinatePointCopyWithImpl<$Res, _$CoordinatePointImpl>
    implements _$$CoordinatePointImplCopyWith<$Res> {
  __$$CoordinatePointImplCopyWithImpl(
      _$CoordinatePointImpl _value, $Res Function(_$CoordinatePointImpl) _then)
      : super(_value, _then);

  /// Create a copy of CoordinatePoint
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
  }) {
    return _then(_$CoordinatePointImpl(
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

class _$CoordinatePointImpl implements _CoordinatePoint {
  const _$CoordinatePointImpl(
      {required this.latitude, required this.longitude});

  @override
  final double latitude;
  @override
  final double longitude;

  @override
  String toString() {
    return 'CoordinatePoint(latitude: $latitude, longitude: $longitude)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CoordinatePointImpl &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude));
  }

  @override
  int get hashCode => Object.hash(runtimeType, latitude, longitude);

  /// Create a copy of CoordinatePoint
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CoordinatePointImplCopyWith<_$CoordinatePointImpl> get copyWith =>
      __$$CoordinatePointImplCopyWithImpl<_$CoordinatePointImpl>(
          this, _$identity);
}

abstract class _CoordinatePoint implements CoordinatePoint {
  const factory _CoordinatePoint(
      {required final double latitude,
      required final double longitude}) = _$CoordinatePointImpl;

  @override
  double get latitude;
  @override
  double get longitude;

  /// Create a copy of CoordinatePoint
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CoordinatePointImplCopyWith<_$CoordinatePointImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$AddressSearchResult {
  String get address => throw _privateConstructorUsedError;
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  String? get roadAddress => throw _privateConstructorUsedError;
  String? get jibunAddress => throw _privateConstructorUsedError;
  String? get buildingName => throw _privateConstructorUsedError;

  /// Create a copy of AddressSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $AddressSearchResultCopyWith<AddressSearchResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AddressSearchResultCopyWith<$Res> {
  factory $AddressSearchResultCopyWith(
          AddressSearchResult value, $Res Function(AddressSearchResult) then) =
      _$AddressSearchResultCopyWithImpl<$Res, AddressSearchResult>;
  @useResult
  $Res call(
      {String address,
      double latitude,
      double longitude,
      String? roadAddress,
      String? jibunAddress,
      String? buildingName});
}

/// @nodoc
class _$AddressSearchResultCopyWithImpl<$Res, $Val extends AddressSearchResult>
    implements $AddressSearchResultCopyWith<$Res> {
  _$AddressSearchResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of AddressSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = null,
    Object? latitude = null,
    Object? longitude = null,
    Object? roadAddress = freezed,
    Object? jibunAddress = freezed,
    Object? buildingName = freezed,
  }) {
    return _then(_value.copyWith(
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      jibunAddress: freezed == jibunAddress
          ? _value.jibunAddress
          : jibunAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$AddressSearchResultImplCopyWith<$Res>
    implements $AddressSearchResultCopyWith<$Res> {
  factory _$$AddressSearchResultImplCopyWith(_$AddressSearchResultImpl value,
          $Res Function(_$AddressSearchResultImpl) then) =
      __$$AddressSearchResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String address,
      double latitude,
      double longitude,
      String? roadAddress,
      String? jibunAddress,
      String? buildingName});
}

/// @nodoc
class __$$AddressSearchResultImplCopyWithImpl<$Res>
    extends _$AddressSearchResultCopyWithImpl<$Res, _$AddressSearchResultImpl>
    implements _$$AddressSearchResultImplCopyWith<$Res> {
  __$$AddressSearchResultImplCopyWithImpl(_$AddressSearchResultImpl _value,
      $Res Function(_$AddressSearchResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of AddressSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? address = null,
    Object? latitude = null,
    Object? longitude = null,
    Object? roadAddress = freezed,
    Object? jibunAddress = freezed,
    Object? buildingName = freezed,
  }) {
    return _then(_$AddressSearchResultImpl(
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      jibunAddress: freezed == jibunAddress
          ? _value.jibunAddress
          : jibunAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      buildingName: freezed == buildingName
          ? _value.buildingName
          : buildingName // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$AddressSearchResultImpl implements _AddressSearchResult {
  const _$AddressSearchResultImpl(
      {required this.address,
      required this.latitude,
      required this.longitude,
      this.roadAddress,
      this.jibunAddress,
      this.buildingName});

  @override
  final String address;
  @override
  final double latitude;
  @override
  final double longitude;
  @override
  final String? roadAddress;
  @override
  final String? jibunAddress;
  @override
  final String? buildingName;

  @override
  String toString() {
    return 'AddressSearchResult(address: $address, latitude: $latitude, longitude: $longitude, roadAddress: $roadAddress, jibunAddress: $jibunAddress, buildingName: $buildingName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AddressSearchResultImpl &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude) &&
            (identical(other.roadAddress, roadAddress) ||
                other.roadAddress == roadAddress) &&
            (identical(other.jibunAddress, jibunAddress) ||
                other.jibunAddress == jibunAddress) &&
            (identical(other.buildingName, buildingName) ||
                other.buildingName == buildingName));
  }

  @override
  int get hashCode => Object.hash(runtimeType, address, latitude, longitude,
      roadAddress, jibunAddress, buildingName);

  /// Create a copy of AddressSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$AddressSearchResultImplCopyWith<_$AddressSearchResultImpl> get copyWith =>
      __$$AddressSearchResultImplCopyWithImpl<_$AddressSearchResultImpl>(
          this, _$identity);
}

abstract class _AddressSearchResult implements AddressSearchResult {
  const factory _AddressSearchResult(
      {required final String address,
      required final double latitude,
      required final double longitude,
      final String? roadAddress,
      final String? jibunAddress,
      final String? buildingName}) = _$AddressSearchResultImpl;

  @override
  String get address;
  @override
  double get latitude;
  @override
  double get longitude;
  @override
  String? get roadAddress;
  @override
  String? get jibunAddress;
  @override
  String? get buildingName;

  /// Create a copy of AddressSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$AddressSearchResultImplCopyWith<_$AddressSearchResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ReverseGeocodeResult {
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  String? get roadAddress => throw _privateConstructorUsedError;
  String? get jibunAddress => throw _privateConstructorUsedError;
  String? get region1depth => throw _privateConstructorUsedError;
  String? get region2depth => throw _privateConstructorUsedError;
  String? get region3depth => throw _privateConstructorUsedError;

  /// Create a copy of ReverseGeocodeResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $ReverseGeocodeResultCopyWith<ReverseGeocodeResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ReverseGeocodeResultCopyWith<$Res> {
  factory $ReverseGeocodeResultCopyWith(ReverseGeocodeResult value,
          $Res Function(ReverseGeocodeResult) then) =
      _$ReverseGeocodeResultCopyWithImpl<$Res, ReverseGeocodeResult>;
  @useResult
  $Res call(
      {double latitude,
      double longitude,
      String? roadAddress,
      String? jibunAddress,
      String? region1depth,
      String? region2depth,
      String? region3depth});
}

/// @nodoc
class _$ReverseGeocodeResultCopyWithImpl<$Res,
        $Val extends ReverseGeocodeResult>
    implements $ReverseGeocodeResultCopyWith<$Res> {
  _$ReverseGeocodeResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of ReverseGeocodeResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
    Object? roadAddress = freezed,
    Object? jibunAddress = freezed,
    Object? region1depth = freezed,
    Object? region2depth = freezed,
    Object? region3depth = freezed,
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
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      jibunAddress: freezed == jibunAddress
          ? _value.jibunAddress
          : jibunAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      region1depth: freezed == region1depth
          ? _value.region1depth
          : region1depth // ignore: cast_nullable_to_non_nullable
              as String?,
      region2depth: freezed == region2depth
          ? _value.region2depth
          : region2depth // ignore: cast_nullable_to_non_nullable
              as String?,
      region3depth: freezed == region3depth
          ? _value.region3depth
          : region3depth // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ReverseGeocodeResultImplCopyWith<$Res>
    implements $ReverseGeocodeResultCopyWith<$Res> {
  factory _$$ReverseGeocodeResultImplCopyWith(_$ReverseGeocodeResultImpl value,
          $Res Function(_$ReverseGeocodeResultImpl) then) =
      __$$ReverseGeocodeResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double latitude,
      double longitude,
      String? roadAddress,
      String? jibunAddress,
      String? region1depth,
      String? region2depth,
      String? region3depth});
}

/// @nodoc
class __$$ReverseGeocodeResultImplCopyWithImpl<$Res>
    extends _$ReverseGeocodeResultCopyWithImpl<$Res, _$ReverseGeocodeResultImpl>
    implements _$$ReverseGeocodeResultImplCopyWith<$Res> {
  __$$ReverseGeocodeResultImplCopyWithImpl(_$ReverseGeocodeResultImpl _value,
      $Res Function(_$ReverseGeocodeResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of ReverseGeocodeResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? latitude = null,
    Object? longitude = null,
    Object? roadAddress = freezed,
    Object? jibunAddress = freezed,
    Object? region1depth = freezed,
    Object? region2depth = freezed,
    Object? region3depth = freezed,
  }) {
    return _then(_$ReverseGeocodeResultImpl(
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      jibunAddress: freezed == jibunAddress
          ? _value.jibunAddress
          : jibunAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      region1depth: freezed == region1depth
          ? _value.region1depth
          : region1depth // ignore: cast_nullable_to_non_nullable
              as String?,
      region2depth: freezed == region2depth
          ? _value.region2depth
          : region2depth // ignore: cast_nullable_to_non_nullable
              as String?,
      region3depth: freezed == region3depth
          ? _value.region3depth
          : region3depth // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$ReverseGeocodeResultImpl implements _ReverseGeocodeResult {
  const _$ReverseGeocodeResultImpl(
      {required this.latitude,
      required this.longitude,
      this.roadAddress,
      this.jibunAddress,
      this.region1depth,
      this.region2depth,
      this.region3depth});

  @override
  final double latitude;
  @override
  final double longitude;
  @override
  final String? roadAddress;
  @override
  final String? jibunAddress;
  @override
  final String? region1depth;
  @override
  final String? region2depth;
  @override
  final String? region3depth;

  @override
  String toString() {
    return 'ReverseGeocodeResult(latitude: $latitude, longitude: $longitude, roadAddress: $roadAddress, jibunAddress: $jibunAddress, region1depth: $region1depth, region2depth: $region2depth, region3depth: $region3depth)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReverseGeocodeResultImpl &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude) &&
            (identical(other.roadAddress, roadAddress) ||
                other.roadAddress == roadAddress) &&
            (identical(other.jibunAddress, jibunAddress) ||
                other.jibunAddress == jibunAddress) &&
            (identical(other.region1depth, region1depth) ||
                other.region1depth == region1depth) &&
            (identical(other.region2depth, region2depth) ||
                other.region2depth == region2depth) &&
            (identical(other.region3depth, region3depth) ||
                other.region3depth == region3depth));
  }

  @override
  int get hashCode => Object.hash(runtimeType, latitude, longitude, roadAddress,
      jibunAddress, region1depth, region2depth, region3depth);

  /// Create a copy of ReverseGeocodeResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$ReverseGeocodeResultImplCopyWith<_$ReverseGeocodeResultImpl>
      get copyWith =>
          __$$ReverseGeocodeResultImplCopyWithImpl<_$ReverseGeocodeResultImpl>(
              this, _$identity);
}

abstract class _ReverseGeocodeResult implements ReverseGeocodeResult {
  const factory _ReverseGeocodeResult(
      {required final double latitude,
      required final double longitude,
      final String? roadAddress,
      final String? jibunAddress,
      final String? region1depth,
      final String? region2depth,
      final String? region3depth}) = _$ReverseGeocodeResultImpl;

  @override
  double get latitude;
  @override
  double get longitude;
  @override
  String? get roadAddress;
  @override
  String? get jibunAddress;
  @override
  String? get region1depth;
  @override
  String? get region2depth;
  @override
  String? get region3depth;

  /// Create a copy of ReverseGeocodeResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$ReverseGeocodeResultImplCopyWith<_$ReverseGeocodeResultImpl>
      get copyWith => throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$PlaceSearchResult {
  String get placeId => throw _privateConstructorUsedError;
  String get placeName => throw _privateConstructorUsedError;
  String get address => throw _privateConstructorUsedError;
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  String? get categoryName => throw _privateConstructorUsedError;
  String? get roadAddress => throw _privateConstructorUsedError;
  String? get phone => throw _privateConstructorUsedError;
  String? get placeUrl => throw _privateConstructorUsedError;
  double? get distance => throw _privateConstructorUsedError;

  /// Create a copy of PlaceSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $PlaceSearchResultCopyWith<PlaceSearchResult> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlaceSearchResultCopyWith<$Res> {
  factory $PlaceSearchResultCopyWith(
          PlaceSearchResult value, $Res Function(PlaceSearchResult) then) =
      _$PlaceSearchResultCopyWithImpl<$Res, PlaceSearchResult>;
  @useResult
  $Res call(
      {String placeId,
      String placeName,
      String address,
      double latitude,
      double longitude,
      String? categoryName,
      String? roadAddress,
      String? phone,
      String? placeUrl,
      double? distance});
}

/// @nodoc
class _$PlaceSearchResultCopyWithImpl<$Res, $Val extends PlaceSearchResult>
    implements $PlaceSearchResultCopyWith<$Res> {
  _$PlaceSearchResultCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of PlaceSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeId = null,
    Object? placeName = null,
    Object? address = null,
    Object? latitude = null,
    Object? longitude = null,
    Object? categoryName = freezed,
    Object? roadAddress = freezed,
    Object? phone = freezed,
    Object? placeUrl = freezed,
    Object? distance = freezed,
  }) {
    return _then(_value.copyWith(
      placeId: null == placeId
          ? _value.placeId
          : placeId // ignore: cast_nullable_to_non_nullable
              as String,
      placeName: null == placeName
          ? _value.placeName
          : placeName // ignore: cast_nullable_to_non_nullable
              as String,
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
      categoryName: freezed == categoryName
          ? _value.categoryName
          : categoryName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      phone: freezed == phone
          ? _value.phone
          : phone // ignore: cast_nullable_to_non_nullable
              as String?,
      placeUrl: freezed == placeUrl
          ? _value.placeUrl
          : placeUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      distance: freezed == distance
          ? _value.distance
          : distance // ignore: cast_nullable_to_non_nullable
              as double?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$PlaceSearchResultImplCopyWith<$Res>
    implements $PlaceSearchResultCopyWith<$Res> {
  factory _$$PlaceSearchResultImplCopyWith(_$PlaceSearchResultImpl value,
          $Res Function(_$PlaceSearchResultImpl) then) =
      __$$PlaceSearchResultImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String placeId,
      String placeName,
      String address,
      double latitude,
      double longitude,
      String? categoryName,
      String? roadAddress,
      String? phone,
      String? placeUrl,
      double? distance});
}

/// @nodoc
class __$$PlaceSearchResultImplCopyWithImpl<$Res>
    extends _$PlaceSearchResultCopyWithImpl<$Res, _$PlaceSearchResultImpl>
    implements _$$PlaceSearchResultImplCopyWith<$Res> {
  __$$PlaceSearchResultImplCopyWithImpl(_$PlaceSearchResultImpl _value,
      $Res Function(_$PlaceSearchResultImpl) _then)
      : super(_value, _then);

  /// Create a copy of PlaceSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? placeId = null,
    Object? placeName = null,
    Object? address = null,
    Object? latitude = null,
    Object? longitude = null,
    Object? categoryName = freezed,
    Object? roadAddress = freezed,
    Object? phone = freezed,
    Object? placeUrl = freezed,
    Object? distance = freezed,
  }) {
    return _then(_$PlaceSearchResultImpl(
      placeId: null == placeId
          ? _value.placeId
          : placeId // ignore: cast_nullable_to_non_nullable
              as String,
      placeName: null == placeName
          ? _value.placeName
          : placeName // ignore: cast_nullable_to_non_nullable
              as String,
      address: null == address
          ? _value.address
          : address // ignore: cast_nullable_to_non_nullable
              as String,
      latitude: null == latitude
          ? _value.latitude
          : latitude // ignore: cast_nullable_to_non_nullable
              as double,
      longitude: null == longitude
          ? _value.longitude
          : longitude // ignore: cast_nullable_to_non_nullable
              as double,
      categoryName: freezed == categoryName
          ? _value.categoryName
          : categoryName // ignore: cast_nullable_to_non_nullable
              as String?,
      roadAddress: freezed == roadAddress
          ? _value.roadAddress
          : roadAddress // ignore: cast_nullable_to_non_nullable
              as String?,
      phone: freezed == phone
          ? _value.phone
          : phone // ignore: cast_nullable_to_non_nullable
              as String?,
      placeUrl: freezed == placeUrl
          ? _value.placeUrl
          : placeUrl // ignore: cast_nullable_to_non_nullable
              as String?,
      distance: freezed == distance
          ? _value.distance
          : distance // ignore: cast_nullable_to_non_nullable
              as double?,
    ));
  }
}

/// @nodoc

class _$PlaceSearchResultImpl implements _PlaceSearchResult {
  const _$PlaceSearchResultImpl(
      {required this.placeId,
      required this.placeName,
      required this.address,
      required this.latitude,
      required this.longitude,
      this.categoryName,
      this.roadAddress,
      this.phone,
      this.placeUrl,
      this.distance});

  @override
  final String placeId;
  @override
  final String placeName;
  @override
  final String address;
  @override
  final double latitude;
  @override
  final double longitude;
  @override
  final String? categoryName;
  @override
  final String? roadAddress;
  @override
  final String? phone;
  @override
  final String? placeUrl;
  @override
  final double? distance;

  @override
  String toString() {
    return 'PlaceSearchResult(placeId: $placeId, placeName: $placeName, address: $address, latitude: $latitude, longitude: $longitude, categoryName: $categoryName, roadAddress: $roadAddress, phone: $phone, placeUrl: $placeUrl, distance: $distance)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlaceSearchResultImpl &&
            (identical(other.placeId, placeId) || other.placeId == placeId) &&
            (identical(other.placeName, placeName) ||
                other.placeName == placeName) &&
            (identical(other.address, address) || other.address == address) &&
            (identical(other.latitude, latitude) ||
                other.latitude == latitude) &&
            (identical(other.longitude, longitude) ||
                other.longitude == longitude) &&
            (identical(other.categoryName, categoryName) ||
                other.categoryName == categoryName) &&
            (identical(other.roadAddress, roadAddress) ||
                other.roadAddress == roadAddress) &&
            (identical(other.phone, phone) || other.phone == phone) &&
            (identical(other.placeUrl, placeUrl) ||
                other.placeUrl == placeUrl) &&
            (identical(other.distance, distance) ||
                other.distance == distance));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      placeId,
      placeName,
      address,
      latitude,
      longitude,
      categoryName,
      roadAddress,
      phone,
      placeUrl,
      distance);

  /// Create a copy of PlaceSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$PlaceSearchResultImplCopyWith<_$PlaceSearchResultImpl> get copyWith =>
      __$$PlaceSearchResultImplCopyWithImpl<_$PlaceSearchResultImpl>(
          this, _$identity);
}

abstract class _PlaceSearchResult implements PlaceSearchResult {
  const factory _PlaceSearchResult(
      {required final String placeId,
      required final String placeName,
      required final String address,
      required final double latitude,
      required final double longitude,
      final String? categoryName,
      final String? roadAddress,
      final String? phone,
      final String? placeUrl,
      final double? distance}) = _$PlaceSearchResultImpl;

  @override
  String get placeId;
  @override
  String get placeName;
  @override
  String get address;
  @override
  double get latitude;
  @override
  double get longitude;
  @override
  String? get categoryName;
  @override
  String? get roadAddress;
  @override
  String? get phone;
  @override
  String? get placeUrl;
  @override
  double? get distance;

  /// Create a copy of PlaceSearchResult
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$PlaceSearchResultImplCopyWith<_$PlaceSearchResultImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$MarkerCluster {
  String get clusterId => throw _privateConstructorUsedError;
  double get centerLatitude => throw _privateConstructorUsedError;
  double get centerLongitude => throw _privateConstructorUsedError;
  int get placeCount => throw _privateConstructorUsedError;
  List<String> get placeIds => throw _privateConstructorUsedError;
  MapBounds? get bounds => throw _privateConstructorUsedError;

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MarkerClusterCopyWith<MarkerCluster> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MarkerClusterCopyWith<$Res> {
  factory $MarkerClusterCopyWith(
          MarkerCluster value, $Res Function(MarkerCluster) then) =
      _$MarkerClusterCopyWithImpl<$Res, MarkerCluster>;
  @useResult
  $Res call(
      {String clusterId,
      double centerLatitude,
      double centerLongitude,
      int placeCount,
      List<String> placeIds,
      MapBounds? bounds});

  $MapBoundsCopyWith<$Res>? get bounds;
}

/// @nodoc
class _$MarkerClusterCopyWithImpl<$Res, $Val extends MarkerCluster>
    implements $MarkerClusterCopyWith<$Res> {
  _$MarkerClusterCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? clusterId = null,
    Object? centerLatitude = null,
    Object? centerLongitude = null,
    Object? placeCount = null,
    Object? placeIds = null,
    Object? bounds = freezed,
  }) {
    return _then(_value.copyWith(
      clusterId: null == clusterId
          ? _value.clusterId
          : clusterId // ignore: cast_nullable_to_non_nullable
              as String,
      centerLatitude: null == centerLatitude
          ? _value.centerLatitude
          : centerLatitude // ignore: cast_nullable_to_non_nullable
              as double,
      centerLongitude: null == centerLongitude
          ? _value.centerLongitude
          : centerLongitude // ignore: cast_nullable_to_non_nullable
              as double,
      placeCount: null == placeCount
          ? _value.placeCount
          : placeCount // ignore: cast_nullable_to_non_nullable
              as int,
      placeIds: null == placeIds
          ? _value.placeIds
          : placeIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      bounds: freezed == bounds
          ? _value.bounds
          : bounds // ignore: cast_nullable_to_non_nullable
              as MapBounds?,
    ) as $Val);
  }

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $MapBoundsCopyWith<$Res>? get bounds {
    if (_value.bounds == null) {
      return null;
    }

    return $MapBoundsCopyWith<$Res>(_value.bounds!, (value) {
      return _then(_value.copyWith(bounds: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MarkerClusterImplCopyWith<$Res>
    implements $MarkerClusterCopyWith<$Res> {
  factory _$$MarkerClusterImplCopyWith(
          _$MarkerClusterImpl value, $Res Function(_$MarkerClusterImpl) then) =
      __$$MarkerClusterImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String clusterId,
      double centerLatitude,
      double centerLongitude,
      int placeCount,
      List<String> placeIds,
      MapBounds? bounds});

  @override
  $MapBoundsCopyWith<$Res>? get bounds;
}

/// @nodoc
class __$$MarkerClusterImplCopyWithImpl<$Res>
    extends _$MarkerClusterCopyWithImpl<$Res, _$MarkerClusterImpl>
    implements _$$MarkerClusterImplCopyWith<$Res> {
  __$$MarkerClusterImplCopyWithImpl(
      _$MarkerClusterImpl _value, $Res Function(_$MarkerClusterImpl) _then)
      : super(_value, _then);

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? clusterId = null,
    Object? centerLatitude = null,
    Object? centerLongitude = null,
    Object? placeCount = null,
    Object? placeIds = null,
    Object? bounds = freezed,
  }) {
    return _then(_$MarkerClusterImpl(
      clusterId: null == clusterId
          ? _value.clusterId
          : clusterId // ignore: cast_nullable_to_non_nullable
              as String,
      centerLatitude: null == centerLatitude
          ? _value.centerLatitude
          : centerLatitude // ignore: cast_nullable_to_non_nullable
              as double,
      centerLongitude: null == centerLongitude
          ? _value.centerLongitude
          : centerLongitude // ignore: cast_nullable_to_non_nullable
              as double,
      placeCount: null == placeCount
          ? _value.placeCount
          : placeCount // ignore: cast_nullable_to_non_nullable
              as int,
      placeIds: null == placeIds
          ? _value._placeIds
          : placeIds // ignore: cast_nullable_to_non_nullable
              as List<String>,
      bounds: freezed == bounds
          ? _value.bounds
          : bounds // ignore: cast_nullable_to_non_nullable
              as MapBounds?,
    ));
  }
}

/// @nodoc

class _$MarkerClusterImpl implements _MarkerCluster {
  const _$MarkerClusterImpl(
      {required this.clusterId,
      required this.centerLatitude,
      required this.centerLongitude,
      required this.placeCount,
      required final List<String> placeIds,
      this.bounds})
      : _placeIds = placeIds;

  @override
  final String clusterId;
  @override
  final double centerLatitude;
  @override
  final double centerLongitude;
  @override
  final int placeCount;
  final List<String> _placeIds;
  @override
  List<String> get placeIds {
    if (_placeIds is EqualUnmodifiableListView) return _placeIds;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_placeIds);
  }

  @override
  final MapBounds? bounds;

  @override
  String toString() {
    return 'MarkerCluster(clusterId: $clusterId, centerLatitude: $centerLatitude, centerLongitude: $centerLongitude, placeCount: $placeCount, placeIds: $placeIds, bounds: $bounds)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MarkerClusterImpl &&
            (identical(other.clusterId, clusterId) ||
                other.clusterId == clusterId) &&
            (identical(other.centerLatitude, centerLatitude) ||
                other.centerLatitude == centerLatitude) &&
            (identical(other.centerLongitude, centerLongitude) ||
                other.centerLongitude == centerLongitude) &&
            (identical(other.placeCount, placeCount) ||
                other.placeCount == placeCount) &&
            const DeepCollectionEquality().equals(other._placeIds, _placeIds) &&
            (identical(other.bounds, bounds) || other.bounds == bounds));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      clusterId,
      centerLatitude,
      centerLongitude,
      placeCount,
      const DeepCollectionEquality().hash(_placeIds),
      bounds);

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MarkerClusterImplCopyWith<_$MarkerClusterImpl> get copyWith =>
      __$$MarkerClusterImplCopyWithImpl<_$MarkerClusterImpl>(this, _$identity);
}

abstract class _MarkerCluster implements MarkerCluster {
  const factory _MarkerCluster(
      {required final String clusterId,
      required final double centerLatitude,
      required final double centerLongitude,
      required final int placeCount,
      required final List<String> placeIds,
      final MapBounds? bounds}) = _$MarkerClusterImpl;

  @override
  String get clusterId;
  @override
  double get centerLatitude;
  @override
  double get centerLongitude;
  @override
  int get placeCount;
  @override
  List<String> get placeIds;
  @override
  MapBounds? get bounds;

  /// Create a copy of MarkerCluster
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MarkerClusterImplCopyWith<_$MarkerClusterImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$MapBounds {
  double get north => throw _privateConstructorUsedError;
  double get south => throw _privateConstructorUsedError;
  double get east => throw _privateConstructorUsedError;
  double get west => throw _privateConstructorUsedError;

  /// Create a copy of MapBounds
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MapBoundsCopyWith<MapBounds> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MapBoundsCopyWith<$Res> {
  factory $MapBoundsCopyWith(MapBounds value, $Res Function(MapBounds) then) =
      _$MapBoundsCopyWithImpl<$Res, MapBounds>;
  @useResult
  $Res call({double north, double south, double east, double west});
}

/// @nodoc
class _$MapBoundsCopyWithImpl<$Res, $Val extends MapBounds>
    implements $MapBoundsCopyWith<$Res> {
  _$MapBoundsCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MapBounds
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? north = null,
    Object? south = null,
    Object? east = null,
    Object? west = null,
  }) {
    return _then(_value.copyWith(
      north: null == north
          ? _value.north
          : north // ignore: cast_nullable_to_non_nullable
              as double,
      south: null == south
          ? _value.south
          : south // ignore: cast_nullable_to_non_nullable
              as double,
      east: null == east
          ? _value.east
          : east // ignore: cast_nullable_to_non_nullable
              as double,
      west: null == west
          ? _value.west
          : west // ignore: cast_nullable_to_non_nullable
              as double,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$MapBoundsImplCopyWith<$Res>
    implements $MapBoundsCopyWith<$Res> {
  factory _$$MapBoundsImplCopyWith(
          _$MapBoundsImpl value, $Res Function(_$MapBoundsImpl) then) =
      __$$MapBoundsImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call({double north, double south, double east, double west});
}

/// @nodoc
class __$$MapBoundsImplCopyWithImpl<$Res>
    extends _$MapBoundsCopyWithImpl<$Res, _$MapBoundsImpl>
    implements _$$MapBoundsImplCopyWith<$Res> {
  __$$MapBoundsImplCopyWithImpl(
      _$MapBoundsImpl _value, $Res Function(_$MapBoundsImpl) _then)
      : super(_value, _then);

  /// Create a copy of MapBounds
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? north = null,
    Object? south = null,
    Object? east = null,
    Object? west = null,
  }) {
    return _then(_$MapBoundsImpl(
      north: null == north
          ? _value.north
          : north // ignore: cast_nullable_to_non_nullable
              as double,
      south: null == south
          ? _value.south
          : south // ignore: cast_nullable_to_non_nullable
              as double,
      east: null == east
          ? _value.east
          : east // ignore: cast_nullable_to_non_nullable
              as double,
      west: null == west
          ? _value.west
          : west // ignore: cast_nullable_to_non_nullable
              as double,
    ));
  }
}

/// @nodoc

class _$MapBoundsImpl implements _MapBounds {
  const _$MapBoundsImpl(
      {required this.north,
      required this.south,
      required this.east,
      required this.west});

  @override
  final double north;
  @override
  final double south;
  @override
  final double east;
  @override
  final double west;

  @override
  String toString() {
    return 'MapBounds(north: $north, south: $south, east: $east, west: $west)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MapBoundsImpl &&
            (identical(other.north, north) || other.north == north) &&
            (identical(other.south, south) || other.south == south) &&
            (identical(other.east, east) || other.east == east) &&
            (identical(other.west, west) || other.west == west));
  }

  @override
  int get hashCode => Object.hash(runtimeType, north, south, east, west);

  /// Create a copy of MapBounds
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MapBoundsImplCopyWith<_$MapBoundsImpl> get copyWith =>
      __$$MapBoundsImplCopyWithImpl<_$MapBoundsImpl>(this, _$identity);
}

abstract class _MapBounds implements MapBounds {
  const factory _MapBounds(
      {required final double north,
      required final double south,
      required final double east,
      required final double west}) = _$MapBoundsImpl;

  @override
  double get north;
  @override
  double get south;
  @override
  double get east;
  @override
  double get west;

  /// Create a copy of MapBounds
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MapBoundsImplCopyWith<_$MapBoundsImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$RoutePolyline {
  String get routeId => throw _privateConstructorUsedError;
  List<CoordinatePoint> get coordinates => throw _privateConstructorUsedError;
  double get totalDistanceKm => throw _privateConstructorUsedError;
  int get totalDurationMinutes => throw _privateConstructorUsedError;
  List<Map<String, dynamic>> get waypoints =>
      throw _privateConstructorUsedError;

  /// Create a copy of RoutePolyline
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $RoutePolylineCopyWith<RoutePolyline> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $RoutePolylineCopyWith<$Res> {
  factory $RoutePolylineCopyWith(
          RoutePolyline value, $Res Function(RoutePolyline) then) =
      _$RoutePolylineCopyWithImpl<$Res, RoutePolyline>;
  @useResult
  $Res call(
      {String routeId,
      List<CoordinatePoint> coordinates,
      double totalDistanceKm,
      int totalDurationMinutes,
      List<Map<String, dynamic>> waypoints});
}

/// @nodoc
class _$RoutePolylineCopyWithImpl<$Res, $Val extends RoutePolyline>
    implements $RoutePolylineCopyWith<$Res> {
  _$RoutePolylineCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of RoutePolyline
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? routeId = null,
    Object? coordinates = null,
    Object? totalDistanceKm = null,
    Object? totalDurationMinutes = null,
    Object? waypoints = null,
  }) {
    return _then(_value.copyWith(
      routeId: null == routeId
          ? _value.routeId
          : routeId // ignore: cast_nullable_to_non_nullable
              as String,
      coordinates: null == coordinates
          ? _value.coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as List<CoordinatePoint>,
      totalDistanceKm: null == totalDistanceKm
          ? _value.totalDistanceKm
          : totalDistanceKm // ignore: cast_nullable_to_non_nullable
              as double,
      totalDurationMinutes: null == totalDurationMinutes
          ? _value.totalDurationMinutes
          : totalDurationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      waypoints: null == waypoints
          ? _value.waypoints
          : waypoints // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$RoutePolylineImplCopyWith<$Res>
    implements $RoutePolylineCopyWith<$Res> {
  factory _$$RoutePolylineImplCopyWith(
          _$RoutePolylineImpl value, $Res Function(_$RoutePolylineImpl) then) =
      __$$RoutePolylineImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String routeId,
      List<CoordinatePoint> coordinates,
      double totalDistanceKm,
      int totalDurationMinutes,
      List<Map<String, dynamic>> waypoints});
}

/// @nodoc
class __$$RoutePolylineImplCopyWithImpl<$Res>
    extends _$RoutePolylineCopyWithImpl<$Res, _$RoutePolylineImpl>
    implements _$$RoutePolylineImplCopyWith<$Res> {
  __$$RoutePolylineImplCopyWithImpl(
      _$RoutePolylineImpl _value, $Res Function(_$RoutePolylineImpl) _then)
      : super(_value, _then);

  /// Create a copy of RoutePolyline
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? routeId = null,
    Object? coordinates = null,
    Object? totalDistanceKm = null,
    Object? totalDurationMinutes = null,
    Object? waypoints = null,
  }) {
    return _then(_$RoutePolylineImpl(
      routeId: null == routeId
          ? _value.routeId
          : routeId // ignore: cast_nullable_to_non_nullable
              as String,
      coordinates: null == coordinates
          ? _value._coordinates
          : coordinates // ignore: cast_nullable_to_non_nullable
              as List<CoordinatePoint>,
      totalDistanceKm: null == totalDistanceKm
          ? _value.totalDistanceKm
          : totalDistanceKm // ignore: cast_nullable_to_non_nullable
              as double,
      totalDurationMinutes: null == totalDurationMinutes
          ? _value.totalDurationMinutes
          : totalDurationMinutes // ignore: cast_nullable_to_non_nullable
              as int,
      waypoints: null == waypoints
          ? _value._waypoints
          : waypoints // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>,
    ));
  }
}

/// @nodoc

class _$RoutePolylineImpl implements _RoutePolyline {
  const _$RoutePolylineImpl(
      {required this.routeId,
      required final List<CoordinatePoint> coordinates,
      required this.totalDistanceKm,
      required this.totalDurationMinutes,
      required final List<Map<String, dynamic>> waypoints})
      : _coordinates = coordinates,
        _waypoints = waypoints;

  @override
  final String routeId;
  final List<CoordinatePoint> _coordinates;
  @override
  List<CoordinatePoint> get coordinates {
    if (_coordinates is EqualUnmodifiableListView) return _coordinates;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_coordinates);
  }

  @override
  final double totalDistanceKm;
  @override
  final int totalDurationMinutes;
  final List<Map<String, dynamic>> _waypoints;
  @override
  List<Map<String, dynamic>> get waypoints {
    if (_waypoints is EqualUnmodifiableListView) return _waypoints;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_waypoints);
  }

  @override
  String toString() {
    return 'RoutePolyline(routeId: $routeId, coordinates: $coordinates, totalDistanceKm: $totalDistanceKm, totalDurationMinutes: $totalDurationMinutes, waypoints: $waypoints)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$RoutePolylineImpl &&
            (identical(other.routeId, routeId) || other.routeId == routeId) &&
            const DeepCollectionEquality()
                .equals(other._coordinates, _coordinates) &&
            (identical(other.totalDistanceKm, totalDistanceKm) ||
                other.totalDistanceKm == totalDistanceKm) &&
            (identical(other.totalDurationMinutes, totalDurationMinutes) ||
                other.totalDurationMinutes == totalDurationMinutes) &&
            const DeepCollectionEquality()
                .equals(other._waypoints, _waypoints));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      routeId,
      const DeepCollectionEquality().hash(_coordinates),
      totalDistanceKm,
      totalDurationMinutes,
      const DeepCollectionEquality().hash(_waypoints));

  /// Create a copy of RoutePolyline
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$RoutePolylineImplCopyWith<_$RoutePolylineImpl> get copyWith =>
      __$$RoutePolylineImplCopyWithImpl<_$RoutePolylineImpl>(this, _$identity);
}

abstract class _RoutePolyline implements RoutePolyline {
  const factory _RoutePolyline(
          {required final String routeId,
          required final List<CoordinatePoint> coordinates,
          required final double totalDistanceKm,
          required final int totalDurationMinutes,
          required final List<Map<String, dynamic>> waypoints}) =
      _$RoutePolylineImpl;

  @override
  String get routeId;
  @override
  List<CoordinatePoint> get coordinates;
  @override
  double get totalDistanceKm;
  @override
  int get totalDurationMinutes;
  @override
  List<Map<String, dynamic>> get waypoints;

  /// Create a copy of RoutePolyline
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$RoutePolylineImplCopyWith<_$RoutePolylineImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
