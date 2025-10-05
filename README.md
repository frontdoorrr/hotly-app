# hotly-app
AI 기반 핫플레이스 / 데이트 코스 / 맛집 아카이빙 앱

## 프로젝트 구조

```
hotly-app/
├── backend/           # FastAPI 백엔드 애플리케이션
│   ├── app/          # 메인 애플리케이션 코드
│   ├── tests/        # TDD 테스트 프레임워크
│   ├── alembic/      # 데이터베이스 마이그레이션
│   ├── scripts/      # 유틸리티 스크립트
│   └── [config]      # 백엔드 설정 파일들
├── frontend/         # Next.js 프론트엔드 애플리케이션
├── prd/             # Product Requirements Documents
├── trd/             # Technical Requirements Documents
├── task/            # Implementation Tasks
└── docs/            # 추가 문서
```

## 빠른 시작

### 전체 스택 실행 (Docker)
```bash
# 전체 스택 실행 (백엔드 + 프론트엔드 + DB + Redis)
docker-compose up
```

### 백엔드만 실행
```bash
cd backend
poetry install
uvicorn app.main:app --reload
```

### 프론트엔드만 실행
```bash
cd frontend
npm install
npm run dev
```

## 개발 가이드

자세한 개발 가이드는 [CLAUDE.md](./CLAUDE.md)를 참조하세요.

- 아키텍처 설명
- 개발 명령어
- 테스트 실행 방법
- 코드 품질 도구
- CI/CD 파이프라인
