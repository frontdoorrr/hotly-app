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
import 'features/link_analysis/presentation/widgets/link_input_bottom_sheet.dart';
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

class _HotlyAppState extends ConsumerState<HotlyApp> {
  StreamSubscription? _intentDataStreamSubscription;

  @override
  void initState() {
    super.initState();
    _setupNotificationHandler();
    _setupSharingIntentHandler();
  }

  @override
  void dispose() {
    _intentDataStreamSubscription?.cancel();
    super.dispose();
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
    // URL 패턴 검증
    final urlPattern = RegExp(
      r'https?:\/\/(www\.)?(instagram\.com|naver\.com|blog\.naver\.com|youtube\.com|youtu\.be)\/[^\s]+',
      caseSensitive: false,
    );

    final match = urlPattern.firstMatch(text);
    if (match != null) {
      final url = match.group(0)!;
      AppLogger.d('Valid URL detected: $url', tag: 'Share');

      // 지원하는 URL인지 확인
      if (!ShareQueueStorageService.isSupportedUrl(url)) {
        AppLogger.w('Unsupported URL platform: $url', tag: 'Share');
        return;
      }

      // ShareQueue에 추가
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          ref.read(shareQueueProvider.notifier).addUrl(url);
          AppLogger.i('URL added to share queue: $url', tag: 'Share');
        }
      });
    } else {
      AppLogger.w('No valid URL found in shared text', tag: 'Share');
    }
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(goRouterProvider);

    return MaterialApp.router(
      title: 'Hotly',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.system,
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
      locale: const Locale('ko'),
    );
  }
}
