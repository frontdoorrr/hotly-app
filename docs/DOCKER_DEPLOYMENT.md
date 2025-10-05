# Docker Deployment Guide for hotly-app

This guide explains how to build and deploy the hotly-app using Docker and Docker Compose.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- Git (for version tagging)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/hotly-app.git
cd hotly-app
```

### 2. Set Up Environment Variables

```bash
# For development
cp .env.example .env

# For production
cp .env.production.example .env.production
# Edit .env.production and fill in your API keys and secrets
```

### 3. Start the Application

```bash
# Development (with hot reload)
./scripts/docker-run.sh --dev

# Production
./scripts/docker-run.sh --prod
```

The API will be available at:
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Development Environment

### Building the Development Image

```bash
./scripts/docker-build.sh --dev
```

### Running Development Services

```bash
# Start all services (app, database, redis) in development mode
./scripts/docker-run.sh --dev

# View logs in real-time
./scripts/docker-run.sh --logs

# Stop all services
./scripts/docker-run.sh --down
```

### Development Features

- **Hot Reload**: Code changes are automatically detected
- **Debug Mode**: Detailed error messages and stack traces
- **All Dependencies**: Includes development tools (pytest, black, mypy, etc.)

### Running Tests Inside Container

```bash
# Enter the container shell
docker-compose exec app bash

# Run tests
poetry run pytest
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/unit/test_example.py -v
```

## Production Deployment

### 1. Prepare Environment

Create `.env.production` with your production configuration:

```bash
cp .env.production.example .env.production
```

**Required Environment Variables**:

```env
# Database
POSTGRES_PASSWORD=<STRONG_PASSWORD>

# API Keys
KAKAO_API_KEY=<YOUR_KEY>
GOOGLE_GEMINI_API_KEY=<YOUR_KEY>
SUPABASE_URL=<YOUR_URL>
SUPABASE_KEY=<YOUR_KEY>

# Security
SECRET_KEY=<RANDOM_SECRET_KEY>
ALLOWED_HOSTS=yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

### 2. Build Production Image

```bash
./scripts/docker-build.sh --prod --version v1.0.0
```

This creates an optimized multi-stage Docker image:
- **Smaller size**: Only production dependencies
- **Security**: Runs as non-root user
- **Performance**: Gunicorn with Uvicorn workers

### 3. Start Production Services

```bash
./scripts/docker-run.sh --prod
```

### 4. Verify Deployment

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

## Docker Compose Services

### Production Stack (`docker-compose.prod.yml`)

| Service | Description | Port |
|---------|-------------|------|
| **app** | FastAPI application with Gunicorn | 8000 |
| **db** | PostgreSQL 15 with PostGIS | 5432 |
| **redis** | Redis 7 for caching | 6379 |
| **nginx** | Reverse proxy (optional) | 80, 443 |

### Service Configuration

#### Application (app)

- **Image**: `hotly-app:latest`
- **Workers**: 4 Gunicorn workers with Uvicorn
- **Resources**: 2 CPU cores, 2GB RAM (limit)
- **Health Check**: `/health` endpoint every 30s
- **Restart Policy**: unless-stopped

#### Database (db)

- **Image**: `postgis/postgis:15-3.3-alpine`
- **Extensions**: PostGIS, pg_trgm, uuid-ossp
- **Persistent Volume**: `postgres_data`
- **Health Check**: `pg_isready` every 10s

#### Redis (redis)

- **Image**: `redis:7-alpine`
- **Max Memory**: 512MB with LRU eviction
- **Persistence**: AOF + RDB snapshots
- **Persistent Volume**: `redis_data`

## Container Management

### Viewing Logs

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f app
docker-compose -f docker-compose.prod.yml logs -f db
```

### Executing Commands

```bash
# Enter application container
docker-compose -f docker-compose.prod.yml exec app bash

# Run database migrations
docker-compose -f docker-compose.prod.yml exec app poetry run alembic upgrade head

# Access database
docker-compose -f docker-compose.prod.yml exec db psql -U hotly_user -d hotly_db
```

### Updating the Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./scripts/docker-build.sh --prod --version v1.1.0
./scripts/docker-run.sh --prod --build
```

### Backup and Restore

#### Database Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U hotly_user hotly_db > backup.sql

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T db psql -U hotly_user hotly_db < backup.sql
```

#### Volume Backup

```bash
# Backup PostgreSQL data
docker run --rm -v hotly-app_postgres_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz /data

# Backup Redis data
docker run --rm -v hotly-app_redis_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/redis-backup-$(date +%Y%m%d).tar.gz /data
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Common issues:
# 1. Missing environment variables
# 2. Database not ready (wait for health check)
# 3. Port already in use
```

### Database Connection Issues

```bash
# Check if database is ready
docker-compose -f docker-compose.prod.yml exec db pg_isready -U hotly_user

# Test connection from app container
docker-compose -f docker-compose.prod.yml exec app poetry run python -c \
    "from app.db.session import SessionLocal; db = SessionLocal(); print('OK')"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Adjust limits in docker-compose.prod.yml:
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

### Clear Everything and Start Fresh

```bash
# WARNING: This will delete all data!
docker-compose -f docker-compose.prod.yml down -v
docker system prune -a
./scripts/docker-run.sh --prod --build
```

## Performance Tuning

### Gunicorn Workers

Adjust worker count based on CPU cores:

```bash
# Formula: (2 x CPU cores) + 1
# For 4 cores: 9 workers
CMD ["gunicorn", "app.main:app", "--workers", "9", ...]
```

### Redis Memory

Adjust max memory in `docker-compose.prod.yml`:

```yaml
command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

### PostgreSQL Connection Pool

Adjust in `app/core/config.py`:

```python
SQLALCHEMY_POOL_SIZE = 10  # Default connections
SQLALCHEMY_MAX_OVERFLOW = 20  # Additional connections
```

## Security Best Practices

1. **Use Strong Secrets**: Generate secure passwords and API keys
2. **Non-Root User**: Application runs as `hotly` user
3. **Network Isolation**: Services communicate via Docker network
4. **HTTPS**: Use nginx with SSL certificates in production
5. **Regular Updates**: Keep Docker images and dependencies updated

## Next Steps

- [Set up CI/CD Pipeline](./CI_CD.md)
- [Configure Nginx Reverse Proxy](./NGINX.md)
- [Monitor Production Deployment](./MONITORING.md)
