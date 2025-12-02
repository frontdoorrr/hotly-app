import 'package:flutter_test/flutter_test.dart';
import 'package:hotly_app/features/share_queue/domain/entities/share_queue_item.dart';

void main() {
  group('ShareQueueItem', () {
    test('should create item with required fields', () {
      final item = ShareQueueItem(
        id: '123',
        url: 'https://instagram.com/p/xxx',
        sharedAt: DateTime(2025, 1, 1),
      );

      expect(item.id, '123');
      expect(item.url, 'https://instagram.com/p/xxx');
      expect(item.status, ShareQueueStatus.pending);
      expect(item.retryCount, 0);
    });

    test('should create item with optional fields', () {
      final item = ShareQueueItem(
        id: '123',
        url: 'https://instagram.com/p/xxx',
        title: '강남 카페',
        sharedAt: DateTime(2025, 1, 1),
        platform: 'instagram',
      );

      expect(item.title, '강남 카페');
      expect(item.platform, 'instagram');
    });

    test('should serialize to JSON', () {
      final item = ShareQueueItem(
        id: '123',
        url: 'https://instagram.com/p/xxx',
        sharedAt: DateTime(2025, 1, 1),
        status: ShareQueueStatus.pending,
      );

      final json = item.toJson();

      expect(json['id'], '123');
      expect(json['url'], 'https://instagram.com/p/xxx');
      expect(json['status'], 'pending');
    });

    test('should deserialize from JSON', () {
      final json = {
        'id': '123',
        'url': 'https://instagram.com/p/xxx',
        'sharedAt': '2025-01-01T00:00:00.000',
        'status': 'pending',
        'retryCount': 0,
      };

      final item = ShareQueueItem.fromJson(json);

      expect(item.id, '123');
      expect(item.url, 'https://instagram.com/p/xxx');
      expect(item.status, ShareQueueStatus.pending);
    });

    test('copyWith should update fields', () {
      final item = ShareQueueItem(
        id: '123',
        url: 'https://instagram.com/p/xxx',
        sharedAt: DateTime(2025, 1, 1),
      );

      final updated = item.copyWith(
        status: ShareQueueStatus.analyzing,
        retryCount: 1,
      );

      expect(updated.id, '123');
      expect(updated.status, ShareQueueStatus.analyzing);
      expect(updated.retryCount, 1);
    });
  });

  group('ShareQueueAnalysisResult', () {
    test('should create result with required fields', () {
      final result = ShareQueueAnalysisResult(
        placeName: '강남 카페',
        category: '카페',
      );

      expect(result.placeName, '강남 카페');
      expect(result.category, '카페');
      expect(result.confidence, 0.0);
      expect(result.tags, isEmpty);
    });

    test('should create result with all fields', () {
      final result = ShareQueueAnalysisResult(
        placeName: '강남 카페',
        category: '카페',
        address: '서울시 강남구',
        imageUrl: 'https://example.com/image.jpg',
        confidence: 0.95,
        tags: ['카페', '디저트'],
        analysisId: 'analysis-123',
      );

      expect(result.address, '서울시 강남구');
      expect(result.confidence, 0.95);
      expect(result.tags, ['카페', '디저트']);
    });

    test('should serialize to JSON', () {
      final result = ShareQueueAnalysisResult(
        placeName: '강남 카페',
        category: '카페',
        confidence: 0.85,
      );

      final json = result.toJson();

      expect(json['placeName'], '강남 카페');
      expect(json['category'], '카페');
      expect(json['confidence'], 0.85);
    });

    test('should deserialize from JSON', () {
      final json = {
        'placeName': '강남 카페',
        'category': '카페',
        'confidence': 0.85,
        'tags': <String>[],
      };

      final result = ShareQueueAnalysisResult.fromJson(json);

      expect(result.placeName, '강남 카페');
      expect(result.confidence, 0.85);
    });
  });

  group('ShareQueueState', () {
    test('should create empty state', () {
      const state = ShareQueueState();

      expect(state.items, isEmpty);
      expect(state.isProcessing, false);
      expect(state.pendingCount, 0);
      expect(state.completedCount, 0);
    });

    test('pendingCount should count pending items', () {
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
            status: ShareQueueStatus.completed,
          ),
        ],
      );

      expect(state.pendingCount, 2);
      expect(state.completedCount, 1);
    });

    test('processableItems should return pending and failed items with retry < 3', () {
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
            status: ShareQueueStatus.failed,
            retryCount: 1,
          ),
          ShareQueueItem(
            id: '3',
            url: 'https://instagram.com/p/3',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.failed,
            retryCount: 3, // Should be excluded
          ),
          ShareQueueItem(
            id: '4',
            url: 'https://instagram.com/p/4',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.completed,
          ),
        ],
      );

      final processable = state.processableItems;

      expect(processable.length, 2);
      expect(processable.map((e) => e.id), ['1', '2']);
    });

    test('highConfidenceItems should filter by confidence >= 0.7', () {
      final state = ShareQueueState(
        items: [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.completed,
            result: const ShareQueueAnalysisResult(
              placeName: 'High confidence',
              category: '카페',
              confidence: 0.95,
            ),
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.completed,
            result: const ShareQueueAnalysisResult(
              placeName: 'Low confidence',
              category: '식당',
              confidence: 0.45,
            ),
          ),
        ],
      );

      final highConfidence = state.highConfidenceItems;

      expect(highConfidence.length, 1);
      expect(highConfidence.first.result!.placeName, 'High confidence');
    });

    test('progress should calculate correctly', () {
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
            status: ShareQueueStatus.completed,
          ),
        ],
        processingIndex: 1,
      );

      expect(state.progress, 0.5);
    });

    test('progress should return 0 for empty items', () {
      const state = ShareQueueState();
      expect(state.progress, 0.0);
    });
  });

  group('ShareQueueStatus', () {
    test('should have correct enum values', () {
      expect(ShareQueueStatus.values.length, 6);
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.pending));
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.analyzing));
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.completed));
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.saved));
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.failed));
      expect(ShareQueueStatus.values, contains(ShareQueueStatus.ignored));
    });
  });
}
