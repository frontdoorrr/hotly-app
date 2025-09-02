# Task 1: 핵심 기능 개발 (Core Features Development)

## 1-1. SNS 링크 분석 백엔드 개발

### 목표
Instagram, 블로그 등 SNS 링크를 분석하여 장소 정보를 추출하는 AI 기반 시스템 구축

### 사용자 가치
- **시간 절약**: 수동 장소 입력 대신 SNS 링크로 30초 내 자동 추출
- **정확도 향상**: AI 분서으로 90% 정확도의 장소 정보 확보
- **사용성**: 복잡한 입력 없이 URL 붙여넣기만으로 장소 발견

### 가설 및 KPI
- **가설**: 링크 분석 기능으로 장소 등록 시간 80% 단축
- **측정 지표**: 
  - 분석 완료 시간 p90 30초 이내
  - AI 정확도 90% 이상
  - 캐시 적중률 40% 이상
  - 동시 처리율 100건/분

### 완료 정의 (DoD)
- [x] URL 파싱 및 메타데이터 추출 API (30초 이내 응답)
- [x] Google Gemini AI 연동 서비스 (90% 이상 정확도)
- [ ] 장소 정보 추출 및 저장 로직
- [ ] Redis 기반 캐싱 시스템 (40% 이상 캐시 적중률)
- [ ] 분석 결과 조회 API
- [ ] Circuit Breaker 패턴으로 외부 서비스 장애 대응
- [ ] 동시 분석 요청 100건/분 처리 가능

### 수용 기준
- Given Instagram URL 입력, When 링크 분석 요청, Then 30초 이내 장소 정보 반환 (p90)
- Given 중복 URL 요청, When 캐시 조회, Then 1초 이내 캐시된 결과 반환
- Given AI 서비스 장애, When Circuit Breaker 활성화, Then 우아한 실패 처리 및 재시도 안내

### 세부 작업

#### 1-1-1. URL 링크 파싱 및 메타데이터 추출 서비스
**상세**: Playwright 기반 웹 스크래핑, Instagram/YouTube/네이버블로그 지원

**TDD 구현 순서**:
1. **RED**: 콘텐츠 추출 테스트 작성
2. **GREEN**: 최소 스크래핑 기능 구현
3. **REFACTOR**: 성능 최적화 및 예외 처리 강화

**구현 체크리스트**:
- [ ] 콘텐츠 추출 테스트 작성 (`tests/test_content_extractor.py`)
- [ ] Playwright 헤드리스 브라우저 설정 (타임아웃 30초)
- [ ] 플랫폼별 스크래퍼 클래스 (UnsupportedPlatformError 예외)
- [ ] 메타데이터 추출 및 검증 (Pydantic 스키마)
- [ ] 봇 감지 회피 (지수 백오프 재시도)
- [ ] Circuit Breaker 패턴 구현 (임계값: 에러율 50%)
- [ ] 구조화 로깅 (trace_id, user_id 포함)
- [ ] PII 데이터 마스킹 (URL, 텍스트 샘플링)

**결과물**: 
- `app/services/content_extractor.py` - 콘텐츠 추출 서비스
- `app/scrapers/` - 플랫폼별 스크래퍼 모듈
- `app/schemas/content.py` - ContentData 스키마

**API**: `POST /api/v1/links/extract-content`

**데이터모델**: ContentData(url, title, description, images, text_content)

**도메인 예외 클래스**:
```python
class ContentExtractionError(Exception):
    """Content extraction failed"""
    pass

class UnsupportedPlatformError(ContentExtractionError):
    """Platform not supported for content extraction"""
    pass

class ScrapingTimeoutError(ContentExtractionError):
    """Scraping operation timed out"""
    pass
```

**재시도 정책**:
- 초기 대기: 1초
- 최대 재시도: 3회
- 백오프 비율: 2.0 (지수 증가)
- 회로 차단기 임계값: 5분간 50% 에러율

**테스트 시나리오**:
- 정상 콘텐츠 추출 (Instagram, YouTube, 블로그)
- 타임아웃 처리 (30초 초과)
- 봇 감지 회피 (다양한 User-Agent)
- 지원되지 않는 플랫폼 처리
- 네트워크 장애 시나리오

