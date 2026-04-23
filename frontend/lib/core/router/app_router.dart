import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/archive/presentation/screens/archive_detail_screen.dart';
import '../../features/discover/presentation/screens/discover_screen.dart';
import '../../features/home/presentation/screens/home_screen.dart';
import '../../features/plan/presentation/screens/plan_screen.dart';
import '../../features/course/presentation/screens/course_builder_screen.dart';
import '../../features/search/presentation/screens/search_screen.dart';
import '../../features/place/presentation/screens/place_detail_screen.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../features/profile/presentation/screens/profile_edit_screen.dart';
import '../../features/map/presentation/screens/map_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/signup_screen.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/onboarding/presentation/screens/onboarding_screen.dart';
import '../../features/onboarding/presentation/providers/onboarding_provider.dart';
import '../../features/share_queue/presentation/screens/share_queue_results_screen.dart';
import 'main_shell_screen.dart';

/// App Router Configuration
/// Using go_router for declarative routing
final goRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);
  final isOnboardingCompleted = ref.watch(isOnboardingCompletedProvider);

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isAuthenticated = authState.status == AuthStatus.authenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/signup');
      final isOnboardingRoute = state.matchedLocation == '/onboarding';

      // 온보딩 미완료 시 온보딩으로 리다이렉트 (인증 화면 제외)
      if (!isOnboardingCompleted && !isOnboardingRoute && !isAuthRoute) {
        return '/onboarding';
      }

      // 온보딩 완료 후 온보딩 페이지 접근 시 홈으로
      if (isOnboardingCompleted && isOnboardingRoute) {
        return '/';
      }

      // 인증 안 된 상태에서 인증/온보딩 외 모든 페이지 → 로그인으로
      if (!isAuthenticated && !isAuthRoute && !isOnboardingRoute) {
        return '/login?redirect=${state.matchedLocation}';
      }

      // 인증된 상태에서 로그인 페이지 접근 시 홈으로
      if (isAuthenticated && isAuthRoute) {
        final redirect = state.uri.queryParameters['redirect'];
        return redirect ?? '/';
      }

      return null; // No redirect
    },
    routes: [
      // Main Shell with Bottom Navigation
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return MainShellScreen(
            currentIndex: navigationShell.currentIndex,
            child: navigationShell,
          );
        },
        branches: [
          // Home Tab
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/',
                name: 'home',
                builder: (context, state) => const HomeScreen(),
              ),
            ],
          ),

          // Discover Tab
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/discover',
                name: 'discover',
                builder: (context, state) => const DiscoverScreen(),
              ),
            ],
          ),

          // Plan Tab
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/plan',
                name: 'plan',
                builder: (context, state) => const PlanScreen(),
              ),
            ],
          ),

          // Map Tab
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/map',
                name: 'map',
                builder: (context, state) => const MapScreen(),
              ),
            ],
          ),

          // Profile Tab
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                name: 'profile',
                builder: (context, state) => const ProfileScreen(),
              ),
            ],
          ),
        ],
      ),

      // Archive Detail Screen (outside bottom nav)
      GoRoute(
        path: '/archive/:archiveId',
        name: 'archiveDetail',
        pageBuilder: (context, state) {
          final id = state.pathParameters['archiveId']!;
          return _detailTransitionPage(
            state: state,
            child: ArchiveDetailScreen(archiveId: id),
          );
        },
      ),

      // Search Screen (outside bottom nav) — modal style
      GoRoute(
        path: '/search',
        name: 'search',
        pageBuilder: (context, state) => _modalTransitionPage(
          state: state,
          child: const SearchScreen(),
        ),
      ),

      // Place Detail Screen (outside bottom nav)
      GoRoute(
        path: '/places/:placeId',
        name: 'placeDetail',
        pageBuilder: (context, state) {
          final placeId = state.pathParameters['placeId']!;
          return _detailTransitionPage(
            state: state,
            child: PlaceDetailScreen(placeId: placeId),
          );
        },
      ),

      // Course Builder Screen (outside bottom nav)
      GoRoute(
        path: '/courses/create',
        name: 'courseCreate',
        pageBuilder: (context, state) => _detailTransitionPage(
          state: state,
          child: const CourseBuilderScreen(),
        ),
      ),

      // Course Edit Screen (outside bottom nav)
      GoRoute(
        path: '/courses/:courseId/edit',
        name: 'courseEdit',
        pageBuilder: (context, state) {
          final courseId = state.pathParameters['courseId']!;
          return _detailTransitionPage(
            state: state,
            child: CourseBuilderScreen(courseId: courseId),
          );
        },
      ),

      // Login Screen
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),

      // Sign Up Screen
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (context, state) => const SignUpScreen(),
      ),

      // Profile Edit Screen
      GoRoute(
        path: '/profile/edit',
        name: 'profileEdit',
        pageBuilder: (context, state) => _detailTransitionPage(
          state: state,
          child: const ProfileEditScreen(),
        ),
      ),

      // Onboarding Screen
      GoRoute(
        path: '/onboarding',
        name: 'onboarding',
        builder: (context, state) => const OnboardingScreen(),
      ),

      // Share Queue Results Screen — modal style
      GoRoute(
        path: '/share-queue/results',
        name: 'shareQueueResults',
        pageBuilder: (context, state) => _modalTransitionPage(
          state: state,
          child: const ShareQueueResultsScreen(),
        ),
      ),
    ],

    // Error Handler
    errorBuilder: (context, state) => Scaffold(
      appBar: AppBar(title: const Text('Page Not Found')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64),
            const SizedBox(height: 16),
            Text('Error: ${state.error}'),
          ],
        ),
      ),
    ),
  );
});

/// 상세 화면 전환: fade + 미세한 slideY
CustomTransitionPage<void> _detailTransitionPage({
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<void>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 300),
    reverseTransitionDuration: const Duration(milliseconds: 250),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final curved = CurvedAnimation(parent: animation, curve: Curves.easeOut);
      return FadeTransition(
        opacity: curved,
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0, 0.04),
            end: Offset.zero,
          ).animate(curved),
          child: child,
        ),
      );
    },
  );
}

/// 모달성 화면 전환: fade + scale-up
CustomTransitionPage<void> _modalTransitionPage({
  required GoRouterState state,
  required Widget child,
}) {
  return CustomTransitionPage<void>(
    key: state.pageKey,
    child: child,
    transitionDuration: const Duration(milliseconds: 300),
    reverseTransitionDuration: const Duration(milliseconds: 250),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      final curved = CurvedAnimation(parent: animation, curve: Curves.easeOut);
      return FadeTransition(
        opacity: curved,
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.97, end: 1.0).animate(curved),
          child: child,
        ),
      );
    },
  );
}
