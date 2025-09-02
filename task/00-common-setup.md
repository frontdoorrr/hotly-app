# Task 0: 공통 기본 세팅 (Common Setup)

## 0-1. 개발환경 및 프로젝트 구조 설정

### 목표
일관된 개발 환경과 코드 품질 보장을 위한 기본 인프라 구축

### 사용자 가치
- **개발자 경험**: 5분 내 개발 환경 구축으로 온보딩 시간 단축
- **코드 품질**: 자동화된 품질 검사로 버그 사전 방지
- **팀 협업**: 일관된 환경으로 "내 컴퓨터에서는 잘 됐는데" 문제 해결

### 가설 및 KPI
- **가설**: 표준화된 개발 환경으로 개발 생산성 30% 향상
- **측정 지표**: 환경 구축 시간 5분 이내, pre-commit 통과율 95% 이상

### 완료 정의 (DoD)
- [x] Backend FastAPI 프로젝트 구조 완성 (Poetry + 가상환경)
- [x] 코드 품질 도구 설정 (black, isort, flake8, mypy)
- [ ] Pre-commit hooks 및 GitHub Actions CI/CD 파이프라인 구축
- [ ] 테스트 커버리지 80% 이상 유지 설정 (pytest-cov)
- [ ] Docker 개발 환경 및 docker-compose.yml 구성
- [ ] 보안 스캔 도구 설정 (bandit, safety)
- [ ] API 문서 자동화 (OpenAPI/Swagger)
- [ ] 환경변수 스키마 검증 (Pydantic BaseSettings)

### 수용 기준
- Given 새로운 개발자가 프로젝트를 클론함, When `make setup` 실행함, Then 5분 내에 개발 환경이 구축됨
- Given 코드를 커밋함, When pre-commit hook이 실행됨, Then 모든 린트/포맷 검사를 통과함
- Given `docker-compose up`을 실행함, When 서비스가 시작됨, Then 헬스체크 엔드포인트가 200 응답함

### 세부 작업

#### 0-1-1. FastAPI 프로젝트 구조 생성 및 Poetry 설정
**상세**: `app/main.py`, `app/api/`, `app/core/`, `app/models/`, `app/schemas/`, `app/services/`, `app/db/`, `tests/` 디렉터리 구조

**TDD 구현 순서**:
1. **RED**: 프로젝트 구조 검증 테스트 작성
2. **GREEN**: 최소 프로젝트 구조 생성
3. **REFACTOR**: 구조 최적화 및 표준화

**구현 체크리스트**:
- [ ] 프로젝트 구조 테스트 작성 (`tests/test_project_structure.py`)
- [ ] Poetry 초기화 및 pyproject.toml 설정
- [ ] feature-first 디렉터리 구조 생성 (`app/features/`)
- [ ] 기본 FastAPI 앱 설정 (CORS, 미들웨어)
- [ ] 개발 의존성 패키지 설치 (pytest, black, mypy 등)
- [ ] 환경변수 스키마 검증 (.env 템플릿 + Pydantic)
- [ ] 도메인별 예외 클래스 정의 (`app/exceptions/`)
- [ ] 로깅 설정 (구조화 JSON 로그)

**결과물**: 
- `pyproject.toml` - Poetry 설정 (의존성 버전 고정)
- `app/` - feature-first 애플리케이션 구조
- `tests/` - TDD 기반 테스트 코드
- `.env.example` - 스키마 검증된 환경변수 템플릿
- `app/exceptions/` - 도메인별 예외 클래스
- `app/core/logging.py` - 구조화 로깅 설정

**보안 요구사항**:
- 환경변수로 모든 시크릿 관리 (하드코딩 금지)
- PII 데이터 로그 마스킹 설정
- API 키/토큰 별도 시크릿 매니저 연동

**성능 기준**:
- 프로젝트 초기화: 5분 이내
- 의존성 설치: 2분 이내
- 테스트 실행: 30초 이내

**테스트**: 
- 프로젝트 구조 검증 테스트
- Poetry 가상환경 격리 테스트
- 환경변수 스키마 검증 테스트

#### 0-1-2. 코드 품질 도구 설정 (black, isort, flake8, mypy)
**상세**: PEP8 준수, 타입 힌트, docstring 강제, 보안 스캔 포함

**TDD 구현 순서**:
1. **RED**: 코드 품질 검증 테스트 작성
2. **GREEN**: 품질 도구 설정 및 통과
3. **REFACTOR**: 설정 최적화 및 표준화

