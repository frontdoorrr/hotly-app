import 'package:dio/dio.dart';
import '../../../../core/network/api_endpoints.dart';
import '../models/link_analysis_response.dart';

/// Remote data source for Link Analysis API
class LinkAnalysisRemoteDataSource {
  final Dio _dio;

  LinkAnalysisRemoteDataSource(this._dio);

  /// Analyze a single URL
  ///
  /// POST /api/v1/links/analyze
  /// Body: { "url": "https://...", "force_refresh": false }
  Future<LinkAnalysisResponse> analyzeLink({
    required String url,
    bool forceRefresh = false,
    String? webhookUrl,
  }) async {
    try {
      final response = await _dio.post(
        ApiEndpoints.linkAnalyze,
        data: {
          'url': url,
          'force_refresh': forceRefresh,
          if (webhookUrl != null) 'webhook_url': webhookUrl,
        },
      );

      return LinkAnalysisResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Get analysis status by ID
  ///
  /// GET /api/v1/link-analysis/analyses/{analysis_id}
  Future<LinkAnalysisResponse> getAnalysisStatus(String analysisId) async {
    try {
      final response = await _dio.get(
        ApiEndpoints.linkAnalysisStatus(analysisId),
      );

      return LinkAnalysisResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Cancel ongoing analysis
  ///
  /// DELETE /api/v1/link-analysis/analyses/{analysis_id}
  Future<void> cancelAnalysis(String analysisId) async {
    try {
      await _dio.delete(
        ApiEndpoints.linkAnalysisStatus(analysisId),
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  /// Analyze multiple URLs in batch
  ///
  /// POST /api/v1/links/bulk-analyze
  Future<Map<String, dynamic>> bulkAnalyzeLinks({
    required List<String> urls,
    bool forceRefresh = false,
    String? webhookUrl,
  }) async {
    try {
      final response = await _dio.post(
        '${ApiEndpoints.linkAnalyze}/bulk-analyze',
        data: {
          'urls': urls,
          'force_refresh': forceRefresh,
          if (webhookUrl != null) 'webhook_url': webhookUrl,
        },
      );

      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  Exception _handleError(DioException e) {
    switch (e.response?.statusCode) {
      case 422:
        return Exception('Unsupported platform: ${e.response?.data['detail']}');
      case 429:
        return Exception('Rate limit exceeded. Please try again later.');
      case 503:
        return Exception('AI analysis service unavailable');
      case 404:
        return Exception('Analysis not found');
      default:
        return Exception(
          e.response?.data['detail'] ?? 'Failed to analyze link',
        );
    }
  }
}
