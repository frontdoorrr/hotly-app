# TRD: iOS 공유 큐 시스템 - 일괄 분석 아키텍처

## 1. 시스템 개요

### 1-1. 아키텍처 구조
```
┌─────────────────────────────────────────────────────────────┐
│                     External Apps                            │
│            (Instagram, Blog, YouTube)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ iOS Share Sheet
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 iOS Share Extension                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ URL Extractor│  │ Domain Filter│  │ Queue Writer │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                   ┌────────────────┐                        │
│                   │  App Groups    │                        │
│                   │  UserDefaults  │                        │
│                   └────────┬───────┘                        │
└────────────────────────────┼────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Main App                          │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │          Presentation Layer                  │           │
│  │  ┌──────────────┐  ┌──────────────┐         │           │
│  │  │ Queue Badge  │  │ Processing   │         │           │
│  │  │ Widget       │  │ Sheet        │         │           │
│  │  └──────┬───────┘  └──────┬───────┘         │           │
│  │         │                  │                  │           │
│  │         └──────────┬───────┘                  │           │
│  │                    │                          │           │
│  │         ┌──────────▼───────────┐              │           │
│  │         │ Results Review Screen│              │           │
│  │         └──────────────────────┘              │           │
│  └────────────────┬──────────────────────────────┘           │
│                   │                                          │
│  ┌────────────────▼──────────────────────────────┐           │
│  │          State Management (Riverpod)          │           │
│  │  ┌──────────────────────────────────────┐    │           │
│  │  │    ShareQueueNotifier                │    │           │
│  │  │  ┌────────────┐  ┌────────────┐     │    │           │
│  │  │  │ Queue      │  │ Batch      │     │    │           │
│  │  │  │ Manager    │  │ Processor  │     │    │           │
│  │  │  └─────┬──────┘  └─────┬──────┘     │    │           │
│  │  │        │                │            │    │           │
│  │  │        └────────┬───────┘            │    │           │
│  │  │                 │                    │    │           │
│  │  └─────────────────┼────────────────────┘    │           │
│  └────────────────────┼─────────────────────────┘           │
│                       │                                      │
│  ┌────────────────────▼─────────────────────────┐           │
│  │          Data Layer                          │           │
│  │  ┌──────────────┐  ┌──────────────┐         │           │
│  │  │ Local        │  │ Remote       │         │           │
│  │  │ Storage      │  │ Data Source  │         │           │
│  │  │(SharedPrefs) │  │(Link Analysis│         │           │
│  │  └──────┬───────┘  └──────┬───────┘         │           │
│  │         │                  │                  │           │
│  └─────────┼──────────────────┼──────────────────┘           │
└────────────┼──────────────────┼───────────────────────────────┘
             │                  │
             │                  ▼
             │         ┌─────────────────┐
             │         │  FastAPI Backend│
             │         │  ┌────────────┐ │
             │         │  │ Link       │ │
             │         │  │ Analysis   │ │
             │         │  │ Service    │ │
             │         │  └─────┬──────┘ │
             │         │        │        │
             │         │        ▼        │
             │         │  ┌────────────┐ │
             │         │  │ Gemini AI  │ │
             │         │  │ Analysis   │ │
             │         │  └────────────┘ │
             │         └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ SQLite Database │
    │ (Local Queue)   │
    └─────────────────┘
```

### 1-2. 기술 스택
```yaml
iOS Share Extension:
  Language: Swift 5.9+
  Framework: UIKit
  Min iOS: 14.0+
  Data Sharing: App Groups
  Storage: UserDefaults (Shared)
  Max Memory: 30MB

Flutter App:
  Framework: Flutter 3.16+
  State Management: Riverpod 2.4+
  Packages:
    - receive_sharing_intent: ^1.5.1
    - shared_preferences: ^2.2.2
    - freezed: ^2.4.6
    - freezed_annotation: ^2.4.1
    - json_annotation: ^4.8.1
  Storage: SharedPreferences + SQLite

Backend:
  Runtime: Python 3.11+
  Framework: FastAPI
  AI: Google Gemini API
  Endpoints:
    - POST /api/v1/link-analysis/analyze (기존 활용)

Security:
  Data: App Groups Sandboxing
  Network: HTTPS/TLS 1.3
  Token: Firebase ID Token
```

