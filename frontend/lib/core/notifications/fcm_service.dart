import 'dart:async';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:logger/logger.dart';

/// FCM Service for handling push notifications
class FCMService {
  static final FCMService _instance = FCMService._internal();
  factory FCMService() => _instance;
  FCMService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  final Logger _logger = Logger();

  String? _fcmToken;
  String? get fcmToken => _fcmToken;

  // Notification tap callback
  Function(Map<String, dynamic>)? onNotificationTap;

  /// Initialize FCM service
  Future<void> initialize() async {
    try {
      // Request permission
      final settings = await _requestPermission();

      if (settings.authorizationStatus == AuthorizationStatus.authorized) {
        _logger.i('FCM: User granted notification permission');

        // Get FCM token
        await _getFCMToken();

        // Initialize local notifications
        await _initializeLocalNotifications();

        // Set up message handlers
        _setupMessageHandlers();

        _logger.i('FCM: Service initialized successfully');
      } else {
        _logger.w('FCM: User denied notification permission');
      }
    } catch (e) {
      _logger.e('FCM: Initialization failed: $e');
    }
  }

  /// Request notification permission
  Future<NotificationSettings> _requestPermission() async {
    return await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
      announcement: false,
      carPlay: false,
      criticalAlert: false,
    );
  }

  /// Get FCM token
  Future<String?> _getFCMToken() async {
    try {
      _fcmToken = await _messaging.getToken();
      _logger.i('FCM Token: $_fcmToken');

      // Listen for token refresh
      _messaging.onTokenRefresh.listen((newToken) {
        _fcmToken = newToken;
        _logger.i('FCM Token refreshed: $newToken');
        // TODO: Send updated token to backend
      });

      return _fcmToken;
    } catch (e) {
      _logger.e('Failed to get FCM token: $e');
      return null;
    }
  }

  /// Initialize local notifications for foreground display
  Future<void> _initializeLocalNotifications() async {
    const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosSettings = DarwinInitializationSettings(
      requestAlertPermission: false,
      requestBadgePermission: false,
      requestSoundPermission: false,
    );

    const initSettings = InitializationSettings(
      android: androidSettings,
      iOS: iosSettings,
    );

    await _localNotifications.initialize(
      initSettings,
      onDidReceiveNotificationResponse: (details) {
        // Handle notification tap
        if (details.payload != null) {
          _handleNotificationTap(details.payload!);
        }
      },
    );

    // Create Android notification channel
    const androidChannel = AndroidNotificationChannel(
      'high_importance_channel',
      'High Importance Notifications',
      description: 'This channel is used for important notifications.',
      importance: Importance.high,
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(androidChannel);
  }

  /// Setup message handlers
  void _setupMessageHandlers() {
    // Foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Background messages (app in background but not terminated)
    FirebaseMessaging.onMessageOpenedApp.listen(_handleBackgroundMessageTap);

    // Terminated state (app was completely closed)
    _messaging.getInitialMessage().then((message) {
      if (message != null) {
        _handleBackgroundMessageTap(message);
      }
    });
  }

  /// Handle foreground message (show local notification)
  void _handleForegroundMessage(RemoteMessage message) {
    _logger.i('Foreground message received: ${message.messageId}');

    final notification = message.notification;
    final android = message.notification?.android;

    if (notification != null) {
      _localNotifications.show(
        notification.hashCode,
        notification.title,
        notification.body,
        NotificationDetails(
          android: AndroidNotificationDetails(
            'high_importance_channel',
            'High Importance Notifications',
            channelDescription: 'This channel is used for important notifications.',
            importance: Importance.high,
            priority: Priority.high,
            icon: android?.smallIcon ?? '@mipmap/ic_launcher',
          ),
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        payload: _encodePayload(message.data),
      );
    }
  }

  /// Handle background message tap (app opened from notification)
  void _handleBackgroundMessageTap(RemoteMessage message) {
    _logger.i('Background message tapped: ${message.messageId}');
    _handleNotificationTap(_encodePayload(message.data));
  }

  /// Handle notification tap
  void _handleNotificationTap(String payload) {
    _logger.i('Notification tapped with payload: $payload');

    final data = _decodePayload(payload);

    // Call the callback if registered
    if (onNotificationTap != null) {
      onNotificationTap!(data);
    }
  }

  /// Encode payload to string
  String _encodePayload(Map<String, dynamic> data) {
    return data.entries.map((e) => '${e.key}=${e.value}').join('&');
  }

  /// Decode payload from string
  Map<String, dynamic> _decodePayload(String payload) {
    final map = <String, dynamic>{};
    for (final pair in payload.split('&')) {
      final kv = pair.split('=');
      if (kv.length == 2) {
        map[kv[0]] = kv[1];
      }
    }
    return map;
  }

  /// Subscribe to topic
  Future<void> subscribeToTopic(String topic) async {
    try {
      await _messaging.subscribeToTopic(topic);
      _logger.i('Subscribed to topic: $topic');
    } catch (e) {
      _logger.e('Failed to subscribe to topic $topic: $e');
    }
  }

  /// Unsubscribe from topic
  Future<void> unsubscribeFromTopic(String topic) async {
    try {
      await _messaging.unsubscribeFromTopic(topic);
      _logger.i('Unsubscribed from topic: $topic');
    } catch (e) {
      _logger.e('Failed to unsubscribe from topic $topic: $e');
    }
  }

  /// Send token to backend
  Future<void> sendTokenToBackend(String endpoint) async {
    if (_fcmToken == null) return;

    // TODO: Implement API call to send token to backend
    _logger.i('Sending FCM token to backend: $endpoint');
  }

  /// Delete FCM token
  Future<void> deleteToken() async {
    try {
      await _messaging.deleteToken();
      _fcmToken = null;
      _logger.i('FCM token deleted');
    } catch (e) {
      _logger.e('Failed to delete FCM token: $e');
    }
  }
}

/// Background message handler (must be top-level function)
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  final logger = Logger();
  logger.i('Background message received: ${message.messageId}');
  // Process notification in background
}
