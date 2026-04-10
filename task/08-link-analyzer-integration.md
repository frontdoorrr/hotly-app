# Task 08 — link-analyzer 연동 및 아카이빙 구조 전환

## 배경 및 목적

기존 hotly-app은 SNS 콘텐츠 추출(Playwright)과 AI 분석(Google Gemini)을 백엔드 내부에서 직접 처리했다.
이를 외부 서비스 **link-analyzer**로 위임하고, hotly-app은 **아카이빙과 사용자 경험**에 집중하는 구조로 전환한다.

### 새로운 흐름

```
Flutter 앱
  → hotly-app 백엔드 (POST /archive)
    → link-analyzer API (POST /api/v1/analyze)
      ← ContentResponse (content_type + type_specific_data)
    → DB 저장 (archived_contents)
  ← 아카이빙 결과 반환
```

### 콘텐츠 분류 체계

| content_type | 설명 |
|---|---|
| `place` | 장소/맛집/카페 방문기 |
| `event` | 팝업/공연/전시/모임 안내 |
| `tips` | 꿀팁/방법/절차 안내 |
| `review` | 제품/서비스 사용 후기 |
| `unknown` | 뉴스/에세이 등 분류 불가 |

---

## 단계별 구현 계획

---

### 1단계 — 백엔드: link-analyzer 클라이언트 + 아카이빙 API

#### 1-1. `LinkAnalyzerClient` 서비스

**파일**: `backend/app/services/link_analyzer_client.py`

**역할**: link-analyzer REST API를 호출하는 HTTP 클라이언트

**구현 내용**:
- `analyze(url: str, force: bool = False) → ContentResponse`
  - `POST /api/v1/analyze` 호출
  - 타임아웃 120초 (영상 분석 시간 고려)
  - `X-API-Key` 헤더 자동 주입
- `get_content(content_id: str) → ContentResponse`
  - `GET /api/v1/contents/{content_id}` 호출
- 에러 핸들링
  - `UNSUPPORTED_PLATFORM` → `UnsupportedPlatformError`
  - `EXTRACTION_FAILED` → `ContentExtractionError`
  - `401` → `LinkAnalyzerAuthError`

**설정값** (`core/config.py` 추가):
```
LINK_ANALYZER_BASE_URL: str
LINK_ANALYZER_API_KEY: str
```

---

#### 1-2. DB 모델 — `ArchivedContent`

**파일**: `backend/app/models/archived_content.py`

**테이블**: `archived_contents`

```
id                  UUID (PK, default gen_random_uuid())
user_id             UUID (FK → users.id, NOT NULL)
url                 TEXT (NOT NULL)
platform            ENUM(youtube, instagram, naver_blog)
content_type        ENUM(place, event, tips, review, unknown)

-- 콘텐츠 메타데이터
title               TEXT
author              TEXT
published_at        TIMESTAMPTZ
thumbnail_url       TEXT
language            VARCHAR(10)

-- 분석 공통 필드
summary             TEXT
keywords_main       TEXT[]
keywords_sub        TEXT[]
named_entities      TEXT[]
topic_categories    TEXT[]
sentiment           ENUM(positive, neutral, negative)
todos               TEXT[]
insights            TEXT[]

-- 타입별 추가 데이터
type_specific_data  JSONB

-- 앱 메타
link_analyzer_id    UUID          -- link-analyzer content.id (재조회용)
archived_at         TIMESTAMPTZ   (default now())
```

**인덱스**:
- `(user_id, content_type)` — 타입별 목록 조회
- `(user_id, archived_at DESC)` — 최신순 정렬
- `url` — 중복 저장 방지 확인용

---

#### 1-3. `type_specific_data` 스키마 정의

**파일**: `backend/app/schemas/type_specific.py`

**place**:
```python
class PlaceData(BaseModel):
    address: str | None
    hours: str | None
    menus: list[MenuItem] | None      # MenuItem(name, price)
    price_range: str | None
    reservation_required: bool | None
    visit_tips: list[str] | None
    phone: str | None
    website: str | None
```

**event**:
```python
class EventData(BaseModel):
    start_date: date | None
    end_date: date | None
    time: str | None
    venue_name: str | None
    venue_address: str | None
    ticket_price: str | None
    booking_url: str | None
    organizer: str | None
    pre_registration_required: bool | None
```

**tips**:
```python
class TipsData(BaseModel):
    tip_list: list[TipItem] | None    # TipItem(step, description)
    difficulty: Literal["easy", "medium", "hard"] | None
    materials: list[str] | None
    sub_field: str | None
    estimated_time: str | None
    cautions: list[str] | None
```

**review**:
```python
class ReviewData(BaseModel):
    product_name: str | None
    brand: str | None
    pros: list[str] | None
    cons: list[str] | None
    price: PriceInfo | None           # PriceInfo(amount, currency)
    rating: float | None              # 0.0–5.0
    recommended_for: list[str] | None
    purchase_url: str | None
```

---

#### 1-4. 아카이빙 API 엔드포인트

**파일**: `backend/app/api/api_v1/endpoints/archive.py`

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/api/v1/archive` | URL 분석 후 아카이빙 |
| `GET` | `/api/v1/archive` | 아카이빙 목록 조회 (페이지네이션 + 타입 필터) |
| `GET` | `/api/v1/archive/{id}` | 아카이빙 상세 조회 |
| `DELETE` | `/api/v1/archive/{id}` | 아카이빙 삭제 |

**`POST /api/v1/archive` 요청/응답**:
```json
// 요청
{ "url": "https://...", "force": false }