---

## 2. iOS Share Extension 구현

### 2-1. Xcode 프로젝트 설정

#### Step 1: Share Extension Target 추가
```bash
# Xcode에서
1. File > New > Target
2. iOS > Share Extension 선택
3. Product Name: ShareExtension
4. Language: Swift
5. Bundle Identifier: com.hotly.app.ShareExtension
6. Embed In Application: Runner
```

#### Step 2: App Groups 설정
```bash
# 1. Apple Developer Console
- Certificates, Identifiers & Profiles
- App Groups 생성: group.com.hotly.sharequeue

# 2. Main App (Runner) Capabilities
- Signing & Capabilities 탭
- + Capability > App Groups
- ✅ group.com.hotly.sharequeue

# 3. Share Extension Capabilities
- Share Extension target 선택
- Signing & Capabilities 탭
- + Capability > App Groups
- ✅ group.com.hotly.sharequeue
```

### 2-2. Info.plist 설정

#### ShareExtension/Info.plist
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSExtension</key>
    <dict>
        <key>NSExtensionAttributes</key>
        <dict>
            <key>NSExtensionActivationRule</key>
            <dict>
                <!-- URL 공유 지원 -->
                <key>NSExtensionActivationSupportsWebURLWithMaxCount</key>
                <integer>5</integer>

                <!-- 웹페이지 공유 지원 -->
                <key>NSExtensionActivationSupportsWebPageWithMaxCount</key>
                <integer>5</integer>
            </dict>
        </dict>

        <key>NSExtensionMainStoryboard</key>
        <string>MainInterface</string>

        <key>NSExtensionPointIdentifier</key>
        <string>com.apple.share-services</string>
    </dict>
</dict>
</plist>
```

### 2-3. ShareViewController.swift 구현

#### 전체 코드
```swift
import UIKit
import Social
import MobileCoreServices

class ShareViewController: SLComposeServiceViewController {

    // App Group 식별자
    private let appGroupId = "group.com.hotly.sharequeue"

    // 지원하는 도메인
    private let allowedDomains = [
        "instagram.com",
        "blog.naver.com",
        "youtube.com",
        "youtu.be"
    ]

    override func viewDidLoad() {
        super.viewDidLoad()

        // UI 커스터마이징
        self.title = "Hotly에 추가"
        self.placeholder = "이 장소에 대한 메모 (선택사항)"

        // 공유 항목 처리
        handleSharedContent()
    }

    private func handleSharedContent() {
        guard let extensionItem = extensionContext?.inputItems.first as? NSExtensionItem,
              let itemProviders = extensionItem.attachments else {
            closeWithError("공유할 항목을 찾을 수 없습니다")
            return
        }

        // URL 추출
        for provider in itemProviders {
            if provider.hasItemConformingToTypeIdentifier(kUTTypeURL as String) {
                provider.loadItem(forTypeIdentifier: kUTTypeURL as String, options: nil) { [weak self] (item, error) in
                    guard let self = self,
                          let url = item as? URL else { return }

                    DispatchQueue.main.async {
                        self.processURL(url)
                    }
                }
                break
            } else if provider.hasItemConformingToTypeIdentifier(kUTTypePropertyList as String) {
                provider.loadItem(forTypeIdentifier: kUTTypePropertyList as String, options: nil) { [weak self] (item, error) in
                    guard let self = self,
                          let dictionary = item as? [String: Any],
                          let results = dictionary[NSExtensionJavaScriptPreprocessingResultsKey] as? [String: Any],
                          let urlString = results["URL"] as? String,
                          let url = URL(string: urlString) else { return }

                    DispatchQueue.main.async {
                        self.processURL(url)
                    }
                }
                break
            }
        }
    }

    private func processURL(_ url: URL) {
        // 도메인 검증
        guard isAllowedDomain(url) else {
            closeWithError("지원하지 않는 플랫폼입니다\n(Instagram, 네이버 블로그, YouTube만 지원)")
            return
        }

        // 큐에 추가
        addToQueue(url: url)
    }

    private func isAllowedDomain(_ url: URL) -> Bool {
        guard let host = url.host?.lowercased() else { return false }
        return allowedDomains.contains { host.contains($0) }
    }