#### 1-1-2. Google Gemini AI 연동 및 프롬프트 엔지니어링
**상세**: Gemini Pro Vision 멀티모달 분석, 프롬프트 템플릿 관리

**TDD 구현 순서**:
1. **RED**: AI 분석 응답 및 예외 테스트
2. **GREEN**: 최소 Gemini API 연동
3. **REFACTOR**: 프롬프트 엔지니어링 및 성능 최적화

**구현 체크리스트**:
- [ ] AI 분석 테스트 작성 (Mock 응답 포함)
- [ ] Google AI SDK 연동 (타임아웃 60초, 레이트 리미트 대응)
- [ ] 프롬프트 템플릿 버저닝 시스템
- [ ] 멀티모달 분석 (텍스트 + 이미지, PII 마스킹)
- [ ] JSONSchema 기반 응답 검증
- [ ] 지수 백오프 재시도 (초기 1초, 최대 32초)
- [ ] 레이트 리미트 처리 (429 상태코드)
- [ ] 민감정보 비저장 원칙 (입력 데이터 최소화)

**결과물**: 
- `app/services/ai_analyzer.py` - AI 분석 서비스
- `app/prompts/` - 프롬프트 템플릿 관리
- `app/schemas/ai.py` - AI 요청/응답 스키마

**API**: `POST /api/v1/ai/analyze-place`

**데이터모델**: GeminiRequest(content, images), GeminiResponse(places, confidence)

**도메인 예외 클래스**:
```python
class AIAnalysisError(Exception):
    """AI analysis operation failed"""
    pass

class RateLimitError(AIAnalysisError):
    """AI service rate limit exceeded"""
    pass

class InvalidResponseError(AIAnalysisError):
    """AI response format invalid"""
    pass
```

**레이트 리미트 정책**:
- Gemini API: 60 RPM (requests per minute)
- 백오프 전략: 1s → 2s → 4s → 8s → 16s → 32s
- Circuit Breaker: 5분간 50% 실패율 시 회로 차단
- Graceful Degradation: AI 장애 시 수동 입력 모드 제공

**테스트 시나리오**:
- Mock Gemini 정상 응답 및 파싱
- 다양한 콘텐츠 타입 (텍스트, 이미지, 비디오)
- 레이트 리미트 에러 (429) 및 백오프
- AI 서비스 완전 장애 시나리오
- 잘못된 응답 형식 처리

#### 1-1-3. 장소 정보 추출 및 구조화 로직
**상세**: AI 응답 파싱, 데이터 검증, 신뢰도 계산

**구현 체크리스트**:
- [ ] AI 응답 파싱 로직
- [ ] 장소 정보 검증 및 정규화
- [ ] 신뢰도 점수 계산
- [ ] 주소 정규화 및 좌표 변환
- [ ] 카테고리 매핑 로직

**결과물**: 
- `app/services/place_extractor.py` - 장소 추출 서비스
- `app/utils/address_normalizer.py` - 주소 정규화 유틸리티
- `app/schemas/place_extraction.py` - 추출 결과 스키마

**API**: 내부 서비스 (직접 API 노출 안함)

**데이터모델**: PlaceExtraction(place_name, address, category, confidence)

**에러처리**: ValidationError, 필수 필드 누락 처리

**테스트**: 다양한 AI 응답 형태, 신뢰도 경계값, 데이터 품질 검증

#### 1-1-4. Redis 캐싱 및 중복 방지 시스템
**상세**: URL 해시 기반 캐싱, 분산 락, TTL 관리

**구현 체크리스트**:
- [ ] URL 해시 기반 캐시 키 생성
- [ ] 분산 락을 이용한 중복 처리 방지
- [ ] 계층적 캐시 (L1: 로컬, L2: Redis)
- [ ] TTL 관리 및 캐시 무효화
- [ ] 캐시 통계 수집

**결과물**: 
- `app/services/cache_manager.py` - 캐시 매니저
- `app/utils/hash_utils.py` - 해시 유틸리티
- `app/schemas/cache.py` - 캐시 스키마

**API**: 내부 서비스 (캐시 통계는 `/admin/cache-stats`에서 확인)

