# ArchyAI
AI 기반 SNS 콘텐츠 아카이빙 앱 (place / event / tips / review)

## 프로젝트 구조

```
hotly-app/
├── backend/           # FastAPI 백엔드 애플리케이션
│   ├── app/          # 메인 애플리케이션 코드
│   ├── tests/        # TDD 테스트 프레임워크
│   ├── alembic/      # 데이터베이스 마이그레이션
│   ├── scripts/      # 유틸리티 스크립트
│   └── [config]      # 백엔드 설정 파일들
├── frontend/         # Flutter 모바일 앱 (iOS / Android)
├── prd/             # Product Requirements Documents
├── trd/             # Technical Requirements Documents
├── task/            # Implementation Tasks
└── docs/            # 추가 문서
```

## 빠른 시작

### 백엔드 실행 (Docker)
```bash
# 백엔드 + DB + Redis
docker-compose up
```

### 백엔드만 실행
```bash
cd backend
poetry install
uvicorn app.main:app --reload
```

### 프론트엔드 실행 (Flutter)
```bash
cd frontend

# 의존성 설치
flutter pub get

# 코드 생성 (Freezed, Riverpod 등)
flutter pub run build_runner build --delete-conflicting-outputs

# 연결된 기기 확인
flutter devices

# 개발 모드 실행
flutter run --dart-define=ENV=dev

# 특정 기기 지정 실행
flutter run -d <device_id> --dart-define=ENV=dev
```

### 빌드
```bash
cd frontend

# Android APK / AAB
./scripts/build-android.sh

# iOS IPA
./scripts/build-ios.sh
```

## 개발 가이드

자세한 개발 가이드는 [CLAUDE.md](./CLAUDE.md)를 참조하세요.

- 아키텍처 설명
- 개발 명령어
- 테스트 실행 방법
- 코드 품질 도구
- CI/CD 파이프라인