// 응답 201
{
  "id": "uuid",
  "url": "...",
  "platform": "youtube",
  "content_type": "place",
  "title": "...",
  "thumbnail_url": "...",
  "summary": "...",
  "type_specific_data": { ... },
  "archived_at": "2025-04-05T12:00:00Z"
}
```

**`GET /api/v1/archive` 쿼리 파라미터**:
```
content_type: place | event | tips | review | unknown (선택)
page: int (기본 1)
page_size: int (기본 20, 최대 100)
```

**중복 처리 정책**: 동일 user + URL이 이미 아카이빙된 경우
- `force: false` → 기존 레코드 반환 (200)
- `force: true` → link-analyzer 재분석 후 기존 레코드 업데이트 (200)

---

#### 1-5. DB 마이그레이션

**파일**: `backend/alembic/versions/xxx_add_archived_contents.py`

- `archived_contents` 테이블 생성
- ENUM 타입 생성 (`platform_type`, `content_type`, `sentiment_type`)
- 인덱스 생성

---

### 2단계 — 프론트엔드: 아카이빙 피처 교체

#### 2-1. 데이터 레이어 교체

**기존**: `features/link_analysis/` (폴링 방식, place 전용)
**신규**: `features/archive/` (동기 응답, 4가지 타입)

**파일 구조**:
```
features/archive/
├── data/
│   ├── datasources/archive_remote_datasource.dart
│   ├── models/
│   │   ├── archived_content_model.dart
│   │   ├── place_data_model.dart
│   │   ├── event_data_model.dart
│   │   ├── tips_data_model.dart
│   │   └── review_data_model.dart
│   └── repositories/archive_repository_impl.dart
├── domain/
│   ├── entities/archived_content.dart
│   └── repositories/archive_repository.dart
└── presentation/
    ├── providers/archive_provider.dart
    └── widgets/
        ├── place_card.dart
        ├── event_card.dart
        ├── tips_card.dart
        └── review_card.dart
```

**폴링 제거**: link-analyzer는 동기 응답 → 폴링 로직 불필요

---

#### 2-2. 타입별 상세 UI

| content_type | 표시 정보 |
|---|---|
| `place` | 주소, 영업시간, 메뉴/가격, 방문 팁 |
| `event` | 날짜, 장소, 티켓 가격, 예매 링크 |
| `tips` | 단계별 팁, 난이도, 준비물, 소요 시간 |
| `review` | 제품명, 평점, 장단점, 구매 링크 |
| `unknown` | summary + keywords만 표시 |

---

#### 2-3. 홈/목록 화면 업데이트

- 탭 또는 필터: 전체 / 장소 / 이벤트 / 팁 / 리뷰
- 카드 디자인: content_type별 아이콘 + 대표 정보 표시

---

### 3단계 — 기존 코드 제거

기존 기능이 신규로 완전히 대체된 이후 제거한다.

#### 백엔드 제거 대상
```
app/services/ai/                        # Gemini 분석 전체
app/services/places/                    # ContentExtractor, PlaceAnalysisService 등
app/services/media/image_processor.py   # 이미지 전처리
app/api/api_v1/endpoints/link_analysis.py
app/api/api_v1/endpoints/ai.py
app/schemas/ai.py
app/schemas/link_analysis.py
app/schemas/content.py
app/exceptions/ai.py
```

**config.py에서 제거**:
```
GEMINI_API_KEY
```

**pyproject.toml에서 제거**:
```
google-generativeai
playwright
pillow (이미지 처리용으로만 사용된 경우)
```

#### 프론트엔드 제거 대상
```
features/link_analysis/   # 신규 archive 피처로 완전 대체 후 제거
```

#### 루트 임시 파일 제거
```
debug_url_norm.py
test_gemini_video.py
gemini_analysis_result.json
```

---

## 완료 기준 (Definition of Done)

### 1단계
- [ ] `LinkAnalyzerClient`로 link-analyzer 호출 성공
- [ ] `archived_contents` 테이블 마이그레이션 완료
- [ ] `POST /api/v1/archive` — URL 입력 시 분석+저장 동작
- [ ] `GET /api/v1/archive` — 목록 + content_type 필터 동작
- [ ] `GET /api/v1/archive/{id}` — 상세 조회 동작
- [ ] `DELETE /api/v1/archive/{id}` — 삭제 동작
- [ ] 동일 URL 중복 처리 (force 옵션) 동작

### 2단계
- [ ] `archive` 피처 — URL 입력 → 분석 결과 표시 동작
- [ ] 4가지 content_type별 카드 UI 구현
- [ ] 목록 화면 타입 필터 동작

### 3단계
- [ ] 기존 AI 분석 코드 전량 제거
- [ ] 제거 후 기존 테스트 정리 (관련 테스트 삭제 또는 대체)
- [ ] 불필요 패키지 의존성 제거

---

## 환경 변수 추가 필요

```env
# .env에 추가
LINK_ANALYZER_BASE_URL=http://localhost:8000
LINK_ANALYZER_API_KEY=your-api-key
```
