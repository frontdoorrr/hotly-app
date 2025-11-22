// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'home_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$HomeState {
  List<Place> get recommendedPlaces => throw _privateConstructorUsedError;
  List<Place> get nearbyPlaces => throw _privateConstructorUsedError;
  List<Place> get popularPlaces => throw _privateConstructorUsedError;
  bool get isLoadingRecommended => throw _privateConstructorUsedError;
  bool get isLoadingNearby => throw _privateConstructorUsedError;
  bool get isLoadingPopular => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $HomeStateCopyWith<HomeState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $HomeStateCopyWith<$Res> {
  factory $HomeStateCopyWith(HomeState value, $Res Function(HomeState) then) =
      _$HomeStateCopyWithImpl<$Res, HomeState>;
  @useResult
  $Res call(
      {List<Place> recommendedPlaces,
      List<Place> nearbyPlaces,
      List<Place> popularPlaces,
      bool isLoadingRecommended,
      bool isLoadingNearby,
      bool isLoadingPopular,
      String? error});
}

/// @nodoc
class _$HomeStateCopyWithImpl<$Res, $Val extends HomeState>
    implements $HomeStateCopyWith<$Res> {
  _$HomeStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? recommendedPlaces = null,
    Object? nearbyPlaces = null,
    Object? popularPlaces = null,
    Object? isLoadingRecommended = null,
    Object? isLoadingNearby = null,
    Object? isLoadingPopular = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      recommendedPlaces: null == recommendedPlaces
          ? _value.recommendedPlaces
          : recommendedPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      nearbyPlaces: null == nearbyPlaces
          ? _value.nearbyPlaces
          : nearbyPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      popularPlaces: null == popularPlaces
          ? _value.popularPlaces
          : popularPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoadingRecommended: null == isLoadingRecommended
          ? _value.isLoadingRecommended
          : isLoadingRecommended // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingNearby: null == isLoadingNearby
          ? _value.isLoadingNearby
          : isLoadingNearby // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingPopular: null == isLoadingPopular
          ? _value.isLoadingPopular
          : isLoadingPopular // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$HomeStateImplCopyWith<$Res>
    implements $HomeStateCopyWith<$Res> {
  factory _$$HomeStateImplCopyWith(
          _$HomeStateImpl value, $Res Function(_$HomeStateImpl) then) =
      __$$HomeStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<Place> recommendedPlaces,
      List<Place> nearbyPlaces,
      List<Place> popularPlaces,
      bool isLoadingRecommended,
      bool isLoadingNearby,
      bool isLoadingPopular,
      String? error});
}

/// @nodoc
class __$$HomeStateImplCopyWithImpl<$Res>
    extends _$HomeStateCopyWithImpl<$Res, _$HomeStateImpl>
    implements _$$HomeStateImplCopyWith<$Res> {
  __$$HomeStateImplCopyWithImpl(
      _$HomeStateImpl _value, $Res Function(_$HomeStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? recommendedPlaces = null,
    Object? nearbyPlaces = null,
    Object? popularPlaces = null,
    Object? isLoadingRecommended = null,
    Object? isLoadingNearby = null,
    Object? isLoadingPopular = null,
    Object? error = freezed,
  }) {
    return _then(_$HomeStateImpl(
      recommendedPlaces: null == recommendedPlaces
          ? _value._recommendedPlaces
          : recommendedPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      nearbyPlaces: null == nearbyPlaces
          ? _value._nearbyPlaces
          : nearbyPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      popularPlaces: null == popularPlaces
          ? _value._popularPlaces
          : popularPlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoadingRecommended: null == isLoadingRecommended
          ? _value.isLoadingRecommended
          : isLoadingRecommended // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingNearby: null == isLoadingNearby
          ? _value.isLoadingNearby
          : isLoadingNearby // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingPopular: null == isLoadingPopular
          ? _value.isLoadingPopular
          : isLoadingPopular // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$HomeStateImpl implements _HomeState {
  const _$HomeStateImpl(
      {final List<Place> recommendedPlaces = const [],
      final List<Place> nearbyPlaces = const [],
      final List<Place> popularPlaces = const [],
      this.isLoadingRecommended = false,
      this.isLoadingNearby = false,
      this.isLoadingPopular = false,
      this.error})
      : _recommendedPlaces = recommendedPlaces,
        _nearbyPlaces = nearbyPlaces,
        _popularPlaces = popularPlaces;

  final List<Place> _recommendedPlaces;
  @override
  @JsonKey()
  List<Place> get recommendedPlaces {
    if (_recommendedPlaces is EqualUnmodifiableListView)
      return _recommendedPlaces;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_recommendedPlaces);
  }

  final List<Place> _nearbyPlaces;
  @override
  @JsonKey()
  List<Place> get nearbyPlaces {
    if (_nearbyPlaces is EqualUnmodifiableListView) return _nearbyPlaces;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_nearbyPlaces);
  }

  final List<Place> _popularPlaces;
  @override
  @JsonKey()
  List<Place> get popularPlaces {
    if (_popularPlaces is EqualUnmodifiableListView) return _popularPlaces;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_popularPlaces);
  }

  @override
  @JsonKey()
  final bool isLoadingRecommended;
  @override
  @JsonKey()
  final bool isLoadingNearby;
  @override
  @JsonKey()
  final bool isLoadingPopular;
  @override
  final String? error;

  @override
  String toString() {
    return 'HomeState(recommendedPlaces: $recommendedPlaces, nearbyPlaces: $nearbyPlaces, popularPlaces: $popularPlaces, isLoadingRecommended: $isLoadingRecommended, isLoadingNearby: $isLoadingNearby, isLoadingPopular: $isLoadingPopular, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$HomeStateImpl &&
            const DeepCollectionEquality()
                .equals(other._recommendedPlaces, _recommendedPlaces) &&
            const DeepCollectionEquality()
                .equals(other._nearbyPlaces, _nearbyPlaces) &&
            const DeepCollectionEquality()
                .equals(other._popularPlaces, _popularPlaces) &&
            (identical(other.isLoadingRecommended, isLoadingRecommended) ||
                other.isLoadingRecommended == isLoadingRecommended) &&
            (identical(other.isLoadingNearby, isLoadingNearby) ||
                other.isLoadingNearby == isLoadingNearby) &&
            (identical(other.isLoadingPopular, isLoadingPopular) ||
                other.isLoadingPopular == isLoadingPopular) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_recommendedPlaces),
      const DeepCollectionEquality().hash(_nearbyPlaces),
      const DeepCollectionEquality().hash(_popularPlaces),
      isLoadingRecommended,
      isLoadingNearby,
      isLoadingPopular,
      error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$HomeStateImplCopyWith<_$HomeStateImpl> get copyWith =>
      __$$HomeStateImplCopyWithImpl<_$HomeStateImpl>(this, _$identity);
}

abstract class _HomeState implements HomeState {
  const factory _HomeState(
      {final List<Place> recommendedPlaces,
      final List<Place> nearbyPlaces,
      final List<Place> popularPlaces,
      final bool isLoadingRecommended,
      final bool isLoadingNearby,
      final bool isLoadingPopular,
      final String? error}) = _$HomeStateImpl;

  @override
  List<Place> get recommendedPlaces;
  @override
  List<Place> get nearbyPlaces;
  @override
  List<Place> get popularPlaces;
  @override
  bool get isLoadingRecommended;
  @override
  bool get isLoadingNearby;
  @override
  bool get isLoadingPopular;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$HomeStateImplCopyWith<_$HomeStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
