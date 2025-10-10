// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'search_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$SearchState {
  String get searchQuery => throw _privateConstructorUsedError;
  List<Place> get searchResults => throw _privateConstructorUsedError;
  List<String> get autocompleteSuggestions =>
      throw _privateConstructorUsedError;
  List<String> get searchHistory => throw _privateConstructorUsedError;
  bool get isSearching => throw _privateConstructorUsedError;
  bool get isLoadingSuggestions => throw _privateConstructorUsedError;
  bool get isLoadingHistory => throw _privateConstructorUsedError;
  ApiException? get error => throw _privateConstructorUsedError;

  /// Create a copy of SearchState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $SearchStateCopyWith<SearchState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $SearchStateCopyWith<$Res> {
  factory $SearchStateCopyWith(
          SearchState value, $Res Function(SearchState) then) =
      _$SearchStateCopyWithImpl<$Res, SearchState>;
  @useResult
  $Res call(
      {String searchQuery,
      List<Place> searchResults,
      List<String> autocompleteSuggestions,
      List<String> searchHistory,
      bool isSearching,
      bool isLoadingSuggestions,
      bool isLoadingHistory,
      ApiException? error});
}

/// @nodoc
class _$SearchStateCopyWithImpl<$Res, $Val extends SearchState>
    implements $SearchStateCopyWith<$Res> {
  _$SearchStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of SearchState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? searchQuery = null,
    Object? searchResults = null,
    Object? autocompleteSuggestions = null,
    Object? searchHistory = null,
    Object? isSearching = null,
    Object? isLoadingSuggestions = null,
    Object? isLoadingHistory = null,
    Object? error = freezed,
  }) {
    return _then(_value.copyWith(
      searchQuery: null == searchQuery
          ? _value.searchQuery
          : searchQuery // ignore: cast_nullable_to_non_nullable
              as String,
      searchResults: null == searchResults
          ? _value.searchResults
          : searchResults // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      autocompleteSuggestions: null == autocompleteSuggestions
          ? _value.autocompleteSuggestions
          : autocompleteSuggestions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      searchHistory: null == searchHistory
          ? _value.searchHistory
          : searchHistory // ignore: cast_nullable_to_non_nullable
              as List<String>,
      isSearching: null == isSearching
          ? _value.isSearching
          : isSearching // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingSuggestions: null == isLoadingSuggestions
          ? _value.isLoadingSuggestions
          : isLoadingSuggestions // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingHistory: null == isLoadingHistory
          ? _value.isLoadingHistory
          : isLoadingHistory // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as ApiException?,
    ) as $Val);
  }
}

/// @nodoc
abstract class _$$SearchStateImplCopyWith<$Res>
    implements $SearchStateCopyWith<$Res> {
  factory _$$SearchStateImplCopyWith(
          _$SearchStateImpl value, $Res Function(_$SearchStateImpl) then) =
      __$$SearchStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {String searchQuery,
      List<Place> searchResults,
      List<String> autocompleteSuggestions,
      List<String> searchHistory,
      bool isSearching,
      bool isLoadingSuggestions,
      bool isLoadingHistory,
      ApiException? error});
}

/// @nodoc
class __$$SearchStateImplCopyWithImpl<$Res>
    extends _$SearchStateCopyWithImpl<$Res, _$SearchStateImpl>
    implements _$$SearchStateImplCopyWith<$Res> {
  __$$SearchStateImplCopyWithImpl(
      _$SearchStateImpl _value, $Res Function(_$SearchStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of SearchState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? searchQuery = null,
    Object? searchResults = null,
    Object? autocompleteSuggestions = null,
    Object? searchHistory = null,
    Object? isSearching = null,
    Object? isLoadingSuggestions = null,
    Object? isLoadingHistory = null,
    Object? error = freezed,
  }) {
    return _then(_$SearchStateImpl(
      searchQuery: null == searchQuery
          ? _value.searchQuery
          : searchQuery // ignore: cast_nullable_to_non_nullable
              as String,
      searchResults: null == searchResults
          ? _value._searchResults
          : searchResults // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      autocompleteSuggestions: null == autocompleteSuggestions
          ? _value._autocompleteSuggestions
          : autocompleteSuggestions // ignore: cast_nullable_to_non_nullable
              as List<String>,
      searchHistory: null == searchHistory
          ? _value._searchHistory
          : searchHistory // ignore: cast_nullable_to_non_nullable
              as List<String>,
      isSearching: null == isSearching
          ? _value.isSearching
          : isSearching // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingSuggestions: null == isLoadingSuggestions
          ? _value.isLoadingSuggestions
          : isLoadingSuggestions // ignore: cast_nullable_to_non_nullable
              as bool,
      isLoadingHistory: null == isLoadingHistory
          ? _value.isLoadingHistory
          : isLoadingHistory // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as ApiException?,
    ));
  }
}

