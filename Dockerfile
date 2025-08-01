# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY pyproject.toml .
COPY README.md .
COPY LICENSE .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -e ".[all]"

# Copy source code
COPY taskforge/ ./taskforge/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd --create-home --shell /bin/bash taskforge
RUN chown -R taskforge:taskforge /app

# Switch to non-root user
USER taskforge

# Create data directory
RUN mkdir -p /app/data

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (API server)
CMD ["uvicorn", "taskforge.api:app", "--host", "0.0.0.0", "--port", "8000"]

# Labels for better container management
LABEL org.opencontainers.image.title="TaskForge"
LABEL org.opencontainers.image.description="A comprehensive task management platform"
LABEL org.opencontainers.image.source="https://github.com/taskforge-community/taskforge"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="TaskForge Community"