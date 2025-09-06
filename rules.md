- 문서 작성 rule
1. 목적/원칙
1-1. 사용자가 무엇을, 왜, 어떻게 하려는지 명확히 드러나야 함(사용자 가치 우선).
1-2. 기능은 버튼/상호작용 단위로 정의하고, 결과적으로 사용자가 얻게 되는 이점을 서술.
1-3. 모호한 표현(빠름/좋음 등) 대신 관찰 가능 기준(시간, 단계 수, 성공 조건)으로 기술.

2. 문서 구조(prd/)
2-1. 페르소나(Persona)
    - 인구통계/맥락/목표/동기/제약/성공 정의(Definition of Success)를 포함.
    - 핵심 Pain point를 3개 이내로 우선순위화.
2-2. 유저 스토리(User Stories)
    - 형식: “나는 [역할]으로서 [목표]를 위해 [행위]하고 싶다. 그래서 [가치]를 얻는다.”
    - 각 스토리는 수용 기준(아래 2-4)과 연결.
2-3. 유저 플로우(User Flow)
    - 화면/상태/행동 단위 다이어그램 또는 단계 서술(버튼 → 페이지 → 시스템 반응).
    - 분기/에러/빈 상태(Empty state) 플로우 포함.
2-4. 수용 기준(Acceptance Criteria)
    - 형식: Given/When/Then. 측정 가능·검증 가능해야 함.
    - 예: Given 캐시에 동일 URL이 있음, When 링크를 공유하면, Then 1초 이내 분석 결과가 표시된다.
2-5. 상충/의존성 점검(Conflict Matrix)
    - 버튼/제스처/네비게이션의 중복·충돌 사례를 표로 정리.
    - 타 기능과의 정책 충돌(권한, 속도 우선순위 등) 명세 및 해결안.
2-6. 정보 구조(IA)·용어 사전(Glossary)
    - 사용자 용어로 정의하고 시스템 용어와 매핑(예: "위시리스트"=즐겨찾기 후보).

3. 파일명/버전 규칙
3-1. 파일명: `NN-topic-kebab-case.md` (예: `01-authentication-system.md`).
3-2. prd/와 trd/는 번호·이름 1:1 매칭 유지.
3-3. 변경 이력: 문서 하단에 Changelog(날짜/변경 요약/작성자) 추가.

4. task/ 연동
4-1. prd 변경 → trd 반영 → task 생성/수정 순서 준수.
4-2. task는 구분 가능한 최소 단위로 세분화하고, 각 task는 수용 기준과 연결.
4-3. task에는 완료 정의(DoD) 포함: 테스트/문서/릴리즈 체크.

5. 검토 체크리스트(작성/리뷰 시 공통)
5-1. 사용자 가치가 문서 상단(개요/목표)에 명확히 서술되었는가?
5-2. 주요 페르소나의 Pain point가 기능과 직접 연결되는가?
5-3. 유저 플로우에 빈 상태/에러/로딩/권한 흐름이 포함되는가?
5-4. 수용 기준이 Given/When/Then 형식으로 테스트 가능하게 작성되었는가?
5-5. 버튼/네비/정책 충돌이 Conflict Matrix로 식별·해결되었는가?
5-6. 용어/메트릭/지표 정의가 일관되는가?(예: 응답시간, 캐시 히트율)
5-7. **backend_reference 활용 여부**: 기존 구조와 패턴을 참고하여 일관성을 유지하는가?

6. 지표/KPI(가설-지표-검증)
6-1. 각 기능은 최소 한 개의 가설과 측정 지표(KPI)를 가져야 함.
6-2. 예: 링크 분석 기능 → 가설: 캐시 도입 시 응답시간 p50 1s 이하, 히트율 40%.

7. 접근성/국제화 고려
7-1. 텍스트 대비, 터치 타깃, 스크린리더 레이블 등 핵심 항목 포함.
7-2. 다국어/시간대/날짜·주소 포맷 차이를 유저 플로우에 반영.


- 코드 작성 rule
2. 모든 코드는 재사용이 가능하도록 설계되어야 함.
2-1. 객체지향적이고 모듈화가 잘 이루어져야함.
2-2. 모든 코드 작성 시, 예시 아키텍쳐를 잘 따라야 하고 예외 사항이 많지 않아야 함.
2-3. 모든 코드는 테스트 코드 먼저 작성하며, TDD 기반으로 설계되어야 함.
    - Red-Green-Refactor 사이클 준수: 실패하는 테스트 → 최소 구현 → 리팩토링
    - 단위 테스트부터 시작하여 점진적으로 통합/E2E 테스트 추가
    - 테스트 케이스는 요구사항을 코드로 명세하는 역할 (Living Documentation)
    - 테스트 우선 설계로 결합도 낮추고 테스트 가능한 구조 강제
