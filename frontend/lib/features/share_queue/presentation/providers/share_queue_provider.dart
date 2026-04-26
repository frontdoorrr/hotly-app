import 'dart:async';
import 'package:dartz/dartz.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';
import '../../../archive/data/datasources/archive_remote_datasource.dart';
import '../../../archive/data/repositories/archive_repository_impl.dart';
import '../../../archive/data/services/instagram_media_extractor.dart';
import '../../../archive/domain/entities/archived_content.dart';
import '../../../archive/domain/repositories/archive_repository.dart';
import '../../../archive/presentation/providers/archive_provider.dart';
import '../../../saved/presentation/providers/saved_places_provider.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../core/notifications/fcm_service.dart';
import '../../../../core/providers/language_provider.dart';
import '../../data/services/share_queue_storage_service.dart';
import '../../domain/entities/share_queue_item.dart';

/// URL 추가 결과
enum AddUrlResult { added, duplicate, queueFull, unsupported }

/// ShareQueue Storage Service Provider
final shareQueueStorageServiceProvider =
    Provider<ShareQueueStorageService>((ref) {
  return ShareQueueStorageService();
});

/// ShareQueue State Notifier
///
/// 공유된 링크 큐의 상태를 관리합니다.
/// - 큐 로드/저장
/// - 일괄 분석 처리
/// - 항목 상태 관리
class ShareQueueNotifier extends StateNotifier<ShareQueueState> {
  final ShareQueueStorageService _storageService;
  final ArchiveRepository _archiveRepository;
  final Ref _ref;
  final Logger _logger = Logger();

  bool _isDisposed = false;
  Timer? _saveDebounceTimer;

  ShareQueueNotifier(
    this._storageService,
    this._archiveRepository,
    this._ref,
  ) : super(const ShareQueueState()) {
    _loadQueue();
  }

  @override
  void dispose() {
    _isDisposed = true;
    _saveDebounceTimer?.cancel();
    super.dispose();
  }

  /// 큐 로드
  Future<void> _loadQueue() async {
    try {
      final items = await _storageService.loadQueue();
      if (!_isDisposed) {
        // 앱 강제종료로 analyzing 상태에 stuck된 항목을 pending으로 복구
        final stuckItems = items.where((i) => i.status == ShareQueueStatus.analyzing).toList();
        final List<ShareQueueItem> recovered;
        if (stuckItems.isNotEmpty) {
          _logger.i('ShareQueue: Recovering ${stuckItems.length} stuck analyzing items');
          recovered = items.map((item) => item.status == ShareQueueStatus.analyzing
              ? item.copyWith(status: ShareQueueStatus.pending, errorMessage: null)
              : item).toList();
          await _storageService.saveQueue(recovered);
        } else {
          recovered = items;
        }

        state = state.copyWith(
          items: recovered,
          lastSyncAt: DateTime.now(),
        );
      }
    } catch (e) {
      _logger.e('ShareQueue: Failed to load queue: $e');
      if (!_isDisposed) {
        state = state.copyWith(error: e.toString());
      }
    }
  }

  /// 큐 새로고침
  Future<void> refreshQueue() async {
    await _loadQueue();
  }

  /// 새 URL 추가
  Future<AddUrlResult> addUrl(String url, {String? title}) async {
    if (!ShareQueueStorageService.isSupportedUrl(url)) {
      state = state.copyWith(error: '지원하지 않는 플랫폼입니다');
      return AddUrlResult.unsupported;
    }

    if (state.items.any((item) => item.url == url)) {
      return AddUrlResult.duplicate;
    }

    if (state.items.length >= 20) {
      state = state.copyWith(error: '큐가 가득 찼습니다 (최대 20개)');
      return AddUrlResult.queueFull;
    }

    final newItem = await _storageService.addItem(url: url, title: title);

    if (newItem == null) {
      state = state.copyWith(error: '링크 추가에 실패했습니다');
      return AddUrlResult.queueFull;
    }

    state = state.copyWith(items: [...state.items, newItem], error: null);
    _logger.i('ShareQueue: URL added to queue — ${newItem.url} (id: ${newItem.id})');
    return AddUrlResult.added;
  }