**구현 체크리스트**:
- [ ] 품질 검사 테스트 작성 (`tests/test_code_quality.py`)
- [ ] black 설정 (라인 길이 88, Google docstring 스타일)
- [ ] isort 설정 (black 호환, 모듈별 그룹화)
- [ ] flake8 설정 (E203, W503 무시, 복잡도 10 이하)
- [ ] mypy 설정 (strict 모드, 타입 힌트 강제)
- [ ] bandit 보안 스캔 설정
- [ ] safety 의존성 취약점 검사
- [ ] VS Code 설정 파일 (.vscode/settings.json)

**보안 검사 추가**:
- bandit: 보안 취약점 정적 분석
- safety: 의존성 보안 취약점 검사
- PII 데이터 하드코딩 검출

**결과물**: 
- `pyproject.toml` - 통합 도구 설정 (black, isort, mypy)
- `.flake8` - Flake8 설정
- `bandit.yaml` - 보안 스캔 설정
- `.vscode/settings.json` - VS Code 설정
- `scripts/quality_check.sh` - 품질 검사 스크립트

**성능 기준**:
- 린트 검사: 10초 이내 (전체 코드베이스)
- 타입 체크: 15초 이내
- 보안 스캔: 30초 이내

**테스트**: 
- 의도적 품질 오류 코드로 각 도구 차단 확인
- CI에서 품질 게이트 통과 여부 검증
- 보안 취약점 검출 테스트

#### 0-1-3. Pre-commit hooks 설정
**상세**: `.pre-commit-config.yaml` 작성, black/isort/flake8/mypy 훅 설정

**구현 체크리스트**:
- [ ] pre-commit 설치 및 설정
- [ ] 코드 포맷팅 훅 (black, isort)
- [ ] 린팅 훅 (flake8, mypy)
- [ ] 커밋 메시지 검증 훅

**결과물**: 
- `.pre-commit-config.yaml` - Pre-commit 설정
- 커밋 시 자동 코드 품질 검사 실행

**테스트**: 의도적 오류 코드 커밋하여 훅 차단 확인

#### 0-1-4. GitHub Actions CI/CD 파이프라인 구성
**상세**: `.github/workflows/ci.yml`, 테스트/린트/빌드/배포 단계

**구현 체크리스트**:
- [ ] CI 워크플로우 설정
- [ ] 테스트 자동화
- [ ] 코드 품질 검사
- [ ] 배포 자동화 (스테이징/프로덕션)

**결과물**: 
- `.github/workflows/ci.yml` - CI 워크플로우
- `.github/workflows/deploy.yml` - 배포 워크플로우

**테스트**: 의도적 테스트 실패로 CI 차단 확인

#### 0-1-5. 테스트 프레임워크 및 커버리지 설정
**상세**: pytest, pytest-cov, pytest-asyncio 설정

**구현 체크리스트**:
- [ ] pytest 설정 및 conftest.py
- [ ] 커버리지 설정 (80% 최소)
- [ ] 비동기 테스트 설정
- [ ] 테스트 데이터베이스 설정

**결과물**: 
- `pytest.ini` - Pytest 설정
- `tests/conftest.py` - 테스트 설정
- 커버리지 리포트 HTML 생성

**테스트**: 샘플 테스트 실행하여 80% 커버리지 달성 확인

#### 0-1-6. Docker 개발 환경 설정
**상세**: `Dockerfile`, `docker-compose.yml` (FastAPI + PostgreSQL + Redis)

**구현 체크리스트**:
- [ ] FastAPI Dockerfile 작성
- [ ] docker-compose.yml 설정
- [ ] PostgreSQL 컨테이너 설정
- [ ] Redis 컨테이너 설정
- [ ] 개발용 볼륨 마운트

**결과물**: 
- `Dockerfile` - FastAPI 컨테이너
- `docker-compose.yml` - 전체 스택
- `docker-compose.dev.yml` - 개발 환경

**테스트**: `docker-compose up`으로 전체 스택 실행 확인

---

## 0-2. 공통 데이터베이스 및 캐시 설정

### 목표
PostgreSQL과 Redis를 이용한 확장 가능한 데이터베이스 환경 구축

