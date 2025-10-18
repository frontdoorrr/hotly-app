// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

part of 'map_provider.dart';

// **************************************************************************
// FreezedGenerator
// **************************************************************************

T _$identity<T>(T value) => value;

final _privateConstructorUsedError = UnsupportedError(
    'It seems like you constructed your class using `MyClass._()`. This constructor is only meant to be used by freezed and you are not supposed to need it nor use it.\nPlease check the documentation here for more information: https://github.com/rrousselGit/freezed#adding-getters-and-methods-to-our-models');

/// @nodoc
mixin _$MapState {
  CoordinatePoint? get currentLocation => throw _privateConstructorUsedError;
  List<PlaceSearchResult> get searchResults =>
      throw _privateConstructorUsedError;
  List<Map<String, dynamic>> get placesOnMap =>
      throw _privateConstructorUsedError;
  List<Place> get visiblePlaces =>
      throw _privateConstructorUsedError; // 현재 화면에 보이는 장소들
  List<MarkerCluster> get clusters =>
      throw _privateConstructorUsedError; // 마커 클러스터들
  MapBounds? get currentBounds => throw _privateConstructorUsedError; // 현재 뷰포트
  bool get isLoading => throw _privateConstructorUsedError;
  bool get isSearching => throw _privateConstructorUsedError;
  bool get showSearchThisAreaButton =>
      throw _privateConstructorUsedError; // "이 지역 검색" 버튼 표시 여부
  String? get error => throw _privateConstructorUsedError;
  String? get selectedPlaceId => throw _privateConstructorUsedError;
  PlaceSearchResult? get selectedSearchResult =>
      throw _privateConstructorUsedError;

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  $MapStateCopyWith<MapState> get copyWith =>
      throw _privateConstructorUsedError;
}

/// @nodoc
abstract class $MapStateCopyWith<$Res> {
  factory $MapStateCopyWith(MapState value, $Res Function(MapState) then) =
      _$MapStateCopyWithImpl<$Res, MapState>;
  @useResult
  $Res call(
      {CoordinatePoint? currentLocation,
      List<PlaceSearchResult> searchResults,
      List<Map<String, dynamic>> placesOnMap,
      List<Place> visiblePlaces,
      List<MarkerCluster> clusters,
      MapBounds? currentBounds,
      bool isLoading,
      bool isSearching,
      bool showSearchThisAreaButton,
      String? error,
      String? selectedPlaceId,
      PlaceSearchResult? selectedSearchResult});

  $CoordinatePointCopyWith<$Res>? get currentLocation;
  $MapBoundsCopyWith<$Res>? get currentBounds;
  $PlaceSearchResultCopyWith<$Res>? get selectedSearchResult;
}

