# Task 07: Frontend Development - Phase 4 상세 참고 (Supabase Auth)

## Phase 4: 인증 및 온보딩 - Supabase Auth

### 4.1 Supabase Auth 인증 플로우 🔐

**📚 참고 문서**:
- 화면 스펙: `docs/screens/auth-screen-spec.md`
- Backend: Supabase Auth (Self-hosted or Cloud)
- Supabase Docs: https://supabase.com/docs/guides/auth

**🔌 Supabase Auth API**:
```
POST   /auth/v1/signup                          # 이메일 회원가입
POST   /auth/v1/token?grant_type=password       # 이메일 로그인
POST   /auth/v1/logout                          # 로그아웃
POST   /auth/v1/recover                         # 비밀번호 재설정
GET    /auth/v1/user                            # 현재 사용자 정보
POST   /auth/v1/otp                             # OTP 인증 (이메일 확인)

# OAuth
GET    /auth/v1/authorize?provider=google       # Google OAuth
GET    /auth/v1/authorize?provider=apple        # Apple OAuth
GET    /auth/v1/callback                        # OAuth Callback
```

**📦 Flutter 패키지**:
```yaml
dependencies:
  supabase_flutter: ^2.3.0      # Supabase Auth + Realtime
  flutter_dotenv: ^5.1.0         # 환경 변수 관리
  google_sign_in: ^6.2.1         # Google OAuth (Optional)
  sign_in_with_apple: ^5.0.0     # Apple OAuth (Optional)
```

---

### 4.2 Supabase 프로젝트 설정

**Supabase Dashboard 설정**:
1. Supabase 프로젝트 생성
2. **Settings → API** 에서 확인:
   - Project URL: `https://xxxxx.supabase.co`
   - anon/public key: `eyJhbG...` (공개키)
   - service_role key: `eyJhbG...` (서버용, 사용 X)

3. **Authentication → Providers** 설정:
   - Email: Enabled (이메일 확인 필수 설정 가능)
   - Google: OAuth 클라이언트 ID/Secret 설정
   - Apple: OAuth 설정

4. **Authentication → URL Configuration**:
   - Site URL: `com.example.hotly://`
   - Redirect URLs 추가:
     - `com.example.hotly://login-callback`
     - `com.example.hotly://reset-password`

---

### 4.3 환경 변수 설정

`.env.dev`:
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here

# OAuth Redirect (Deep Link)
REDIRECT_URL=com.example.hotly://login-callback
```

`.env.prod`:
```bash
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_ANON_KEY=your-prod-anon-key
REDIRECT_URL=com.example.hotly://login-callback
```

**main.dart 초기화**:
```dart
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load .env
  await dotenv.load(fileName: ".env.dev");

  // Initialize Supabase
  await Supabase.initialize(
    url: dotenv.env['SUPABASE_URL']!,
    anonKey: dotenv.env['SUPABASE_ANON_KEY']!,
    authOptions: const FlutterAuthClientOptions(
      authFlowType: AuthFlowType.pkce,
    ),
  );

  // Initialize LocalStorage
  await LocalStorage.instance.init();

  runApp(const ProviderScope(child: MyApp()));
}
```

---

### 4.4 User 모델 확장

**기존 User 모델 확장** (`lib/shared/models/user.dart`):
```dart
@freezed
class User with _$User {
  const factory User({
    required String id,              // Supabase user.id (UUID)
    required String name,
    required String email,
    String? profileImageUrl,
    String? phoneNumber,

    // Supabase 추가 필드
    @Default(false) bool emailConfirmed,
    String? provider,                 // 'email', 'google', 'apple'
    Map<String, dynamic>? metadata,   // user_metadata
    DateTime? lastSignInAt,

    // 앱 통계
    @Default(0) int savedPlacesCount,
    @Default(0) int likedPlacesCount,
    @Default(0) int coursesCount,
    DateTime? createdAt,
  }) = _User;

  factory User.fromJson(Map<String, dynamic> json) => _$UserFromJson(json);

  factory User.initial() => const User(
        id: '',
        name: 'Guest',
        email: 'guest@example.com',
      );