    private func addToQueue(url: URL) {
        guard let userDefaults = UserDefaults(suiteName: appGroupId) else {
            closeWithError("데이터 저장 실패")
            return
        }

        // 기존 큐 로드
        var queue = loadQueue(from: userDefaults)

        // 중복 체크
        if queue.contains(where: { $0["url"] as? String == url.absoluteString }) {
            closeWithSuccess("이미 추가된 링크입니다")
            return
        }

        // 큐 크기 제한 (최대 20개)
        if queue.count >= 20 {
            closeWithError("큐가 가득 찼습니다\n앱에서 먼저 분석해주세요")
            return
        }

        // 새 항목 추가
        let newItem: [String: Any] = [
            "id": UUID().uuidString,
            "url": url.absoluteString,
            "title": contentText ?? "",
            "sharedAt": ISO8601DateFormatter().string(from: Date()),
            "status": "pending"
        ]

        queue.append(newItem)

        // 저장
        userDefaults.set(queue, forKey: "share_queue")
        userDefaults.synchronize()

        // 성공 메시지
        closeWithSuccess("\(queue.count)개 링크 추가됨")
    }

    private func loadQueue(from userDefaults: UserDefaults) -> [[String: Any]] {
        guard let data = userDefaults.array(forKey: "share_queue") as? [[String: Any]] else {
            return []
        }
        return data
    }

    private func closeWithSuccess(_ message: String) {
        // 토스트 메시지 표시 (간단한 alert)
        let alert = UIAlertController(title: "✅ 완료", message: message, preferredStyle: .alert)
        present(alert, animated: true)

        // 0.5초 후 자동 닫기
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { [weak self] in
            self?.extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
        }
    }

    private func closeWithError(_ message: String) {
        let alert = UIAlertController(title: "⚠️ 오류", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "확인", style: .default) { [weak self] _ in
            self?.extensionContext?.cancelRequest(withError: NSError(domain: "ShareExtension", code: -1))
        })
        present(alert, animated: true)
    }

    override func isContentValid() -> Bool {
        // 항상 true (URL 검증은 processURL에서)
        return true
    }

    override func didSelectPost() {
        // 이미 handleSharedContent에서 처리됨
        extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
    }

    override func configurationItems() -> [Any]! {
        // 추가 설정 항목 (필요시)
        return []
    }
}
```

### 2-4. 빌드 설정

#### Podfile 수정
```ruby
target 'ShareExtension' do
  use_frameworks!

  # Share Extension은 최소한의 의존성만
  # UserDefaults만 사용하므로 추가 pod 불필요
end
```

---

## 3. Flutter App 구현

### 3-1. 패키지 설치

#### pubspec.yaml
```yaml
dependencies:
  flutter:
    sdk: flutter

  # State Management
  flutter_riverpod: ^2.4.9

  # Share Intent
  receive_sharing_intent: ^1.5.1

  # Local Storage
  shared_preferences: ^2.2.2

  # Code Generation
  freezed_annotation: ^2.4.1
  json_annotation: ^4.8.1

  # Utilities
  uuid: ^4.3.3

dev_dependencies:
  # Code Generators
  freezed: ^2.4.6
  json_serializable: ^6.7.1
  build_runner: ^2.4.7
```

### 3-2. 데이터 모델

#### models/share_queue_item.dart
```dart
import 'package:freezed_annotation/freezed_annotation.dart';

part 'share_queue_item.freezed.dart';
part 'share_queue_item.g.dart';

enum ShareQueueStatus {
  pending,
  analyzing,
  completed,
  saved,
  failed,
  ignored,
}

@freezed
class ShareQueueItem with _$ShareQueueItem {
  const factory ShareQueueItem({
    required String id,
    required String url,
    String? title,
    required DateTime sharedAt,
    @Default(ShareQueueStatus.pending) ShareQueueStatus status,
    PlaceAnalysisResult? result,
    String? errorMessage,
    @Default(0) int retryCount,
  }) = _ShareQueueItem;

  factory ShareQueueItem.fromJson(Map<String, dynamic> json) =>
      _$ShareQueueItemFromJson(json);
}

