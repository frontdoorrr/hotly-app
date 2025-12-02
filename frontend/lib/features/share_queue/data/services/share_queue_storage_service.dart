import 'dart:convert';
import 'dart:io';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:logger/logger.dart';
import '../../domain/entities/share_queue_item.dart';

/// ShareQueue 로컬 저장소 서비스
///
/// SharedPreferences를 사용하여 큐 데이터를 저장/로드합니다.
/// App Groups를 통해 iOS Share Extension과 데이터를 공유합니다.
class ShareQueueStorageService {
  static const String _queueKey = 'share_queue';
  static const int _maxQueueSize = 20;
  static const Duration _itemTTL = Duration(days: 7);

  /// iOS App Groups Method Channel
  static const _channel = MethodChannel('com.hotly.app/share_queue');

  final Logger _logger = Logger();

  /// iOS App Groups에서 공유된 URL 가져오기
  ///
  /// Share Extension이 저장한 URL들을 읽어와서 큐에 추가합니다.
  Future<List<ShareQueueItem>> loadFromAppGroups() async {
    if (!Platform.isIOS) {
      return [];
    }

    try {
      final List<dynamic>? sharedUrls =
          await _channel.invokeMethod('getSharedUrls');

      if (sharedUrls == null || sharedUrls.isEmpty) {
        _logger.d('ShareQueue: No shared URLs in App Groups');
        return [];
      }

      _logger.i('ShareQueue: Found ${sharedUrls.length} URLs in App Groups');

      final items = <ShareQueueItem>[];
      for (final urlData in sharedUrls) {
        if (urlData is Map) {
          final url = urlData['url'] as String?;
          final id = urlData['id'] as String?;
          final sharedAtStr = urlData['sharedAt'] as String?;

          if (url != null && url.isNotEmpty) {
            DateTime sharedAt;
            try {
              sharedAt = sharedAtStr != null
                  ? DateTime.parse(sharedAtStr)
                  : DateTime.now();
            } catch (_) {
              sharedAt = DateTime.now();
            }

            items.add(ShareQueueItem(
              id: id ?? DateTime.now().millisecondsSinceEpoch.toString(),
              url: url,
              sharedAt: sharedAt,
              platform: _detectPlatform(url),
              status: ShareQueueStatus.pending,
            ));

            _logger.d('ShareQueue: Loaded from App Groups: $url');
          }
        }
      }

      // App Groups 데이터 삭제
      await _channel.invokeMethod('clearSharedUrls');
      _logger.i('ShareQueue: Cleared App Groups after loading');

      return items;
    } catch (e) {
      _logger.e('ShareQueue: Failed to load from App Groups: $e');
      return [];
    }
  }

  /// 큐 로드
  ///
  /// SharedPreferences에서 큐 데이터를 로드하고,
  /// iOS App Groups에서 새로 공유된 URL도 함께 로드합니다.
  /// 오래된 항목(7일 경과)은 자동으로 제거됩니다.
  Future<List<ShareQueueItem>> loadQueue() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final jsonStr = prefs.getString(_queueKey);

      List<ShareQueueItem> items = [];

      if (jsonStr != null && jsonStr.isNotEmpty) {
        final List<dynamic> jsonList = jsonDecode(jsonStr);
        items = jsonList
            .map(
                (json) => ShareQueueItem.fromJson(json as Map<String, dynamic>))
            .toList();
      }

      // iOS App Groups에서 새 항목 로드
      final appGroupItems = await loadFromAppGroups();
      if (appGroupItems.isNotEmpty) {
        // 중복 제거하며 병합
        for (final newItem in appGroupItems) {
          if (!items.any((item) => item.url == newItem.url)) {
            items.add(newItem);
            _logger.i('ShareQueue: Added from App Groups: ${newItem.url}');
          }
        }
        // 새 항목이 추가되었으면 저장
        await saveQueue(items);
      }

      // 오래된 항목 자동 제거
      final now = DateTime.now();
      final validItems = items
          .where((item) => now.difference(item.sharedAt) < _itemTTL)
          .toList();

      // 정리가 필요하면 저장
      if (validItems.length != items.length) {
        _logger.i(
          'ShareQueue: Cleaned up ${items.length - validItems.length} expired items',
        );
        await saveQueue(validItems);
      }

