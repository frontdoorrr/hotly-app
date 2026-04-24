// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'onboarding_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$OnboardingState {
  int get currentStep => throw _privateConstructorUsedError;
  bool get locationPermissionGranted => throw _privateConstructorUsedError;
  bool get notificationPermissionGranted => throw _privateConstructorUsedError;
  bool get isCompleted => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $OnboardingStateCopyWith<OnboardingState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $OnboardingStateCopyWith<$Res> {
  factory $OnboardingStateCopyWith(
          OnboardingState value, $Res Function(OnboardingState) then) =
      _$OnboardingStateCopyWithImpl<$Res, OnboardingState>;
  @useResult
  $Res call(
      {int currentStep,
      bool locationPermissionGranted,
      bool notificationPermissionGranted,
      bool isCompleted});
}

/// @nodoc
class _$OnboardingStateCopyWithImpl<$Res, $Val extends OnboardingState>
    implements $OnboardingStateCopyWith<$Res> {
  _$OnboardingStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentStep = null,
    Object? locationPermissionGranted = null,
    Object? notificationPermissionGranted = null,
    Object? isCompleted = null,
  }) {
    return _then(_value.copyWith(
      currentStep: null == currentStep
          ? _value.currentStep
          : currentStep // ignore: cast_nullable_to_non_nullable
              as int,
      locationPermissionGranted: null == locationPermissionGranted
          ? _value.locationPermissionGranted
          : locationPermissionGranted // ignore: cast_nullable_to_non_nullable
              as bool,
      notificationPermissionGranted: null == notificationPermissionGranted
          ? _value.notificationPermissionGranted
          : notificationPermissionGranted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCompleted: null == isCompleted
          ? _value.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$OnboardingStateImplCopyWith<$Res>
    implements $OnboardingStateCopyWith<$Res> {
  factory _$$OnboardingStateImplCopyWith(_$OnboardingStateImpl value,
          $Res Function(_$OnboardingStateImpl) then) =
      __$$OnboardingStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {int currentStep,
      bool locationPermissionGranted,
      bool notificationPermissionGranted,
      bool isCompleted});
}

/// @nodoc
class __$$OnboardingStateImplCopyWithImpl<$Res>
    extends _$OnboardingStateCopyWithImpl<$Res, _$OnboardingStateImpl>
    implements _$$OnboardingStateImplCopyWith<$Res> {
  __$$OnboardingStateImplCopyWithImpl(
      _$OnboardingStateImpl _value, $Res Function(_$OnboardingStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentStep = null,
    Object? locationPermissionGranted = null,
    Object? notificationPermissionGranted = null,
    Object? isCompleted = null,
  }) {
    return _then(_$OnboardingStateImpl(
      currentStep: null == currentStep
          ? _value.currentStep
          : currentStep // ignore: cast_nullable_to_non_nullable
              as int,
      locationPermissionGranted: null == locationPermissionGranted
          ? _value.locationPermissionGranted
          : locationPermissionGranted // ignore: cast_nullable_to_non_nullable
              as bool,
      notificationPermissionGranted: null == notificationPermissionGranted
          ? _value.notificationPermissionGranted
          : notificationPermissionGranted // ignore: cast_nullable_to_non_nullable
              as bool,
      isCompleted: null == isCompleted
          ? _value.isCompleted
          : isCompleted // ignore: cast_nullable_to_non_nullable
              as bool,
    ));
  }
}

/// @nodoc

class _$OnboardingStateImpl implements _OnboardingState {
  const _$OnboardingStateImpl(
      {this.currentStep = 0,
      this.locationPermissionGranted = false,
      this.notificationPermissionGranted = false,
      this.isCompleted = false});

  @override
  @JsonKey()
  final int currentStep;
  @override
  @JsonKey()
  final bool locationPermissionGranted;
  @override
  @JsonKey()
  final bool notificationPermissionGranted;
  @override
  @JsonKey()
  final bool isCompleted;

  @override
  String toString() {
    return 'OnboardingState(currentStep: $currentStep, locationPermissionGranted: $locationPermissionGranted, notificationPermissionGranted: $notificationPermissionGranted, isCompleted: $isCompleted)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$OnboardingStateImpl &&
            (identical(other.currentStep, currentStep) ||
                other.currentStep == currentStep) &&
            (identical(other.locationPermissionGranted,
                    locationPermissionGranted) ||
                other.locationPermissionGranted == locationPermissionGranted) &&
            (identical(other.notificationPermissionGranted,
                    notificationPermissionGranted) ||
                other.notificationPermissionGranted ==
                    notificationPermissionGranted) &&
            (identical(other.isCompleted, isCompleted) ||
                other.isCompleted == isCompleted));
  }

  @override
  int get hashCode => Object.hash(runtimeType, currentStep,
      locationPermissionGranted, notificationPermissionGranted, isCompleted);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$OnboardingStateImplCopyWith<_$OnboardingStateImpl> get copyWith =>
      __$$OnboardingStateImplCopyWithImpl<_$OnboardingStateImpl>(
          this, _$identity);
}

abstract class _OnboardingState implements OnboardingState {
  const factory _OnboardingState(
      {final int currentStep,
      final bool locationPermissionGranted,
      final bool notificationPermissionGranted,
      final bool isCompleted}) = _$OnboardingStateImpl;

  @override
  int get currentStep;
  @override
  bool get locationPermissionGranted;
  @override
  bool get notificationPermissionGranted;
  @override
  bool get isCompleted;
  @override
  @JsonKey(ignore: true)
  _$$OnboardingStateImplCopyWith<_$OnboardingStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
