import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/dio_client.dart';
import '../../data/datasources/archive_remote_datasource.dart';
import '../../data/repositories/archive_repository_impl.dart';
import '../../domain/entities/archived_content.dart';
import '../../domain/repositories/archive_repository.dart';

part 'archive_provider.freezed.dart';

// ------------------------------------------------------------------
// 아카이빙 입력 상태 (URL 입력 → 분석 → 결과)
// ------------------------------------------------------------------

@freezed
class ArchiveInputState with _$ArchiveInputState {
  const factory ArchiveInputState({
    @Default(false) bool isLoading,
    ArchivedContent? result,
    String? error,
    String? inputUrl,
  }) = _ArchiveInputState;
}

class ArchiveInputNotifier extends StateNotifier<ArchiveInputState> {
  final ArchiveRepository _repository;

  ArchiveInputNotifier(this._repository) : super(const ArchiveInputState());

  Future<void> archiveUrl(String url, {bool force = false}) async {
    state = state.copyWith(isLoading: true, error: null, inputUrl: url);

    final result = await _repository.archiveUrl(url, force: force);

    result.fold(
      (error) => state = state.copyWith(isLoading: false, error: error.toString()),
      (content) => state = state.copyWith(isLoading: false, result: content),
    );
  }

  void setInputUrl(String url) => state = state.copyWith(inputUrl: url);

  void clear() => state = const ArchiveInputState();
}

// ------------------------------------------------------------------
// 아카이빙 목록 상태
// ------------------------------------------------------------------

@freezed
class ArchiveListState with _$ArchiveListState {
  const factory ArchiveListState({
    @Default([]) List<ArchivedContent> items,
    @Default(0) int total,
    @Default(1) int page,
    @Default(false) bool isLoading,
    @Default(false) bool hasMore,
    ContentType? selectedType,
    String? error,
  }) = _ArchiveListState;
}

class ArchiveListNotifier extends StateNotifier<ArchiveListState> {
  final ArchiveRepository _repository;
  static const _pageSize = 20;

  ArchiveListNotifier(this._repository) : super(const ArchiveListState());

  Future<void> load({ContentType? contentType, bool refresh = false}) async {
    final targetType = contentType ?? state.selectedType;
    final page = refresh ? 1 : state.page;

    if (state.isLoading) return;

    state = state.copyWith(
      isLoading: true,
      error: null,
      selectedType: targetType,
      items: refresh ? [] : state.items,
      page: page,
    );

    final result = await _repository.getArchives(
      contentType: targetType,
      page: page,
      pageSize: _pageSize,
    );

    result.fold(
      (error) => state = state.copyWith(isLoading: false, error: error.toString()),
      (list) => state = state.copyWith(
        isLoading: false,
        items: refresh ? list.items : [...state.items, ...list.items],
        total: list.total,
        page: page + 1,
        hasMore: (refresh ? list.items.length : state.items.length + list.items.length) < list.total,
      ),
    );
  }

  Future<void> delete(String id) async {
    final result = await _repository.deleteArchive(id);
    result.fold(
      (error) => state = state.copyWith(error: error.toString()),
      (_) => state = state.copyWith(
        items: state.items.where((e) => e.id != id).toList(),
        total: state.total - 1,
      ),
    );
  }

  void filterByType(ContentType? type) => load(contentType: type, refresh: true);
}

// ------------------------------------------------------------------
// Providers
// ------------------------------------------------------------------

final archiveRepositoryProvider = Provider<ArchiveRepository>((ref) {
  final dio = ref.watch(dioClientProvider).dio;
  return ArchiveRepositoryImpl(ArchiveRemoteDataSource(dio));
});

final archiveInputProvider =
    StateNotifierProvider<ArchiveInputNotifier, ArchiveInputState>((ref) {
  return ArchiveInputNotifier(ref.watch(archiveRepositoryProvider));
});

final archiveListProvider =
    StateNotifierProvider<ArchiveListNotifier, ArchiveListState>((ref) {
  return ArchiveListNotifier(ref.watch(archiveRepositoryProvider));
});

/// 홈 전용 최근 아카이빙 목록 (상태 격리, 필터 없음, 8개 고정)
final recentArchiveProvider = FutureProvider<List<ArchivedContent>>((ref) async {
  final repo = ref.watch(archiveRepositoryProvider);
  final result = await repo.getArchives(page: 1, pageSize: 8);
  return result.fold((e) => throw e, (list) => list.items);
});

/// 개별 아카이브 상세 조회
final archiveDetailProvider = FutureProvider.family<ArchivedContent, String>(
  (ref, id) async {
    final repo = ref.watch(archiveRepositoryProvider);
    final result = await repo.getArchive(id);
    return result.fold((e) => throw e, (content) => content);
  },
);
