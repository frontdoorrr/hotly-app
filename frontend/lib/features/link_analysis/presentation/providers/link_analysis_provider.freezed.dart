// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'link_analysis_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$LinkAnalysisState {
  LinkAnalysisResult? get result => throw _privateConstructorUsedError;
  bool get isLoading => throw _privateConstructorUsedError;
  bool get isPolling => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;
  String? get inputUrl => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $LinkAnalysisStateCopyWith<LinkAnalysisState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $LinkAnalysisStateCopyWith<$Res> {
  factory $LinkAnalysisStateCopyWith(
          LinkAnalysisState value, $Res Function(LinkAnalysisState) then) =
      _$LinkAnalysisStateCopyWithImpl<$Res, LinkAnalysisState>;
  @useResult
  $Res call(
      {LinkAnalysisResult? result,
      bool isLoading,
      bool isPolling,
      String? error,
      String? inputUrl});

  $LinkAnalysisResultCopyWith<$Res>? get result;
}

/// @nodoc
class _$LinkAnalysisStateCopyWithImpl<$Res, $Val extends LinkAnalysisState>
    implements $LinkAnalysisStateCopyWith<$Res> {
  _$LinkAnalysisStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? result = freezed,
    Object? isLoading = null,
    Object? isPolling = null,
    Object? error = freezed,
    Object? inputUrl = freezed,
  }) {
    return _then(_value.copyWith(
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as LinkAnalysisResult?,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isPolling: null == isPolling
          ? _value.isPolling
          : isPolling // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      inputUrl: freezed == inputUrl
          ? _value.inputUrl
          : inputUrl // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }

  @override
  @pragma('vm:prefer-inline')
  $LinkAnalysisResultCopyWith<$Res>? get result {
    if (_value.result == null) {
      return null;
    }

    return $LinkAnalysisResultCopyWith<$Res>(_value.result!, (value) {
      return _then(_value.copyWith(result: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$LinkAnalysisStateImplCopyWith<$Res>
    implements $LinkAnalysisStateCopyWith<$Res> {
  factory _$$LinkAnalysisStateImplCopyWith(_$LinkAnalysisStateImpl value,
          $Res Function(_$LinkAnalysisStateImpl) then) =
      __$$LinkAnalysisStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {LinkAnalysisResult? result,
      bool isLoading,
      bool isPolling,
      String? error,
      String? inputUrl});

  @override
  $LinkAnalysisResultCopyWith<$Res>? get result;
}

/// @nodoc
class __$$LinkAnalysisStateImplCopyWithImpl<$Res>
    extends _$LinkAnalysisStateCopyWithImpl<$Res, _$LinkAnalysisStateImpl>
    implements _$$LinkAnalysisStateImplCopyWith<$Res> {
  __$$LinkAnalysisStateImplCopyWithImpl(_$LinkAnalysisStateImpl _value,
      $Res Function(_$LinkAnalysisStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? result = freezed,
    Object? isLoading = null,
    Object? isPolling = null,
    Object? error = freezed,
    Object? inputUrl = freezed,
  }) {
    return _then(_$LinkAnalysisStateImpl(
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as LinkAnalysisResult?,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isPolling: null == isPolling
          ? _value.isPolling
          : isPolling // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      inputUrl: freezed == inputUrl
          ? _value.inputUrl
          : inputUrl // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$LinkAnalysisStateImpl implements _LinkAnalysisState {
  const _$LinkAnalysisStateImpl(
      {this.result,
      this.isLoading = false,
      this.isPolling = false,
      this.error,
      this.inputUrl});

  @override
  final LinkAnalysisResult? result;
  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool isPolling;
  @override
  final String? error;
  @override
  final String? inputUrl;

  @override
  String toString() {
    return 'LinkAnalysisState(result: $result, isLoading: $isLoading, isPolling: $isPolling, error: $error, inputUrl: $inputUrl)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$LinkAnalysisStateImpl &&
            (identical(other.result, result) || other.result == result) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.isPolling, isPolling) ||
                other.isPolling == isPolling) &&
            (identical(other.error, error) || other.error == error) &&
            (identical(other.inputUrl, inputUrl) ||
                other.inputUrl == inputUrl));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, result, isLoading, isPolling, error, inputUrl);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$LinkAnalysisStateImplCopyWith<_$LinkAnalysisStateImpl> get copyWith =>
      __$$LinkAnalysisStateImplCopyWithImpl<_$LinkAnalysisStateImpl>(
          this, _$identity);
}

abstract class _LinkAnalysisState implements LinkAnalysisState {
  const factory _LinkAnalysisState(
      {final LinkAnalysisResult? result,
      final bool isLoading,
      final bool isPolling,
      final String? error,
      final String? inputUrl}) = _$LinkAnalysisStateImpl;

  @override
  LinkAnalysisResult? get result;
  @override
  bool get isLoading;
  @override
  bool get isPolling;
  @override
  String? get error;
  @override
  String? get inputUrl;
  @override
  @JsonKey(ignore: true)
  _$$LinkAnalysisStateImplCopyWith<_$LinkAnalysisStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
