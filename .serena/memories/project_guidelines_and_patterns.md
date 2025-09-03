# Project Guidelines and Design Patterns

## Architecture Principles

### Clean Architecture Layers
1. **API Layer** (`app/api/`) - FastAPI routers, request/response handling
2. **Service Layer** (`app/services/`) - Business logic and orchestration
3. **CRUD Layer** (`app/crud/`) - Database operations
4. **Model Layer** (`app/models/`) - SQLAlchemy ORM models
5. **Schema Layer** (`app/schemas/`) - Pydantic validation models

### Domain-Driven Design
- **Features**: Organized by business domain (`app/features/`)
- **Bounded Contexts**: Clear separation between domains
- **Aggregates**: Models grouped by business rules
- **Domain Services**: Complex business logic encapsulation

## Design Patterns

### Configuration Management
- **12-Factor App**: Environment variable based configuration
- **Pydantic Settings**: Type-safe configuration with validation
- **Secret Management**: Environment variables, no hardcoded secrets

### Error Handling Strategy
- **Domain Exceptions**: Custom exceptions for business logic
- **HTTP Error Mapping**: Consistent API error responses
- **Retry Patterns**: Exponential backoff for transient failures
- **Circuit Breaker**: Prevent cascading failures

### Caching Strategy
- **Multi-layer**: L1 (local) + L2 (Redis) caching
- **Key Namespacing**: `hotly:{domain}:{key}` pattern
- **TTL Management**: Domain-specific expiration policies
- **Cache Invalidation**: Event-driven cache updates

### Database Patterns
- **Repository Pattern**: Abstract database operations
- **Unit of Work**: Transaction management
- **Migration Strategy**: Alembic for schema versioning
- **Indexing**: Optimized for query patterns

## Backend Reference Patterns
The `backend_reference/` directory contains proven patterns to follow:

### Project Structure
- Follow `backend_reference/app/app/` structure
- API organization: `api/api_v1/endpoints/`
- Service layer separation
- Configuration centralization

### FastAPI Patterns
- Router organization by domain
- Dependency injection for database sessions
- Middleware for cross-cutting concerns
- OpenAPI documentation generation

### Database Patterns
- SQLAlchemy models with relationships
- Alembic migration management
- Connection pooling configuration
- Query optimization techniques

## Development Workflow

### Branch Strategy
- **Feature Branches**: `feat/<scope>-<description>`
- **Bug Fixes**: `fix/<scope>-<description>`
- **Hotfixes**: `hotfix/<description>`

### Commit Convention (Conventional Commits)
Format: `<type>(<scope>): <description>`
- Types: feat, fix, docs, refactor, test, chore, perf, ci, build
- Example: `feat(places): add duplicate detection algorithm`

### Code Review Process
- Minimum 1 reviewer approval
- All CI checks must pass
- Test coverage maintained at 80%+
- Security review for sensitive changes

## Performance Guidelines

### API Performance
- Response time p95 < 2 seconds
- Implement pagination for list endpoints
- Use async/await for I/O operations
- Database connection pooling

### Caching Requirements
- Cache hit rate ≥ 60%
- Redis for shared cache
- Local cache for frequently accessed data
- Cache warm-up strategies

### Monitoring & Observability
- Structured JSON logging
- Request tracing with correlation IDs
- Performance metrics collection
- Error rate monitoring

## Security Guidelines

### Data Protection
- PII masking in logs
- Encryption for sensitive data
- Input validation and sanitization
- SQL injection prevention

### Authentication & Authorization
- JWT token validation
- Role-based access control
- API rate limiting
- CORS configuration

### Secure Development
- Dependency vulnerability scanning
- Security headers implementation
- Environment variable management
- Regular security audits