@freezed
class PlaceAnalysisResult with _$PlaceAnalysisResult {
  const factory PlaceAnalysisResult({
    required String placeName,
    required String category,
    String? address,
    String? imageUrl,
    @Default(0.0) double confidence,
    Map<String, dynamic>? extractedInfo,
  }) = _PlaceAnalysisResult;

  factory PlaceAnalysisResult.fromJson(Map<String, dynamic> json) =>
      _$PlaceAnalysisResultFromJson(json);
}
```

### 3-3. State Management

#### providers/share_queue_provider.dart
```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import '../models/share_queue_item.dart';
import '../services/share_queue_service.dart';
import '../services/link_analysis_service.dart';

part 'share_queue_provider.freezed.dart';

@freezed
class ShareQueueState with _$ShareQueueState {
  const factory ShareQueueState({
    @Default([]) List<ShareQueueItem> items,
    @Default(false) bool isProcessing,
    @Default(0) int processingIndex,
    String? error,
  }) = _ShareQueueState;
}

class ShareQueueNotifier extends StateNotifier<ShareQueueState> {
  ShareQueueNotifier(this._service, this._analysisService, this._ref)
      : super(const ShareQueueState()) {
    _loadQueue();
  }

  final ShareQueueService _service;
  final LinkAnalysisService _analysisService;
  final Ref _ref;

  // 큐 로드
  Future<void> _loadQueue() async {
    try {
      final items = await _service.loadQueue();
      state = state.copyWith(items: items);
    } catch (e) {
      state = state.copyWith(error: e.toString());
    }
  }

  // 새 URL 추가
  Future<void> addUrl(String url, {String? title}) async {
    final newItem = ShareQueueItem(
      id: const Uuid().v4(),
      url: url,
      title: title,
      sharedAt: DateTime.now(),
    );

    state = state.copyWith(
      items: [...state.items, newItem],
    );

    await _service.saveQueue(state.items);
  }

  // 일괄 분석 시작
  Future<void> processBatch() async {
    if (state.isProcessing) return;

    state = state.copyWith(isProcessing: true);

    final pendingItems = state.items
        .where((item) => item.status == ShareQueueStatus.pending)
        .toList();

    for (var i = 0; i < pendingItems.length; i++) {
      state = state.copyWith(processingIndex: i);

      await _analyzeItem(pendingItems[i]);

      // 품질 우선: 각 분석 대기
      await Future.delayed(const Duration(milliseconds: 500));
    }

    state = state.copyWith(
      isProcessing: false,
      processingIndex: 0,
    );
  }

  Future<void> _analyzeItem(ShareQueueItem item) async {
    // 상태: analyzing
    _updateItemStatus(item.id, ShareQueueStatus.analyzing);

    try {
      // API 호출
      final result = await _analysisService.analyzeLink(item.url);

      // 성공: completed
      _updateItemWithResult(item.id, result);
    } catch (e) {
      // 실패: failed
      _updateItemError(item.id, e.toString());
    }

    await _service.saveQueue(state.items);
  }

  void _updateItemStatus(String id, ShareQueueStatus status) {
    state = state.copyWith(
      items: state.items
          .map((item) => item.id == id ? item.copyWith(status: status) : item)
          .toList(),
    );
  }

  void _updateItemWithResult(String id, PlaceAnalysisResult result) {
    state = state.copyWith(
      items: state.items
          .map((item) => item.id == id
              ? item.copyWith(
                  status: ShareQueueStatus.completed,
                  result: result,
                  errorMessage: null,
                )
              : item)
          .toList(),
    );
  }

  void _updateItemError(String id, String error) {
    state = state.copyWith(
      items: state.items
          .map((item) => item.id == id
              ? item.copyWith(
                  status: ShareQueueStatus.failed,
                  errorMessage: error,
                  retryCount: item.retryCount + 1,
                )
              : item)
          .toList(),
    );
  }

  // 재시도
  Future<void> retryFailed() async {
    final failedItems = state.items
        .where((item) =>
            item.status == ShareQueueStatus.failed && item.retryCount < 3)
        .toList();

    for (final item in failedItems) {
      await _analyzeItem(item);
    }
  }

