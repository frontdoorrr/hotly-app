import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/place.dart';
import '../../../../shared/data/mock_places.dart';
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

    // 개발 모드에서는 Mock 데이터 우선 사용
    if (kDebugMode) {
      debugPrint('📦 Loading mock places data (${MockPlaces.savedPlaces.length} places)');
      await Future.delayed(const Duration(milliseconds: 500)); // API 호출 시뮬레이션

      state = state.copyWith(
        isLoading: false,
        hasError: false,
        places: MockPlaces.savedPlaces,
      );
      return;
    }

    // 프로덕션 모드에서는 실제 API 호출
    final result = await _repository.getPlaces(page: 1, pageSize: 100);

    result.fold(
      (error) {
        debugPrint('⚠️ Failed to load places from API: ${error.message}');
        debugPrint('📦 Falling back to mock data');

        // API 실패 시 Mock 데이터로 fallback
        state = state.copyWith(
          isLoading: false,
          hasError: false,
          places: MockPlaces.savedPlaces,
          errorMessage: 'Using mock data (API error: ${error.message})',
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
