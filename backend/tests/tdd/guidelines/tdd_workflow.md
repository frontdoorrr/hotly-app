# TDD Workflow Guide

## Red-Green-Refactor Cycle

### 1. RED Phase - Write Failing Test First

**Goal**: Define expected behavior through tests before writing implementation.

#### Steps:
1. **Identify the requirement** from task/feature specification
2. **Write the simplest failing test** that captures the requirement
3. **Run the test** to confirm it fails (RED)
4. **Commit the failing test** to version control

#### Example:
```python
def test_analyze_link_validInstagramUrl_returnsSuccessResponse():
    """RED: This test defines what we want to build."""
    # Given
    url = "https://instagram.com/p/CXXXXXXXXXx/"
    request = LinkAnalyzeRequest(url=url)

    # When - This will fail because LinkAnalysisService doesn't exist yet
    service = LinkAnalysisService()
    result = await service.analyze_link(request)

    # Then - Expected behavior
    assert result.success is True
    assert result.analysis_id is not None
    assert result.status == AnalysisStatus.COMPLETED
```

#### RED Phase Checklist:
- [ ] Test is focused on single behavior
- [ ] Test name follows `methodName_condition_expectedResult` convention
- [ ] Test fails for the right reason (missing implementation, not syntax error)
- [ ] Test captures business requirement accurately
- [ ] Test is the simplest possible to express the requirement

### 2. GREEN Phase - Write Minimal Implementation

**Goal**: Make the test pass with the simplest possible implementation.

#### Steps:
1. **Write minimal code** to make the test pass
2. **Don't worry about perfect design** yet
3. **Run the test** to confirm it passes (GREEN)
4. **Run all tests** to ensure no regressions
5. **Commit the working code**

#### Example:
```python
# Minimal implementation - just make it work
class LinkAnalysisService:
    async def analyze_link(self, request):
        # Hardcoded response to make test pass
        return LinkAnalyzeResponse(
            success=True,
            analysis_id="test-123",
            status=AnalysisStatus.COMPLETED,
            result=None,
            cached=False,
            processing_time=0.1
        )
```

#### GREEN Phase Checklist:
- [ ] Test passes
- [ ] All existing tests still pass
- [ ] Implementation is minimal (no gold-plating)
- [ ] Code compiles/runs without errors
- [ ] Implementation directly addresses the failing test

### 3. REFACTOR Phase - Improve Implementation

**Goal**: Improve code quality while keeping all tests green.

#### Steps:
1. **Identify code smells** in current implementation
2. **Refactor incrementally** (small steps)
3. **Run tests after each change** to ensure they stay green
4. **Improve design, performance, readability**
5. **Commit improved code**

#### Example:
```python
# Refactored implementation with proper design
class LinkAnalysisService:
    def __init__(self, content_extractor, ai_analyzer, cache_manager):
        self.content_extractor = content_extractor
        self.ai_analyzer = ai_analyzer
        self.cache_manager = cache_manager

    async def analyze_link(self, request):
        analysis_id = str(uuid.uuid4())

        # Check cache first
        cached_result = await self.cache_manager.get(request.url)
        if cached_result and not request.force_refresh:
            return self._build_response(analysis_id, cached_result, cached=True)

        # Extract content
        content = await self.content_extractor.extract_content(request.url)

        # Analyze with AI
        analysis = await self.ai_analyzer.analyze_content(content)

        # Cache result
        await self.cache_manager.set(request.url, analysis)

        return self._build_response(analysis_id, analysis, cached=False)
```

#### REFACTOR Phase Checklist:
- [ ] All tests remain green throughout refactoring
- [ ] Code is more readable and maintainable
- [ ] Duplicated code is eliminated
- [ ] Design patterns are applied appropriately
- [ ] Performance is improved where possible
- [ ] Error handling is robust

## TDD Best Practices

### Test Writing Guidelines

1. **Test Behavior, Not Implementation**
   ```python
   # Good - tests behavior
   def test_analyze_link_invalidUrl_raisesValidationError():
       with pytest.raises(ValidationError):
           service.analyze_link("invalid-url")

   # Bad - tests implementation details
   def test_analyze_link_callsUrlValidator():
       service.analyze_link("url")
       assert service.url_validator.validate.called
   ```

2. **Use Descriptive Test Names**
   ```python
   # Good
   def test_cache_hit_returnsStoredResult()
   def test_cache_miss_performsFullAnalysis()
   def test_invalidUrl_raisesValidationError()

   # Bad
   def test_cache()
   def test_analyze()
   def test_error()
   ```

3. **Follow Given-When-Then Structure**
   ```python
   def test_place_creation_validData_savesToDatabase():
       # Given (Arrange)
       place_data = {"name": "Test Restaurant", "address": "123 Main St"}

       # When (Act)
       result = place_service.create_place(place_data)

       # Then (Assert)
       assert result.id is not None
       assert result.name == "Test Restaurant"
   ```

### TDD Anti-Patterns to Avoid

1. **Writing Tests After Implementation**
   - Defeats the design benefit of TDD
   - Tests may not catch real bugs
   - Implementation may be hard to test

2. **Testing Implementation Details**
   - Makes refactoring difficult
   - Tests become brittle
   - Focus on behavior/outcomes instead

3. **Large Test Steps**
   - Write small, focused tests
   - Each test should verify one behavior
   - Large tests are hard to debug when they fail

4. **Skipping Refactor Phase**
   - Code quality degrades over time
   - Technical debt accumulates
   - Refactor continuously while tests are green

### TDD Cycle Timing

- **RED**: 30 seconds to 2 minutes
- **GREEN**: 1 to 10 minutes
- **REFACTOR**: 2 to 10 minutes
- **Complete cycle**: 5 to 20 minutes

If any phase takes longer, consider breaking down the requirement into smaller pieces.

## TDD in Team Environment

### Code Review Guidelines
- [ ] Tests written before implementation
- [ ] All tests pass
- [ ] Test names clearly describe behavior
- [ ] Implementation is clean and minimal
- [ ] Code coverage meets team standards (80%+)

### Pair Programming with TDD
1. **Navigator writes test** (RED)
2. **Driver implements code** (GREEN)
3. **Both refactor together** (REFACTOR)
4. **Switch roles** and repeat

### Continuous Integration
- Run all tests on every commit
- Fail build if coverage drops below threshold
- Run tests in multiple environments
- Generate coverage reports

## TDD for Different Test Types

### Unit Tests (Most Common)
- Test single methods/functions
- Mock all external dependencies
- Fast execution (< 10ms per test)
- Follow strict TDD cycle

### Integration Tests
- Test component interactions
- Use real database/services where appropriate
- TDD cycle may be longer due to setup
- Focus on interface contracts

### End-to-End Tests
- Test complete user workflows
- Modified TDD approach (may write fewer, broader tests)
- Focus on critical business scenarios
- Longer feedback cycle

## Measuring TDD Success

### Code Quality Metrics
- **Test Coverage**: 80%+ line coverage
- **Cyclomatic Complexity**: < 10 per method
- **Test-to-Code Ratio**: 1:1 to 3:1 lines
- **Defect Rate**: Decreasing over time

### Process Metrics
- **Time to Green**: How quickly tests pass
- **Refactor Frequency**: Regular, small improvements
- **Test Failure Rate**: Low rate in CI/CD
- **Code Review Speed**: Faster due to better design

### Team Benefits
- **Confidence**: Safe to refactor and change code
- **Documentation**: Tests serve as living specifications
- **Design**: Better API design through test-first approach
- **Debugging**: Failing tests pinpoint issues quickly
