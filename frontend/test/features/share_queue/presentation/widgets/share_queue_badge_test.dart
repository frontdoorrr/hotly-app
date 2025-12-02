import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hotly_app/features/share_queue/domain/entities/share_queue_item.dart';
import 'package:hotly_app/features/share_queue/presentation/providers/share_queue_provider.dart';
import 'package:hotly_app/features/share_queue/presentation/widgets/share_queue_badge.dart';

void main() {
  group('ShareQueueBadge', () {
    testWidgets('should not display when no pending items', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(const ShareQueueState());
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueBadge(),
            ),
          ),
        ),
      );

      expect(find.byType(ShareQueueBadge), findsOneWidget);
      expect(find.text('분석 시작'), findsNothing);
    });

    testWidgets('should display pending count', (tester) async {
      final state = ShareQueueState(
        items: [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(state);
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueBadge(),
            ),
          ),
        ),
      );

      expect(find.text('2개 링크 분석 대기 중'), findsOneWidget);
      expect(find.text('분석 시작'), findsOneWidget);
    });

    testWidgets('should show progress when processing', (tester) async {
      final state = ShareQueueState(
        items: [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.analyzing,
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
        ],
        isProcessing: true,
        processingIndex: 0,
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(state);
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueBadge(),
            ),
          ),
        ),
      );

      // Should show processing indicator
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.textContaining('분석 중'), findsOneWidget);
    });

    testWidgets('should open bottom sheet on tap', (tester) async {
      final state = ShareQueueState(
        items: [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(state);
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueBadge(),
            ),
          ),
        ),
      );

      await tester.tap(find.byType(InkWell).first);
      await tester.pumpAndSettle();

      // Bottom sheet should be shown
      expect(find.byType(BottomSheet), findsOneWidget);
    });
  });

  group('ShareQueueMiniBadge', () {
    testWidgets('should not show badge when no pending items', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(const ShareQueueState());
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueMiniBadge(
                child: Icon(Icons.home),
              ),
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.home), findsOneWidget);
      // No badge number should be shown
      expect(find.text('1'), findsNothing);
    });

    testWidgets('should show badge with count', (tester) async {
      final state = ShareQueueState(
        items: [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
          ShareQueueItem(
            id: '3',
            url: 'https://instagram.com/p/3',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(state);
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueMiniBadge(
                child: Icon(Icons.home),
              ),
            ),
          ),
        ),
      );

      expect(find.text('3'), findsOneWidget);
    });

    testWidgets('should show 9+ for more than 9 items', (tester) async {
      final items = List.generate(
        12,
        (i) => ShareQueueItem(
          id: '$i',
          url: 'https://instagram.com/p/$i',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.pending,
        ),
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            shareQueueProvider.overrideWith((ref) {
              return _TestShareQueueNotifier(ShareQueueState(items: items));
            }),
          ],
          child: const MaterialApp(
            home: Scaffold(
              body: ShareQueueMiniBadge(
                child: Icon(Icons.home),
              ),
            ),
          ),
        ),
      );

      expect(find.text('9+'), findsOneWidget);
    });
  });
}

/// Test notifier that allows direct state control
class _TestShareQueueNotifier extends ShareQueueNotifier {
  _TestShareQueueNotifier(ShareQueueState initialState)
      : super(
          _MockStorageService(),
          _MockRepository(),
        ) {
    state = initialState;
  }
}

class _MockStorageService implements ShareQueueStorageService {
  @override
  Future<List<ShareQueueItem>> loadQueue() async => [];

  @override
  Future<void> saveQueue(List<ShareQueueItem> items) async {}

  @override
  Future<void> clearQueue() async {}

  @override
  Future<ShareQueueItem?> addItem({
    required String url,
    String? title,
    String? platform,
  }) async => null;

  @override
  Future<void> updateItem(ShareQueueItem item) async {}

  @override
  Future<void> removeItem(String id) async {}

  @override
  Future<int> cleanupCompletedItems() async => 0;
}

class _MockRepository implements LinkAnalysisRepository {
  @override
  Future<dynamic> analyzeLink(String url, {bool forceRefresh = false}) async {
    throw UnimplementedError();
  }

  @override
  Future<dynamic> getAnalysisStatus(String analysisId) async {
    throw UnimplementedError();
  }

  @override
  Future<dynamic> cancelAnalysis(String analysisId) async {
    throw UnimplementedError();
  }

  @override
  Future<dynamic> saveAnalyzedPlace(String analysisId, {String? sourceUrl}) async {
    throw UnimplementedError();
  }
}
