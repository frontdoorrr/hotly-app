// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'map_models.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

AddressSearchResultModel _$AddressSearchResultModelFromJson(
    Map<String, dynamic> json) {
  return _AddressSearchResultModel.fromJson(json);
}

/// @nodoc
mixin _$AddressSearchResultModel {
  String get address => throw _privateConstructorUsedError;
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  @JsonKey(name: 'road_address')
  String? get roadAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'jibun_address')
  String? get jibunAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'building_name')
  String? get buildingName => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $AddressSearchResultModelCopyWith<AddressSearchResultModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $AddressSearchResultModelCopyWith<$Res> {
  factory $AddressSearchResultModelCopyWith(AddressSearchResultModel value,
          $Res Function(AddressSearchResultModel) then) =
      _$AddressSearchResultModelCopyWithImpl<$Res, AddressSearchResultModel>;
  @useResult
  $Res call(
      {String address,
      double latitude,
      double longitude,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'jibun_address') String? jibunAddress,
      @JsonKey(name: 'building_name') String? buildingName});
}

/// @nodoc
class _$AddressSearchResultModelCopyWithImpl<$Res,
        $Val extends AddressSearchResultModel>
    implements $AddressSearchResultModelCopyWith<$Res> {
  _$AddressSearchResultModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

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
abstract class _$$AddressSearchResultModelImplCopyWith<$Res>
    implements $AddressSearchResultModelCopyWith<$Res> {
  factory _$$AddressSearchResultModelImplCopyWith(
          _$AddressSearchResultModelImpl value,
          $Res Function(_$AddressSearchResultModelImpl) then) =
      __$$AddressSearchResultModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String address,
      double latitude,
      double longitude,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'jibun_address') String? jibunAddress,
      @JsonKey(name: 'building_name') String? buildingName});
}

