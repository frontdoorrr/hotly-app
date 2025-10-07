import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/place.dart';
import '../../data/repositories/search_repository_impl.dart';
import '../../domain/repositories/search_repository.dart';
import '../../domain/usecases/search_places.dart';

part 'search_provider.freezed.dart';

@freezed
class SearchState with _$SearchState {
  const factory SearchState({
    @Default('') String searchQuery,
    @Default([]) List<Place> searchResults,
    @Default([]) List<String> autocompleteSuggestions,
    @Default([]) List<String> searchHistory,
    @Default(false) bool isSearching,
    @Default(false) bool isLoadingSuggestions,
    @Default(false) bool isLoadingHistory,
    ApiException? error,
  }) = _SearchState;
}

class SearchNotifier extends StateNotifier<SearchState> {
  final SearchRepository _repository;
  final SearchPlaces _searchPlacesUseCase;

  SearchNotifier(this._repository)
      : _searchPlacesUseCase = SearchPlaces(_repository),
        super(const SearchState()) {
    _loadSearchHistory();
  }

  Future<void> search({
    String? category,
    double? maxDistance,
    double? minRating,
  }) async {
    if (state.searchQuery.trim().isEmpty) {
      state = state.copyWith(
        searchResults: [],
        error: null,
      );
      return;
    }

    state = state.copyWith(isSearching: true, error: null);

    final result = await _searchPlacesUseCase(
      query: state.searchQuery,
      category: category,
      maxDistance: maxDistance,
      minRating: minRating,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isSearching: false,
          error: error,
          searchResults: [],
        );
      },
      (places) async {
        state = state.copyWith(
          isSearching: false,
          searchResults: places,
          error: null,
        );
        // Save to search history
        await _repository.saveSearchHistory(state.searchQuery);
        await _loadSearchHistory();
      },
    );
  }

  Future<void> loadAutocompleteSuggestions(String query) async {
    if (query.trim().isEmpty) {
      state = state.copyWith(autocompleteSuggestions: []);
      return;
    }

    state = state.copyWith(isLoadingSuggestions: true);

    final result = await _repository.getAutocompleteSuggestions(query: query);

    result.fold(
      (error) {
        state = state.copyWith(
          isLoadingSuggestions: false,
          autocompleteSuggestions: [],
        );
      },
      (suggestions) {
        state = state.copyWith(
          isLoadingSuggestions: false,
          autocompleteSuggestions: suggestions,
        );
      },
    );
  }

  Future<void> _loadSearchHistory() async {
    state = state.copyWith(isLoadingHistory: true);
    final history = await _repository.getSearchHistory();
    state = state.copyWith(
      searchHistory: history,
      isLoadingHistory: false,
    );
  }

  Future<void> clearSearchHistory() async {
    await _repository.clearSearchHistory();
    state = state.copyWith(searchHistory: []);
  }

  void updateSearchQuery(String query) {
    state = state.copyWith(searchQuery: query);
    if (query.isNotEmpty) {
      loadAutocompleteSuggestions(query);
    } else {
      state = state.copyWith(autocompleteSuggestions: []);
    }
  }

  void selectSuggestion(String suggestion) {
    state = state.copyWith(
      searchQuery: suggestion,
      autocompleteSuggestions: [],
    );
    search();
  }

  void clearSearchResults() {
    state = state.copyWith(
      searchQuery: '',
      searchResults: [],
      autocompleteSuggestions: [],
      error: null,
    );
  }
}

final searchProvider = StateNotifierProvider<SearchNotifier, SearchState>((ref) {
  final repository = ref.watch(searchRepositoryProvider);
  return SearchNotifier(repository);
});
