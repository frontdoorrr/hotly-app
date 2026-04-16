import 'package:dio/dio.dart';
import '../../../../core/network/api_endpoints.dart';
import '../models/archive_model.dart';

class ArchiveRemoteDataSource {
  final Dio _dio;

  ArchiveRemoteDataSource(this._dio);

  /// POST /api/v1/archive — URL 분석 및 아카이빙
  Future<ArchivedContentModel> archiveUrl(String url, {bool force = false}) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.archive,
        data: {'url': url, 'force': force},
      );
      return ArchivedContentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// GET /api/v1/archive — 목록 조회
  Future<ArchiveListModel> getArchives({
    String? contentType,
    int page = 1,
    int pageSize = 20,
  }) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.archive,
        queryParameters: {
          if (contentType != null) 'content_type': contentType,
          'page': page,
          'page_size': pageSize,
        },
      );
      return ArchiveListModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// GET /api/v1/archive/{id} — 상세 조회
  Future<ArchivedContentModel> getArchive(String id) async {
    try {
      final response = await _dio.get(ApiEndpoints.archiveDetail(id));
      return ArchivedContentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// DELETE /api/v1/archive/{id} — 삭제
  Future<void> deleteArchive(String id) async {
    try {
      await _dio.delete(ApiEndpoints.archiveDetail(id));
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    final data = e.response?.data;
    final detail = (data is Map) ? data['detail'] : null;
    switch (e.response?.statusCode) {
      case 400:
        return Exception('지원하지 않는 플랫폼입니다.');
      case 403:
        return Exception('접근 권한이 없습니다.');
      case 404:
        return Exception('아카이브를 찾을 수 없습니다.');
      case 422:
        return Exception('콘텐츠 추출에 실패했습니다. 비공개 콘텐츠일 수 있습니다.');
      case 503:
        return Exception('분석 서비스를 일시적으로 사용할 수 없습니다.');
      default:
        return Exception(detail?.toString() ?? '알 수 없는 오류가 발생했습니다.');
    }
  }
}