  // 저장
  Future<void> saveItem(String id) async {
    _updateItemStatus(id, ShareQueueStatus.saved);
    await _service.saveQueue(state.items);
  }

  // 무시
  Future<void> ignoreItem(String id) async {
    _updateItemStatus(id, ShareQueueStatus.ignored);
    await _service.saveQueue(state.items);
  }

  // 삭제
  Future<void> removeItem(String id) async {
    state = state.copyWith(
      items: state.items.where((item) => item.id != id).toList(),
    );
    await _service.saveQueue(state.items);
  }

  // 전체 삭제
  Future<void> clearQueue() async {
    state = const ShareQueueState();
    await _service.clearQueue();
  }
}

final shareQueueProvider =
    StateNotifierProvider<ShareQueueNotifier, ShareQueueState>((ref) {
  final service = ref.watch(shareQueueServiceProvider);
  final analysisService = ref.watch(linkAnalysisServiceProvider);
  return ShareQueueNotifier(service, analysisService, ref);
});
```

### 3-4. Local Storage Service

#### services/share_queue_service.dart
```dart
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/share_queue_item.dart';

class ShareQueueService {
  static const String _queueKey = 'share_queue';
  static const int _maxQueueSize = 20;
  static const Duration _itemTTL = Duration(days: 7);

  // 큐 로드
  Future<List<ShareQueueItem>> loadQueue() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_queueKey);

    if (jsonStr == null || jsonStr.isEmpty) {
      return [];
    }

    try {
      final List<dynamic> jsonList = jsonDecode(jsonStr);
      final items = jsonList
          .map((json) => ShareQueueItem.fromJson(json as Map<String, dynamic>))
          .toList();

      // 오래된 항목 자동 제거
      final now = DateTime.now();
      final validItems = items
          .where((item) => now.difference(item.sharedAt) < _itemTTL)
          .toList();

      // 정리가 필요하면 저장
      if (validItems.length != items.length) {
        await saveQueue(validItems);
      }

      return validItems;
    } catch (e) {
      // JSON 파싱 실패 시 빈 큐 반환
      return [];
    }
  }

  // 큐 저장
  Future<void> saveQueue(List<ShareQueueItem> items) async {
    final prefs = await SharedPreferences.getInstance();

    // 크기 제한
    final limitedItems = items.take(_maxQueueSize).toList();

    final jsonList = limitedItems.map((item) => item.toJson()).toList();
    final jsonStr = jsonEncode(jsonList);

    await prefs.setString(_queueKey, jsonStr);
  }

  // 큐 삭제
  Future<void> clearQueue() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_queueKey);
  }

  // App Groups에서 로드 (iOS)
  Future<List<ShareQueueItem>> loadFromAppGroups() async {
    // iOS Share Extension에서 추가한 항목 가져오기
    // UserDefaults(suiteName:)으로 접근
    // Flutter에서는 shared_preferences가 자동으로 처리
    return loadQueue();
  }
}

final shareQueueServiceProvider = Provider<ShareQueueService>((ref) {
  return ShareQueueService();
});
```

### 3-5. Share Intent 수신

#### main.dart
```dart
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

class MyApp extends ConsumerStatefulWidget {
  @override
  ConsumerState<MyApp> createState() => _MyAppState();
}

class _MyAppState extends ConsumerState<MyApp> {
  late StreamSubscription _intentDataStreamSubscription;

  @override
  void initState() {
    super.initState();

    // 앱 실행 중 공유 받기
    _intentDataStreamSubscription =
        ReceiveSharingIntent.getTextStream().listen((String value) {
      _handleSharedUrl(value);
    }, onError: (err) {
      print("Error receiving share: $err");
    });

    // 앱이 종료 상태에서 공유로 실행
    ReceiveSharingIntent.getInitialText().then((String? value) {
      if (value != null) {
        _handleSharedUrl(value);
      }
    });
  }

  void _handleSharedUrl(String url) {
    // ShareQueueProvider에 추가
    ref.read(shareQueueProvider.notifier).addUrl(url);

    // 홈 화면으로 이동
    context.go('/home');
  }

