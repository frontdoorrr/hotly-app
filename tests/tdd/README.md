# TDD (Test-Driven Development) Framework

## Overview
This directory contains TDD examples, templates, and documentation for implementing test-first development in the Hotly app project.

## TDD Process

### Red-Green-Refactor Cycle
1. **RED**: Write a failing test first
2. **GREEN**: Write minimal code to pass the test
3. **REFACTOR**: Improve code while keeping tests green

### TDD Principles
- No production code without a failing test
- Write only enough test to fail
- Write only enough production code to pass
- Tests serve as living documentation
- Maintain 80%+ test coverage

## Directory Structure
```
tests/tdd/
├── README.md                 # This file
├── examples/                 # TDD implementation examples
│   ├── link_analysis_tdd.py  # Complete TDD example
│   ├── place_service_tdd.py  # Service layer TDD example
│   └── api_endpoint_tdd.py   # API endpoint TDD example
├── templates/                # Test templates and patterns
│   ├── unit_test_template.py
│   ├── integration_test_template.py
│   └── e2e_test_template.py
└── guidelines/               # TDD guidelines and best practices
    ├── tdd_workflow.md
    ├── naming_conventions.md
    └── mocking_strategies.md
```

## Getting Started

### 1. Follow the TDD Workflow
```python
# Step 1: RED - Write failing test
def test_create_place_validData_returnsPlaceWithId():
    # Given
    place_data = {"name": "Test Restaurant", "address": "123 Main St"}

    # When/Then - This will fail initially
    result = place_service.create_place(place_data)
    assert result.id is not None
    assert result.name == "Test Restaurant"

# Step 2: GREEN - Write minimal implementation
class PlaceService:
    def create_place(self, place_data):
        return Place(id=1, name=place_data["name"])

# Step 3: REFACTOR - Improve implementation
class PlaceService:
    def create_place(self, place_data):
        place = Place(**place_data)
        place.id = generate_unique_id()
        self.repository.save(place)
        return place
```

### 2. Use Test Templates
Copy templates from `templates/` directory for consistent test structure.

### 3. Follow Naming Conventions
- Test files: `test_*.py`
- Test methods: `test_methodName_condition_expectedResult`
- Test classes: `Test*`

## Testing Strategies

### Unit Tests (Fastest, Most)
- Test single functions/methods in isolation
- Mock all external dependencies
- Focus on business logic

### Integration Tests (Medium)
- Test component interactions
- Real database connections (with test data)
- Service-to-service communication

### E2E Tests (Slowest, Fewest)
- Test complete user workflows
- Real API calls through test client
- Critical path validation

## Coverage Requirements
- Minimum: 80% line coverage
- Critical business logic: 95%+ coverage
- New features: 100% coverage requirement

## Running Tests
```bash
# Run all tests with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Exclude slow tests

# Run TDD examples
pytest tests/tdd/examples/
```

## Best Practices
1. Write tests before production code
2. Keep tests simple and focused
3. Use descriptive test names
4. Mock external dependencies
5. Test edge cases and error conditions
6. Maintain test isolation
7. Regular refactoring with green tests
