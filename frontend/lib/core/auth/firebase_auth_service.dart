import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:sign_in_with_apple/sign_in_with_apple.dart';
import 'package:kakao_flutter_sdk_user/kakao_flutter_sdk_user.dart' as kakao;
import 'package:logger/logger.dart';

/// Firebase Authentication 서비스
///
/// Firebase Auth를 사용하여 다양한 소셜 로그인을 처리합니다.
/// - Google Sign-In
/// - Apple Sign-In
/// - Kakao Sign-In (Custom OAuth)
class FirebaseAuthService {
  final FirebaseAuth _firebaseAuth;
  final GoogleSignIn _googleSignIn;
  final Logger _logger;

  FirebaseAuthService({
    FirebaseAuth? firebaseAuth,
    GoogleSignIn? googleSignIn,
    Logger? logger,
  })  : _firebaseAuth = firebaseAuth ?? FirebaseAuth.instance,
        _googleSignIn = googleSignIn ?? GoogleSignIn(),
        _logger = logger ?? Logger();

  /// 현재 로그인된 사용자
  User? get currentUser => _firebaseAuth.currentUser;

  /// 인증 상태 스트림
  Stream<User?> get authStateChanges => _firebaseAuth.authStateChanges();

  /// 사용자 ID 스트림
  Stream<User?> get userChanges => _firebaseAuth.userChanges();

  /// 현재 사용자의 ID Token 가져오기 (API 호출 시 사용)
  Future<String?> getIdToken({bool forceRefresh = false}) async {
    try {
      final user = currentUser;
      if (user == null) return null;

      return await user.getIdToken(forceRefresh);
    } catch (e, stackTrace) {
      _logger.e('Failed to get ID token', error: e, stackTrace: stackTrace);
      return null;
    }
  }

  /// Email/Password Sign-In
  Future<UserCredential?> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      _logger.i('Signing in with email: $email');

      final credential = await _firebaseAuth.signInWithEmailAndPassword(
        email: email,
        password: password,
      );

