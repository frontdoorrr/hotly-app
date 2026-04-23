# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **ArchyAI**, an AI-based SNS content archiving app. Users save links from Instagram, YouTube, TikTok, and other platforms; the app automatically classifies and archives them into:

- **place** — 맛집, 카페, 관광지 등 장소 소개/방문 후기
- **event** — 팝업, 공연, 전시, 모임 등 기간 한정 이벤트
- **tips** — 주식/청소/운동/요리 등 실생활 꿀팁·방법 안내
- **review** — 제품, 서비스, 앱 사용 후기/평가
- **unknown** — 위 4가지 외 일반 정보, 뉴스, 에세이 등

The repository contains:

- `backend/`: FastAPI backend application with comprehensive service architecture
  - `app/`: Main application code
  - `tests/`: Comprehensive TDD-centered testing framework (unit, integration, E2E, performance)
  - Backend-specific configuration files (pyproject.toml, pytest.ini, etc.)
- `frontend/`: Next.js/React frontend application
- `prd/`, `trd/`, `task/`: Product requirements, technical requirements, and task documentation
- `rules.md`: Comprehensive development rules and coding conventions

## Development Commands

### Setup & Dependencies
```bash
# Install backend dependencies with Poetry
cd backend
poetry install

# Install development dependencies
poetry install --with dev

# Install frontend dependencies
cd ../frontend
npm install
```

### Development Server
```bash
# Full stack development (from project root)
docker-compose up

# Backend only (from backend directory)
cd backend
uvicorn app.main:app --reload

# Frontend only (from frontend directory)
cd frontend
npm run dev
```

> **link-analyzer**: 별도 프로세스로 **포트 8003**에서 독립 실행됩니다.
> `docker-compose`에 포함되지 않으며, 백엔드는 `LINK_ANALYZER_BASE_URL=http://localhost:8003` 환경변수로 연결합니다.

### Testing (TDD Framework)
```bash
# All commands run from backend directory
cd backend

# Run all tests with coverage (80% minimum)
pytest

# Run comprehensive test automation
./scripts/run-tests.sh

# Run specific test types
./scripts/run-tests.sh --unit           # Unit tests only
./scripts/run-tests.sh --integration    # Integration tests only
./scripts/run-tests.sh --e2e            # E2E tests only
./scripts/run-tests.sh --fast           # Skip slow tests
./scripts/run-tests.sh --ci             # CI optimized mode

# Run single test file
pytest tests/unit/test_content_extractor.py -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Performance and load testing
pytest tests/performance/ -v
```

### Code Quality
```bash
# All commands run from backend directory
cd backend

# Format code
black app tests
isort app tests
autoflake --remove-all-unused-imports --recursive app tests

# Lint and type checking
flake8 app tests
mypy app
bandit -r app/

# Security scanning
safety check
```

### Database
```bash
# All commands run from backend directory
cd backend

# Apply migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Database rollback
alembic downgrade -1
```

## Architecture

### Application Structure
```
backend/                      # Backend FastAPI application
├── app/
│   ├── main.py              # FastAPI app entry point with create_app factory
│   ├── core/                # Core configuration and utilities
│   ├── api/api_v1/         # API endpoints with /api/v1 prefix
│   │   └── endpoints/      # Individual endpoint modules (link_analysis, etc.)
│   ├── services/           # Business logic services
│   │   ├── content_extractor.py  # Social media content extraction
│   │   ├── place_analysis_service.py # AI-powered place analysis
│   │   └── cache_manager.py      # Multi-layer caching (L1: memory, L2: Redis)
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── crud/               # Database CRUD operations
│   ├── db/                 # Database session and initialization
│   ├── middleware/         # Custom middleware components
│   ├── analytics/          # Analytics and monitoring services
│   ├── features/           # Feature-specific modules
│   └── utils/              # Utility functions and helpers
├── tests/                  # TDD-centered testing framework
│   ├── unit/              # Unit tests with high coverage
│   ├── integration/       # Integration tests for service communication
│   ├── e2e/               # End-to-end user workflow tests
│   ├── performance/       # Load and performance testing
│   ├── tdd/               # TDD examples and templates
│   ├── framework/         # Meta-tests for testing infrastructure
│   └── utils/             # Test helpers and mock factories
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
└── [config files]         # pyproject.toml, pytest.ini, etc.

frontend/                   # Frontend Next.js application
└── [TBD]                  # To be structured
```

