import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hotly_app/features/share_queue/data/services/share_queue_storage_service.dart';
import 'package:hotly_app/features/share_queue/domain/entities/share_queue_item.dart';

void main() {
  late ShareQueueStorageService service;

  setUp(() {
    SharedPreferences.setMockInitialValues({});
    service = ShareQueueStorageService();
  });

  group('ShareQueueStorageService', () {
    group('loadQueue', () {
      test('should return empty list when no data', () async {
        final items = await service.loadQueue();
        expect(items, isEmpty);
      });

      test('should load saved items', () async {
        // Save first
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
        );
        await service.saveQueue([item]);

        // Then load
        final loaded = await service.loadQueue();

        expect(loaded.length, 1);
        expect(loaded.first.id, '123');
        expect(loaded.first.url, 'https://instagram.com/p/xxx');
      });

      test('should filter out items older than 7 days', () async {
        final oldItem = ShareQueueItem(
          id: 'old',
          url: 'https://instagram.com/p/old',
          sharedAt: DateTime.now().subtract(const Duration(days: 8)),
        );
        final newItem = ShareQueueItem(
          id: 'new',
          url: 'https://instagram.com/p/new',
          sharedAt: DateTime.now(),
        );

        await service.saveQueue([oldItem, newItem]);
        final loaded = await service.loadQueue();

        expect(loaded.length, 1);
        expect(loaded.first.id, 'new');
      });
    });

    group('saveQueue', () {
      test('should save items', () async {
        final items = [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
          ),
        ];

        await service.saveQueue(items);
        final loaded = await service.loadQueue();

        expect(loaded.length, 2);
      });

      test('should limit to 20 items', () async {
        final items = List.generate(
          25,
          (i) => ShareQueueItem(
            id: '$i',
            url: 'https://instagram.com/p/$i',
            sharedAt: DateTime.now(),
          ),
        );

        await service.saveQueue(items);
        final loaded = await service.loadQueue();

        expect(loaded.length, 20);
      });
    });

    group('clearQueue', () {
      test('should clear all items', () async {
        final item = ShareQueueItem(
          id: '123',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
        );
        await service.saveQueue([item]);

        await service.clearQueue();
        final loaded = await service.loadQueue();

        expect(loaded, isEmpty);
      });
    });

    group('addItem', () {
      test('should add new item', () async {
        final item = await service.addItem(
          url: 'https://instagram.com/p/xxx',
          title: 'Test',
        );

        expect(item, isNotNull);
        expect(item!.url, 'https://instagram.com/p/xxx');
        expect(item.title, 'Test');
        expect(item.platform, 'instagram');
      });

      test('should return null for duplicate URL', () async {
        await service.addItem(url: 'https://instagram.com/p/xxx');
        final duplicate = await service.addItem(url: 'https://instagram.com/p/xxx');

        expect(duplicate, isNull);
      });

      test('should return null when queue is full', () async {
        // Fill queue to max
        for (var i = 0; i < 20; i++) {
          await service.addItem(url: 'https://instagram.com/p/$i');
        }

        final item = await service.addItem(url: 'https://instagram.com/p/new');
        expect(item, isNull);
      });

      test('should detect platform from URL', () async {
        final instagram = await service.addItem(
          url: 'https://www.instagram.com/p/xxx',
        );
        expect(instagram!.platform, 'instagram');

        final naverBlog = await service.addItem(
          url: 'https://blog.naver.com/xxx',
        );
        expect(naverBlog!.platform, 'naver_blog');

        final youtube = await service.addItem(
          url: 'https://www.youtube.com/watch?v=xxx',
        );
        expect(youtube!.platform, 'youtube');

        final youtubeShort = await service.addItem(
          url: 'https://youtu.be/xxx',
        );
        expect(youtubeShort!.platform, 'youtube');
      });
    });

    group('updateItem', () {
      test('should update existing item', () async {
        final item = await service.addItem(url: 'https://instagram.com/p/xxx');

        final updated = item!.copyWith(status: ShareQueueStatus.analyzing);
        await service.updateItem(updated);

        final loaded = await service.loadQueue();
        expect(loaded.first.status, ShareQueueStatus.analyzing);
      });

      test('should not fail for non-existing item', () async {
        final item = ShareQueueItem(
          id: 'non-existing',
          url: 'https://instagram.com/p/xxx',
          sharedAt: DateTime.now(),
        );

        // Should not throw
        await service.updateItem(item);
      });
    });

    group('removeItem', () {
      test('should remove item by id', () async {
        await service.addItem(url: 'https://instagram.com/p/1');
        final item2 = await service.addItem(url: 'https://instagram.com/p/2');

        await service.removeItem(item2!.id);
        final loaded = await service.loadQueue();

        expect(loaded.length, 1);
        expect(loaded.first.url, 'https://instagram.com/p/1');
      });
    });

    group('cleanupCompletedItems', () {
      test('should remove saved and ignored items', () async {
        final items = [
          ShareQueueItem(
            id: '1',
            url: 'https://instagram.com/p/1',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.saved,
          ),
          ShareQueueItem(
            id: '2',
            url: 'https://instagram.com/p/2',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.ignored,
          ),
          ShareQueueItem(
            id: '3',
            url: 'https://instagram.com/p/3',
            sharedAt: DateTime.now(),
            status: ShareQueueStatus.pending,
          ),
        ];
        await service.saveQueue(items);

        final removedCount = await service.cleanupCompletedItems();
        final loaded = await service.loadQueue();

        expect(removedCount, 2);
        expect(loaded.length, 1);
        expect(loaded.first.id, '3');
      });
    });
  });

  group('isSupportedUrl', () {
    test('should return true for Instagram', () {
      expect(
        ShareQueueStorageService.isSupportedUrl('https://instagram.com/p/xxx'),
        true,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl('https://www.instagram.com/reel/xxx'),
        true,
      );
    });

    test('should return true for Naver Blog', () {
      expect(
        ShareQueueStorageService.isSupportedUrl('https://blog.naver.com/xxx/123'),
        true,
      );
    });

    test('should return true for YouTube', () {
      expect(
        ShareQueueStorageService.isSupportedUrl('https://youtube.com/watch?v=xxx'),
        true,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl('https://www.youtube.com/watch?v=xxx'),
        true,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl('https://youtu.be/xxx'),
        true,
      );
    });

    test('should return false for unsupported platforms', () {
      expect(
        ShareQueueStorageService.isSupportedUrl('https://facebook.com/xxx'),
        false,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl('https://twitter.com/xxx'),
        false,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl('https://tiktok.com/xxx'),
        false,
      );
    });

    test('should return false for invalid URLs', () {
      expect(
        ShareQueueStorageService.isSupportedUrl('not-a-url'),
        false,
      );
      expect(
        ShareQueueStorageService.isSupportedUrl(''),
        false,
      );
    });
  });

  group('supportedDomains', () {
    test('should contain all supported domains', () {
      expect(
        ShareQueueStorageService.supportedDomains,
        containsAll(['instagram.com', 'blog.naver.com', 'youtube.com', 'youtu.be']),
      );
    });
  });
}
