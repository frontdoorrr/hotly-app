// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'course_builder_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$CourseBuilderState {
  String get title => throw _privateConstructorUsedError;
  CourseType get type => throw _privateConstructorUsedError;
  List<CoursePlace> get places => throw _privateConstructorUsedError;
  Duration get totalDuration => throw _privateConstructorUsedError;
  bool get isSaving => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  /// Create a copy of CourseBuilderState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $CourseBuilderStateCopyWith<CourseBuilderState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $CourseBuilderStateCopyWith<$Res> {
  factory $CourseBuilderStateCopyWith(
          CourseBuilderState value, $Res Function(CourseBuilderState) then) =
      _$CourseBuilderStateCopyWithImpl<$Res, CourseBuilderState>;
  @useResult
  $Res call(
      {String title,
      CourseType type,
      List<CoursePlace> places,
      Duration totalDuration,
      bool isSaving,
      String? error});
}

/// @nodoc
class _$CourseBuilderStateCopyWithImpl<$Res, $Val extends CourseBuilderState>
    implements $CourseBuilderStateCopyWith<$Res> {
  _$CourseBuilderStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of CourseBuilderState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? title = null,
    Object? type = null,
    Object? places = null,
    Object? totalDuration = null,
    Object? isSaving = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as CourseType,
      places: null == places
          ? _value.places
          : places // ignore: cast_nullable_to_non_nullable
              as List<CoursePlace>,
      totalDuration: null == totalDuration
          ? _value.totalDuration
          : totalDuration // ignore: cast_nullable_to_non_nullable
              as Duration,
      isSaving: null == isSaving
          ? _value.isSaving
          : isSaving // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$CourseBuilderStateImplCopyWith<$Res>
    implements $CourseBuilderStateCopyWith<$Res> {
  factory _$$CourseBuilderStateImplCopyWith(_$CourseBuilderStateImpl value,
          $Res Function(_$CourseBuilderStateImpl) then) =
      __$$CourseBuilderStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String title,
      CourseType type,
      List<CoursePlace> places,
      Duration totalDuration,
      bool isSaving,
      String? error});
}

/// @nodoc
class __$$CourseBuilderStateImplCopyWithImpl<$Res>
    extends _$CourseBuilderStateCopyWithImpl<$Res, _$CourseBuilderStateImpl>
    implements _$$CourseBuilderStateImplCopyWith<$Res> {
  __$$CourseBuilderStateImplCopyWithImpl(_$CourseBuilderStateImpl _value,
      $Res Function(_$CourseBuilderStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of CourseBuilderState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? title = null,
    Object? type = null,
    Object? places = null,
    Object? totalDuration = null,
    Object? isSaving = null,
    Object? error = freezed,
  }) {
    return _then(_$CourseBuilderStateImpl(
      title: null == title
          ? _value.title
          : title // ignore: cast_nullable_to_non_nullable
              as String,
      type: null == type
          ? _value.type
          : type // ignore: cast_nullable_to_non_nullable
              as CourseType,
      places: null == places
          ? _value._places
          : places // ignore: cast_nullable_to_non_nullable
              as List<CoursePlace>,
      totalDuration: null == totalDuration
          ? _value.totalDuration
          : totalDuration // ignore: cast_nullable_to_non_nullable
              as Duration,
      isSaving: null == isSaving
          ? _value.isSaving
          : isSaving // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$CourseBuilderStateImpl implements _CourseBuilderState {
  const _$CourseBuilderStateImpl(
      {required this.title,
      required this.type,
      required final List<CoursePlace> places,
      required this.totalDuration,
      this.isSaving = false,
      this.error})
      : _places = places;

  @override
  final String title;
  @override
  final CourseType type;
  final List<CoursePlace> _places;
  @override
  List<CoursePlace> get places {
    if (_places is EqualUnmodifiableListView) return _places;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_places);
  }

  @override
  final Duration totalDuration;
  @override
  @JsonKey()
  final bool isSaving;
  @override
  final String? error;

  @override
  String toString() {
    return 'CourseBuilderState(title: $title, type: $type, places: $places, totalDuration: $totalDuration, isSaving: $isSaving, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$CourseBuilderStateImpl &&
            (identical(other.title, title) || other.title == title) &&
            (identical(other.type, type) || other.type == type) &&
            const DeepCollectionEquality().equals(other._places, _places) &&
            (identical(other.totalDuration, totalDuration) ||
                other.totalDuration == totalDuration) &&
            (identical(other.isSaving, isSaving) ||
                other.isSaving == isSaving) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      title,
      type,
      const DeepCollectionEquality().hash(_places),
      totalDuration,
      isSaving,
      error);

  /// Create a copy of CourseBuilderState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$CourseBuilderStateImplCopyWith<_$CourseBuilderStateImpl> get copyWith =>
      __$$CourseBuilderStateImplCopyWithImpl<_$CourseBuilderStateImpl>(
          this, _$identity);
}

abstract class _CourseBuilderState implements CourseBuilderState {
  const factory _CourseBuilderState(
      {required final String title,
      required final CourseType type,
      required final List<CoursePlace> places,
      required final Duration totalDuration,
      final bool isSaving,
      final String? error}) = _$CourseBuilderStateImpl;

  @override
  String get title;
  @override
  CourseType get type;
  @override
  List<CoursePlace> get places;
  @override
  Duration get totalDuration;
  @override
  bool get isSaving;
  @override
  String? get error;

  /// Create a copy of CourseBuilderState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$CourseBuilderStateImplCopyWith<_$CourseBuilderStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