  @override
  void dispose() {
    _intentDataStreamSubscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      routerConfig: router,
    );
  }
}
```

---

## 4. UI 구현

### 4-1. 홈 화면 배지

#### widgets/share_queue_badge.dart
```dart
class ShareQueueBadge extends ConsumerWidget {
  const ShareQueueBadge({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final queueState = ref.watch(shareQueueProvider);
    final pendingCount = queueState.items
        .where((item) => item.status == ShareQueueStatus.pending)
        .length;

    if (pendingCount == 0) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.primary,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: AppColors.primary.withOpacity(0.3),
            blurRadius: 8,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          const Icon(Icons.link, color: Colors.white, size: 24),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              '$pendingCount개 링크 분석 대기 중',
              style: AppTextStyles.subtitle1.copyWith(color: Colors.white),
            ),
          ),
          ElevatedButton(
            onPressed: () => _showProcessingSheet(context, ref),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              foregroundColor: AppColors.primary,
            ),
            child: const Text('분석 시작'),
          ),
        ],
      ),
    );
  }

  void _showProcessingSheet(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const BatchProcessingSheet(),
    );

    // 분석 시작
    ref.read(shareQueueProvider.notifier).processBatch();
  }
}
```

### 4-2. 분석 진행 바텀 시트

#### widgets/batch_processing_sheet.dart
```dart
class BatchProcessingSheet extends ConsumerWidget {
  const BatchProcessingSheet({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(shareQueueProvider);
    final totalCount = state.items
        .where((item) => item.status != ShareQueueStatus.saved &&
            item.status != ShareQueueStatus.ignored)
        .length;

    final progress = totalCount == 0 ? 0.0 : state.processingIndex / totalCount;

    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          // 제목
          Text(
            '📦 링크 분석 중 (${state.processingIndex}/$totalCount)',
            style: AppTextStyles.h3,
          ),
          const SizedBox(height: 16),

          // 진행률
          LinearProgressIndicator(
            value: progress,
            minHeight: 8,
            borderRadius: BorderRadius.circular(4),
          ),
          const SizedBox(height: 8),
          Text(
            '${(progress * 100).toInt()}%',
            style: AppTextStyles.body2,
          ),
          const SizedBox(height: 24),

          // 항목 목록
          Expanded(
            child: ListView.builder(
              itemCount: state.items.length,
              itemBuilder: (context, index) {
                final item = state.items[index];
                return ShareQueueItemTile(item: item);
              },
            ),
          ),

          // 백그라운드 버튼
          if (state.isProcessing)
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('백그라운드로'),
            ),
        ],
      ),
    );
  }
}

class ShareQueueItemTile extends StatelessWidget {
  final ShareQueueItem item;

  const ShareQueueItemTile({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: _buildStatusIcon(),
      title: Text(
        item.result?.placeName ?? item.title ?? item.url,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: _buildSubtitle(),
      trailing: item.status == ShareQueueStatus.completed
          ? Text(
              '${(item.result!.confidence * 100).toInt()}%',
              style: AppTextStyles.caption.copyWith(
                color: _getConfidenceColor(item.result!.confidence),
                fontWeight: FontWeight.bold,
              ),
            )
          : null,
    );
  }

  Widget _buildStatusIcon() {
    switch (item.status) {
      case ShareQueueStatus.pending:
        return const Icon(Icons.schedule, color: Colors.grey);
      case ShareQueueStatus.analyzing:
        return const SizedBox(
          width: 24,
          height: 24,
          child: CircularProgressIndicator(strokeWidth: 2),
        );
      case ShareQueueStatus.completed:
        return const Icon(Icons.check_circle, color: Colors.green);
      case ShareQueueStatus.failed:
        return const Icon(Icons.error, color: Colors.red);
      default:
        return const SizedBox.shrink();
    }
  }

  Widget? _buildSubtitle() {
    switch (item.status) {
      case ShareQueueStatus.pending:
        return const Text('대기 중');
      case ShareQueueStatus.analyzing:
        return const Text('분석 중...');
      case ShareQueueStatus.completed:
        return Text(item.result?.category ?? '');
      case ShareQueueStatus.failed:
        return Text(
          item.errorMessage ?? '분석 실패',
          style: const TextStyle(color: Colors.red),
        );
      default:
        return null;
    }
  }

  Color _getConfidenceColor(double confidence) {
    if (confidence >= 0.9) return Colors.green;
    if (confidence >= 0.7) return Colors.orange;
    return Colors.red;
  }
}
```

---

## 5. 성능 최적화

### 5-1. 메모리 관리
```dart
// 큐 크기 제한
static const int _maxQueueSize = 20;

// 오래된 항목 자동 정리
static const Duration _itemTTL = Duration(days: 7);

// 이미지 캐싱 제한
CachedNetworkImage(
  imageUrl: imageUrl,
  memCacheWidth: 400,
  memCacheHeight: 400,
  maxWidthDiskCache: 800,
  maxHeightDiskCache: 800,
)
```

### 5-2. 네트워크 최적화
```dart
// 순차 처리로 서버 부하 분산
for (final item in items) {
  await _analyzeItem(item);
  await Future.delayed(const Duration(milliseconds: 500));
}

// 타임아웃 설정
final dio = Dio(
  BaseOptions(
    connectTimeout: const Duration(seconds: 30),
    receiveTimeout: const Duration(seconds: 30),
  ),
);
```

### 5-3. 배터리 최적화
```dart
import 'package:battery_plus/battery_plus.dart';

class BatteryAwareProcessor {
  final Battery _battery = Battery();

