import 'package:dartz/dartz.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hotly_app/features/share_queue/data/services/share_queue_storage_service.dart';
import 'package:hotly_app/features/share_queue/domain/entities/share_queue_item.dart';
import 'package:hotly_app/features/share_queue/presentation/providers/share_queue_provider.dart';
import 'package:hotly_app/features/link_analysis/domain/entities/link_analysis_result.dart';
import 'package:hotly_app/features/link_analysis/domain/repositories/link_analysis_repository.dart';

class MockLinkAnalysisRepository extends Mock
    implements LinkAnalysisRepository {}

class MockShareQueueStorageService extends Mock
    implements ShareQueueStorageService {}

void main() {
  late ShareQueueNotifier notifier;
  late MockShareQueueStorageService mockStorageService;
  late MockLinkAnalysisRepository mockRepository;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    mockStorageService = MockShareQueueStorageService();
    mockRepository = MockLinkAnalysisRepository();

    // Default stub for loadQueue
    when(() => mockStorageService.loadQueue()).thenAnswer((_) async => []);
    when(() => mockStorageService.saveQueue(any())).thenAnswer((_) async {});

    notifier = ShareQueueNotifier(mockStorageService, mockRepository);
  });

  tearDown(() {
    notifier.dispose();
  });

  group('ShareQueueNotifier', () {
    group('initialization', () {
      test('should load queue on creation', () async {
        // Wait for async initialization
        await Future.delayed(const Duration(milliseconds: 100));

        verify(() => mockStorageService.loadQueue()).called(1);
      });

      test('should start with empty state', () {
        expect(notifier.state.items, isEmpty);
        expect(notifier.state.isProcessing, false);
      });
    });

    group('addUrl', () {
      test('should add valid URL to queue', () async {
        when(() => mockStorageService.addItem(
              url: any(named: 'url'),
              title: any(named: 'title'),
            )).thenAnswer((_) async => ShareQueueItem(
              id: '123',
              url: 'https://instagram.com/p/xxx',
              sharedAt: DateTime.now(),
            ));

        final result = await notifier.addUrl('https://instagram.com/p/xxx');

        expect(result, true);
        expect(notifier.state.items.length, 1);
      });

      test('should reject unsupported URL', () async {
        final result = await notifier.addUrl('https://facebook.com/xxx');

        expect(result, false);
        expect(notifier.state.error, contains('지원하지 않는'));
      });

      test('should reject duplicate URL', () async {
        when(() => mockStorageService.addItem(
              url: any(named: 'url'),
              title: any(named: 'title'),
            )).thenAnswer((_) async => null);

        final result = await notifier.addUrl('https://instagram.com/p/xxx');

        expect(result, false);
        expect(notifier.state.error, isNotNull);
      });
    });

    group('processBatch', () {
      test('should not process if already processing', () async {
        // Manually set isProcessing
        notifier.state = notifier.state.copyWith(isProcessing: true);

        await notifier.processBatch();

        // Should not call repository
        verifyNever(() => mockRepository.analyzeLink(url: any(named: 'url')));
      });

      test('should not process if no processable items', () async {
        await notifier.processBatch();

        verifyNever(() => mockRepository.analyzeLink(url: any(named: 'url')));
      });

      test('should process pending items', () async {
        // Setup item
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.pending,
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);

        // Re-initialize with items
        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        // Mock successful analysis
        when(() => mockRepository.analyzeLink(
              url: any(named: 'url'),
              forceRefresh: any(named: 'forceRefresh'),
            )).thenAnswer(
          (_) async => Right(const LinkAnalysisResult(
            analysisId: 'analysis-123',
            status: AnalysisStatus.completed,
            placeInfo: PlaceInfo(
              name: '강남 카페',
              category: '카페',
            ),
            confidence: 0.95,
          )),
        );

        await notifier.processBatch();

        verify(() => mockRepository.analyzeLink(
              url: 'https://instagram.com/p/xxx',
            )).called(1);
      });

      test('should handle analysis failure', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.pending,
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);

        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        when(() => mockRepository.analyzeLink(
              url: any(named: 'url'),
              forceRefresh: any(named: 'forceRefresh'),
            )).thenAnswer(
          (_) async => const Left('Network error'),
        );

        await notifier.processBatch();

        expect(
          notifier.state.items.first.status,
          ShareQueueStatus.failed,
        );
        expect(
          notifier.state.items.first.retryCount,
          1,
        );
      });
    });

    group('retryFailed', () {
      test('should reset failed items and reprocess', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.failed,
          retryCount: 1,
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);

        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        when(() => mockRepository.analyzeLink(
              url: any(named: 'url'),
              forceRefresh: any(named: 'forceRefresh'),
            )).thenAnswer(
          (_) async => Right(const LinkAnalysisResult(
            analysisId: 'analysis-123',
            status: AnalysisStatus.completed,
            placeInfo: PlaceInfo(name: '강남 카페', category: '카페'),
            confidence: 0.95,
          )),
        );

        await notifier.retryFailed();

        verify(() => mockRepository.analyzeLink(url: any(named: 'url'))).called(1);
      });

      test('should not retry items with retryCount >= 3', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.failed,
          retryCount: 3,
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);

        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        await notifier.retryFailed();

        verifyNever(() => mockRepository.analyzeLink(url: any(named: 'url')));
      });
    });

    group('ignoreItem', () {
      test('should update item status to ignored', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
          status: ShareQueueStatus.completed,
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);

        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        notifier.ignoreItem('123');

        expect(
          notifier.state.items.first.status,
          ShareQueueStatus.ignored,
        );
      });
    });

    group('removeItem', () {
      test('should remove item from queue', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
        );

        when(() => mockStorageService.loadQueue())
            .thenAnswer((_) async => [item]);
        when(() => mockStorageService.removeItem(any()))
            .thenAnswer((_) async {});

        notifier = ShareQueueNotifier(mockStorageService, mockRepository);
        await Future.delayed(const Duration(milliseconds: 100));

        await notifier.removeItem('123');

        expect(notifier.state.items, isEmpty);
        verify(() => mockStorageService.removeItem('123')).called(1);
      });
    });

    group('clearQueue', () {
      test('should clear all items', () async {
        when(() => mockStorageService.clearQueue()).thenAnswer((_) async {});

        await notifier.clearQueue();

        expect(notifier.state.items, isEmpty);
        expect(notifier.state.isProcessing, false);
        verify(() => mockStorageService.clearQueue()).called(1);
      });
    });

    group('cancelProcessing', () {
      test('should set isProcessing to false', () {
        notifier.state = notifier.state.copyWith(isProcessing: true);

        notifier.cancelProcessing();

        expect(notifier.state.isProcessing, false);
      });
    });

    group('clearError', () {
      test('should clear error', () {
        notifier.state = notifier.state.copyWith(error: 'Some error');

        notifier.clearError();

        expect(notifier.state.error, isNull);
      });
    });
  });
}
