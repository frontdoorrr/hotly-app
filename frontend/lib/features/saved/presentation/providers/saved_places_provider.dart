import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/place.dart';
import '../../../place/domain/repositories/place_repository.dart';
import '../../../place/data/repositories/place_repository_impl.dart';

part 'saved_places_provider.freezed.dart';

@freezed
class SavedPlacesState with _$SavedPlacesState {
  const factory SavedPlacesState({
    @Default([]) List<Place> places,
    @Default({}) Set<String> selectedTags,
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

    AppLogger.d('Loading saved places from API', tag: 'SavedPlaces');

    final result = await _repository.getSavedPlaces();

    result.fold(
      (error) {
        AppLogger.e('Failed to load saved places: ${error.message}', tag: 'SavedPlaces');
        state = state.copyWith(
          isLoading: false,
          hasError: true,
          places: [],
          errorMessage: error.message,
        );
      },
      (places) {
        AppLogger.d('Loaded ${places.length} saved places', tag: 'SavedPlaces');
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

  /// 태그 선택/해제
  void toggleTag(String tag) {
    final currentTags = Set<String>.from(state.selectedTags);
    if (currentTags.contains(tag)) {
      currentTags.remove(tag);
    } else {
      currentTags.add(tag);
    }
    state = state.copyWith(selectedTags: currentTags);
  }

  /// 모든 태그 필터 초기화
  void clearTagFilters() {
    state = state.copyWith(selectedTags: {});
  }

  /// 필터링된 장소 목록
  List<Place> get filteredPlaces {
    if (state.selectedTags.isEmpty) {
      return state.places;
    }
    return state.places.where((place) {
      return place.tags.any((tag) => state.selectedTags.contains(tag));
    }).toList();
  }

  /// 태그 통계 계산
  Map<String, int> get tagStatistics {
    final tagCounts = <String, int>{};
    for (final place in state.places) {
      for (final tag in place.tags) {
        tagCounts[tag] = (tagCounts[tag] ?? 0) + 1;
      }
    }
    final sortedEntries = tagCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return Map.fromEntries(sortedEntries);
  }
}

final savedPlacesProvider =
    StateNotifierProvider<SavedPlacesNotifier, SavedPlacesState>((ref) {
  final repository = ref.watch(placeRepositoryProvider);
  return SavedPlacesNotifier(repository);
});
