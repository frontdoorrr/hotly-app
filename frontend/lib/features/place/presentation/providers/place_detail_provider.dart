import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/place.dart';
import '../../data/repositories/place_repository_impl.dart';
import '../../domain/repositories/place_repository.dart';
import '../../domain/usecases/get_place_detail.dart';

part 'place_detail_provider.freezed.dart';

@freezed
class PlaceDetailState with _$PlaceDetailState {
  const factory PlaceDetailState({
    Place? place,
    @Default([]) List<Place> similarPlaces,
    @Default(false) bool isLoading,
    @Default(false) bool isLoadingSimilar,
    @Default(false) bool isLiked,
    @Default(false) bool isSaved,
    ApiException? error,
  }) = _PlaceDetailState;
}

class PlaceDetailNotifier extends StateNotifier<PlaceDetailState> {
  final PlaceRepository _repository;
  final GetPlaceDetail _getPlaceDetailUseCase;
  final String placeId;

  PlaceDetailNotifier(this._repository, this.placeId)
      : _getPlaceDetailUseCase = GetPlaceDetail(_repository),
        super(const PlaceDetailState()) {
    _loadPlaceDetail();
    _loadSimilarPlaces();
  }

  Future<void> _loadPlaceDetail() async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _getPlaceDetailUseCase(placeId);

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (place) {
        state = state.copyWith(
          isLoading: false,
          place: place,
          isLiked: place.isLiked ?? false,
          isSaved: place.isSaved ?? false,
          error: null,
        );
      },
    );
  }

  Future<void> _loadSimilarPlaces() async {
    state = state.copyWith(isLoadingSimilar: true);

    final result = await _repository.getSimilarPlaces(placeId: placeId);

    result.fold(
      (_) {
        state = state.copyWith(isLoadingSimilar: false);
      },
      (places) {
        state = state.copyWith(
          isLoadingSimilar: false,
          similarPlaces: places,
        );
      },
    );
  }

  Future<void> toggleLike() async {
    final previousState = state.isLiked;
    state = state.copyWith(isLiked: !previousState);

    final result = await _repository.toggleLike(placeId);

    result.fold(
      (_) {
        // Revert on error
        state = state.copyWith(isLiked: previousState);
      },
      (_) {
        // Success - state already updated optimistically
      },
    );
  }

  Future<void> toggleSave() async {
    final previousState = state.isSaved;
    state = state.copyWith(isSaved: !previousState);

    final result = await _repository.toggleSave(placeId);

    result.fold(
      (_) {
        // Revert on error
        state = state.copyWith(isSaved: previousState);
      },
      (_) {
        // Success - state already updated optimistically
      },
    );
  }

  Future<void> refresh() async {
    await _loadPlaceDetail();
    await _loadSimilarPlaces();
  }
}

final placeDetailProvider =
    StateNotifierProvider.family<PlaceDetailNotifier, PlaceDetailState, String>(
  (ref, placeId) {
    final repository = ref.watch(placeRepositoryProvider);
    return PlaceDetailNotifier(repository, placeId);
  },
);