**데이터모델**: CacheEntry(data, ttl, created_at), CacheStats(hit_rate, miss_count)

**에러처리**: CacheConnectionError, graceful degradation

**테스트**: 캐시 적중/미적중 시나리오, TTL 만료, 분산 락 경합

#### 1-1-5. 링크 분석 API 엔드포인트 구현
**상세**: 비동기 분석 큐, 상태 조회, 웹훅 지원

**구현 체크리스트**:
- [ ] 비동기 분석 큐 (Celery 또는 asyncio)
- [ ] 분석 상태 추적 및 조회
- [ ] 웹훅 알림 지원
- [ ] 레이트 리미팅 미들웨어
- [ ] API 문서화 (OpenAPI)

**결과물**: 
- `app/api/v1/endpoints/link_analysis.py` - 링크 분석 API
- `app/services/analysis_queue.py` - 분석 큐 관리
- `app/webhooks/` - 웹훅 처리

**API**: 
- `POST /api/v1/links/analyze` - 분석 요청
- `GET /api/v1/analyses/{analysis_id}` - 결과 조회
- `DELETE /api/v1/analyses/{analysis_id}` - 분석 취소

**데이터모델**: LinkAnalyzeRequest, AnalysisResponse, AnalysisStatus

**에러처리**: 400(잘못된 URL), 429(레이트 리미트), 503(서비스 장애)

**테스트**: E2E 분석 플로우, 동시 요청 처리, 레이트 리미팅

#### 1-1-6. SNS 링크 분석 종합 테스트 코드 작성
**상세**: TDD 기반 전체 플로우 테스트, 성능 테스트, 부하 테스트

**구현 체크리스트**:
- [ ] 단위 테스트 (각 서비스별)
- [ ] 통합 테스트 (E2E 플로우)
- [ ] 성능 테스트 (응답 시간, 처리량)
- [ ] 부하 테스트 (동시 요청 처리)
- [ ] 장애 시나리오 테스트

**결과물**: 
- `tests/test_link_analysis.py` - 링크 분석 테스트
- `tests/performance/test_link_analysis_load.py` - 성능 테스트
- `tests/integration/test_link_analysis_e2e.py` - E2E 테스트

**커버리지**: 전체 링크 분석 기능 85% 이상 (중요 기능은 95%)

**시나리오**: 정상 분석, 캐시 적중/미적중, AI 장애, 네트워크 장애

**테스트**: 100개 동시 요청, 캐시 적중률, 메모리 사용량

---

## 1-2. 장소 관리 백엔드 개발

### 목표
사용자가 발견한 장소를 저장, 분류, 검색할 수 있는 백엔드 시스템 구축

### 완료 정의 (DoD)
- [ ] 장소 CRUD API 구현 (p95 1초 이내 응답)
- [ ] 중복 장소 방지 로직 (95% 정확도, 이름+주소+좌표 기반)
- [ ] AI 기반 자동 카테고리 분류 (80% 이상 정확도)
- [ ] 사용자 정의 태그 관리 및 자동완성
- [ ] 지리적 검색 (PostGIS 인덱스, 50km 반경)
- [ ] PostgreSQL 기반 전문 검색 (500ms 이내)

### 수용 기준
- Given 사용자가 장소를 등록함, When 중복 검사를 실행함, Then 95% 정확도로 중복 감지
- Given 장소 목록 요청, When 50km 반경 검색함, Then 거리순으로 20개씩 페이지네이션
- Given 100개 장소 데이터, When 키워드 검색함, Then 500ms 내 관련도순 결과 반환
- Given 태그 입력, When 자동완성 요청, Then 사용 빈도순 10개 태그 제안

### 세부 작업

#### 1-2-1. PostgreSQL 장소 스키마 및 인덱스 설계
**상세**: PostGIS 좌표, 사용자별 파티셔닝, 복합 인덱스 최적화

**구현 체크리스트**:
- [ ] PostGIS 확장 설치 및 설정
- [ ] places 테이블 스키마 생성
- [ ] 복합 인덱스 최적화
- [ ] 파티셔닝 전략 (사용자별)
- [ ] 검색 인덱스 (GIN, GiST) 생성