/// @nodoc
class __$$AddressSearchResultModelImplCopyWithImpl<$Res>
    extends _$AddressSearchResultModelCopyWithImpl<$Res,
        _$AddressSearchResultModelImpl>
    implements _$$AddressSearchResultModelImplCopyWith<$Res> {
  __$$AddressSearchResultModelImplCopyWithImpl(
      _$AddressSearchResultModelImpl _value,
      $Res Function(_$AddressSearchResultModelImpl) _then)
      : super(_value, _then);

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
    return _then(_$AddressSearchResultModelImpl(
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
@JsonSerializable()
class _$AddressSearchResultModelImpl implements _AddressSearchResultModel {
  const _$AddressSearchResultModelImpl(
      {required this.address,
      required this.latitude,
      required this.longitude,
      @JsonKey(name: 'road_address') this.roadAddress,
      @JsonKey(name: 'jibun_address') this.jibunAddress,
      @JsonKey(name: 'building_name') this.buildingName});

  factory _$AddressSearchResultModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$AddressSearchResultModelImplFromJson(json);

  @override
  final String address;
  @override
  final double latitude;
  @override
  final double longitude;
  @override
  @JsonKey(name: 'road_address')
  final String? roadAddress;
  @override
  @JsonKey(name: 'jibun_address')
  final String? jibunAddress;
  @override
  @JsonKey(name: 'building_name')
  final String? buildingName;

  @override
  String toString() {
    return 'AddressSearchResultModel(address: $address, latitude: $latitude, longitude: $longitude, roadAddress: $roadAddress, jibunAddress: $jibunAddress, buildingName: $buildingName)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$AddressSearchResultModelImpl &&
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

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, address, latitude, longitude,
      roadAddress, jibunAddress, buildingName);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$AddressSearchResultModelImplCopyWith<_$AddressSearchResultModelImpl>
      get copyWith => __$$AddressSearchResultModelImplCopyWithImpl<
          _$AddressSearchResultModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$AddressSearchResultModelImplToJson(
      this,
    );
  }
}

abstract class _AddressSearchResultModel implements AddressSearchResultModel {
  const factory _AddressSearchResultModel(
          {required final String address,
          required final double latitude,
          required final double longitude,
          @JsonKey(name: 'road_address') final String? roadAddress,
          @JsonKey(name: 'jibun_address') final String? jibunAddress,
          @JsonKey(name: 'building_name') final String? buildingName}) =
      _$AddressSearchResultModelImpl;

  factory _AddressSearchResultModel.fromJson(Map<String, dynamic> json) =
      _$AddressSearchResultModelImpl.fromJson;

  @override
  String get address;
  @override
  double get latitude;
  @override
  double get longitude;
  @override
  @JsonKey(name: 'road_address')
  String? get roadAddress;
  @override
  @JsonKey(name: 'jibun_address')
  String? get jibunAddress;
  @override
  @JsonKey(name: 'building_name')
  String? get buildingName;
  @override
  @JsonKey(ignore: true)
  _$$AddressSearchResultModelImplCopyWith<_$AddressSearchResultModelImpl>
      get copyWith => throw _privateConstructorUsedError;
}

ReverseGeocodeResultModel _$ReverseGeocodeResultModelFromJson(
    Map<String, dynamic> json) {
  return _ReverseGeocodeResultModel.fromJson(json);
}

/// @nodoc
mixin _$ReverseGeocodeResultModel {
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  @JsonKey(name: 'road_address')
  String? get roadAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'jibun_address')
  String? get jibunAddress => throw _privateConstructorUsedError;
  @JsonKey(name: 'region_1depth')
  String? get region1depth => throw _privateConstructorUsedError;
  @JsonKey(name: 'region_2depth')
  String? get region2depth => throw _privateConstructorUsedError;
  @JsonKey(name: 'region_3depth')
  String? get region3depth => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $ReverseGeocodeResultModelCopyWith<ReverseGeocodeResultModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ReverseGeocodeResultModelCopyWith<$Res> {
  factory $ReverseGeocodeResultModelCopyWith(ReverseGeocodeResultModel value,
          $Res Function(ReverseGeocodeResultModel) then) =
      _$ReverseGeocodeResultModelCopyWithImpl<$Res, ReverseGeocodeResultModel>;
  @useResult
  $Res call(
      {double latitude,
      double longitude,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'jibun_address') String? jibunAddress,
      @JsonKey(name: 'region_1depth') String? region1depth,
      @JsonKey(name: 'region_2depth') String? region2depth,
      @JsonKey(name: 'region_3depth') String? region3depth});
}

/// @nodoc
class _$ReverseGeocodeResultModelCopyWithImpl<$Res,
        $Val extends ReverseGeocodeResultModel>
    implements $ReverseGeocodeResultModelCopyWith<$Res> {
  _$ReverseGeocodeResultModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

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
abstract class _$$ReverseGeocodeResultModelImplCopyWith<$Res>
    implements $ReverseGeocodeResultModelCopyWith<$Res> {
  factory _$$ReverseGeocodeResultModelImplCopyWith(
          _$ReverseGeocodeResultModelImpl value,
          $Res Function(_$ReverseGeocodeResultModelImpl) then) =
      __$$ReverseGeocodeResultModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {double latitude,
      double longitude,
      @JsonKey(name: 'road_address') String? roadAddress,
      @JsonKey(name: 'jibun_address') String? jibunAddress,
      @JsonKey(name: 'region_1depth') String? region1depth,
      @JsonKey(name: 'region_2depth') String? region2depth,
      @JsonKey(name: 'region_3depth') String? region3depth});
}

/// @nodoc
class __$$ReverseGeocodeResultModelImplCopyWithImpl<$Res>
    extends _$ReverseGeocodeResultModelCopyWithImpl<$Res,
        _$ReverseGeocodeResultModelImpl>
    implements _$$ReverseGeocodeResultModelImplCopyWith<$Res> {
  __$$ReverseGeocodeResultModelImplCopyWithImpl(
      _$ReverseGeocodeResultModelImpl _value,
      $Res Function(_$ReverseGeocodeResultModelImpl) _then)
      : super(_value, _then);

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
    return _then(_$ReverseGeocodeResultModelImpl(
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
@JsonSerializable()
class _$ReverseGeocodeResultModelImpl implements _ReverseGeocodeResultModel {
  const _$ReverseGeocodeResultModelImpl(
      {required this.latitude,
      required this.longitude,
      @JsonKey(name: 'road_address') this.roadAddress,
      @JsonKey(name: 'jibun_address') this.jibunAddress,
      @JsonKey(name: 'region_1depth') this.region1depth,
      @JsonKey(name: 'region_2depth') this.region2depth,
      @JsonKey(name: 'region_3depth') this.region3depth});

  factory _$ReverseGeocodeResultModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$ReverseGeocodeResultModelImplFromJson(json);

  @override
  final double latitude;
  @override
  final double longitude;
  @override
  @JsonKey(name: 'road_address')
  final String? roadAddress;
  @override
  @JsonKey(name: 'jibun_address')
  final String? jibunAddress;
  @override
  @JsonKey(name: 'region_1depth')
  final String? region1depth;
  @override
  @JsonKey(name: 'region_2depth')
  final String? region2depth;
  @override
  @JsonKey(name: 'region_3depth')
  final String? region3depth;

  @override
  String toString() {
    return 'ReverseGeocodeResultModel(latitude: $latitude, longitude: $longitude, roadAddress: $roadAddress, jibunAddress: $jibunAddress, region1depth: $region1depth, region2depth: $region2depth, region3depth: $region3depth)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ReverseGeocodeResultModelImpl &&
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

  @JsonKey(ignore: true)
  @override
  int get hashCode => Object.hash(runtimeType, latitude, longitude, roadAddress,
      jibunAddress, region1depth, region2depth, region3depth);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ReverseGeocodeResultModelImplCopyWith<_$ReverseGeocodeResultModelImpl>
      get copyWith => __$$ReverseGeocodeResultModelImplCopyWithImpl<
          _$ReverseGeocodeResultModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$ReverseGeocodeResultModelImplToJson(
      this,
    );
  }
}

abstract class _ReverseGeocodeResultModel implements ReverseGeocodeResultModel {
  const factory _ReverseGeocodeResultModel(
          {required final double latitude,
          required final double longitude,
          @JsonKey(name: 'road_address') final String? roadAddress,
          @JsonKey(name: 'jibun_address') final String? jibunAddress,
          @JsonKey(name: 'region_1depth') final String? region1depth,
          @JsonKey(name: 'region_2depth') final String? region2depth,
          @JsonKey(name: 'region_3depth') final String? region3depth}) =
      _$ReverseGeocodeResultModelImpl;

  factory _ReverseGeocodeResultModel.fromJson(Map<String, dynamic> json) =
      _$ReverseGeocodeResultModelImpl.fromJson;

  @override
  double get latitude;
  @override
  double get longitude;
  @override
  @JsonKey(name: 'road_address')
  String? get roadAddress;
  @override
  @JsonKey(name: 'jibun_address')
  String? get jibunAddress;
  @override
  @JsonKey(name: 'region_1depth')
  String? get region1depth;
  @override
  @JsonKey(name: 'region_2depth')
  String? get region2depth;
  @override
  @JsonKey(name: 'region_3depth')
  String? get region3depth;
  @override
  @JsonKey(ignore: true)
  _$$ReverseGeocodeResultModelImplCopyWith<_$ReverseGeocodeResultModelImpl>
      get copyWith => throw _privateConstructorUsedError;
}

PlaceSearchResultModel _$PlaceSearchResultModelFromJson(
    Map<String, dynamic> json) {
  return _PlaceSearchResultModel.fromJson(json);
}

/// @nodoc
mixin _$PlaceSearchResultModel {
  @JsonKey(name: 'place_id')
  String get placeId => throw _privateConstructorUsedError;
  @JsonKey(name: 'place_name')
  String get placeName => throw _privateConstructorUsedError;
  String get address => throw _privateConstructorUsedError;
  double get latitude => throw _privateConstructorUsedError;
  double get longitude => throw _privateConstructorUsedError;
  @JsonKey(name: 'category_name')
  String? get categoryName => throw _privateConstructorUsedError;
  @JsonKey(name: 'road_address')
  String? get roadAddress => throw _privateConstructorUsedError;
  String? get phone => throw _privateConstructorUsedError;
  @JsonKey(name: 'place_url')
  String? get placeUrl => throw _privateConstructorUsedError;
  double? get distance => throw _privateConstructorUsedError;

  Map<String, dynamic> toJson() => throw _privateConstructorUsedError;
  @JsonKey(ignore: true)
  $PlaceSearchResultModelCopyWith<PlaceSearchResultModel> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlaceSearchResultModelCopyWith<$Res> {
  factory $PlaceSearchResultModelCopyWith(PlaceSearchResultModel value,
          $Res Function(PlaceSearchResultModel) then) =
      _$PlaceSearchResultModelCopyWithImpl<$Res, PlaceSearchResultModel>;
  @useResult
  $Res call(
      {@JsonKey(name: 'place_id') String placeId,
      @JsonKey(name: 'place_name') String placeName,
      String address,
      double latitude,
      double longitude,
      @JsonKey(name: 'category_name') String? categoryName,
      @JsonKey(name: 'road_address') String? roadAddress,
      String? phone,
      @JsonKey(name: 'place_url') String? placeUrl,
      double? distance});
}

/// @nodoc
class _$PlaceSearchResultModelCopyWithImpl<$Res,
        $Val extends PlaceSearchResultModel>
    implements $PlaceSearchResultModelCopyWith<$Res> {
  _$PlaceSearchResultModelCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

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
abstract class _$$PlaceSearchResultModelImplCopyWith<$Res>
    implements $PlaceSearchResultModelCopyWith<$Res> {
  factory _$$PlaceSearchResultModelImplCopyWith(
          _$PlaceSearchResultModelImpl value,
          $Res Function(_$PlaceSearchResultModelImpl) then) =
      __$$PlaceSearchResultModelImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {@JsonKey(name: 'place_id') String placeId,
      @JsonKey(name: 'place_name') String placeName,
      String address,
      double latitude,
      double longitude,
      @JsonKey(name: 'category_name') String? categoryName,
      @JsonKey(name: 'road_address') String? roadAddress,
      String? phone,
      @JsonKey(name: 'place_url') String? placeUrl,
      double? distance});
}

/// @nodoc
class __$$PlaceSearchResultModelImplCopyWithImpl<$Res>
    extends _$PlaceSearchResultModelCopyWithImpl<$Res,
        _$PlaceSearchResultModelImpl>
    implements _$$PlaceSearchResultModelImplCopyWith<$Res> {
  __$$PlaceSearchResultModelImplCopyWithImpl(
      _$PlaceSearchResultModelImpl _value,
      $Res Function(_$PlaceSearchResultModelImpl) _then)
      : super(_value, _then);

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
    return _then(_$PlaceSearchResultModelImpl(
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
@JsonSerializable()
class _$PlaceSearchResultModelImpl implements _PlaceSearchResultModel {
  const _$PlaceSearchResultModelImpl(
      {@JsonKey(name: 'place_id') required this.placeId,
      @JsonKey(name: 'place_name') required this.placeName,
      required this.address,
      required this.latitude,
      required this.longitude,
      @JsonKey(name: 'category_name') this.categoryName,
      @JsonKey(name: 'road_address') this.roadAddress,
      this.phone,
      @JsonKey(name: 'place_url') this.placeUrl,
      this.distance});

  factory _$PlaceSearchResultModelImpl.fromJson(Map<String, dynamic> json) =>
      _$$PlaceSearchResultModelImplFromJson(json);

  @override
  @JsonKey(name: 'place_id')
  final String placeId;
  @override
  @JsonKey(name: 'place_name')
  final String placeName;
  @override
  final String address;
  @override
  final double latitude;
  @override
  final double longitude;
  @override
  @JsonKey(name: 'category_name')
  final String? categoryName;
  @override
  @JsonKey(name: 'road_address')
  final String? roadAddress;
  @override
  final String? phone;
  @override
  @JsonKey(name: 'place_url')
  final String? placeUrl;
  @override
  final double? distance;

  @override
  String toString() {
    return 'PlaceSearchResultModel(placeId: $placeId, placeName: $placeName, address: $address, latitude: $latitude, longitude: $longitude, categoryName: $categoryName, roadAddress: $roadAddress, phone: $phone, placeUrl: $placeUrl, distance: $distance)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlaceSearchResultModelImpl &&
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

  @JsonKey(ignore: true)
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

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PlaceSearchResultModelImplCopyWith<_$PlaceSearchResultModelImpl>
      get copyWith => __$$PlaceSearchResultModelImplCopyWithImpl<
          _$PlaceSearchResultModelImpl>(this, _$identity);

  @override
  Map<String, dynamic> toJson() {
    return _$$PlaceSearchResultModelImplToJson(
      this,
    );
  }
}

abstract class _PlaceSearchResultModel implements PlaceSearchResultModel {
  const factory _PlaceSearchResultModel(
      {@JsonKey(name: 'place_id') required final String placeId,
      @JsonKey(name: 'place_name') required final String placeName,
      required final String address,
      required final double latitude,
      required final double longitude,
      @JsonKey(name: 'category_name') final String? categoryName,
      @JsonKey(name: 'road_address') final String? roadAddress,
      final String? phone,
      @JsonKey(name: 'place_url') final String? placeUrl,
      final double? distance}) = _$PlaceSearchResultModelImpl;

  factory _PlaceSearchResultModel.fromJson(Map<String, dynamic> json) =
      _$PlaceSearchResultModelImpl.fromJson;

  @override
  @JsonKey(name: 'place_id')
  String get placeId;
  @override
  @JsonKey(name: 'place_name')
  String get placeName;
  @override
  String get address;
  @override
  double get latitude;
  @override
  double get longitude;
  @override
  @JsonKey(name: 'category_name')
  String? get categoryName;
  @override
  @JsonKey(name: 'road_address')
  String? get roadAddress;
  @override
  String? get phone;
  @override
  @JsonKey(name: 'place_url')
  String? get placeUrl;
  @override
  double? get distance;
  @override
  @JsonKey(ignore: true)
  _$$PlaceSearchResultModelImplCopyWith<_$PlaceSearchResultModelImpl>
      get copyWith => throw _privateConstructorUsedError;
}
