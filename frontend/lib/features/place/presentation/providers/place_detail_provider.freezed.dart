// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'place_detail_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$PlaceDetailState {
  Place? get place => throw _privateConstructorUsedError;
  List<Place> get similarPlaces => throw _privateConstructorUsedError;
  bool get isLoading => throw _privateConstructorUsedError;
  bool get isLoadingSimilar => throw _privateConstructorUsedError;
  bool get isLiked => throw _privateConstructorUsedError;
  bool get isSaved => throw _privateConstructorUsedError;
  ApiException? get error => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $PlaceDetailStateCopyWith<PlaceDetailState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $PlaceDetailStateCopyWith<$Res> {
  factory $PlaceDetailStateCopyWith(
          PlaceDetailState value, $Res Function(PlaceDetailState) then) =
      _$PlaceDetailStateCopyWithImpl<$Res, PlaceDetailState>;
  @useResult
  $Res call(
      {Place? place,
      List<Place> similarPlaces,
      bool isLoading,
      bool isLoadingSimilar,
      bool isLiked,
      bool isSaved,
      ApiException? error});

  $PlaceCopyWith<$Res>? get place;
}

/// @nodoc
class _$PlaceDetailStateCopyWithImpl<$Res, $Val extends PlaceDetailState>
    implements $PlaceDetailStateCopyWith<$Res> {
  _$PlaceDetailStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? place = freezed,
    Object? similarPlaces = null,
    Object? isLoading = null,
    Object? isLoadingSimilar = null,
    Object? isLiked = null,
    Object? isSaved = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      place: freezed == place
          ? _value.place
          : place // ignore: cast_nullable_to_non_nullable
              as Place?,
      similarPlaces: null == similarPlaces
          ? _value.similarPlaces
          : similarPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingSimilar: null == isLoadingSimilar
          ? _value.isLoadingSimilar
          : isLoadingSimilar // ignore: cast_nullable_to_non_nullable
              as bool,
      isLiked: null == isLiked
          ? _value.isLiked
          : isLiked // ignore: cast_nullable_to_non_nullable
              as bool,
      isSaved: null == isSaved
          ? _value.isSaved
          : isSaved // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as ApiException?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $PlaceCopyWith<$Res>? get place {
    if (_value.place == null) {
      return null;
    }

    return $PlaceCopyWith<$Res>(_value.place!, (value) {
      return _then(_value.copyWith(place: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$PlaceDetailStateImplCopyWith<$Res>
    implements $PlaceDetailStateCopyWith<$Res> {
  factory _$$PlaceDetailStateImplCopyWith(_$PlaceDetailStateImpl value,
          $Res Function(_$PlaceDetailStateImpl) then) =
      __$$PlaceDetailStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {Place? place,
      List<Place> similarPlaces,
      bool isLoading,
      bool isLoadingSimilar,
      bool isLiked,
      bool isSaved,
      ApiException? error});

  @override
  $PlaceCopyWith<$Res>? get place;
}

/// @nodoc
class __$$PlaceDetailStateImplCopyWithImpl<$Res>
    extends _$PlaceDetailStateCopyWithImpl<$Res, _$PlaceDetailStateImpl>
    implements _$$PlaceDetailStateImplCopyWith<$Res> {
  __$$PlaceDetailStateImplCopyWithImpl(_$PlaceDetailStateImpl _value,
      $Res Function(_$PlaceDetailStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? place = freezed,
    Object? similarPlaces = null,
    Object? isLoading = null,
    Object? isLoadingSimilar = null,
    Object? isLiked = null,
    Object? isSaved = null,
    Object? error = freezed,
  }) {
    return _then(_$PlaceDetailStateImpl(
      place: freezed == place
          ? _value.place
          : place // ignore: cast_nullable_to_non_nullable
              as Place?,
      similarPlaces: null == similarPlaces
          ? _value._similarPlaces
          : similarPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingSimilar: null == isLoadingSimilar
          ? _value.isLoadingSimilar
          : isLoadingSimilar // ignore: cast_nullable_to_non_nullable
              as bool,
      isLiked: null == isLiked
          ? _value.isLiked
          : isLiked // ignore: cast_nullable_to_non_nullable
              as bool,
      isSaved: null == isSaved
          ? _value.isSaved
          : isSaved // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as ApiException?,
    ));
  }
}

/// @nodoc

class _$PlaceDetailStateImpl implements _PlaceDetailState {
  const _$PlaceDetailStateImpl(
      {this.place,
      final List<Place> similarPlaces = const [],
      this.isLoading = false,
      this.isLoadingSimilar = false,
      this.isLiked = false,
      this.isSaved = false,
      this.error})
      : _similarPlaces = similarPlaces;

  @override
  final Place? place;
  final List<Place> _similarPlaces;
  @override
  @JsonKey()
  List<Place> get similarPlaces {
    if (_similarPlaces is EqualUnmodifiableListView) return _similarPlaces;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_similarPlaces);
  }

  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool isLoadingSimilar;
  @override
  @JsonKey()
  final bool isLiked;
  @override
  @JsonKey()
  final bool isSaved;
  @override
  final ApiException? error;

  @override
  String toString() {
    return 'PlaceDetailState(place: $place, similarPlaces: $similarPlaces, isLoading: $isLoading, isLoadingSimilar: $isLoadingSimilar, isLiked: $isLiked, isSaved: $isSaved, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$PlaceDetailStateImpl &&
            (identical(other.place, place) || other.place == place) &&
            const DeepCollectionEquality()
                .equals(other._similarPlaces, _similarPlaces) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.isLoadingSimilar, isLoadingSimilar) ||
                other.isLoadingSimilar == isLoadingSimilar) &&
            (identical(other.isLiked, isLiked) || other.isLiked == isLiked) &&
            (identical(other.isSaved, isSaved) || other.isSaved == isSaved) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      place,
      const DeepCollectionEquality().hash(_similarPlaces),
      isLoading,
      isLoadingSimilar,
      isLiked,
      isSaved,
      error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$PlaceDetailStateImplCopyWith<_$PlaceDetailStateImpl> get copyWith =>
      __$$PlaceDetailStateImplCopyWithImpl<_$PlaceDetailStateImpl>(
          this, _$identity);
}

abstract class _PlaceDetailState implements PlaceDetailState {
  const factory _PlaceDetailState(
      {final Place? place,
      final List<Place> similarPlaces,
      final bool isLoading,
      final bool isLoadingSimilar,
      final bool isLiked,
      final bool isSaved,
      final ApiException? error}) = _$PlaceDetailStateImpl;

  @override
  Place? get place;
  @override
  List<Place> get similarPlaces;
  @override
  bool get isLoading;
  @override
  bool get isLoadingSimilar;
  @override
  bool get isLiked;
  @override
  bool get isSaved;
  @override
  ApiException? get error;
  @override
  @JsonKey(ignore: true)
  _$$PlaceDetailStateImplCopyWith<_$PlaceDetailStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