2-4. "Python 코드 스타일은 PEP8을 준수하세요. 코드를 리뷰할 때 PEP8 위반 사항(들여쓰기, 라인 길이 등)을 지적하세요."
    "모든 함수와 클래스에는 docstring을 포함하고, 함수 정의에는 가능한 한 타입 힌트를 사용하세요."
    "예외 처리를 누락하지 않도록 하고, try/except 사용 시 발생 가능한 모든 예외를 적절히 처리하세요."
2-5. 예외 처리
    - `except Exception`과 같은 포괄 예외는 금지(최소 범위의 구체 예외 사용).
    - 재시도 가능한 오류는 재시도/백오프 정책으로 처리, 비재시도 오류는 즉시 실패.
    - 사용자 입력/외부 API/DB/네트워크 별로 예외 타입을 구분해 핸들링.
    - 도메인 전용 예외 클래스를 정의하고 API 계층에서 HTTP 오류로 일관 매핑.
2-6. 로깅
    - 구조화 로그(JSON) 사용: timestamp, level, message, trace_id, user_id(가능 시).
    - 민감정보(토큰/PII/프롬프트)는 마스킹. 요청/응답 바디는 샘플링/크기 제한.
    - 레벨 가이드: DEBUG(개발 상세), INFO(정상 흐름), WARN(회복 가능 이상), ERROR(기능 실패), FATAL(서비스 중단).
2-7. 설정/비밀 관리
    - 12-Factor 원칙: 환경변수 기반. 스키마 검증(필수/기본값)과 타입 캐스팅 필수.
    - 비밀은 시크릿 매니저/CI 변수 사용. 코드/리포지토리에 하드코딩 금지.
    - 구성 값 변경은 재배포 없이 반영 가능한 구조 선호.
2-8. API 설계
    - 요청/응답 스키마는 명시적(Pydantic)으로 정의하고 자동 문서화(OpenAPI) 유지.
    - 페이지네이션/정렬/필터는 표준 파라미터로 통일. 에러 포맷 일관 유지.
    - 타임아웃/레이트리밋/아이도empotency-Key(필요 시) 지원.
2-9. 비동기/성능
    - 외부 호출은 타임아웃 기본값 설정(네트워크/AI/DB). 재시도는 지수 백오프.
    - 큐 작업은 아이템 idempotent 설계, 데드레터 큐 분리, 관측 메트릭 기록.
    - 캐시 정책(키 네임스페이스/TTL/무효화 전략) 문서화 및 일관 적용.
2-10. 데이터 품질
    - 스키마 버저닝과 마이그레이션 기록. 인덱스/고유 제약/TTL 명시.
    - 중복 방지 규칙과 퍼지 매칭 임계값을 상수/설정으로 고정.
    - 일관성 수준을 기능별 정의(강한/최종 일관성)하고 문서화.
2-11. 테스트 전략 (TDD 중심)
    - 테스트 피라미드: 단위(최다) → 통합 → E2E(스모크). 실패를 재현 가능하게.
    - TDD 사이클 적용: 요구사항 → 테스트 작성 → 최소 구현 → 리팩토링 → 반복
    - 경계값/에러 경로/예외/시간대/로케일 테스트 포함. 외부 의존성은 모킹.
    - 테스트 네이밍: `methodName_condition_expectedResult`.
    - 테스트 코드도 프로덕션 코드와 동일한 품질 기준 적용 (DRY, 가독성, 유지보수성)
    - Given-When-Then 패턴으로 테스트 시나리오 구조화
2-12. 코드 리뷰 체크리스트 (TDD 강화)
    - 단일 책임, 모듈/함수 크기 적절성, 네이밍 명확성.
    - 테스트 우선 개발 여부: 프로덕션 코드보다 테스트가 먼저 작성되었는가?
    - 테스트 커버리지: 모든 공개 메서드와 주요 분기에 테스트 존재하는가?
    - 예외/로깅/설정/보안(PII/토큰)/입력 검증 존재 여부.
    - API 스키마/문서 동기화, 성능(쿼리/캐시), 테스트 의미성.
    - 컨벤션/린트/타입체크/포맷 CI 통과 여부.
    - 테스트 품질: 테스트가 구현이 아닌 행동/요구사항을 검증하는가?