/// @nodoc

class _$SearchStateImpl implements _SearchState {
  const _$SearchStateImpl(
      {this.searchQuery = '',
      final List<Place> searchResults = const [],
      final List<String> autocompleteSuggestions = const [],
      final List<String> searchHistory = const [],
      this.isSearching = false,
      this.isLoadingSuggestions = false,
      this.isLoadingHistory = false,
      this.error})
      : _searchResults = searchResults,
        _autocompleteSuggestions = autocompleteSuggestions,
        _searchHistory = searchHistory;

  @override
  @JsonKey()
  final String searchQuery;
  final List<Place> _searchResults;
  @override
  @JsonKey()
  List<Place> get searchResults {
    if (_searchResults is EqualUnmodifiableListView) return _searchResults;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_searchResults);
  }

  final List<String> _autocompleteSuggestions;
  @override
  @JsonKey()
  List<String> get autocompleteSuggestions {
    if (_autocompleteSuggestions is EqualUnmodifiableListView)
      return _autocompleteSuggestions;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_autocompleteSuggestions);
  }

  final List<String> _searchHistory;
  @override
  @JsonKey()
  List<String> get searchHistory {
    if (_searchHistory is EqualUnmodifiableListView) return _searchHistory;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_searchHistory);
  }

  @override
  @JsonKey()
  final bool isSearching;
  @override
  @JsonKey()
  final bool isLoadingSuggestions;
  @override
  @JsonKey()
  final bool isLoadingHistory;
  @override
  final ApiException? error;

  @override
  String toString() {
    return 'SearchState(searchQuery: $searchQuery, searchResults: $searchResults, autocompleteSuggestions: $autocompleteSuggestions, searchHistory: $searchHistory, isSearching: $isSearching, isLoadingSuggestions: $isLoadingSuggestions, isLoadingHistory: $isLoadingHistory, error: $error)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$SearchStateImpl &&
            (identical(other.searchQuery, searchQuery) ||
                other.searchQuery == searchQuery) &&
            const DeepCollectionEquality()
                .equals(other._searchResults, _searchResults) &&
            const DeepCollectionEquality().equals(
                other._autocompleteSuggestions, _autocompleteSuggestions) &&
            const DeepCollectionEquality()
                .equals(other._searchHistory, _searchHistory) &&
            (identical(other.isSearching, isSearching) ||
                other.isSearching == isSearching) &&
            (identical(other.isLoadingSuggestions, isLoadingSuggestions) ||
                other.isLoadingSuggestions == isLoadingSuggestions) &&
            (identical(other.isLoadingHistory, isLoadingHistory) ||
                other.isLoadingHistory == isLoadingHistory) &&
            (identical(other.error, error) || other.error == error));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      searchQuery,
      const DeepCollectionEquality().hash(_searchResults),
      const DeepCollectionEquality().hash(_autocompleteSuggestions),
      const DeepCollectionEquality().hash(_searchHistory),
      isSearching,
      isLoadingSuggestions,
      isLoadingHistory,
      error);

  /// Create a copy of SearchState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$SearchStateImplCopyWith<_$SearchStateImpl> get copyWith =>
      __$$SearchStateImplCopyWithImpl<_$SearchStateImpl>(this, _$identity);
}

abstract class _SearchState implements SearchState {
  const factory _SearchState(
      {final String searchQuery,
      final List<Place> searchResults,
      final List<String> autocompleteSuggestions,
      final List<String> searchHistory,
      final bool isSearching,
      final bool isLoadingSuggestions,
      final bool isLoadingHistory,
      final ApiException? error}) = _$SearchStateImpl;

  @override
  String get searchQuery;
  @override
  List<Place> get searchResults;
  @override
  List<String> get autocompleteSuggestions;
  @override
  List<String> get searchHistory;
  @override
  bool get isSearching;
  @override
  bool get isLoadingSuggestions;
  @override
  bool get isLoadingHistory;
  @override
  ApiException? get error;

  /// Create a copy of SearchState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$SearchStateImplCopyWith<_$SearchStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
