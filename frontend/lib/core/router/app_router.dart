import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/home/presentation/screens/home_screen.dart';
import '../../features/course/presentation/screens/course_builder_screen.dart';
import '../../features/search/presentation/screens/search_screen.dart';
import '../../features/place/presentation/screens/place_detail_screen.dart';
import '../../features/profile/presentation/screens/profile_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/signup_screen.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';

/// App Router Configuration
/// Using go_router for declarative routing
final goRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    debugLogDiagnostics: true,
    redirect: (context, state) {
      final isAuthenticated = authState.status == AuthStatus.authenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/signup');

      // 인증 필요한 페이지 목록
      final protectedRoutes = ['/profile', '/courses/create'];
      final needsAuth = protectedRoutes.any(
        (route) => state.matchedLocation.startsWith(route),
      );

      // 인증 안 된 상태에서 보호된 페이지 접근 시 로그인으로
      if (!isAuthenticated && needsAuth) {
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
      // Home Screen
      GoRoute(
        path: '/',
        name: 'home',
        builder: (context, state) => const HomeScreen(),
      ),

      // Search Screen
      GoRoute(
        path: '/search',
        name: 'search',
        builder: (context, state) => const SearchScreen(),
      ),

      // Place Detail Screen
      GoRoute(
        path: '/places/:placeId',
        name: 'placeDetail',
        builder: (context, state) {
          final placeId = state.pathParameters['placeId']!;
          return PlaceDetailScreen(placeId: placeId);
        },
      ),

      // Course Builder Screen
      GoRoute(
        path: '/courses/create',
        name: 'courseCreate',
        builder: (context, state) => const CourseBuilderScreen(),
      ),

      // Course Edit Screen
      GoRoute(
        path: '/courses/:courseId/edit',
        name: 'courseEdit',
        builder: (context, state) {
          final courseId = state.pathParameters['courseId']!;
          return CourseBuilderScreen(courseId: courseId);
        },
      ),

      // Profile Screen
      GoRoute(
        path: '/profile',
        name: 'profile',
        builder: (context, state) => const ProfileScreen(),
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
