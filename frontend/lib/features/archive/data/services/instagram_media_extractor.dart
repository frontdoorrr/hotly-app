import 'dart:io';
import 'dart:typed_data';

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

  const InstagramExtractResult({required this.mediaFiles, this.caption, this.author});
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

    final html = await _fetchPageHtml(url);
    final mediaUrls = _parseOgMediaUrls(html);

    if (mediaUrls.isEmpty) {
      throw const InstagramParseError('No Instagram media found');
    }

    final validUrls = mediaUrls.where(_isValidMediaUrl).toList();
    if (validUrls.isEmpty) {
      throw const InstagramParseError('No media found from allowed hosts');
    }

    final files = await Future.wait(
      validUrls.indexed.map((e) => _downloadMedia(e.$2, e.$1)),
    );

    final caption = _parseCaption(html);
    final author = _parseAuthorFromUrl(url);
    return InstagramExtractResult(mediaFiles: files, caption: caption, author: author);
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

  Future<InstagramMediaFile> _downloadMedia(String url, int index) async {
    final client = HttpClient();
    client.connectionTimeout = const Duration(seconds: 30);

    try {
      final request = await client.getUrl(Uri.parse(url));
      request.headers.set(HttpHeaders.userAgentHeader, _userAgent);
      request.headers.set(HttpHeaders.refererHeader, 'https://www.instagram.com/');

      final response = await request.close();
      if (response.statusCode != 200) {
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
      final mime = _inferMimeType(url);
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

  String _inferMimeType(String url) {
    final path = Uri.tryParse(url)?.path.toLowerCase() ?? '';
    if (path.endsWith('.mp4')) return 'video/mp4';
    if (path.endsWith('.mov')) return 'video/quicktime';
    if (path.endsWith('.png')) return 'image/png';
    if (path.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }

  String _inferFilename(String url, int index, String mime) {
    final ext = mime.contains('video') ? 'mp4' : mime.contains('png') ? 'png' : 'jpg';
    return 'instagram_media_$index.$ext';
  }
}
