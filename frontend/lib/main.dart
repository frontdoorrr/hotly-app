import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

import 'firebase_options.dart';
import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';
import 'core/storage/local_storage.dart';
import 'core/notifications/fcm_service.dart';
import 'core/notifications/notification_handler.dart';
import 'features/link_analysis/presentation/widgets/link_input_bottom_sheet.dart';

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
    print('🗺️ Kakao Maps SDK initialized with key: $maskedKey...');
  } else {
    print('⚠️ Kakao Maps SDK key not configured');
  }

  // Initialize local storage
  await LocalStorage.instance.init();

  // Initialize FCM
  await FCMService().initialize();

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
    // TODO: Fix receive_sharing_intent API compatibility issue
    // Temporarily disabled to allow app to run
    debugPrint('⚠️ Sharing intent handler temporarily disabled');

    // Handle initial shared text (앱이 종료된 상태에서 공유받은 경우)
    // ReceiveSharingIntent.instance.getInitialText().then((String? value) {
    //   if (value != null && value.isNotEmpty) {
    //     debugPrint('📤 Initial shared text: $value');
    //     _handleSharedUrl(value);
    //     // Reset after processing
    //     ReceiveSharingIntent.instance.reset();
    //   }
    // });

    // Handle shared text stream (앱이 실행 중일 때 공유받은 경우)
    // _intentDataStreamSubscription = ReceiveSharingIntent.instance.getTextStream().listen(
    //   (String value) {
    //     if (value.isNotEmpty) {
    //       debugPrint('📤 Received shared text: $value');
    //       _handleSharedUrl(value);
    //     }
    //   },
    //   onError: (err) {
    //     debugPrint('❌ Error receiving shared text: $err');
    //   },
    // );
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
      debugPrint('✅ Valid URL detected: $url');

      // 앱이 완전히 빌드된 후 BottomSheet 표시
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          // 현재 context 가져오기
          final context = ref.read(goRouterProvider).routerDelegate.navigatorKey.currentContext;
          if (context != null) {
            LinkInputBottomSheet.show(context);
            // Provider를 통해 URL 미리 설정
            // ref.read(linkAnalysisProvider.notifier).setInputUrl(url);
          }
        }
      });
    } else {
      debugPrint('⚠️ No valid URL found in shared text');
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
    );
  }
}