  // Supabase User → App User 변환
  factory User.fromSupabase(SupabaseUser supabaseUser) {
    return User(
      id: supabaseUser.id,
      email: supabaseUser.email ?? '',
      name: supabaseUser.userMetadata?['name'] ??
            supabaseUser.email?.split('@').first ?? 'User',
      profileImageUrl: supabaseUser.userMetadata?['avatar_url'],
      phoneNumber: supabaseUser.phone,
      emailConfirmed: supabaseUser.emailConfirmedAt != null,
      provider: supabaseUser.appMetadata['provider'],
      metadata: supabaseUser.userMetadata,
      lastSignInAt: supabaseUser.lastSignInAt,
      createdAt: supabaseUser.createdAt,
    );
  }
}
```

---

### 4.5 AuthRepository 구현 예시

**Repository 구현** (`lib/features/auth/data/repositories/auth_repository_impl.dart`):

```dart
class AuthRepositoryImpl implements AuthRepository {
  final SupabaseClient _supabase;

  AuthRepositoryImpl(this._supabase);

  @override
  User? get currentUser {
    final supabaseUser = _supabase.auth.currentUser;
    if (supabaseUser == null) return null;
    return User.fromSupabase(supabaseUser);
  }

  @override
  Stream<User?> get authStateChanges {
    return _supabase.auth.onAuthStateChange.map((event) {
      final user = event.session?.user;
      if (user == null) return null;
      return User.fromSupabase(user);
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

      return Right(User.fromSupabase(response.user!));
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: _getStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(
        message: '알 수 없는 오류가 발생했습니다',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  }) async {
    try {
      final response = await _supabase.auth.signUp(
        email: email,
        password: password,
        data: {
          'name': name,
        },
      );

      if (response.user == null) {
        return Left(ApiException(
          message: '회원가입에 실패했습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromSupabase(response.user!));
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
        statusCode: _getStatusCode(e),
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithGoogle() async {
    try {
      final response = await _supabase.auth.signInWithOAuth(
        Provider.google,
        redirectTo: dotenv.env['REDIRECT_URL'],
      );

      if (!response) {
        return Left(ApiException(
          message: 'Google 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      // OAuth는 비동기로 처리되므로 authStateChanges에서 감지
      // 여기서는 성공 여부만 반환
      return Right(currentUser ?? User.initial());
    } on AuthException catch (e) {
      return Left(ApiException(
        message: _getErrorMessage(e),
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

  @override
  Future<Either<ApiException, void>> resetPassword(String email) async {
    try {
      await _supabase.auth.resetPasswordForEmail(
        email,
        redirectTo: '${dotenv.env['REDIRECT_URL']}/reset-password',
      );
      return const Right(null);
    } on AuthException catch (e) {
      return Left(ApiException(
        message: e.message,
        statusCode: 400,
      ));
    }
  }

  String _getErrorMessage(AuthException e) {
    switch (e.message) {
      case 'Invalid login credentials':
        return '이메일 또는 비밀번호가 올바르지 않습니다';
      case 'Email not confirmed':
        return '이메일 인증이 필요합니다';
      case 'User already registered':
        return '이미 가입된 이메일입니다';
      default:
        return e.message;
    }
  }

  int _getStatusCode(AuthException e) {
    if (e.statusCode != null) {
      return int.tryParse(e.statusCode!) ?? 500;
    }
    return 500;
  }
}
```

---

### 4.6 Deep Link 설정 (OAuth Callback)

**Android** (`android/app/src/main/AndroidManifest.xml`):
```xml
<activity
    android:name=".MainActivity"
    ...>
    <!-- Deep Link for OAuth -->
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="com.example.hotly"
            android:host="login-callback" />
    </intent-filter>
</activity>
```

**iOS** (`ios/Runner/Info.plist`):
```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleTypeRole</key>
        <string>Editor</string>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>com.example.hotly</string>
        </array>
    </dict>
</array>
```

---

### 4.7 AuthState Provider 구현

**Provider** (`lib/features/auth/presentation/providers/auth_provider.dart`):

```dart
@freezed
class AuthState with _$AuthState {
  const factory AuthState({
    User? user,
    @Default(AuthStatus.initial) AuthStatus status,
    @Default(false) bool isLoading,
    ApiException? error,
  }) = _AuthState;
}

enum AuthStatus {
  initial,        // 초기 상태
  authenticated,  // 로그인됨
  unauthenticated, // 로그인 안 됨
}

class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;
  StreamSubscription<User?>? _authSubscription;

  AuthNotifier(this._repository) : super(const AuthState()) {
    _checkInitialAuth();
    _listenToAuthChanges();
  }

  Future<void> _checkInitialAuth() async {
    final currentUser = _repository.currentUser;
    state = state.copyWith(
      user: currentUser,
      status: currentUser != null
          ? AuthStatus.authenticated
          : AuthStatus.unauthenticated,
    );
  }

  void _listenToAuthChanges() {
    _authSubscription = _repository.authStateChanges.listen((user) {
      state = state.copyWith(
        user: user,
        status: user != null
            ? AuthStatus.authenticated
            : AuthStatus.unauthenticated,
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
          status: AuthStatus.unauthenticated,
        );
      },
      (user) {
        state = state.copyWith(
          isLoading: false,
          user: user,
          status: AuthStatus.authenticated,
          error: null,
        );
      },
    );
  }

  Future<void> signUpWithEmail({
    required String email,
    required String password,
    required String name,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    final result = await _repository.signUpWithEmail(
      email: email,
      password: password,
      name: name,
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
          status: user.emailConfirmed
              ? AuthStatus.authenticated
              : AuthStatus.unauthenticated,
          error: null,
        );
      },
    );
  }

  Future<void> signInWithGoogle() async {
    state = state.copyWith(isLoading: true, error: null);
    final result = await _repository.signInWithGoogle();

    result.fold(
      (error) {
        state = state.copyWith(
          isLoading: false,
          error: error,
        );
      },
      (_) {
        // OAuth는 authStateChanges에서 자동으로 상태 업데이트
        state = state.copyWith(isLoading: false);
      },
    );
  }

  Future<void> signOut() async {
    await _repository.signOut();
    state = const AuthState(status: AuthStatus.unauthenticated);
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

// Helper for checking auth status
final isAuthenticatedProvider = Provider<bool>((ref) {
  return ref.watch(authProvider).status == AuthStatus.authenticated;
});
```

---

### 4.8 Router Auth Guard

**go_router with redirect** (`lib/core/router/app_router.dart`):

```dart
final goRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authProvider);

  return GoRouter(
    initialLocation: '/',
    refreshListenable: _GoRouterRefreshStream(
      ref.read(authProvider.notifier).stream,
    ),
    redirect: (context, state) {
      final isAuthenticated = authState.status == AuthStatus.authenticated;
      final isAuthRoute = state.matchedLocation.startsWith('/login') ||
          state.matchedLocation.startsWith('/signup');

      // 인증 필요한 페이지 목록
      final protectedRoutes = [
        '/profile',
        '/courses/create',
        '/places/saved',
      ];

      final needsAuth = protectedRoutes.any(
        (route) => state.matchedLocation.startsWith(route),
      );

      // 인증 안 된 상태에서 보호된 페이지 접근
      if (!isAuthenticated && needsAuth) {
        return '/login?redirect=${state.matchedLocation}';
      }

      // 인증된 상태에서 로그인 페이지 접근
      if (isAuthenticated && isAuthRoute) {
        final redirect = state.uri.queryParameters['redirect'];
        return redirect ?? '/';
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

// Helper class for GoRouter refresh
class _GoRouterRefreshStream extends ChangeNotifier {
  _GoRouterRefreshStream(Stream<AuthState> stream) {
    notifyListeners();
    _subscription = stream.listen((_) {
      notifyListeners();
    });
  }

  late final StreamSubscription<AuthState> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
```

---

### 4.9 Supabase Row Level Security (RLS)

**Backend 측 Supabase 설정** (SQL):

```sql
-- User profiles 테이블
CREATE TABLE user_profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- RLS 활성화
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 자기 프로필만 읽기 가능
CREATE POLICY "Users can read own profile"
  ON user_profiles FOR SELECT
  USING (auth.uid() = id);

-- 자기 프로필만 수정 가능
CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  USING (auth.uid() = id);
```

---

## 요약

Supabase Auth는 Firebase Auth와 유사하지만:
- ✅ **오픈소스** - 자체 호스팅 가능
- ✅ **PostgreSQL 기반** - RLS로 데이터 보안
- ✅ **OAuth 통합** - Google, Apple, GitHub 등
- ✅ **JWT 기반** - API 인증 토큰
- ✅ **Realtime 지원** - WebSocket 구독

Flutter 통합:
1. `supabase_flutter` 패키지 사용
2. `main.dart`에서 초기화
3. `AuthRepository` 구현
4. `AuthState Provider`로 전역 상태 관리
5. `go_router` redirect로 라우팅 보호

---

*작성일: 2025-01-XX*
*Backend: Supabase Auth*
