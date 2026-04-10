# Link Analyzer — 서비스 통합 가이드

이 문서는 link-analyzer API 서버와 통신하는 외부 서비스를 개발할 때 필요한 모든 정보를 담고 있습니다.

---

## 목차

1. [개요](#개요)
2. [기본 정보](#기본-정보)
3. [인증](#인증)
4. [API Key 관리](#api-key-관리)
5. [엔드포인트 레퍼런스](#엔드포인트-레퍼런스)
6. [에러 처리](#에러-처리)
7. [제한사항](#제한사항)
8. [통합 예시 코드](#통합-예시-코드)

---

## 개요

link-analyzer는 YouTube, Instagram, 네이버 블로그 URL을 받아 콘텐츠를 추출하고 Google Gemini로 분석하는 REST API 서버입니다.

**지원 플랫폼**

| 플랫폼 | URL 패턴 예시 |
|--------|--------------|
| YouTube | `https://www.youtube.com/watch?v=...` |
| Instagram | `https://www.instagram.com/p/...` |
| 네이버 블로그 | `https://blog.naver.com/...` |

---

## 기본 정보

| 항목 | 값 |
|------|-----|
| Base URL | `http://localhost:8000` (기본값) |
| API 버전 경로 | `/api/v1` |
| 요청 Content-Type | `application/json` |
| 응답 Content-Type | `application/json` |
| 인터랙티브 문서 | `GET /docs` (Swagger UI) |

---

## 인증

모든 API 요청(헬스 체크 제외)에 `X-API-Key` 헤더가 필요합니다.

```http
X-API-Key: your-api-key
```

**인증 실패 응답**

```json
// 401 — 키가 없거나 유효하지 않음
{
  "detail": {
    "code": "INVALID_API_KEY",
    "message": "유효하지 않은 API Key입니다."
  }
}

// 401 — 만료된 키
{
  "detail": {
    "code": "EXPIRED_API_KEY",
    "message": "만료된 API Key입니다."
  }
}
```

---

## API Key 관리

### 첫 번째 키 발급

서버 운영자로부터 **Admin API Key**를 받으세요. 이 키로 아래 API를 호출해 서비스용 키를 발급받습니다.

### `POST /api/v1/admin/api-keys` — 새 키 발급

> Admin 키 전용 엔드포인트입니다.

**요청**

```http
POST /api/v1/admin/api-keys
X-API-Key: {admin-key}
Content-Type: application/json

{
  "name": "my-service-prod",
  "expires_at": "2026-12-31T23:59:59Z"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | 선택 | 키 이름/용도 메모 (최대 200자) |
| `expires_at` | datetime (ISO 8601) | 선택 | 만료일시. `null`이면 무기한 |

**응답 `201 Created`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "key": "lk_AbCdEfGhIjKlMnOpQrStUvWxYz12",
  "key_prefix": "lk_AbCdEfGh",
  "name": "my-service-prod",
  "is_admin": false,
  "expires_at": "2026-12-31T23:59:59Z",
  "created_at": "2025-04-05T12:00:00Z"
}
```

> **중요**: `key` 값은 이 응답에서만 확인할 수 있습니다. 반드시 안전한 곳에 저장하세요.

---

### `GET /api/v1/admin/api-keys` — 키 목록 조회

```http
GET /api/v1/admin/api-keys
X-API-Key: {admin-key}
```

**응답 `200 OK`**

```json
[
  {
    "id": "550e8400-...",
    "key_prefix": "lk_AbCdEfGh",
    "name": "my-service-prod",
    "is_active": true,
    "is_admin": false,
    "expires_at": "2026-12-31T23:59:59Z",
    "last_used_at": "2025-04-05T15:30:00Z",
    "created_at": "2025-04-05T12:00:00Z",
    "revoked_at": null
  }
]
```

---

### `DELETE /api/v1/admin/api-keys/{key_id}` — 키 취소

```http
DELETE /api/v1/admin/api-keys/550e8400-e29b-41d4-a716-446655440000
X-API-Key: {admin-key}
```

**응답 `204 No Content`** (본문 없음)

취소된 키로 요청하면 즉시 `401 INVALID_API_KEY`가 반환됩니다.

---

## 엔드포인트 레퍼런스

### `GET /api/v1/health` — 헬스 체크

인증 불필요. 서버 동작 확인용.

```http
GET /api/v1/health
```

**응답 `200 OK`**

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### `POST /api/v1/analyze` — URL 분석

URL의 콘텐츠를 추출하고 AI로 분석합니다.  
동일 URL을 재요청하면 캐싱된 결과를 반환합니다 (`force: true`로 강제 재분석 가능).

**요청**

```http
POST /api/v1/analyze
X-API-Key: {your-key}
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "force": false
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `url` | string (URL) | 필수 | 분석할 URL |
| `force` | boolean | 선택 | `true`이면 캐시를 무시하고 재분석 (기본값: `false`) |

**응답 `201 Created`**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "platform": "youtube",
  "metadata": {
    "title": "콘텐츠 제목",
    "author": "채널명 / 작성자",
    "published_at": "2024-01-15T10:30:00Z",
    "thumbnail_url": "https://...",
    "language": "ko"
  },
  "analysis": {
    "summary": "핵심 내용을 200자 내외로 요약한 텍스트.",
    "keywords": {
      "main": ["핵심 키워드1", "핵심 키워드2"],
      "sub": ["세부 키워드1", "세부 키워드2"],
      "named_entities": ["고유명사1"]
    },
    "categories": {
      "topic": ["기술/개발"],
      "format": ["튜토리얼/가이드"]
    },
    "action_items": {
      "todos": ["해야 할 일 1", "해야 할 일 2"],
      "references": [
        {"title": "참고자료 제목", "url": "https://..."}
      ],
      "insights": ["기억해야 할 포인트 1"]
    },
    "sentiment": "positive",
    "content_type": "tips",
    "type_specific_data": {}
  },
  "raw_content": {
    "text": "원본 텍스트 전문",
    "word_count": 1500,
    "images_analyzed": 3
  },
  "created_at": "2025-04-05T12:00:00Z"
}
```

**응답 필드 상세**

| 필드 | 타입 | 설명 |
|------|------|------|
| `platform` | `youtube` \| `instagram` \| `naver_blog` | 감지된 플랫폼 |
| `analysis.sentiment` | `positive` \| `neutral` \| `negative` | 감성 분석 결과 |
| `analysis.content_type` | `place` \| `event` \| `tips` \| `review` \| `unknown` | 콘텐츠 유형 |
| `analysis.type_specific_data` | object | 콘텐츠 유형별 추가 데이터 (없으면 `null`) |

---

### `GET /api/v1/contents` — 콘텐츠 목록 조회

저장된 분석 결과 목록을 페이지네이션으로 조회합니다.

**요청**

```http
GET /api/v1/contents?page=1&page_size=20
X-API-Key: {your-key}
```

| 쿼리 파라미터 | 타입 | 기본값 | 설명 |
|--------------|------|--------|------|
| `page` | integer | `1` | 페이지 번호 (1 이상) |
| `page_size` | integer | `20` | 페이지 크기 (1~100) |

**응답 `200 OK`**

```json
{
  "items": [
    {
      "id": "550e8400-...",
      "url": "https://www.youtube.com/watch?v=...",
      "platform": "youtube",
      "title": "콘텐츠 제목",
      "author": "채널명",
      "summary": "요약 텍스트",
      "created_at": "2025-04-05T12:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### `GET /api/v1/contents/{content_id}` — 콘텐츠 상세 조회

```http
GET /api/v1/contents/550e8400-e29b-41d4-a716-446655440000
X-API-Key: {your-key}
```

**응답 `200 OK`**: `POST /analyze`와 동일한 `ContentResponse` 구조

---

### `DELETE /api/v1/contents/{content_id}` — 콘텐츠 삭제

```http
DELETE /api/v1/contents/550e8400-e29b-41d4-a716-446655440000
X-API-Key: {your-key}
```

**응답 `204 No Content`** (본문 없음)

---

## 에러 처리

모든 에러 응답은 아래 구조를 따릅니다:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "사람이 읽을 수 있는 설명",
    "url": "요청한 URL (해당하는 경우)"
  }
}
```

**에러 코드 목록**

| HTTP 상태 | code | 설명 |
|-----------|------|------|
| `401` | `INVALID_API_KEY` | 키가 없거나 비활성/취소된 키 |
| `401` | `EXPIRED_API_KEY` | 만료된 키 |
| `403` | `FORBIDDEN` | Admin 권한 없음 |
| `400` | `UNSUPPORTED_PLATFORM` | 지원하지 않는 URL/플랫폼 |
| `400` | `CONTENT_TOO_LONG` | 영상 길이 1시간 초과 |
| `400` | `FILE_TOO_LARGE` | 파일 크기 초과 (영상 2GB, 이미지 20MB) |
| `404` | `CONTENT_NOT_FOUND` | 해당 ID의 콘텐츠 없음 |
| `500` | `EXTRACTION_FAILED` | 콘텐츠 추출 실패 (비공개 콘텐츠 등) |
| `422` | — | 요청 형식 오류 (헤더 누락, 잘못된 타입 등) |

---

## 제한사항

| 항목 | 제한 |
|------|------|
| YouTube 영상 길이 | 최대 1시간 |
| 분석 이미지 수 | 최대 10장 |
| 영상 파일 크기 | 최대 2GB |
| 이미지 파일 크기 | 최대 20MB |
| Instagram | 비로그인 모드 — 공개 포스트만 지원 |
| 목록 조회 `page_size` | 최대 100 |

---

## 통합 예시 코드

### Python

```python
import httpx

BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}


def analyze(url: str, force: bool = False) -> dict:
    with httpx.Client() as client:
        resp = client.post(
            f"{BASE_URL}/api/v1/analyze",
            headers=headers,
            json={"url": url, "force": force},
            timeout=120,  # 분석에 시간이 걸릴 수 있음
        )
        resp.raise_for_status()
        return resp.json()


def list_contents(page: int = 1, page_size: int = 20) -> dict:
    with httpx.Client() as client:
        resp = client.get(
            f"{BASE_URL}/api/v1/contents",
            headers=headers,
            params={"page": page, "page_size": page_size},
        )
        resp.raise_for_status()
        return resp.json()


# 사용 예시
result = analyze("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print(result["analysis"]["summary"])
```

### TypeScript / Node.js

```typescript
const BASE_URL = "http://localhost:8000";
const API_KEY = "your-api-key";

const headers = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json",
};

async function analyze(url: string, force = false) {
  const res = await fetch(`${BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ url, force }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(`${res.status}: ${err.detail?.code} — ${err.detail?.message}`);
  }

  return res.json();
}

async function listContents(page = 1, pageSize = 20) {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  const res = await fetch(`${BASE_URL}/api/v1/contents?${params}`, { headers });

  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

// 사용 예시
const result = await analyze("https://www.youtube.com/watch?v=dQw4w9WgXcQ");
console.log(result.analysis.summary);
```

### curl

```bash
# 분석
curl -s -X POST "http://localhost:8000/api/v1/analyze" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}' | jq .

# 목록 조회
curl -s "http://localhost:8000/api/v1/contents?page=1&page_size=10" \
  -H "X-API-Key: your-api-key" | jq .

# 새 API Key 발급 (Admin)
curl -s -X POST "http://localhost:8000/api/v1/admin/api-keys" \
  -H "X-API-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-service"}' | jq .
```
