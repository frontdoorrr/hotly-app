import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';
import 'api_endpoints.dart';
import '../auth/firebase_auth_service.dart';
import '../utils/app_logger.dart';

/// Dio Instance Provider (raw Dio object)
final dioProvider = Provider<Dio>((ref) {
  return DioClient.instance.dio;
});

/// DioClient Instance Provider (wrapped client with helper methods)
final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient.instance;
});

/// Dio HTTP Client
class DioClient {
  static final DioClient _instance = DioClient._internal();
  static DioClient get instance => _instance;

  late final Dio _dio;
  Dio get dio => _dio;

  DioClient._internal() {
    _dio = Dio(
      BaseOptions(
        baseUrl: ApiEndpoints.baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        validateStatus: (status) {
          // 200-299는 성공으로 처리
          return status != null && status >= 200 && status < 300;
        },
      ),
    );

    _addInterceptors();
  }

  void _addInterceptors() {
    // Pretty Logger (개발 환경에서만)
    _dio.interceptors.add(
      PrettyDioLogger(
        requestHeader: true,
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        error: true,
        compact: true,
        maxWidth: 90,
      ),
    );

    // Auth Interceptor (토큰 자동 추가)
    _dio.interceptors.add(
      AuthInterceptor(),
    );
  }

  /// GET 요청
  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.get<T>(
        path,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// POST 요청
  Future<Response<T>> post<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.post<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// PUT 요청
  Future<Response<T>> put<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.put<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// DELETE 요청
  Future<Response<T>> delete<T>(
    String path, {
    dynamic data,
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) async {
    try {
      return await _dio.delete<T>(
        path,
        data: data,
        queryParameters: queryParameters,
        options: options,
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// 에러 핸들링
  ApiException _handleError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ApiException(
          message: '연결 시간이 초과되었습니다. 다시 시도해주세요.',
          statusCode: 408,
          type: ApiExceptionType.timeout,
        );

      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode ?? 500;
        final message = error.response?.data['message'] as String? ??
            error.response?.data['error'] as String? ??
            '서버 오류가 발생했습니다.';

        if (statusCode >= 500) {
          return ApiException(
            message: message,
            statusCode: statusCode,
            type: ApiExceptionType.server,
          );
        } else if (statusCode == 401) {
          return ApiException(
            message: '인증이 필요합니다. 다시 로그인해주세요.',
            statusCode: statusCode,
            type: ApiExceptionType.unauthorized,
          );
        } else if (statusCode == 404) {
          return ApiException(
            message: '요청한 데이터를 찾을 수 없습니다.',
            statusCode: statusCode,
            type: ApiExceptionType.notFound,
          );
        } else {
          return ApiException(
            message: message,
            statusCode: statusCode,
            type: ApiExceptionType.badRequest,
          );
        }

      case DioExceptionType.cancel:
        return ApiException(
          message: '요청이 취소되었습니다.',
          type: ApiExceptionType.cancel,
        );

      case DioExceptionType.connectionError:
      case DioExceptionType.unknown:
      default:
        return ApiException(
          message: '네트워크 연결을 확인해주세요.',
          type: ApiExceptionType.network,
        );
    }
  }
}

/// API Exception Types
enum ApiExceptionType {
  timeout,
  network,
  server,
  unauthorized,
  notFound,
  badRequest,
  cancel,
  unknown,
}

/// API Exception
class ApiException implements Exception {
  final String message;
  final int? statusCode;
  final ApiExceptionType type;

  ApiException({
    required this.message,
    this.statusCode,
    required this.type,
  });

  @override
  String toString() => message;
}

/// Auth Interceptor (Firebase ID Token 자동 추가)
class AuthInterceptor extends Interceptor {
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    try {
      // Firebase에서 ID Token 가져오기
      final firebaseAuthService = FirebaseAuthService();
      final token = await firebaseAuthService.getIdToken();

      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    } catch (e) {
      // 토큰 가져오기 실패해도 요청은 계속 진행
      AppLogger.e('Failed to get Firebase ID token', tag: 'Auth', error: e);
    }

    return handler.next(options);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // 401 에러 시 Firebase에서 자동으로 처리됨
    // authStateChanges 스트림에서 감지하여 로그인 화면으로 이동
    if (err.response?.statusCode == 401) {
      AppLogger.w('Unauthorized: User needs to re-authenticate', tag: 'Auth');
    }

    return handler.next(err);
  }
}
