# Code Style and Conventions

## Python Code Style (PEP8 Compliance)
- **Line Length**: 88 characters (Black default)
- **Target Version**: Python 3.10+
- **Imports**: isort with Black profile
- **Type Hints**: Required for all functions and classes
- **Docstrings**: Google-style docstrings mandatory

## Naming Conventions
- **Files/Directories**: `snake_case`
- **Classes/Enums**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **API JSON Fields**: `camelCase` (external), `snake_case` (internal Python)

## Code Quality Tools Configuration
### Black
- Line length: 88
- Target version: py310
- Excludes: .eggs, .git, .mypy_cache, .tox, .venv, build, dist

### isort
- Profile: "black"
- Multi-line output: 3
- Include trailing comma: true
- Line length: 88
- Source paths: ["app", "tests"]

### MyPy
- Python version: 3.10
- Strict configuration enabled:
  - check_untyped_defs: true
  - disallow_any_generics: true
  - disallow_incomplete_defs: true
  - disallow_untyped_defs: true
  - no_implicit_optional: true

### Flake8
- Configuration in `.flake8` file
- Max line length: 88 (consistent with Black)

### Bandit
- Security linting enabled
- Excludes: tests, migrations
- Skips: B101, B601

## Exception Handling Rules
- **No Generic Exceptions**: Avoid `except Exception`
- **Specific Exceptions**: Use specific exception types
- **Domain Exceptions**: Define custom exceptions for business logic
- **Retry Logic**: Implement exponential backoff for transient errors
- **API Error Mapping**: Consistent HTTP error response format

## Logging Standards
- **Format**: Structured JSON logs
- **Fields**: timestamp, level, message, trace_id, user_id (when available)
- **Sensitive Data**: Mask PII, tokens, prompts
- **Levels**: DEBUG, INFO, WARN, ERROR, FATAL

## API Design Patterns
- **Versioning**: `/api/v1` prefix
- **Resources**: Plural nouns (`/places`, `/courses`)
- **Error Format**: `{"error": {"code": string, "message": string, "details"?: any}}`
- **Pagination**: `?page=1&page_size=20` or cursor-based
- **Schemas**: Pydantic models for request/response validation
