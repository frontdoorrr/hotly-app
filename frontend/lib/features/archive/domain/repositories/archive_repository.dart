import 'package:dartz/dartz.dart';
import '../entities/archived_content.dart';
import '../entities/content_type_info.dart';
import '../../data/services/instagram_media_extractor.dart';

abstract class ArchiveRepository {
  /// URL을 분석하고 아카이빙. force=true 이면 캐시 무시 후 재분석.
  Future<Either<Exception, ArchivedContent>> archiveUrl(
    String url, {
    bool force = false,
  });

  /// Instagram 미디어 파일을 multipart로 업로드하고 아카이빙.
  Future<Either<Exception, ArchivedContent>> archiveInstagram({
    required String url,
    required List<InstagramMediaFile> mediaFiles,
    String? caption,
    String? author,
    bool force = false,
  });

  /// 콘텐츠 타입 목록 조회
  Future<Either<Exception, List<ContentTypeInfo>>> getContentTypes();

  /// 아카이빙 목록 조회
  Future<Either<Exception, ArchiveList>> getArchives({
    String? contentType,
    int page = 1,
    int pageSize = 20,
  });

  /// 아카이빙 상세 조회
  Future<Either<Exception, ArchivedContent>> getArchive(String id);

  /// 아카이빙 삭제
  Future<Either<Exception, void>> deleteArchive(String id);
}
