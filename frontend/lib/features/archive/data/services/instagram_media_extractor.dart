import 'dart:convert';
import 'dart:developer' as developer;
import 'dart:io';
import 'dart:typed_data';

void _log(String message) {
  developer.log(message, name: 'InstagramExtractor');
}

class InstagramMediaFile {
  final String filename;
  final Uint8List bytes;
  final String mimeType;

  const InstagramMediaFile({
    required this.filename,
    required this.bytes,
    required this.mimeType,
  });
}

class InstagramExtractResult {
  final List<InstagramMediaFile> mediaFiles;
  final String? caption;
  final String? author;
  /// true: 임베디드 JSON sidecar 파싱 성공(캐러셀 전체 슬라이드)
  /// false: OG 메타태그 폴백(단일 이미지/릴스 또는 sidecar 파싱 실패)
  final bool fromSidecar;

  const InstagramExtractResult({
    required this.mediaFiles,
    this.caption,
    this.author,
    this.fromSidecar = false,
  });
}

class InstagramBlockedError implements Exception {
  final String message;
  const InstagramBlockedError(this.message);
  @override
  String toString() => 'InstagramBlockedError: $message';
}

class InstagramParseError implements Exception {
  final String message;
  const InstagramParseError(this.message);
  @override
  String toString() => 'InstagramParseError: $message';
}

class InstagramMediaDownloadError implements Exception {
  final String message;
  const InstagramMediaDownloadError(this.message);
  @override
  String toString() => 'InstagramMediaDownloadError: $message';
}

class InstagramMediaExtractor {
  static const _userAgent =
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
      'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';

  static const _maxFileSizeBytes = 100 * 1024 * 1024; // 100MB
  static const _maxMediaCount = 10;

