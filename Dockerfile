# Multi-stage Dockerfile for TaskForge
# Build: docker build -t taskforge .
# Run: docker run -p 8000:8000 taskforge

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./
COPY taskforge/ taskforge/

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e ".[all]" && \
    pip install gunicorn uvicorn[standard]

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TASKFORGE_HOST=0.0.0.0 \
    TASKFORGE_PORT=8000 \
    TASKFORGE_WORKERS=4

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r taskforge \
    && useradd -r -g taskforge -s /bin/bash -c "TaskForge user" taskforge

# Copy application from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs /app/static && \
    chown -R taskforge:taskforge /app

# Switch to non-root user
USER taskforge
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${TASKFORGE_PORT}/health || exit 1

# Expose port
EXPOSE ${TASKFORGE_PORT}

# Default command
CMD ["gunicorn", "taskforge.api:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info"]

# Labels for better container management
LABEL org.opencontainers.image.title="TaskForge"
LABEL org.opencontainers.image.description="A comprehensive task management platform"
LABEL org.opencontainers.image.source="https://github.com/taskforge-community/taskforge"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="TaskForge Community"