      _logger.d('ShareQueue: Loaded ${validItems.length} items total');
      return validItems;
    } catch (e) {
      _logger.e('ShareQueue: Failed to load queue: $e');
      return [];
    }
  }

  /// 큐 저장
  ///
  /// 큐 데이터를 SharedPreferences에 저장합니다.
  /// 최대 20개까지만 저장됩니다.
  Future<void> saveQueue(List<ShareQueueItem> items) async {
    try {
      final prefs = await SharedPreferences.getInstance();

      // 크기 제한
      final limitedItems = items.take(_maxQueueSize).toList();

      final jsonList = limitedItems.map((item) => item.toJson()).toList();
      final jsonStr = jsonEncode(jsonList);

      await prefs.setString(_queueKey, jsonStr);
      _logger.d('ShareQueue: Saved ${limitedItems.length} items');
    } catch (e) {
      _logger.e('ShareQueue: Failed to save queue: $e');
      rethrow;
    }
  }

  /// 큐 삭제 (전체)
  Future<void> clearQueue() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_queueKey);
      _logger.i('ShareQueue: Cleared all items');
    } catch (e) {
      _logger.e('ShareQueue: Failed to clear queue: $e');
      rethrow;
    }
  }

  /// 단일 항목 추가
  ///
  /// 새 URL을 큐에 추가합니다.
  /// 중복 URL은 추가하지 않습니다.
  Future<ShareQueueItem?> addItem({
    required String url,
    String? title,
    String? platform,
  }) async {
    try {
      final items = await loadQueue();

      // 중복 체크
      if (items.any((item) => item.url == url)) {
        _logger.w('ShareQueue: URL already exists: $url');
        return null;
      }

      // 큐 크기 제한
      if (items.length >= _maxQueueSize) {
        _logger.w('ShareQueue: Queue is full');
        return null;
      }

      final newItem = ShareQueueItem(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        url: url,
        title: title,
        sharedAt: DateTime.now(),
        platform: platform ?? _detectPlatform(url),
      );

      items.add(newItem);
      await saveQueue(items);

      _logger.i('ShareQueue: Added item: ${newItem.id}');
      return newItem;
    } catch (e) {
      _logger.e('ShareQueue: Failed to add item: $e');
      return null;
    }
  }

  /// 항목 업데이트
  Future<void> updateItem(ShareQueueItem item) async {
    try {
      final items = await loadQueue();
      final index = items.indexWhere((i) => i.id == item.id);

      if (index == -1) {
        _logger.w('ShareQueue: Item not found: ${item.id}');
        return;
      }

      items[index] = item;
      await saveQueue(items);
      _logger.d('ShareQueue: Updated item: ${item.id}');
    } catch (e) {
      _logger.e('ShareQueue: Failed to update item: $e');
      rethrow;
    }
  }

  /// 항목 삭제
  Future<void> removeItem(String id) async {
    try {
      final items = await loadQueue();
      items.removeWhere((item) => item.id == id);
      await saveQueue(items);
      _logger.i('ShareQueue: Removed item: $id');
    } catch (e) {
      _logger.e('ShareQueue: Failed to remove item: $e');
      rethrow;
    }
  }

  /// 완료된 항목 정리
  ///
  /// saved/ignored 상태인 항목들을 제거합니다.
  Future<int> cleanupCompletedItems() async {
    try {
      final items = await loadQueue();
      final beforeCount = items.length;

      items.removeWhere(
        (item) =>
            item.status == ShareQueueStatus.saved ||
            item.status == ShareQueueStatus.ignored,
      );

      await saveQueue(items);
      final removedCount = beforeCount - items.length;
      _logger.i('ShareQueue: Cleaned up $removedCount completed items');
      return removedCount;
    } catch (e) {
      _logger.e('ShareQueue: Failed to cleanup: $e');
      return 0;
    }
  }

  /// 플랫폼 감지
  String _detectPlatform(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null) return 'unknown';

    final host = uri.host.toLowerCase();
    if (host.contains('instagram.com')) return 'instagram';
    if (host.contains('blog.naver.com')) return 'naver_blog';
    if (host.contains('youtube.com') || host.contains('youtu.be')) {
      return 'youtube';
    }

    return 'unknown';
  }

  /// 지원하는 플랫폼인지 확인
  static bool isSupportedUrl(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null) return false;

    final host = uri.host.toLowerCase();
    return host.contains('instagram.com') ||
        host.contains('blog.naver.com') ||
        host.contains('youtube.com') ||
        host.contains('youtu.be');
  }

  /// 지원하는 도메인 목록
  static const List<String> supportedDomains = [
    'instagram.com',
    'blog.naver.com',
    'youtube.com',
    'youtu.be',
  ];
}