**결과물**: 
- `app/models/place.py` - SQLAlchemy ORM 모델
- `alembic/versions/xxx_create_places.py` - 마이그레이션
- `app/db/indexes.sql` - 인덱스 생성 스크립트

**스키마**: places 테이블 (user_id, place_id, name, coordinates, category, tags, status)

**인덱스**: GiST(coordinates), B-tree(user_id+category), GIN(name+address+tags)

**성능**: 지리 검색 50ms, 텍스트 검색 100ms, 필터링 50ms

**테스트**: 인덱스 성능 벤치마크, 쿼리 실행 계획 분석

#### 1-2-2. 장소 중복 방지 알고리즘 (이름+주소 정규화)
**상세**: 레벤슈타인 거리, 지리적 거리, 퍼지 매칭 조합

**구현 체크리스트**:
- [ ] 이름 정규화 알고리즘
- [ ] 주소 정규화 및 매칭
- [ ] 좌표 기반 근접 검사
- [ ] 다단계 중복 검사 로직
- [ ] 중복 확률 점수 계산

**결과물**: 
- `app/services/duplicate_detector.py` - 중복 검사 서비스
- `app/utils/text_normalizer.py` - 텍스트 정규화 유틸리티
- `app/schemas/duplicate.py` - 중복 검사 스키마

**알고리즘**: 1차(이름 정규화+유사도), 2차(주소 매칭), 3차(좌표 50m 반경)

**성능**: 중복 검사 200ms 이내, 정확도 95% 이상

**API**: `POST /api/v1/places/check-duplicate`

**테스트**: 정확/유사/다른 장소 시나리오, 성능 벤치마크

#### 1-2-3. AI 기반 자동 카테고리 분류 시스템
**상세**: scikit-learn RandomForest, TF-IDF 벡터화, 온라인 학습

**구현 체크리스트**:
- [ ] 카테고리 분류 모델 학습
- [ ] TF-IDF 벡터화 파이프라인
- [ ] 온라인 학습 시스템
- [ ] 모델 버전 관리
- [ ] 분류 신뢰도 임계값 설정

**결과물**: 
- `app/services/place_classifier.py` - 장소 분류 서비스
- `app/ml/models/` - 머신러닝 모델 저장소
- `app/ml/training/` - 모델 학습 스크립트

**모델**: TF-IDF + RandomForest (6개 카테고리 분류)

**성능**: 분류 시간 50ms, 정확도 80% 이상

**API**: `POST /api/v1/places/classify`

**테스트**: 카테고리별 분류 정확도, 신뢰도 임계값, 모델 업데이트

#### 1-2-4. 사용자 정의 태그 관리 및 자동완성
**상세**: 태그 정규화, 사용 통계, 자동완성 제안

**구현 체크리스트**:
- [ ] 태그 정규화 로직
- [ ] 사용 통계 실시간 업데이트
- [ ] 자동완성 제안 알고리즘
- [ ] 인기 태그 추천 시스템
- [ ] 태그 분류 및 그룹화

**결과물**: 
- `app/services/tag_service.py` - 태그 관리 서비스
- `app/models/tag.py` - 태그 ORM 모델
- `app/utils/tag_normalizer.py` - 태그 정규화

**기능**: 태그 추가/삭제, 자동완성, 인기 태그 추천

**성능**: 자동완성 100ms, 태그 통계 실시간 업데이트

**API**: `GET /api/v1/tags/suggestions`, `POST /api/v1/places/{id}/tags`

**테스트**: 태그 정규화, 자동완성 정확도, 사용 통계 업데이트

#### 1-2-5. 장소 CRUD API 및 검색/필터 기능
**상세**: RESTful API, 페이지네이션, 정렬, 다중 필터

**구현 체크리스트**:
- [ ] 장소 생성 API (중복 검사 포함)
- [ ] 장소 조회 API (상세/목록)
- [ ] 장소 수정 API (부분 업데이트)
- [ ] 장소 삭제 API (소프트 삭제)
- [ ] 고급 검색 및 필터링

**결과물**: 
- `app/api/v1/endpoints/places.py` - 장소 API 엔드포인트
- `app/crud/place.py` - 장소 CRUD 로직
- `app/schemas/place.py` - 장소 스키마

