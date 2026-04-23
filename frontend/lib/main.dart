import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';
import 'l10n/app_localizations.dart';

import 'firebase_options.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';
import 'core/storage/local_storage.dart';
import 'core/notifications/fcm_service.dart';
import 'core/notifications/notification_handler.dart';
import 'core/utils/app_logger.dart';
import 'core/monitoring/crashlytics_service.dart';
import 'features/profile/presentation/providers/settings_provider.dart';
import 'features/share_queue/presentation/providers/share_queue_provider.dart';
import 'features/share_queue/data/services/share_queue_storage_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: '.env.dev');

  // Initialize Firebase (Auth, Messaging, Analytics, Crashlytics)
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );

  // Set background message handler
  FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

  // Initialize Kakao Flutter SDK (for Kakao Login)
  KakaoSdk.init(
    nativeAppKey: dotenv.env['KAKAO_NATIVE_APP_KEY'] ?? '',
    javaScriptAppKey: dotenv.env['KAKAO_JAVASCRIPT_APP_KEY'] ?? '',
  );

  // Initialize Kakao Maps SDK
  final kakaoMapKey = dotenv.env['KAKAO_NATIVE_APP_KEY'] ?? '';
  if (kakaoMapKey.isNotEmpty) {
    KakaoMapSdk.instance.initialize(kakaoMapKey);
    final maskedKey = kakaoMapKey.length >= 8 ? kakaoMapKey.substring(0, 8) : kakaoMapKey;
    AppLogger.i('Kakao Maps SDK initialized with key: $maskedKey...', tag: 'Init');
  } else {
    AppLogger.w('Kakao Maps SDK key not configured', tag: 'Init');
  }

  // Initialize local storage
  await LocalStorage.instance.init();

  // Initialize FCM
  await FCMService().initialize();

  // Initialize Crashlytics
  await CrashlyticsService.instance.initialize();

  // Set system UI overlay style
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.dark,
    ),
  );

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  runApp(
    const ProviderScope(
      child: HotlyApp(),
    ),
  );
}

class HotlyApp extends ConsumerStatefulWidget {
  const HotlyApp({super.key});

  @override
  ConsumerState<HotlyApp> createState() => _HotlyAppState();
}

class _HotlyAppState extends ConsumerState<HotlyApp> with WidgetsBindingObserver {
  StreamSubscription? _intentDataStreamSubscription;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _setupNotificationHandler();
    _setupSharingIntentHandler();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _intentDataStreamSubscription?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // Share Extension → 앱 복귀 시 App Groups의 새 URL 로드
      ref.read(shareQueueProvider.notifier).refreshQueue();
    }
  }

  void _setupNotificationHandler() {
    // Set up notification tap handler
    FCMService().onNotificationTap = (data) {
      // Use Navigator after app is built
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          final router = ref.read(goRouterProvider);
          final route = NotificationHandler.getRouteFromPayload(data);
          if (route != null) {
            router.go(route);
          }
        }
      });
    };
  }

  void _setupSharingIntentHandler() {
    // 앱 시작 시 ShareQueue 새로고침 (App Groups에서 데이터 로드)
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        ref.read(shareQueueProvider.notifier).refreshQueue();
      }
    });

    // Handle initial shared media (앱이 종료된 상태에서 공유받은 경우)
    ReceiveSharingIntent.instance.getInitialMedia().then((List<SharedMediaFile> mediaFiles) {
      if (mediaFiles.isNotEmpty) {
        for (final file in mediaFiles) {
          final value = file.path;
          if (value.isNotEmpty) {
            AppLogger.d('📤 Initial shared media: $value (type: ${file.type})', tag: 'Share');
            _handleSharedUrl(value);
          }
        }
        // Reset after processing
        ReceiveSharingIntent.instance.reset();
      }
    });

    // Handle shared media stream (앱이 실행 중일 때 공유받은 경우)
    _intentDataStreamSubscription = ReceiveSharingIntent.instance.getMediaStream().listen(
      (List<SharedMediaFile> mediaFiles) {
        for (final file in mediaFiles) {
          final value = file.path;
          if (value.isNotEmpty) {
            AppLogger.d('📤 Received shared media: $value (type: ${file.type})', tag: 'Share');
            _handleSharedUrl(value);
          }
        }
      },
      onError: (err) {
        AppLogger.e('❌ Error receiving shared media: $err', tag: 'Share');
      },
    );
  }

  void _handleSharedUrl(String text) {
    final urlPattern = RegExp(
      r'https?:\/\/(www\.)?(instagram\.com|naver\.com|blog\.naver\.com|youtube\.com|youtu\.be)\/[^\s]+',
      caseSensitive: false,
    );

    final match = urlPattern.firstMatch(text);
    if (match == null) {
      AppLogger.w('No valid URL found in shared text', tag: 'Share');
      return;
    }

    final url = match.group(0)!;
    AppLogger.d('Valid URL detected: $url', tag: 'Share');

    if (!ShareQueueStorageService.isSupportedUrl(url)) {
      AppLogger.w('Unsupported URL platform: $url', tag: 'Share');
      return;
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;

      ref.read(shareQueueProvider.notifier).addUrl(url).then((result) {
        if (!mounted) return;

        if (result == AddUrlResult.duplicate) {
          AppLogger.w('Duplicate URL, skipping: $url', tag: 'Share');
          FCMService().showLocalNotification(
            id: 1002,
            title: '이미 추가된 링크',
            body: '이 링크는 이미 분석 목록에 있어요.',
          );
          return;
        }

        AppLogger.i('URL added to share queue: $url', tag: 'Share');

        // 홈 탭으로 이동하여 배지가 보이도록
        final router = ref.read(goRouterProvider);
        router.go('/');

        // 분석 자동 시작
        if (result == AddUrlResult.added) {
          Future.delayed(const Duration(milliseconds: 300), () {
            if (mounted) {
              ref.read(shareQueueProvider.notifier).processBatch();
            }
          });
        }
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(goRouterProvider);
    final settings = ref.watch(settingsProvider);

    return MaterialApp.router(
      title: 'Hotly',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: settings.themeMode,
      routerConfig: router,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('ko'),
        Locale('en'),
      ],
      locale: Locale(settings.language),
    );
  }
}
