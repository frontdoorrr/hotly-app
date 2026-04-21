// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'archive_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$ArchiveInputState {
  bool get isLoading => throw _privateConstructorUsedError;
  ArchivedContent? get result => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;
  String? get inputUrl => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $ArchiveInputStateCopyWith<ArchiveInputState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchiveInputStateCopyWith<$Res> {
  factory $ArchiveInputStateCopyWith(
          ArchiveInputState value, $Res Function(ArchiveInputState) then) =
      _$ArchiveInputStateCopyWithImpl<$Res, ArchiveInputState>;
  @useResult
  $Res call(
      {bool isLoading,
      ArchivedContent? result,
      String? error,
      String? inputUrl});

  $ArchivedContentCopyWith<$Res>? get result;
}

/// @nodoc
class _$ArchiveInputStateCopyWithImpl<$Res, $Val extends ArchiveInputState>
    implements $ArchiveInputStateCopyWith<$Res> {
  _$ArchiveInputStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? isLoading = null,
    Object? result = freezed,
    Object? error = freezed,
    Object? inputUrl = freezed,
  }) {
    return _then(_value.copyWith(
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as ArchivedContent?,
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
  $ArchivedContentCopyWith<$Res>? get result {
    if (_value.result == null) {
      return null;
    }

    return $ArchivedContentCopyWith<$Res>(_value.result!, (value) {
      return _then(_value.copyWith(result: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$ArchiveInputStateImplCopyWith<$Res>
    implements $ArchiveInputStateCopyWith<$Res> {
  factory _$$ArchiveInputStateImplCopyWith(_$ArchiveInputStateImpl value,
          $Res Function(_$ArchiveInputStateImpl) then) =
      __$$ArchiveInputStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {bool isLoading,
      ArchivedContent? result,
      String? error,
      String? inputUrl});

  @override
  $ArchivedContentCopyWith<$Res>? get result;
}

/// @nodoc
class __$$ArchiveInputStateImplCopyWithImpl<$Res>
    extends _$ArchiveInputStateCopyWithImpl<$Res, _$ArchiveInputStateImpl>
    implements _$$ArchiveInputStateImplCopyWith<$Res> {
  __$$ArchiveInputStateImplCopyWithImpl(_$ArchiveInputStateImpl _value,
      $Res Function(_$ArchiveInputStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? isLoading = null,
    Object? result = freezed,
    Object? error = freezed,
    Object? inputUrl = freezed,
  }) {
    return _then(_$ArchiveInputStateImpl(
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      result: freezed == result
          ? _value.result
          : result // ignore: cast_nullable_to_non_nullable
              as ArchivedContent?,
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

class _$ArchiveInputStateImpl implements _ArchiveInputState {
  const _$ArchiveInputStateImpl(
      {this.isLoading = false, this.result, this.error, this.inputUrl});

  @override
  @JsonKey()
  final bool isLoading;
  @override
  final ArchivedContent? result;
  @override
  final String? error;
  @override
  final String? inputUrl;

  @override
  String toString() {
    return 'ArchiveInputState(isLoading: $isLoading, result: $result, error: $error, inputUrl: $inputUrl)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchiveInputStateImpl &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.result, result) || other.result == result) &&
            (identical(other.error, error) || other.error == error) &&
            (identical(other.inputUrl, inputUrl) ||
                other.inputUrl == inputUrl));
  }

  @override
  int get hashCode =>
      Object.hash(runtimeType, isLoading, result, error, inputUrl);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ArchiveInputStateImplCopyWith<_$ArchiveInputStateImpl> get copyWith =>
      __$$ArchiveInputStateImplCopyWithImpl<_$ArchiveInputStateImpl>(
          this, _$identity);
}

abstract class _ArchiveInputState implements ArchiveInputState {
  const factory _ArchiveInputState(
      {final bool isLoading,
      final ArchivedContent? result,
      final String? error,
      final String? inputUrl}) = _$ArchiveInputStateImpl;

  @override
  bool get isLoading;
  @override
  ArchivedContent? get result;
  @override
  String? get error;
  @override
  String? get inputUrl;
  @override
  @JsonKey(ignore: true)
  _$$ArchiveInputStateImplCopyWith<_$ArchiveInputStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
mixin _$ArchiveListState {
  List<ArchivedContent> get items => throw _privateConstructorUsedError;
  int get total => throw _privateConstructorUsedError;
  int get page => throw _privateConstructorUsedError;
  bool get isLoading => throw _privateConstructorUsedError;
  bool get hasMore => throw _privateConstructorUsedError;
  String? get selectedType => throw _privateConstructorUsedError;
  String? get error => throw _privateConstructorUsedError;

  @JsonKey(ignore: true)
  $ArchiveListStateCopyWith<ArchiveListState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $ArchiveListStateCopyWith<$Res> {
  factory $ArchiveListStateCopyWith(
          ArchiveListState value, $Res Function(ArchiveListState) then) =
      _$ArchiveListStateCopyWithImpl<$Res, ArchiveListState>;
  @useResult
  $Res call(
      {List<ArchivedContent> items,
      int total,
      int page,
      bool isLoading,
      bool hasMore,
      String? selectedType,
      String? error});
}

/// @nodoc
class _$ArchiveListStateCopyWithImpl<$Res, $Val extends ArchiveListState>
    implements $ArchiveListStateCopyWith<$Res> {
  _$ArchiveListStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? total = null,
    Object? page = null,
    Object? isLoading = null,
    Object? hasMore = null,
    Object? selectedType = freezed,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      items: null == items
          ? _value.items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ArchivedContent>,
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      page: null == page
          ? _value.page
          : page // ignore: cast_nullable_to_non_nullable
              as int,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      hasMore: null == hasMore
          ? _value.hasMore
          : hasMore // ignore: cast_nullable_to_non_nullable
              as bool,
      selectedType: freezed == selectedType
          ? _value.selectedType
          : selectedType // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$ArchiveListStateImplCopyWith<$Res>
    implements $ArchiveListStateCopyWith<$Res> {
  factory _$$ArchiveListStateImplCopyWith(_$ArchiveListStateImpl value,
          $Res Function(_$ArchiveListStateImpl) then) =
      __$$ArchiveListStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {List<ArchivedContent> items,
      int total,
      int page,
      bool isLoading,
      bool hasMore,
      String? selectedType,
      String? error});
}

/// @nodoc
class __$$ArchiveListStateImplCopyWithImpl<$Res>
    extends _$ArchiveListStateCopyWithImpl<$Res, _$ArchiveListStateImpl>
    implements _$$ArchiveListStateImplCopyWith<$Res> {
  __$$ArchiveListStateImplCopyWithImpl(_$ArchiveListStateImpl _value,
      $Res Function(_$ArchiveListStateImpl) _then)
      : super(_value, _then);

  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? items = null,
    Object? total = null,
    Object? page = null,
    Object? isLoading = null,
    Object? hasMore = null,
    Object? selectedType = freezed,
    Object? error = freezed,
  }) {
    return _then(_$ArchiveListStateImpl(
      items: null == items
          ? _value._items
          : items // ignore: cast_nullable_to_non_nullable
              as List<ArchivedContent>,
      total: null == total
          ? _value.total
          : total // ignore: cast_nullable_to_non_nullable
              as int,
      page: null == page
          ? _value.page
          : page // ignore: cast_nullable_to_non_nullable
              as int,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      hasMore: null == hasMore
          ? _value.hasMore
          : hasMore // ignore: cast_nullable_to_non_nullable
              as bool,
      selectedType: freezed == selectedType
          ? _value.selectedType
          : selectedType // ignore: cast_nullable_to_non_nullable
              as String?,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
    ));
  }
}

/// @nodoc

class _$ArchiveListStateImpl implements _ArchiveListState {
  const _$ArchiveListStateImpl(
      {final List<ArchivedContent> items = const [],
      this.total = 0,
      this.page = 1,
      this.isLoading = false,
      this.hasMore = false,
      this.selectedType,
      this.error})
      : _items = items;

  final List<ArchivedContent> _items;
  @override
  @JsonKey()
  List<ArchivedContent> get items {
    if (_items is EqualUnmodifiableListView) return _items;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_items);
  }

  @override
  @JsonKey()
  final int total;
  @override
  @JsonKey()
  final int page;
  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool hasMore;
  @override
  final String? selectedType;
  @override
  final String? error;

  @override
  String toString() {
    return 'ArchiveListState(items: $items, total: $total, page: $page, isLoading: $isLoading, hasMore: $hasMore, selectedType: $selectedType, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$ArchiveListStateImpl &&
            const DeepCollectionEquality().equals(other._items, _items) &&
            (identical(other.total, total) || other.total == total) &&
            (identical(other.page, page) || other.page == page) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.hasMore, hasMore) || other.hasMore == hasMore) &&
            (identical(other.selectedType, selectedType) ||
                other.selectedType == selectedType) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      const DeepCollectionEquality().hash(_items),
      total,
      page,
      isLoading,
      hasMore,
      selectedType,
      error);

  @JsonKey(ignore: true)
  @override
  @pragma('vm:prefer-inline')
  _$$ArchiveListStateImplCopyWith<_$ArchiveListStateImpl> get copyWith =>
      __$$ArchiveListStateImplCopyWithImpl<_$ArchiveListStateImpl>(
          this, _$identity);
}

abstract class _ArchiveListState implements ArchiveListState {
  const factory _ArchiveListState(
      {final List<ArchivedContent> items,
      final int total,
      final int page,
      final bool isLoading,
      final bool hasMore,
      final String? selectedType,
      final String? error}) = _$ArchiveListStateImpl;

  @override
  List<ArchivedContent> get items;
  @override
  int get total;
  @override
  int get page;
  @override
  bool get isLoading;
  @override
  bool get hasMore;
  @override
  String? get selectedType;
  @override
  String? get error;
  @override
  @JsonKey(ignore: true)
  _$$ArchiveListStateImplCopyWith<_$ArchiveListStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
