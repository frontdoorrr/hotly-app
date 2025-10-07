import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:firebase_auth/firebase_auth.dart' as firebase;
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/auth/firebase_auth_service.dart';
import '../../../../core/network/dio_client.dart';
import '../../../../shared/models/user.dart';
import '../../domain/repositories/auth_repository.dart';

/// Auth Repository Implementation (Firebase)
class AuthRepositoryFirebaseImpl implements AuthRepository {
  final FirebaseAuthService _firebaseAuthService;
  final Dio _dio;

  AuthRepositoryFirebaseImpl(
    this._firebaseAuthService,
    this._dio,
  );

  @override
  User? get currentUser {
    final firebaseUser = _firebaseAuthService.currentUser;
    if (firebaseUser == null) return null;
    return User.fromFirebase(firebaseUser);
  }

  @override
  Stream<User?> get authStateChanges {
    return _firebaseAuthService.authStateChanges.map((firebaseUser) {
      if (firebaseUser == null) return null;
      return User.fromFirebase(firebaseUser);
    });
  }

  @override
  Future<Either<ApiException, String>> getIdToken({
    bool forceRefresh = false,
  }) async {
    try {
      final token = await _firebaseAuthService.getIdToken(
        forceRefresh: forceRefresh,
      );

      if (token == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: '로그인이 필요합니다',
          statusCode: 401,
        ));
      }

      return Right(token);
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'ID Token 가져오기 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithEmail({
    required String email,
    required String password,
  }) async {
    try {
      final userCredential = await _firebaseAuthService.signInWithEmail(
        email: email,
        password: password,
      );

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: '이메일 로그인에 실패했습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '로그인 중 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signUpWithEmail({
    required String email,
    required String password,
    String? displayName,
  }) async {
    try {
      final userCredential = await _firebaseAuthService.signUpWithEmail(
        email: email,
        password: password,
        displayName: displayName,
      );

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: '회원가입에 실패했습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '회원가입 중 오류가 발생했습니다: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithGoogle() async {
    try {
      final userCredential = await _firebaseAuthService.signInWithGoogle();

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: 'Google 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'Google 로그인 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithApple() async {
    try {
      final userCredential = await _firebaseAuthService.signInWithApple();

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: 'Apple 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'Apple 로그인 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInWithKakao() async {
    try {
      final userCredential = await _firebaseAuthService.signInWithKakao(
        getCustomTokenFromBackend: _getFirebaseCustomTokenFromBackend,
      );

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: 'Kakao 로그인이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'Kakao 로그인 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> signInAnonymously() async {
    try {
      final userCredential = await _firebaseAuthService.signInAnonymously();

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '익명 로그인 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> linkWithGoogle() async {
    try {
      final userCredential = await _firebaseAuthService.linkWithGoogle();

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: 'Google 계정 연결이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'Google 계정 연결 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, User>> linkWithApple() async {
    try {
      final userCredential = await _firebaseAuthService.linkWithApple();

      if (userCredential == null || userCredential.user == null) {
        return Left(ApiException(type: ApiExceptionType.server, 
          message: 'Apple 계정 연결이 취소되었습니다',
          statusCode: 400,
        ));
      }

      return Right(User.fromFirebase(userCredential.user!));
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: 'Apple 계정 연결 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> signOut() async {
    try {
      await _firebaseAuthService.signOut();
      return const Right(null);
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '로그아웃 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> deleteAccount() async {
    try {
      await _firebaseAuthService.deleteUser();
      return const Right(null);
    } on firebase.FirebaseAuthException catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: _getFirebaseErrorMessage(e),
        statusCode: _getFirebaseStatusCode(e),
      ));
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '회원 탈퇴 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  Future<Either<ApiException, void>> updateProfile({
    String? displayName,
    String? photoURL,
  }) async {
    try {
      await _firebaseAuthService.updateProfile(
        displayName: displayName,
        photoURL: photoURL,
      );
      return const Right(null);
    } catch (e) {
      return Left(ApiException(type: ApiExceptionType.server, 
        message: '프로필 업데이트 실패: $e',
        statusCode: 500,
      ));
    }
  }

  @override
  bool get isAnonymous => _firebaseAuthService.isAnonymous;

  /// Kakao 토큰으로 백엔드에서 Firebase Custom Token 받기
  Future<String> _getFirebaseCustomTokenFromBackend(
    String kakaoAccessToken,
  ) async {
    try {
      final response = await _dio.post(
        '/api/v1/auth/social-login',
        data: {
          'provider': 'kakao',
          'accessToken': kakaoAccessToken,
        },
      );

      final customToken = response.data['customToken'] as String?;

      if (customToken == null) {
        throw Exception('Custom token not found in response');
      }

      return customToken;
    } catch (e) {
      throw Exception('Failed to get custom token from backend: $e');
    }
  }

  /// Firebase Auth 에러 메시지 변환
  String _getFirebaseErrorMessage(firebase.FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
        return '사용자를 찾을 수 없습니다';
      case 'wrong-password':
        return '비밀번호가 올바르지 않습니다';
      case 'email-already-in-use':
        return '이미 사용 중인 이메일입니다';
      case 'invalid-email':
        return '유효하지 않은 이메일 형식입니다';
      case 'weak-password':
        return '비밀번호가 너무 약합니다 (최소 6자 이상)';
      case 'user-disabled':
        return '비활성화된 계정입니다';
      case 'operation-not-allowed':
        return '허용되지 않는 작업입니다';
      case 'account-exists-with-different-credential':
        return '다른 로그인 방법으로 이미 가입된 계정입니다';
      case 'invalid-credential':
        return '인증 정보가 유효하지 않습니다';
      case 'credential-already-in-use':
        return '이미 다른 계정에 연결된 인증 정보입니다';
      case 'requires-recent-login':
        return '보안을 위해 다시 로그인해주세요';
      default:
        return e.message ?? '알 수 없는 오류가 발생했습니다';
    }
  }

  /// Firebase Auth 에러 상태 코드 반환
  int _getFirebaseStatusCode(firebase.FirebaseAuthException e) {
    switch (e.code) {
      case 'user-not-found':
      case 'wrong-password':
      case 'invalid-credential':
        return 401;
      case 'email-already-in-use':
      case 'account-exists-with-different-credential':
      case 'credential-already-in-use':
        return 409;
      case 'user-disabled':
      case 'operation-not-allowed':
        return 403;
      case 'invalid-email':
      case 'weak-password':
        return 400;
      default:
        return 500;
    }
  }
}

/// Auth Repository Provider (Firebase)
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  final firebaseAuthService = ref.watch(firebaseAuthServiceProvider);
  final dio = ref.watch(dioProvider);
  return AuthRepositoryFirebaseImpl(firebaseAuthService, dio);
});

/// Firebase Auth Service Provider
final firebaseAuthServiceProvider = Provider<FirebaseAuthService>((ref) {
  return FirebaseAuthService();
});
