# TDD and Testing Guidelines

## Test-Driven Development (TDD) Process
**Mandatory Red-Green-Refactor Cycle:**

1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to pass the test
3. **REFACTOR**: Improve code while keeping tests green

## Testing Requirements
- **Coverage**: Minimum 80% line coverage (enforced by CI)
- **Test-First**: Always write tests before production code
- **Living Documentation**: Tests serve as executable specifications

## Test Categories & Structure
### Test Pyramid
1. **Unit Tests** (Most) - Fast, isolated, mock external dependencies
2. **Integration Tests** (Medium) - Test component interactions
3. **E2E Tests** (Few) - Smoke tests for critical user flows

### Test Organization
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── e2e/           # End-to-end tests
└── conftest.py    # Shared fixtures
```

## Test Naming Convention
Format: `test_methodName_condition_expectedResult`

Examples:
```python
def test_create_place_validData_returnsPlaceModel():
def test_analyze_link_invalidUrl_raisesValidationError():
def test_search_places_emptyQuery_returnsEmptyList():
```

## Testing Tools & Configuration
### Pytest Configuration
- **Markers**: integration, unit, e2e, slow
- **Coverage**: `--cov=app --cov-report=term-missing --cov-report=html`
- **Test Discovery**: `test_*.py` files, `Test*` classes, `test_*` functions

### Fixtures and Mocking
- Use pytest fixtures for test setup
- Mock external dependencies (APIs, databases)
- Use `@patch` for unit test isolation
- Provide realistic test data

## Test Structure Pattern (Given-When-Then)
```python
def test_feature_condition_result():
    # Given (Arrange)
    user = create_test_user()
    place_data = {"name": "Test Place", "address": "123 Main St"}

    # When (Act)
    result = place_service.create_place(user.id, place_data)

    # Then (Assert)
    assert result.id is not None
    assert result.name == "Test Place"
```

## Coverage Requirements
- **Minimum**: 80% line coverage
- **Critical Paths**: 95%+ coverage for core business logic
- **Exclusions**: `__init__.py`, migrations, test files
- **CI Enforcement**: Build fails if coverage drops below threshold

## Test Data Management
- Use factories for test data generation
- Isolate tests with database transactions
- Clean up test data after each test
- Avoid test dependencies and shared state
