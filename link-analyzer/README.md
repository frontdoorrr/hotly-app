# Link Analyzer Service

링크 분석 마이크로서비스 - URL에서 정보를 추출하고 분석하는 FastAPI 애플리케이션

## 개요

Link Analyzer는 다양한 소셜 미디어 및 웹 플랫폼의 URL을 분석하여 메타데이터를 추출하는 독립적인 마이크로서비스입니다.

### 지원 플랫폼

- Instagram
- Naver Blog
- Tistory
- YouTube
- Kakao Map

## 프로젝트 구조

```
link-analyzer/
├── app/
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           └── analyze.py  # 링크 분석 엔드포인트
│   ├── core/
│   │   └── config.py        # 애플리케이션 설정
│   ├── services/
│   │   └── link_analyzer.py # 링크 분석 비즈니스 로직
│   └── schemas/
│       └── link.py          # Pydantic 스키마
├── Dockerfile
├── requirements.txt
└── README.md
```

## 설치 및 실행

### Docker Compose로 실행 (권장)

프로젝트 루트에서:

```bash
# 모든 서비스 실행
docker-compose up

# link-analyzer만 실행
docker-compose up link-analyzer redis
```

서비스는 `http://localhost:8001`에서 실행됩니다.

### 로컬 개발 환경

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정

# 개발 서버 실행
uvicorn app.main:app --reload --port 8001
```

## API 사용법

### Health Check

```bash
curl http://localhost:8001/health
```

### 링크 분석

```bash
curl -X POST http://localhost:8001/api/v1/analyze/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/p/example/"}'
```

응답 예시:

```json
{
  "url": "https://www.instagram.com/p/example/",
  "title": "Example Post",
  "description": "This is an example post description",
  "platform": "instagram",
  "content_type": "restaurant",
  "metadata": {
    "final_url": "https://www.instagram.com/p/example/",
    "status_code": 200
  }
}
```

## API 문서

FastAPI의 자동 생성 문서는 다음 주소에서 확인할 수 있습니다:

- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## 환경 변수

주요 환경 변수 (.env 파일):

```bash
# Redis 설정
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=1

# AI 서비스
GEMINI_API_KEY=your_api_key_here

# 개발 설정
DEBUG=true
LOG_LEVEL=INFO
```

## 아키텍처

### 서비스 레이어

- **LinkAnalyzerService**: URL 분석 및 메타데이터 추출
  - 플랫폼 감지
  - HTML 파싱 및 메타데이터 추출
  - 향후 AI 기반 컨텐츠 분석 확장 예정

### 캐싱 전략

- Redis를 사용한 분석 결과 캐싱
- DB 1을 사용하여 메인 백엔드와 분리

## 개발 가이드

### 새로운 플랫폼 추가

1. `LinkAnalyzerService.PLATFORM_PATTERNS`에 정규식 패턴 추가
2. 플랫폼별 파싱 로직 구현
3. 테스트 케이스 작성

### 코드 스타일

- Black을 사용한 코드 포맷팅
- Type hints 필수
- Docstring 작성 권장

## 향후 계획

- [ ] AI 기반 컨텐츠 분석 (Google Gemini 통합)
- [ ] 더 많은 플랫폼 지원
- [ ] 이미지 다운로드 및 분석
- [ ] 배치 URL 분석 지원
- [ ] 분석 결과 캐싱 최적화
- [ ] 테스트 코드 작성

## 트러블슈팅

### 포트 충돌

8001 포트가 이미 사용 중인 경우, docker-compose.yml에서 포트 매핑을 변경하세요:

```yaml
ports:
  - "8002:8001"  # 호스트:컨테이너
```

### Redis 연결 오류

Redis 서비스가 실행 중인지 확인:

```bash
docker-compose ps redis
```

## 라이선스

이 프로젝트는 hotly-app의 일부입니다.
