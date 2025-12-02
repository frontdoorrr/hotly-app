import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:logger/logger.dart';
import '../../../../core/network/dio_client.dart';
import '../../../link_analysis/data/datasources/link_analysis_remote_datasource.dart';
import '../../../link_analysis/data/repositories/link_analysis_repository_impl.dart';
import '../../../link_analysis/domain/entities/link_analysis_result.dart';
import '../../../link_analysis/domain/repositories/link_analysis_repository.dart';
import '../../data/services/share_queue_storage_service.dart';
import '../../domain/entities/share_queue_item.dart';

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
  final LinkAnalysisRepository _analysisRepository;
  final Logger _logger = Logger();

  bool _isDisposed = false;

  ShareQueueNotifier(
    this._storageService,
    this._analysisRepository,
  ) : super(const ShareQueueState()) {
    _loadQueue();
  }

  @override
  void dispose() {
    _isDisposed = true;
    super.dispose();
  }

  /// 큐 로드
  Future<void> _loadQueue() async {
    try {
      final items = await _storageService.loadQueue();
      if (!_isDisposed) {
        state = state.copyWith(
          items: items,
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
  Future<bool> addUrl(String url, {String? title}) async {
    // URL 유효성 검사
    if (!ShareQueueStorageService.isSupportedUrl(url)) {
      state = state.copyWith(error: '지원하지 않는 플랫폼입니다');
      return false;
    }

    final newItem = await _storageService.addItem(
      url: url,
      title: title,
    );

    if (newItem == null) {
      state = state.copyWith(error: '링크 추가에 실패했습니다. 이미 추가된 링크이거나 큐가 가득 찼습니다.');
      return false;
    }

    state = state.copyWith(
      items: [...state.items, newItem],
      error: null,
    );

    return true;
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

    final processableItems = state.processableItems;
    if (processableItems.isEmpty) {
      _logger.i('ShareQueue: No items to process');
      return;
    }

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

    state = state.copyWith(
      isProcessing: false,
      processingIndex: 0,
    );

    _logger.i('ShareQueue: Batch processing completed');
  }

  /// 단일 항목 분석
  Future<void> _analyzeItem(ShareQueueItem item) async {
    // 상태: analyzing
    _updateItemStatus(item.id, ShareQueueStatus.analyzing);

    try {
      // API 호출
      final result = await _analysisRepository.analyzeLink(url: item.url);

      result.fold(
        (error) {
          // 실패: failed
          _updateItemError(item.id, error.toString());
        },
        (analysisResult) {
          if (analysisResult.status == AnalysisStatus.completed &&
              analysisResult.placeInfo != null) {
            // 성공: completed
            _updateItemWithResult(
              item.id,
              ShareQueueAnalysisResult.fromLinkAnalysisResult(analysisResult),
            );
          } else if (analysisResult.status == AnalysisStatus.failed) {
            // 분석 실패
            _updateItemError(item.id, analysisResult.error ?? '분석에 실패했습니다');
          } else if (analysisResult.status == AnalysisStatus.inProgress) {
            // 진행 중이면 폴링 시작
            _pollForResult(item.id, analysisResult.analysisId);
          } else {
            // 기타 실패
            _updateItemError(item.id, '장소 정보를 추출할 수 없습니다');
          }
        },
      );
    } catch (e) {
      _logger.e('ShareQueue: Analysis error for ${item.id}: $e');
      _updateItemError(item.id, e.toString());
    }
  }

  /// 분석 결과 폴링
  Future<void> _pollForResult(String itemId, String analysisId) async {
    const maxPolls = 30;
    const pollInterval = Duration(seconds: 2);

    for (var i = 0; i < maxPolls; i++) {
      if (_isDisposed) return;

      await Future.delayed(pollInterval);

      final result = await _analysisRepository.getAnalysisStatus(analysisId);

      result.fold(
        (error) {
          _updateItemError(itemId, error.toString());
          return;
        },
        (analysisResult) {
          if (analysisResult.status == AnalysisStatus.completed &&
              analysisResult.placeInfo != null) {
            _updateItemWithResult(
              itemId,
              ShareQueueAnalysisResult.fromLinkAnalysisResult(analysisResult),
            );
            return;
          } else if (analysisResult.status == AnalysisStatus.failed) {
            _updateItemError(itemId, analysisResult.error ?? '분석에 실패했습니다');
            return;
          }
        },
      );
    }

    // 타임아웃
    _updateItemError(itemId, '분석 시간 초과');
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
    _saveQueue();
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
    _saveQueue();
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
    _saveQueue();
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

  /// 항목 저장 (장소로)
  Future<bool> saveItem(String id) async {
    final item = state.items.firstWhere(
      (item) => item.id == id,
      orElse: () => throw Exception('Item not found'),
    );

    if (item.result?.analysisId == null) {
      state = state.copyWith(error: '저장할 분석 결과가 없습니다');
      return false;
    }

    try {
      final result = await _analysisRepository.saveAnalyzedPlace(
        item.result!.analysisId!,
        sourceUrl: item.url,
      );

      return result.fold(
        (error) {
          state = state.copyWith(error: '저장 실패: ${error.toString()}');
          return false;
        },
        (place) {
          _updateItemStatus(id, ShareQueueStatus.saved);
          return true;
        },
      );
    } catch (e) {
      state = state.copyWith(error: '저장 실패: $e');
      return false;
    }
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

  /// 항목 무시
  void ignoreItem(String id) {
    _updateItemStatus(id, ShareQueueStatus.ignored);
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

  /// 큐 저장 (내부)
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
  final dio = dioClient.dio;
  final remoteDataSource = LinkAnalysisRemoteDataSource(dio);
  final repository = LinkAnalysisRepositoryImpl(remoteDataSource);

  return ShareQueueNotifier(storageService, repository);
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
