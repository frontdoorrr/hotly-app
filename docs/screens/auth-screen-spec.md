# 인증 화면 스펙 (Authentication Screen Specification)

## 문서 정보
- **화면명**: 로그인/회원가입 화면 (Auth Screens)
- **라우트**: `/login`, `/signup`
- **버전**: 1.0
- **작성일**: 2025-01-XX
- **Backend**: Supabase Auth

---

## 1. 화면 목적

- Supabase Auth를 통한 사용자 인증
- 이메일/비밀번호 로그인/회원가입
- OAuth 소셜 로그인 (Google, Apple)
- 인증 상태 전역 관리

---

## 2. 와이어프레임

### 2.1 로그인 화면

```
┌─────────────────────────────────────┐
│                                     │
│         [앱 로고]                   │
│                                     │
│         Hotly                       │
│    AI 기반 핫플 아카이빙            │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 이메일                      │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 비밀번호              [👁]  │   │
│  └─────────────────────────────┘   │
│                                     │
│              비밀번호 찾기          │
│                                     │
│  ┌─────────────────────────────┐   │
│  │        로그인               │   │
│  └─────────────────────────────┘   │
│                                     │
│         또는 소셜 로그인으로         │
│                                     │
│  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │  🔴  │  │  🍎  │  │  📧  │     │ ← Google, Apple, Email
│  └──────┘  └──────┘  └──────┘     │
│                                     │
│  계정이 없으신가요? [회원가입]      │
│                                     │
└─────────────────────────────────────┘
```

### 2.2 회원가입 화면

```
┌─────────────────────────────────────┐
│  ← 회원가입                         │
├─────────────────────────────────────┤
│                                     │
│  이름                               │
│  ┌─────────────────────────────┐   │
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
│  이메일                             │
│  ┌─────────────────────────────┐   │
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
│  비밀번호 (8자 이상)                │
│  ┌─────────────────────────────┐   │
│  │                       [👁]  │   │
│  └─────────────────────────────┘   │
│                                     │
│  비밀번호 확인                       │
│  ┌─────────────────────────────┐   │
│  │                       [👁]  │   │
│  └─────────────────────────────┘   │
│                                     │
│  ☑ [이용약관] 및 [개인정보처리방침] │
│     에 동의합니다.                  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │        가입하기             │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

## 3. Flutter 위젯 트리

### 3.1 LoginScreen

```dart
LoginScreen (ConsumerStatefulWidget)
└─ Scaffold
   └─ SafeArea
      └─ SingleChildScrollView
         └─ Padding
            └─ Column
               ├─ Logo & Title
               ├─ EmailTextField
               ├─ PasswordTextField
               ├─ ForgotPasswordButton
               ├─ LoginButton
               ├─ Divider ("또는 소셜 로그인으로")
               ├─ SocialLoginButtons (Google, Apple)
               └─ SignUpPrompt
```

### 3.2 SignUpScreen

```dart
SignUpScreen (ConsumerStatefulWidget)
└─ Scaffold
   ├─ AppBar (← 뒤로가기)
   └─ SafeArea
      └─ SingleChildScrollView
         └─ Padding
            └─ Form
               └─ Column
                  ├─ NameTextField
                  ├─ EmailTextField
                  ├─ PasswordTextField
                  ├─ PasswordConfirmTextField
                  ├─ TermsCheckbox
                  └─ SignUpButton
```

---

## 4. Supabase Auth 연동

### 4.1 Supabase 초기화

```dart
// lib/core/auth/supabase_client.dart
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SupabaseService {
  static SupabaseClient? _client;

  static Future<void> initialize({
    required String url,
    required String anonKey,
  }) async {
    await Supabase.initialize(
      url: url,
      anonKey: anonKey,
    );
    _client = Supabase.instance.client;
  }

  static SupabaseClient get client {
    if (_client == null) {
      throw Exception('Supabase not initialized');
    }
    return _client!;
  }
}

final supabaseClientProvider = Provider<SupabaseClient>((ref) {
  return SupabaseService.client;
});
```

### 4.2 AuthRepository 인터페이스

```dart
// lib/features/auth/domain/repositories/auth_repository.dart
import 'package:dartz/dartz.dart';
import '../../../../shared/models/user.dart';
import '../../../../core/network/api_exception.dart';

abstract class AuthRepository {
  /// 현재 로그인된 사용자 조회
  User? get currentUser;

  /// 인증 상태 스트림
  Stream<User?> get authStateChanges;

  /// 이메일/비밀번호 로그인
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  });

  /// 이메일/비밀번호 회원가입
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  });

  /// Google OAuth 로그인
  Future<Either<ApiException, User>> signInWithGoogle();

  /// Apple OAuth 로그인
  Future<Either<ApiException, User>> signInWithApple();

  /// 로그아웃
  Future<Either<ApiException, void>> signOut();

  /// 비밀번호 재설정 이메일 전송
  Future<Either<ApiException, void>> resetPassword(String email);
}
```

### 4.3 AuthRepository 구현

```dart
// lib/features/auth/data/repositories/auth_repository_impl.dart
class AuthRepositoryImpl implements AuthRepository {
  final SupabaseClient _supabase;

  AuthRepositoryImpl(this._supabase);

  @override
  User? get currentUser {
    final supabaseUser = _supabase.auth.currentUser;
    if (supabaseUser == null) return null;

    return User(
      id: supabaseUser.id,
      email: supabaseUser.email ?? '',
      name: supabaseUser.userMetadata?['name'] ?? 'User',
      profileImageUrl: supabaseUser.userMetadata?['avatar_url'],
    );
  }