2-13. 문서화
    - 공개 API는 Docstring과 OpenAPI에 반영. 변경 시 changelog와 ADR 남김.


 - 코드 컨벤션 rule (기술 스택 기반)
 3. 공통 컨벤션
 3-1. 네이밍
     - 디렉터리/파일: `snake_case`
     - API JSON 필드: `camelCase`(모바일 친화), 백엔드 내부(Python): `snake_case`
     - 상수: 언어 관례 따름(Flutter: lowerCamel `const`, Python: UPPER_SNAKE)
 3-2. 구성/환경
     - 환경변수는 `.env`(로컬), Secret은 별도 비공개 스토리지. 코드 내 하드코딩 금지.
     - 공통 로깅 포맷: ISO8601 시간, level, trace_id, user_id(가능 시) 포함.
 3-3. API 규약(REST)
     - 버저닝: `/api/v1` 프리픽스. 리소스는 복수형(`/places`).
     - 에러 포맷: `{ "error": { "code": string, "message": string, "details"?: any } }`
     - 페이지네이션: `?page=1&page_size=20` 혹은 `?limit=&cursor=` 중 하나로 통일.
     - 멱등성: 생성 외 POST는 멱등성 키 헤더(`Idempotency-Key`) 지원 고려.
 3-4. 보안/개인정보
     - PII/토큰/프롬프트는 로그에 마스킹. 외부 전송 전 최소화/암호화.
     - 레이트리밋/입력 검증 필수(URL, 좌표, 텍스트 길이 등).
 3-5. 커밋/브랜치 규칙
 3-5-1. Conventional Commits 의무 준수
     - 형식: `<type>(<scope>): <description>`
     - 타입: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`
     - 예시: `feat(places): add place duplicate detection algorithm`
     - Breaking Change: `feat!:` 또는 `BREAKING CHANGE:` 푸터 추가
 3-5-2. 브랜치 네이밍
     - 기능: `feat/<scope>-<description>` (예: `feat/places-duplicate-detection`)
     - 버그픽스: `fix/<scope>-<description>` (예: `fix/auth-token-validation`)
     - 핫픽스: `hotfix/<description>` (예: `hotfix/critical-security-patch`)
     - 릴리즈: `release/v<version>` (예: `release/v1.2.0`)
 3-5-3. 커밋 메시지 상세 규칙
     - 제목: 50자 이내, 명령형 현재 시제 (한국어), 끝에 마침표 없음
     - 본문: 72자로 줄바꿈, 변경 사유 설명 (What & Why, not How)
     - 푸터: 이슈 참조 `Closes #123`, `Refs #456`
     - 템플릿:
       ```
       feat(scope): add feature description

       Explain the reason for this change and what problem it solves.
       Include any breaking changes or migration notes.

       Closes #123
       ```
 3-5-4. 커밋 품질 기준
     - 원자적 커밋: 하나의 논리적 변경사항만 포함
     - 테스트 포함: 기능 커밋 시 관련 테스트 코드 함께 커밋
     - 빌드 가능: 각 커밋에서 빌드/테스트 성공 보장
     - 의미 있는 커밋: WIP, temp 등 임시 커밋 지양
 3-5-5. PR/MR 규칙
     - 제목: 커밋 메시지와 동일한 컨벤션
     - 설명: 변경사항 요약, 테스트 방법, 스크린샷(UI 변경 시)
     - 리뷰어: 최소 1명 승인 필요
     - 체크리스트: CI 통과, 테스트 커버리지 80% 이상, 문서 업데이트
 3-5-6. 머지 전략
     - Squash and Merge: 기능 브랜치 → 메인 브랜치
     - 커밋 히스토리 정리: 의미 있는 커밋만 유지
     - 브랜치 삭제: 머지 후 자동 삭제

 4. 모바일(Flutter / Dart)
 4-1. 스타일/린트
     - `flutter_lints`/`effective_dart` 준수. `dart format`, `flutter analyze` 무오류.
     - 네이밍: 클래스/Enum `PascalCase`, 메서드/변수 `lowerCamelCase`, 파일/폴더 `snake_case`.
 4-2. 위젯/상태
     - `const` 생성자 적극 사용, 불변 데이터 우선.
     - 위젯 분리: 200줄 내외 유지, 빌드 메서드 단순화.
 4-3. 의존성/구조
     - 폴더 구조는 feature-first(`features/<feature>/widgets|views|models|services`).
     - 플랫폼 키/토큰은 런타임 주입(환경/원격 구성). 코드 하드코딩 금지.
 4-4. 테스트 (TDD 적용)
     - `flutter_test`로 단위/위젯 테스트. 핵심 위젯 상호작용 테스트 필수.
     - TDD 사이클: 위젯 요구사항 → 테스트 작성 → 위젯 구현 → 리팩토링
     - 골든 테스트는 디자인 고정 영역에 한정.
     - 비즈니스 로직은 위젯에서 분리하여 단위 테스트 용이하게 설계
     - Mock/Fake 객체로 외부 의존성(API, DB) 격리

 5. 백엔드(FastAPI / Python)
 5-1. 스타일/정적분석
     - `black`, `isort`, `flake8`, `mypy` 통과. PEP8/타입힌트/Docstring(google-style) 필수.
 5-2. 프로젝트 구조(예)
     - `app/main.py`, `app/api/routers`, `app/schemas`(Pydantic), `app/models`, `app/services`, `app/repositories`, `app/core`(config/logging), `tests/`
 5-3. API 설계
     - `APIRouter`로 도메인 분리, `prefix`, `tags` 지정. `response_model` 명시.
     - 예외는 `HTTPException`으로 매핑. 유효성검사는 `Pydantic` 스키마로 일원화.
 5-4. 데이터/직렬화
     - 내부 필드 `snake_case`, 외부 응답은 `camelCase` 변환 레이어 사용.
     - UUID는 문자열로 노출(`id`), 인덱스/제약조건은 마이그레이션에 명시.
     - SQLAlchemy ORM 모델과 Pydantic 스키마 분리로 계층별 검증.

 6. 데이터(PostgreSQL)
 6-1. 네이밍/스키마
     - 테이블명 복수형(`places`, `courses`). 컬럼 `snake_case`(내부).
     - 인덱스/제약조건/파티셔닝은 Alembic 마이그레이션에 선언적으로 기술.
     - JSON/JSONB 컬럼 활용으로 반구조화 데이터 (태그, 메타데이터) 효율 저장.
 6-2. 중복/정규화
     - 장소 중복 키: 이름+주소 정규화+지리 해시. PostgreSQL trigram 유사도 활용.
     - 지리 데이터는 PostGIS 확장으로 공간 인덱스 및 거리 계산 최적화.
 6-3. 트랜잭션/일관성
     - ACID 트랜잭션 활용. 복합 작업은 @transaction 데코레이터로 일관성 보장.
     - 읽기 전용 쿼리는 read replica 활용으로 부하 분산.

 7. 캐시/큐(Redis / RabbitMQ)
 7-1. 키 네임스페이스
     - `hotly:{domain}:{key}` 형식. TTL은 기능별 표준값 문서화.
 7-2. 비동기 작업
     - 큐명/라우팅키 케밥케이스, 재시도 백오프(지수), 데드레터 큐 분리.
     - 작업 페이로드 스키마 버저닝(`schema_version`).

 8. AI 연동(Google Gemini)
 8-1. 안정성
     - 타임아웃, 재시도(지수 백오프), 레이트리밋 대응(429) 공통 미들웨어.
 8-2. 프롬프트/출력
     - 프롬프트 템플릿/모델 버전 버저닝. 출력 스키마를 JSONSchema로 검증.
 8-3. 개인 정보
     - 입력 데이터 최소화, 민감정보 마스킹/비저장 원칙.

 9. 지도/외부 SDK(Kakao Map)
 9-1. 키 관리/보안
     - 키는 환경변수/원격 구성으로 주입. 도메인/패키지 제한 활성화.
 9-2. 성능
     - 마커 클러스터링/뷰포트 단위 로딩. 네트워크/이미지 캐시 사용.

 10. 인증/알림(Firebase Auth + FCM)
 10-1. 인증
     - 백엔드에서 토큰 검증(서명/만료). 사용자 매핑은 내부 `user_id` 표준화.
 10-2. 알림
     - 주제/토픽 네이밍은 `hotly-<scope>`. 야간 조용시간 설정 옵션 제공.

 11. 테스트/품질
 11-1. 범위
     - 단위(로직), 통합(라우터/DB), E2E(핵심 플로우 스모크) 포함.
 11-2. 커버리지
     - 라인 커버리지 80% 이상. 임계 미달 시 머지 불가(예외는 사유 기록).
 11-3. CI (TDD 지원 강화)
     - 모바일: `flutter test`/`flutter analyze`. 백엔드: `pytest -q`, `mypy`, `flake8`, `black --check`, `isort --check`.
     - 테스트 실행 우선순위: 단위 → 통합 → E2E (빠른 피드백)
     - 테스트 실패 시 빌드 중단, 커버리지 임계값 미달 시 경고
     - TDD 준수 검증: 테스트 파일과 소스 파일의 커밋 순서 체크 (가능한 경우)

 12. 문서화/자동화
     - OpenAPI 스펙을 소스 오브 트루스로 관리(FastAPI 자동 문서 노출).
     - Pre-commit 훅으로 포맷/린트/타입체크 자동화. 변경 시 `task/` 우선 갱신.
     - **backend_reference 참고 의무**: 모든 백엔드 개발 시 `backend_reference/app/` 구조/패턴을 기본으로 참고하여 일관성 유지.
