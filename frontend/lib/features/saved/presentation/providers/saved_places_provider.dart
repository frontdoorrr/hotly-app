import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/utils/app_logger.dart';
import '../../../../shared/models/place.dart';
import '../../../../shared/data/mock_places.dart';
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

    // 개발 모드에서는 Mock 데이터 우선 사용
    if (kDebugMode) {
      AppLogger.d('Loading mock places data (${MockPlaces.savedPlaces.length} places)', tag: 'SavedPlaces');
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
        AppLogger.w('Failed to load places from API: ${error.message}', tag: 'SavedPlaces');
        AppLogger.d('Falling back to mock data', tag: 'SavedPlaces');

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