  @override
  Stream<User?> get authStateChanges {
    return _supabase.auth.onAuthStateChange.map((event) {
      final supabaseUser = event.session?.user;
      if (supabaseUser == null) return null;

      return User(
        id: supabaseUser.id,
        email: supabaseUser.email ?? '',
        name: supabaseUser.userMetadata?['name'] ?? 'User',
        profileImageUrl: supabaseUser.userMetadata?['avatar_url'],
      );
    });
  }

  @override
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _supabase.auth.signInWithPassword(
        email: email,
        password: password,
      );

      if (response.user == null) {
        return Left(ApiException(
          message: '로그인에 실패했습니다',
          statusCode: 401,
        ));
      }

      return Right(User(
        id: response.user!.id,
        email: response.user!.email ?? '',
        name: response.user!.userMetadata?['name'] ?? 'User',
      ));
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: e.statusCode != null ? int.parse(e.statusCode!) : 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithGoogle() async {
    try {
      await _supabase.auth.signInWithOAuth(
        Provider.google,
        redirectTo: 'com.example.hotly://login-callback',
      );

      // OAuth는 비동기로 처리되므로 authStateChanges에서 감지
      return Right(currentUser ?? User.initial());
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> signOut() async {
    try {
      await _supabase.auth.signOut();
      return const Right(null);
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: 500,
      ));
    }
  }
}
```

---

## 5. 상태 관리

### 5.1 Auth State Provider

```dart
// lib/features/auth/presentation/providers/auth_provider.dart
@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    User? user,
    @Default(false) bool isLoading,
    @Default(false) bool isAuthenticated,
    ApiException? error,
  }) = _AuthState;
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;
  StreamSubscription<User?>? _authSubscription;

  AuthNotifier(this._repository) : super(const AuthState()) {
    _listenToAuthChanges();
  }

  void _listenToAuthChanges() {
    _authSubscription = _repository.authStateChanges.listen((user) {
      state = state.copyWith(
        user: user,
        isAuthenticated: user != null,
      );
    });
  }

  Future<void> signInWithEmail({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.signInWithEmail(
      email: email,
      password: password,
    );

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (user) {
        state = state.copyWith(
          isLoading: false,
          user: user,
          isAuthenticated: true,
          error: null,
        );
      },
    );
  }

  Future<void> signOut() async {
    await _repository.signOut();
    state = const AuthState();
  }

  @override
  void dispose() {
    _authSubscription?.cancel();
    super.dispose();
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.watch(authRepositoryProvider);
  return AuthNotifier(repository);
});
```

---

## 6. 라우팅 보호 (Auth Guard)

```dart
// lib/core/router/app_router.dart
final goRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    redirect: (context, state) {
      final isAuthenticated = authState.isAuthenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/signup');

      // 인증 필요한 페이지 목록
      final protectedRoutes = ['/profile', '/courses/create'];
      final needsAuth = protectedRoutes.any(
        (route) => state.matchedLocation.startsWith(route),
      );

      // 인증 안 된 상태에서 보호된 페이지 접근 시 로그인으로
      if (!isAuthenticated && needsAuth) {
        return '/login';
      }

      // 인증된 상태에서 로그인 페이지 접근 시 홈으로
      if (isAuthenticated && isAuthRoute) {
        return '/';
      }

      return null; // No redirect
    },
    routes: [
      // ... existing routes
      GoRoute(
        path: '/login',
        name: 'login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/signup',
        name: 'signup',
        builder: (context, state) => const SignUpScreen(),
      ),
    ],
  );
});
```

---

## 7. 환경 변수 설정

```dart
// .env.dev
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

// .env.prod
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

```dart
// lib/main.dart
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load environment variables
  await dotenv.load(fileName: ".env.dev");

  // Initialize Supabase
  await SupabaseService.initialize(
    url: dotenv.env['SUPABASE_URL']!,
    anonKey: dotenv.env['SUPABASE_ANON_KEY']!,
  );

  // Initialize LocalStorage
  await LocalStorage.instance.init();

  runApp(const ProviderScope(child: MyApp()));
}
```

---

## 8. 완료 정의 (DoD)

- [ ] Supabase Auth 클라이언트 초기화
- [ ] 이메일/비밀번호 로그인 화면
- [ ] 이메일/비밀번호 회원가입 화면
- [ ] Google OAuth 로그인
- [ ] Apple OAuth 로그인
- [ ] 비밀번호 재설정 플로우
- [ ] Auth State Provider (전역 인증 상태)
- [ ] Auth Guard (라우팅 보호)
- [ ] 로그아웃 기능
- [ ] 에러 핸들링 (잘못된 이메일/비밀번호 등)

---

## 9. 수용 기준

- **Given** 앱 첫 실행
- **When** 로그인 화면 표시
- **Then** 이메일/비밀번호 입력 및 소셜 로그인 버튼 표시

- **Given** 유효한 이메일/비밀번호 입력
- **When** 로그인 버튼 클릭
- **Then** 인증 성공 후 홈 화면으로 이동, AuthState 업데이트

- **Given** 로그인된 상태
- **When** 로그아웃 버튼 클릭
- **Then** Supabase 세션 종료, 로그인 화면으로 이동

- **Given** 비로그인 상태
- **When** 프로필 화면 접근 시도
- **Then** 자동으로 로그인 화면으로 리다이렉트

---

*작성일: 2025-01-XX*
*작성자: Claude*
*버전: 1.0*
*Backend: Supabase Auth*