### Key Architectural Patterns
- **Service-Oriented Architecture**: Clear separation between content extraction, AI analysis, and caching
- **Multi-Layer Caching**: L1 (in-memory) + L2 (Redis) for optimal performance
- **AI Integration**: Google Gemini for intelligent place analysis from social media content
- **Async Processing**: Full async/await pattern with FastAPI for high concurrency
- **Error Resilience**: Comprehensive error handling with retry logic and circuit breakers

### Core Services Integration
- **Link Analysis Pipeline**: URL → Content Extraction → AI Analysis → Content Classification → Cached Results
- **Content Extraction**: Platform-specific extractors for Instagram, YouTube, TikTok, Naver Blog, etc.
- **Content Classification**: AI-powered categorization into place / event / tips / review / unknown with confidence scoring
- **Caching Strategy**: Intelligent cache invalidation with performance optimization

## TDD Testing Framework

This project implements a comprehensive Test-Driven Development approach with 80%+ coverage requirements:

### Testing Philosophy
- **Red-Green-Refactor**: Write failing tests first, implement minimum code to pass, then refactor
- **Test Pyramid**: Most unit tests, fewer integration tests, minimal E2E tests
- **Living Documentation**: Tests serve as executable specifications

### Test Organization
- `tests/unit/`: Fast, isolated tests for individual components
- `tests/integration/`: Service-to-service communication tests
- `tests/e2e/`: Complete user workflow tests
- `tests/performance/`: Load testing and performance validation
- `tests/framework/`: Meta-tests ensuring testing infrastructure reliability

### Test Utilities
- `tests/utils/test_helpers.py`: MockFactory, TestDataBuilder, ValidationHelpers
- `tests/tdd/`: TDD examples and templates for new development
- Comprehensive fixture system in `tests/conftest.py`

## Development Rules

This project follows comprehensive coding standards defined in `rules.md`:

### Core Requirements
- **TDD First**: Write tests before implementation, maintain 80%+ coverage
- **Code Quality**: Black formatting, isort imports, flake8 linting, mypy typing
- **API Design**: OpenAPI documentation, Pydantic schemas, consistent error formats
- **Error Handling**: Specific exceptions with retry logic and circuit breakers
- **Logging**: Structured JSON logs with trace_id, sanitized sensitive data
- **Security**: Environment variables for secrets, comprehensive input validation

### Naming Conventions
- Files/directories: `snake_case`
- API JSON fields: `camelCase` (external), `snake_case` (internal Python)
- Constants: `UPPER_SNAKE_CASE`
- Test methods: `methodName_condition_expectedResult`

## Documentation Structure

The project uses a three-tier documentation system:
- **PRD** (`prd/`): Product requirements with user personas, stories, acceptance criteria
- **TRD** (`trd/`): Technical requirements and architecture decisions
- **Task** (`task/`): Implementation tasks linked to requirements

Files follow `NN-topic-kebab-case.md` naming and maintain version consistency across tiers.

## CI/CD Pipeline

Automated testing pipeline via GitHub Actions (`.github/workflows/test-automation.yml`):
- **Code Quality**: Black, isort, flake8, mypy, bandit security scanning
- **Unit Tests**: Fast execution with coverage reporting
- **Integration Tests**: With PostgreSQL and Redis services
- **E2E Tests**: Complete user workflow validation
- **Performance Tests**: Load testing and performance validation
- **Coverage Reports**: Combined coverage with 80% minimum threshold
- **Security Scanning**: Bandit and Safety dependency checks

## Flutter 개발 주의사항

### l10n (다국어) 수정
`frontend/lib/l10n/` 하위의 `.dart` 파일들은 **빌드 시 자동 생성**된다. 직접 수정해도 빌드 때 덮어써진다.

**반드시 ARB 파일을 수정할 것:**
- `frontend/lib/l10n/app_ko.arb` — 한국어
- `frontend/lib/l10n/app_en.arb` — 영어

설정: `frontend/l10n.yaml` (template: `app_ko.arb`, output: `app_localizations.dart`)

## Environment Setup

Key configuration files:
- `backend/pyproject.toml`: Poetry dependencies and tool configuration
- `backend/pytest.ini`: Testing configuration with markers and coverage settings
- `backend/.coveragerc`: Coverage reporting configuration
- `backend/alembic.ini`: Database migration configuration
- `backend/.env.example`: Environment variables template
- `docker-compose.yml`: Full-stack development environment
- `backend/docker-compose.dev.yml`: Backend-only development