  /// 일괄 분석 시작
  ///
  /// 대기 중인 모든 항목을 순차적으로 분석합니다.
  /// 품질 우선을 위해 각 분석 사이에 500ms 딜레이를 둡니다.
  Future<void> processBatch() async {
    if (state.isProcessing) {
      _logger.w('ShareQueue: Already processing');
      return;
    }

    // 새 배치 시작 전 이전 세션 종료 항목 정리
    // (completed, saved, ignored, 재시도 소진 failed)
    final activeItems = state.items
        .where((item) =>
            item.status == ShareQueueStatus.pending ||
            item.status == ShareQueueStatus.analyzing ||
            (item.status == ShareQueueStatus.failed && item.retryCount < 3))
        .toList();
    if (activeItems.length != state.items.length) {
      _logger.i(
          'ShareQueue: Cleaned ${state.items.length - activeItems.length} stale items before batch');
      state = state.copyWith(items: activeItems);
      await _storageService.saveQueue(activeItems);
    }

    final processableItems = state.processableItems;
    if (processableItems.isEmpty) {
      _logger.i('ShareQueue: No items to process');
      return;
    }

    // 이번 배치 ID를 미리 캡처해 완료 카운팅에 사용
    final batchIds = processableItems.map((i) => i.id).toSet();

    state = state.copyWith(
      isProcessing: true,
      processingIndex: 0,
      error: null,
    );

    _logger.i('ShareQueue: Starting batch processing of ${processableItems.length} items');

    for (var i = 0; i < processableItems.length; i++) {
      if (_isDisposed || !state.isProcessing) {
        _logger.i('ShareQueue: Processing cancelled');
        break;
      }

      state = state.copyWith(processingIndex: i);
      await _analyzeItem(processableItems[i]);

      // 품질 우선: 각 분석 사이에 딜레이
      if (i < processableItems.length - 1) {
        await Future.delayed(const Duration(milliseconds: 500));
      }
    }

    // 이번 배치에서 새로 완료된 항목만 카운트
    final completedCount = state.items
        .where((item) =>
            batchIds.contains(item.id) &&
            item.status == ShareQueueStatus.completed)
        .length;

    state = state.copyWith(
      isProcessing: false,
      processingIndex: 0,
    );

    _logger.i('ShareQueue: Batch processing completed');

    // 앱이 백그라운드(paused/hidden/detached) 상태일 때만 로컬 알림 발송
    final lc = WidgetsBinding.instance.lifecycleState;
    final isBackgrounded = lc == AppLifecycleState.paused ||
        lc == AppLifecycleState.hidden ||
        lc == AppLifecycleState.detached;
    if (completedCount > 0 && isBackgrounded) {
      await FCMService().showLocalNotification(
        id: 1001,
        title: '분석 완료',
        body: '$completedCount개 장소 분석이 완료됐어요. 확인해보세요!',
        payload: 'type=share_queue',
      );
    }
  }

