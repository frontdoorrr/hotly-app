import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/place.dart';
import '../../../place/domain/repositories/place_repository.dart';
import '../../../place/data/repositories/place_repository_impl.dart';

part 'saved_places_provider.freezed.dart';

@freezed
class SavedPlacesState with _$SavedPlacesState {
  const factory SavedPlacesState({
    @Default([]) List<Place> places,
    @Default(false) bool isLoading,
    @Default(false) bool hasError,
    String? errorMessage,
  }) = _SavedPlacesState;
}

class SavedPlacesNotifier extends StateNotifier<SavedPlacesState> {
  final PlaceRepository _repository;

  SavedPlacesNotifier(this._repository) : super(const SavedPlacesState()) {
    loadPlaces();
  }

  Future<void> loadPlaces() async {
    state = state.copyWith(isLoading: true, hasError: false);

    final result = await _repository.getPlaces(page: 1, pageSize: 100);

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          hasError: true,
          errorMessage: error.message,
        );
      },
      (places) {
        state = state.copyWith(
          isLoading: false,
          hasError: false,
          places: places,
        );
      },
    );
  }

  Future<void> refresh() async {
    await loadPlaces();
  }
}

final savedPlacesProvider =
    StateNotifierProvider<SavedPlacesNotifier, SavedPlacesState>((ref) {
  final repository = ref.watch(placeRepositoryProvider);
  return SavedPlacesNotifier(repository);
});
