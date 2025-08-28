# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **hotly-app**, an AI-based hot place/dating course/restaurant archiving app. The repository contains:

- `backend_reference/`: FastAPI-based backend reference implementation with PostgreSQL
- `prd/`, `trd/`, `task/`: Product requirements, technical requirements, and task documentation
- `rules.md`: Comprehensive development rules and coding conventions

## Development Commands

### Backend (FastAPI with Poetry)
Located in `backend_reference/app/`:

**Setup & Dependencies:**
```bash
cd backend_reference/app
poetry install
```

**Development:**
```bash
# Run development server
uvicorn app.main:app --reload

# Run with scripts
./scripts/test.sh          # Run tests with coverage
./scripts/format.sh        # Format code (autoflake, black, isort)  
./scripts/lint.sh          # Lint code (mypy, black --check, isort --check, flake8)
./scripts/test-cov-html.sh # Generate HTML coverage report
```

**Testing:**
```bash
pytest --cov=app --cov-report=term-missing app/tests
```

**Database:**
```bash
alembic upgrade head       # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

## Architecture

### Backend Structure (FastAPI)
```
app/
├── main.py                 # FastAPI app entry point
├── core/
│   ├── config.py          # Pydantic settings with environment variables
│   ├── security.py        # JWT/password hashing utilities
│   └── celery_app.py      # Celery configuration
├── api/
│   └── api_v1/
│       ├── api.py         # API router aggregation
│       └── endpoints/     # Individual endpoint modules
├── models/                # SQLAlchemy ORM models
├── schemas/               # Pydantic request/response schemas
├── crud/                  # Database CRUD operations
├── db/                    # Database session and initialization
└── tests/                 # Test suite organized by layer
```

### Key Patterns
- **Settings Management**: Pydantic BaseSettings with environment variable validation
- **API Structure**: Modular routers with `/api/v1` prefix, organized by domain
- **Database**: SQLAlchemy ORM with Alembic migrations, PostgreSQL backend
- **Authentication**: JWT tokens with configurable expiration
- **Testing**: Pytest with coverage reporting, fixture-based test organization
- **Background Tasks**: Celery worker support with Redis/RabbitMQ

### Configuration
- Environment-driven configuration via Pydantic BaseSettings
- CORS origins configurable via `BACKEND_CORS_ORIGINS`
- Database connection auto-assembled from individual PostgreSQL components
- Email templates using Jinja2 with MJML compilation support

## Development Rules

This project follows comprehensive coding standards defined in `rules.md`:

### Key Requirements
- **TDD Approach**: Write tests first, maintain 80%+ coverage
- **Code Style**: PEP8 compliance, use black/isort/flake8/mypy
- **API Design**: OpenAPI documentation, Pydantic schemas, consistent error formats
- **Exception Handling**: Specific exceptions, proper retry/backoff patterns
- **Logging**: Structured JSON logs with trace_id, masked sensitive data
- **Security**: Environment variables for secrets, input validation, rate limiting

### Naming Conventions
- Files/directories: `snake_case`
- API JSON fields: `camelCase` (external), `snake_case` (internal Python)
- Constants: `UPPER_SNAKE_CASE`

### Testing Strategy
- Unit tests (most), integration tests, E2E smoke tests
- Mock external dependencies
- Test naming: `methodName_condition_expectedResult`
- Boundary value and error path testing

## Documentation Structure

The project uses a three-tier documentation system:
- **PRD** (`prd/`): Product requirements with user personas, stories, acceptance criteria
- **TRD** (`trd/`): Technical requirements and architecture decisions  
- **Task** (`task/`): Implementation tasks linked to requirements

Files follow `NN-topic-kebab-case.md` naming and maintain version consistency across tiers.