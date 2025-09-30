# Hotly App - Backend Architecture Documentation

> **버전**: 1.0
> **작성일**: 2025-09-30
> **최종 업데이트**: 2025-09-30

## 목차

1. [시스템 개요](#시스템-개요)
2. [아키텍처 패턴](#아키텍처-패턴)
3. [계층별 구조](#계층별-구조)
4. [인프라 구성](#인프라-구성)
5. [핵심 데이터 흐름](#핵심-데이터-흐름)
6. [보안 및 인증](#보안-및-인증)
7. [성능 최적화](#성능-최적화)
8. [외부 서비스 통합](#외부-서비스-통합)
9. [개발 가이드](#개발-가이드)

---

## 시스템 개요

### 프로젝트 소개
**Hotly App**은 SNS 링크에서 장소 정보를 추출하고, AI 기반으로 최적화된 데이트 코스를 추천하는 모바일 애플리케이션의 백엔드 시스템입니다.

### 기술 스택

#### Backend Framework
- **FastAPI** 0.109.0 - 고성능 비동기 Python 웹 프레임워크
- **Python** 3.10+ - 타입 힌팅 및 최신 언어 기능 활용
- **Pydantic** 1.10.0 - 데이터 검증 및 설정 관리
- **Poetry** - 의존성 관리 및 패키징

#### Database & Storage
- **PostgreSQL** - 주 데이터베이스 (장소, 사용자, 코스 데이터)
- **PostGIS** - 지리 공간 데이터 처리 확장
- **Redis** - 멀티레이어 캐싱 및 세션 관리
- **Elasticsearch** 8.11.0 - 전문 검색 엔진 (한국어 nori 분석기)

#### AI & External Services
- **Google Gemini** - AI 기반 장소 분석 및 카테고리 분류
- **Firebase Admin** - 인증 및 푸시 알림 (FCM)
- **Kakao Map API** - 지도 및 위치 서비스
- **geopy** - 지리적 거리 계산

#### Infrastructure & Monitoring
- **SQLAlchemy** 1.4.0 - ORM 및 데이터베이스 추상화
- **Alembic** - 데이터베이스 마이그레이션
- **Celery** - 비동기 작업 큐 (Redis 백엔드)
- **GitHub Actions** - CI/CD 파이프라인

---

## 아키텍처 패턴

### 1. Service-Oriented Architecture (SOA)

시스템은 **서비스 지향 아키텍처**를 채택하여 각 비즈니스 로직을 독립적인 서비스로 분리합니다.

```
┌──────────────────────────────────────────────────────────────┐
│                        API Layer                              │
│  (FastAPI Routers - 17개의 독립적인 엔드포인트 모듈)           │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                      Service Layer                            │
│  (60+ 독립 서비스 - 비즈니스 로직 캡슐화)                      │
│  • Content Extraction  • AI Analysis  • Caching               │
│  • Search & Ranking    • Notification • Recommendation        │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│                       Data Layer                              │
│  • PostgreSQL (ORM)  • Redis (Cache)  • Elasticsearch (Search)│
└──────────────────────────────────────────────────────────────┘
```

### 2. Clean Architecture 원칙

- **의존성 역전**: 상위 계층이 하위 계층에 의존하지 않도록 인터페이스 활용
- **단일 책임**: 각 서비스는 하나의 명확한 책임만 가짐
- **독립성**: 서비스 간 낮은 결합도로 테스트 및 유지보수 용이

### 3. Test-Driven Development (TDD)

- **80%+ 코드 커버리지** 유지
- RED-GREEN-REFACTOR 사이클 준수
- 단위 → 통합 → E2E 테스트 피라미드 구조

---

## 계층별 구조

### API Layer (`app/api/`)

FastAPI 라우터를 통한 RESTful API 제공.

#### 주요 엔드포인트 모듈

| 엔드포인트 | 경로 | 설명 | 주요 기능 |
|-----------|------|------|-----------|
| **링크 분석** | `/api/v1/links` | SNS 링크 분석 | URL 파싱, AI 분석, 캐싱 |
| **장소 관리** | `/api/v1/places` | 장소 CRUD | 생성, 검색, 필터, 중복 방지 |
| **코스 추천** | `/api/v1/courses` | AI 코스 생성 | TSP 최적화, 카테고리 다양성 |
| **검색** | `/api/v1/search` | 전문 검색 | Elasticsearch, 자동완성 |
| **알림** | `/api/v1/notifications` | 푸시 알림 | FCM, 스케줄링, 개인화 |
| **온보딩** | `/api/v1/onboarding` | 사용자 온보딩 | 취향 설정, 가이드 |
| **사용자 데이터** | `/api/v1/user-data` | 사용자 정보 | 프로필, 활동 로그, GDPR |
| **성능 모니터링** | `/api/v1/performance` | 시스템 지표 | APM, 메트릭, 대시보드 |

#### API 라우터 등록 흐름

```python
# app/main.py
app = create_app()
  ├─ app.include_router(health_router)                    # 헬스체크
  └─ app.include_router(api_router, prefix="/api/v1")    # API v1

# app/api/api_v1/api.py
api_router = APIRouter()
  ├─ link_analysis.router    (prefix="/links")
  ├─ places.router           (prefix="/places")
  ├─ courses.router          (prefix="/courses")
  ├─ search.router           (prefix="/search")
  ├─ notifications.router    (prefix="/notifications")
  └─ ... (17개 라우터)
```

#### 요청/응답 흐름

```
Client Request
     │
     ▼
[FastAPI Router] ──────────────────────────┐
     │                                     │
     ▼                                     │
[Dependency Injection] ◄───────────────────┘
     │ (get_db, get_current_user, etc.)
     ▼
[Pydantic Schema Validation]
     │ (Request → Domain Object)
     ▼
[Service Layer Call]
     │ (Business Logic)
     ▼
[Data Layer Access]
     │ (PostgreSQL / Redis / Elasticsearch)
     ▼
[Response Schema Serialization]
     │ (Domain Object → JSON)
     ▼
Client Response
```

---

### Service Layer (`app/services/`)

비즈니스 로직을 캡슐화한 60개 이상의 독립 서비스.

#### 핵심 서비스 카테고리

##### 1. Content & Analysis (콘텐츠 분석)
```
content_extractor.py          # SNS 콘텐츠 추출 (Instagram, Naver, YouTube)
place_analysis_service.py     # AI 기반 장소 분석 (Gemini)
category_classifier.py        # 자동 카테고리 분류 (하이브리드 AI)
duplicate_detector.py         # 중복 장소 감지 (Levenshtein + GIS)
place_extractor.py            # 장소 정보 파싱
```

##### 2. Recommendation & Optimization (추천 최적화)
```
course_recommender.py         # 코스 추천 엔진 (TSP + 2-Opt)
travel_time_calculator.py     # 이동 시간 계산
ml_engine.py                  # 머신러닝 기반 추천
personalization_engine.py     # 개인화 엔진
```

##### 3. Search & Discovery (검색 시스템)
```
search_service.py             # Elasticsearch 통합 검색
autocomplete_service.py       # 자동완성 제안
search_ranking_service.py     # 검색 결과 랭킹
search_optimization_service.py # 검색 성능 최적화
search_analytics_service.py   # 검색 분석
```

##### 4. Caching & Performance (캐싱 및 성능)
```
cache_manager.py              # 멀티레이어 캐싱 (L1: Memory, L2: Redis)
redis_queue.py                # Redis 기반 작업 큐
performance_service.py        # 성능 모니터링
cdn_service.py                # CDN 통합
```

##### 5. Notification System (알림 시스템)
```
notification_service.py       # 알림 전송 오케스트레이션
fcm_service.py                # Firebase Cloud Messaging
notification_scheduler.py     # 알림 스케줄링
personalized_notification_service.py # 개인화 알림
ml_notification_optimizer.py  # ML 기반 타이밍 최적화
```

##### 6. User & Preferences (사용자 관리)
```
user_preference_service.py    # 사용자 취향 관리
user_data_service.py          # 사용자 데이터 CRUD
onboarding_service.py         # 온보딩 플로우
feedback_service.py           # 피드백 수집 및 분석
```

##### 7. Analytics & Monitoring (분석 및 모니터링)
```
user_behavior_analytics_service.py  # 사용자 행동 분석
performance_monitoring_service.py   # 성능 지표 수집
logging_service.py                  # 구조화된 로깅
ab_testing_service.py               # A/B 테스트 프레임워크
```

#### 서비스 패턴 예시

```python
# 서비스 간 의존성 주입 패턴
class CourseRecommender:
    def __init__(
        self,
        distance_weight: float = 0.7,
        diversity_weight: float = 0.3,
    ):
        self.distance_weight = distance_weight
        self.diversity_weight = diversity_weight

    def recommend_course(
        self,
        places: List[PlaceCreate],
        start_location: Optional[Tuple[float, float]] = None
    ) -> CourseRecommendation:
        # 비즈니스 로직만 집중
        optimized_order = self._optimize_order(places, start_location)
        places_in_course = self._calculate_travel_info(optimized_order)
        return CourseRecommendation(...)
```

---

### Data Layer (`app/models/`, `app/crud/`, `app/db/`)

#### 데이터베이스 구조

##### PostgreSQL 주요 테이블

| 테이블 | 설명 | 주요 컬럼 | 인덱스 |
|--------|------|-----------|--------|
| **users** | 사용자 정보 | id, email, firebase_uid | B-tree(email), B-tree(firebase_uid) |
| **places** | 장소 데이터 | id, user_id, name, coordinates, category | GiST(coordinates), GIN(name, address) |
| **user_preferences** | 사용자 취향 | user_id, categories, tags | B-tree(user_id) |
| **notifications** | 알림 기록 | id, user_id, type, status | B-tree(user_id, created_at) |
| **user_devices** | 디바이스 토큰 | id, user_id, fcm_token | B-tree(user_id), B-tree(fcm_token) |

##### PostgreSQL 확장 기능

```sql
-- 지리 공간 데이터 처리
CREATE EXTENSION postgis;

-- 전문 검색 (pg_trgm - 유사도 검색)
CREATE EXTENSION pg_trgm;

-- GiST 인덱스 (지리 공간 쿼리 최적화)
CREATE INDEX idx_places_coordinates ON places USING GIST(coordinates);

-- GIN 인덱스 (전문 검색 최적화)
CREATE INDEX idx_places_search ON places USING GIN(
    to_tsvector('korean', name || ' ' || address)
);
```

#### Redis 키 네임스페이스

```
hotly:cache:{service}:{key}           # L2 캐시 데이터
hotly:session:{user_id}:{session_id}  # 세션 데이터
hotly:queue:{task_name}               # Celery 작업 큐
hotly:rate_limit:{endpoint}:{user_id} # 레이트 리미팅
hotly:analytics:{metric}:{timestamp}  # 실시간 분석 지표
```

#### Elasticsearch 인덱스 구조

```json
// hotly_places 인덱스 매핑
{
  "mappings": {
    "properties": {
      "place_id": {"type": "keyword"},
      "name": {
        "type": "text",
        "analyzer": "nori",           // 한국어 형태소 분석
        "fields": {
          "keyword": {"type": "keyword"},
          "autocomplete": {
            "type": "text",
            "analyzer": "autocomplete"
          }
        }
      },
      "address": {"type": "text", "analyzer": "nori"},
      "category": {"type": "keyword"},
      "tags": {"type": "keyword"},
      "coordinates": {"type": "geo_point"},
      "created_at": {"type": "date"}
    }
  }
}
```

#### ORM 모델 예시

```python
# app/models/place.py
from sqlalchemy import Column, String, Enum, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry

class Place(Base):
    __tablename__ = "places"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500))
    coordinates = Column(Geometry('POINT', srid=4326), index=True)  # PostGIS
    category = Column(Enum(PlaceCategory), index=True)
    tags = Column(JSONB, default=list)
    status = Column(Enum(PlaceStatus), default=PlaceStatus.ACTIVE)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # 복합 인덱스
    __table_args__ = (
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_name_address_gin', 'name', 'address', postgresql_using='gin'),
    )
```

---

## 인프라 구성

### 시스템 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                       │
│                  (iOS / Android / Web Browser)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Load Balancer                            │
│                      (Future: Nginx/ALB)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│                    (Uvicorn ASGI Server)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  API Layer (17 Routers)                                   │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  Service Layer (60+ Services)                             │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  CRUD / ORM Layer                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────┬─────────┬─────────┬────────────┬────────────────────────┘
       │         │         │            │
       ▼         ▼         ▼            ▼
 ┌─────────┐ ┌──────┐ ┌──────────┐ ┌──────────────────┐
 │PostgreSQL│ │Redis │ │Elasticsearch│ │External Services│
 │         │ │      │ │          │ │  • Firebase      │
 │ • Places│ │• L2  │ │• Search  │ │  • Gemini AI     │
 │ • Users │ │Cache │ │• Nori    │ │  • Kakao Map     │
 │ • Logs  │ │• Queue│ │          │ └──────────────────┘
 └─────────┘ └──────┘ └──────────┘
```

### 환경 설정 관리

```python
# app/core/config.py
class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Hotly App"

    # Database URLs (자동 조합)
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:..."

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/..."

    # 환경변수 기반 설정
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()  # 싱글톤 인스턴스
```

### 의존성 주입 (Dependency Injection)

```python
# app/api/deps.py
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db() -> Generator:
    """PostgreSQL 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """현재 인증된 사용자"""
    # JWT 토큰 검증 로직
    return user

# 엔드포인트에서 사용
@router.get("/places")
async def get_places(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return place_crud.get_multi(db, user_id=current_user.id)
```

---

## 핵심 데이터 흐름

### 1. SNS 링크 분석 플로우 (Task 1-1)

```
사용자 → Instagram URL 입력
    │
    ▼
[POST /api/v1/links/analyze]
    │
    ├─ 1. URL 검증 및 중복 체크 (Redis Cache)
    │   └─ Cache Hit? → 즉시 캐시 결과 반환 (1초 이내)
    │
    ├─ 2. ContentExtractor 서비스
    │   ├─ Playwright로 웹 스크래핑
    │   ├─ 메타데이터 추출 (title, images, text)
    │   └─ 플랫폼별 파서 (Instagram, Naver, YouTube)
    │
    ├─ 3. PlaceAnalysisService (AI)
    │   ├─ Google Gemini API 호출
    │   ├─ 멀티모달 분석 (텍스트 + 이미지)
    │   ├─ 장소 정보 추출 (이름, 주소, 카테고리)
    │   └─ 신뢰도 점수 계산 (0.0 ~ 1.0)
    │
    ├─ 4. CacheManager
    │   ├─ L1 캐시 (메모리) 저장 - 10분 TTL
    │   └─ L2 캐시 (Redis) 저장 - 1시간 TTL
    │
    └─ 5. 응답 반환
        └─ {places: [...], confidence: 0.95, cached: false}
```

**성능 지표**:
- p90: 30초 이내 (AI 분석 포함)
- 캐시 적중 시: 1초 이내
- 캐시 적중률: 40% 이상

---

### 2. AI 코스 추천 플로우 (Task 1-3)

```
사용자 → 3-6개 장소 선택
    │
    ▼
[POST /api/v1/courses/recommend]
    │
    ├─ 1. 입력 검증 (3-6개 장소)
    │
    ├─ 2. 장소 데이터 조회 (PostgreSQL)
    │   └─ place_crud.get_multi(db, place_ids)
    │
    ├─ 3. CourseRecommender 서비스
    │   ├─ a. Nearest Neighbor 초기 경로
    │   │   ├─ 모든 장소를 시작점으로 시도
    │   │   └─ 가장 짧은 초기 경로 선택
    │   │
    │   ├─ b. 2-Opt 최적화
    │   │   ├─ 경로 세그먼트 역순 시도
    │   │   └─ 거리 개선 시 경로 업데이트
    │   │
    │   ├─ c. 카테고리 다양성 검증
    │   │   └─ 연속 동일 카테고리 <= 2개
    │   │
    │   └─ d. 이동 정보 계산
    │       ├─ geopy.distance로 거리 계산
    │       └─ 평균 이동 속도로 시간 추정
    │
    └─ 4. 응답 반환
        └─ {
             places: [{position, travel_distance_km, ...}],
             total_distance_km: 12.5,
             total_duration_minutes: 420,
             optimization_score: 0.85
           }
```

**알고리즘 특징**:
- TSP (Traveling Salesman Problem) 근사 해법
- 시간 복잡도: O(n³) (n <= 6이므로 실용적)
- 최적화율: 최악 경로 대비 30% 이상 개선

---

### 3. 검색 플로우 (Task 2-3)

```
사용자 → 검색어 입력 "강남 카페"
    │
    ▼
[GET /api/v1/search?q=강남 카페&category=cafe]
    │
    ├─ 1. SearchService (Elasticsearch)
    │   ├─ 한국어 형태소 분석 (nori analyzer)
    │   ├─ 다중 필드 매칭 (name, address, tags)
    │   ├─ 카테고리/태그 필터 적용
    │   └─ 지리 공간 필터 (선택적)
    │
    ├─ 2. SearchRankingService
    │   ├─ TF-IDF 기반 관련도 스코어
    │   ├─ 개인화 가중치 (사용자 취향)
    │   ├─ 인기도 부스팅 (조회수, 저장 횟수)
    │   └─ 최신성 부스팅 (최근 등록 장소)
    │
    ├─ 3. SearchCacheService
    │   ├─ 인기 검색어는 Redis 캐싱
    │   └─ TTL: 5분
    │
    └─ 4. 응답 반환
        └─ {
             results: [{place_id, name, score, ...}],
             total: 42,
             aggregations: {categories: {...}}
           }
```

**성능 목표**:
- 검색 응답 시간: p95 500ms 이내
- 자동완성: 100ms 이내
- 동시 검색 요청: 1000 QPS

---

## 보안 및 인증

### Firebase Authentication 통합

```
사용자 → 로그인 (Google/Apple/Kakao)
    │
    ▼
[Firebase Auth SDK] (클라이언트)
    │
    ├─ OAuth 인증 플로우
    ├─ ID Token 발급 (JWT)
    └─ 클라이언트에 토큰 저장

사용자 → API 요청 (Header: Authorization: Bearer <token>)
    │
    ▼
[FastAPI Middleware]
    │
    ├─ 1. JWT 토큰 검증 (firebase-admin)
    ├─ 2. 토큰 만료 확인
    ├─ 3. 사용자 권한 확인
    └─ 4. current_user 컨텍스트 설정

API 엔드포인트
    │
    └─ current_user = Depends(get_current_user)
```

### 보안 계층

#### 1. 입력 검증 (Pydantic)
```python
class PlaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., max_length=500)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    category: PlaceCategory  # Enum 검증
```

#### 2. 레이트 리미팅
```python
# app/middleware/rate_limiter.py
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Redis 기반 토큰 버킷 알고리즘
    # - 일반 사용자: 100 req/min
    # - 인증 엔드포인트: 10 req/min
    pass
```

#### 3. SQL Injection 방어
- SQLAlchemy ORM 사용 (파라미터화된 쿼리)
- 직접 SQL 작성 시 `text()` 바인딩 필수

#### 4. XSS 방어
- Pydantic 스키마 검증
- HTML 이스케이핑 (응답 시)

#### 5. 민감 정보 보호
```python
# 로깅 시 자동 마스킹
def sanitize_log(data: dict) -> dict:
    SENSITIVE_FIELDS = ['password', 'token', 'api_key']
    return {k: '***' if k in SENSITIVE_FIELDS else v
            for k, v in data.items()}
```

---

## 성능 최적화

### 1. 멀티레이어 캐싱 전략

```python
class CacheManager:
    def __init__(self):
        self.l1_cache = {}  # 메모리 (10분 TTL)
        self.redis_client = Redis()  # L2 (1시간 TTL)

    async def get(self, key: str) -> Optional[Any]:
        # L1 조회
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2 조회
        value = await self.redis_client.get(key)
        if value:
            self.l1_cache[key] = value  # L1 승격
            return value

        return None
```

**캐싱 대상**:
- SNS 링크 분석 결과 (URL 해시 기반)
- 사용자 취향 데이터
- 인기 검색 결과
- 장소 상세 정보

### 2. 데이터베이스 쿼리 최적화

#### a. N+1 문제 해결
```python
# 안티패턴 (N+1 쿼리)
places = db.query(Place).all()
for place in places:
    user = place.user  # 각 장소마다 쿼리 1번씩

# 최적화 (조인)
places = db.query(Place).options(
    joinedload(Place.user)  # 단 1번의 쿼리
).all()
```

#### b. 인덱스 활용
```sql
-- 지리 공간 쿼리 최적화
EXPLAIN ANALYZE
SELECT * FROM places
WHERE ST_DWithin(
    coordinates,
    ST_SetSRID(ST_MakePoint(127.027, 37.498), 4326),
    50000  -- 50km 반경
);
-- → GiST 인덱스 사용 확인
```

#### c. 페이지네이션
```python
@router.get("/places")
async def get_places(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    # OFFSET/LIMIT 페이징
    places = place_crud.get_multi(db, skip=skip, limit=limit)
    return places
```

### 3. 비동기 처리

#### Celery 작업 큐
```python
@celery_app.task
def send_notification_batch(notification_ids: List[str]):
    """비동기 푸시 알림 전송"""
    for notification_id in notification_ids:
        fcm_service.send(notification_id)

# API 엔드포인트에서 호출
send_notification_batch.delay(notification_ids)  # 즉시 반환
```

### 4. 연결 풀 관리

```python
# PostgreSQL 연결 풀
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_size=20,          # 최대 20개 연결 유지
    max_overflow=10,       # 초과 시 10개까지 생성
    pool_pre_ping=True,    # 연결 유효성 자동 확인
    pool_recycle=3600,     # 1시간마다 연결 재생성
)
```

---

## 외부 서비스 통합

### 1. Google Gemini (AI 분석)

```python
# app/services/place_analysis_service.py
import google.generativeai as genai

class PlaceAnalysisService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro-vision')

    async def analyze_content(
        self,
        text: str,
        images: List[str]
    ) -> PlaceAnalysis:
        prompt = f"""
        다음 SNS 게시물에서 장소 정보를 추출하세요:

        내용: {text}

        JSON 형식으로 응답:
        {{
          "place_name": "장소 이름",
          "address": "주소",
          "category": "카테고리",
          "confidence": 0.0-1.0
        }}
        """

        response = await self.model.generate_content([
            prompt,
            *images
        ])

        return self._parse_response(response.text)
```

**에러 처리**:
- 지수 백오프 재시도 (3회)
- Circuit Breaker 패턴 (실패율 50% 시 차단)
- Fallback: 규칙 기반 분석

### 2. Firebase Cloud Messaging (푸시 알림)

```python
# app/services/fcm_service.py
from firebase_admin import messaging

class FCMService:
    async def send_notification(
        self,
        token: str,
        title: str,
        body: str
    ) -> bool:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(sound="default")
                )
            ),
            android=messaging.AndroidConfig(
                priority='high',
                ttl=3600,  # 1시간
            ),
        )

        try:
            response = messaging.send(message)
            logger.info(f"FCM sent: {response}")
            return True
        except Exception as e:
            logger.error(f"FCM error: {e}")
            return False
```

### 3. Kakao Map API (지도 서비스)

```python
# app/services/map_service.py
class MapService:
    def __init__(self):
        self.api_key = settings.KAKAO_API_KEY
        self.base_url = "https://dapi.kakao.com/v2/local"

    async def search_address(self, query: str) -> List[Address]:
        """주소 검색 API"""
        headers = {"Authorization": f"KakaoAK {self.api_key}"}
        response = await httpx.get(
            f"{self.base_url}/search/address.json",
            headers=headers,
            params={"query": query}
        )
        return response.json()["documents"]
```

---

## 개발 가이드

### 새로운 API 엔드포인트 추가

#### 1. 스키마 정의 (`app/schemas/`)
```python
# app/schemas/place.py
class PlaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class PlaceResponse(BaseModel):
    id: str
    name: str
    address: str
    created_at: datetime

    class Config:
        orm_mode = True
```

#### 2. 서비스 로직 (`app/services/`)
```python
# app/services/place_service.py
class PlaceService:
    def __init__(self, db: Session):
        self.db = db

    def create_place(self, place_data: PlaceCreate) -> Place:
        # 비즈니스 로직
        place = Place(**place_data.dict())
        self.db.add(place)
        self.db.commit()
        return place
```

#### 3. API 엔드포인트 (`app/api/api_v1/endpoints/`)
```python
# app/api/api_v1/endpoints/places.py
@router.post("/", response_model=PlaceResponse)
async def create_place(
    place_data: PlaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = PlaceService(db)
    place = service.create_place(place_data)
    return place
```

#### 4. 테스트 작성 (`tests/`)
```python
# tests/unit/test_place_service.py
def test_create_place_valid_data_success():
    # Given
    place_data = PlaceCreate(
        name="강남 카페",
        address="서울시 강남구",
        latitude=37.498,
        longitude=127.027
    )

    # When
    place = place_service.create_place(place_data)

    # Then
    assert place.name == "강남 카페"
    assert place.id is not None
```

### TDD 워크플로우

```bash
# 1. RED: 실패하는 테스트 작성
pytest tests/unit/test_new_feature.py  # FAIL

# 2. GREEN: 최소한의 구현으로 테스트 통과
# (코드 작성)
pytest tests/unit/test_new_feature.py  # PASS

# 3. REFACTOR: 코드 개선
# (리팩토링)
pytest tests/unit/test_new_feature.py  # PASS

# 4. 커버리지 확인
pytest --cov=app --cov-report=html
# 브라우저에서 htmlcov/index.html 확인
```

### 코드 품질 체크

```bash
# 자동 포맷팅
black app tests
isort app tests

# 린트 검사
flake8 app tests
mypy app

# 보안 스캔
bandit -r app/
safety check

# 전체 테스트 실행
./scripts/run-tests.sh --all
```

---

## 참고 자료

### 프로젝트 문서
- [PRD (Product Requirements)](prd/main.md)
- [TRD (Technical Requirements)](trd/main.md)
- [Task Breakdown](task/main.md)
- [Development Rules](rules.md)
- [CLAUDE.md (AI Assistant Guide)](CLAUDE.md)

### 외부 문서
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [PostgreSQL PostGIS](https://postgis.net/)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Firebase Admin SDK](https://firebase.google.com/docs/admin/setup)
- [Google Gemini API](https://ai.google.dev/)

---

**문서 버전**: 1.0
**최종 수정**: 2025-09-30
**작성자**: Claude (AI Assistant)
**검토자**: Hotly Team
