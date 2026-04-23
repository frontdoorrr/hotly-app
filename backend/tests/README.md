# ArchyAI App - Test Suite

## 📊 Test Structure Overview

This test suite follows the **Test Pyramid** pattern for optimal coverage and maintainability:

```
        /\
       /  \  E2E (15 tests)          - Complete user workflows
      /    \
     /------\ Integration (25 tests) - Service & API integration
    /--------\
   /----------\ Unit (46 tests)      - Individual components
  /------------\
```

### Current Test Distribution

| Category      | Count | Directory | Purpose |
|--------------|-------|-----------|---------|
| **Unit**      | 46    | `tests/unit/` | Fast, isolated tests for individual functions/classes |
| **Integration** | 25  | `tests/integration/` | Service-to-service and API endpoint tests |
| **E2E**        | 15   | `tests/e2e/` | Complete user workflow tests |
| **Performance** | 10  | `tests/performance/` | Load, stress, and performance benchmarks |
| **Framework**   | 6   | `tests/framework/` | Testing infrastructure and tooling tests |

**Total: 102 tests** 🎯

## 📂 Directory Structure

```
tests/
├── unit/                        # Unit tests (46 tests)
│   ├── services/                # Service layer tests
│   ├── models/                  # Model/schema tests
│   ├── api/                     # API layer unit tests
│   └── *.py                     # Other unit tests
│
├── integration/                 # Integration tests (25 tests)
│   ├── api/                     # API endpoint integration tests
│   └── services/                # Service integration tests
│
├── e2e/                         # End-to-end tests (15 tests)
│   └── *.py                     # Complete user workflows
│
├── performance/                 # Performance tests (10 tests)
│   └── *.py                     # Load, stress, benchmark tests
│
├── framework/                   # Framework tests (6 tests)
│   ├── infrastructure/          # Project structure, Docker, DB tests
│   └── *.py                     # Test helpers, pytest config tests
│
├── tdd/                         # TDD documentation & examples
│   ├── examples/                # TDD example implementations
│   ├── guidelines/              # TDD best practices
│   └── templates/               # Test templates
│
└── utils/                       # Test utilities
    └── test_helpers.py          # MockFactory, TestDataBuilder
```

## 🚀 Running Tests

### Run All Tests
```bash
pytest
```

### Run by Category
```bash
# Unit tests (fast, run frequently)
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests (slower, comprehensive)
pytest tests/e2e/

# Performance tests
pytest tests/performance/
```

### Run Specific Test Suites
```bash
# Unit service tests only
pytest tests/unit/services/

# API integration tests only
pytest tests/integration/api/

# Single test file
pytest tests/unit/test_exceptions.py -v
```

### Run with Coverage
```bash
# Full coverage report
pytest --cov=app --cov-report=html

# Coverage for specific module
pytest tests/unit/services/ --cov=app.services
```

### Test Automation Script
```bash
# Comprehensive test automation (includes all test types)
./scripts/run-tests.sh

# Specific test types
./scripts/run-tests.sh --unit           # Unit only
./scripts/run-tests.sh --integration    # Integration only
./scripts/run-tests.sh --e2e            # E2E only
./scripts/run-tests.sh --fast           # Skip slow tests
./scripts/run-tests.sh --ci             # CI optimized
```

## 📝 Writing Tests

### Test Naming Convention
```python
def test_methodName_condition_expectedResult():
    """Test description in Korean or English."""
    # Given: Setup
    # When: Action
    # Then: Assertion
```

### Where to Put Your Test

#### ✅ Unit Test (`tests/unit/`)
- Tests a **single function, class, or module** in isolation
- Uses mocks for external dependencies
- Fast execution (< 100ms per test)
- Example: Testing a service method with mocked database

```python
# tests/unit/services/test_my_service.py
from unittest.mock import Mock
def test_myMethod_validInput_returnsResult():
    service = MyService(db=Mock())
    result = service.my_method("input")
    assert result == "expected"
```

#### ✅ Integration Test (`tests/integration/`)
- Tests **multiple components working together**
- May use real database/Redis (test instances)
- Moderate execution time (< 1s per test)
- Example: Testing an API endpoint with real services

```python
# tests/integration/api/test_my_api.py
from fastapi.testclient import TestClient
def test_myEndpoint_validRequest_returns200(client: TestClient):
    response = client.post("/api/v1/my-endpoint", json={...})
    assert response.status_code == 200
```

#### ✅ E2E Test (`tests/e2e/`)
- Tests **complete user workflows** from start to finish
- Uses full application stack
- Slow execution (> 1s per test)
- Example: User registration → login → create resource → verify

```python
# tests/e2e/test_user_workflow.py
def test_completeUserJourney_newUser_successfulFlow():
    # 1. Register user
    # 2. Verify email
    # 3. Login
    # 4. Create first resource
    # 5. Verify resource saved
    pass
```

#### ✅ Performance Test (`tests/performance/`)
- Tests **performance benchmarks** and load handling
- Measures response time, throughput, resource usage
- Example: Load testing with 100 concurrent requests

```python
# tests/performance/test_api_performance.py
def test_apiEndpoint_100ConcurrentRequests_under500ms():
    # Concurrent load simulation
    # Assert p95 < 500ms
    pass
```

## 🎯 Test Quality Standards

### Coverage Requirements
- **Overall**: 80% minimum (enforced by CI)
- **Critical paths**: 95%+ recommended
- **New features**: Must include tests before merge

### Test Characteristics
- ✅ **Fast**: Unit tests < 100ms, Integration < 1s
- ✅ **Isolated**: No dependencies between tests
- ✅ **Deterministic**: Same input = same output
- ✅ **Readable**: Clear Given-When-Then structure
- ✅ **Maintainable**: Uses test helpers and fixtures

## 🛠️ Test Utilities

### MockFactory
```python
from tests.utils.test_helpers import MockFactory

# Create mock data
user = MockFactory.create_user()
place = MockFactory.create_place(category="cafe")
```

### TestDataBuilder
```python
from tests.utils.test_helpers import TestDataBuilder

course = TestDataBuilder() \
    .with_places(3) \
    .with_transport("walking") \
    .build_course()
```

### Fixtures (conftest.py)
```python
import pytest

@pytest.fixture
def db():
    """Test database session."""
    # Setup
    yield session
    # Teardown
```

## 🔍 TDD Workflow

1. **Red**: Write failing test first
2. **Green**: Implement minimum code to pass
3. **Refactor**: Improve code quality

See `tests/tdd/README.md` for detailed TDD guidelines and examples.

## 📊 Monitoring Test Health

### Check Test Distribution
```bash
python scripts/classify_tests.py
```

### View Coverage Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### CI/CD Integration
All tests run automatically on:
- Every pull request
- Merge to main branch
- GitHub Actions workflow: `.github/workflows/test-automation.yml`

## 📚 Additional Resources

- **TDD Guidelines**: `tests/tdd/guidelines/tdd_workflow.md`
- **Test Templates**: `tests/tdd/templates/`
- **TDD Examples**: `tests/tdd/examples/`
- **Project Rules**: `rules.md` (TDD section)

## 🐛 Troubleshooting

### Common Issues

**Import errors after moving tests:**
```bash
# Re-run pytest to rebuild cache
pytest --cache-clear
```

**Slow test execution:**
```bash
# Run only fast tests
pytest -m "not slow"
```

**Flaky tests:**
```bash
# Run test multiple times
pytest tests/path/to/test.py --count=10
```

---

**Last Updated**: 2025-10-03
**Maintained By**: Development Team
**Test Count**: 102 tests
