# Docker Deployment Guide

## Quick Start

### Production Mode
```bash
# From project root
docker-compose up -d link-analyzer

# Check logs
docker-compose logs -f link-analyzer

# Check health
curl http://localhost:8001/health
```

### Development Mode (with hot reload)
```bash
# From project root
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up link-analyzer

# Or rebuild and run
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build link-analyzer
```

## Environment Variables

Required environment variables in `link-analyzer/.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key
YOUTUBE_API_KEY=your_youtube_api_key
```

Docker Compose will automatically load from `.env` file.

## Architecture

```
┌─────────────────────────────────────┐
│     Docker Network (hotly-network)  │
│                                     │
│  ┌──────────┐    ┌──────────────┐  │
│  │  Redis   │◄───│ Link-Analyzer│  │
│  │  :6379   │    │    :8001     │  │
│  └──────────┘    └──────────────┘  │
│                                     │
│  ┌──────────┐    ┌──────────────┐  │
│  │PostgreSQL│◄───│   Backend    │  │
│  │  :5432   │    │    :8000     │  │
│  └──────────┘    └──────────────┘  │
└─────────────────────────────────────┘
```

## Dockerfile Stages

### 1. Builder Stage
- Installs build dependencies (gcc, curl)
- Compiles Python packages
- Creates optimized wheels

### 2. Runtime Stage (Production)
- Minimal base image
- Non-root user (appuser:1000)
- Health checks
- No hot reload
- **Target**: `runtime`

### 3. Development Stage
- Extends runtime
- Enables hot reload
- Volume mounts for live code updates
- **Target**: `development`

## Docker Commands

### Build
```bash
# Production build
docker build -t link-analyzer:latest ./link-analyzer

# Development build
docker build -t link-analyzer:dev --target development ./link-analyzer

# Multi-platform build (for deployment)
docker buildx build --platform linux/amd64,linux/arm64 -t link-analyzer:latest ./link-analyzer
```

### Run
```bash
# Run production container
docker run -d \
  --name link-analyzer \
  -p 8001:8001 \
  --env-file ./link-analyzer/.env \
  -e REDIS_HOST=redis \
  link-analyzer:latest

# Run with docker-compose
docker-compose up -d link-analyzer
```

### Debug
```bash
# View logs
docker-compose logs -f link-analyzer

# Execute bash in container
docker-compose exec link-analyzer /bin/bash

# Check health
docker-compose exec link-analyzer curl http://localhost:8001/health

# Inspect container
docker inspect link-analyzer
```

### Cleanup
```bash
# Stop and remove
docker-compose down

# Remove with volumes
docker-compose down -v

# Clean unused images
docker system prune -a
```

## Health Checks

### Docker Health Check
Dockerfile includes built-in health check:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1
```

### Manual Health Check
```bash
# API health endpoint
curl http://localhost:8001/health

# Docker health status
docker-compose ps
```

## Performance Optimization

### Image Size
- Multi-stage build reduces image size
- Production image: ~200-300MB
- Development image: ~250-350MB

### Security
- Non-root user (UID 1000)
- Read-only root filesystem compatible
- No secrets in image layers
- Minimal attack surface

### Caching
- Layer caching optimized
- Dependencies cached separately from app code
- Faster rebuilds during development

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs link-analyzer

# Check environment variables
docker-compose exec link-analyzer env | grep -E 'GEMINI|YOUTUBE'

# Verify .env file
cat link-analyzer/.env
```

### Health check failing
```bash
# Test endpoint directly
docker-compose exec link-analyzer curl -v http://localhost:8001/health

# Check if service is listening
docker-compose exec link-analyzer netstat -tlnp | grep 8001
```

### Redis connection issues
```bash
# Ping Redis from link-analyzer
docker-compose exec link-analyzer ping redis

# Test Redis connection
docker-compose exec link-analyzer curl -v telnet://redis:6379
```

## Production Deployment

### Recommended Configuration
```yaml
services:
  link-analyzer:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
      restart_policy:
        condition: on-failure
        max_attempts: 3
```

### Environment Considerations
- Set `DEBUG=false`
- Use `LOG_LEVEL=INFO` or `WARNING`
- Configure proper `BACKEND_CORS_ORIGINS`
- Use secrets management for API keys
- Enable logging driver (e.g., json-file, syslog)

## Monitoring

### Logs
```bash
# Follow logs
docker-compose logs -f --tail=100 link-analyzer

# Export logs
docker-compose logs --no-color link-analyzer > logs.txt
```

### Metrics
```bash
# Container stats
docker stats link-analyzer

# Detailed resource usage
docker-compose top link-analyzer
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Build Docker image
  run: docker build -t link-analyzer:${{ github.sha }} ./link-analyzer

- name: Run tests in container
  run: |
    docker run --rm \
      -e GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }} \
      -e YOUTUBE_API_KEY=${{ secrets.YOUTUBE_API_KEY }} \
      link-analyzer:${{ github.sha }} \
      pytest tests/

- name: Push to registry
  run: docker push link-analyzer:${{ github.sha }}
```