/// @nodoc
class _$MapStateCopyWithImpl<$Res, $Val extends MapState>
    implements $MapStateCopyWith<$Res> {
  _$MapStateCopyWithImpl(this._value, this._then);

  // ignore: unused_field
  final $Val _value;
  // ignore: unused_field
  final $Res Function($Val) _then;

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentLocation = freezed,
    Object? searchResults = null,
    Object? placesOnMap = null,
    Object? visiblePlaces = null,
    Object? clusters = null,
    Object? currentBounds = freezed,
    Object? isLoading = null,
    Object? isSearching = null,
    Object? showSearchThisAreaButton = null,
    Object? error = freezed,
    Object? selectedPlaceId = freezed,
    Object? selectedSearchResult = freezed,
  }) {
    return _then(_value.copyWith(
      currentLocation: freezed == currentLocation
          ? _value.currentLocation
          : currentLocation // ignore: cast_nullable_to_non_nullable
              as CoordinatePoint?,
      searchResults: null == searchResults
          ? _value.searchResults
          : searchResults // ignore: cast_nullable_to_non_nullable
              as List<PlaceSearchResult>,
      placesOnMap: null == placesOnMap
          ? _value.placesOnMap
          : placesOnMap // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>,
      visiblePlaces: null == visiblePlaces
          ? _value.visiblePlaces
          : visiblePlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      clusters: null == clusters
          ? _value.clusters
          : clusters // ignore: cast_nullable_to_non_nullable
              as List<MarkerCluster>,
      currentBounds: freezed == currentBounds
          ? _value.currentBounds
          : currentBounds // ignore: cast_nullable_to_non_nullable
              as MapBounds?,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isSearching: null == isSearching
          ? _value.isSearching
          : isSearching // ignore: cast_nullable_to_non_nullable
              as bool,
      showSearchThisAreaButton: null == showSearchThisAreaButton
          ? _value.showSearchThisAreaButton
          : showSearchThisAreaButton // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedPlaceId: freezed == selectedPlaceId
          ? _value.selectedPlaceId
          : selectedPlaceId // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedSearchResult: freezed == selectedSearchResult
          ? _value.selectedSearchResult
          : selectedSearchResult // ignore: cast_nullable_to_non_nullable
              as PlaceSearchResult?,
    ) as $Val);
  }

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $CoordinatePointCopyWith<$Res>? get currentLocation {
    if (_value.currentLocation == null) {
      return null;
    }

    return $CoordinatePointCopyWith<$Res>(_value.currentLocation!, (value) {
      return _then(_value.copyWith(currentLocation: value) as $Val);
    });
  }

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $MapBoundsCopyWith<$Res>? get currentBounds {
    if (_value.currentBounds == null) {
      return null;
    }

    return $MapBoundsCopyWith<$Res>(_value.currentBounds!, (value) {
      return _then(_value.copyWith(currentBounds: value) as $Val);
    });
  }

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @pragma('vm:prefer-inline')
  $PlaceSearchResultCopyWith<$Res>? get selectedSearchResult {
    if (_value.selectedSearchResult == null) {
      return null;
    }

    return $PlaceSearchResultCopyWith<$Res>(_value.selectedSearchResult!,
        (value) {
      return _then(_value.copyWith(selectedSearchResult: value) as $Val);
    });
  }
}

/// @nodoc
abstract class _$$MapStateImplCopyWith<$Res>
    implements $MapStateCopyWith<$Res> {
  factory _$$MapStateImplCopyWith(
          _$MapStateImpl value, $Res Function(_$MapStateImpl) then) =
      __$$MapStateImplCopyWithImpl<$Res>;
  @override
  @useResult
  $Res call(
      {CoordinatePoint? currentLocation,
      List<PlaceSearchResult> searchResults,
      List<Map<String, dynamic>> placesOnMap,
      List<Place> visiblePlaces,
      List<MarkerCluster> clusters,
      MapBounds? currentBounds,
      bool isLoading,
      bool isSearching,
      bool showSearchThisAreaButton,
      String? error,
      String? selectedPlaceId,
      PlaceSearchResult? selectedSearchResult});

  @override
  $CoordinatePointCopyWith<$Res>? get currentLocation;
  @override
  $MapBoundsCopyWith<$Res>? get currentBounds;
  @override
  $PlaceSearchResultCopyWith<$Res>? get selectedSearchResult;
}