  static bool _isValidInstagramUrl(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null || !uri.isAbsolute) return false;
    return uri.host == 'www.instagram.com' || uri.host == 'instagram.com';
  }

  static bool _isValidMediaUrl(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null || !uri.isAbsolute) return false;
    final host = uri.host;
    return host.endsWith('.cdninstagram.com') ||
        host.endsWith('.fbcdn.net') ||
        host == 'cdninstagram.com' ||
        host == 'fbcdn.net';
  }

  Future<InstagramExtractResult> extract(String url) async {
    if (!_isValidInstagramUrl(url)) {
      throw const InstagramParseError('Not a valid Instagram URL');
    }
    // Stories는 og 태그를 노출하지 않으므로 조기 반환
    if (url.contains('/stories/')) {
      throw const InstagramParseError('Instagram Stories are not supported');
    }

    _log('extract start url=$url');
    final html = await _fetchPageHtml(url);
    _log('html fetched bytes=${html.length}');

    // 캐러셀(sidecar) 우선 — 임베디드 GraphQL JSON에서 전체 슬라이드 추출
    var candidates = _extractSidecarMedia(html);
    final fromSidecar = candidates.isNotEmpty;
    _log('sidecar parse result: count=${candidates.length} '
        'fromSidecar=$fromSidecar');

    // sidecar 미존재(단일 이미지/릴스) 또는 파싱 실패 시 OG 메타태그 폴백
    if (candidates.isEmpty) {
      final ogUrls = _parseOgMediaUrls(html);
      _log('OG fallback: og_count=${ogUrls.length}');
      candidates = ogUrls
          .map((u) => _MediaCandidate(url: u, isVideo: u.contains('.mp4')))
          .toList();
    }

    if (candidates.isEmpty) {
      _log('extract FAIL: no media found in sidecar nor OG');
      throw const InstagramParseError('No Instagram media found');
    }

    final validCandidates =
        candidates.where((c) => _isValidMediaUrl(c.url)).toList();
    final filteredOut = candidates.length - validCandidates.length;
    if (filteredOut > 0) {
      _log('CDN host filter dropped $filteredOut candidate(s)');
    }
    if (validCandidates.isEmpty) {
      _log('extract FAIL: all candidates rejected by CDN host filter');
      throw const InstagramParseError('No media found from allowed hosts');
    }

    // 서버 처리 한도 + 인스타 캐러셀 한도(10장) 매치, 순서 보존
    final capped = validCandidates.take(_maxMediaCount).toList();
    if (validCandidates.length > _maxMediaCount) {
      _log('capped from ${validCandidates.length} to $_maxMediaCount');
    }

    for (var i = 0; i < capped.length; i++) {
      final c = capped[i];
      _log('candidate[$i] isVideo=${c.isVideo} '
          'urlHost=${Uri.tryParse(c.url)?.host} '
          'urlPath=${Uri.tryParse(c.url)?.path}');
    }

    final files = await Future.wait(
      capped.indexed.map((e) => _downloadMedia(
            e.$2.url,
            e.$1,
            isVideoHint: e.$2.isVideo,
          )),
    );
    _log('downloaded ${files.length} files: '
        '${files.map((f) => "${f.filename}(${f.mimeType},${f.bytes.length}B)").join(", ")}');

    final caption = _parseCaption(html);
    final author = _parseAuthorFromUrl(url);
    return InstagramExtractResult(
      mediaFiles: files,
      caption: caption,
      author: author,
      fromSidecar: fromSidecar,
    );
  }

  /// 임베디드 `<script type="application/json">` 안의 GraphQL payload에서
  /// 캐러셀(sidecar) 슬라이드 전체를 추출한다.
  ///
  /// Instagram이 외부에 공식 보장하는 인터페이스가 아니므로
  /// 키 위치 변경에 대비해 재귀 탐색하고, 실패 시 빈 리스트를 반환한다.
  List<_MediaCandidate> _extractSidecarMedia(String html) {
    final scriptPattern = RegExp(
      r'<script[^>]*type="application/json"[^>]*>([\s\S]*?)</script>',
      caseSensitive: false,
    );

    final allMatches = scriptPattern.allMatches(html).toList();
    _log('sidecar scan: ${allMatches.length} <script type="application/json"> tag(s)');

    var jsonOk = 0;
    var sidecarSeen = 0;
    for (var i = 0; i < allMatches.length; i++) {
      final raw = allMatches[i].group(1);
      if (raw == null || raw.isEmpty) continue;

      dynamic decoded;
      try {
        decoded = jsonDecode(raw);
        jsonOk++;
      } catch (_) {
        continue;
      }

      final sidecar = _findSidecarNode(decoded);
      if (sidecar == null) continue;
      sidecarSeen++;

      final edges = sidecar['edges'];
      if (edges is! List) {
        _log('sidecar[$i] found but edges not a List (type=${edges.runtimeType})');
        continue;
      }

      final result = <_MediaCandidate>[];
      var skippedNoUrl = 0;
      for (final edge in edges) {
        if (edge is! Map) continue;
        final node = edge['node'];
        if (node is! Map) continue;

        final isVideo = node['is_video'] == true;
        final url = isVideo ? node['video_url'] : node['display_url'];
        if (url is! String || url.isEmpty) {
          skippedNoUrl++;
          continue;
        }

        result.add(_MediaCandidate(url: url, isVideo: isVideo));
      }

      _log('sidecar[$i] edges=${edges.length} extracted=${result.length} '
          'skipped(no_url)=$skippedNoUrl');

      if (result.isNotEmpty) return result;
    }

    _log('sidecar scan done: jsonDecodeOk=$jsonOk sidecarNodesFound=$sidecarSeen '
        '→ no usable sidecar');
    return [];
  }

  /// `edge_sidecar_to_children` 노드를 재귀 탐색해 반환.
  /// 인스타가 키 위치를 자주 바꾸므로 깊이 제한 없는 DFS로 탐색한다.
  Map<String, dynamic>? _findSidecarNode(dynamic json) {
    if (json is Map) {
      final sidecar = json['edge_sidecar_to_children'];
      if (sidecar is Map<String, dynamic> && sidecar['edges'] is List) {
        return sidecar;
      }
      for (final value in json.values) {
        final found = _findSidecarNode(value);
        if (found != null) return found;
      }
    } else if (json is List) {
      for (final item in json) {
        final found = _findSidecarNode(item);
        if (found != null) return found;
      }
    }
    return null;
  }

  /// URL에서 username 추출: instagram.com/{username}/p/{shortcode}/
  String? _parseAuthorFromUrl(String url) {
    final uri = Uri.tryParse(url);
    if (uri == null) return null;
    final segments = uri.pathSegments.where((s) => s.isNotEmpty).toList();
    // [{username}, 'p'|'reel', {shortcode}] 패턴
    if (segments.length >= 3 &&
        (segments[1] == 'p' || segments[1] == 'reel' || segments[1] == 'reels')) {
      return segments[0];
    }
    return null;
  }

  Future<String> _fetchPageHtml(String url) async {
    final client = HttpClient();
    client.connectionTimeout = const Duration(seconds: 15);

    try {
      final request = await client.getUrl(Uri.parse(url));
      request.headers.set(HttpHeaders.userAgentHeader, _userAgent);
      request.headers.set(HttpHeaders.acceptHeader,
          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8');
      request.headers.set(HttpHeaders.acceptLanguageHeader, 'ko-KR,ko;q=0.9,en;q=0.8');

      final response = await request.close();

      if (response.statusCode == 403 || response.statusCode == 401) {
        throw InstagramBlockedError('Instagram page access blocked (${response.statusCode})');
      }
      if (response.statusCode != 200) {
        throw InstagramBlockedError('Instagram page request failed (${response.statusCode})');
      }

      final buffer = StringBuffer();
      await for (final chunk in response.transform(systemEncoding.decoder)) {
        buffer.write(chunk);
      }
      return buffer.toString();
    } on InstagramBlockedError {
      rethrow;
    } on SocketException catch (e) {
      throw InstagramBlockedError('Network error: $e');
    } finally {
      client.close();
    }
  }

  /// og:video:url > og:video:secure_url > og:image 순으로 미디어 URL 추출
  List<String> _parseOgMediaUrls(String html) {
    final seen = <String>{};
    final results = <String>[];

    // 동영상 URL 우선
    final videoPattern = RegExp(
      r'<meta\s+property="og:video(?::secure_url|:url)?"\s+content="([^"]+)"',
      caseSensitive: false,
    );
    for (final m in videoPattern.allMatches(html)) {
      final u = _decodeHtmlEntities(m.group(1)!);
      if (!seen.contains(u) && !u.contains('/profile_pic/')) {
        seen.add(u);
        results.add(u);
      }
    }

    // 이미지 URL (캐러셀 포함)
    final imagePattern = RegExp(
      r'<meta\s+property="og:image"\s+content="([^"]+)"',
      caseSensitive: false,
    );
    for (final m in imagePattern.allMatches(html)) {
      final u = _decodeHtmlEntities(m.group(1)!);
      if (!seen.contains(u) && !u.contains('/profile_pic/')) {
        seen.add(u);
        results.add(u);
      }
    }

    return results;
  }

  /// HTML 속성값에 포함된 엔티티를 URL용으로 디코딩
  /// Instagram og 태그의 CDN URL 쿼리스트링에 &amp; 등이 포함되면 CDN이 400/403 반환
  String _decodeHtmlEntities(String input) {
    return input
        .replaceAll('&amp;', '&')
        .replaceAll('&lt;', '<')
        .replaceAll('&gt;', '>')
        .replaceAll('&#39;', "'")
        .replaceAll('&quot;', '"');
  }

  String? _parseCaption(String html) {
    final pattern = RegExp(
      r'<meta\s+(?:name="description"|property="og:description")[\s\S]*?content="([^"]{1,2000})"',
      caseSensitive: false,
    );
    final raw = pattern.firstMatch(html)?.group(1);
    return raw != null ? _decodeHtmlEntities(raw) : null;
  }

  Future<InstagramMediaFile> _downloadMedia(
    String url,
    int index, {
    bool isVideoHint = false,
  }) async {
    final client = HttpClient();
    client.connectionTimeout = const Duration(seconds: 30);

    try {
      final request = await client.getUrl(Uri.parse(url));
      request.headers.set(HttpHeaders.userAgentHeader, _userAgent);
      request.headers.set(HttpHeaders.refererHeader, 'https://www.instagram.com/');

      final response = await request.close();
      if (response.statusCode != 200) {
        _log('download[$index] FAIL status=${response.statusCode} url=$url');
        throw InstagramMediaDownloadError('Media download failed (${response.statusCode}): $url');
      }

      final builder = BytesBuilder();
      await for (final chunk in response) {
        builder.add(chunk);
        if (builder.length > _maxFileSizeBytes) {
          throw InstagramMediaDownloadError('File size exceeds 100MB: $url');
        }
      }

      final bytes = builder.toBytes();
      final mime = _inferMimeType(url, isVideoHint: isVideoHint);
      final filename = _inferFilename(url, index, mime);

      return InstagramMediaFile(filename: filename, bytes: bytes, mimeType: mime);
    } on InstagramMediaDownloadError {
      rethrow;
    } on SocketException catch (e) {
      throw InstagramMediaDownloadError('Network error: $e');
    } finally {
      client.close();
    }
  }

  String _inferMimeType(String url, {bool isVideoHint = false}) {
    final path = Uri.tryParse(url)?.path.toLowerCase() ?? '';
    if (path.endsWith('.mp4')) return 'video/mp4';
    if (path.endsWith('.mov')) return 'video/quicktime';
    if (path.endsWith('.png')) return 'image/png';
    if (path.endsWith('.webp')) return 'image/webp';
    // 인스타 CDN의 video_url은 확장자가 항상 명확하지 않으므로 hint 우선
    if (isVideoHint) return 'video/mp4';
    return 'image/jpeg';
  }

  String _inferFilename(String url, int index, String mime) {
    final ext = mime.contains('video') ? 'mp4' : mime.contains('png') ? 'png' : 'jpg';
    return 'instagram_media_$index.$ext';
  }
}

class _MediaCandidate {
  final String url;
  final bool isVideo;
  const _MediaCandidate({required this.url, required this.isVideo});
}