**API**: 
- `POST /api/v1/places` - 장소 생성
- `GET /api/v1/places` - 목록 조회 (필터/정렬/페이지네이션)
- `GET /api/v1/places/{id}` - 상세 조회
- `PUT /api/v1/places/{id}` - 정보 수정
- `DELETE /api/v1/places/{id}` - 삭제
- `PUT /api/v1/places/{id}/status` - 상태 변경

**성능**: CRUD 작업 p95 1초 이내

**테스트**: 전체 CRUD 플로우, 권한 검증, 입력 검증

#### 1-2-6. 지리적 검색 및 거리 계산 로직
**상세**: PostgreSQL PostGIS 확장, 거리 계산

**구현 체크리스트**:
- [ ] PostGIS spatial 인덱스 활용
- [ ] 반경 검색 쿼리 최적화
- [ ] 거리순 정렬 로직
- [ ] 지역별 클러스터링
- [ ] 경계값 처리

**결과물**: 
- `app/services/geo_service.py` - 지리 검색 서비스
- `app/utils/distance_calculator.py` - 거리 계산 유틸리티
- `app/schemas/geo.py` - 지리 정보 스키마

**기능**: 반경 검색, 거리순 정렬, 지역별 클러스터링

**성능**: 지리 검색 100ms, 1000개 장소 대상 성능 유지

**API**: `GET /api/v1/places/nearby?lat={lat}&lng={lng}&radius={km}`

**테스트**: 다양한 반경/위치, 거리 계산 정확도, 경계값 테스트

#### 1-2-7. PostgreSQL 전문 검색 시스템
**상세**: PostgreSQL full-text search, 한국어 형태소 분석, 하이브리드 검색

**구현 체크리스트**:
- [ ] PostgreSQL tsvector 검색 설정
- [ ] 한국어 텍스트 분석 설정
- [ ] 검색 순위 알고리즘
- [ ] 퍼지 매칭 및 자동완성
- [ ] 검색어 하이라이팅

**결과물**: 
- `app/services/search_service.py` - 검색 서비스
- `app/utils/korean_analyzer.py` - 한국어 분석기
- `app/schemas/search.py` - 검색 스키마

**기능**: 전문 검색, 퍼지 매칭, 검색어 하이라이팅, 자동완성

**성능**: 검색 응답 500ms 이내, 자동완성 100ms

**API**: `GET /api/v1/places/search?q={query}&category={cat}&tags={tags}`

**테스트**: 검색 정확도, 한국어 검색, 복합 필터, 성능 테스트

#### 1-2-8. 장소 관리 종합 테스트 코드 작성
**상세**: 전체 플로우 통합 테스트, 성능 테스트, 부하 테스트

**구현 체크리스트**:
- [ ] E2E 통합 테스트 시나리오
- [ ] 성능 벤치마크 테스트
- [ ] 부하 테스트 (동시 사용자)
- [ ] 데이터 무결성 테스트
- [ ] 보안 취약점 테스트

**결과물**: 
- `tests/test_place_management.py` - 장소 관리 통합 테스트
- `tests/performance/test_place_performance.py` - 성능 테스트
- `tests/security/test_place_security.py` - 보안 테스트

**커버리지**: 전체 장소 관리 기능 80% 이상

**시나리오**: 생성→검색→수정→삭제, 중복 처리, 상태 전이

**성능**: 동시 사용자 100명, 메모리 누수 검사

---

## 1-3. AI 기반 코스 추천 백엔드 개발

### 목표
사용자 취향 및 위치 기반으로 최적화된 데이트 코스를 AI가 추천하는 시스템

### 완료 정의 (DoD)
- [ ] 사용자 취향 분석 70% 정확도 (피드백 기반 학습)
- [ ] 실시간 위치 기반 코스 추천
- [ ] 다양한 코스 타입 5개 이상 (로맨틱, 액티비티, 맛집 등)

### 수용 기준
- Given 5개 이상 취향 데이터, When 코스 추천 요청, Then 3가지 이상 코스 타입 제공
- Given 코스 추천 결과, When 실시간 위치 확인, Then Google Maps API 기반 경로 정보 제공

### 세부 작업