/// @nodoc
class __$$MapStateImplCopyWithImpl<$Res>
    extends _$MapStateCopyWithImpl<$Res, _$MapStateImpl>
    implements _$$MapStateImplCopyWith<$Res> {
  __$$MapStateImplCopyWithImpl(
      _$MapStateImpl _value, $Res Function(_$MapStateImpl) _then)
      : super(_value, _then);

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @pragma('vm:prefer-inline')
  @override
  $Res call({
    Object? currentLocation = freezed,
    Object? searchResults = null,
    Object? placesOnMap = null,
    Object? visiblePlaces = null,
    Object? clusters = null,
    Object? currentBounds = freezed,
    Object? isLoading = null,
    Object? isSearching = null,
    Object? showSearchThisAreaButton = null,
    Object? error = freezed,
    Object? selectedPlaceId = freezed,
    Object? selectedSearchResult = freezed,
  }) {
    return _then(_$MapStateImpl(
      currentLocation: freezed == currentLocation
          ? _value.currentLocation
          : currentLocation // ignore: cast_nullable_to_non_nullable
              as CoordinatePoint?,
      searchResults: null == searchResults
          ? _value._searchResults
          : searchResults // ignore: cast_nullable_to_non_nullable
              as List<PlaceSearchResult>,
      placesOnMap: null == placesOnMap
          ? _value._placesOnMap
          : placesOnMap // ignore: cast_nullable_to_non_nullable
              as List<Map<String, dynamic>>,
      visiblePlaces: null == visiblePlaces
          ? _value._visiblePlaces
          : visiblePlaces // ignore: cast_nullable_to_non_nullable
              as List<Place>,
      clusters: null == clusters
          ? _value._clusters
          : clusters // ignore: cast_nullable_to_non_nullable
              as List<MarkerCluster>,
      currentBounds: freezed == currentBounds
          ? _value.currentBounds
          : currentBounds // ignore: cast_nullable_to_non_nullable
              as MapBounds?,
      isLoading: null == isLoading
          ? _value.isLoading
          : isLoading // ignore: cast_nullable_to_non_nullable
              as bool,
      isSearching: null == isSearching
          ? _value.isSearching
          : isSearching // ignore: cast_nullable_to_non_nullable
              as bool,
      showSearchThisAreaButton: null == showSearchThisAreaButton
          ? _value.showSearchThisAreaButton
          : showSearchThisAreaButton // ignore: cast_nullable_to_non_nullable
              as bool,
      error: freezed == error
          ? _value.error
          : error // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedPlaceId: freezed == selectedPlaceId
          ? _value.selectedPlaceId
          : selectedPlaceId // ignore: cast_nullable_to_non_nullable
              as String?,
      selectedSearchResult: freezed == selectedSearchResult
          ? _value.selectedSearchResult
          : selectedSearchResult // ignore: cast_nullable_to_non_nullable
              as PlaceSearchResult?,
    ));
  }
}

/// @nodoc

class _$MapStateImpl implements _MapState {
  const _$MapStateImpl(
      {this.currentLocation,
      final List<PlaceSearchResult> searchResults = const [],
      final List<Map<String, dynamic>> placesOnMap = const [],
      final List<Place> visiblePlaces = const [],
      final List<MarkerCluster> clusters = const [],
      this.currentBounds,
      this.isLoading = false,
      this.isSearching = false,
      this.showSearchThisAreaButton = false,
      this.error,
      this.selectedPlaceId,
      this.selectedSearchResult})
      : _searchResults = searchResults,
        _placesOnMap = placesOnMap,
        _visiblePlaces = visiblePlaces,
        _clusters = clusters;

  @override
  final CoordinatePoint? currentLocation;
  final List<PlaceSearchResult> _searchResults;
  @override
  @JsonKey()
  List<PlaceSearchResult> get searchResults {
    if (_searchResults is EqualUnmodifiableListView) return _searchResults;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_searchResults);
  }

  final List<Map<String, dynamic>> _placesOnMap;
  @override
  @JsonKey()
  List<Map<String, dynamic>> get placesOnMap {
    if (_placesOnMap is EqualUnmodifiableListView) return _placesOnMap;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_placesOnMap);
  }

  final List<Place> _visiblePlaces;
  @override
  @JsonKey()
  List<Place> get visiblePlaces {
    if (_visiblePlaces is EqualUnmodifiableListView) return _visiblePlaces;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_visiblePlaces);
  }

// 현재 화면에 보이는 장소들
  final List<MarkerCluster> _clusters;
// 현재 화면에 보이는 장소들
  @override
  @JsonKey()
  List<MarkerCluster> get clusters {
    if (_clusters is EqualUnmodifiableListView) return _clusters;
    // ignore: implicit_dynamic_type
    return EqualUnmodifiableListView(_clusters);
  }

// 마커 클러스터들
  @override
  final MapBounds? currentBounds;
// 현재 뷰포트
  @override
  @JsonKey()
  final bool isLoading;
  @override
  @JsonKey()
  final bool isSearching;
  @override
  @JsonKey()
  final bool showSearchThisAreaButton;
