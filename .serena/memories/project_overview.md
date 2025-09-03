# Hotly App - Project Overview

## Purpose
Hotly App is an **AI-based hot place/dating course/restaurant archiving app**. The application helps users:
- Analyze SNS links (Instagram, blogs) to extract place information using AI
- Manage and categorize discovered places
- Get AI-based course recommendations for dates
- Visualize courses on maps
- Share and save courses socially

## Tech Stack

### Backend (FastAPI + Python)
- **Framework**: FastAPI 0.109.0+ with Python 3.10+
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Cache**: Redis for caching and session management
- **Authentication**: JWT-based with python-jose
- **AI Integration**: Google Generative AI (Gemini)
- **Background Tasks**: Celery with Redis broker
- **Deployment**: Docker with docker-compose

### Development Tools
- **Package Management**: Poetry
- **Code Quality**: black, isort, flake8, mypy, bandit
- **Testing**: pytest with coverage (80%+ required)
- **Pre-commit**: Automated code quality checks
- **Container**: Docker + docker-compose for development

## Project Structure
```
hotly-app/
├── app/                    # Main application code
│   ├── api/               # API routes and endpoints
│   ├── core/              # Configuration and security
│   ├── crud/              # Database CRUD operations
│   ├── db/                # Database session and setup
│   ├── features/          # Domain-specific feature modules
│   ├── models/            # SQLAlchemy ORM models
│   ├── schemas/           # Pydantic request/response schemas
│   ├── services/          # Business logic services
│   ├── exceptions/        # Custom exceptions
│   └── main.py           # FastAPI application entry point
├── backend_reference/     # Reference implementation patterns
├── tests/                 # Test suite
├── scripts/              # Development scripts
├── alembic/              # Database migrations
├── prd/, trd/, task/     # Documentation (PRD, TRD, Tasks)
└── docker-compose.yml    # Development environment
```

## Architecture Patterns
- **Domain-driven Design**: Features organized by domain
- **Clean Architecture**: Separation of concerns (API → Services → CRUD → Models)
- **Dependency Injection**: Environment-based configuration with Pydantic Settings
- **Test-Driven Development**: TDD with Red-Green-Refactor cycle mandatory
- **API-First**: OpenAPI documentation auto-generated from FastAPI
