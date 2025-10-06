import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:kakao_map_plugin/kakao_map_plugin.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import 'core/theme/app_theme.dart';
import 'core/router/app_router.dart';
import 'core/storage/local_storage.dart';
import 'core/auth/supabase_service.dart';
import 'core/notifications/fcm_service.dart';
import 'core/notifications/notification_handler.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: '.env.dev');

  // Initialize Firebase
  await Firebase.initializeApp();

  // Set background message handler
  FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);

  // Initialize Kakao Map
  AuthRepository.initialize(appKey: dotenv.env['KAKAO_MAP_APP_KEY'] ?? '');

  // Initialize Supabase
  await SupabaseService.initialize(
    url: dotenv.env['SUPABASE_URL'] ?? '',
    anonKey: dotenv.env['SUPABASE_ANON_KEY'] ?? '',
  );

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
  @override
  void initState() {
    super.initState();
    _setupNotificationHandler();
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
