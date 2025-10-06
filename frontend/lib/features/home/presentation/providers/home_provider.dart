import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../shared/models/place.dart';
import '../../../../core/network/dio_client.dart';
import '../../domain/repositories/home_repository.dart';
import '../../domain/usecases/get_recommended_places.dart';
import '../../domain/usecases/get_nearby_places.dart';
import '../../data/datasources/home_remote_datasource.dart';
import '../../data/repositories/home_repository_impl.dart';

part 'home_provider.freezed.dart';

/// Home State
@freezed
class HomeState with _$HomeState {
  const factory HomeState({
    @Default([]) List<Place> recommendedPlaces,
    @Default([]) List<Place> nearbyPlaces,
    @Default([]) List<Place> popularPlaces,
    @Default(false) bool isLoadingRecommended,
    @Default(false) bool isLoadingNearby,
    @Default(false) bool isLoadingPopular,
    String? error,
  }) = _HomeState;
}

/// Home Provider Dependencies
final homeRemoteDataSourceProvider = Provider<HomeRemoteDataSource>((ref) {
  return HomeRemoteDataSource(ref.read(dioProvider));
});

final homeRepositoryProvider = Provider<HomeRepository>((ref) {
  return HomeRepositoryImpl(ref.read(homeRemoteDataSourceProvider));
});

/// Home State Notifier
class HomeNotifier extends StateNotifier<HomeState> {
  final GetRecommendedPlaces getRecommendedPlaces;
  final GetNearbyPlaces getNearbyPlaces;
  final HomeRepository repository;

  HomeNotifier({
    required this.getRecommendedPlaces,
    required this.getNearbyPlaces,
    required this.repository,
  }) : super(const HomeState());

  /// 추천 장소 로드
  Future<void> loadRecommendedPlaces() async {
    state = state.copyWith(isLoadingRecommended: true, error: null);

    final result = await getRecommendedPlaces(limit: 10);

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoadingRecommended: false,
          error: failure.message,
        );
      },
      (places) {
        state = state.copyWith(
          recommendedPlaces: places,
          isLoadingRecommended: false,
        );
      },
    );
  }

  /// 근처 장소 로드
  Future<void> loadNearbyPlaces(double lat, double lng) async {
    state = state.copyWith(isLoadingNearby: true, error: null);

    final result = await getNearbyPlaces(
      latitude: lat,
      longitude: lng,
      limit: 20,
    );

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoadingNearby: false,
          error: failure.message,
        );
      },
      (places) {
        state = state.copyWith(
          nearbyPlaces: places,
          isLoadingNearby: false,
        );
      },
    );
  }

  /// 인기 장소 로드
  Future<void> loadPopularPlaces() async {
    state = state.copyWith(isLoadingPopular: true, error: null);

    final result = await repository.getPopularPlaces(limit: 12);

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoadingPopular: false,
          error: failure.message,
        );
      },
      (places) {
        state = state.copyWith(
          popularPlaces: places,
          isLoadingPopular: false,
        );
      },
    );
  }

  /// 전체 데이터 새로고침
  Future<void> refreshAll(double? lat, double? lng) async {
    await Future.wait([
      loadRecommendedPlaces(),
      if (lat != null && lng != null) loadNearbyPlaces(lat, lng),
      loadPopularPlaces(),
    ]);
  }
}

/// Home Provider
final homeProvider =
    StateNotifierProvider<HomeNotifier, HomeState>((ref) {
  final repository = ref.read(homeRepositoryProvider);

  return HomeNotifier(
    getRecommendedPlaces: GetRecommendedPlaces(repository),
    getNearbyPlaces: GetNearbyPlaces(repository),
    repository: repository,
  );
});