// "이 지역 검색" 버튼 표시 여부
  @override
  final String? error;
  @override
  final String? selectedPlaceId;
  @override
  final PlaceSearchResult? selectedSearchResult;

  @override
  String toString() {
    return 'MapState(currentLocation: $currentLocation, searchResults: $searchResults, placesOnMap: $placesOnMap, visiblePlaces: $visiblePlaces, clusters: $clusters, currentBounds: $currentBounds, isLoading: $isLoading, isSearching: $isSearching, showSearchThisAreaButton: $showSearchThisAreaButton, error: $error, selectedPlaceId: $selectedPlaceId, selectedSearchResult: $selectedSearchResult)';
  }

  @override
  bool operator ==(Object other) {
    return identical(this, other) ||
        (other.runtimeType == runtimeType &&
            other is _$MapStateImpl &&
            (identical(other.currentLocation, currentLocation) ||
                other.currentLocation == currentLocation) &&
            const DeepCollectionEquality()
                .equals(other._searchResults, _searchResults) &&
            const DeepCollectionEquality()
                .equals(other._placesOnMap, _placesOnMap) &&
            const DeepCollectionEquality()
                .equals(other._visiblePlaces, _visiblePlaces) &&
            const DeepCollectionEquality().equals(other._clusters, _clusters) &&
            (identical(other.currentBounds, currentBounds) ||
                other.currentBounds == currentBounds) &&
            (identical(other.isLoading, isLoading) ||
                other.isLoading == isLoading) &&
            (identical(other.isSearching, isSearching) ||
                other.isSearching == isSearching) &&
            (identical(
                    other.showSearchThisAreaButton, showSearchThisAreaButton) ||
                other.showSearchThisAreaButton == showSearchThisAreaButton) &&
            (identical(other.error, error) || other.error == error) &&
            (identical(other.selectedPlaceId, selectedPlaceId) ||
                other.selectedPlaceId == selectedPlaceId) &&
            (identical(other.selectedSearchResult, selectedSearchResult) ||
                other.selectedSearchResult == selectedSearchResult));
  }

  @override
  int get hashCode => Object.hash(
      runtimeType,
      currentLocation,
      const DeepCollectionEquality().hash(_searchResults),
      const DeepCollectionEquality().hash(_placesOnMap),
      const DeepCollectionEquality().hash(_visiblePlaces),
      const DeepCollectionEquality().hash(_clusters),
      currentBounds,
      isLoading,
      isSearching,
      showSearchThisAreaButton,
      error,
      selectedPlaceId,
      selectedSearchResult);

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @JsonKey(includeFromJson: false, includeToJson: false)
  @override
  @pragma('vm:prefer-inline')
  _$$MapStateImplCopyWith<_$MapStateImpl> get copyWith =>
      __$$MapStateImplCopyWithImpl<_$MapStateImpl>(this, _$identity);
}

abstract class _MapState implements MapState {
  const factory _MapState(
      {final CoordinatePoint? currentLocation,
      final List<PlaceSearchResult> searchResults,
      final List<Map<String, dynamic>> placesOnMap,
      final List<Place> visiblePlaces,
      final List<MarkerCluster> clusters,
      final MapBounds? currentBounds,
      final bool isLoading,
      final bool isSearching,
      final bool showSearchThisAreaButton,
      final String? error,
      final String? selectedPlaceId,
      final PlaceSearchResult? selectedSearchResult}) = _$MapStateImpl;

  @override
  CoordinatePoint? get currentLocation;
  @override
  List<PlaceSearchResult> get searchResults;
  @override
  List<Map<String, dynamic>> get placesOnMap;
  @override
  List<Place> get visiblePlaces; // 현재 화면에 보이는 장소들
  @override
  List<MarkerCluster> get clusters; // 마커 클러스터들
  @override
  MapBounds? get currentBounds; // 현재 뷰포트
  @override
  bool get isLoading;
  @override
  bool get isSearching;
  @override
  bool get showSearchThisAreaButton; // "이 지역 검색" 버튼 표시 여부
  @override
  String? get error;
  @override
  String? get selectedPlaceId;
  @override
  PlaceSearchResult? get selectedSearchResult;

  /// Create a copy of MapState
  /// with the given fields replaced by the non-null parameter values.
  @override
  @JsonKey(includeFromJson: false, includeToJson: false)
  _$$MapStateImplCopyWith<_$MapStateImpl> get copyWith =>
      throw _privateConstructorUsedError;
}