#### 1-3-1. 사용자 취향 분석 및 프로파일링 시스템
**구현 체크리스트**:
- [ ] 사용자 행동 데이터 수집
- [ ] 취향 분석 알고리즘 구현
- [ ] 프로파일링 모델 학습
- [ ] 피드백 기반 학습 시스템
- [ ] 취향 변화 추적

#### 1-3-2. 장소 간 실시간 위치 확인 및 거리 알고리즘
**구현 체크리스트**:
- [ ] 실시간 위치 기반 거리 계산
- [ ] 경로 최적화 알고리즘
- [ ] 교통수단별 이동시간 계산
- [ ] 실시간 교통정보 연동
- [ ] 경로 대안 제시

#### 1-3-3. AI 기반 코스 추천 엔진 및 타입 분류
**구현 체크리스트**:
- [ ] 추천 알고리즘 구현
- [ ] 코스 타입 분류 시스템
- [ ] 다양성 보장 알고리즘
- [ ] 실시간 추천 업데이트
- [ ] A/B 테스트 프레임워크

#### 1-3-4. 추천 결과 API 및 사용자 피드백 수집
**구현 체크리스트**:
- [ ] 추천 결과 API 구현
- [ ] 피드백 수집 시스템
- [ ] 추천 품질 평가
- [ ] 개인화 학습 피드백 루프
- [ ] 추천 설명 제공

#### 1-3-5. 코스 추천 UI 연동 및 최적화 로직
**구현 체크리스트**:
- [ ] 실시간 추천 업데이트
- [ ] 캐싱 최적화
- [ ] 배치 추천 처리
- [ ] 추천 결과 개인화
- [ ] 성능 모니터링

#### 1-3-6. 코스 추천 테스트 코드 작성
**구현 체크리스트**:
- [ ] 추천 정확도 테스트
- [ ] 다양성 검증 테스트
- [ ] 성능 테스트
- [ ] 피드백 루프 테스트
- [ ] A/B 테스트 검증

---

## 1-4. 지도 기반 시각화 백엔드 개발

### 목표
추천된 코스를 지도 위에 시각적으로 표현하고 사용자에게 직관적인 경로 제공

### 완료 정의 (DoD)
- [ ] Kakao Map SDK 연동 완료
- [ ] 지도 데이터 최적화로 100개 이상 마커 1초 내 렌더링
- [ ] 코스 경로 표시 및 소요시간 계산 정확도

### 수용 기준
- Given 50개 이상 장소 마커, When 지도 로딩/줌인함, Then 60fps 유지하며 데이터 표시
- Given 코스 선택, When 경로 표시 요청, Then 2초 이내 경로 정보 표시

### 세부 작업

#### 1-4-1. Kakao Map SDK 연동 및 기본 지도 로딩
**구현 체크리스트**:
- [ ] Kakao Map API 키 설정
- [ ] 지도 초기화 및 설정
- [ ] 기본 마커 표시
- [ ] 지도 이벤트 처리
- [ ] 모바일 최적화

#### 1-4-2. 마커 클러스터링 및 지도 데이터 최적화
**구현 체크리스트**:
- [ ] 마커 클러스터링 알고리즘
- [ ] 줌 레벨별 데이터 최적화
- [ ] 뷰포트 기반 데이터 로딩
- [ ] 마커 아이콘 최적화
- [ ] 렌더링 성능 튜닝

#### 1-4-3. 코스 경로 표시 및 인터랙션 구현
**구현 체크리스트**:
- [ ] 경로 폴리라인 표시
- [ ] 순서별 마커 번호
- [ ] 드래그 앤 드롭 순서 변경
- [ ] 경로 상세 정보 표시
- [ ] 인터랙티브 경로 편집

#### 1-4-4. 지도 상 장소 상세정보 팝업 및 액션
**구현 체크리스트**:
- [ ] 인포윈도우 커스터마이징
- [ ] 장소 상세 정보 표시
- [ ] 액션 버튼 (저장, 공유, 경로)
- [ ] 이미지 갤러리 표시
- [ ] 리뷰 및 평점 표시