  /// 단일 항목 분석 (archive API — 동기 응답, 폴링 불필요)
  Future<void> _analyzeItem(ShareQueueItem item) async {
    _logger.i('ShareQueue: Analysis started — ${item.url} (platform: ${item.platform ?? 'unknown'})');
    _updateItemStatus(item.id, ShareQueueStatus.analyzing);

    try {
      final Either<Exception, ArchivedContent> result;

      final language = _ref.read(languageCodeProvider);
      if (item.platform == 'instagram') {
        result = await _analyzeInstagram(item, language: language);
      } else {
        result = await _archiveRepository.archiveUrl(item.url, language: language);
      }

      result.fold(
        (error) => _updateItemError(item.id, error.toString()),
        (content) {
          _updateItemWithResult(
            item.id,
            ShareQueueAnalysisResult.fromArchivedContent(content),
          );
          // Share Queue 분석이 곧 아카이브 저장이므로, 목록/홈도 함께 갱신.
          _ref.invalidate(recentArchiveProvider);
          Future.microtask(
            () => _ref.read(archiveListProvider.notifier).load(refresh: true),
          );
          // Place 타입은 백엔드 지오코딩 완료 후 Map의 저장된 장소 목록을 새로 고침.
          if (content.contentType == 'place') {
            Future.delayed(const Duration(seconds: 3), () {
              try {
                _ref.read(savedPlacesProvider.notifier).refresh();
              } catch (_) {
                // 프로바이더가 아직 초기화되지 않은 경우 무시
              }
            });
          }
        },
      );
    } catch (e) {
      _logger.e('ShareQueue: Analysis error for ${item.id}: $e');
      _updateItemError(item.id, e.toString());
    }
  }

  Future<Either<Exception, ArchivedContent>> _analyzeInstagram(
      ShareQueueItem item, {String language = 'ko'}) async {
    try {
      final extractor = InstagramMediaExtractor();
      final extracted = await extractor.extract(item.url);

      // 캐러셀 추출 가시성 — 운영 모니터링용
      _logger.i(
        'ShareQueue: Instagram extracted ${extracted.mediaFiles.length} media '
        '(sidecar: ${extracted.fromSidecar}) for ${item.id}',
      );
      // img_index가 붙어있는데 1장만 추출된 경우 = 캐러셀이지만 sidecar 파싱 실패 의심
      final hasImgIndex =
          Uri.tryParse(item.url)?.queryParameters['img_index'] != null;
      if (hasImgIndex && extracted.mediaFiles.length <= 1) {
        _logger.w(
          'ShareQueue: Suspected carousel parsed as single media — '
          'url=${item.url}, count=${extracted.mediaFiles.length}, '
          'sidecar=${extracted.fromSidecar}',
        );
      }

      return _archiveRepository.archiveInstagram(
        url: item.url,
        mediaFiles: extracted.mediaFiles,
        caption: extracted.caption,
        author: extracted.author,
        language: language,
      );
    } on InstagramBlockedError catch (e, st) {
      _logger.w('ShareQueue: Instagram blocked for ${item.id}', error: e, stackTrace: st);
      return Left(Exception('error_instagramBlocked'));
    } on InstagramParseError catch (e, st) {
      _logger.w('ShareQueue: Instagram parse error for ${item.id}', error: e, stackTrace: st);
      return Left(Exception('error_instagramParseError'));
    } on InstagramMediaDownloadError catch (e, st) {
      _logger.w('ShareQueue: Instagram download error for ${item.id}', error: e, stackTrace: st);
      return Left(Exception('error_instagramDownloadError'));
    } on Exception catch (e) {
      return Left(e);
    }
  }

  /// 항목 상태 업데이트
  void _updateItemStatus(String id, ShareQueueStatus status) {
    final items = state.items.map((item) {
      if (item.id == id) {
        return item.copyWith(status: status);
      }
      return item;
    }).toList();

    state = state.copyWith(items: items);
    _scheduleSave();
  }

  /// 항목에 결과 추가
  void _updateItemWithResult(String id, ShareQueueAnalysisResult result) {
    final items = state.items.map((item) {
      if (item.id == id) {
        return item.copyWith(
          status: ShareQueueStatus.completed,
          result: result,
          errorMessage: null,
        );
      }
      return item;
    }).toList();

    state = state.copyWith(items: items);
    _scheduleSave();
  }