  Future<bool> shouldProcess() async {
    final level = await _battery.batteryLevel;
    final state = await _battery.batteryState;

    // 충전 중이거나 배터리 20% 이상
    return state == BatteryState.charging || level > 20;
  }
}
```

---

## 6. 에러 처리

### 6-1. 재시도 로직
```dart
Future<void> _analyzeWithRetry(ShareQueueItem item) async {
  const maxRetries = 3;
  const retryDelay = Duration(seconds: 2);

  for (var i = 0; i < maxRetries; i++) {
    try {
      final result = await _analysisService.analyzeLink(item.url);
      _updateItemWithResult(item.id, result);
      return;
    } catch (e) {
      if (i == maxRetries - 1) {
        _updateItemError(item.id, e.toString());
      } else {
        await Future.delayed(retryDelay * (i + 1));
      }
    }
  }
}
```

### 6-2. 네트워크 에러
```dart
class NetworkErrorHandler {
  static Future<T> handleNetworkCall<T>(
    Future<T> Function() call,
  ) async {
    try {
      return await call();
    } on DioException catch (e) {
      if (e.type == DioExceptionType.connectionTimeout) {
        throw '네트워크 연결 시간 초과';
      } else if (e.type == DioExceptionType.receiveTimeout) {
        throw '서버 응답 시간 초과';
      } else if (e.response?.statusCode == 429) {
        throw '요청이 너무 많습니다. 잠시 후 다시 시도해주세요';
      } else {
        throw '네트워크 오류: ${e.message}';
      }
    }
  }
}
```

---

## 7. 테스트

### 7-1. Unit Tests
```dart
// test/share_queue_service_test.dart
void main() {
  group('ShareQueueService', () {
    late ShareQueueService service;

    setUp(() {
      service = ShareQueueService();
    });

    test('should save and load queue', () async {
      final items = [
        ShareQueueItem(
          id: '1',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
        ),
      ];

      await service.saveQueue(items);
      final loaded = await service.loadQueue();

      expect(loaded.length, 1);
      expect(loaded.first.url, 'https://instagram.com/p/xxx');
    });

    test('should limit queue size to 20', () async {
      final items = List.generate(
        25,
        (i) => ShareQueueItem(
          id: '$i',
          url: 'https://example.com/$i',
          sharedAt: DateTime.now(),
        ),
      );

      await service.saveQueue(items);
      final loaded = await service.loadQueue();

      expect(loaded.length, 20);
    });
  });
}
```

### 7-2. Widget Tests
```dart
// test/widgets/share_queue_badge_test.dart
void main() {
  testWidgets('should show pending count', (tester) async {
    final container = ProviderContainer(
      overrides: [
        shareQueueProvider.overrideWith((ref) {
          return ShareQueueNotifier(...);
        }),
      ],
    );

    await tester.pumpWidget(
      UncontrolledProviderScope(
        container: container,
        child: MaterialApp(
          home: Scaffold(
            body: ShareQueueBadge(),
          ),
        ),
      ),
    );

    expect(find.text('3개 링크 분석 대기 중'), findsOneWidget);
  });
}
```

### 7-3. Integration Tests
```dart
// integration_test/share_flow_test.dart
void main() {
  testWidgets('complete share flow', (tester) async {
    await tester.pumpWidget(MyApp());

    // 1. 공유 URL 추가
    // (Share Extension 테스트는 수동)

    // 2. 배지 확인
    expect(find.byType(ShareQueueBadge), findsOneWidget);

    // 3. 분석 시작
    await tester.tap(find.text('분석 시작'));
    await tester.pumpAndSettle();

    // 4. 진행 확인
    expect(find.byType(BatchProcessingSheet), findsOneWidget);

    // 5. 완료 대기
    await tester.pump(Duration(seconds: 60));

    // 6. 결과 확인
    expect(find.text('분석 완료'), findsOneWidget);
  });
}
```

---

## 8. 배포

### 8-1. iOS 빌드 설정
```bash
# 1. Bundle ID 확인
Main App: com.hotly.app
Share Extension: com.hotly.app.ShareExtension

# 2. App Groups 확인
group.com.hotly.sharequeue

# 3. 프로비저닝 프로파일
- Main App: Distribution Profile
- Share Extension: Distribution Profile (동일 Team ID)

# 4. 빌드
flutter build ios --release
```

### 8-2. 버전 관리
```yaml
# pubspec.yaml
version: 1.1.0+11

# iOS/Runner/Info.plist
CFBundleShortVersionString: 1.1.0
CFBundleVersion: 11

# iOS/ShareExtension/Info.plist
CFBundleShortVersionString: 1.1.0
CFBundleVersion: 11
```

---

## 9. 모니터링

### 9-1. Analytics
```dart
class ShareQueueAnalytics {
  static Future<void> logShareReceived(String platform) async {
    await FirebaseAnalytics.instance.logEvent(
      name: 'share_received',
      parameters: {'platform': platform},
    );
  }

