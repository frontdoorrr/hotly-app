import 'package:dartz/dartz.dart';
import '../entities/archived_content.dart';

abstract class ArchiveRepository {
  /// URL을 분석하고 아카이빙. force=true 이면 캐시 무시 후 재분석.
  Future<Either<Exception, ArchivedContent>> archiveUrl(
    String url, {
    bool force = false,
  });

  /// 아카이빙 목록 조회
  Future<Either<Exception, ArchiveList>> getArchives({
    ContentType? contentType,
    int page = 1,
    int pageSize = 20,
  });

  /// 아카이빙 상세 조회
  Future<Either<Exception, ArchivedContent>> getArchive(String id);

  /// 아카이빙 삭제
  Future<Either<Exception, void>> deleteArchive(String id);
}