  /// 항목에 에러 추가
  void _updateItemError(String id, String error) {
    final items = state.items.map((item) {
      if (item.id == id) {
        return item.copyWith(
          status: ShareQueueStatus.failed,
          errorMessage: error,
          retryCount: item.retryCount + 1,
        );
      }
      return item;
    }).toList();

    state = state.copyWith(items: items);
    _scheduleSave();
  }

  /// 실패한 항목만 재시도
  Future<void> retryFailed() async {
    final failedItems = state.items
        .where(
          (item) =>
              item.status == ShareQueueStatus.failed && item.retryCount < 3,
        )
        .toList();

    if (failedItems.isEmpty) {
      _logger.i('ShareQueue: No failed items to retry');
      return;
    }

    // 실패한 항목들을 pending으로 변경
    for (final item in failedItems) {
      _updateItemStatus(item.id, ShareQueueStatus.pending);
    }

    // 일괄 분석 시작
    await processBatch();
  }

  /// 항목 저장 (archive에서 completed 상태로 전환)
  Future<bool> saveItem(String id) async {
    final item = state.items.firstWhere(
      (item) => item.id == id,
      orElse: () => throw Exception('Item not found'),
    );

    if (item.result == null) {
      state = state.copyWith(error: '저장할 분석 결과가 없습니다');
      return false;
    }

    // archive API는 archiveUrl 시점에 이미 저장 완료 — 큐에서 즉시 제거
    await removeItem(id);
    return true;
  }

  /// 선택된 항목들 일괄 저장
  Future<int> saveSelectedItems(List<String> ids) async {
    var savedCount = 0;

    for (final id in ids) {
      final success = await saveItem(id);
      if (success) savedCount++;
    }

    return savedCount;
  }

  /// 항목 무시 — 큐에서 즉시 제거
  Future<void> ignoreItem(String id) async {
    await removeItem(id);
  }

  /// 항목 삭제
  Future<void> removeItem(String id) async {
    final items = state.items.where((item) => item.id != id).toList();
    state = state.copyWith(items: items);
    await _storageService.removeItem(id);
  }

  /// 전체 큐 삭제
  Future<void> clearQueue() async {
    state = const ShareQueueState();
    await _storageService.clearQueue();
  }

  /// 완료된 항목 정리
  Future<void> cleanupCompleted() async {
    await _storageService.cleanupCompletedItems();
    await _loadQueue();
  }

  /// 처리 취소
  void cancelProcessing() {
    if (state.isProcessing) {
      state = state.copyWith(isProcessing: false);
      _logger.i('ShareQueue: Processing cancelled by user');
    }
  }

  /// 에러 초기화
  void clearError() {
    state = state.copyWith(error: null);
  }

  /// 큐 저장 (내부) — debounce 500ms로 배치 처리 중 반복 I/O 방지
  void _scheduleSave() {
    _saveDebounceTimer?.cancel();
    _saveDebounceTimer = Timer(const Duration(milliseconds: 500), _saveQueue);
  }

  Future<void> _saveQueue() async {
    try {
      await _storageService.saveQueue(state.items);
    } catch (e) {
      _logger.e('ShareQueue: Failed to save queue: $e');
    }
  }
}

/// ShareQueue Provider
final shareQueueProvider =
    StateNotifierProvider<ShareQueueNotifier, ShareQueueState>((ref) {
  final storageService = ref.watch(shareQueueStorageServiceProvider);
  final dioClient = ref.watch(dioClientProvider);
  final repository = ArchiveRepositoryImpl(
    ArchiveRemoteDataSource(dioClient.dio),
  );

  return ShareQueueNotifier(storageService, repository, ref);
});

/// 대기 중인 항목 수 Provider (UI 배지용)
final pendingQueueCountProvider = Provider<int>((ref) {
  final state = ref.watch(shareQueueProvider);
  return state.pendingCount;
});

/// 처리 중 여부 Provider
final isProcessingQueueProvider = Provider<bool>((ref) {
  final state = ref.watch(shareQueueProvider);
  return state.isProcessing;
});