  static Future<void> logBatchProcessingStarted(int itemCount) async {
    await FirebaseAnalytics.instance.logEvent(
      name: 'batch_processing_started',
      parameters: {'item_count': itemCount},
    );
  }

  static Future<void> logAnalysisCompleted({
    required String itemId,
    required double confidence,
    required Duration duration,
  }) async {
    await FirebaseAnalytics.instance.logEvent(
      name: 'analysis_completed',
      parameters: {
        'item_id': itemId,
        'confidence': confidence,
        'duration_ms': duration.inMilliseconds,
      },
    );
  }
}
```

### 9-2. Error Tracking
```dart
class ShareQueueErrorTracking {
  static Future<void> logError(
    String operation,
    dynamic error,
    StackTrace? stack,
  ) async {
    await FirebaseCrashlytics.instance.recordError(
      error,
      stack,
      reason: 'ShareQueue: $operation',
    );
  }
}
```

---

## 10. 보안

### 10-1. URL 검증
```dart
class URLValidator {
  static final _allowedDomains = [
    'instagram.com',
    'blog.naver.com',
    'youtube.com',
    'youtu.be',
  ];

  static bool isAllowed(String url) {
    try {
      final uri = Uri.parse(url);
      final host = uri.host.toLowerCase();
      return _allowedDomains.any((domain) => host.contains(domain));
    } catch (e) {
      return false;
    }
  }

  static bool isSafe(String url) {
    // XSS, SSRF 방지
    final uri = Uri.parse(url);
    return uri.scheme == 'https' || uri.scheme == 'http';
  }
}
```

### 10-2. 데이터 암호화
```dart
// Sensitive data는 flutter_secure_storage 사용
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureQueueStorage {
  final FlutterSecureStorage _storage = FlutterSecureStorage();

  Future<void> saveSecureQueue(List<ShareQueueItem> items) async {
    final jsonStr = jsonEncode(items.map((e) => e.toJson()).toList());
    await _storage.write(key: 'secure_queue', value: jsonStr);
  }
}
```

---

**버전:** v1.0
**작성일:** 2025-11-26
**작성자:** Claude Code
**상태:** 구현 준비 완료
