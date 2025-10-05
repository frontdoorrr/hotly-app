# Multi-stage FastAPI Dockerfile following backend_reference patterns
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1
ENV POETRY_VENV_IN_PROJECT=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR=/opt/pypoetry

# Development stage
FROM base as development

WORKDIR /backend

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --with dev

# Copy application code
COPY . .

EXPOSE 8000

# Default development command
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production

WORKDIR /backend

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install only production dependencies
RUN poetry install --only main --no-dev

# Copy application code
COPY . .

# Create non-root user
RUN groupadd -r hotly && useradd -r -g hotly hotly
RUN chown -R hotly:hotly /backend
USER hotly

EXPOSE 8000

# Production command
CMD ["poetry", "run", "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
