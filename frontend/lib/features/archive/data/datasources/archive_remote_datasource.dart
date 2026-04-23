import 'package:dio/dio.dart';
import '../../../../core/network/api_endpoints.dart';
import '../models/archive_model.dart';
import '../models/content_type_model.dart';
import '../services/instagram_media_extractor.dart';

class ArchiveRemoteDataSource {
  final Dio _dio;

  ArchiveRemoteDataSource(this._dio);

  /// POST /api/v1/archive — URL 분석 및 아카이빙
  Future<ArchivedContentModel> archiveUrl(String url, {bool force = false, String language = 'ko'}) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.archive,
        data: {'url': url, 'force': force, 'language': language},
      );
      return ArchivedContentModel.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// POST /api/v1/archive/instagram — Instagram 미디어 multipart 아카이빙
  Future<ArchivedContentModel> archiveInstagram({
    required String url,
    required List<InstagramMediaFile> mediaFiles,
    String? caption,
    String? author,
    bool force = false,
    String language = 'ko',
  }) async {
    try {
      final formData = FormData();
      formData.fields.add(MapEntry('url', url));
      formData.fields.add(MapEntry('force', force.toString()));
      formData.fields.add(MapEntry('language', language));
      if (caption != null) {
        formData.fields.add(MapEntry('caption', caption));
      }
      if (author != null) {
        formData.fields.add(MapEntry('author', author));
      }
      for (final f in mediaFiles) {
        formData.files.add(
          MapEntry(
            'media',
            MultipartFile.fromBytes(
              f.bytes,
              filename: f.filename,
              contentType: DioMediaType.parse(f.mimeType),
            ),
          ),
        );
      }
      final response = await _dio.post(
        ApiEndpoints.archiveInstagram,
        data: formData,
        options: Options(
          sendTimeout: const Duration(minutes: 5),
          receiveTimeout: const Duration(minutes: 5),
        ),
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

  /// GET /api/v1/content-types — 콘텐츠 타입 목록
  Future<List<ContentTypeInfoModel>> getContentTypes() async {
    try {
      final response = await _dio.get(ApiEndpoints.contentTypes);
      final list = response.data as List<dynamic>;
      return list
          .map((e) => ContentTypeInfoModel.fromJson(e as Map<String, dynamic>))
          .toList();
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
    switch (e.response?.statusCode) {
      case 400:
        return Exception('error_unsupportedLink');
      case 403:
        return Exception('error_accessDenied');
      case 404:
        return Exception('error_archiveNotFound');
      case 422:
        return Exception('error_privateOrDeleted');
      case 429:
        return Exception('error_rateLimited');
      case 503:
        return Exception('error_serviceUnavailable');
      default:
        return Exception('error_unknown');
    }
  }
}
