# Task Completion Checklist

## Mandatory Steps When Completing Any Task

### 1. Code Quality Checks
```bash
# Format code
./scripts/format.sh

# Run linting
./scripts/lint.sh

# Must pass all checks:
# - mypy (type checking)
# - black --check (formatting)
# - isort --check (import sorting)
# - flake8 (style guide)
# - bandit (security)
```

### 2. Test Requirements
```bash
# Run all tests with coverage
./scripts/test.sh

# Requirements:
# - All tests must pass
# - Coverage ≥ 80% (CI enforced)
# - New features must have tests written FIRST (TDD)
```

### 3. Database Migration (if applicable)
```bash
# Create migration for schema changes
poetry run alembic revision --autogenerate -m "description"

# Apply migration
poetry run alembic upgrade head

# Test migration rollback
poetry run alembic downgrade -1
poetry run alembic upgrade head
```

### 4. Documentation Updates
- Update API documentation (OpenAPI auto-generated)
- Update relevant `.md` files in `prd/`, `trd/`, `task/` directories
- Add/update docstrings for new functions/classes
- Update `CLAUDE.md` if development patterns change

### 5. Security Checks
- No hardcoded secrets or API keys
- Proper input validation and sanitization
- PII data properly masked in logs
- Authentication/authorization implemented where needed

### 6. Performance Validation
- API response times within requirements (p95 < 2s)
- Database queries optimized with proper indexes
- Cache implementation where specified
- Memory usage tested under load

### 7. Pre-commit Validation
```bash
# Ensure pre-commit hooks pass
poetry run pre-commit run --all-files
```

### 8. Integration Testing
- Test with development Docker stack
- Verify external service integrations (AI, databases)
- Test error scenarios and edge cases
- Validate API contracts with frontend expectations

## Definition of Done (DoD) Criteria
- [ ] Feature implemented according to TRD specifications
- [ ] Tests written first (TDD) with ≥80% coverage
- [ ] All code quality checks pass
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Performance requirements met
- [ ] Integration testing completed
- [ ] Code reviewed and approved
- [ ] Deployment ready (Docker builds successfully)

## Rollback Preparedness
- [ ] Migration rollback tested
- [ ] Feature flags implemented for major changes
- [ ] Monitoring and alerting configured
- [ ] Backup procedures verified