      _logger.i('Successfully signed in with email: ${credential.user?.email}');
      return credential;
    } on FirebaseAuthException catch (e, stackTrace) {
      _logger.e('Email sign-in failed', error: e, stackTrace: stackTrace);
      rethrow;
    } catch (e, stackTrace) {
      _logger.e('Unexpected error during email sign-in', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// Email/Password Sign-Up
  Future<UserCredential?> signUpWithEmail({
    required String email,
    required String password,
    String? displayName,
  }) async {
    try {
      _logger.i('Creating account with email: $email');

      final credential = await _firebaseAuth.createUserWithEmailAndPassword(
        email: email,
        password: password,
      );

      // Update display name if provided
      if (displayName != null && credential.user != null) {
        await credential.user!.updateDisplayName(displayName);
        await credential.user!.reload();
      }

      _logger.i('Successfully created account: ${credential.user?.email}');
      return credential;
    } on FirebaseAuthException catch (e, stackTrace) {
      _logger.e('Email sign-up failed', error: e, stackTrace: stackTrace);
      rethrow;
    } catch (e, stackTrace) {
      _logger.e('Unexpected error during email sign-up', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// Google Sign-In
  Future<UserCredential?> signInWithGoogle() async {
    try {
      _logger.i('Starting Google Sign-In');

      // Google Sign-In 시작
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();

      if (googleUser == null) {
        _logger.w('Google Sign-In cancelled by user');
        return null;
      }

      // Google 인증 정보 가져오기
      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      // Firebase 인증 정보 생성
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // Firebase에 로그인
      final userCredential =
          await _firebaseAuth.signInWithCredential(credential);

      _logger.i('Google Sign-In successful: ${userCredential.user?.email}');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Google Sign-In failed', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// Apple Sign-In
  Future<UserCredential?> signInWithApple() async {
    try {
      _logger.i('Starting Apple Sign-In');

      // Apple Sign-In 시작
      final appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      // Firebase 인증 정보 생성
      final oAuthProvider = OAuthProvider('apple.com');
      final credential = oAuthProvider.credential(
        idToken: appleCredential.identityToken,
        accessToken: appleCredential.authorizationCode,
      );

      // Firebase에 로그인
      final userCredential =
          await _firebaseAuth.signInWithCredential(credential);

      _logger.i('Apple Sign-In successful: ${userCredential.user?.email}');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Apple Sign-In failed', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// Kakao Sign-In
  ///
  /// Kakao SDK로 로그인 후 백엔드에서 Firebase Custom Token을 받아 로그인합니다.
  Future<UserCredential?> signInWithKakao({
    required Future<String> Function(String kakaoAccessToken)
        getCustomTokenFromBackend,
  }) async {
    try {
      _logger.i('Starting Kakao Sign-In');

      // Kakao 로그인 (SDK 사용)
      kakao.OAuthToken token;

      // 카카오톡이 설치되어 있으면 카카오톡으로 로그인, 아니면 웹으로 로그인
      if (await kakao.isKakaoTalkInstalled()) {
        token = await kakao.UserApi.instance.loginWithKakaoTalk();
      } else {
        token = await kakao.UserApi.instance.loginWithKakaoAccount();
      }

      _logger.i('Kakao login successful, getting custom token from backend');

      // 백엔드에 Kakao 액세스 토큰 전송하여 Firebase Custom Token 받기
      final customToken = await getCustomTokenFromBackend(token.accessToken);

      // Firebase에 Custom Token으로 로그인
      final userCredential =
          await _firebaseAuth.signInWithCustomToken(customToken);

      _logger.i('Kakao Sign-In successful: ${userCredential.user?.uid}');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Kakao Sign-In failed', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 익명 로그인 (게스트 모드)
  Future<UserCredential> signInAnonymously() async {
    try {
      _logger.i('Starting anonymous sign-in');

      final userCredential = await _firebaseAuth.signInAnonymously();

      _logger.i('Anonymous sign-in successful: ${userCredential.user?.uid}');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Anonymous sign-in failed', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 익명 사용자를 인증된 사용자로 업그레이드 (Google)
  Future<UserCredential?> linkWithGoogle() async {
    try {
      final user = currentUser;
      if (user == null || !user.isAnonymous) {
        throw Exception('No anonymous user to link');
      }

      _logger.i('Linking anonymous user with Google');

      // Google Sign-In
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final GoogleSignInAuthentication googleAuth =
          await googleUser.authentication;

      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      // 익명 사용자와 Google 계정 연결
      final userCredential = await user.linkWithCredential(credential);

      _logger.i('Anonymous user linked with Google successfully');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Failed to link with Google', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 익명 사용자를 인증된 사용자로 업그레이드 (Apple)
  Future<UserCredential?> linkWithApple() async {
    try {
      final user = currentUser;
      if (user == null || !user.isAnonymous) {
        throw Exception('No anonymous user to link');
      }

      _logger.i('Linking anonymous user with Apple');

      final appleCredential = await SignInWithApple.getAppleIDCredential(
        scopes: [
          AppleIDAuthorizationScopes.email,
          AppleIDAuthorizationScopes.fullName,
        ],
      );

      final oAuthProvider = OAuthProvider('apple.com');
      final credential = oAuthProvider.credential(
        idToken: appleCredential.identityToken,
        accessToken: appleCredential.authorizationCode,
      );

      // 익명 사용자와 Apple 계정 연결
      final userCredential = await user.linkWithCredential(credential);

      _logger.i('Anonymous user linked with Apple successfully');
      return userCredential;
    } catch (e, stackTrace) {
      _logger.e('Failed to link with Apple', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 로그아웃
  Future<void> signOut() async {
    try {
      _logger.i('Signing out');

      // Firebase 로그아웃
      await _firebaseAuth.signOut();

      // Google 로그아웃
      if (await _googleSignIn.isSignedIn()) {
        await _googleSignIn.signOut();
      }

      // Kakao 로그아웃
      try {
        await kakao.UserApi.instance.logout();
      } catch (e) {
        _logger.w('Kakao logout failed (user might not be logged in with Kakao)');
      }

      _logger.i('Sign out successful');
    } catch (e, stackTrace) {
      _logger.e('Sign out failed', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 사용자 삭제 (회원 탈퇴)
  Future<void> deleteUser() async {
    try {
      final user = currentUser;
      if (user == null) {
        throw Exception('No user to delete');
      }

      _logger.i('Deleting user: ${user.uid}');

      await user.delete();

      // 소셜 로그인도 로그아웃
      if (await _googleSignIn.isSignedIn()) {
        await _googleSignIn.signOut();
      }

      try {
        await kakao.UserApi.instance.unlink();
      } catch (e) {
        _logger.w('Kakao unlink failed (user might not be logged in with Kakao)');
      }

      _logger.i('User deleted successfully');
    } catch (e, stackTrace) {
      _logger.e('Failed to delete user', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// 사용자 정보 업데이트
  Future<void> updateProfile({
    String? displayName,
    String? photoURL,
  }) async {
    try {
      final user = currentUser;
      if (user == null) {
        throw Exception('No user to update');
      }

      _logger.i('Updating user profile: $displayName');

      await user.updateDisplayName(displayName);
      await user.updatePhotoURL(photoURL);

      // 프로필 업데이트 후 리로드
      await user.reload();

      _logger.i('User profile updated successfully');
    } catch (e, stackTrace) {
      _logger.e('Failed to update profile', error: e, stackTrace: stackTrace);
      rethrow;
    }
  }

  /// ID Token 리프레시
  Future<String?> refreshIdToken() async {
    return await getIdToken(forceRefresh: true);
  }

  /// 사용자가 로그인되어 있는지 확인
  bool get isSignedIn => currentUser != null;

  /// 익명 사용자인지 확인
  bool get isAnonymous => currentUser?.isAnonymous ?? false;
}