#### 1-4-5. 소요시간 및 거리 기반 지도 최적화
**구현 체크리스트**:
- [ ] 실시간 거리/시간 계산
- [ ] 교통상황 고려 경로
- [ ] 대중교통 연동
- [ ] 최적 경로 제안
- [ ] 경로 대안 제시

#### 1-4-6. 지도 시각화 테스트 코드 작성
**구현 체크리스트**:
- [ ] 지도 로딩 성능 테스트
- [ ] 마커 클러스터링 테스트
- [ ] 경로 계산 정확도 테스트
- [ ] UI 인터랙션 테스트
- [ ] 모바일 반응형 테스트

---

## 1-5. 코스 공유 및 저장 백엔드 개발

### 목표
완성된 코스를 다른 사용자에게 공유하고 즐겨찾기 할 수 있는 소셜 기능

### 완료 정의 (DoD)
- [ ] 코스 링크 공유 및 소유권 저장 기능
- [ ] 좋아요 및 댓글 시스템으로 사용자 상호작용 구현
- [ ] 개인 저장 (즐겨찾기/위시리스트) 기능

### 수용 기준
- Given 코스 공유 링크, When 외부에서 접근함, Then 즐겨찾기 없이 코스 정보 표시
- Given 저장된 코스 목록, When 소유자가 삭제 요청함, Then 연결된 공유링크 1초 이내 무효화

### 세부 작업

#### 1-5-1. 코스 공유 링크 생성 및 개인 저장 시스템
**구현 체크리스트**:
- [ ] 고유 공유 링크 생성
- [ ] 공유 권한 및 만료 관리
- [ ] 개인 즐겨찾기 시스템
- [ ] 폴더 기반 분류
- [ ] 공유 통계 수집

#### 1-5-2. 소유권 기반 저장 기능 (WebSocket 기반)
**구현 체크리스트**:
- [ ] WebSocket 연결 관리
- [ ] 실시간 코스 상태 동기화
- [ ] 소유권 검증 시스템
- [ ] 충돌 해결 메커니즘
- [ ] 오프라인 동기화

#### 1-5-3. 좋아요, 댓글, 평가 시스템 로직
**구현 체크리스트**:
- [ ] 좋아요 시스템 구현
- [ ] 댓글 및 대댓글 시스템
- [ ] 평가 및 리뷰 시스템
- [ ] 신고 및 모더레이션
- [ ] 소셜 알림 연동

#### 1-5-4. 공유 코스 UI/UX 및 소셜 기능 백엔드
**구현 체크리스트**:
- [ ] 공유 페이지 렌더링
- [ ] 소셜 미디어 메타태그
- [ ] 임베드 코드 생성
- [ ] 공유 분석 대시보드
- [ ] 바이럴 요소 추가

#### 1-5-5. 개인 폴더 및 태그 분류 시스템
**구현 체크리스트**:
- [ ] 개인 폴더 관리
- [ ] 태그 기반 분류
- [ ] 스마트 컬렉션
- [ ] 검색 및 필터링
- [ ] 백업 및 동기화

#### 1-5-6. 코스 공유 테스트 코드 작성
**구현 체크리스트**:
- [ ] 공유 플로우 테스트
- [ ] 권한 검증 테스트
- [ ] 소셜 기능 테스트
- [ ] 성능 테스트
- [ ] 보안 테스트

---

## 참고 문서
- `prd/01-sns-link-analysis.md` - SNS 링크 분석 요구사항
- `prd/02-place-management.md` - 장소 관리 요구사항
- `prd/03-course-recommendation.md` - 코스 추천 요구사항
- `prd/04-map-visualization.md` - 지도 시각화 요구사항
- `prd/05-sharing-system.md` - 공유 시스템 요구사항
- `trd/01-sns-link-analysis.md` - SNS 링크 분석 기술 설계
- `trd/02-place-management.md` - 장소 관리 기술 설계
- `trd/03-course-recommendation.md` - 코스 추천 기술 설계
- `trd/04-map-visualization.md` - 지도 시각화 기술 설계
- `trd/05-sharing-system.md` - 공유 시스템 기술 설계
- `database-schema.md` - 데이터베이스 스키마
- `rules.md` - 개발 규칙

---

*작성일: 2025-01-XX*  
*작성자: Claude*  
*버전: 1.0*