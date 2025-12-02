import 'package:freezed_annotation/freezed_annotation.dart';
import '../../../link_analysis/domain/entities/link_analysis_result.dart';

part 'share_queue_item.freezed.dart';
part 'share_queue_item.g.dart';

/// Share Queue Item Status
enum ShareQueueStatus {
  /// 대기 중 - 아직 분석이 시작되지 않음
  pending,

  /// 분석 중 - AI 분석 진행 중
  analyzing,

  /// 완료 - 분석 완료
  completed,

  /// 저장됨 - 장소로 저장 완료
  saved,

  /// 실패 - 분석 실패
  failed,

  /// 무시됨 - 사용자가 무시함
  ignored,
}

/// Share Queue Item - iOS Share Extension으로 공유된 링크 항목
@freezed
class ShareQueueItem with _$ShareQueueItem {
  const factory ShareQueueItem({
    /// 고유 ID (UUID)
    required String id,

    /// 원본 URL
    required String url,

    /// 페이지 제목 (선택)
    String? title,

    /// 공유 시각
    required DateTime sharedAt,

    /// 현재 상태
    @Default(ShareQueueStatus.pending) ShareQueueStatus status,

    /// 분석 결과 (완료 시)
    ShareQueueAnalysisResult? result,

    /// 에러 메시지 (실패 시)
    String? errorMessage,

    /// 재시도 횟수
    @Default(0) int retryCount,

    /// 플랫폼 (instagram, naver_blog, youtube)
    String? platform,
  }) = _ShareQueueItem;

  factory ShareQueueItem.fromJson(Map<String, dynamic> json) =>
      _$ShareQueueItemFromJson(json);
}

/// Share Queue Analysis Result - 분석 결과 (저장용 경량 모델)
@freezed
class ShareQueueAnalysisResult with _$ShareQueueAnalysisResult {
  const factory ShareQueueAnalysisResult({
    /// 장소명
    required String placeName,

    /// 카테고리
    required String category,

    /// 주소
    String? address,

    /// 이미지 URL
    String? imageUrl,

    /// 신뢰도 점수 (0.0 ~ 1.0)
    @Default(0.0) double confidence,

    /// 태그 목록
    @Default([]) List<String> tags,

    /// 추출된 추가 정보
    Map<String, dynamic>? extractedInfo,

    /// 원본 분석 ID (서버)
    String? analysisId,
  }) = _ShareQueueAnalysisResult;

  factory ShareQueueAnalysisResult.fromJson(Map<String, dynamic> json) =>
      _$ShareQueueAnalysisResultFromJson(json);

  /// LinkAnalysisResult에서 변환
  factory ShareQueueAnalysisResult.fromLinkAnalysisResult(
    LinkAnalysisResult result,
  ) {
    final placeInfo = result.placeInfo;
    return ShareQueueAnalysisResult(
      placeName: placeInfo?.name ?? 'Unknown',
      category: placeInfo?.category ?? 'Unknown',
      address: placeInfo?.address,
      imageUrl: result.contentMetadata?.images.isNotEmpty == true
          ? result.contentMetadata!.images.first
          : null,
      confidence: result.confidence,
      tags: placeInfo?.tags ?? [],
      analysisId: result.analysisId,
    );
  }
}

/// Share Queue State - 전체 큐 상태
@freezed
class ShareQueueState with _$ShareQueueState {
  const factory ShareQueueState({
    /// 큐 항목 목록
    @Default([]) List<ShareQueueItem> items,

    /// 처리 중 여부
    @Default(false) bool isProcessing,

    /// 현재 처리 중인 인덱스
    @Default(0) int processingIndex,

    /// 에러 메시지
    String? error,

    /// 마지막 동기화 시각
    DateTime? lastSyncAt,
  }) = _ShareQueueState;

  const ShareQueueState._();

  /// 대기 중인 항목 수
  int get pendingCount =>
      items.where((item) => item.status == ShareQueueStatus.pending).length;

  /// 분석 완료된 항목 수
  int get completedCount =>
      items.where((item) => item.status == ShareQueueStatus.completed).length;

  /// 실패한 항목 수
  int get failedCount =>
      items.where((item) => item.status == ShareQueueStatus.failed).length;

  /// 처리 가능한 항목 (pending + failed with retry < 3)
  List<ShareQueueItem> get processableItems => items
      .where(
        (item) =>
            item.status == ShareQueueStatus.pending ||
            (item.status == ShareQueueStatus.failed && item.retryCount < 3),
      )
      .toList();

  /// 신뢰도 높은 결과만 필터링 (70% 이상)
  List<ShareQueueItem> get highConfidenceItems => items
      .where(
        (item) =>
            item.status == ShareQueueStatus.completed &&
            item.result != null &&
            item.result!.confidence >= 0.7,
      )
      .toList();

  /// 전체 진행률 (0.0 ~ 1.0)
  double get progress {
    if (items.isEmpty) return 0.0;
    final totalToProcess = items
        .where(
          (item) =>
              item.status != ShareQueueStatus.saved &&
              item.status != ShareQueueStatus.ignored,
        )
        .length;
    if (totalToProcess == 0) return 1.0;
    return processingIndex / totalToProcess;
  }
}
