// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'saved_places_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$SavedPlacesState {
  List<Place> get places => throw _privateConstructorUsedError;
  bool get isLoading => throw _privateConstructorUsedError;
  bool get hasError => throw _privateConstructorUsedError;
  String? get errorMessage => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $SavedPlacesStateCopyWith<SavedPlacesState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SavedPlacesStateCopyWith<$Res> {
  factory $SavedPlacesStateCopyWith(
          SavedPlacesState value, $Res Function(SavedPlacesState) then) =
      _$SavedPlacesStateCopyWithImpl<$Res, SavedPlacesState>;
  @useResult
  $Res call(
      {List<Place> places,
      bool isLoading,
      bool hasError,
      String? errorMessage});
}

/// @nodoc
class _$SavedPlacesStateCopyWithImpl<$Res, $Val extends SavedPlacesState>
    implements $SavedPlacesStateCopyWith<$Res> {
  _$SavedPlacesStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? places = null,
    Object? isLoading = null,
    Object? hasError = null,
    Object? errorMessage = freezed,
  }) {
    return _then(_value.copyWith(
      places: null == places
          ? _value.places
          : places // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      hasError: null == hasError
          ? _value.hasError
          : hasError // ignore: cast_nullable_to_non_nullable
              as bool,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SavedPlacesStateImplCopyWith<$Res>
    implements $SavedPlacesStateCopyWith<$Res> {
  factory _$$SavedPlacesStateImplCopyWith(_$SavedPlacesStateImpl value,
          $Res Function(_$SavedPlacesStateImpl) then) =
      __$$SavedPlacesStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<Place> places,
      bool isLoading,
      bool hasError,
      String? errorMessage});
}

/// @nodoc
class __$$SavedPlacesStateImplCopyWithImpl<$Res>
    extends _$SavedPlacesStateCopyWithImpl<$Res, _$SavedPlacesStateImpl>
    implements _$$SavedPlacesStateImplCopyWith<$Res> {
  __$$SavedPlacesStateImplCopyWithImpl(_$SavedPlacesStateImpl _value,
      $Res Function(_$SavedPlacesStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? places = null,
    Object? isLoading = null,
    Object? hasError = null,
    Object? errorMessage = freezed,
  }) {
    return _then(_$SavedPlacesStateImpl(
      places: null == places
          ? _value._places
          : places // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      hasError: null == hasError
          ? _value.hasError
          : hasError // ignore: cast_nullable_to_non_nullable
              as bool,
      errorMessage: freezed == errorMessage
          ? _value.errorMessage
          : errorMessage // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$SavedPlacesStateImpl
    with DiagnosticableTreeMixin
    implements _SavedPlacesState {
  const _$SavedPlacesStateImpl(
      {final List<Place> places = const [],
      this.isLoading = false,
      this.hasError = false,
      this.errorMessage})
      : _places = places;

  final List<Place> _places;
  @override
  @JsonKey()
  List<Place> get places {
    if (_places is EqualUnmodifiableListView) return _places;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_places);
  }

  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool hasError;
  @override
  final String? errorMessage;

  @override
  String toString({DiagnosticLevel minLevel = DiagnosticLevel.info}) {
    return 'SavedPlacesState(places: $places, isLoading: $isLoading, hasError: $hasError, errorMessage: $errorMessage)';
  }

  @override
  void debugFillProperties(DiagnosticPropertiesBuilder properties) {
    super.debugFillProperties(properties);
    properties
      ..add(DiagnosticsProperty('type', 'SavedPlacesState'))
      ..add(DiagnosticsProperty('places', places))
      ..add(DiagnosticsProperty('isLoading', isLoading))
      ..add(DiagnosticsProperty('hasError', hasError))
      ..add(DiagnosticsProperty('errorMessage', errorMessage));
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SavedPlacesStateImpl &&
            const DeepCollectionEquality().equals(other._places, _places) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.hasError, hasError) ||
                other.hasError == hasError) &&
            (identical(other.errorMessage, errorMessage) ||
                other.errorMessage == errorMessage));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_places),
      isLoading,
      hasError,
      errorMessage);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$SavedPlacesStateImplCopyWith<_$SavedPlacesStateImpl> get copyWith =>
      __$$SavedPlacesStateImplCopyWithImpl<_$SavedPlacesStateImpl>(
          this, _$identity);
}

abstract class _SavedPlacesState implements SavedPlacesState {
  const factory _SavedPlacesState(
      {final List<Place> places,
      final bool isLoading,
      final bool hasError,
      final String? errorMessage}) = _$SavedPlacesStateImpl;

  @override
  List<Place> get places;
  @override
  bool get isLoading;
  @override
  bool get hasError;
  @override
  String? get errorMessage;
  @override
  @JsonKey(ignore: true)
  _$$SavedPlacesStateImplCopyWith<_$SavedPlacesStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
