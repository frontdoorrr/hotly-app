import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/providers/language_provider.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';
import '../../data/datasources/archive_remote_datasource.dart';
import '../../data/repositories/archive_repository_impl.dart';
import '../../domain/entities/archived_content.dart';
import '../../domain/entities/content_type_info.dart';
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
  final Ref _ref;

  ArchiveInputNotifier(this._repository, this._ref) : super(const ArchiveInputState());

  Future<void> archiveUrl(String url, {bool force = false}) async {
    state = state.copyWith(isLoading: true, error: null, inputUrl: url);
    final language = _ref.read(languageCodeProvider);
    final result = await _repository.archiveUrl(url, force: force, language: language);

    result.fold(
      (error) => state = state.copyWith(isLoading: false, error: error.toString()),
      (content) {
        state = state.copyWith(isLoading: false, result: content);
        _notifyArchiveSaved(content);
      },
    );
  }

  /// 아카이브 저장 성공 시 목록/홈 프로바이더에 새 항목 반영.
  void _notifyArchiveSaved(ArchivedContent content) {
    _ref.invalidate(recentArchiveProvider);
    // 목록은 notifier가 살아있는 경우만 새로고침 (listen 하지 않음).
    Future.microtask(
      () => _ref.read(archiveListProvider.notifier).load(refresh: true),
    );
    // Place 타입은 백엔드가 주소 → 좌표 지오코딩을 background task로 실행한다.
    // 지오코딩이 끝날 시간을 주고 Map(저장된 장소) 프로바이더를 새로 고친다.
    if (content.contentType == 'place') {
      Future.delayed(const Duration(seconds: 3), () {
        try {
          _ref.read(savedPlacesProvider.notifier).refresh();
        } catch (_) {
          // 프로바이더가 아직 초기화되지 않은 경우 무시
        }
      });
    }
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
    String? selectedType,
    String? error,
  }) = _ArchiveListState;
}

class ArchiveListNotifier extends StateNotifier<ArchiveListState> {
  final ArchiveRepository _repository;
  final Ref _ref;
  static const _pageSize = 20;

  ArchiveListNotifier(this._repository, this._ref) : super(const ArchiveListState());

  Future<void> load({String? contentType, bool overrideType = false, bool refresh = false}) async {
    final targetType = overrideType ? contentType : (contentType ?? state.selectedType);
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
      (_) {
        state = state.copyWith(
          items: state.items.where((e) => e.id != id).toList(),
          total: state.total - 1,
        );
        _ref.invalidate(recentArchiveProvider);
      },
    );
  }

  void filterByType(String? type) => load(contentType: type, overrideType: true, refresh: true);
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
  return ArchiveInputNotifier(ref.watch(archiveRepositoryProvider), ref);
});

final archiveListProvider =
    StateNotifierProvider<ArchiveListNotifier, ArchiveListState>((ref) {
  return ArchiveListNotifier(ref.watch(archiveRepositoryProvider), ref);
});

/// 콘텐츠 타입 목록 (앱 세션 동안 캐시)
final contentTypesProvider = FutureProvider<List<ContentTypeInfo>>((ref) async {
  final repo = ref.watch(archiveRepositoryProvider);
  final result = await repo.getContentTypes();
  return result.fold((e) => throw e, (list) => list);
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