### 완료 정의 (DoD)
- [ ] PostgreSQL 연결 설정 및 기본 테이블 스키마 정의
- [ ] Redis 연결 설정 및 키 네임스페이스 정의
- [ ] Alembic migrations 시스템 구축
- [ ] 연결 상태 헬스체크 엔드포인트 구현
- [ ] 데이터베이스 인덱스 최적화 및 성능 튜닝

### 수용 기준
- Given 애플리케이션이 시작됨, When 데이터베이스 연결을 확인함, Then 2초 내에 연결 상태 응답
- Given 스키마 변경이 필요함, When 마이그레이션을 실행함, Then 데이터 무결성을 유지하며 스키마 업데이트
- Given 1000개 장소 데이터가 있음, When 검색 쿼리를 실행함, Then 100ms 내에 결과 반환

### 세부 작업

#### 0-2-1. PostgreSQL 연결 설정 및 모델 정의
**상세**: asyncpg 비동기 드라이버, SQLAlchemy ORM 설정, 연결 풀 최적화

**구현 체크리스트**:
- [ ] asyncpg 드라이버 설정
- [ ] SQLAlchemy 비동기 엔진 설정
- [ ] 연결 풀 최적화 (최소 5, 최대 20)
- [ ] 기본 모델 클래스 정의
- [ ] 타임스탬프 mixin 클래스

**결과물**: 
- `app/db/postgresql.py` - PostgreSQL 연결
- `app/models/` - SQLAlchemy 모델들
- `app/db/base.py` - 기본 모델 클래스

**API**: `GET /health/db` - PostgreSQL 연결 상태 확인

**테스트**: 연결 실패 시나리오, 트랜잭션 롤백, 타임아웃 처리

#### 0-2-2. Redis 연결 설정 및 키 네임스페이스 정의
**상세**: aioredis 설정, 클러스터 지원, 키 네이밍 컨벤션 `hotly:{service}:{key}`

**구현 체크리스트**:
- [ ] aioredis 연결 설정
- [ ] 키 네임스페이스 정의
- [ ] 캐시 매니저 클래스
- [ ] TTL 관리 유틸리티

**결과물**: 
- `app/db/redis.py` - Redis 연결
- `app/services/cache_manager.py` - 캐시 매니저

**API**: `GET /health/cache` - Redis 연결 상태 확인

**테스트**: Redis 장애 시 graceful degradation 확인

#### 0-2-3. Alembic 마이그레이션 시스템 구축
**상세**: Alembic 기반 스키마 버전 관리, 자동 마이그레이션 생성

**구현 체크리스트**:
- [ ] Alembic 초기화
- [ ] 마이그레이션 스크립트 템플릿
- [ ] 자동 마이그레이션 생성 설정
- [ ] 백업 및 복구 스크립트

**결과물**: 
- `alembic/` - 마이그레이션 디렉터리
- `alembic.ini` - Alembic 설정
- `scripts/migrate.sh` - 마이그레이션 스크립트

**API**: `POST /admin/migrate` - 마이그레이션 실행 (관리자 전용)

**테스트**: 마이그레이션 up/down, 스키마 변경, 데이터 보존

#### 0-2-4. 헬스체크 엔드포인트 구현
**상세**: 데이터베이스, 캐시, 외부 서비스 상태 종합 확인

**구현 체크리스트**:
- [ ] 기본 헬스체크 엔드포인트
- [ ] 상세 헬스체크 (서비스별)
- [ ] Kubernetes 레디니스/라이브니스 프로브
- [ ] 메트릭 수집

**결과물**: 
- `app/api/health.py` - 헬스체크 API

**API**: 
- `GET /health` - 기본 헬스체크
- `GET /health/detailed` - 상세 상태

**테스트**: 각 서비스별 장애 시나리오 시뮬레이션

#### 0-2-5. PostgreSQL 인덱스 및 확장 설정
**상세**: B-tree/GIN/GiST 인덱스, PostGIS 확장, pg_trgm 유사도 검색

**구현 체크리스트**:
- [ ] PostGIS 확장 설치
- [ ] 전문검색 확장 (pg_trgm)
- [ ] UUID 확장
- [ ] 인덱스 생성 마이그레이션
- [ ] 성능 모니터링 쿼리

**결과물**: 
- 확장 설치 마이그레이션
- 인덱스 생성 마이그레이션
- 성능 모니터링 스크립트

**API**: `GET /admin/indexes` - 인덱스 상태 확인

**테스트**: 공간 쿼리, 전문 검색, 인덱스 성능, EXPLAIN ANALYZE

