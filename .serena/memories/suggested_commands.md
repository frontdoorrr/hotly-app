# Essential Development Commands

## Setup Commands
```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Start development services (PostgreSQL + Redis)
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations
poetry run alembic upgrade head
```

## Development Server
```bash
# Start FastAPI development server
poetry run uvicorn app.main:app --reload

# Alternative with custom host/port
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Code Quality & Testing
```bash
# Run all tests with coverage
./scripts/test.sh
poetry run pytest --cov=app --cov-report=term-missing app/tests

# Format code (autoflake + black + isort)
./scripts/format.sh

# Lint code (mypy + black --check + isort --check + flake8 + bandit)
./scripts/lint.sh

# Generate HTML coverage report
./scripts/test-coverage.sh
```

## Database Management
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1
```

## Docker Operations
```bash
# Start full development stack
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down

# Production build
docker-compose up --build
```

## System Utilities (macOS)
```bash
# File operations
ls -la              # List files with details
find . -name "*.py" # Find Python files
grep -r "pattern"   # Search in files
cd /path/to/dir     # Change directory

# Git operations
git status          # Check git status
git add .           # Stage changes
git commit -m "msg" # Commit changes
git push origin main # Push to remote
```

## Pre-commit Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```