#### 0-2-6. 데이터베이스 설정 테스트 코드 작성
**상세**: 연결 테스트, 기본 CRUD 테스트, 트랜잭션 테스트

**구현 체크리스트**:
- [ ] 연결 테스트
- [ ] 기본 CRUD 테스트
- [ ] 트랜잭션 테스트
- [ ] 성능 테스트
- [ ] 장애 복구 테스트

**결과물**: 
- `tests/test_database.py` - 데이터베이스 테스트
- `tests/test_redis.py` - Redis 테스트

**테스트**: DB 장애 복구, 연결 풀 exhaustion 처리

---

## 0-3. 공통 인증 및 보안 설정

### 목표
JWT 인증, 환경변수 관리, API 보안 기본 설정

### 완료 정의 (DoD)
- [ ] JWT 토큰 생성/검증 시스템 구축
- [ ] 환경변수 기반 설정 관리 시스템
- [ ] API 레이트 리미팅 및 입력 검증 미들웨어
- [ ] 보안 헤더 및 CORS 설정

### 수용 기준
- Given 유효한 JWT 토큰으로 요청함, When API를 호출함, Then 인증된 사용자로 처리됨
- Given 초당 100개 요청을 보냄, When 레이트 리미트에 도달함, Then 429 상태코드 반환

### 세부 작업

#### 0-3-1. JWT 인증 시스템 구현
**구현 체크리스트**:
- [ ] JWT 토큰 생성 로직
- [ ] 토큰 검증 미들웨어
- [ ] 토큰 갱신 메커니즘
- [ ] 권한 기반 접근 제어

#### 0-3-2. 환경변수 기반 설정 관리 (Pydantic Settings)
**구현 체크리스트**:
- [ ] Pydantic BaseSettings 클래스
- [ ] 환경별 설정 분리
- [ ] 민감 정보 암호화
- [ ] 설정 검증

#### 0-3-3. API 레이트 리미팅 미들웨어
**구현 체크리스트**:
- [ ] slowapi 레이트 리미터 설정
- [ ] Redis 기반 분산 카운터
- [ ] IP/사용자별 제한
- [ ] 제한 초과 시 응답

#### 0-3-4. 입력 검증 및 보안 헤더 설정
**구현 체크리스트**:
- [ ] Pydantic 모델 검증
- [ ] SQL 인젝션 방지
- [ ] XSS 방지 헤더
- [ ] CORS 정책 설정

#### 0-3-5. 인증/보안 테스트 코드 작성
**구현 체크리스트**:
- [ ] JWT 토큰 테스트
- [ ] 인증 미들웨어 테스트
- [ ] 레이트 리미팅 테스트
- [ ] 보안 취약점 테스트

---

## Backend Reference 활용 가이드

### 기존 구조 참고사항
`backend_reference/app/`에서 다음 패턴들을 참고하여 구현:

**프로젝트 구조**: 
- `app/main.py` - FastAPI 앱 진입점 및 CORS 설정
- `app/core/config.py` - Pydantic BaseSettings 환경변수 관리 패턴
- `app/core/security.py` - JWT 토큰 생성/검증 유틸리티
- `app/api/api_v1/` - API 라우터 모듈화 패턴
- `app/crud/base.py` - Generic CRUD 베이스 클래스
- `app/db/session.py` - SQLAlchemy 세션 관리

**설정 관리 패턴**:
```python
# backend_reference/app/app/core/config.py 참고
class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    POSTGRES_SERVER: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    
    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v, values):
        # 기존 패턴 활용
```

**API 라우터 패턴**:
```python
# backend_reference/app/app/api/api_v1/api.py 참고
api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

**테스트 구조**:
- `tests/conftest.py` - 테스트 설정 및 픽처
- `tests/api/api_v1/` - API 엔드포인트 테스트
- `tests/crud/` - CRUD 로직 테스트

## 참고 문서
- `prd/main.md` - 제품 요구사항
- `trd/main.md` - 기술 요구사항
- `backend_reference/app/` - **FastAPI 구조 및 패턴 참고**
  - 설정 관리: `core/config.py`
  - API 구조: `api/api_v1/`
  - 데이터베이스: `db/session.py`, `models/`
  - 테스트: `tests/` 구조
- `database-schema.md` - 데이터베이스 스키마
- `rules.md` - 개발 규칙

---

*작성일: 2025-01-XX*  
*작성자: Claude*  
*버전: 1.0*